#!/usr/bin/env bash
# spikes/b1/run-b1-checks.sh — verifiche reali di B1 (Task 1: B1-V1..V7 sugli strumenti con cui i subagenti si informano).
# Lo esegue solo il controller. Modo `controlla`: nessuna rete, nessun `claude`, nessuna scrittura.
# Uso: run-b1-checks.sh controlla | sonda --redirect-url <url> | latenza | valida | raccogli [N]
#
#   controlla  stampa i passi e il comando `claude` della sonda, e controlla i file della sonda (nessuna scrittura)
#   sonda      B1-V1, V2, V4, V5: UN `claude -p` da /tmp/tollgate-b1/probe/ con --plugin-dir; ogni esecuzione è un
#              `tentativo-N` sotto /tmp/tollgate-b1/ (log degli hook, uscita JSON, errori, comando, eco dell'heredoc);
#              nulla si cancella: ciò che esiste già si rinomina in <nome>.prev-<tempo>
#   latenza    B1-V6 e B1-V3 a secco, senza `claude`: spikes/b1/latenza.py (50 + 50 invocazioni di hooks/run, più un
#              PreToolUse MCP dell'implementatore)
#   valida     B1-V7: copia della sonda in /tmp/tollgate-b1/valida/ con una skill `approved: prova` e
#              `claude plugin validate --strict` (non lancia il modello)
#   raccogli   copia nelle evidenze (anonimizzate) il tentativo N (l'ultimo se manca), confronta l'heredoc di B1-V5 e scrive
#              spikes/fixtures/hook-inputs/samples-b1.json (spikes/b1/raccogli.py)
#
# Cautele: `claude -p` solo da una cartella sotto /tmp/tollgate-b1/ e sempre con --plugin-dir (lo script lo controlla); gli
# hook della sonda registrano solo l'input JSON che ricevono; nessun file sotto la HOME; curl, wget, gh e git push negati
# al modello con --disallowedTools. Mai kill per nome.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
MODE="${1:-}"
[ "$#" -gt 0 ] && shift

DEFAULT_TMP=/tmp/tollgate-b1
CHECK="${B1_CHECK:-0}"                                 # 1 solo nei test: permette un'altra radice in /tmp
TMP="$DEFAULT_TMP"
[ "$CHECK" = 1 ] && TMP="${B1_TMP:-$DEFAULT_TMP}"
OUT="${B1_OUT:-$root/docs/verifiche/evidenze/b1}"
SAMPLES="${B1_SAMPLES:-$root/spikes/fixtures/hook-inputs/samples-b1.json}"
PLUGIN="${B1_PLUGIN_DIR-$here/probe-plugin}"            # senza i due punti: una variabile vuota resta vuota e viene rifiutata
WORK="${B1_WORK:-$TMP/probe}"
MODEL="${B1_MODEL:-sonnet}"
TIMEOUT_S="${B1_TIMEOUT:-900}"
TOOLS="Read,Grep,Glob,Bash,Agent,Skill,Write,Edit,WebFetch,WebSearch,mcp__context7__*,mcp__plugin_context7_context7__*"
DISALLOWED="Bash(curl:*),Bash(wget:*),Bash(gh:*),Bash(git push:*)"

die() { echo "ERRORE: $*" >&2; exit 1; }

# rot <percorso...>: se esiste lo rinomina in <percorso>.prev-<tempo> (mai cancellare)
rot() {
  local p
  for p in "$@"; do
    if [ -e "$p" ] || [ -L "$p" ]; then mv -- "$p" "$p.prev-$(date +%Y%m%d-%H%M%S)-$$"; fi
  done
}

# sotto_tmp <percorso>: vero se è una sottocartella stretta di $TMP, senza `..`
sotto_tmp() {
  case "$1" in *..*) return 1 ;; "$TMP"/?*) return 0 ;; *) return 1 ;; esac
}

prompt() { # <url con reindirizzamento>
  cat <<TESTO
Usa la skill probe:leggi (strumento Skill). Il subagente probe:lettore deve eseguire, nell'ordine e con lo strumento indicato, questi passi nella cartella corrente, uno alla volta:
1. Read di src/app.py.
2. Read di src/assente.py (il file non esiste: serve l'errore).
3. Grep del pattern «somma» nella cartella src, con output_mode content.
4. Grep del pattern «somma» con path src/app.py (un file), con output_mode content.
5. Grep del pattern «somma» con path src/app.py, senza output_mode (non passare il parametro).
6. Grep del pattern «somma» nella cartella src, con output_mode files_with_matches.
7. Glob con pattern «**/*.py».
8. Bash: cat pyproject.toml.
9. WebFetch di https://docs.python.org/3/library/tomllib.html, chiedendo una riga su cosa fa il modulo.
10. WebFetch di $1, chiedendo una riga su cosa fa il modulo.
11. WebSearch di «python tomllib».
12. Se hai uno strumento di context7 (un nome che contiene context7): risolvi la libreria «tomllib» o «python» e interroga la documentazione su tomllib; se lo strumento non c'è, o chiede l'autenticazione, scrivilo e passa oltre.
Dopo i dodici passi il passo finale della skill (l'heredoc verso bin/eco). Alla fine riporta una riga per passo.
TESTO
}

# comando_claude <url>: riempie l'array CMD; rifiuta se manca --plugin-dir
comando_claude() {
  local -a pd=()
  [ -n "$PLUGIN" ] && pd=(--plugin-dir "$PLUGIN")
  CMD=(claude -p "${pd[@]}" --model "$MODEL" --permission-mode acceptEdits --allowedTools "$TOOLS"
       --disallowedTools "$DISALLOWED" --output-format json "$(prompt "$1")")
  case " ${CMD[*]} " in *" --plugin-dir "*) ;; *) die "claude -p senza --plugin-dir" ;; esac
  [ -d "$PLUGIN" ] || die "la cartella del plugin non esiste: $PLUGIN"
}

crea_repo_di_prova() {
  local d="$1"
  mkdir -p "$d/src"
  git -C "$d" init -q -b main
  cat > "$d/src/app.py" <<'PY'
def somma(a, b):
    return a + b
PY
  cat > "$d/pyproject.toml" <<'TOML'
[project]
name = "prova"
version = "0.0.1"
requires-python = ">=3.11"
TOML
  git -C "$d" add -A
  git -C "$d" -c user.name=b1 -c user.email=b1@example.com -c commit.gpgsign=false commit -qm base
}

# ---------------------------------------------------------------- controlla

modo_controlla() {
  local rc=0 f
  echo "radice di lavoro: $DEFAULT_TMP"
  echo "--- i modi"
  echo "  sonda    B1-V1, V2, V4, V5: un claude -p da $DEFAULT_TMP/probe con --plugin-dir (tentativo-N)"
  echo "  latenza  B1-V6 e B1-V3 a secco: 50 + 50 invocazioni di hooks/run e un PreToolUse MCP"
  echo "  valida   B1-V7: claude plugin validate --strict su una copia con una skill approved: prova"
  echo "  raccogli copia le evidenze anonimizzate, confronta l'heredoc (B1-V5), scrive samples-b1.json"
  echo "--- il comando claude della sonda (URL di esempio)"
  PLUGIN="$here/probe-plugin"
  comando_claude "https://esempio.invalid/vecchio"
  printf '  cwd: %s\n  ' "$DEFAULT_TMP/probe"; printf '%q ' "${CMD[@]:0:${#CMD[@]}-1}"; echo "<prompt>"
  echo "--- i file della sonda"
  bash -n "$here/run-b1-checks.sh" || { echo "  bash -n fallito"; rc=1; }
  for f in latenza.py raccogli.py probe-plugin/hooks/record.py probe-plugin/bin/eco; do
    python3 -B -c "import sys; compile(open(sys.argv[1]).read(), sys.argv[1], 'exec')" "$here/$f" || { echo "  non compila: $f"; rc=1; }
  done
  python3 -B -c "
import json, sys
h = json.load(open(sys.argv[1]))['hooks']
want = {'PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'SubagentStart', 'SubagentStop'}
assert set(h) == want, sorted(h)
for ev in ('PreToolUse', 'PostToolUse', 'PostToolUseFailure'):
    assert h[ev][0]['matcher'] == '.*', ev
" "$here/probe-plugin/hooks/hooks.json" || { echo "  hooks.json non è quello atteso"; rc=1; }
  grep -q '^tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__context7__\*, mcp__plugin_context7_context7__\*$' \
    "$here/probe-plugin/agents/lettore.md" || { echo "  lettore.md: riga tools inattesa"; rc=1; }
  python3 -B "$here/raccogli.py" atteso --skill "$here/probe-plugin/skills/leggi/SKILL.md" >/dev/null || { echo "  heredoc della skill non trovato"; rc=1; }
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

# ---------------------------------------------------------------- sonda

modo_sonda() {
  local url="" n att rc=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --redirect-url) [ "$#" -ge 2 ] || die "--redirect-url vuole un URL"; url="$2"; shift 2 ;;
      *) die "argomento sconosciuto: $1" ;;
    esac
  done
  [ -n "$url" ] || die "sonda richiede --redirect-url <url> (un URL che reindirizza su un altro percorso, scelto dal controller)"
  case "$url" in https://*) ;; *) die "l'URL deve cominciare con https://" ;; esac
  sotto_tmp "$WORK" || die "la cartella di lavoro $WORK non è sotto $TMP/"
  comando_claude "$url"
  mkdir -p "$TMP"
  n=1
  while [ -e "$TMP/tentativo-$n" ]; do n=$((n + 1)); done
  att="$TMP/tentativo-$n"
  mkdir "$att" || die "non riesco a creare $att"
  rot "$WORK"
  crea_repo_di_prova "$WORK" || die "repo di prova non creato"
  if [ "$CHECK" != 1 ]; then rot "$DEFAULT_TMP/hooks.jsonl" "$DEFAULT_TMP/eco.txt"; fi
  mkdir -p "$TMP/state" && : > "$TMP/state/.tollgate-test"     # stato isolato con la sentinella: un hook di tollgate attivo nella sessione non usa mai lo stato dell'utente
  printf '%s\n' "$url" > "$att/redirect-url.txt"
  { printf 'cwd: %s\n' "$WORK"; printf '%q ' "${CMD[@]}"; printf '\n'; } > "$att/argv.txt"
  timeout 30 claude --version > "$att/versione.txt" 2>&1 < /dev/null
  echo "tentativo $n: claude -p da $WORK (tetto $TIMEOUT_S s)"
  ( cd "$WORK" && B1_PROBE_LOG="$att/hooks.jsonl" B1_ECO_OUT="$att/eco.txt" TOLLGATE_STATE="$TMP/state" \
      timeout "$TIMEOUT_S" "${CMD[@]}" < /dev/null ) > "$att/claude.json" 2> "$att/claude.err"
  rc=$?
  echo "$rc" > "$att/uscita.txt"
  if [ "$CHECK" != 1 ]; then      # se l'ambiente non è arrivato agli hook o a eco, i file stanno nei percorsi di ripiego
    [ -e "$att/hooks.jsonl" ] || { [ -e "$DEFAULT_TMP/hooks.jsonl" ] && mv "$DEFAULT_TMP/hooks.jsonl" "$att/hooks.jsonl"; }
    [ -e "$att/eco.txt" ] || { [ -e "$DEFAULT_TMP/eco.txt" ] && mv "$DEFAULT_TMP/eco.txt" "$att/eco.txt"; }
  fi
  echo "tentativo $n: uscita $rc; hooks.jsonl: $( [ -e "$att/hooks.jsonl" ] && wc -l < "$att/hooks.jsonl" || echo assente ) righe"
  return 0
}

# ---------------------------------------------------------------- latenza

modo_latenza() {
  mkdir -p "$TMP" "$OUT"
  python3 -B "$here/latenza.py" --root "$TMP" --out "$OUT" --runs "${B1_RUNS:-50}"
}

# ---------------------------------------------------------------- valida

modo_valida() {
  local d="$TMP/valida" rc
  [ -d "$here/probe-plugin" ] || die "manca la sonda"
  mkdir -p "$TMP" "$OUT"
  rot "$d"
  cp -R "$here/probe-plugin" "$d"
  mkdir -p "$d/skills/rules-base"
  cat > "$d/skills/rules-base/SKILL.md" <<'TESTO'
---
name: rules-base
description: Prova di B1-V7, un campo approved nel frontmatter di una skill.
approved: prova
---

Skill di prova.
TESTO
  rot "$OUT/valida-esito.txt"
  ( cd "$d" && claude plugin validate --strict . ) > "$OUT/valida-esito.txt" 2>&1 < /dev/null
  rc=$?
  echo "uscita: $rc" >> "$OUT/valida-esito.txt"
  cat "$OUT/valida-esito.txt"
  return 0
}

# ---------------------------------------------------------------- raccogli

modo_raccogli() {
  local n="${1:-}" att
  if [ -z "$n" ]; then
    n=0
    for att in "$TMP"/tentativo-*; do
      [ -d "$att" ] || continue
      case "${att##*tentativo-}" in *[!0-9]*|"") continue ;; esac
      [ "${att##*tentativo-}" -gt "$n" ] && n="${att##*tentativo-}"
    done
    [ "$n" -gt 0 ] || die "nessun tentativo in $TMP"
  fi
  att="$TMP/tentativo-$n"
  [ -d "$att" ] || die "manca $att"
  [ -n "${HOME:-}" ] && [ "$HOME" != / ] || die "--home vuoto: HOME non è impostata, non si può anonimizzare"
  mkdir -p "$OUT"
  python3 -B "$here/raccogli.py" raccogli --tentativo "$att" --out "$OUT" --samples "$SAMPLES" \
    --skill "$here/probe-plugin/skills/leggi/SKILL.md" --home "${HOME:-}"
}

case "$MODE" in
  controlla) modo_controlla ;;
  sonda) modo_sonda "$@" ;;
  latenza) modo_latenza ;;
  valida) modo_valida ;;
  raccogli) modo_raccogli "$@" ;;
  *) echo "uso: $0 controlla | sonda --redirect-url <url> | latenza | valida | raccogli [N]" >&2; exit 2 ;;
esac
