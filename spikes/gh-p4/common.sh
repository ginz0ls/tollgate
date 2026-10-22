#!/usr/bin/env bash
# spikes/gh-p4/common.sh — funzioni comuni degli script con gh vero (run-p4-checks.sh, run-p4-gate.sh, run-p4-flow.sh).
# Si carica con `. common.sh` dopo aver impostato: root, OUT, WORK, PROT, DET, CHECK, WAIT_MAX, POLL, RETRY_SLEEP.
# Nessun gh senza passare da ghguard.py (decisione 25): gh_call e gh_q lo controllano prima di lanciare gh.
GH4_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "errore: $*" >&2; exit 1; }

# ---------------------------------------------------------------- guardie

# Prima di ogni gh: lista degli ammessi della decisione 25, unica fonte in ghguard.py (la usa anche check_gh_log).
guard_args() {
  local msg
  msg="$(python3 -B -I "$GH4_DIR/ghguard.py" check -- "$@" 2>&1)" || die "gh $*: $msg"
}

# Un remoto git diverso dal repo atteso ferma lo script prima di ogni git che parla con la rete.
check_remote() {
  local n="$1" repo url
  repo="$(repo_of "$n")"
  url="$(git -C "$WORK/$n" remote get-url --push origin 2>/dev/null)" || return 1
  case "$url" in
    "https://github.com/$repo"|"https://github.com/$repo.git"|"git@github.com:$repo.git") return 0 ;;
  esac
  [ "$CHECK" = 1 ] && [ -n "${P4_GIT_BASE:-}" ] && [ "$url" = "$P4_GIT_BASE/$repo.git" ] && return 0
  return 1
}

repo_of() { case "$1" in protected) echo "$PROT" ;; detect) echo "$DET" ;; *) die "repo sconosciuto: $1" ;; esac; }

# ---------------------------------------------------------------- uscite

rot() { # rinomina i file esistenti, non li cancella
  local f
  for f; do [ -e "$f" ] && mv -- "$f" "$f.prev-$(date +%s%N)"; done
  return 0
}

log_cmd() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$OUT/comandi.log"; }

# gh_call <etichetta> <argomenti di gh...>: stdout, stderr e codice d'uscita in tre file; il codice anche in $RC
gh_call() {
  local label="$1"; shift
  guard_args "$@"
  rot "$OUT/$label".out "$OUT/$label".err "$OUT/$label".rc
  log_cmd "gh $*"
  ${GH_TIMEOUT:+timeout "$GH_TIMEOUT"} gh "$@" >"$OUT/$label.out" 2>"$OUT/$label.err" </dev/null
  RC=$?
  echo "$RC" >"$OUT/$label.rc"
  return 0
}

# gh_q <argomenti di gh...>: per i sondaggi ripetuti, scrive solo su stdout (la chiamata finale si salva con gh_call)
gh_q() { guard_args "$@"; gh "$@" 2>/dev/null </dev/null; }

# git_call <etichetta> <protected|detect> <argomenti di git...>
git_call() {
  local label="$1" n="$2"; shift 2
  check_remote "$n" || die "il remoto di $n non è quello atteso: mi fermo"
  rot "$OUT/$label".out "$OUT/$label".err "$OUT/$label".rc
  log_cmd "git -C $n $*"
  git -C "$WORK/$n" "$@" >"$OUT/$label.out" 2>"$OUT/$label.err" </dev/null
  RC=$?
  echo "$RC" >"$OUT/$label.rc"
  return 0
}

save_text() { # file, testo...
  local f="$1"; shift
  rot "$f"
  printf '%s\n' "$@" > "$f"
}

load_env() { # file; fallisce se manca (il modo che lo scrive non è stato lanciato)
  [ -s "$1" ] || die "manca $(basename "$1"): lancia prima il modo che lo scrive"
  # shellcheck disable=SC1090
  . "$1"
}

# ---------------------------------------------------------------- cloni e PR

clone_or_update() { # protected | detect
  local n="$1" repo d
  repo="$(repo_of "$n")"; d="$WORK/$n"
  mkdir -p "$WORK"
  if [ -d "$d/.git" ]; then
    check_remote "$n" || die "il remoto di $n non è quello atteso: mi fermo"
    git -C "$d" fetch -q origin && git -C "$d" switch -q main && git -C "$d" merge -q --ff-only origin/main \
      || die "aggiornamento del clone di $n fallito"
  else
    gh_call "clone-$n" repo clone "$repo" "$d" -- -q
    [ "$RC" = 0 ] || die "clone di $repo fallito (vedi clone-$n.err)"
    if [ "$CHECK" = 1 ] && [ -n "${P4_GIT_BASE:-}" ]; then
      git -C "$d" remote set-url origin "$P4_GIT_BASE/$repo.git"
    fi
    git -C "$d" config user.name "tollgate-p4-probe"
    git -C "$d" config user.email "probe@example.invalid"
  fi
}

# ---------------------------------------------------------------- attese sui run

# wait_run <etichetta> <repo> <workflow> <sha> <ramo> <ripiego>
# Cerca il run per testa (sha o ramo); con ripiego=1 accetta anche il più recente creato negli ultimi minuti
# (pull_request_target e workflow_run non hanno la testa della PR come head_sha in modo garantito).
# Attende con un tetto di tempo (WAIT_MAX). Imposta RUN_ID e RUN_CONC; scrive <etichetta>-{runs,watch,view}.* e -runid.txt.
wait_run() {
  local label="$1" repo="$2" wf="$3" sha="$4" br="$5" fb="$6" since deadline id="" left
  since="$(date -u -d '-2 minutes' +%FT%TZ)"
  export P4_WAIT_SHA="$sha" P4_WAIT_BRANCH="$br"
  deadline=$(( $(date +%s) + WAIT_MAX ))
  RUN_ID=""; RUN_CONC=""
  while :; do
    gh_q run list --repo "$repo" --workflow "$wf" --limit 30 \
      --json databaseId,headSha,headBranch,event,status,conclusion,createdAt >"$WORK/poll.json"
    id="$(jq -r --arg s "$sha" --arg b "$br" --arg t "$since" --arg f "$fb" \
      '[.[] | select(.headSha == $s or ($b != "" and .headBranch == $b) or ($f == "1" and .createdAt >= $t))]
       | sort_by(.databaseId) | last | .databaseId // empty' "$WORK/poll.json" 2>/dev/null)"
    [ -n "$id" ] && break
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "run di $wf non comparso entro ${WAIT_MAX}s ($label)" >&2
      save_text "$OUT/$label-runid.txt" "non determinato: run non comparso entro ${WAIT_MAX}s"
      return 1
    fi
    sleep "$POLL"
  done
  left=$(( deadline - $(date +%s) )); [ "$left" -lt 30 ] && left=30
  GH_TIMEOUT="$left" gh_call "$label-watch" run watch "$id" --repo "$repo" --exit-status
  gh_call "$label-runs" run list --repo "$repo" --workflow "$wf" --limit 30 \
    --json databaseId,headSha,headBranch,event,status,conclusion,createdAt
  gh_call "$label-view" run view "$id" --repo "$repo" \
    --json databaseId,workflowName,event,headSha,headBranch,status,conclusion,createdAt,updatedAt,jobs
  RUN_ID="$id"
  RUN_CONC="$(jq -r '.conclusion // empty' "$OUT/$label-view.out" 2>/dev/null)"
  save_text "$OUT/$label-runid.txt" "$id"
  return 0
}

# track_run: wait_run + scarico degli artefatti del run
track_run() {
  wait_run "$@" || return 1
  gh_call "$1-download" run download "$RUN_ID" --repo "$2" -D "$OUT/$1-artifacts-$RUN_ID"
  return 0
}

# ---------------------------------------------------------------- stati, commenti e run di una PR (gate e flusso)

STATUS_JQ='.[] | {context, state, creator: .creator.login, description, created_at}'
COMMENT_JQ='.[] | {id, user: .user.login, body}'

# statuses <etichetta> <repo> <sha>: gli stati del commit dal più recente, con l'autore (verifica `--paginate --jq`)
statuses() {
  gh_call "$1" api --paginate "repos/$2/commits/$3/statuses?per_page=100" --jq "$STATUS_JQ"
}

# await_statuses <repo> <sha> <contesto...>: attende che ogni contesto abbia l'ultimo stato diverso da pending
await_statuses() {
  local repo="$1" sha="$2" c deadline complete; shift 2
  deadline=$(( $(date +%s) + WAIT_MAX ))
  while :; do
    gh_q api --paginate "repos/$repo/commits/$sha/statuses?per_page=100" --jq "$STATUS_JQ" >"$WORK/poll-statuses.jsonl"
    complete=1
    for c in "$@"; do
      jq -es --arg c "$c" 'map(select(.context == $c)) | .[0] | select(. != null and .state != "pending")' \
        "$WORK/poll-statuses.jsonl" >/dev/null 2>&1 || complete=0
    done
    [ "$complete" = 1 ] && return 0
    [ "$(date +%s)" -ge "$deadline" ] && { echo "stati non comparsi entro ${WAIT_MAX}s su $sha: $*" >&2; return 1; }
    sleep "$POLL"
  done
}

# await_comments <repo> <pr> <prefisso...>: attende che il bot abbia un commento che comincia con ogni prefisso
await_comments() {
  local repo="$1" pr="$2" p deadline complete; shift 2
  deadline=$(( $(date +%s) + WAIT_MAX ))
  while :; do
    gh_q api --paginate "repos/$repo/issues/$pr/comments?per_page=100" --jq "$COMMENT_JQ" >"$WORK/poll-comments.jsonl"
    complete=1
    for p in "$@"; do
      jq -es --arg p "$p" 'map(select(.user == "github-actions[bot]" and (.body | ltrimstr("\n") | startswith($p)))) | length > 0' \
        "$WORK/poll-comments.jsonl" 2>/dev/null | grep -q true || complete=0
    done
    [ "$complete" = 1 ] && return 0
    [ "$(date +%s)" -ge "$deadline" ] && { echo "commenti non comparsi entro ${WAIT_MAX}s sulla PR $pr: $*" >&2; return 1; }
    sleep "$POLL"
  done
}

# pr_runs <etichetta> <repo> <sha> <pr>: i run di guard, run e verdict che appartengono alla PR <pr>, con i minuti di Actions.
#  - tollgate-guard (pull_request_target) e tollgate-run (pull_request): `headSha` uguale allo SHA (V1 del Task 1) e il numero
#    della PR in `pull_requests` del run; un run senza quel numero resta fuori e si dichiara. Mai «il più recente».
#  - tollgate-verdict (workflow_run): ha `headSha` e `headBranch` del predefinito e nessuna PR in `pull_requests`; si aggancia
#    il run la cui durata contiene il momento dello stato `tollgate/verdict` scritto dal bot sullo SHA (nessun ripiego).
# Una riga per run: workflow, id, evento, conclusione, durata in ms, metodo di aggancio.
pr_runs() {
  local label="$1" repo="$2" sha="$3" pr="$4" wf id vts how
  export P4_WAIT_SHA="$sha" P4_WAIT_PR="$pr"
  rot "$OUT/$label-runs.tsv"
  : > "$OUT/$label-runs.tsv"
  vts="$(jq -rs 'map(select(.context == "tollgate/verdict" and .creator == "github-actions[bot]")) | .[0].created_at // empty' \
    "$OUT/$label-statuses.out" 2>/dev/null)"
  for wf in tollgate-guard.yml tollgate-run.yml tollgate-verdict.yml; do
    gh_q run list --repo "$repo" --workflow "$wf" --limit 50 \
      --json databaseId,headSha,event,status,conclusion,createdAt >"$WORK/pr-runs.json"
    if [ "$wf" = tollgate-verdict.yml ]; then
      [ -n "$vts" ] || { printf '%s\t-\t-\t-\t0\tnon determinato: nessuno stato verdict del bot\n' "$wf" >> "$OUT/$label-runs.tsv"; continue; }
      how="finestra del run contiene lo stato verdict ($vts)"
      for id in $(jq -r '.[].databaseId' "$WORK/pr-runs.json" 2>/dev/null); do
        gh_q api "repos/$repo/actions/runs/$id" >"$WORK/pr-run-$id.json"
        jq -e --arg t "$vts" '(.run_started_at | fromdateiso8601) - 2 <= ($t | fromdateiso8601)
                              and ($t | fromdateiso8601) <= (.updated_at | fromdateiso8601) + 2' \
          "$WORK/pr-run-$id.json" >/dev/null 2>&1 && pr_run_row "$label" "$repo" "$wf" "$id" "$how"
      done
    else
      how="headSha e numero della PR in pull_requests"
      for id in $(jq -r --arg s "$sha" '.[] | select(.headSha == $s) | .databaseId' "$WORK/pr-runs.json" 2>/dev/null); do
        gh_q api "repos/$repo/actions/runs/$id" >"$WORK/pr-run-$id.json"
        jq -e --argjson n "$pr" '[.pull_requests[]?.number] | index($n) != null' "$WORK/pr-run-$id.json" >/dev/null 2>&1 \
          && pr_run_row "$label" "$repo" "$wf" "$id" "$how" \
          || printf '%s\t%s\t-\t-\t0\tscartato: numero della PR assente da pull_requests\n' "$wf" "$id" >> "$OUT/$label-runs.tsv"
      done
    fi
  done
}

pr_run_row() { # <etichetta> <repo> <workflow> <id> <metodo>: attende il run, salva run e timing, aggiunge la riga
  GH_TIMEOUT=120 gh_call "$1-watch-$4" run watch "$4" --repo "$2"
  gh_call "$1-run-$4" api "repos/$2/actions/runs/$4"
  gh_call "$1-run-$4-timing" api "repos/$2/actions/runs/$4/timing"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$3" "$4" "$(jq -r '.event' "$OUT/$1-run-$4.out")" \
    "$(jq -r '.conclusion // "-"' "$OUT/$1-run-$4.out")" \
    "$(jq -r '.run_duration_ms // 0' "$OUT/$1-run-$4-timing.out")" "$5" >> "$OUT/$1-runs.tsv"
}

