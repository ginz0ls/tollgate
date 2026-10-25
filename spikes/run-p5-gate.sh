#!/usr/bin/env bash
# spikes/run-p5-gate.sh — prova reale del gate di P5 su ginz0ls/tollgate-p4-detect (Task 13): aggiornamento alla 0.2.0 con
# azioni fissate per SHA, fissaggio acceso (V9), rivalutazione (M-3) e `[skip ci]` (M-4). Lo esegue solo il controller.
# Modo `controlla`: nessuna rete, `gh` finto davanti nel PATH, remoto nudo locale, git vero.
# Uso: run-p5-gate.sh elenco | aggiorna | pin-on | pin-off | caso <nome> | raccogli | controlla
#
#   elenco            i casi (nome, repo, esito atteso, descrizione), senza rete
#   aggiorna          nel clone di detect `bin/tollgate init --update` (procedura 9.4): ramo tollgate-config/<versione> con i soli
#                     file proposti (mai `git add -A`), PR, attesa di guard e verdict, merge, attesa della sentinella sul merge.
#                     Codici: 4 = init non propone nulla (non si apre nessuna PR).
#   pin-on            salva il valore iniziale di sha_pinning_required (e di allowed_actions) in un file di stato FUORI dal repo,
#                     poi PUT actions/permissions con sha_pinning_required=true. Con uno stato già presente si rifiuta.
#   pin-off           rimette il valore salvato e lo verifica; senza lo stato si rifiuta (codice 2). Codice 3: rimessa non verificata.
#   caso <nome>       pulita-fissata | rifiuto-v4 | rivalutazione | skip-ci (l'ultimo: lascia aperta l'unica issue di sentinella,
#                     la chiude il controller). Una riga del rapporto per tentativo in gate-casi-righe.md. Servono tollgate 0.2.0
#                     installato su main (aggiorna) e, per pulita-fissata e rifiuto-v4, pin-on. pulita-fissata e rivalutazione
#                     chiudono un'issue aperta ("Closes #N"): `issue create` è ammesso dalla guardia solo al controller, lo script non lo usa: la apre il controller (titolo
#                     «prova P5: ...») e la passa in P5_ISSUE; senza P5_ISSUE si cerca l'unica aperta con quel titolo. Con un'issue
#                     di sentinella aperta questi due casi non partono (codice 6).
#   raccogli          run, PR, issue e permessi di detect; log dei job di ogni run seguito; minuti; osservazioni sui log; scansione
#                     di token nelle uscite `gate-*`
#   controlla         nessuna rete: tutti i modi su un nudo locale con un gh finto, ogni gh passato da ghguard.py (profilo p5)
#
# Regole (decisioni 20-21): ogni `gh` passa da ghguard.py col profilo p5 (P4_PROFILE=p5); ogni git con la rete passa da
# `ghguard.py gitcheck` (git_net); mai un --force, mai `push --delete`, nessun ramo cancellato (nomi nuovi a ogni tentativo:
# p5-gate-<caso>-<ora>); il solo push su main è quello di `[skip ci]` del caso skip-ci. Nessuna cartella di uscite si cancella
# mai: un file che esiste già si rinomina in <nome>.prev-<tempo>. Uscite in docs/verifiche/evidenze/p5/, tutte `gate-*`.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
GH4="$here/gh-p4"
P4="$here/p4"
MODE="${1:-}"
ARG="${2:-}"

OWNER=ginz0ls
DET="$OWNER/tollgate-p4-detect"       # privato, GitHub Free, modalità detect
DET_URL="https://github.com/$DET.git"
OUT="${P5_OUT:-$root/docs/verifiche/evidenze/p5}"
WORK="${P5_WORK:-/tmp/tollgate-p5}"                  # cloni di lavoro, non sono uscite
WAIT_MAX="${P5_WAIT_MAX:-900}"                       # tetto di attesa per ogni stato o run, in secondi
POLL="${P5_POLL:-15}"
RETRY_SLEEP="${P5_RETRY_SLEEP:-5}"
RETRIES="${P5_RETRIES:-3}"                           # ritentativi di una lettura che risponde 5xx
SETTLE="${P5_SETTLE:-120}"                           # attesa prima di dire che per un commit [skip ci] non c'è nessun run
CHECK="${P5_CHECK:-0}"                               # 1 solo dentro il modo controlla
STATE_FILE="${P5_GATE_STATE:-${XDG_CACHE_HOME:-$HOME/.cache}/tollgate-p5-gate/pin-iniziale.env}"   # fuori dal repo
STATE_DIR="$WORK/gate-state"                         # stato di tollgate per `init`: cartella di prova con la sentinella
SENTINEL_TITLE='tollgate: merge non verificato'
unset GH_REPO GH_HOST GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN GIT_DIR GIT_WORK_TREE GIT_CONFIG_COUNT GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
# ghguard.py li legge: -D e i cloni devono stare qui sotto; il registro delle PR aperte è per questa prova
export P4_OUT="$OUT" P4_WORK="$WORK" P4_PROFILE=p5 P5_PR_REGISTRY="$OUT/prs-aperte.txt"

. "$GH4/common.sh"          # die, rot, log_cmd, gh_call, save_text, wait_run, await_statuses, statuses (guard_args chiama ghguard.py p5)
# anche i sondaggi (gh_q) restano in comandi.log: ogni gh eseguito dallo script è registrato
gh_q() { guard_args "$@"; log_cmd "gh $*"; gh "$@" 2>/dev/null </dev/null; }
for _dir in "$OUT" "$WORK"; do
  case "$_dir" in /*) ;; *) die "i percorsi P5_OUT e P5_WORK devono essere assoluti: $_dir" ;; esac
done
for _tool in jq git python3; do command -v "$_tool" >/dev/null 2>&1 || die "manca $_tool"; done

# ---------------------------------------------------------------- uscite, tentativi, PR aperte

LEDGER="$OUT/gate-tentativi.tsv"      # ora, modo, esito di ogni tentativo (il «composito» lo decide il controller)
ROWS="$OUT/gate-casi-righe.md"        # una riga del rapporto per tentativo di caso
RUNS="$OUT/gate-runs.tsv"             # etichetta, repo, id, conclusione dei run seguiti: li usa `raccogli`
declare -a OPEN_PRS=()
CASE_MS=0; CASE_RUNS=0; ROW_FAIL=0
PR_NUM=""; BR=""; SHA=""; ISSUE=""; TS=""

add_run() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$RUNS"; }

# close_open_prs: ogni PR aperta da questo modo e ancora aperta si chiude (anche dopo un errore): a fine prova nessuna PR aperta
close_open_prs() {
  local pr
  for pr in "${OPEN_PRS[@]}"; do
    gh_call "gate-chiusura-stato-$pr" pr view "$pr" --repo "$DET" --json state
    if [ "$(jq -r '.state' "$OUT/gate-chiusura-stato-$pr.out" 2>/dev/null)" = OPEN ]; then
      gh_call "gate-chiusura-$pr" pr close "$pr" --repo "$DET"
    fi
  done
  OPEN_PRS=()
}

finish_mode() {
  local rc=$?
  close_open_prs
  mkdir -p "$OUT"
  printf '%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$MODE${ARG:+ $ARG}" "$rc" >> "$LEDGER"
}

# ---------------------------------------------------------------- git con la rete

# no_rewrite_rules <cartella>: nessuna regola url.*.insteadOf nelle configurazioni che git legge (reindirizzerebbe un push)
no_rewrite_rules() {
  local d="$1"
  [ -d "$d" ] || d="."
  if env -u GIT_CONFIG_COUNT git -C "$d" config --get-regexp '^url\..*\.(insteadof|pushinsteadof)$' >/dev/null 2>&1; then
    die "la configurazione di git riscrive degli URL (url.*.insteadOf): mi fermo"
  fi
}

# build_genv: GENV_VARS = ambiente dei git con la rete (mai un prompt di credenziali). Nel modo controlla gli URL di
# github.com/ginz0ls vanno al nudo locale.
build_genv() {
  GENV_VARS=(GIT_TERMINAL_PROMPT=0)
  if [ "$CHECK" = 1 ] && [ -n "${P5_GIT_BASE:-}" ]; then
    GENV_VARS+=(GIT_CONFIG_COUNT=1 "GIT_CONFIG_KEY_0=url.$P5_GIT_BASE/$OWNER/.insteadOf" "GIT_CONFIG_VALUE_0=https://github.com/$OWNER/")
  fi
}

# git_net <etichetta> <cartella> <argomenti di git senza -C>: il bersaglio lo controlla `ghguard.py gitcheck` (push solo verso
# detect, mai forzato né cancellazione; clone solo di detect), poi git gira con stdout, stderr e codice d'uscita in tre file
git_net() {
  local label="$1" dir="$2" msg; shift 2
  msg="$(python3 -B -I "$GH4/ghguard.py" gitcheck --dir "$dir" -- "$@" 2>&1)" || die "git $*: $msg"
  no_rewrite_rules "$dir"
  rot "$OUT/$label".out "$OUT/$label".err "$OUT/$label".rc
  log_cmd "git-net dir=$dir $*"
  build_genv
  if [ "$1" = clone ]; then
    env "${GENV_VARS[@]}" git "$@" >"$OUT/$label.out" 2>"$OUT/$label.err" </dev/null
  else
    env "${GENV_VARS[@]}" git -C "$dir" "$@" >"$OUT/$label.out" 2>"$OUT/$label.err" </dev/null
  fi
  RC=$?
  echo "$RC" >"$OUT/$label.rc"
  return 0
}

# net_push <etichetta> <cartella> <ramo>: il solo push è `push <url di detect> <ramo>` (nessun refspec, nessuna opzione). Su main
# solo dal caso skip-ci (ALLOW_MAIN_PUSH), che è il caso M-4 della decisione 16.
ALLOW_MAIN_PUSH=0
net_push() {
  case "$3" in -*|*:*|*+*|'') die "ramo non ammesso per un push: $3" ;; esac
  if [ "$3" = main ] && [ "$ALLOW_MAIN_PUSH" != 1 ]; then die "push su main non ammesso fuori dal caso skip-ci"; fi
  git_net "$1" "$2" push "$DET_URL" "$3"
}

# ---------------------------------------------------------------- letture con ritentativo

# is_read <argomenti di gh...>: una lettura (pr/issue view|list, run list|view, api senza scrittura); `run watch` no (esce 1 su un run rosso)
is_read() {
  local a
  case "${1:-} ${2:-}" in "pr view"|"pr list"|"issue view"|"issue list"|"run list"|"run view") return 0 ;; esac
  [ "${1:-}" = api ] || return 1
  for a in "$@"; do case "$a" in --method|-X|-f|-F|--input|--field|--raw-field) return 1 ;; esac; done
  return 0
}

# gh_call (di common.sh) diventa gh_call_once; gh_call ritenta le LETTURE che rispondono 5xx (anche a corpo vuoto) fino a RETRIES
# volte, e così fanno statuses, wait_run e close_open_prs. Le scritture (pr create, merge, PATCH, close) non si ritentano mai.
eval "$(declare -f gh_call | sed '1s/^gh_call/gh_call_once/')"
gh_call() {
  local label="$1" n=0; shift
  if ! is_read "$@"; then gh_call_once "$label" "$@"; return 0; fi
  while :; do
    gh_call_once "$label" "$@"
    [ "$RC" = 0 ] && return 0
    if grep -Eq 'HTTP 5[0-9][0-9]' "$OUT/$label.err" 2>/dev/null && [ "$n" -lt "$RETRIES" ]; then
      n=$((n + 1))
      printf '%s %s tentativo %d dopo un 5xx\n' "$(date -u +%FT%TZ)" "$label" "$n" >> "$OUT/gate-ritentativi.log"
      sleep "$RETRY_SLEEP"
      continue
    fi
    return 0
  done
}
gh_read() { gh_call "$@"; }
gh_write_idem() { gh_call_once_idem "$@"; }
# la PUT di permessi è idempotente (stesso corpo): si ritenta come una lettura
gh_call_once_idem() {
  local label="$1" n=0; shift
  while :; do
    gh_call_once "$label" "$@"
    [ "$RC" = 0 ] && return 0
    if grep -Eq 'HTTP 5[0-9][0-9]' "$OUT/$label.err" 2>/dev/null && [ "$n" -lt "$RETRIES" ]; then
      n=$((n + 1)); sleep "$RETRY_SLEEP"; continue
    fi
    return 0
  done
}

# with_guarded_gh <comando...>: il `gh` dei programmi figli (tollgate init) è il wrapper con guardia (profilo p5); il gh vero lo
# conosce da P4_REAL_GH. Lo stato di tollgate è una cartella di prova. Anche il `git fetch origin` interno a init passa da qui.
with_guarded_gh() {
  local real; real="$(command -v gh)" || die "gh non trovato"
  mkdir -p "$STATE_DIR"; : > "$STATE_DIR/.tollgate-test"
  build_genv
  env -u TOLLGATE_GH TOLLGATE_STATE="$STATE_DIR" P4_REAL_GH="$real" P4_REPO="$DET" P4_LOG="$OUT/comandi.log" \
      PATH="$GH4/bin:$PATH" "${GENV_VARS[@]}" "$@"
}

# ---------------------------------------------------------------- clone, PR, stati

# detect_clone <etichetta>: clone fresco di detect in $WORK/gate-detect (il vecchio si rinomina); fetch e pull non sono ammessi,
# quindi per rivedere main dopo un merge si riclona
detect_clone() {
  local d="$WORK/gate-detect"
  mkdir -p "$WORK"
  rot "$d"
  git_net "$1-clone" "$d" clone -q "$DET_URL" "$d"
  [ "$RC" = 0 ] || die "clone di $DET fallito (vedi $1-clone.err)"
  git -C "$d" config user.name "tollgate-p5-gate"
  git -C "$d" config user.email "probe@example.invalid"
  git -C "$d" config commit.gpgsign false
  git -C "$d" switch -q main || die "main di detect non trovato"
}

# require_installed: su main di detect c'è tollgate con le azioni fissate per SHA (dopo `aggiorna`)
require_installed() {
  local d="$WORK/gate-detect" text
  git -C "$d" cat-file -e "origin/main:tollgate.toml" 2>/dev/null || die "su main di detect manca tollgate.toml"
  text="$(git -C "$d" show "origin/main:.github/workflows/tollgate-guard.yml" 2>/dev/null)" \
    || die "tollgate non è installato su main di detect: lancia prima aggiorna"
  printf '%s\n' "$text" | grep -Eq 'uses: [^ ]+@[0-9a-f]{40}' || die "i workflow di detect non sono fissati per SHA: lancia prima aggiorna"
  ! printf '%s\n' "$text" | grep -Eq 'uses: [^ ]+@v[0-9]' || die "i workflow di detect hanno ancora un tag mobile: lancia prima aggiorna"
}

# fresh_branch <nome>: imposta BR a <nome>, o a <nome>-<ora> se il ramo esiste già su detect (mai un push non-ff)
fresh_branch() {
  gh_read "gate-ramo-${1//\//-}" api "repos/$DET/branches/$1"
  if [ "$RC" = 0 ]; then BR="$1-$(date +%Y%m%d-%H%M%S)"; else BR="$1"; fi
}

# open_pr <etichetta> <ramo> <titolo> <file del corpo>: PR verso main su detect, registrata nella guardia; imposta PR_NUM
open_pr() {
  local url
  gh_call "$1-pr-create" pr create --repo "$DET" --base main --head "$2" --title "$3" --body-file "$4"
  [ "$RC" = 0 ] || die "creazione della PR fallita (vedi $1-pr-create.err)"
  url="$(tail -n 1 "$OUT/$1-pr-create.out")"
  PR_NUM="${url##*/}"
  case "$PR_NUM" in ''|*[!0-9]*) die "numero della PR non leggibile da: $url" ;; esac
  OPEN_PRS+=("$PR_NUM")      # subito: se un passo dopo fallisce, il trap chiude la PR
  python3 -B -I "$GH4/ghguard.py" register-pr "$PR_NUM" || die "la guardia non registra la PR $PR_NUM"
  save_text "$OUT/$1-pr.env" "PR=$PR_NUM" "SHA=$SHA" "BRANCH=$2"
}

# wait_run (di common.sh) ridefinito: con ripiego=1 (pull_request_target e workflow_run, che non hanno la testa della PR come
# head_sha garantito) il run si cerca PRIMA per headBranch uguale al ramo della PR e per event (7° argomento); un run di un altro
# ramo non si prende mai, nemmeno se è il più recente nello stesso intervallo. Senza run del ramo entro il tetto: nessun run.
# Con ripiego=0: per SHA o per ramo, come in common.sh. Imposta RUN_ID e RUN_CONC.
wait_run() {
  local label="$1" repo="$2" wf="$3" sha="$4" br="$5" fb="$6" ev="${7:-}" deadline id="" left
  export P4_WAIT_SHA="$sha" P4_WAIT_BRANCH="$br"
  deadline=$(( $(date +%s) + WAIT_MAX ))
  RUN_ID=""; RUN_CONC=""
  while :; do
    gh_q run list --repo "$repo" --workflow "$wf" --limit 30 \
      --json databaseId,headSha,headBranch,event,status,conclusion,createdAt >"$WORK/poll.json"
    id="$(jq -r --arg s "$sha" --arg b "$br" --arg f "$fb" --arg e "$ev" \
      '[.[] | select(($e == "" or .event == $e)
                     and (if $f == "1" then ($b != "" and .headBranch == $b) else (.headSha == $s or ($b != "" and .headBranch == $b)) end))]
       | sort_by(.databaseId) | last | .databaseId // empty' "$WORK/poll.json" 2>/dev/null)"
    [ -n "$id" ] && break
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "nessun run di $wf del ramo ${br:-?} (evento ${ev:-qualunque}) entro ${WAIT_MAX}s ($label)" >&2
      save_text "$OUT/$label-runid.txt" "non determinato: nessun run del ramo ${br:-?} entro ${WAIT_MAX}s"
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

# track <etichetta> <workflow> <sha> <ramo> <ripiego> [evento]: attende il run (wait_run), registra durata e riga per `raccogli`
track() {
  local ms
  wait_run "$1" "$DET" "$2" "$3" "$4" "$5" "${6:-}" || return 1
  add_run "$1" "$DET" "$RUN_ID" "$RUN_CONC"
  gh_read "$1-timing" api "repos/$DET/actions/runs/$RUN_ID/timing"
  ms="$(jq -r '.run_duration_ms // 0' "$OUT/$1-timing.out" 2>/dev/null)"
  case "$ms" in ''|*[!0-9]*) ms=0 ;; esac
  CASE_MS=$((CASE_MS + ms)); CASE_RUNS=$((CASE_RUNS + 1))
  return 0
}

# stati: l'API li dà dal più recente
latest_state() { jq -rs --arg c "$2" 'map(select(.context == $c)) | .[0].state // "none"' "$1" 2>/dev/null || echo none; }
latest_creator() { jq -rs --arg c "$2" 'map(select(.context == $c)) | .[0].creator // "-"' "$1" 2>/dev/null || echo -; }
count_ctx() { jq -s --arg c "$2" '[.[] | select(.context == $c)] | length' "$1" 2>/dev/null || echo 0; }

# shown_states <file> <contesto...>: «guard=success (github-actions[bot]), ...»
shown_states() {
  local f="$1" c s=""; shift
  for c in "$@"; do s="${s:+$s, }${c##*/}=$(latest_state "$f" "$c") ($(latest_creator "$f" "$c"))"; done
  echo "$s"
}

# emit_row <caso> <pr> <sha> <ottenuto> <atteso> <esito>: la riga del rapporto (stesse colonne di quello di P4), con i minuti
# del tentativo (durata dei run seguiti: l'API dei minuti fatturati è 0 sui privati Free)
emit_row() {
  local row
  row="| $1 | $2 | ${3:0:10} | $4 | $5 | $6 | $(awk -v ms="$CASE_MS" -v n="$CASE_RUNS" 'BEGIN { printf "%.1f (%d run)", ms / 60000, n }') |"
  printf '%s\n' "$row" >> "$ROWS"
  echo "$row"
  case "$6" in riuscito*) ;; *) ROW_FAIL=1 ;; esac
}

# case_issue: l'issue aperta del caso (lo script non crea issue: `issue create` è ammesso dalla guardia solo al controller, che la apre). P5_ISSUE, oppure l'unica
# aperta il cui titolo comincia per «prova P5». Nessuna issue di sentinella aperta (renderebbe rossa `attention`).
case_issue() {
  local n
  gh_read "$1-issue-list" issue list --repo "$DET" --state open --limit 100 --json number,title
  [ "$RC" = 0 ] || die "elenco delle issue non leggibile (vedi $1-issue-list.err)"
  n="$(jq --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | length' "$OUT/$1-issue-list.out" 2>/dev/null)"
  [ "${n:-0}" = 0 ] || { echo "c'è un'issue di sentinella aperta: chiudila (la chiude il controller) prima di un caso che aspetta attention verde" >&2; exit 6; }
  if [ -n "${P5_ISSUE:-}" ]; then
    case "$P5_ISSUE" in *[!0-9]*) die "P5_ISSUE non è un numero: $P5_ISSUE" ;; esac
    ISSUE="$P5_ISSUE"
  else
    ISSUE="$(jq -r '[.[] | select(.title | startswith("prova P5"))] | first | .number // empty' "$OUT/$1-issue-list.out" 2>/dev/null)"
  fi
  [ -n "$ISSUE" ] || die "serve un'issue aperta su $DET per il caso: aprila a mano (titolo «prova P5: ...») e passala in P5_ISSUE"
  gh_read "$1-issue-stato" issue view "$ISSUE" --repo "$DET" --json number,title,state
  [ "$(jq -r '.state' "$OUT/$1-issue-stato.out" 2>/dev/null)" = OPEN ] || die "l'issue #$ISSUE non risulta aperta (vedi $1-issue-stato.out)"
}

# build_work_pr <etichetta> <caso> <make_case>: il lavoro pulito su tg/<N>-p5-gate-<caso>-<ora> con il codice di P4 (make_case.py),
# da main di detect: imposta CASEJSON (con il nome del caso di P5), BR, SHA, BODY_FILE
build_work_pr() {
  local d="$WORK/gate-detect" old head
  python3 -B "$P4/make_case.py" build "$3" --clone "$d" --issue "$ISSUE" --ts "$TS" --out "$OUT" --label "$1" \
    >"$OUT/$1-build.txt" 2>&1 || { cat "$OUT/$1-build.txt" >&2; die "costruzione del caso fallita"; }
  old="$(jq -r '.branch' "$OUT/$1-case.json")"
  BR="tg/$ISSUE-p5-gate-$2-$TS"
  git -C "$d" branch -m "$old" "$BR" || die "ramo $old non rinominato"
  CASEJSON="$OUT/$1-case-p5.json"
  rot "$CASEJSON"
  jq --arg o "$old" --arg n "$BR" --arg name "$2" '.name = $name | .branch = $n | .ops |= map(if .branch == $o then .branch = $n else . end)' \
    "$OUT/$1-case.json" > "$CASEJSON" || die "caso riscritto male"
  SHA="$(jq -r '.ops[] | select(.op == "push") | .sha' "$CASEJSON")"
  head="$(git -C "$d" rev-parse HEAD)"
  [ "$SHA" = "$head" ] || die "la testa del ramo ($head) non è lo SHA del caso ($SHA)"
  BODY_FILE="$(jq -r '.ops[] | select(.op == "pr") | .body_file' "$CASEJSON")"
  [ -s "$BODY_FILE" ] || die "corpo della PR assente: $BODY_FILE"
}

# collect_green <etichetta>: attende guard, verdict e attention sullo SHA, salva stati e commenti (con autore)
collect_green() {
  await_statuses "$DET" "$SHA" tollgate/guard tollgate/verdict tollgate/attention || echo "attesa degli stati non riuscita su $SHA" >&2
  statuses "$1-statuses" "$DET" "$SHA"
  gh_call "$1-comments" api --paginate "repos/$DET/issues/$PR_NUM/comments?per_page=100" --jq "$COMMENT_JQ"
}

# ---------------------------------------------------------------- aggiorna (procedura 9.4)

modo_aggiorna() {
  local d="$WORK/gate-detect" label="gate-aggiorna" version rel line m1 body out prop
  prop="$d/docs/superpowers/tollgate-init"
  TS="$(date +%Y%m%d-%H%M%S)"
  detect_clone "$label"
  mkdir -p "$d/.git/info"
  grep -qx 'docs/superpowers/tollgate-init/' "$d/.git/info/exclude" 2>/dev/null \
    || echo 'docs/superpowers/tollgate-init/' >> "$d/.git/info/exclude"
  version="$(sed -n 's/^VERSION = "\(.*\)"$/\1/p' "$root/bin/tollgate_core/__init__.py")"
  [ -n "$version" ] || die "versione di tollgate non leggibile"
  rot "$OUT/$label-init.out" "$OUT/$label-init.err" "$OUT/$label-init.rc"
  log_cmd "tollgate init --update (cwd gate-detect)"
  ( cd "$d" && with_guarded_gh python3 -B "$root/bin/tollgate" init --update --merges-per-month 20 ) \
    >"$OUT/$label-init.out" 2>"$OUT/$label-init.err" </dev/null
  echo "$?" >"$OUT/$label-init.rc"
  [ "$(cat "$OUT/$label-init.rc")" = 0 ] || die "tollgate init --update rifiutato (vedi $label-init.out e .err)"
  if grep -q 'nulla da aggiornare' "$OUT/$label-init.out"; then
    save_text "$OUT/$label-esito.txt" "init --update non propone nulla: nessuna PR aperta"
    echo "init --update non propone nessun file: mi fermo (codice 4)" >&2
    exit 4
  fi
  [ -d "$prop/files" ] || die "la proposta non ha files/"
  rot "$OUT/$label-proposta"
  mkdir -p "$OUT/$label-proposta"
  [ -e "$prop/README.md" ] && cp "$prop/README.md" "$OUT/$label-proposta/README.md"
  ( cd "$prop/files" && find . -type f | sort ) >"$OUT/$label-proposta/elenco-files.txt"
  fresh_branch "tollgate-config/$version"
  git -C "$d" switch -q -c "$BR" origin/main || die "ramo $BR non creato"
  while IFS= read -r rel; do         # solo i file proposti, uno per uno: mai `git add -A`
    rel="${rel#./}"
    case "$rel" in ''|/*|*..*) die "percorso proposto non ammesso: $rel" ;; esac
    mkdir -p "$d/$(dirname "$rel")"
    cp "$prop/files/$rel" "$d/$rel" && git -C "$d" add -- "$rel" || die "file proposto non copiato: $rel"
  done < "$OUT/$label-proposta/elenco-files.txt"
  while IFS= read -r line; do        # «Da cancellare» del README: solo file tracciati sotto .github/tollgate/
    printf '%s\n' "$line" | grep -Eq '^\.github/tollgate/[A-Za-z0-9._/-]+$' || die "riga di «Da cancellare» non ammessa: $line"
    git -C "$d" ls-files --error-unmatch -- "$line" >/dev/null 2>&1 || die "da cancellare ma non tracciato: $line"
    git -C "$d" rm -q -- "$line" || die "cancellazione non riuscita: $line"
  done < <(awk '/^## /{s = ($0 == "## Da cancellare")} s && NF && !/^## / && !/^File di tollgate presenti/ {print}' "$prop/README.md")
  git -C "$d" diff --cached --quiet && die "nessun file in staging dopo la copia della proposta"
  git -C "$d" diff --cached --name-status > "$OUT/$label-staging.txt"
  git -C "$d" commit -qm "tollgate: aggiornamento alla $version (init --update)" || die "commit dell'aggiornamento fallito"
  SHA="$(git -C "$d" rev-parse HEAD)"
  net_push "$label-push" "$d" "$BR"
  [ "$RC" = 0 ] || die "push di $BR fallito (vedi $label-push.err)"
  body="$OUT/$label-corpo.md"
  rot "$body"
  printf 'Aggiornamento di tollgate alla %s con `init --update` (prova P5 su detect): contiene solo file di tollgate.\n' "$version" > "$body"
  open_pr "$label" "$BR" "tollgate: aggiornamento alla $version (prova P5)" "$body"
  await_statuses "$DET" "$SHA" tollgate/guard tollgate/verdict || echo "attesa degli stati non riuscita su $SHA" >&2
  statuses "$label-statuses" "$DET" "$SHA"
  track "$label-run" tollgate-run.yml "$SHA" "$BR" 0 || echo "run di tollgate-run non completato su $SHA" >&2
  out="$(shown_states "$OUT/$label-statuses.out" tollgate/guard tollgate/verdict tollgate/attention)"
  save_text "$OUT/$label-esito.txt" "PR #$PR_NUM, ramo $BR, SHA $SHA" "stati: $out"
  echo "aggiorna: PR #$PR_NUM, $out"
  if [ "$(latest_state "$OUT/$label-statuses.out" tollgate/guard)" != success ] || [ "$(latest_state "$OUT/$label-statuses.out" tollgate/verdict)" != success ]; then
    die "guard o verdict non sono verdi su $SHA: non unisco (vedi $label-statuses.out); la PR si chiude"
  fi
  gh_call "$label-merge" pr merge "$PR_NUM" --repo "$DET" --squash
  [ "$RC" = 0 ] || die "merge della PR $PR_NUM fallito (vedi $label-merge.err)"
  gh_read "$label-merge-stato" pr view "$PR_NUM" --repo "$DET" --json state,mergeCommit
  m1="$(jq -r '.mergeCommit.oid // empty' "$OUT/$label-merge-stato.out" 2>/dev/null)"
  [ -n "$m1" ] || die "SHA del merge non leggibile (vedi $label-merge-stato.out)"
  save_text "$OUT/$label-merge-sha.txt" "$m1"
  track "$label-sentinel" tollgate-sentinel.yml "$m1" "" 0 || echo "tollgate-sentinel non completato su $m1" >&2
  track "$label-base" tollgate-base.yml "$m1" "" 0 || echo "tollgate-base non completato su $m1" >&2
  await_statuses "$DET" "$m1" tollgate/sentinel || echo "stato di sentinel non comparso su $m1" >&2
  statuses "$label-merge-statuses" "$DET" "$m1"
  echo "aggiorna: merge $m1, sentinel $(latest_state "$OUT/$label-merge-statuses.out" tollgate/sentinel)"
}

# ---------------------------------------------------------------- pin-on, pin-off

# pin_put <etichetta> <true|false> <allowed_actions o vuoto>
pin_put() {
  local -a f=(-F enabled=true -F "sha_pinning_required=$2")
  [ -n "$3" ] && f+=(-F "allowed_actions=$3")
  gh_write_idem "$1" api --method PUT "repos/$DET/actions/permissions" "${f[@]}"
}

# pin_value <etichetta>: sha_pinning_required corrente (true|false), vuoto se non si legge
pin_value() {
  gh_read "$1" api "repos/$DET/actions/permissions"
  [ "$RC" = 0 ] || return 1
  jq -r '.sha_pinning_required // false' "$OUT/$1.out" 2>/dev/null
}

modo_pin_on() {
  local init actions now
  [ ! -e "$STATE_FILE" ] || { echo "stato già presente ($STATE_FILE): un pin-on è già in corso o non è stato chiuso; lancia pin-off o controlla a mano" >&2; exit 2; }
  gh_read gate-pin-iniziale api "repos/$DET/actions/permissions"
  [ "$RC" = 0 ] || die "permessi iniziali di $DET non leggibili (vedi gate-pin-iniziale.err)"
  [ "$(jq -r '.enabled' "$OUT/gate-pin-iniziale.out" 2>/dev/null)" = true ] || die "Actions non risulta abilitato su $DET: mi fermo"
  init="$(jq -r '.sha_pinning_required // false' "$OUT/gate-pin-iniziale.out")"
  actions="$(jq -r '.allowed_actions // empty' "$OUT/gate-pin-iniziale.out")"
  case "$init" in true|false) ;; *) die "sha_pinning_required iniziale non leggibile" ;; esac
  case "$actions" in ''|all|local_only|selected) ;; *) die "allowed_actions iniziale inatteso: $actions" ;; esac
  mkdir -p "$(dirname "$STATE_FILE")" && chmod 700 "$(dirname "$STATE_FILE")" 2>/dev/null
  printf 'PIN_INIT=%s\nPIN_ACTIONS=%s\n' "$init" "$actions" > "$STATE_FILE.nuovo" && mv "$STATE_FILE.nuovo" "$STATE_FILE" \
    || die "stato non scritto in $STATE_FILE"
  save_text "$OUT/gate-pin-stato.txt" "valore iniziale di sha_pinning_required: $init" "allowed_actions iniziale: ${actions:-non letto}" \
    "stato salvato in $STATE_FILE (fuori dal repo)"
  pin_put gate-pin-on true "$actions"
  now="$(pin_value gate-pin-on-verifica)"
  if [ "$now" != true ]; then
    # la PUT non ha avuto effetto: se il valore è ancora quello iniziale non c'è niente da rimettere e lo stato si archivia
    if [ "$now" = "$init" ]; then rot "$STATE_FILE"; fi
    die "sha_pinning_required non risulta acceso (letto: ${now:-illeggibile}); vedi gate-pin-on.err e gate-pin-on-verifica.out"
  fi
  echo "sha_pinning_required acceso (valore iniziale: $init, salvato in $STATE_FILE)"
}

modo_pin_off() {
  local init actions try now
  [ -f "$STATE_FILE" ] || { echo "nessuno stato salvato ($STATE_FILE): non so quale valore rimettere, mi rifiuto" >&2; exit 2; }
  init="$(sed -n 's/^PIN_INIT=//p' "$STATE_FILE")"
  actions="$(sed -n 's/^PIN_ACTIONS=//p' "$STATE_FILE")"
  case "$init" in true|false) ;; *) die "stato illeggibile in $STATE_FILE: controlla a mano" ;; esac
  case "$actions" in ''|all|local_only|selected) ;; *) die "stato illeggibile in $STATE_FILE: controlla a mano" ;; esac
  for try in 1 2 3; do
    pin_put gate-pin-off "$init" "$actions"
    [ "$RC" = 0 ] && break
    sleep "$RETRY_SLEEP"
  done
  now="$(pin_value gate-pin-dopo)"
  if [ "$now" = "$init" ]; then
    mv "$STATE_FILE" "$STATE_FILE.rimesso-$(date +%s)"
    echo "sha_pinning_required rimesso a $init (verificato)"
  else
    echo "RIPRISTINO NON VERIFICATO: rimetti a mano sha_pinning_required=$init su $DET (vedi gate-pin-off.* e gate-pin-dopo.*)" >&2
    exit 3
  fi
}

# ---------------------------------------------------------------- casi

CASES="pulita-fissata rifiuto-v4 rivalutazione skip-ci"

modo_elenco() {
  printf 'pulita-fissata\tdetect\tguard=success, verdict=success, attention=success; log del job verdict: Cache mode: read\tPR pulita con sha_pinning_required acceso (VG1)\n'
  printf 'rifiuto-v4\tdetect\trun rifiutato (failure): tutte le azioni devono essere fissate per SHA\tramo con un workflow a @v4 e il fissaggio acceso\n'
  printf 'rivalutazione\tdetect\tverdict dopo la modifica del corpo: pending (guard) poi success\tPR verde, PATCH del corpo; registra l ordine reale (decisione 15)\n'
  printf 'skip-ci\tdetect\tsentinel=failure sul commit saltato, success fermo al segnale, una sola issue\tpush controllato, push diretto su main con [skip ci], push normale (decisione 16)\n'
}

pin_state_now() { # <etichetta> -> true|false|illeggibile
  local v; v="$(pin_value "$1")" || v=""
  echo "${v:-illeggibile}"
}

caso_pulita_fissata() {
  local label="gate-caso-pulita-fissata-$TS" d="$WORK/gate-detect" row esito pin cm
  pin="$(pin_state_now "$label-pin")"
  [ "$pin" = true ] || die "sha_pinning_required non è acceso ($pin): lancia prima pin-on"
  detect_clone "$label"; require_installed
  case_issue "$label"
  build_work_pr "$label" pulita-fissata detect-pulita
  net_push "$label-push" "$d" "$BR"
  [ "$RC" = 0 ] || die "push di $BR fallito (vedi $label-push.err)"
  open_pr "$label" "$BR" "prova P5: pulita-fissata" "$BODY_FILE"
  # i run si agganciano subito dopo l'apertura: pull_request_target e workflow_run non hanno la testa della PR come head_sha in
  # modo garantito, quindi guard e verdict si cercano col ripiego «il più recente creato negli ultimi minuti» (come in Task 1)
  GUARD_MISSING=0
  track "$label-guard" tollgate-guard.yml "$SHA" "$BR" 1 pull_request_target || { GUARD_MISSING=1; echo "run di tollgate-guard del ramo $BR non trovato" >&2; }
  track "$label-run" tollgate-run.yml "$SHA" "$BR" 0 || echo "run di tollgate-run non trovato su $SHA" >&2
  rot "$OUT/$label-cache-mode.txt"
  cm="non determinato: il run di tollgate-verdict non è comparso entro ${WAIT_MAX}s"
  if track "$label-verdict" tollgate-verdict.yml "$SHA" "$BR" 1 workflow_run; then
    gh_read "$label-verdict-log" run view "$RUN_ID" --repo "$DET" --log
    cm="$(grep -a 'Cache mode:' "$OUT/$label-verdict-log.out" | head -n 1 | sed 's/^.*\(Cache mode:.*\)$/\1/')"
    [ -n "$cm" ] || cm="non determinato: nessuna riga «Cache mode:» nel log del job verdict"
  fi
  collect_green "$label"
  save_text "$OUT/$label-cache-mode.txt" "$cm"
  row="$(python3 -B "$P4/make_case.py" judge "$CASEJSON" --push "$(jq -r '.expect[0].push' "$CASEJSON")" --statuses "$OUT/$label-statuses.out" \
    --comments "$OUT/$label-comments.out" --pr "#$PR_NUM" --sha "$SHA")" || ROW_FAIL=1
  row="${row%| |}"
  printf '%s\n' "$row| $(awk -v ms="$CASE_MS" -v n="$CASE_RUNS" 'BEGIN { printf "%.1f (%d run)", ms / 60000, n }') |" | tee -a "$ROWS"
  case "$cm" in 'Cache mode: read'*) esito=riuscito ;; *) esito="non riuscito: $cm" ;; esac
  emit_row pulita-fissata-cache "#$PR_NUM" "$SHA" "$cm" "Cache mode: read (VG1)" "$esito"
  [ "$GUARD_MISSING" = 0 ] || emit_row pulita-fissata-aggancio "#$PR_NUM" "$SHA" "nessun run di guard del ramo $BR" "run di guard agganciato per ramo" \
    "non riuscito: run di guard non trovato (minuti incompleti; gli stati restano giudicati)"
  close_open_prs
}

caso_rifiuto_v4() {
  local label="gate-caso-rifiuto-v4-$TS" d="$WORK/gate-detect" pin wf conc="-" msg="assente" esito wanted
  pin="$(pin_state_now "$label-pin")"
  [ "$pin" = true ] || die "sha_pinning_required non è acceso ($pin): lancia prima pin-on"
  detect_clone "$label"
  BR="p5-gate-rifiuto-v4-$TS"
  wf="p5-gate-rifiuto-v4.yml"
  git -C "$d" switch -q -c "$BR" main || die "ramo $BR non creato"
  mkdir -p "$d/.github/workflows"
  cat > "$d/.github/workflows/$wf" <<'YML'
name: p5-gate-rifiuto-v4
# Prova P5 su detect: azione a tag mobile (@v4); con sha_pinning_required acceso il run deve essere rifiutato.
on:
  push:
    branches: ["p5-gate-rifiuto-v4-*"]
permissions:
  contents: read
jobs:
  prova:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo prova-rifiuto-v4
YML
  git -C "$d" add -- ".github/workflows/$wf" && git -C "$d" commit -qm "prova P5: workflow a @v4 con il fissaggio acceso" || die "commit del workflow fallito"
  SHA="$(git -C "$d" rev-parse HEAD)"
  net_push "$label-push" "$d" "$BR"
  [ "$RC" = 0 ] || die "push di $BR fallito (vedi $label-push.err)"
  save_text "$OUT/$label-ramo.env" "BRANCH=$BR" "SHA=$SHA"
  wanted="run rifiutato: conclusione failure e messaggio «must be pinned to a full-length commit SHA»"
  if track "$label-v4" "$wf" "$SHA" "$BR" 0; then
    conc="$RUN_CONC"
    gh_read "$label-v4-log-failed" run view "$RUN_ID" --repo "$DET" --log-failed
    if grep -aqi 'must be pinned to a full-length commit SHA' "$OUT/$label-v4-log-failed.out" "$OUT/$label-v4-log-failed.err" 2>/dev/null; then
      msg="presente"
    fi
    if [ "$conc" = failure ] && [ "$msg" = presente ]; then esito=riuscito
    else esito="non riuscito: conclusione $conc, messaggio $msg"; fi
  else
    esito="non riuscito: il run di $wf non è comparso entro ${WAIT_MAX}s"
  fi
  emit_row rifiuto-v4 "ramo $BR" "$SHA" "run conclusione $conc, messaggio $msg" "$wanted" "$esito"
}

caso_rivalutazione() {
  local label="gate-caso-rivalutazione-$TS" d="$WORK/gate-detect" k edit_body seq creators final esito got deadline n
  detect_clone "$label"; require_installed
  case_issue "$label"
  build_work_pr "$label" rivalutazione detect-pulita
  net_push "$label-push" "$d" "$BR"
  [ "$RC" = 0 ] || die "push di $BR fallito (vedi $label-push.err)"
  open_pr "$label" "$BR" "prova P5: rivalutazione" "$BODY_FILE"
  collect_green "$label-prima"
  track "$label-prima-run" tollgate-run.yml "$SHA" "$BR" 0 || echo "run di tollgate-run non trovato su $SHA" >&2
  if [ "$(latest_state "$OUT/$label-prima-statuses.out" tollgate/verdict)" != success ]; then
    emit_row rivalutazione "#$PR_NUM" "$SHA" "$(shown_states "$OUT/$label-prima-statuses.out" tollgate/guard tollgate/verdict tollgate/attention)" \
      "PR verde prima della modifica" "non riuscito: la PR non era verde prima della modifica"
    close_open_prs
    return 0
  fi
  k="$(count_ctx "$OUT/$label-prima-statuses.out" tollgate/verdict)"
  # il corpo con la REST: `gh pr edit` esce con 1 con gh 2.46 (Projects classic); è la forma di bin/tollgate_flow/gh.py
  edit_body="$OUT/$label-corpo-modificato.md"
  rot "$edit_body"
  { cat "$BODY_FILE"; printf '\nCorpo modificato dopo l apertura (prova P5, rivalutazione).\n'; } > "$edit_body"
  gh_call "$label-pr-edit" api --method PATCH "repos/$DET/pulls/$PR_NUM" -F "body=@$edit_body"
  [ "$RC" = 0 ] || die "modifica della PR fallita (vedi $label-pr-edit.err)"
  # almeno due stati verdict nuovi (pending dal guard, success dal verdict) e l'ultimo non pending
  deadline=$(( $(date +%s) + WAIT_MAX ))
  while :; do
    gh_q api --paginate "repos/$DET/commits/$SHA/statuses?per_page=100" --jq "$STATUS_JQ" > "$WORK/poll-statuses.jsonl"
    n="$(count_ctx "$WORK/poll-statuses.jsonl" tollgate/verdict)"
    [ "${n:-0}" -ge $((k + 2)) ] && [ "$(latest_state "$WORK/poll-statuses.jsonl" tollgate/verdict)" != pending ] && break
    [ "$(date +%s)" -ge "$deadline" ] && { echo "stati verdict dopo la modifica non comparsi entro ${WAIT_MAX}s su $SHA" >&2; break; }
    sleep "$POLL"
  done
  statuses "$label-statuses" "$DET" "$SHA"
  # ordine reale (decisione 15): gli stati verdict nuovi, dal più vecchio, con autore e ora
  seq="$(jq -rs --arg c tollgate/verdict --argjson k "$k" '[.[] | select(.context == $c)] | reverse | .[$k:] | map(.state) | join(" -> ")' "$OUT/$label-statuses.out" 2>/dev/null)"
  creators="$(jq -rs --arg c tollgate/verdict --argjson k "$k" '[.[] | select(.context == $c)] | reverse | .[$k:] | map(.creator + "@" + .created_at) | join(", ")' "$OUT/$label-statuses.out" 2>/dev/null)"
  save_text "$OUT/$label-ordine.txt" "stati tollgate/verdict dopo la modifica, dal più vecchio: ${seq:-illeggibile}" "autori e ora: ${creators:-illeggibile}"
  final="$(latest_state "$OUT/$label-statuses.out" tollgate/verdict)"
  got="verdict dopo la modifica: ${seq:-illeggibile} ($creators); $(shown_states "$OUT/$label-statuses.out" tollgate/guard tollgate/verdict tollgate/attention)"
  if [ "${seq%% *}" = pending ] && [ "$final" = success ] && ! printf '%s' "$creators" | tr ',' '\n' | sed 's/^ //' | grep -v '^github-actions\[bot\]@' | grep -q .; then
    esito=riuscito
  elif [ "$final" = pending ]; then
    esito="non riuscito: verdict è rimasto pending (verdict prima di guard: si rilancia il run di verdict); ordine reale: ${seq:-illeggibile}"
  else
    esito="non riuscito: ordine reale ${seq:-illeggibile}, ultimo stato $final"
  fi
  emit_row rivalutazione "#$PR_NUM" "$SHA" "$got" "verdict: pending (guard su edited) poi success, tutti github-actions[bot]" "$esito"
  close_open_prs
}

# issue_text <numero> <file>: corpo e commenti di un'issue in un solo testo
issue_text() {
  gh_read "$2" issue view "$1" --repo "$DET" --json number,title,state,body,comments
  jq -r '[.body, (.comments[]?.body)] | join("\n")' "$OUT/$2.out" 2>/dev/null
}

caso_skip_ci() {
  local label="gate-caso-skip-ci-$TS" d="$WORK/gate-detect" body m1 s_sha n_sha open_n comments_n text esito got problems="" st_s st_n st_m1 runs_s runs_n pr issue_no rc_n
  detect_clone "$label"; require_installed
  gh_read "$label-issue-prima" issue list --repo "$DET" --state open --limit 100 --json number,title
  open_n="$(jq --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | length' "$OUT/$label-issue-prima.out" 2>/dev/null)"
  save_text "$OUT/$label-issue-prima.txt" "issue di sentinella aperte prima del caso: ${open_n:-?}"
  # 1. push controllato: la PR di un ramo libero con un file in notes/, verde, unita (squash): il merge è un push su main che
  #    la sentinella deve verificare e segnare con success
  BR="p5-gate-skip-ci-base-$TS"
  git -C "$d" switch -q -c "$BR" main || die "ramo $BR non creato"
  mkdir -p "$d/notes"
  printf 'push controllato del caso skip-ci (prova P5)\n' > "$d/notes/p5-skip-ci-base-$TS.md"
  git -C "$d" add -- "notes/p5-skip-ci-base-$TS.md" && git -C "$d" commit -qm "prova P5 skip-ci: contenuto del push controllato" || die "commit fallito"
  SHA="$(git -C "$d" rev-parse HEAD)"
  net_push "$label-push-base" "$d" "$BR"
  [ "$RC" = 0 ] || die "push di $BR fallito (vedi $label-push-base.err)"
  body="$OUT/$label-corpo.md"; rot "$body"
  printf 'PR di prova del caso skip-ci (tollgate P5): il suo merge è il push controllato.\n' > "$body"
  open_pr "$label-base" "$BR" "prova P5: skip-ci, push controllato" "$body"
  pr="$PR_NUM"
  await_statuses "$DET" "$SHA" tollgate/guard tollgate/verdict || echo "attesa degli stati non riuscita su $SHA" >&2
  statuses "$label-base-statuses" "$DET" "$SHA"
  if [ "$(latest_state "$OUT/$label-base-statuses.out" tollgate/guard)" != success ] || [ "$(latest_state "$OUT/$label-base-statuses.out" tollgate/verdict)" != success ]; then
    emit_row skip-ci "#$pr" "$SHA" "$(shown_states "$OUT/$label-base-statuses.out" tollgate/guard tollgate/verdict)" \
      "PR di partenza verde" "non riuscito: la PR di partenza non è verde, non la unisco"
    close_open_prs
    return 0
  fi
  gh_call "$label-merge" pr merge "$pr" --repo "$DET" --squash
  [ "$RC" = 0 ] || die "merge della PR $pr fallito (vedi $label-merge.err)"
  gh_read "$label-merge-stato" pr view "$pr" --repo "$DET" --json state,mergeCommit
  m1="$(jq -r '.mergeCommit.oid // empty' "$OUT/$label-merge-stato.out" 2>/dev/null)"
  [ -n "$m1" ] || die "SHA del merge non leggibile (vedi $label-merge-stato.out)"
  track "$label-sentinel-m1" tollgate-sentinel.yml "$m1" "" 0 || echo "tollgate-sentinel non completato su $m1" >&2
  await_statuses "$DET" "$m1" tollgate/sentinel || echo "stato di sentinel non comparso su $m1" >&2
  statuses "$label-m1-statuses" "$DET" "$m1"
  if [ "$(latest_state "$OUT/$label-m1-statuses.out" tollgate/sentinel)" != success ]; then
    emit_row skip-ci "#$pr" "$m1" "sentinel su $m1: $(latest_state "$OUT/$label-m1-statuses.out" tollgate/sentinel)" \
      "il push controllato lascia tollgate/sentinel success" "non riuscito: manca il segnale di partenza (success sul merge)"
    return 0
  fi
  # 2. clone fresco (fetch e pull non sono ammessi): main ora contiene il merge. Push diretto con [skip ci], poi push normale.
  #    È il caso M-4 (decisione 16): i soli push su main di tutta la prova.
  detect_clone "$label-2"
  ALLOW_MAIN_PUSH=1
  mkdir -p "$d/notes"
  printf 'push diretto con [skip ci] (prova P5)\n' > "$d/notes/p5-skip-ci-saltato-$TS.md"
  git -C "$d" add -- "notes/p5-skip-ci-saltato-$TS.md" && git -C "$d" commit -qm "prova P5 skip-ci: push diretto [skip ci]" || die "commit fallito"
  s_sha="$(git -C "$d" rev-parse HEAD)"
  net_push "$label-push-saltato" "$d" main
  [ "$RC" = 0 ] || { ALLOW_MAIN_PUSH=0; die "push diretto fallito (vedi $label-push-saltato.err)"; }
  save_text "$OUT/$label-saltato-sha.txt" "$s_sha"
  sleep "$SETTLE"     # il run che [skip ci] impedisce non compare: si lascia il tempo di comparire a uno che invece parte
  printf 'push normale dopo il saltato (prova P5)\n' > "$d/notes/p5-skip-ci-normale-$TS.md"
  git -C "$d" add -- "notes/p5-skip-ci-normale-$TS.md" && git -C "$d" commit -qm "prova P5 skip-ci: push normale" || die "commit fallito"
  n_sha="$(git -C "$d" rev-parse HEAD)"
  net_push "$label-push-normale" "$d" main
  rc_n="$RC"
  ALLOW_MAIN_PUSH=0
  [ "$rc_n" = 0 ] || die "push normale fallito (vedi $label-push-normale.err)"
  save_text "$OUT/$label-normale-sha.txt" "$n_sha"
  track "$label-sentinel-n" tollgate-sentinel.yml "$n_sha" "" 0 || problems="$problems il run di sentinella sul push normale non è comparso;"
  await_statuses "$DET" "$n_sha" tollgate/sentinel || echo "stato di sentinel non comparso su $n_sha" >&2
  await_statuses "$DET" "$s_sha" tollgate/sentinel || echo "stato di sentinel non comparso su $s_sha" >&2
  statuses "$label-s-statuses" "$DET" "$s_sha"
  statuses "$label-n-statuses" "$DET" "$n_sha"
  statuses "$label-m1-statuses-dopo" "$DET" "$m1"
  gh_read "$label-runs" run list --repo "$DET" --workflow tollgate-sentinel.yml --limit 30 --json databaseId,headSha,event,status,conclusion,createdAt
  runs_s="$(jq --arg s "$s_sha" '[.[] | select(.headSha == $s)] | length' "$OUT/$label-runs.out" 2>/dev/null)"
  runs_n="$(jq --arg s "$n_sha" '[.[] | select(.headSha == $s)] | length' "$OUT/$label-runs.out" 2>/dev/null)"
  gh_read "$label-issue-dopo" issue list --repo "$DET" --state open --limit 100 --json number,title
  open_n="$(jq --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | length' "$OUT/$label-issue-dopo.out" 2>/dev/null)"
  text=""; comments_n="-"
  if [ "${open_n:-0}" = 1 ]; then
    issue_no="$(jq -r --arg t "$SENTINEL_TITLE" '[.[] | select(.title == $t)] | first | .number' "$OUT/$label-issue-dopo.out")"
    text="$(issue_text "$issue_no" "$label-issue-testo")"
    comments_n="$(jq '.comments | length' "$OUT/$label-issue-testo.out" 2>/dev/null)"
  fi
  st_s="$(latest_state "$OUT/$label-s-statuses.out" tollgate/sentinel)"
  st_n="$(latest_state "$OUT/$label-n-statuses.out" tollgate/sentinel)"
  st_m1="$(latest_state "$OUT/$label-m1-statuses-dopo.out" tollgate/sentinel)"
  [ "${runs_s:-x}" = 0 ] || problems="$problems il commit [skip ci] ha un run di sentinella (${runs_s:-?});"
  [ "${runs_n:-x}" -ge 1 ] 2>/dev/null || problems="$problems nessun run di sentinella sul push normale;"
  [ "$st_s" = failure ] || problems="$problems il commit saltato ha sentinel $st_s invece di failure;"
  [ "$st_n" = failure ] || problems="$problems il push normale ha sentinel $st_n invece di failure;"
  [ "$st_m1" = success ] || problems="$problems il segnale di partenza non è più success ($st_m1);"
  [ "${open_n:-x}" = 1 ] || problems="$problems issue di sentinella aperte: ${open_n:-?} invece di 1;"
  printf '%s' "$text" | grep -q "$s_sha" || problems="$problems l'issue non nomina il commit saltato;"
  printf '%s' "$text" | grep -q "$m1" && problems="$problems l'issue nomina il segnale di partenza (doveva fermarsi lì);"
  got="saltato $st_s, normale $st_n, partenza $st_m1; run di sentinella: saltato ${runs_s:-?}, normale ${runs_n:-?}; issue aperte ${open_n:-?}, commenti ${comments_n}"
  if [ -z "$problems" ]; then esito=riuscito; else esito="non riuscito:${problems%;}"; fi
  emit_row skip-ci "main (PR di partenza #$pr)" "$n_sha" "$got" \
    "saltato=failure, normale=failure, partenza=success, nessun run sul saltato, una sola issue che nomina il saltato" "$esito"
  echo "skip-ci: l'issue di sentinella resta aperta: la chiude il controller"
  close_open_prs
}

modo_caso() {
  local name="${1:-}"
  case " $CASES " in *" $name "*) ;; *) echo "caso sconosciuto: ${name:-<vuoto>} (vedi: $0 elenco)" >&2; exit 2 ;; esac
  TS="$(date +%Y%m%d-%H%M%S)"
  case "$name" in
    pulita-fissata) caso_pulita_fissata ;;
    rifiuto-v4) caso_rifiuto_v4 ;;
    rivalutazione) caso_rivalutazione ;;
    skip-ci) caso_skip_ci ;;
  esac
  return "$ROW_FAIL"
}

# ---------------------------------------------------------------- raccogli

modo_raccogli() {
  local label repo id conc ms total_ms=0 n=0 f hits=0 open_prs open_issues found
  rot "$OUT/gate-raccogli-versione.txt" "$OUT/gate-raccogli-minuti.txt" "$OUT/gate-raccogli-osservazioni.txt" "$OUT/gate-raccogli-stato-finale.txt"
  gh_call gate-raccogli-versione --version
  cp "$OUT/gate-raccogli-versione.out" "$OUT/gate-raccogli-versione.txt"
  gh_read gate-raccogli-runs run list --repo "$DET" --limit 200 --json databaseId,workflowName,event,headSha,headBranch,status,conclusion,createdAt,updatedAt
  gh_read gate-raccogli-pr pr list --repo "$DET" --state all --limit 200 --json number,title,state,headRefName,headRefOid,baseRefName,mergedAt
  gh_read gate-raccogli-pr-aperte pr list --repo "$DET" --state open --limit 200 --json number,title,state
  gh_read gate-raccogli-issue issue list --repo "$DET" --state open --limit 100 --json number,title
  gh_read gate-raccogli-permessi api "repos/$DET/actions/permissions"
  open_prs="$(jq 'length' "$OUT/gate-raccogli-pr-aperte.out" 2>/dev/null || echo '?')"
  open_issues="$(jq -r '[.[] | "#\(.number) \(.title)"] | join("; ")' "$OUT/gate-raccogli-issue.out" 2>/dev/null)"
  save_text "$OUT/gate-raccogli-stato-finale.txt" "PR aperte: $open_prs (atteso 0)" \
    "sha_pinning_required: $(jq -r '.sha_pinning_required // false' "$OUT/gate-raccogli-permessi.out" 2>/dev/null)" \
    "issue aperte: ${open_issues:-nessuna}" "stato di pin-on/pin-off: $([ -e "$STATE_FILE" ] && echo "PRESENTE in $STATE_FILE" || echo assente)"
  : > "$OUT/gate-raccogli-minuti.txt"
  if [ -s "$RUNS" ]; then
    while IFS=$'\t' read -r label repo id conc; do
      [ -n "$id" ] || continue
      gh_read "gate-raccogli-timing-$label-$id" api "repos/$repo/actions/runs/$id/timing"
      ms="$(jq -r '.run_duration_ms // 0' "$OUT/gate-raccogli-timing-$label-$id.out" 2>/dev/null)"
      case "$ms" in ''|*[!0-9]*) ms=0 ;; esac
      total_ms=$((total_ms + ms)); n=$((n + 1))
      printf '%s\t%s\trun %s\tconclusione %s\tdurata %s ms\n' "$label" "$repo" "$id" "$conc" "$ms" >> "$OUT/gate-raccogli-minuti.txt"
      # il log dei job (ledger, Task 3): checkout v7 con la chiamata API in più, download-artifact v8 con il digest
      gh_read "gate-log-$label-$id" run view "$id" --repo "$repo" --log
      [ "$RC" = 0 ] || gh_read "gate-log-$label-$id-failed" run view "$id" --repo "$repo" --log-failed
    done < "$RUNS"
  fi
  printf 'totale: %d run, %d ms di durata (circa %d minuti; l API dei minuti fatturati è 0 sui privati Free)\n' "$n" "$total_ms" $(( (total_ms + 59999) / 60000 )) >> "$OUT/gate-raccogli-minuti.txt"
  found="$(grep -a -i -n -E 'digest|mismatch|Cache mode:|Cache (restored|not found)|is not allowed|must be pinned|ref .*commit|fetch-depth' "$OUT"/gate-log-*.out 2>/dev/null | cut -c1-300)"
  { echo "# righe dei log dei job su digest, checkout e cache (osservazioni del ledger del Task 3)"; echo "${found:-(nessuna riga trovata)}"; } > "$OUT/gate-raccogli-osservazioni.txt"
  rot "$OUT/gate-raccogli-comandi-controllo.txt"
  env -u P4_OUT P4_WORK="$WORK" P4_PROFILE=p5 P5_PR_REGISTRY="$OUT/prs-aperte.txt" python3 -B -I "$GH4/ghguard.py" comandi "$OUT/comandi.log" \
    > "$OUT/gate-raccogli-comandi-controllo.txt" 2>&1 || echo "comandi.log: righe non ammesse (vedi gate-raccogli-comandi-controllo.txt)" >&2
  # nessuna forma di token nelle uscite di questa prova (stesso modello di run-p5-checks.sh cerca-token): solo i nomi dei file
  for f in "$OUT"/gate-*; do
    [ -f "$f" ] || continue
    if grep -aqE 'gh[pos]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|sk-ant-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}' "$f"; then
      echo "FORMA DI TOKEN in ${f#"$OUT/"}: da togliere prima del commit" >&2; hits=$((hits + 1))
    fi
  done
  cat "$OUT/gate-raccogli-stato-finale.txt" "$OUT/gate-raccogli-minuti.txt"
  [ "$hits" = 0 ]
}

# ---------------------------------------------------------------- modo controlla (nessuna rete)

# gh finto: nessuna rete; PR, merge e stati ricavati dallo stato dei nudi locali (vedi il testo del file). Lo scrive `controlla`.
write_fake_gh() { # <file>
  cat > "$1" <<'PY'
#!/usr/bin/env python3
"""Il finto di GitHub del modo controlla di run-p5-gate.sh: registra gli argomenti (separati da tab), nessuna rete.
Lo stato sta in P5_FAKE_STATE (prs.json, perm.json, issues.json, closed-<n>); i repo sono i nudi locali di P5_GIT_BASE.
Gli stati dei commit si ricavano dallo stato: le PR hanno guard, verdict e attention (un ramo non tg/* ha attention rossa),
ogni PATCH del corpo aggiunge pending e success di verdict, i commit di main hanno lo stato di sentinella che il codice di
tollgate darebbe (un commit con [skip ci] non ha run né stato)."""
import json
import os
import subprocess
import sys

args = sys.argv[1:]
state = os.environ.get("P5_FAKE_STATE", "/tmp/p5-gate-fake-state")
os.makedirs(state, exist_ok=True)
with open(os.environ["P5_FAKE_LOG"], "a") as fh:
    fh.write("".join(a + "\t" for a in args) + "\n")
base = os.environ.get("P5_GIT_BASE", "")
BARE = os.path.join(base, "ginz0ls", "tollgate-p4-detect.git")
BOT = "github-actions[bot]"
ENV = dict(os.environ, GIT_AUTHOR_NAME="fake", GIT_AUTHOR_EMAIL="fake@example.invalid",
           GIT_COMMITTER_NAME="fake", GIT_COMMITTER_EMAIL="fake@example.invalid")


def git(*a, check=True):
    r = subprocess.run(["git", "--git-dir", BARE, *a], capture_output=True, text=True, env=ENV)
    if check and r.returncode != 0:
        fail("git finto: " + r.stderr.strip())
    return r.stdout.strip()


def fail(msg, code=1):
    sys.stderr.write(msg + "\n")
    sys.exit(code)


def load(name, default):
    try:
        return json.load(open(os.path.join(state, name)))
    except (OSError, ValueError):
        return default


def save(name, data):
    json.dump(data, open(os.path.join(state, name), "w"))


def counter(name, start=0):
    n = int(open(os.path.join(state, name)).read()) if os.path.exists(os.path.join(state, name)) else start
    open(os.path.join(state, name), "w").write(str(n + 1))
    return n + 1


def opt(name):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else ""


def perm():
    return load("perm.json", {"enabled": True, "allowed_actions": "all", "sha_pinning_required": False})


def stamp(i):
    return "2099-01-01T%02d:%02d:%02dZ" % (i // 3600, i % 3600 // 60, i % 60)


def main_commits():
    out = git("log", "--first-parent", "--reverse", "--format=%H%x09%s", "refs/heads/main")
    return [tuple(line.split("\t", 1)) for line in out.splitlines() if line]


def sentinel_marks():
    """Come sentinel.run: ogni commit senza [skip ci] è un push; il suo intervallo parte dall'ultimo controllato."""
    prs = load("prs.json", [])
    verified = {p["merge_sha"] for p in prs if p.get("merge_sha")}
    marks, flagged, pending = {}, [], []
    for i, (sha, subject) in enumerate(main_commits()):
        pending.append(sha)
        if i == 0:
            marks[sha] = "success"
            pending = []
            continue
        if "[skip ci]" in subject:
            continue
        bad = [x for x in pending if x not in verified]
        for x in bad:
            marks[x] = "failure"
        if sha not in bad:
            marks[sha] = "success"
        flagged += bad
        pending = []
    return marks, flagged


def issues():
    out = load("issues.json", [])
    flagged = sentinel_marks()[1]
    if flagged and not os.path.exists(os.path.join(state, "closed-90")):
        out = out + [{"number": 90, "title": "tollgate: merge non verificato", "state": "OPEN",
                      "body": "## tollgate: merge non verificato\n\n" + "\n".join("- `%s`: nessuna PR unita" % s for s in flagged),
                      "comments": []}]
    return out


def statuses_for(sha):
    chrono = []
    for p in load("prs.json", []):
        if p["sha"] != sha:
            continue
        attention = "success" if p["head"].startswith("tg/") else "failure"
        chrono += [("tollgate/verdict", "pending"), ("tollgate/guard", "success"), ("tollgate/verdict", "success"),
                   ("tollgate/attention", attention)]
        for _ in range(p.get("edits", 0)):
            chrono += [("tollgate/verdict", "pending"), ("tollgate/guard", "success"), ("tollgate/verdict", "success")]
    mark = sentinel_marks()[0].get(sha)
    if mark:
        chrono.append(("tollgate/sentinel", mark))
    rows = [{"context": c, "state": s, "creator": BOT, "description": "finto", "created_at": stamp(i)} for i, (c, s) in enumerate(chrono)]
    return list(reversed(rows))


if not args:
    fail("gh finto: nessun argomento", 2)
first, second = args[0], (args[1] if len(args) > 1 else "")
if first == "--version":
    print("gh version 2.46.0 (finto)")
elif first == "api":
    method = opt("--method") or opt("-X") or "GET"
    ep = [a for a in args[1:] if a.startswith("repos/")][0]
    flat = "--jq" in args or "-q" in args
    if method == "GET":
        if ep.endswith("/branches/main/protection"):
            if "--include" in args:
                sys.stdout.write("HTTP/2.0 403 Forbidden\r\n\r\n")
            print(json.dumps({"message": "Upgrade to GitHub Pro or make this repository public to enable this feature.", "status": "403"}))
            fail("gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)")
        elif "/branches/" in ep:
            name = ep.split("/branches/", 1)[1]
            if subprocess.run(["git", "--git-dir", BARE, "rev-parse", "-q", "--verify", "refs/heads/" + name], capture_output=True).returncode != 0:
                fail("gh: Branch not found (HTTP 404)")
            print(json.dumps({"name": name}))
        elif ep.endswith("/actions/permissions"):
            print(json.dumps(perm()))
        elif ep.endswith("/timing"):
            print(json.dumps({"billable": {"UBUNTU": {"total_ms": 0}}, "run_duration_ms": 90000}))
        elif "/commits/" in ep and "/statuses" in ep:
            rows = statuses_for(ep.split("/commits/", 1)[1].split("/", 1)[0])
            for r in rows:
                print(json.dumps(r) if flat else json.dumps({**r, "creator": {"login": r["creator"]}}))
        elif "/issues/" in ep and ep.split("?")[0].endswith("/comments"):
            n = int(ep.split("/issues/", 1)[1].split("/", 1)[0])
            for p in load("prs.json", []):
                if p["number"] == n:
                    print(json.dumps({"id": n, "user": BOT, "body": "<!-- tollgate-verdict sha=%s -->\nNessuna voce." % p["sha"]}))
        else:
            print("{}")
    elif method == "PUT" and ep.endswith("/actions/permissions"):
        fields = {args[i + 1].split("=", 1)[0]: args[i + 1].split("=", 1)[1] for i, a in enumerate(args) if a == "-F"}
        cur = perm()
        cur["enabled"] = fields.get("enabled") == "true"
        cur["sha_pinning_required"] = fields.get("sha_pinning_required") == "true"
        if "allowed_actions" in fields:
            cur["allowed_actions"] = fields["allowed_actions"]
        save("perm.json", cur)
    elif method == "PATCH" and "/pulls/" in ep:
        n = int(ep.rsplit("/", 1)[1])
        prs = load("prs.json", [])
        for p in prs:
            if p["number"] == n:
                p["edits"] = p.get("edits", 0) + 1
        save("prs.json", prs)
        print("{}")
    else:
        fail("gh finto: scrittura non prevista: " + " ".join(args), 2)
elif first == "pr":
    prs = load("prs.json", [])
    if second == "create":
        head = opt("--head")
        sha = git("rev-parse", "-q", "--verify", "refs/heads/" + head)
        n = counter("pr", 10)
        prs.append({"number": n, "head": head, "sha": sha, "state": "OPEN", "merge_sha": None, "edits": 0})
        save("prs.json", prs)
        print("https://github.com/ginz0ls/tollgate-p4-detect/pull/%d" % n)
    else:
        n = int(args[2]) if len(args) > 2 and args[2].isdigit() else 0
        p = next((x for x in prs if x["number"] == n), None)
        if second == "view" and p:
            print(json.dumps({"state": p["state"], "mergeCommit": {"oid": p["merge_sha"]} if p["merge_sha"] else None}))
        elif second == "close" and p:
            p["state"] = "CLOSED"
            save("prs.json", prs)
        elif second == "merge" and p:
            tree = git("rev-parse", p["sha"] + "^{tree}")
            main = git("rev-parse", "refs/heads/main")
            merged = git("commit-tree", tree, "-p", main, "-m", "Merge PR #%d (squash)" % n)
            git("update-ref", "refs/heads/main", merged)
            p["state"], p["merge_sha"] = "MERGED", merged
            save("prs.json", prs)
        elif second == "list":
            want = opt("--state")
            print(json.dumps([{"number": x["number"], "title": "t", "state": x["state"]} for x in prs if want in ("all", "") or x["state"].lower() == want]))
        else:
            fail("gh finto: comando non previsto: " + " ".join(args), 2)
elif first == "issue":
    if second == "list":
        print(json.dumps([{"number": i["number"], "title": i["title"]} for i in issues()]))
    elif second == "view":
        n = int(args[2])
        found = [i for i in issues() if i["number"] == n]
        if not found:
            fail("gh: issue non trovata", 1)
        print(json.dumps({"body": "", "comments": [], **found[0]}))
    elif second == "close":
        open(os.path.join(state, "closed-%s" % args[2]), "w").write("1")
    else:
        fail("gh finto: comando non previsto: " + " ".join(args), 2)
elif first == "run":
    if second == "list":
        wf = opt("--workflow")
        open(os.path.join(state, "last-wf"), "w").write(wf)
        n = counter("run", 100)
        if wf == "tollgate-sentinel.yml":
            rows = [{"databaseId": 5000 + i, "headSha": s, "headBranch": "main", "event": "push", "status": "completed",
                     "conclusion": "success", "createdAt": "2099-01-01T00:00:00Z"}
                    for i, (s, subj) in enumerate(main_commits()) if i > 0 and "[skip ci]" not in subj]
            print(json.dumps(rows))
        else:
            ev = {"tollgate-guard.yml": "pull_request_target", "tollgate-verdict.yml": "workflow_run", "tollgate-run.yml": "pull_request"}.get(wf, "push")
            true = {"databaseId": n, "headSha": os.environ.get("P4_WAIT_SHA", ""), "headBranch": os.environ.get("P4_WAIT_BRANCH", ""),
                    "event": ev, "status": "completed", "conclusion": "success", "createdAt": "2099-01-01T00:00:00Z"}
            # un run più recente (id più alto) di un altro ramo nello stesso intervallo: l'aggancio deve scartarlo
            decoy = dict(true, databaseId=900000 + n, headSha="d" * 40, headBranch="tollgate-config/0.2.0", createdAt="2099-01-01T00:00:01Z")
            print(json.dumps([decoy, true]))
    elif second == "watch":
        print("Run completed (finto)")
    elif second == "view":
        last = open(os.path.join(state, "last-wf")).read() if os.path.exists(os.path.join(state, "last-wf")) else ""
        rejected = last == "p5-gate-rifiuto-v4.yml" and perm().get("sha_pinning_required")
        if "--log" in args or "--log-failed" in args:
            if rejected:
                print("prova\tSet up job\tThe action actions/checkout@v4 is not allowed in ginz0ls/tollgate-p4-detect because all actions must be pinned to a full-length commit SHA.")
            elif "--log-failed" not in args:
                print("verdict\tCache\tCache mode: read-only (finto)")
        else:
            print(json.dumps({"databaseId": int(args[2]), "workflowName": last, "event": "push", "headSha": os.environ.get("P4_WAIT_SHA", ""),
                              "headBranch": os.environ.get("P4_WAIT_BRANCH", ""), "status": "completed",
                              "conclusion": "failure" if rejected else "success", "createdAt": "2099-01-01T00:00:00Z",
                              "updatedAt": "2099-01-01T00:05:00Z", "jobs": [{"name": "verdict"}]}))
    else:
        fail("gh finto: comando non previsto: " + " ".join(args), 2)
else:
    fail("gh finto: comando non previsto: " + " ".join(args), 2)
PY
  chmod +x "$1"
}

# Prova negativa: ogni comando vietato deve fermare guard_args; ogni comando che lo script emette deve passare
check_negativi() { # <cartella> <numero di una PR registrata>
  local T="$1" pr="$2" n=0 stopped=0 ok=0 cmd
  local -x P5_PR_REGISTRY="$T/negativi-registro.txt"      # un registro a parte: le prove non toccano quello della prova
  printf 'pr %s\n' "$pr" > "$P5_PR_REGISTRY"
  local -a forbidden=(
    "issue create --repo $DET --title x" "pr edit 1 --repo $DET --body x" "pr merge 1 --repo $DET" "pr close 1 --repo $OWNER/tollgate-p4-protected"
    "pr list --repo $OWNER/tollgate-p4-protected" "pr comment 1 --repo $OWNER/tollgate" "issue delete 1 --repo $DET"
    "api --method PATCH repos/$DET/pulls/99999 -F body=@$OUT/x" "api --method DELETE repos/$DET" "api --method POST repos/$DET/issues"
    "api --method PUT repos/$DET/actions/permissions -F enabled=false" "api --method PUT repos/$DET/actions/permissions -F enabled=true -F sha_pinning_required=maybe"
    "api repos/$OWNER/tollgate-p4-protected/actions/permissions" "api --method DELETE repos/$DET/git/refs/heads/p5-gate-x" "api user" "api repos/$DET/actions/secrets"
    "repo delete $DET" "repo create $DET --private" "run delete 1 --repo $DET" "run cancel 1 --repo $DET" "auth login" "workflow run x.yml --repo $DET"
  )
  local -a allowed=(
    "--version" "api repos/$DET/actions/permissions" "api repos/$DET/branches/tollgate-config/0.2.0"
    "api --paginate repos/$DET/commits/0123456789abcdef0123456789abcdef01234567/statuses?per_page=100 --jq ."
    "api --paginate repos/$DET/issues/$pr/comments?per_page=100 --jq ." "api repos/$DET/actions/runs/5/timing"
    "api --method PUT repos/$DET/actions/permissions -F enabled=true -F sha_pinning_required=true -F allowed_actions=all"
    "api --method PUT repos/$DET/actions/permissions -F enabled=true -F sha_pinning_required=false"
    "api --method PATCH repos/$DET/pulls/$pr -F body=@$OUT/x.md" "pr create --repo $DET --base main --head tg/7-p5-gate-x --title t --body-file $OUT/x.md"
    "pr view $pr --repo $DET --json state,mergeCommit" "pr merge $pr --repo $DET --squash" "pr close $pr --repo $DET" "pr list --repo $DET --state open --limit 200 --json number,title,state"
    "issue list --repo $DET --state open --limit 100 --json number,title" "issue view 7 --repo $DET --json number,title,state,body,comments" "issue close 90 --repo $DET"
    "run list --repo $DET --workflow tollgate-sentinel.yml --limit 30 --json databaseId,headSha" "run watch 5 --repo $DET --exit-status" "run view 5 --repo $DET --log"
    "run view 5 --repo $DET --log-failed" "run view 5 --repo $DET --json databaseId,jobs" "run rerun 5 --repo $DET --failed"
  )
  for cmd in "${forbidden[@]}"; do
    n=$((n + 1))
    # shellcheck disable=SC2086
    if ( guard_args $cmd ) >/dev/null 2>&1; then echo "  NON FERMATO da guard_args: $cmd"; else stopped=$((stopped + 1)); fi
  done
  echo "  guard_args: $stopped fermati su $n"
  for cmd in "${allowed[@]}"; do
    # shellcheck disable=SC2086
    if ( guard_args $cmd ) >/dev/null 2>&1; then ok=$((ok + 1)); else echo "  AMMESSO MA RIFIUTATO: $cmd"; fi
  done
  echo "  comandi legittimi ammessi: $ok su ${#allowed[@]}"
  [ "$stopped" = "$n" ] && [ "$ok" = "${#allowed[@]}" ]
}

# Prova negativa dei comandi git con la rete: mai forzato, mai --delete, mai main fuori dal caso (lo ferma net_push), mai altri repo
check_git_negativi() {
  local n=0 stopped=0 args
  local -a forbidden=(
    "push --force $DET_URL main" "push -f $DET_URL main" "push $DET_URL +main" "push $DET_URL main:main" "push --mirror $DET_URL"
    "push --delete $DET_URL p5-gate-x" "push --delete $DET_URL main" "push --all $DET_URL" "push origin main" "pull $DET_URL" "fetch $DET_URL main"
    "push https://github.com/$OWNER/tollgate-p4-protected.git main" "push https://github.com/$OWNER/altro.git main" "ls-remote $DET_URL"
  )
  for args in "${forbidden[@]}"; do
    n=$((n + 1))
    # shellcheck disable=SC2086
    if python3 -B -I "$GH4/ghguard.py" gitcheck --dir "$WORK/gate-detect" -- $args >/dev/null 2>&1; then echo "  git NON FERMATO: $args"; else stopped=$((stopped + 1)); fi
  done
  echo "  git: $stopped fermati su $n"
  python3 -B -I "$GH4/ghguard.py" gitcheck --dir "$WORK/gate-detect" -- push "$DET_URL" tollgate-config/0.2.0 || { echo "  git legittimo rifiutato"; return 1; }
  [ "$stopped" = "$n" ]
}

# nudo locale di detect con il progetto di prova di P4 su main (come dopo P4, senza tollgate installato)
make_remote() { # <cartella dei nudi>
  local R="$1" tmp
  tmp="$R.costruzione"
  mkdir -p "$R/$OWNER" "$tmp/d"
  git init -q --bare -b main "$R/$OWNER/tollgate-p4-detect.git"
  git init -q -b main "$tmp/d"
  python3 -B "$P4/make_case.py" baseline detect "$tmp/d" >/dev/null || die "progetto di prova non scritto"
  git -C "$tmp/d" add -A && git -C "$tmp/d" -c user.name=t -c user.email=t@example.invalid commit -q -m "progetto di prova del gate (tollgate P4)" \
    && git -C "$tmp/d" push -q "$R/$OWNER/tollgate-p4-detect.git" main || die "nudo di detect non costruito"
}

modo_controlla() {
  local T rc=0 mode f url pr cmd forced
  bash -n "$here/run-p5-gate.sh" || die "bash -n fallito"
  T="${P5_CHECK_DIR:-$(mktemp -d /tmp/tollgate-p5-gate-controlla.XXXXXX)}"
  mkdir -p "$T/bin" "$T/remote" "$T/out" "$T/work" "$T/fake" "$T/stato"
  write_fake_gh "$T/bin/gh"
  make_remote "$T/remote"
  printf '[{"number": 7, "title": "prova P5: casi del gate", "state": "OPEN"}]\n' > "$T/fake/issues.json"
  export PATH="$T/bin:$PATH"
  [ "$(command -v gh)" = "$T/bin/gh" ] || die "il gh finto non è il primo nel PATH"
  export P5_CHECK=1 P5_OUT="$T/out" P5_WORK="$T/work" P5_GIT_BASE="$T/remote" P5_FAKE_LOG="$T/gh.log" P5_FAKE_STATE="$T/fake" \
         P5_GATE_STATE="$T/stato/pin-iniziale.env" P5_ISSUE=7 P5_WAIT_MAX=5 P5_POLL=0 P5_RETRY_SLEEP=0 P5_SETTLE=0
  : > "$P5_FAKE_LOG"
  OUT="$T/out"; WORK="$T/work"; export P4_OUT="$OUT" P4_WORK="$WORK" P5_PR_REGISTRY="$OUT/prs-aperte.txt"
  echo "cartella del controllo: $T"
  echo "--- elenco dei casi"
  modo_elenco | cut -f1,2 | sed 's/^/  /'
  run_mode() { # <nome> <argomenti...>: esito atteso 0
    local name="$1"; shift
    if bash "$here/run-p5-gate.sh" "$@" >"$T/modo-$name.log" 2>&1; then echo "modo $name: ok"
    else echo "modo $name: FALLITO (vedi $T/modo-$name.log)"; tail -n 5 "$T/modo-$name.log"; rc=1; fi
  }
  run_fails() { # <nome> <argomenti...>: esito atteso diverso da 0
    local name="$1"; shift
    if bash "$here/run-p5-gate.sh" "$@" >"$T/modo-$name.log" 2>&1; then echo "modo $name: DOVEVA FALLIRE"; rc=1
    else echo "modo $name: fermato come previsto"; fi
  }
  echo "--- rifiuti"
  run_fails pin-off-senza-stato pin-off
  grep -q 'mi rifiuto' "$T/modo-pin-off-senza-stato.log" && echo "pin-off: senza stato si rifiuta"
  [ ! -s "$T/fake/perm.json" ] && echo "pin-off: nessuna PUT senza stato"
  run_fails caso-sconosciuto caso non-esiste
  run_fails caso-senza-pin-on caso pulita-fissata
  local b
  for b in main 'a:b' '+main' '-f' ''; do      # net_push gira davvero: muore prima di toccare git (ALLOW_MAIN_PUSH vale 0 fuori da skip-ci)
    if ( net_push prova-rifiuto "$WORK/gate-detect" "$b" ) >/dev/null 2>&1; then echo "NET_PUSH NON RIFIUTATO: '$b'"; rc=1; fi
  done
  echo "net_push: main e rami con :, + o - rifiutati fuori da skip-ci"
  echo "--- modi"
  run_mode aggiorna aggiorna
  run_mode pin-on pin-on
  [ "$(jq -r '.sha_pinning_required' "$T/fake/perm.json")" = true ] && echo "pin-on: fissaggio acceso" || { echo "PIN-ON: NON ACCESO"; rc=1; }
  [ "$(sed -n 's/^PIN_INIT=//p' "$T/stato/pin-iniziale.env")" = false ] && echo "pin-on: valore iniziale salvato (false)" || { echo "PIN-ON: STATO NON SALVATO"; rc=1; }
  run_fails pin-on-due-volte pin-on
  [ "$(sed -n 's/^PIN_INIT=//p' "$T/stato/pin-iniziale.env")" = false ] && echo "pin-on: il secondo non sovrascrive il valore iniziale" || { echo "PIN-ON: VALORE INIZIALE PERSO"; rc=1; }
  for mode in pulita-fissata rifiuto-v4 rivalutazione skip-ci; do run_mode "caso-$mode" caso "$mode"; done
  run_fails caso-con-sentinella-aperta caso pulita-fissata
  grep -q "issue di sentinella aperta" "$T/modo-caso-con-sentinella-aperta.log" && echo "caso: con un'issue di sentinella aperta non parte"
  run_mode pin-off pin-off
  [ "$(jq -r '.sha_pinning_required' "$T/fake/perm.json")" = false ] && echo "pin-off: valore iniziale rimesso (false)" || { echo "PIN-OFF: VALORE NON RIMESSO"; rc=1; }
  ls "$T/stato"/pin-iniziale.env.rimesso-* >/dev/null 2>&1 && [ ! -e "$T/stato/pin-iniziale.env" ] && echo "pin-off: stato archiviato, non cancellato"
  run_mode raccogli raccogli
  echo "--- aggancio dei run per ramo"
  local rid bad=0
  for f in "$T"/out/gate-caso-pulita-fissata-*-guard-runid.txt "$T"/out/gate-caso-pulita-fissata-*-verdict-runid.txt; do
    rid="$(cat "$f" 2>/dev/null)"
    case "$rid" in ''|*[!0-9]*) bad=1 ;; *) [ "$rid" -lt 900000 ] || bad=1 ;; esac
  done
  [ "$bad" = 0 ] && echo "  guard e verdict agganciati per ramo: il run più recente di un altro ramo è scartato" || { echo "  AGGANCIO DI UN RUN DI UN ALTRO RAMO"; rc=1; }
  echo "--- rapporto"
  [ -f "$T/out/gate-casi-righe.md" ] && echo "  righe: $(wc -l < "$T/out/gate-casi-righe.md")"
  grep -c 'non riuscito' "$T/out/gate-casi-righe.md" | sed 's/^/  non riuscite: /'
  grep -q 'non riuscito' "$T/out/gate-casi-righe.md" && rc=1
  echo "  tentativi registrati: $(wc -l < "$T/out/gate-tentativi.tsv")"
  echo "--- attese andate a tetto nei modi (nel banco di prova non devono esserci)"
  if grep -l "non riuscita\|non comparso\|non comparsa\|non completato\|non determinato" "$T"/modo-*.log 2>/dev/null; then rc=1; else echo "  nessuna"; fi
  echo "--- stato finale del finto"
  [ "$(jq '[.[] | select(.state == "OPEN")] | length' "$T/fake/prs.json")" = 0 ] && echo "  nessuna PR aperta" || { echo "  PR APERTE ALLA FINE"; rc=1; }
  [ "$(git --git-dir "$T/remote/$OWNER/tollgate-p4-detect.git" log --first-parent --format=%s refs/heads/main | grep -c '\[skip ci\]')" = 1 ] \
    && echo "  un solo commit [skip ci] su main" || { echo "  COMMIT [skip ci] INATTESI"; rc=1; }
  [ "$(git --git-dir "$T/remote/$OWNER/tollgate-p4-detect.git" log --first-parent --format=%s refs/heads/main | grep -c 'prova P5 skip-ci')" = 2 ] \
    && echo "  su main: solo i due push diretti del caso (gli altri commit sono merge di PR)" || { echo "  COMMIT DIRETTI INATTESI SU MAIN"; rc=1; }
  [ -e "$T/fake/closed-90" ] && echo "  issue di sentinella: ancora aperta (la chiude il controller)" || echo "  issue di sentinella: aperta, come previsto"
  echo "--- registro dei comandi gh (profilo p5)"
  python3 -B -I "$GH4/ghguard.py" log "$P5_FAKE_LOG" || rc=1
  echo "--- comandi.log delle uscite (ogni gh e ogni git passa dalla guardia)"
  env -u P4_OUT P4_WORK="$T/work" python3 -B -I "$GH4/ghguard.py" comandi "$T/out/comandi.log" > "$T/comandi-controllo.txt" 2>&1 || { rc=1; cat "$T/comandi-controllo.txt"; }
  sed 's/^/  /' "$T/comandi-controllo.txt" | head -n 40
  echo "  righe RIFIUTATO nel registro: $(grep -c RIFIUTATO "$T/out/comandi.log")"
  grep -q RIFIUTATO "$T/out/comandi.log" && rc=1
  forced="$(grep -E 'git-net .* push ' "$T/out/comandi.log" | grep -cE -- ' (--force|-f|--delete|--mirror|--all)( |$)| \+|:refs/')"
  echo "  push forzati o con --delete nel registro: $forced"
  [ "$forced" = 0 ] || rc=1
  echo "  push nel registro: $(grep -cE 'git-net .* push ' "$T/out/comandi.log")"
  echo "  gh pr edit nel registro: $(grep -cE ' gh pr edit ' "$T/out/comandi.log")"
  grep -qE ' gh pr edit ' "$T/out/comandi.log" && rc=1
  echo "  gh issue close/create nel registro dello script: $(grep -cE ' gh issue (close|create) ' "$T/out/comandi.log")"
  grep -qE ' gh issue (close|create) ' "$T/out/comandi.log" && rc=1
  echo "--- prova negativa della guardia gh"
  pr="$(sed -n 's/^pr //p' "$T/out/prs-aperte.txt" | head -n 1)"
  check_negativi "$T" "${pr:-11}" || { echo "PROVA NEGATIVA FALLITA"; rc=1; }
  echo "--- prova negativa dei comandi git"
  check_git_negativi || { echo "PROVA NEGATIVA GIT FALLITA"; rc=1; }
  echo "--- remoti e rami nei nudi"
  echo "  detect: $(git --git-dir "$T/remote/$OWNER/tollgate-p4-detect.git" for-each-ref --format='%(refname:short)' refs/heads | sort | paste -sd, -)"
  echo "--- uscite attese"
  local missing=0
  for f in gate-aggiorna-init.out gate-aggiorna-statuses.out gate-aggiorna-merge-sha.txt gate-pin-iniziale.out gate-pin-on.rc gate-pin-off.rc gate-pin-dopo.out \
           gate-pin-stato.txt gate-casi-righe.md gate-tentativi.tsv gate-runs.tsv gate-raccogli-minuti.txt gate-raccogli-osservazioni.txt \
           gate-raccogli-stato-finale.txt gate-raccogli-comandi-controllo.txt comandi.log prs-aperte.txt; do
    [ -e "$T/out/$f" ] || { echo "  manca $f"; missing=1; }
  done
  ls "$T/out"/gate-caso-pulita-fissata-*-cache-mode.txt "$T/out"/gate-caso-rivalutazione-*-ordine.txt "$T/out"/gate-caso-rifiuto-v4-*-v4-log-failed.out \
     "$T/out"/gate-caso-skip-ci-*-issue-testo.out >/dev/null 2>&1 || { echo "  manca un'uscita dei casi"; missing=1; }
  [ "$missing" = 0 ] && echo "  tutte presenti"
  [ "$missing" = 0 ] || rc=1
  echo "--- remoti dei cloni"
  url="$(git -C "$T/work/gate-detect" remote get-url --push origin 2>&1)"
  echo "  gate-detect -> $url"
  case "$url" in "https://github.com/$DET.git") echo "  (l'origin resta l'URL vero: la rete è reindirizzata solo da GIT_CONFIG nell'ambiente dei git)" ;; *) echo "  ORIGIN INATTESO"; rc=1 ;; esac
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

# ---------------------------------------------------------------- dispatch

case "$MODE" in
  elenco) modo_elenco ;;
  controlla) modo_controlla ;;
  aggiorna|pin-on|pin-off|caso|raccogli)
    mkdir -p "$OUT" "$WORK"
    trap finish_mode EXIT
    log_cmd "(modo $MODE${ARG:+ $ARG})"       # segna l'inizio del modo in comandi.log: ghguard.py comandi ignora le righe che non sono gh o git-net
    "modo_${MODE//-/_}" "${2:-}" ;;
  *) echo "uso: $0 elenco|aggiorna|pin-on|pin-off|caso <nome>|raccogli|controlla" >&2; exit 2 ;;
esac
