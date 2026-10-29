#!/usr/bin/env bash
# spikes/run-b1-flow.sh — prova reale di un lavoro L1 con la nota di ricerca di B1 (Task 9). Lo esegue solo il controller.
# Deriva da spikes/run-p4-flow.sh e spikes/run-p3a-flow.sh, senza GitHub: `gh` finto (tests/fakegh.py), `origin` nudo locale.
# Modo `controlla`: nessuna rete, nessun `claude`, nessuna scrittura: stampa i passi e i comandi.
# Uso: run-b1-flow.sh controlla | prepara | passo1 | passo2 | registra
#
#   controlla  stampa i passi e i comandi `claude`, controlla i file (nessuna scrittura)
#   prepara    copia il plugin in /tmp/tollgate-b1/plugin e vi aggiunge SOLO NELLA COPIA skills/rules-base/SKILL.md con
#              `approved: prova-b1` (l'interruttore di B1 acceso, decisione 8); crea il progetto di prova in
#              /tmp/tollgate-b1/flow (repo con origin nudo locale), lo stato con la sentinella in /tmp/tollgate-b1/state e
#              il gh finto in testa al PATH; controlla il piano di prova con plan-check
#   passo1     `claude plugin validate --strict` sulla copia (senza modello; se fallisce il passo si ferma), poi
#              `claude -p "/tollgate:start #1 L1"` dal checkout
#   passo2     dal worktree: il modello scrive il piano con Write (il testo è nel prompt), lo committa, poi /tollgate:execute
#   registra   versione di claude, righe di `lookups` e nota salvata, `.tollgate-run/1/research-*.md`, eventi research_note,
#              research_reminder e veto, stato dei task (`status --json`), comandi Bash del modello, conto dei Grep
#
# Uscite in docs/verifiche/evidenze/b1/flusso/: mai cancellate. Ogni tentativo di un passo è una sottocartella nuova
# (<passo>/tentativo-N) con argv, uscita JSONL, errori e l'esito; oltre 3 tentativi per passo lo script rifiuta. Ciò che esiste
# già si rinomina in <nome>.prev-<tempo>.
#
# Cautele: `claude -p` solo da /tmp/tollgate-b1/ e sempre con --plugin-dir (lo script lo controlla); gh è il finto
# tests/fakegh.py, in testa al PATH; al modello sono negati con --disallowedTools gh per percorso, git push verso remoti non
# locali, curl e wget; nessun plugin installato o abilitato. Mai kill per nome.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
MODE="${1:-}"

DEFAULT_TMP=/tmp/tollgate-b1
CHECK="${B1_FLOW_CHECK:-0}"                              # 1 solo nei test: permette un'altra radice
TMP="${B1_FLOW_ROOT:-$DEFAULT_TMP}"
OUT="$root/docs/verifiche/evidenze/b1/flusso"
PLUGIN="$TMP/plugin"
[ "$CHECK" = 1 ] && { OUT="${B1_FLOW_OUT:-$OUT}"; PLUGIN="${B1_FLOW_PLUGIN-$PLUGIN}"; }
REPO="$TMP/flow"
BARE="$TMP/origin.git"
STATE="$TMP/state"
GHBIN="$TMP/ghbin"
GH_DATA="$TMP/fakegh-data.json"
GH_LOG="$TMP/fakegh.log"
ORIGIN_URL=https://github.com/prova/flow.git
ISSUE=1
MODEL=sonnet
STEP_TIMEOUT="${B1_FLOW_TIMEOUT:-2400}"
MAX_ATTEMPTS=3
PLAN_SRC="$here/b1/flow/piano-L1.md"
PLAN_REL=docs/superpowers/plans/2026-10-27-prova-b1.md
# B1-V2: nessuna voce MCP di context7 (non autenticato). WebFetch e WebSearch servono all'implementatore per informarsi.
TOOLS="Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob,WebFetch,WebSearch"
# Divieti per Claude Code (prefissi `Bash(<comando>:*)`): gh per percorso o dietro un prefisso, git push verso remoti non
# locali o forzato, curl e wget. Il gh in testa al PATH è il finto, quindi `gh` nudo resta ammesso.
DISALLOWED="Bash(*/gh:*),Bash(command gh:*),Bash(gh repo:*),Bash(gh api:*),Bash(gh auth:*),Bash(gh secret:*),\
Bash(git push https:*),Bash(git push http:*),Bash(git push ssh:*),Bash(git push git@:*),Bash(git push --force:*),\
Bash(git push -f:*),Bash(git push --mirror:*),Bash(git push --delete:*),\
Bash(curl:*),Bash(wget:*),Bash(*/curl:*),Bash(*/wget:*)"

die() { echo "ERRORE: $*" >&2; exit 1; }

# rot <percorso...>: se esiste lo rinomina in <percorso>.prev-<tempo> (mai cancellare)
rot() {
  local p
  for p in "$@"; do
    if [ -e "$p" ] || [ -L "$p" ]; then mv -- "$p" "$p.prev-$(date +%Y%m%d-%H%M%S)-$$"; fi
  done
}

# verifica_radice: la radice di lavoro è /tmp/tollgate-b1 (o una sua sottocartella), senza `..`; solo nei test un'altra
verifica_radice() {
  [ "$CHECK" = 1 ] && return 0
  case "$TMP" in *..*) die "la radice $TMP non è sotto $DEFAULT_TMP/" ;; esac
  case "$TMP" in "$DEFAULT_TMP"|"$DEFAULT_TMP"/?*) ;; *) die "la radice $TMP non è sotto $DEFAULT_TMP/" ;; esac
}

verifica_stato() {
  [ -f "$STATE/.tollgate-test" ] || die "manca lo stato di prova con la sentinella ($STATE/.tollgate-test): lancia prepara"
  [ -z "${TOLLGATE_TEST_CONFIG:-}" ] || die "TOLLGATE_TEST_CONFIG è impostata"
}

# comando_claude <id> <prompt>: riempie l'array CMD; rifiuta se manca --plugin-dir
comando_claude() {
  local -a pd=()
  [ -n "$PLUGIN" ] && pd=(--plugin-dir "$PLUGIN")
  CMD=(claude -p "${pd[@]}" --model "$MODEL" --permission-mode acceptEdits --allowedTools "$TOOLS"
       --disallowedTools "$DISALLOWED" --output-format stream-json --verbose --include-hook-events "$2")
  case " ${CMD[*]} " in *" --plugin-dir "*) ;; *) die "claude -p senza --plugin-dir" ;; esac
}

worktree_lavoro() { # il worktree del ramo tg/1-*, sempre sotto la radice
  local wt
  wt="$(git -C "$REPO" worktree list --porcelain 2>/dev/null | awk -v p="refs/heads/tg/$ISSUE-" \
    '/^worktree /{w=substr($0,10)} /^branch /{ if (index(substr($0,8), p) == 1) print w }' | head -n 1)"
  case "$wt" in "$TMP"/*) echo "$wt" ;; *) echo "worktree del lavoro non trovato: '$wt'" >&2; return 1 ;; esac
}

prompt_passo2() {
  cat <<TESTO
Per l'issue #$ISSUE, nel worktree del lavoro: scrivi il piano con lo strumento Write nel file $PLAN_REL, con esattamente il testo tra i marcatori <<<PIANO e PIANO>>> (i marcatori esclusi). Poi committalo con git (git add e git commit). Poi esegui /tollgate:execute fino alla chiusura di tutti i task. Non lanciare /tollgate:finish.
<<<PIANO
$(cat "$PLAN_SRC")
PIANO>>>
TESTO
}

# ---------------------------------------------------------------- controlla

modo_controlla() {
  local rc=0 f
  echo "radice di lavoro: $DEFAULT_TMP"
  echo "--- i passi"
  echo "  prepara   copia del plugin in $DEFAULT_TMP/plugin con skills/rules-base/SKILL.md (approved: prova-b1) solo nella copia; progetto in $DEFAULT_TMP/flow"
  echo "  passo1    claude plugin validate --strict sulla copia, poi claude -p \"/tollgate:start #$ISSUE L1\" dal checkout"
  echo "  passo2    dal worktree: Write del piano, commit, poi /tollgate:execute"
  echo "  registra  lookups, nota, eventi research_note/research_reminder/veto, stato dei task, comandi Bash, conto dei Grep"
  echo "--- i comandi claude (--plugin-dir, tetto di ${STEP_TIMEOUT} s)"
  PLUGIN="$DEFAULT_TMP/plugin"
  printf '  %s\n' "claude plugin validate --strict ."
  comando_claude passo1 "/tollgate:start #$ISSUE L1"
  printf '  passo1 (cwd %s/flow): ' "$DEFAULT_TMP"; printf '%q ' "${CMD[@]:0:${#CMD[@]}-1}"; echo "<prompt>"
  comando_claude passo2 "$(prompt_passo2)"
  printf '  passo2 (cwd = worktree del lavoro): '; printf '%q ' "${CMD[@]:0:${#CMD[@]}-1}"; echo "<prompt>"
  echo "--- i file"
  bash -n "$here/run-b1-flow.sh" || { echo "  bash -n fallito"; rc=1; }
  python3 -B -c "import sys; compile(open(sys.argv[1]).read(), sys.argv[1], 'exec')" "$here/b1/flowreg.py" || { echo "  non compila: flowreg.py"; rc=1; }
  for f in tollgate.toml config.toml issue-1.md piano-L1.md src/__init__.py tests/__init__.py tests/test_smoke.py .gitignore; do
    [ -f "$here/b1/flow/$f" ] || { echo "  manca b1/flow/$f"; rc=1; }
  done
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

# ---------------------------------------------------------------- prepara

modo_prepara() {
  local t sha
  verifica_radice
  for t in git python3 tar; do command -v "$t" >/dev/null 2>&1 || die "manca $t"; done
  mkdir -p "$TMP" "$OUT" || die "non riesco a creare $TMP"
  rot "$PLUGIN" "$REPO" "$BARE" "$STATE" "$GHBIN" "$GH_DATA" "$GH_LOG" "$OUT/passo1" "$OUT/passo2"
  mkdir -p "$PLUGIN" "$REPO" "$STATE" "$GHBIN" || die "cartelle di lavoro non create"
  # la copia del plugin (senza __pycache__): il repo non cambia
  ( cd "$root" && tar --exclude=__pycache__ -cf - .claude-plugin agents bin gate hooks skills templates statusline LICENSE ) \
    | ( cd "$PLUGIN" && tar -xf - ) || die "copia del plugin non riuscita"
  mkdir -p "$PLUGIN/skills/rules-base"
  cat > "$PLUGIN/skills/rules-base/SKILL.md" <<'TESTO'
---
name: rules-base
description: Regole di prova della prova reale di B1.
approved: prova-b1
---

Regole di prova della prova reale di B1: non sono le regole di B2.
TESTO
  : > "$STATE/.tollgate-test"
  printf '#!/bin/sh\nexec python3 "%s" "$@"\n' "$root/tests/fakegh.py" > "$GHBIN/gh" && chmod +x "$GHBIN/gh" || die "gh finto non scritto"
  # il progetto di prova (senza l'issue e il piano, che stanno nei dati del gh finto e nel prompt)
  tar -C "$here/b1/flow" --exclude=./issue-1.md --exclude=./piano-L1.md -cf - . | tar -C "$REPO" -xf - || die "progetto non copiato"
  git init -q --bare -b main "$BARE" || die "origin nudo non creato"
  git init -q -b main "$REPO" || die "git init fallito"
  (
    cd "$REPO" || exit 1
    git config user.name prova; git config user.email prova@example.com; git config commit.gpgsign false
    mkdir -p .github/workflows .github/tollgate
    for n in guard run verdict base sentinel; do printf 'name: tollgate-%s\n' "$n" > ".github/workflows/tollgate-$n.yml"; done
    python3 -B - "$PLUGIN" > .github/tollgate/VERSION <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/bin")
from tollgate_core import VERSION
print(VERSION)
PY
    git add -A && git commit -qm base || exit 1
    git remote add origin "$BARE"
    git push -q -u origin main || exit 1
    git remote set-head origin main
    git config tollgate.defaultBranch main
    # come FlowLab: l'URL grezzo è quello di GitHub (prereq.is_github), il fetch va al repo nudo locale
    git config remote.origin.url "$ORIGIN_URL"
    git config "url.$BARE.insteadOf" "$ORIGIN_URL"
  ) || die "repo di prova non creato"
  sha="$(git -C "$REPO" rev-parse origin/main)"
  python3 -B - "$GH_DATA" "$sha" "$here/b1/flow/issue-1.md" <<'PY' || die "dati del gh finto non scritti"
import json, sys
path, sha, issue = sys.argv[1:4]
json.dump({"auth": True,
           "issues": {"1": {"number": 1, "title": "Leggi il nome dell'app da config.toml", "state": "OPEN",
                            "body": open(issue).read().strip(), "labels": [], "author_association": "OWNER"}},
           "prs": [], "issue_list": [],
           "statuses": {sha: {"statuses": [{"context": "tollgate/guard", "state": "success"},
                                           {"context": "tollgate/verdict", "state": "success"}]}}},
          open(path, "w"))
PY
  # il piano di prova deve passare plan-check PRIMA della prova reale
  python3 -B - "$PLUGIN" "$REPO" "$PLAN_SRC" <<'PY' || die "il piano di prova non passa plan-check"
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1] + "/bin")
from tollgate_core import config
from tollgate_analysis import plan
cfg = config.load_config_at(Path(sys.argv[2]), "origin/main")
c = cfg.data
r = plan.check_plan(Path(sys.argv[3]).read_text(), required_sections=c["plan"]["required_sections"],
                    max_scope_files=c["plan"]["max_scope_files"], must_have_tests=True, level="L1",
                    profiles=cfg.profiles, active_always=c["profiles"]["active"])
print("plan-check:", "ok" if r.ok else r.problems, r.warnings)
sys.exit(0 if r.ok else 1)
PY
  echo "pronto: $REPO (plugin: $PLUGIN, stato: $STATE)"
}

# ---------------------------------------------------------------- un passo con claude -p

# valida_copia: claude plugin validate --strict sulla copia del plugin (senza modello); un esito per volta in validate/validate-N.txt
valida_copia() {
  local n=1 f rc
  mkdir -p "$OUT/validate"
  while [ -e "$OUT/validate/validate-$n.txt" ]; do n=$((n + 1)); done
  f="$OUT/validate/validate-$n.txt"
  ( cd "$PLUGIN" && claude plugin validate --strict . ) > "$f" 2>&1 < /dev/null
  rc=$?
  echo "uscita: $rc" >> "$f"
  if [ "$rc" != 0 ]; then
    echo "STOP: claude plugin validate --strict ha fallito sulla copia del plugin (uscita $rc, vedi $f): nessun claude -p" >&2
    return 1
  fi
  echo "validate: ok ($f)"
}

# claude_step <id> <cartella> <prompt>
claude_step() {
  local id="$1" dir="$2" prompt="$3" n=1 att rc=0 t0 t1
  verifica_radice; verifica_stato
  case "$dir" in "$TMP"/*) ;; *) die "claude -p solo da $TMP: $dir è altrove" ;; esac
  [ -d "$dir" ] || die "la cartella $dir non esiste: lancia prima il passo precedente"
  comando_claude "$id" "$prompt"
  [ -d "$PLUGIN" ] || die "la cartella del plugin non esiste: $PLUGIN"
  [ "$(PATH="$GHBIN:$PATH" command -v gh)" = "$GHBIN/gh" ] || die "il primo gh del PATH non è il finto $GHBIN/gh"
  while [ -e "$OUT/$id/tentativo-$n" ]; do n=$((n + 1)); done
  [ "$n" -le "$MAX_ATTEMPTS" ] || die "$id: già $MAX_ATTEMPTS tentativi in $OUT/$id: mi fermo (nulla si cancella)"
  if [ "$id" = passo1 ]; then valida_copia || return 1; fi
  mkdir -p "$OUT/$id"
  att="$OUT/$id/tentativo-$n"
  mkdir "$att" || die "non riesco a creare $att"
  { printf 'cwd: %s\nPATH in testa: %s\n' "$dir" "$GHBIN"; printf '%q ' "${CMD[@]}"; printf '\n'; } > "$att/argv.txt"
  t0="$(date +%Y-%m-%dT%H:%M:%S)"
  echo "$id, tentativo $n: claude -p da $dir (tetto $STEP_TIMEOUT s)"
  ( cd "$dir" && env PATH="$GHBIN:$PATH" TOLLGATE_STATE="$STATE" TOLLGATE_GH="$root/tests/fakegh.py" \
      TOLLGATE_FAKEGH_DATA="$GH_DATA" TOLLGATE_FAKEGH_LOG="$GH_LOG" \
      timeout "$STEP_TIMEOUT" "${CMD[@]}" < /dev/null ) > "$att/claude.jsonl" 2> "$att/claude.err"
  rc=$?
  t1="$(date +%Y-%m-%dT%H:%M:%S)"
  echo "$rc" > "$att/uscita.txt"
  {
    echo "passo: $id"; echo "tentativo: $n"; echo "inizio: $t0"; echo "fine: $t1"; echo "uscita: $rc"
    case "$rc" in 0) echo "esito: claude uscito con 0 (l'esito del prodotto lo dice registra)" ;;
      124) echo "esito: tetto di tempo superato" ;; *) echo "esito: claude uscito con $rc" ;; esac
  } > "$att/esito.txt"
  echo "$id: tentativo $n, uscita $rc" | tee -a "$OUT/exit-codes.txt"
  return "$rc"
}

modo_passo1() { claude_step passo1 "$REPO" "/tollgate:start #$ISSUE L1"; }

modo_passo2() {
  local wt
  verifica_radice
  wt="$(worktree_lavoro)" || return 1
  case "$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)" in tg/"$ISSUE"-*) ;; *) die "$wt non è sul ramo tg/$ISSUE-*" ;; esac
  claude_step passo2 "$wt" "$(prompt_passo2)"
}

# ---------------------------------------------------------------- registra

modo_registra() {
  local n=1 d wt att
  verifica_radice
  [ -d "$REPO/.git" ] || die "manca il progetto $REPO: lancia prepara"
  mkdir -p "$OUT"
  while [ -e "$OUT/registro-$n" ]; do n=$((n + 1)); done
  d="$OUT/registro-$n"
  mkdir "$d" || die "non riesco a creare $d"
  timeout 30 claude --version > "$d/versione-claude.txt" 2>&1 < /dev/null
  export TOLLGATE_STATE="$STATE" TOLLGATE_GH="$root/tests/fakegh.py" TOLLGATE_FAKEGH_DATA="$GH_DATA" TOLLGATE_FAKEGH_LOG="$GH_LOG"
  TG=(python3 -B "$PLUGIN/bin/tollgate")
  ( cd "$REPO" && "${TG[@]}" events > "$d/events.jsonl" 2> "$d/events.err"
    "${TG[@]}" stats > "$d/stats.json" 2> "$d/stats.err"
    "${TG[@]}" status --json > "$d/status.json" 2> "$d/status.err" )
  python3 -B "$here/b1/flowreg.py" eventi "$d/events.jsonl" > "$d/eventi-ricerca.jsonl" 2> "$d/eventi-ricerca.err"
  python3 -B "$here/b1/flowreg.py" lookups "$STATE/tollgate.db" > "$d/lookups.txt" 2> "$d/lookups.err"
  for att in "$OUT"/passo1/tentativo-*/claude.jsonl "$OUT"/passo2/tentativo-*/claude.jsonl; do
    [ -f "$att" ] && python3 -B "$here/b1/flowreg.py" comandi "$att" >> "$d/comandi-modello.txt" 2>> "$d/comandi-modello.err"
  done
  : >> "$d/comandi-modello.txt"
  python3 -B "$here/b1/flowreg.py" grep "$d/comandi-modello.txt" "$d/lookups.txt" > "$d/grep-non-registrati.txt" 2>&1
  grep -E '(^bash.*(git push|gh |curl|wget))' "$d/comandi-modello.txt" > "$d/comandi-rischiosi.txt" 2>&1
  wt="$(worktree_lavoro 2>/dev/null)" && {
    git -C "$wt" log --format='%h %s' > "$d/git-log-worktree.txt" 2>&1
    for att in "$wt"/.tollgate-run/$ISSUE/research-*.md; do [ -f "$att" ] && cp "$att" "$d/$(basename "$att")"; done
  }
  [ -f "$GH_LOG" ] && cp "$GH_LOG" "$d/fakegh.log"
  [ -f "$STATE/hook-errors.log" ] && cp "$STATE/hook-errors.log" "$d/hooks.log"
  [ -f "$STATE/skipped.log" ] && cp "$STATE/skipped.log" "$d/skipped.log"
  [ -f "$OUT/exit-codes.txt" ] && cp "$OUT/exit-codes.txt" "$d/exit-codes.txt"
  echo "registrato in $d"
  cat "$d/grep-non-registrati.txt"
}

case "$MODE" in
  controlla) modo_controlla ;;
  prepara) modo_prepara ;;
  passo1) modo_passo1 ;;
  passo2) modo_passo2 ;;
  registra) modo_registra ;;
  *) echo "uso: $0 controlla | prepara | passo1 | passo2 | registra" >&2; exit 2 ;;
esac
