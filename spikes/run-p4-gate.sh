#!/usr/bin/env bash
# spikes/run-p4-gate.sh — prova reale del gate di P4 su GitHub (Task 16, criteri 10, 11 e 34), decisione 25.
# Lo esegue solo il controller. Modo `controlla`: nessuna rete, `gh` finto davanti nel PATH.
# Uso: run-p4-gate.sh elenco | installa <protected|detect> | protezione | caso <nome> | raccogli | controlla
#
#   elenco              i casi (nome, repo, esito atteso, descrizione), senza rete
#   installa <repo>     progetto di prova sul predefinito, `bin/tollgate init --propose` nel clone, copia di files/,
#                       commit su main, attesa di tollgate-base (miss), poi un commit vuoto e una seconda attesa
#                       (hit della cache). Su protected il codice di tollgate diventa pubblico: serve
#                       P4_CONFERMA_PUBBLICO=1, che il controller imposta dopo averlo detto all'utente.
#   protezione          solo protected: `protect.sh` sullo SHA di tollgate-base (decisione 18)
#   caso <nome>         issue, ramo, PR; attesa degli stati (tetto P4_WAIT_MAX, 900 s), raccolta di stati con autore,
#                       commenti, mergeStateStatus, forma di GET pulls/<n>, run e minuti; riga del rapporto
#   raccogli            run, PR e minuti di Actions dei due repo, controllo del registro dei comandi
#   controlla           nessuna rete: tutti i modi su repo nudi locali con un gh finto, e ogni gh passato da ghguard.py
#
# Lezione dell'incidente di P0: nessuna cartella di uscite si cancella mai. Le uscite stanno in
# docs/verifiche/evidenze/gh-p4/; un file che esiste già si rinomina in <nome>.prev-<tempo>. Prima di ogni git che
# parla con la rete lo script controlla `git remote get-url --push origin`; ogni gh passa da ghguard.py.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
GH4="$here/gh-p4"
P4="$here/p4"
MODE="${1:-}"

OWNER=ginz0ls
PROT="$OWNER/tollgate-p4-protected"   # pubblico, modalità protected
DET="$OWNER/tollgate-p4-detect"       # privato, GitHub Free, modalità detect
OUT="${P4_OUT:-$root/docs/verifiche/evidenze/gh-p4}"
WORK="${P4_WORK:-/tmp/tollgate-p4/gh}"   # cloni di lavoro, non sono uscite
export P4_OUT="$OUT" P4_WORK="$WORK"
WAIT_MAX="${P4_WAIT_MAX:-900}"           # tetto di attesa degli stati di una PR, in secondi (15 minuti)
POLL="${P4_POLL:-10}"
RETRY_SLEEP="${P4_RETRY_SLEEP:-5}"
SLEEP_SCALE="${P4_SLEEP_SCALE:-1}"
CHECK="${P4_CHECK:-0}"                   # 1 solo dentro il modo controlla
STATE_DIR="$WORK/state"                  # stato di tollgate per init: cartella di prova con la sentinella

. "$GH4/common.sh"

SENTINEL_TITLE='tollgate: merge non verificato'

# ---------------------------------------------------------------- utilità

# with_guarded_gh <repo protected|detect> <comando...>: il `gh` dei programmi figli (tollgate init, protect.sh) è il
# wrapper con guardia; il gh vero lo conosce da P4_REAL_GH. Lo stato di tollgate è una cartella di prova.
with_guarded_gh() {
  local n="$1" real; shift
  real="$(command -v gh)" || die "gh non trovato"
  mkdir -p "$STATE_DIR"; : > "$STATE_DIR/.tollgate-test"
  env -u TOLLGATE_GH TOLLGATE_STATE="$STATE_DIR" P4_REAL_GH="$real" P4_REPO="$(repo_of "$n")" \
      P4_LOG="$OUT/comandi.log" PATH="$GH4/bin:$PATH" "$@"
}

require_tools() {
  local t
  for t in jq git python3; do command -v "$t" >/dev/null 2>&1 || die "manca $t"; done
}

ci_number() { # <url o testo> -> numero in coda (PR o issue)
  local url n
  url="$(tail -n 1 "$1")"
  n="${url##*/}"
  case "$n" in ''|*[!0-9]*) die "numero non leggibile da: $url" ;; esac
  echo "$n"
}

mode_installed() { # <protected|detect>: i workflow di tollgate sono su origin/main del clone
  git -C "$WORK/$1" cat-file -e "origin/main:.github/workflows/tollgate-guard.yml" 2>/dev/null
}

wait_job_conclusion() { # <file view.out> -> conclusione del job tollgate-base (o vuoto)
  jq -r '[.jobs[]? | select(.name == "tollgate-base") | .conclusion] | first // empty' "$1" 2>/dev/null
}

# ---------------------------------------------------------------- installa

modo_installa() {
  local n="${1:-}" repo d sha prop f mode_line
  INSTALL_FAIL=0
  case "$n" in protected|detect) ;; *) die "uso: $0 installa <protected|detect>" ;; esac
  require_tools
  repo="$(repo_of "$n")"; d="$WORK/$n"
  if [ "$n" = protected ] && [ "${P4_CONFERMA_PUBBLICO:-0}" != 1 ]; then
    die "su protected il codice di tollgate (la copia del CLI in .github/tollgate) diventa pubblico: dillo all'utente e rilancia con P4_CONFERMA_PUBBLICO=1"
  fi
  clone_or_update "$n"
  check_remote "$n" || die "il remoto di $n non è quello atteso: mi fermo"
  mkdir -p "$d/.git/info"
  grep -qx 'docs/superpowers/tollgate-init/' "$d/.git/info/exclude" 2>/dev/null \
    || echo 'docs/superpowers/tollgate-init/' >> "$d/.git/info/exclude"
  if git -C "$d" cat-file -e origin/main:tollgate.toml 2>/dev/null; then
    save_text "$OUT/installa-$n-progetto.txt" "progetto di prova già sul predefinito: $(git -C "$d" rev-parse origin/main)"
  else
    rot "$OUT/installa-$n-baseline-file.txt"
    python3 -B "$P4/make_case.py" baseline "$n" "$d" >"$OUT/installa-$n-baseline-file.txt" || die "file del progetto non scritti"
    git -C "$d" add -A && git -C "$d" commit -qm "progetto di prova del gate (tollgate P4)" || die "commit del progetto fallito"
    git_call "installa-$n-push-progetto" "$n" push origin main
    [ "$RC" = 0 ] || die "push del progetto fallito (vedi installa-$n-push-progetto.err)"
  fi
  # init legge origin/main: la proposta usa il tollgate.toml del progetto
  git_call "installa-$n-fetch" "$n" fetch -q origin
  rot "$OUT/installa-$n-init.out" "$OUT/installa-$n-init.err" "$OUT/installa-$n-init.rc"
  log_cmd "tollgate init --propose (cwd $n)"
  ( cd "$d" && with_guarded_gh "$n" python3 -B "$root/bin/tollgate" init --propose --merges-per-month 20 ) \
    >"$OUT/installa-$n-init.out" 2>"$OUT/installa-$n-init.err" </dev/null
  echo "$?" >"$OUT/installa-$n-init.rc"
  [ "$(cat "$OUT/installa-$n-init.rc")" = 0 ] || die "tollgate init --propose rifiutato (vedi installa-$n-init.out e .err)"
  prop="$d/docs/superpowers/tollgate-init"
  [ -d "$prop/files" ] || die "la proposta non ha files/"
  rot "$OUT/installa-$n-proposta"
  mkdir -p "$OUT/installa-$n-proposta"
  for f in README.md protection.json protect.sh; do [ -e "$prop/$f" ] && cp "$prop/$f" "$OUT/installa-$n-proposta/$f"; done
  ( cd "$prop/files" && find . -type f | sort ) >"$OUT/installa-$n-proposta/elenco-files.txt"
  mode_line="$(grep -E '^mode *=' "$prop/files/tollgate.toml" | head -n 1)"
  save_text "$OUT/installa-$n-modo.txt" "tollgate.toml della proposta: $mode_line" \
    "protect.sh: $([ -e "$prop/protect.sh" ] && echo presente || echo assente)"
  case "$n:$mode_line" in
    protected:*'"protected"'*) [ -e "$prop/protect.sh" ] || die "protected senza protect.sh nella proposta" ;;
    detect:*'"detect"'*) [ ! -e "$prop/protect.sh" ] || die "detect con un protect.sh nella proposta" ;;
    *) die "modalità della proposta inattesa per $n: $mode_line" ;;
  esac
  if git -C "$d" cat-file -e origin/main:.github/workflows/tollgate-guard.yml 2>/dev/null; then
    save_text "$OUT/installa-$n-commit.txt" "tollgate già installato su origin/main: $(git -C "$d" rev-parse origin/main)"
  else
    cp -R "$prop/files/." "$d/" || die "copia di files/ fallita"
    git -C "$d" add -A && git -C "$d" commit -qm "installa tollgate (P4)" || die "commit dell'installazione fallito"
    sha="$(git -C "$d" rev-parse HEAD)"
    git_call "installa-$n-push-installazione" "$n" push origin main
    [ "$RC" = 0 ] || die "push dell'installazione fallito (vedi installa-$n-push-installazione.err)"
    save_text "$OUT/installa-$n-commit.txt" "$sha"
    installa_attese "$n" "$repo" "$sha" miss
    # secondo commit sullo stesso albero: hit della cache di tollgate-base
    git -C "$d" commit -q --allow-empty -m "commit vuoto: stesso albero, hit della cache (P4)" || die "commit vuoto fallito"
    sha="$(git -C "$d" rev-parse HEAD)"
    git_call "installa-$n-push-vuoto" "$n" push origin main
    [ "$RC" = 0 ] || die "push del commit vuoto fallito (vedi installa-$n-push-vuoto.err)"
    save_text "$OUT/installa-$n-commit-vuoto.txt" "$sha"
    installa_attese "$n" "$repo" "$sha" hit
  fi
  return "$INSTALL_FAIL"
}

# close_sentinel_issues <etichetta> <repo>: le issue aperte di sentinel si chiudono, perché `sentinel_open` è una voce di
# `attenzione` di ogni PR successiva; le chiude lo script (decisione 25: `issue close`), dopo averle registrate
close_sentinel_issues() {
  local label="$1" repo="$2" c
  gh_call "$label-issue-list" issue list --repo "$repo" --state open --limit 100 --json number,title
  for c in $(jq -r --arg t "$SENTINEL_TITLE" '.[] | select(.title == $t) | .number' "$OUT/$label-issue-list.out" 2>/dev/null); do
    gh_call "$label-issue-$c" issue view "$c" --repo "$repo" --json number,title,comments
    gh_call "$label-issue-$c-close" issue close "$c" --repo "$repo"
  done
}

# installa_attese <n> <repo> <sha> <miss|hit>: tollgate-base e tollgate-sentinel sullo SHA, stati e issue di sentinel.
# Il primo push (miss) non apre l'issue (criterio 34). Il secondo è un commit vuoto spinto direttamente: sentinel lo
# segnala (nessuna PR) e apre l'issue; si registra e si chiude, così non pesa sui casi che seguono.
installa_attese() {
  local n="$1" repo="$2" sha="$3" kind="$4" label="installa-$n-$4" count verdict34
  wait_run "$label-base" "$repo" tollgate-base.yml "$sha" "" 0 \
    || echo "tollgate-base non completato su $sha ($kind)" >&2
  [ -f "$OUT/$label-base-view.out" ] && save_text "$OUT/$label-base-conclusione.txt" \
    "tollgate-base su $sha ($kind): job $(wait_job_conclusion "$OUT/$label-base-view.out"), run $RUN_CONC"
  wait_run "$label-sentinel" "$repo" tollgate-sentinel.yml "$sha" "" 0 || echo "tollgate-sentinel non completato su $sha" >&2
  statuses "$label-statuses" "$repo" "$sha"
  if [ "$kind" = miss ]; then
    gh_call "$label-issue-list" issue list --repo "$repo" --state open --limit 100 --json number,title
    count="$(jq --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | length' "$OUT/$label-issue-list.out" 2>"$OUT/$label-issue-sentinel.jqerr")"
    if [ "$count" = 0 ]; then verdict34="riuscito"
    else verdict34="non riuscito (conteggio: '${count:-illeggibile}', vedi $label-issue-sentinel.jqerr)"; INSTALL_FAIL=1; fi
    save_text "$OUT/$label-issue-sentinel.txt" "criterio 34, issue di sentinel aperte dopo il primo push: ${count:-?} (atteso 0): $verdict34"
    echo "criterio 34 ($n): $verdict34"
  else
    fake_sentinel on
    close_sentinel_issues "$label" "$repo"
    fake_sentinel off
  fi
}

# fake_sentinel on|off: solo nel modo controlla, il gh finto mostra o no un'issue di sentinel aperta
fake_sentinel() {
  [ "$CHECK" = 1 ] || return 0
  mkdir -p "$P4_FAKE_STATE"
  if [ "$1" = on ]; then : > "$P4_FAKE_STATE/sentinel"; else rm -f "$P4_FAKE_STATE/sentinel"; fi
}

# ---------------------------------------------------------------- protezione

modo_protezione() {
  local d="$WORK/protected" sha
  require_tools
  mode_installed protected || [ -d "$d/docs/superpowers/tollgate-init" ] || die "lancia prima: installa protected"
  clone_or_update protected
  check_remote protected || die "il remoto di protected non è quello atteso: mi fermo"
  [ -f "$d/docs/superpowers/tollgate-init/protect.sh" ] || die "manca protect.sh: lancia prima installa protected"
  git_call protezione-fetch protected fetch -q origin
  sha="$(git -C "$d" rev-parse origin/main)"
  rot "$OUT/protezione-protect.out" "$OUT/protezione-protect.err" "$OUT/protezione-protect.rc"
  log_cmd "bash docs/superpowers/tollgate-init/protect.sh $sha (cwd protected)"
  ( cd "$d" && with_guarded_gh protected bash docs/superpowers/tollgate-init/protect.sh "$sha" ) \
    >"$OUT/protezione-protect.out" 2>"$OUT/protezione-protect.err" </dev/null
  echo "$?" >"$OUT/protezione-protect.rc"
  save_text "$OUT/protezione-sha.txt" "$sha"
  gh_call protezione-get api "repos/$PROT/branches/main/protection"
  [ "$(cat "$OUT/protezione-protect.rc")" = 0 ] || die "protect.sh non riuscito (vedi protezione-protect.err)"
}

# ---------------------------------------------------------------- caso

case_field() { jq -r "$1" "$CASEJSON"; }

# run_ops: esegue le operazioni del caso in ordine; imposta SHA[id], PUSHBR[id], PRN[ramo]
run_ops() {
  local label="$1" repo="$2" n="$3" k=0 i count op id br sha base title body pr state
  count="$(jq '.ops | length' "$CASEJSON")"
  for ((i = 0; i < count; i++)); do
    op="$(jq -r ".ops[$i].op" "$CASEJSON")"
    case "$op" in
      push)
        id="$(jq -r ".ops[$i].id" "$CASEJSON")"; br="$(jq -r ".ops[$i].branch" "$CASEJSON")"; sha="$(jq -r ".ops[$i].sha" "$CASEJSON")"
        if [ "$br" = main ] && [ "$n" != detect ]; then die "mai un push diretto su main di $n"; fi
        git_call "$label-push-$id" "$n" push origin "$sha:refs/heads/$br"
        [ "$RC" = 0 ] || die "push di $br fallito (vedi $label-push-$id.err)"
        SHA[$id]="$sha"; PUSHBR[$id]="$br" ;;
      pr)
        br="$(jq -r ".ops[$i].branch" "$CASEJSON")"; base="$(jq -r ".ops[$i].base" "$CASEJSON")"
        title="$(jq -r ".ops[$i].title" "$CASEJSON")"; body="$(jq -r ".ops[$i].body_file" "$CASEJSON")"
        k=$((k + 1))
        gh_call "$label-pr-create-$k" pr create --repo "$repo" --base "$base" --head "$br" --title "$title" --body-file "$body"
        [ "$RC" = 0 ] || die "creazione della PR fallita (vedi $label-pr-create-$k.err)"
        PRN[$br]="$(ci_number "$OUT/$label-pr-create-$k.out")" ;;
      sleep) sleep $(( $(jq -r ".ops[$i].s" "$CASEJSON") * SLEEP_SCALE )) ;;
      wait)
        id="$(jq -r ".ops[$i].push" "$CASEJSON")"
        seed_fake "$label" "$id" "${SHA[$id]}" "${PRN[${PUSHBR[$id]}]:-0}"
        await_statuses "$repo" "${SHA[$id]}" $(expected_contexts "$id") || echo "attesa anticipata non riuscita per $id" >&2 ;;
      edit)
        br="$(jq -r ".ops[$i].branch" "$CASEJSON")"; pr="${PRN[$br]:-}"; [ -n "$pr" ] || die "edit senza PR per $br"
        # il corpo con la REST: `gh pr edit` esce con 1 con gh 2.46 (Projects classic); è la forma di bin/tollgate_flow/gh.py
        gh_call "$label-pr-edit" api --method PATCH "repos/$repo/pulls/$pr" -F "body=@$(jq -r ".ops[$i].body_file" "$CASEJSON")"
        [ "$RC" = 0 ] || die "modifica della PR fallita (vedi $label-pr-edit.err)" ;;
      wait_count)
        id="$(jq -r ".ops[$i].push" "$CASEJSON")"
        await_status_count "$repo" "${SHA[$id]}" "$(jq -r ".ops[$i].context" "$CASEJSON")" "$(jq -r ".ops[$i].n" "$CASEJSON")" \
          || echo "attesa del secondo stato non riuscita per $id" >&2 ;;
      post_status)
        id="$(jq -r ".ops[$i].push" "$CASEJSON")"
        gh_call "$label-post-status-$id" api --method POST "repos/$repo/statuses/${SHA[$id]}" \
          -f "state=$(jq -r ".ops[$i].state" "$CASEJSON")" -f "context=$(jq -r ".ops[$i].context" "$CASEJSON")" \
          -f "description=prova-token-personale-p4"
        [ "$RC" = 0 ] || die "POST dello stato fallito (vedi $label-post-status-$id.err)" ;;
      merge)
        id="$(jq -r ".ops[$i].id" "$CASEJSON")"; br="$(jq -r ".ops[$i].branch" "$CASEJSON")"
        pr="${PRN[$br]:-}"; [ -n "$pr" ] || die "merge senza PR per $br"
        gh_call "$label-pr-state-$id" pr view "$pr" --repo "$repo" --json state,mergedAt
        state="$(jq -r '.state' "$OUT/$label-pr-state-$id.out" 2>/dev/null)"
        if [ "$state" = MERGED ]; then
          echo "PR $pr già unita: non ripeto il merge" >&2
        else
          gh_call "$label-merge-$id" pr merge "$pr" --repo "$repo" "$(jq -r ".ops[$i].mode" "$CASEJSON")"
          [ "$RC" = 0 ] || die "merge della PR $pr fallito (vedi $label-merge-$id.err)"
        fi
        git_call "$label-fetch-$id" "$n" fetch -q origin
        SHA[$id]="$(git -C "$WORK/$n" rev-parse origin/main)"; PUSHBR[$id]="$br" ;;
      direct)
        id="$(jq -r ".ops[$i].id" "$CASEJSON")"
        [ "$n" = detect ] || die "mai un push diretto su main di $n"
        git_call "$label-fetch-$id" "$n" fetch -q origin
        git -C "$WORK/$n" switch -q --detach origin/main || die "checkout di origin/main fallito"
        mkdir -p "$(dirname "$WORK/$n/$(jq -r ".ops[$i].file" "$CASEJSON")")"
        jq -r ".ops[$i].text" "$CASEJSON" > "$WORK/$n/$(jq -r ".ops[$i].file" "$CASEJSON")"
        git -C "$WORK/$n" add "$(jq -r ".ops[$i].file" "$CASEJSON")" \
          && git -C "$WORK/$n" commit -qm "push diretto su main (tollgate P4)" || die "commit del push diretto fallito"
        SHA[$id]="$(git -C "$WORK/$n" rev-parse HEAD)"; PUSHBR[$id]=main
        git_call "$label-push-$id" "$n" push origin "HEAD:refs/heads/main"
        [ "$RC" = 0 ] || die "push diretto fallito (vedi $label-push-$id.err)" ;;
      *) die "operazione sconosciuta: $op" ;;
    esac
  done
}

# await_status_count <repo> <sha> <contesto> <n>: attende almeno n stati di quel contesto (una nuova valutazione dello stesso SHA
# scrive uno stato nuovo); nel modo controlla il finto non ne produce di nuovi e non si attende
await_status_count() {
  local repo="$1" sha="$2" c="$3" n="$4" deadline got
  [ "$CHECK" != 1 ] || return 0
  deadline=$(( $(date +%s) + WAIT_MAX ))
  while :; do
    got="$(gh_q api --paginate "repos/$repo/commits/$sha/statuses?per_page=100" --jq "$STATUS_JQ" | jq -s --arg c "$c" '[.[] | select(.context == $c)] | length' 2>/dev/null)"
    [ "${got:-0}" -ge "$n" ] && return 0
    [ "$(date +%s)" -ge "$deadline" ] && return 1
    sleep "$POLL"
  done
}

# expected_contexts <id>: i contesti con uno stato atteso preciso (né none né *) per quel push
expected_contexts() {
  jq -r --arg id "$1" '.expect[] | select(.push == $id) | .states | to_entries[] | select(.value != "none" and .value != "*") | .key' "$CASEJSON"
}

# seed_fake <etichetta> <id> <sha> <pr>: solo nel modo controlla, il gh finto risponde con gli stati attesi
seed_fake() {
  [ "$CHECK" = 1 ] || return 0
  local f="$P4_FAKE_STATE/seed-$3"
  mkdir -p "$P4_FAKE_STATE"
  jq -c --arg id "$2" --arg sha "$3" '.expect[] | select(.push == $id) | .states | to_entries[]
    | select(.value != "none" and .value != "*") | {context: .key, state: .value, creator: "github-actions[bot]", description: "finto", created_at: "2099-01-01T00:00:00Z"}' \
    "$CASEJSON" > "$f.statuses"
  jq -c --arg id "$2" '.expect[] | select(.push == $id) | .comments[]' "$CASEJSON" > "$f.comments"
  jq -r --arg id "$2" '.expect[] | select(.push == $id) | .merge_state // empty' "$CASEJSON" > "$f.merge"
  printf '%s\n' "$4" > "$f.pr"
  export P4_FAKE_SEED="$f"
}

# sentinel_wait <repo> <commenti minimi>: attende l'unica issue aperta di sentinel con almeno tanti commenti (tetto WAIT_MAX)
sentinel_wait() {
  local repo="$1" min="$2" deadline num cmt
  deadline=$(( $(date +%s) + WAIT_MAX ))
  while :; do
    num="$(gh_q issue list --repo "$repo" --state open --limit 100 --json number,title \
      | jq -r --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | first | .number // empty' 2>/dev/null)"
    if [ -n "$num" ]; then
      cmt="$(gh_q issue view "$num" --repo "$repo" --json comments | jq '.comments | length' 2>/dev/null)"
      [ "${cmt:-0}" -ge "$min" ] && return 0
    fi
    [ "$(date +%s)" -ge "$deadline" ] && { echo "issue di sentinel non comparsa (o senza commenti) entro ${WAIT_MAX}s" >&2; return 1; }
    sleep "$POLL"
  done
}

# collect_judged <etichetta> <repo> <n> <id>: attende, raccoglie e giudica uno SHA spinto
collect_judged() {
  local label="$1" repo="$2" n="$3" id="$4" sha br pr merge="" sent="" cmt="" want_merge want_sent want_cmt tries row rc=0 c; local -a prefixes=()
  sha="${SHA[$id]:-}"; [ -n "$sha" ] || { echo "nessuno SHA per $id" >&2; return 1; }
  br="${PUSHBR[$id]}"; pr="${PRN[$br]:-}"
  seed_fake "$label" "$id" "$sha" "${pr:-0}"
  # shellcheck disable=SC2046
  await_statuses "$repo" "$sha" $(expected_contexts "$id") || echo "attesa degli stati non riuscita per $id" >&2
  if [ -n "$pr" ]; then
    mapfile -t prefixes < <(jq -r --arg id "$id" '.expect[] | select(.push == $id) | .comments[]' "$CASEJSON")   # i prefissi hanno spazi
    await_comments "$repo" "$pr" "${prefixes[@]}" || echo "attesa dei commenti non riuscita per $id" >&2
  fi
  statuses "$label-$id-statuses" "$repo" "$sha"
  if [ -n "$pr" ]; then
    gh_call "$label-$id-comments" api --paginate "repos/$repo/issues/$pr/comments?per_page=100" --jq "$COMMENT_JQ"
    gh_call "$label-$id-pulls" api "repos/$repo/pulls/$pr"          # forma di GET pulls/<n> letta da verdict
    pr_runs "$label-$id" "$repo" "$sha" "$pr"
  fi
  want_merge="$(jq -r --arg id "$id" '.expect[] | select(.push == $id) | .merge_state // empty' "$CASEJSON")"
  if [ -n "$want_merge" ] && [ -n "$pr" ]; then
    for tries in 1 2 3 4 5 6; do
      gh_call "$label-$id-merge-state" pr view "$pr" --repo "$repo" --json mergeStateStatus,state,headRefOid
      merge="$(jq -r '.mergeStateStatus // empty' "$OUT/$label-$id-merge-state.out" 2>/dev/null)"
      [ -n "$merge" ] && [ "$merge" != UNKNOWN ] && break
      sleep "$RETRY_SLEEP"
    done
  fi
  want_sent="$(jq -r --arg id "$id" '.expect[] | select(.push == $id) | .sentinel_issue // empty' "$CASEJSON")"
  want_cmt="$(jq -r --arg id "$id" '.expect[] | select(.push == $id) | .sentinel_comments_min // 0' "$CASEJSON")"
  if [ -n "$want_sent" ]; then
    # sentinel scrive prima gli stati e poi l'issue o il commento: si attende che l'issue ci sia (con i commenti attesi)
    fake_sentinel on
    sentinel_wait "$repo" "$want_cmt"
    gh_call "$label-$id-issue-list" issue list --repo "$repo" --state open --limit 100 --json number,title
    sent="$(jq --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | length' "$OUT/$label-$id-issue-list.out" 2>/dev/null)"
    for c in $(jq -r --arg t "$SENTINEL_TITLE" '.[] | select(.title == $t) | .number' "$OUT/$label-$id-issue-list.out" 2>/dev/null); do
      gh_call "$label-$id-issue-$c" issue view "$c" --repo "$repo" --json number,title,comments
      cmt="$(jq '.comments | length' "$OUT/$label-$id-issue-$c.out" 2>/dev/null)"
    done
  fi
  row="$(python3 -B "$P4/make_case.py" judge "$CASEJSON" --push "$id" --statuses "$OUT/$label-$id-statuses.out" \
    --comments "$OUT/$label-$id-comments.out" ${merge:+--merge "$merge"} ${sent:+--sentinel-issues "$sent"} ${cmt:+--sentinel-comments "$cmt"} \
    --pr "${pr:-$id}" --sha "$sha")" || rc=$?
  rot "$OUT/$label-$id-riga.md"
  printf '%s\n' "$row" > "$OUT/$label-$id-riga.md"
  printf '%s\n' "$row" >> "$OUT/casi-righe.md"
  echo "$row"
  return "$rc"
}

modo_caso() {
  local name="${1:-}" kind n repo ts label d issue="" extra="" fail=0 id br pr
  [ -n "$name" ] || die "uso: $0 caso <nome> (vedi: $0 elenco)"
  require_tools
  kind="$(python3 -B "$P4/make_case.py" list | awk -F'\t' -v c="$name" '$1 == c {print $2}')"
  [ -n "$kind" ] || die "caso sconosciuto: $name"
  n="$kind"; repo="$(repo_of "$n")"; d="$WORK/$n"
  clone_or_update "$n"
  mode_installed "$n" || die "tollgate non è installato su $n: lancia prima installa $n"
  ts="$(date +%Y%m%d-%H%M%S)"; label="caso-$name-$ts"
  CASEJSON="$OUT/$label-case.json"
  declare -gA SHA=() PUSHBR=() PRN=()
  # l'issue del caso (e per il caso «Closes» una seconda issue, chiusa prima di aprire la PR)
  gh_call "$label-issue-create" issue create --repo "$repo" --title "prova P4: $name" --body "issue di prova del gate (tollgate P4, caso $name), da chiudere"
  [ "$RC" = 0 ] || die "creazione dell'issue fallita (vedi $label-issue-create.err)"
  issue="$(ci_number "$OUT/$label-issue-create.out")"
  if [ "$name" = detect-closes ]; then
    gh_call "$label-issue-extra-create" issue create --repo "$repo" --title "prova P4: $name (chiusa)" --body "issue di prova, chiusa subito"
    [ "$RC" = 0 ] || die "creazione della seconda issue fallita"
    extra="$(ci_number "$OUT/$label-issue-extra-create.out")"
    gh_call "$label-issue-extra-close" issue close "$extra" --repo "$repo"
  fi
  git -C "$d" switch -q --detach origin/main || die "checkout di origin/main fallito"
  python3 -B "$P4/make_case.py" build "$name" --clone "$d" --issue "$issue" ${extra:+--extra-issue "$extra"} \
    --ts "$ts" --out "$OUT" --label "$label" >"$OUT/$label-build.txt" 2>&1 || { cat "$OUT/$label-build.txt" >&2; die "costruzione del caso fallita"; }
  save_text "$OUT/$label-descrizione.txt" "caso: $name" "repo: $repo" "issue: #$issue${extra:+ (extra #$extra)}" \
    "attesa: $(python3 -B "$P4/make_case.py" list | awk -F'\t' -v c="$name" '$1 == c {print $3 " - " $4}')"
  run_ops "$label" "$repo" "$n"
  for id in $(jq -r '.expect[].push' "$CASEJSON"); do
    collect_judged "$label" "$repo" "$n" "$id" || fail=1
  done
  # chiusura: le PR aperte si chiudono (le unite no), l'issue del caso si chiude
  for br in "${!PRN[@]}"; do
    pr="${PRN[$br]}"
    gh_call "$label-close-state-$pr" pr view "$pr" --repo "$repo" --json state
    [ "$(jq -r '.state' "$OUT/$label-close-state-$pr.out" 2>/dev/null)" = OPEN ] && gh_call "$label-pr-close-$pr" pr close "$pr" --repo "$repo"
  done
  gh_call "$label-issue-close" issue close "$issue" --repo "$repo"
  if jq -e '[.expect[].sentinel_issue] | any(. != null)' "$CASEJSON" >/dev/null 2>&1; then
    close_sentinel_issues "$label-fine" "$repo"
    fake_sentinel off
  fi
  git -C "$d" switch -q main 2>/dev/null
  save_text "$OUT/$label-esito.txt" "$([ "$fail" = 0 ] && echo riuscito || echo "non riuscito (vedi le righe sopra)")"
  return "$fail"
}

# ---------------------------------------------------------------- raccogli

modo_raccogli() {
  local repo n id ids tot
  require_tools
  gh_call raccogli-versione-gh --version
  for n in protected detect; do
    repo="$(repo_of "$n")"
    gh_call "raccogli-$n-runs" run list --repo "$repo" --limit 200 \
      --json databaseId,workflowName,event,headSha,headBranch,status,conclusion,createdAt,updatedAt
    gh_call "raccogli-$n-pr" pr list --repo "$repo" --state all --limit 200 \
      --json number,title,state,headRefName,headRefOid,baseRefName,mergedAt,isCrossRepository,mergeStateStatus
    ids="$(jq -r '.[].databaseId' "$OUT/raccogli-$n-runs.out" 2>/dev/null)"
    for id in $ids; do gh_call "raccogli-$n-timing-$id" api "repos/$repo/actions/runs/$id/timing"; done
    rot "$OUT/raccogli-$n-minuti.txt"
    {
      echo "run sul repo $n: $(echo "$ids" | grep -c .)"
      for id in $ids; do cat "$OUT/raccogli-$n-timing-$id.out" 2>/dev/null; echo; done \
        | jq -s '{run: length, run_duration_ms_totale: ([.[].run_duration_ms // 0] | add),
                  fatturati_ubuntu_ms: ([.[].billable.UBUNTU.total_ms // 0] | add)}' 2>&1
    } > "$OUT/raccogli-$n-minuti.txt"
  done
  rot "$OUT/raccogli-comandi-controllo.txt"
  env -u P4_OUT P4_WORK="$WORK" python3 -B -I "$GH4/ghguard.py" comandi "$OUT/comandi.log" > "$OUT/raccogli-comandi-controllo.txt" 2>&1 \
    || echo "comandi.log: righe non ammesse (vedi raccogli-comandi-controllo.txt)" >&2
}

modo_elenco() { python3 -B "$P4/make_case.py" list; }

# ---------------------------------------------------------------- controlla (nessuna rete)

write_fake_gh() { # <file>: il gh finto condiviso con run-p4-flow.sh
  cp "$GH4/fakegh.sh" "$1" && chmod +x "$1"
}

modo_controlla() {
  local T mode name rc=0 n url f
  bash -n "$here/run-p4-gate.sh" || die "bash -n fallito"
  T="${P4_CHECK_DIR:-$(mktemp -d /tmp/tollgate-p4-gate-controlla.XXXXXX)}"
  mkdir -p "$T/bin" "$T/remote" "$T/out" "$T/work"
  write_fake_gh "$T/bin/gh"
  export P4_CHECK=1 P4_OUT="$T/out" P4_WORK="$T/work" P4_GIT_BASE="$T/remote" \
         P4_FAKE_LOG="$T/gh.log" P4_FAKE_STATE="$T/fake" P4_WAIT_MAX=5 P4_POLL=0 P4_RETRY_SLEEP=0 P4_SLEEP_SCALE=0
  export PATH="$T/bin:$PATH"
  [ "$(command -v gh)" = "$T/bin/gh" ] || die "il gh finto non è il primo nel PATH"
  : > "$P4_FAKE_LOG"
  echo "cartella del controllo: $T"
  # i due repo «esistono già»: repo nudi locali con un README, come dopo il Task 1
  for n in protected detect; do
    local bare="$T/remote/$(repo_of "$n").git" tmp
    mkdir -p "$(dirname "$bare")"; git init -q --bare -b main "$bare"
    tmp="$(mktemp -d)"; git clone -q "$bare" "$tmp/s" 2>/dev/null
    echo "# $n" > "$tmp/s/README.md"; git -C "$tmp/s" add README.md
    git -C "$tmp/s" -c user.name=fake -c user.email=fake@example.invalid commit -qm init
    git -C "$tmp/s" branch -M main; git -C "$tmp/s" push -q origin main
  done
  echo "--- elenco dei casi"
  modo_elenco | cut -f1,2,3 | sed 's/^/  /'
  echo "--- modi"
  run_mode() { # <etichetta> <argomenti...>
    local label="$1"; shift
    if P4_CONFERMA_PUBBLICO=1 bash "$here/run-p4-gate.sh" "$@" >"$T/modo-$label.log" 2>&1; then
      echo "modo $label: ok"
    else
      echo "modo $label: FALLITO (vedi $T/modo-$label.log)"; tail -n 5 "$T/modo-$label.log"; rc=1
    fi
  }
  run_mode installa-protected installa protected
  run_mode installa-detect installa detect
  run_mode protezione protezione
  while IFS=$'\t' read -r name _; do
    # P4_CHECK_CASES: solo questi casi (separati da spazi); il test della suite ne prova una scelta
    [ -z "${P4_CHECK_CASES:-}" ] || case " $P4_CHECK_CASES " in *" $name "*) ;; *) continue ;; esac
    run_mode "caso-$name" caso "$name"
  done < <(modo_elenco)
  run_mode raccogli raccogli
  echo "--- attese andate a tetto nei modi (nel banco di prova non devono esserci)"
  if grep -l "non riuscita\|non comparsi\|non comparsa\|non completato\|non determinato" "$T"/modo-*.log 2>/dev/null; then rc=1; else echo "  nessuna"; fi
  echo "--- registro dei comandi gh"
  python3 -B -I "$GH4/ghguard.py" log "$P4_FAKE_LOG" || rc=1
  echo "--- comandi.log delle uscite (ogni gh passa da ghguard.py)"
  env -u P4_OUT P4_WORK="$T/work" python3 -B -I "$GH4/ghguard.py" comandi "$T/out/comandi.log" > "$T/comandi-controllo.txt" 2>&1 || rc=1
  sed 's/^/  /' "$T/comandi-controllo.txt"
  grep -c RIFIUTATO "$T/out/comandi.log" | sed 's/^/  righe RIFIUTATO nel registro: /'
  grep -q RIFIUTATO "$T/out/comandi.log" && rc=1
  echo "--- protect.sh: corpo della PUT"
  if ls "$T/fake"/put-body-*.json >/dev/null 2>&1; then
    f="$(ls "$T/fake"/put-body-*.json | tail -n 1)"
    jq -c '{app_ids: [.required_status_checks.checks[].app_id], strict: .required_status_checks.strict}' "$f" | sed 's/^/  /'
    jq -e '[.required_status_checks.checks[].app_id] | all(. == 15368)' "$f" >/dev/null || { echo "  app_id non fissato"; rc=1; }
  else
    echo "  nessuna PUT di protezione"; rc=1
  fi
  echo "--- remoti dei cloni"
  for f in protected detect; do
    url="$(git -C "$T/work/$f" remote get-url --push origin 2>&1)"
    echo "  $f -> $url"
    case "$url" in "$T/remote/"*) ;; *) echo "REMOTO FUORI DAL BANCO: $f"; rc=1 ;; esac
  done
  echo "--- righe del rapporto"
  [ -f "$T/out/casi-righe.md" ] && { echo "  righe: $(wc -l < "$T/out/casi-righe.md")"; grep -c "non riuscito" "$T/out/casi-righe.md" | sed 's/^/  non riuscite: /'; }
  grep -q "non riuscito" "$T/out/casi-righe.md" && rc=1
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

case "$MODE" in
  elenco) modo_elenco ;;
  installa) mkdir -p "$OUT" "$WORK"; modo_installa "${2:-}" ;;
  protezione) mkdir -p "$OUT" "$WORK"; modo_protezione ;;
  caso) mkdir -p "$OUT" "$WORK"; modo_caso "${2:-}" ;;
  raccogli) mkdir -p "$OUT" "$WORK"; modo_raccogli ;;
  controlla) modo_controlla ;;
  *) echo "uso: $0 elenco|installa <protected|detect>|protezione|caso <nome>|raccogli|controlla" >&2; exit 2 ;;
esac
