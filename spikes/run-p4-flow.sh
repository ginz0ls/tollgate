#!/usr/bin/env bash
# spikes/run-p4-flow.sh — prova reale del flusso L1 con `claude -p` fino a PR e verdetto sul repo protected (Task 16,
# decisioni 26 e 27). Lo esegue solo il controller. Deriva da spikes/run-p3c-flow.sh, che resta com'è.
# Modo `controlla`: nessuna rete e nessun `claude`: i passi si stampano e basta.
# Uso: run-p4-flow.sh issue | prepara | shim | passo1 | passo2 | passo3 | attendi | passo4 | registra | controlla
#
#   issue     crea l'issue di prova sul repo protected (o si imposta P4_FLOW_ISSUE con un'issue creata dal controller)
#   prepara   clone di protected in /tmp/tollgate-p4/flow/protected, stato di prova con la sentinella (nessuna TOLLGATE_GH),
#             shim di gh (finto) e gh con guardia (il vero, dietro ghguard.py); l'issue la legge da P4_FLOW_ISSUE o dal file
#   shim      senza rete: il modello lancia `command -v gh` e `echo $PATH`; si confronta l'uscita del tool con lo shim
#   passo1    /tollgate:start #N L1 dal checkout
#   passo2    dal worktree: il piano (se non c'è) e /tollgate:execute
#   passo3    dal worktree: /tollgate:finish fino a `finish open-pr`, con il gh vero (solo su protected)
#   attendi   gli stati della PR (tetto P4_WAIT_MAX, 900 s): atteso guard e verdict `success` e il commento con lo SHA
#   passo4    solo se verdict è rosso: /tollgate:start #N e `task start --from-gate`, un solo giro
#   registra  versione di claude, sessioni, eventi, token (`tollgate stats`), PATH del tool Bash, comandi gh del modello
#
# Cautele: `claude -p` solo qui, solo da /tmp/tollgate-p4/flow e sempre con --plugin-dir (lo script lo controlla).
# Prima di ogni passo `git remote get-url --push origin` deve essere protected; TOLLGATE_GH non impostata. Il gh del
# modello è il wrapper con guardia (profilo flow: niente creazione di issue, merge, chiusure, scritture api); in più
# `--disallowedTools` per gh repo|api|auth|secret e `gh issue create`. Dopo ogni passo si confrontano i gh del modello e gli
# eventi `veto` ed `effect_*` con l'atteso, e lo script si ferma su un gh rivolto ad altro. Mai kill per nome.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
GH4="$here/gh-p4"
MODE="${1:-}"

OWNER=ginz0ls
PROT="$OWNER/tollgate-p4-protected"
DET="$OWNER/tollgate-p4-detect"
CHECK="${P4_CHECK:-0}"
FLOW=/tmp/tollgate-p4/flow
[ "$CHECK" = 1 ] && FLOW="${P4_FLOW:-$FLOW}"      # solo il modo controlla può usare un'altra cartella
OUT="${P4_OUT:-$root/docs/verifiche/evidenze/gh-p4}"
LOGS="$OUT/flusso"                                  # le uscite del flusso: mai cancellate, i file esistenti si rinominano
WORK="$FLOW"                                        # il clone è $FLOW/protected (common.sh lo cerca in $WORK/<repo>)
REPO="$FLOW/protected"
STATE="$FLOW/state"
SHIM="$FLOW/shim"                                   # in testa al PATH del solo passo `shim`: gh finto
GHBIN="$FLOW/ghbin"                                 # in testa al PATH degli altri passi: gh con guardia
export P4_OUT="$OUT" P4_WORK="$WORK" P4_TMP="$FLOW"     # P4_TMP: i file di ingresso di gh del flusso stanno solo qui sotto
WAIT_MAX="${P4_WAIT_MAX:-900}"
POLL="${P4_POLL:-10}"
RETRY_SLEEP="${P4_RETRY_SLEEP:-5}"
STEP_TIMEOUT="${P4_STEP_TIMEOUT:-1800}"
MODEL="${P4_MODEL:-sonnet}"
TOOLS="Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob"
# Divieti per Claude Code (prefissi `Bash(<comando>:*)`): gh pericolosi, git push forzato o verso main, gh per percorso o dietro un
# prefisso, impostazione inline di P4_*. Il formato non permette un jolly a metà comando né di vietare per regola ogni forma
# (`git push origin tg/7-x:main`, `bash -c '…'`): ciò che sfugge lo prende l'audit di `registra` (flowcheck.py audit) sul
# transcript e su gh-wrap.log, che rende la prova «non riuscita».
DISALLOWED="Bash(gh repo:*),Bash(gh api:*),Bash(gh auth:*),Bash(gh secret:*),Bash(gh issue create:*),\
Bash(git push --force:*),Bash(git push -f:*),Bash(git push --force-with-lease:*),Bash(git push --mirror:*),Bash(git push --delete:*),\
Bash(git push origin main:*),Bash(git push origin master:*),Bash(git push origin +:*),Bash(git push -u origin main:*),\
Bash(*/gh:*),Bash(command gh:*),Bash(env:*),Bash(exec:*),Bash(xargs:*),\
Bash(P4_PROFILE=:*),Bash(P4_REPO=:*),Bash(P4_REAL_GH=:*),Bash(P4_LOG=:*),Bash(P4_TMP=:*),Bash(export P4_:*)"
if [ "${PLUGIN_LINK:-0}" = 1 ]; then PLUGIN="$FLOW/plugin"; else PLUGIN="$root"; fi
REAL_GH="$(command -v gh 2>/dev/null || true)"
TG=(python3 -B "$PLUGIN/bin/tollgate")

. "$GH4/common.sh"

# ---------------------------------------------------------------- guardie

verifica_push() { check_remote protected || die "git remote get-url --push origin non è protected: mi fermo"; }

verifica_env() {
  [ -z "${TOLLGATE_GH:-}" ] || die "TOLLGATE_GH è impostata: il flusso usa il gh vero (decisione 27)"
  [ -z "${TOLLGATE_TEST_CONFIG:-}" ] || die "TOLLGATE_TEST_CONFIG è impostata"
  [ -f "$STATE/.tollgate-test" ] || die "manca lo stato di prova con la sentinella: lancia prepara"
}

verifica_gh() { # <cartella dei gh>: il primo gh del PATH dei claude -p è quello atteso
  local found; found="$(PATH="$1:$PATH" command -v gh 2>/dev/null)"
  [ "$found" = "$1/gh" ] || die "command -v gh = '$found', atteso '$1/gh'"
}

issue_number() {
  local n="${P4_FLOW_ISSUE:-}"
  [ -n "$n" ] || n="$(sed -n 's/^ISSUE=//p' "$LOGS/issue.env" 2>/dev/null | tail -n 1)"
  case "$n" in ''|*[!0-9]*) die "manca il numero dell'issue di prova: modo issue, o P4_FLOW_ISSUE=<N>" ;; esac
  echo "$n"
}

worktree_lavoro() { # il worktree del ramo tg/<N>-*, sempre sotto $FLOW
  local n wt; n="$(issue_number)" || return 1
  wt="$(git -C "$REPO" worktree list --porcelain | awk -v p="refs/heads/tg/$n-" '/^worktree /{w=substr($0,10)} /^branch /{ if (index(substr($0,8), p) == 1) print w }' | head -n 1)"
  case "$wt" in "$FLOW"/*) echo "$wt" ;; *) echo "worktree del lavoro non trovato: '$wt'" >&2; return 1 ;; esac
}

# ---------------------------------------------------------------- un passo con claude -p

# claude_step <id> <cartella> <cartella dei gh> <strumenti> <prompt>
claude_step() {
  local id="$1" dir="$2" bindir="$3" tools="$4" prompt="$5" rc=0 cmd
  case "$FLOW" in /tmp/tollgate-p4/flow) ;; *) [ "$CHECK" = 1 ] || die "cartella di lavoro inattesa: $FLOW" ;; esac
  case "$dir" in "$FLOW"|"$FLOW"/*) ;; *) die "claude -p solo da $FLOW: $dir è altrove" ;; esac
  verifica_push; verifica_env; verifica_gh "$bindir"
  mkdir -p "$LOGS"
  rot "$LOGS/$id.jsonl" "$LOGS/$id.err" "$LOGS/$id.argv"
  cmd=(claude -p --plugin-dir "$PLUGIN" --model "$MODEL" --permission-mode acceptEdits --allowedTools "$tools"
       --disallowedTools "$DISALLOWED" --output-format stream-json --verbose --include-hook-events "$prompt")
  case " ${cmd[*]} " in *" --plugin-dir "*) ;; *) die "claude -p senza --plugin-dir" ;; esac
  { printf 'cwd: %s\nPATH in testa: %s\n' "$dir" "$bindir"; printf '%q ' "${cmd[@]}"; printf '\n'; } > "$LOGS/$id.argv"
  log_cmd "claude -p $id (cwd $dir, PATH $bindir)"
  if [ "$CHECK" = 1 ]; then
    check_canned "$id" "$dir" "$bindir"
  else
    # profilo, repo, gh vero e registro non passano dall'ambiente: li fissa il wrapper generato da prepara
    ( cd "$dir" && env -u TOLLGATE_GH -u TOLLGATE_TEST_CONFIG -u P4_PROFILE -u P4_REPO -u P4_REAL_GH -u P4_LOG \
        PATH="$bindir:$PATH" TOLLGATE_STATE="$STATE" \
        timeout "$STEP_TIMEOUT" "${cmd[@]}" < /dev/null ) > "$LOGS/$id.jsonl" 2> "$LOGS/$id.err"
    rc=$?
  fi
  echo "$id: uscita $rc (cwd $dir)" | tee -a "$LOGS/exit-codes.txt"
  verifica_push
  return "$rc"
}

# post_passo <id> <atteso degli effetti: nessuno|open-pr>: eventi del DB, comandi Bash e gh del modello; si ferma su un gh rivolto ad altro
post_passo() {
  local id="$1" expected="$2" rc=0
  rot "$LOGS/events-$id.jsonl" "$LOGS/events-$id.err" "$LOGS/$id-eventi.txt" "$LOGS/$id-gh-modello.txt" "$LOGS/$id-comandi-bash.txt"
  ( cd "$REPO" && env -u TOLLGATE_GH TOLLGATE_STATE="$STATE" "${TG[@]}" events ) > "$LOGS/events-$id.jsonl" 2> "$LOGS/events-$id.err"
  python3 -B -I "$GH4/flowcheck.py" commands "$LOGS/$id.jsonl" > "$LOGS/$id-comandi-bash.txt" 2>&1
  python3 -B -I "$GH4/flowcheck.py" events "$LOGS/events-$id.jsonl" "$expected" > "$LOGS/$id-eventi.txt" 2>&1 || rc=1
  python3 -B -I "$GH4/flowcheck.py" gh "$LOGS/$id.jsonl" > "$LOGS/$id-gh-modello.txt" 2>&1 || rc=1
  rot "$LOGS/$id-audit.txt"
  python3 -B -I "$GH4/flowcheck.py" audit "$LOGS" "$LOGS/gh-wrap.log" > "$LOGS/$id-audit.txt" 2>&1 || rc=1
  [ "$rc" = 0 ] || { echo "STOP dopo $id: un gh del modello non è ammesso o gli eventi non sono quelli attesi (vedi $LOGS/$id-gh-modello.txt, $id-audit.txt e $id-eventi.txt)" >&2; return 1; }
  return 0
}

# ---------------------------------------------------------------- modi

modo_issue() {
  require_cmds
  mkdir -p "$LOGS"
  gh_call flusso-issue-create issue create --repo "$PROT" --title "prova P4 del flusso: dividi(a, b) in src/calc.py" \
    --body "Aggiungere la funzione dividi(a, b) a src/calc.py con il test test_dividi in tests/test_calc.py (dividi(6, 3) == 2). La divisione per zero solleva l'errore di Python, senza controlli. Nessun altro file."
  [ "$RC" = 0 ] || die "creazione dell'issue fallita (vedi flusso-issue-create.err)"
  local n; n="$(tail -n 1 "$OUT/flusso-issue-create.out")"; n="${n##*/}"
  case "$n" in ''|*[!0-9]*) die "numero dell'issue non leggibile" ;; esac
  printf 'ISSUE=%s\n' "$n" >> "$LOGS/issue.env"
  echo "issue di prova: #$n"
}

require_cmds() { local t; for t in jq git python3; do command -v "$t" >/dev/null 2>&1 || die "manca $t"; done; }

modo_prepara() {
  require_cmds
  case "$FLOW" in /tmp/tollgate-p4/flow) ;; *) [ "$CHECK" = 1 ] || die "cartella di lavoro inattesa: $FLOW" ;; esac
  mkdir -p "$FLOW" "$LOGS" "$STATE" "$SHIM" "$GHBIN"
  : > "$STATE/.tollgate-test"
  # nessun rm: un clone che esiste già si rinomina, come le uscite
  if [ -d "$REPO/.git" ]; then
    check_remote protected || die "il clone esistente non ha il remoto atteso: mi fermo"
  fi
  clone_or_update protected
  check_remote protected || die "il remoto del clone non è quello atteso: mi fermo"
  printf '#!/bin/sh\nexec python3 "%s" "$@"\n' "$root/tests/fakegh.py" > "$SHIM/gh" && chmod +x "$SHIM/gh" || die "shim non scritto"
  [ -n "$REAL_GH" ] || die "gh non trovato nel PATH"
  # il gh del flusso fissa profilo, repo, gh vero e registro nel file stesso (sola lettura): l'ambiente del modello non li cambia
  python3 -B -I "$GH4/ghwrap.py" make-wrapper "$GHBIN/gh" --real "$REAL_GH" --repo "$PROT" --profile flow \
    --log "$LOGS/gh-wrap.log" --tmp "$FLOW" || die "gh con guardia non generato"
  [ "$PLUGIN" = "$root" ] || ln -sfn "$root" "$PLUGIN"
  git -C "$REPO" cat-file -e origin/main:.github/workflows/tollgate-guard.yml 2>/dev/null \
    || die "tollgate non è installato su protected: lancia prima run-p4-gate.sh installa protected"
  verifica_gh "$SHIM"; verifica_gh "$GHBIN"; verifica_env
  save_text "$LOGS/prepara.txt" "clone: $REPO ($(git -C "$REPO" rev-parse origin/main))" "stato: $STATE" "shim: $SHIM/gh" \
    "gh con guardia: $GHBIN/gh (gh vero: $REAL_GH)" "plugin: $PLUGIN" "issue: $(issue_number 2>/dev/null || echo 'non ancora: modo issue')"
  echo "pronto: $REPO"
}

modo_shim() {
  require_cmds
  verifica_gh "$SHIM"
  claude_step shim "$REPO" "$SHIM" "Bash" \
    'Esegui con lo strumento Bash, in due comandi separati, `command -v gh` e `echo "$PATH"`. Riporta le due uscite così come sono, senza altro testo.' || return 1
  rot "$LOGS/shim-esito.txt"
  python3 -B -I "$GH4/flowcheck.py" shim "$LOGS/shim.jsonl" "$SHIM/gh" > "$LOGS/shim-esito.txt" 2>&1
  local rc=$?
  cat "$LOGS/shim-esito.txt"
  post_passo shim nessuno || return 1
  return "$rc"
}

passo1() {
  local n; n="$(issue_number)" || return 1
  claude_step passo1 "$REPO" "$GHBIN" "$TOOLS" "/tollgate:start #$n L1" || return 1
  post_passo passo1 nessuno
}

passo2() {
  local n wt; n="$(issue_number)" || return 1; wt="$(worktree_lavoro)" || return 1
  case "$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)" in tg/"$n"-*) ;; *) die "$wt non è sul ramo tg/$n-*" ;; esac
  claude_step passo2 "$wt" "$GHBIN" "$TOOLS" \
    "Per l'issue #$n: se il piano non è già scritto e committato in docs/superpowers/plans/, scrivilo con lo strumento Write (le sezioni sono quelle di plan-check; scope: src/calc.py e tests/test_calc.py; must-have: tests.test_calc.CalcTest::test_dividi) e committalo. Poi esegui /tollgate:execute fino alla chiusura di tutti i task. Non lanciare /tollgate:finish." || return 1
  post_passo passo2 nessuno
}

passo3() {
  local wt; wt="$(worktree_lavoro)" || return 1
  claude_step passo3 "$wt" "$GHBIN" "$TOOLS" "/tollgate:finish" || return 1
  post_passo passo3 open-pr
}

# attendi: la PR del ramo del lavoro, gli stati con autore, i commenti, la forma di GET pulls/<n>, i run e i minuti
modo_attendi() {
  local n wt branch sha pr label=flusso-attendi head verdict marker ok=1 c
  require_cmds
  n="$(issue_number)" || return 1; wt="$(worktree_lavoro)" || return 1
  branch="$(git -C "$wt" rev-parse --abbrev-ref HEAD)"; head="$(git -C "$wt" rev-parse HEAD)"
  gh_call "$label-pr-list" pr list --repo "$PROT" --head "$branch" --state all --limit 100 \
    --json number,state,url,headRefOid,mergedAt,isCrossRepository
  # si aggancia la PR con il numero più alto dello stesso repo la cui testa è lo SHA locale: mai il «più recente» per ripiego
  pr="$(jq -r --arg s "$head" '[.[] | select(.isCrossRepository == false and .headRefOid == $s)] | max_by(.number) | .number // empty' \
    "$OUT/$label-pr-list.out" 2>/dev/null)"
  [ -n "$pr" ] || die "nessuna PR aperta da $branch con la testa $head (vedi $label-pr-list.out)"
  sha="$head"
  export P4_WAIT_SHA="$sha" P4_WAIT_PR="$pr"
  [ "$CHECK" != 1 ] || { export P4_FAKE_SEED="$P4_FAKE_STATE/seed-flow"; }
  await_statuses "$PROT" "$sha" tollgate/guard tollgate/verdict tollgate/attention || echo "stati non completi entro ${WAIT_MAX}s" >&2
  statuses "$label-statuses" "$PROT" "$sha"
  await_comments "$PROT" "$pr" "<!-- tollgate-verdict sha=$sha -->" || echo "commento del verdetto non comparso" >&2
  gh_call "$label-comments" api --paginate "repos/$PROT/issues/$pr/comments?per_page=100" --jq "$COMMENT_JQ"
  gh_call "$label-pulls" api "repos/$PROT/pulls/$pr"
  gh_call "$label-merge-state" pr view "$pr" --repo "$PROT" --json mergeStateStatus,state,headRefOid
  pr_runs "$label" "$PROT" "$sha" "$pr"
  verdict="$(jq -rs 'map(select(.context == "tollgate/verdict")) | .[0].state // "none"' "$OUT/$label-statuses.out")"
  for c in tollgate/guard tollgate/verdict; do
    [ "$(jq -rs --arg c "$c" 'map(select(.context == $c)) | .[0].state // "none"' "$OUT/$label-statuses.out")" = success ] || ok=0
  done
  marker="$(jq -rs --arg m "<!-- tollgate-verdict sha=$sha -->" 'map(select(.user == "github-actions[bot]" and (.body | ltrimstr("\n") | startswith($m)))) | length' "$OUT/$label-comments.out" 2>/dev/null)"
  [ "${marker:-0}" -ge 1 ] || ok=0
  rot "$LOGS/attendi-esito.txt"
  {
    echo "PR #$pr, ramo $branch, testa $sha (issue #$n)"
    echo "atteso: tollgate/guard success, tollgate/verdict success, commento del bot con il marcatore e lo SHA della testa"
    echo "ottenuto:"
    jq -rs 'map({context, state, creator}) | unique_by(.context) | .[] | "  \(.context) = \(.state) (\(.creator))"' "$OUT/$label-statuses.out"
    echo "  commenti del bot con il marcatore e lo SHA: ${marker:-0}"
    echo "esito: $([ "$ok" = 1 ] && echo riuscito || echo "non riuscito (verdict: $verdict)")"
  } > "$LOGS/attendi-esito.txt"
  cat "$LOGS/attendi-esito.txt"
  save_text "$LOGS/pr.env" "PR=$pr" "SHA=$sha" "BRANCH=$branch" "VERDICT=$verdict"
  [ "$ok" = 1 ]
}

passo4() {
  local n wt verdict
  n="$(issue_number)" || return 1
  verdict="$(sed -n 's/^VERDICT=//p' "$LOGS/pr.env" 2>/dev/null | tail -n 1)"
  [ -n "$verdict" ] || die "manca $LOGS/pr.env: lancia prima attendi"
  if [ "$verdict" = success ]; then echo "verdict verde: il passo 4 non serve"; return 0; fi
  claude_step passo4a "$REPO" "$GHBIN" "$TOOLS" "/tollgate:start #$n" || return 1
  post_passo passo4a open-pr || return 1
  wt="$(worktree_lavoro)" || return 1
  claude_step passo4b "$wt" "$GHBIN" "$TOOLS" \
    "Il gate ha dato verdict rosso sulla PR del lavoro #$n. Lancia dal worktree python3 \"$PLUGIN/bin/tollgate\" task start --from-gate, esegui UN solo giro di correzione (implementatore, revisione, task done) e fermati: non lanciare /tollgate:finish e non fare altri giri." || return 1
  post_passo passo4b open-pr
}

modo_registra() {
  require_cmds
  mkdir -p "$LOGS"
  rot "$LOGS/versione-claude.txt" "$LOGS/sessioni.txt" "$LOGS/stats.json" "$LOGS/stats.err" "$LOGS/status.txt" \
    "$LOGS/git-log-worktree.txt" "$LOGS/events.jsonl" "$LOGS/events.err" "$LOGS/hooks.log" "$LOGS/skipped.log" \
    "$LOGS/audit.txt" "$LOGS/audit-esito.txt"
  if [ "$CHECK" != 1 ] && command -v claude >/dev/null 2>&1; then timeout 30 claude --version > "$LOGS/versione-claude.txt" 2>&1 < /dev/null; fi
  ( cd "$REPO" && env -u TOLLGATE_GH TOLLGATE_STATE="$STATE" "${TG[@]}" events > "$LOGS/events.jsonl" 2> "$LOGS/events.err"
    env -u TOLLGATE_GH TOLLGATE_STATE="$STATE" "${TG[@]}" stats > "$LOGS/stats.json" 2> "$LOGS/stats.err"
    env -u TOLLGATE_GH TOLLGATE_STATE="$STATE" "${TG[@]}" status > "$LOGS/status.txt" 2>&1 )
  local wt; wt="$(worktree_lavoro 2>/dev/null)" && git -C "$wt" log --format='%h %s' > "$LOGS/git-log-worktree.txt" 2>&1
  python3 -B -I "$GH4/flowcheck.py" sessions "$LOGS" > "$LOGS/sessioni.txt"
  [ -f "$STATE/hook-errors.log" ] && cp "$STATE/hook-errors.log" "$LOGS/hooks.log" || : > "$LOGS/hooks.log"
  [ -f "$STATE/skipped.log" ] && cp "$STATE/skipped.log" "$LOGS/skipped.log"
  # audit a valle: wrapper e transcript contro le forme ammesse; una voce fuori elenco rende la prova non riuscita
  python3 -B -I "$GH4/flowcheck.py" audit "$LOGS" "$LOGS/gh-wrap.log" > "$LOGS/audit.txt" 2>&1
  local audit_rc=$?
  save_text "$LOGS/audit-esito.txt" "$(tail -n 1 "$LOGS/audit.txt")"
  cat "$LOGS/audit.txt"
  save_text "$LOGS/ricapitolo.txt" "versione di claude: $(cat "$LOGS/versione-claude.txt" 2>/dev/null)" \
    "sessioni (passo, id, cartella):" "$(cat "$LOGS/sessioni.txt")" \
    "uscite dei passi: $(cat "$LOGS/exit-codes.txt" 2>/dev/null | tr '\n' ';')" \
    "uscita del tool Bash per \`command -v gh\` (passo shim): $(sed -n 's/^uscita del tool: //p' "$LOGS/shim-esito.txt" 2>/dev/null)"
  echo "registrato in $LOGS"
  [ "$audit_rc" = 0 ] || { echo "AUDIT NON RIUSCITO: la prova del flusso è non riuscita (vedi $LOGS/audit.txt)" >&2; return 1; }
}

# ---------------------------------------------------------------- controlla (nessuna rete, nessun claude)

# check_canned <id> <cartella> <cartella dei gh>: nel modo controlla un passo non lancia claude; scrive un'uscita stream-json
# di esempio (una sessione, uno shim o un gh ammesso) e, per i passi che cambiano il repo, ne simula l'effetto sul banco locale
check_canned() {
  local id="$1" dir="$2" bindir="$3" n tool_use result branch
  n="$(issue_number 2>/dev/null || echo 7)"
  branch="tg/$n-prova"
  case "$id" in
    shim) tool_use='command -v gh'; result="$bindir/gh" ;;
    *) tool_use='gh pr list --head '"$branch"' --state all --limit 100 --json number,state,url,headRefOid,mergedAt,isCrossRepository'; result='[]' ;;
  esac
  [ "$id" = shim ] || printf '%s gh pr list --head %s --state all --limit 100 --json number,state,url,headRefOid,mergedAt,isCrossRepository --repo %s\n' \
    "$(date -u +%FT%TZ)" "$branch" "$PROT" >> "$LOGS/gh-wrap.log"
  python3 -B - "$LOGS/$id.jsonl" "$id" "$dir" "$tool_use" "$result" <<'PY'
import json, sys
path, sid, cwd, command, result = sys.argv[1:6]
lines = [{"type": "system", "subtype": "init", "session_id": "finto-" + sid, "cwd": cwd},
         {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": command}}]}},
         {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": result}]}}]
open(path, "w").write("".join(json.dumps(x) + "\n" for x in lines))
PY
  case "$id" in
    passo1)    # il lavoro: worktree e ramo
      git -C "$REPO" worktree add -q -b "$branch" "$REPO/.claude/worktrees/tg-$n-prova" origin/main || die "worktree non creato" ;;
    passo3)    # la PR: ramo spinto e PR aperta (il gh del finto passa dalla guardia come in gh_call)
      git -C "$REPO/.claude/worktrees/tg-$n-prova" -c user.name=fake -c user.email=fake@example.invalid \
        commit -q --allow-empty -m "lavoro di prova" || die "commit non creato"
      check_remote protected || die "remoto non atteso"
      git -C "$REPO/.claude/worktrees/tg-$n-prova" push -q origin "$branch" || die "push di prova fallito"
      printf 'corpo di prova\n' > "$OUT/check-body.md"
      gh_call check-pr-create pr create --repo "$PROT" --base main --head "$branch" --title "prova" --body-file "$OUT/check-body.md" ;;
  esac
}

write_fake_gh() { cp "$GH4/fakegh.sh" "$1" && chmod +x "$1"; }

modo_controlla() {
  local T rc=0 f
  bash -n "$here/run-p4-flow.sh" || die "bash -n fallito"
  T="${P4_CHECK_DIR:-$(mktemp -d /tmp/tollgate-p4-flow-controlla.XXXXXX)}"
  mkdir -p "$T/bin" "$T/remote" "$T/out" "$T/flow"
  write_fake_gh "$T/bin/gh"
  export P4_CHECK=1 P4_OUT="$T/out" P4_WORK="$T/flow" P4_FLOW="$T/flow" P4_GIT_BASE="$T/remote" \
         P4_FAKE_LOG="$T/gh.log" P4_FAKE_STATE="$T/fake" P4_WAIT_MAX=5 P4_POLL=0 P4_RETRY_SLEEP=0
  export PATH="$T/bin:$PATH"
  [ "$(command -v gh)" = "$T/bin/gh" ] || die "il gh finto non è il primo nel PATH"
  : > "$P4_FAKE_LOG"
  echo "cartella del controllo: $T"
  local bare="$T/remote/$PROT.git" tmp
  mkdir -p "$(dirname "$bare")"; git init -q --bare -b main "$bare"
  tmp="$(mktemp -d)"; git clone -q "$bare" "$tmp/s" 2>/dev/null
  mkdir -p "$tmp/s/.github/workflows"; echo "name: tollgate-guard" > "$tmp/s/.github/workflows/tollgate-guard.yml"
  echo "# protected" > "$tmp/s/README.md"; git -C "$tmp/s" add -A
  git -C "$tmp/s" -c user.name=fake -c user.email=fake@example.invalid commit -qm init
  git -C "$tmp/s" branch -M main; git -C "$tmp/s" push -q origin main
  mkdir -p "$T/fake"
  # le risposte del gh finto per attendi: stati e commento attesi, con lo SHA della testa
  printf '%s\n' '{"context":"tollgate/guard","state":"success","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}' \
    '{"context":"tollgate/verdict","state":"success","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}' \
    '{"context":"tollgate/attention","state":"success","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}' > "$T/fake/seed-flow.statuses"
  printf '%s\n' '"<!-- tollgate-verdict"' > "$T/fake/seed-flow.comments"
  echo 1 > "$T/fake/seed-flow.pr"
  export P4_FLOW_ISSUE=7
  LOGS_CHECK="$T/out/flusso"
  echo "--- i gh che il flusso di tollgate fa davvero, ognuno passato da ghguard.py (profilo flow)"
  python3 -B -I "$GH4/flowcheck.py" shapes | sed 's/^/  /' > "$T/shapes.txt"; [ "${PIPESTATUS[0]}" = 0 ] || rc=1
  cut -c1-150 "$T/shapes.txt"
  echo "--- modi"
  run_mode() { # <modo>
    if bash "$here/run-p4-flow.sh" "$1" >"$T/modo-$1.log" 2>&1; then echo "modo $1: ok"
    else echo "modo $1: FALLITO (vedi $T/modo-$1.log)"; tail -n 6 "$T/modo-$1.log"; rc=1; fi
  }
  for f in prepara shim passo1 passo2 passo3 attendi passo4; do run_mode "$f"; done
  cp "$T/out/flusso/attendi-esito.txt" "$T/attendi-verde.txt"
  # il ramo del verdict rosso: attendi lo dichiara non riuscito (uscita 1) e passo4 fa i due passi di correzione
  printf '%s\n' '{"context":"tollgate/guard","state":"success","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}' \
    '{"context":"tollgate/verdict","state":"failure","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}' \
    '{"context":"tollgate/attention","state":"success","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}' > "$T/fake/seed-flow.statuses"
  if bash "$here/run-p4-flow.sh" attendi >"$T/modo-attendi-rosso.log" 2>&1; then
    echo "modo attendi (verdict rosso): doveva uscire con 1"; rc=1
  else echo "modo attendi (verdict rosso): ok (uscita 1, come atteso)"; fi
  run_mode passo4
  grep -q -- '--from-gate' "$LOGS_CHECK/passo4b.argv" 2>/dev/null || { echo "  passo4b senza task start --from-gate"; rc=1; }
  run_mode registra
  run_mode registra            # una seconda registra non perde le uscite della prima (rotazione)
  ls "$LOGS_CHECK"/events.jsonl.prev-* "$LOGS_CHECK"/audit.txt.prev-* >/dev/null 2>&1 || { echo "  la seconda registra non ha ruotato le uscite"; rc=1; }
  # un transcript con un gh per percorso e un git push forzato verso main: l'audit di registra deve dire «non riuscito»
  python3 -B - "$LOGS_CHECK/passo9.jsonl" <<'PY'
import json, sys
cmds = ["/usr/bin/gh pr merge 5 --squash", "git push --for" + "ce origin main"]
lines = [{"type": "system", "subtype": "init", "session_id": "finto-9", "cwd": "/x"}]
for i, c in enumerate(cmds):
    lines.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "h%d" % i, "name": "Bash", "input": {"command": c}}]}})
open(sys.argv[1], "w").write("".join(json.dumps(x) + "\n" for x in lines))
PY
  if bash "$here/run-p4-flow.sh" registra >"$T/modo-registra-ostile.log" 2>&1; then
    echo "modo registra (transcript ostile): doveva uscire con 1"; rc=1
  else echo "modo registra (transcript ostile): ok (audit non riuscito, come atteso)"; fi
  grep -q 'git push --for' "$LOGS_CHECK/audit.txt" && grep -q 'audit: non riuscito' "$LOGS_CHECK/audit.txt" || { echo "  l'audit non ha segnalato il transcript ostile"; rc=1; }
  mv "$LOGS_CHECK/passo9.jsonl" "$LOGS_CHECK/passo9.ostile.txt"
  echo "--- attese andate a tetto nei modi (nel banco di prova non devono esserci)"
  if grep -l "non completi\|non comparso\|non comparsi\|non completato" "$T"/modo-*.log 2>/dev/null; then rc=1; else echo "  nessuna"; fi
  echo "--- i comandi claude che verrebbero lanciati"
  for f in "$T/out/flusso"/*.argv; do echo "  $(basename "$f" .argv):"; sed 's/^/    /' "$f" | cut -c1-260; done
  echo "--- controlli sui comandi claude"
  for f in "$T/out/flusso"/*.argv; do
    grep -q -- '--plugin-dir' "$f" || { echo "  senza --plugin-dir: $f"; rc=1; }
    grep -q -- "cwd: $T/flow" "$f" || { echo "  cartella fuori da $T/flow: $f"; rc=1; }
    grep -q -- '--disallowedTools' "$f" || { echo "  senza --disallowedTools: $f"; rc=1; }
  done
  [ -z "${TOLLGATE_GH:-}" ] || { echo "  TOLLGATE_GH impostata"; rc=1; }
  echo "--- registro dei comandi gh dello script"
  python3 -B -I "$GH4/ghguard.py" log "$P4_FAKE_LOG" || rc=1
  echo "--- comandi.log delle uscite"
  env -u P4_OUT P4_WORK="$T/flow" python3 -B -I "$GH4/ghguard.py" comandi "$T/out/comandi.log" > "$T/comandi-controllo.txt" 2>&1 || rc=1
  sed 's/^/  /' "$T/comandi-controllo.txt"
  grep -q RIFIUTATO "$T/out/comandi.log" 2>/dev/null && { echo "  righe RIFIUTATO nel registro"; rc=1; }
  echo "--- esito di attendi e dello shim"
  sed 's/^/  /' "$T/attendi-verde.txt" "$T/out/flusso/shim-esito.txt"
  grep -q 'esito: riuscito' "$T/attendi-verde.txt" || rc=1
  grep -q 'esito: non riuscito (verdict: failure)' "$T/out/flusso/attendi-esito.txt" || { echo "  attendi con verdict rosso non lo dichiara"; rc=1; }
  grep -q 'uguali: sì' "$T/out/flusso/shim-esito.txt" || rc=1
  echo "--- remoto del clone"
  f="$(git -C "$T/flow/protected" remote get-url --push origin 2>&1)"; echo "  protected -> $f"
  case "$f" in "$T/remote/"*) ;; *) echo "REMOTO FUORI DAL BANCO"; rc=1 ;; esac
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

case "$MODE" in
  issue) modo_issue ;;
  prepara) modo_prepara ;;
  shim) modo_shim ;;
  passo1) passo1 ;;
  passo2) passo2 ;;
  passo3) passo3 ;;
  attendi) modo_attendi ;;
  passo4) passo4 ;;
  registra) modo_registra ;;
  controlla) modo_controlla ;;
  *) echo "uso: $0 issue|prepara|shim|passo1|passo2|passo3|attendi|passo4|registra|controlla" >&2; exit 2 ;;
esac
