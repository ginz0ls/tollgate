#!/usr/bin/env bash
# spikes/run-p3a-flow.sh — prova reale del flusso P3a con `claude -p` (Task 13).
# Percorso: skill -> CLI -> hook -> agenti, su un repo locale. Nessuna rete verso GitHub,
# nessun push, nessun plugin installato. Tutto sotto /tmp/tollgate-p3a/flow.
#
# Uso: [PLUGIN_REAL_PATH=1] bash spikes/run-p3a-flow.sh [prepara|passo1|passo2|passo3|tutto]
# (predefinito: tutto). Il push dello script va al repo nudo locale, mai a GitHub.
set -uo pipefail

PLUGIN_REAL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
FLOW=/tmp/tollgate-p3a/flow
# Per impostazione predefinita il plugin passa dal link senza spazi $FLOW/plugin. Con
# PLUGIN_REAL_PATH=1 si usa il percorso reale del worktree, con i suoi spazi (caso D2: in una
# sessione isolata in un worktree Claude Code rifiuta un comando il cui nome e' un percorso con
# spazi tra virgolette, per questo le skill scrivono `python3 "<percorso>"`).
if [ "${PLUGIN_REAL_PATH:-0}" = 1 ]; then PLUGIN="$PLUGIN_REAL"; else PLUGIN="$FLOW/plugin"; fi
REPO="$FLOW/repo"          # checkout principale (cwd di claude -p)
BARE="$FLOW/origin.git"    # repo nudo locale, dietro l'URL finto
STATE="$FLOW/state"
LOGS="$FLOW/logs"
PLAN_SRC="$FLOW/piano-L1.md"
GH_DATA="$FLOW/fakegh-data.json"
ORIGIN_URL=https://github.com/prova/flow.git
MODEL=sonnet
TOOLS="Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob"

export TOLLGATE_STATE="$STATE"
export TOLLGATE_GH="$PLUGIN/tests/fakegh.py"
export TOLLGATE_FAKEGH_DATA="$GH_DATA"
export TOLLGATE_FAKEGH_LOG="$LOGS/fakegh.log"
TG=(python3 "$PLUGIN/bin/tollgate")

prepara() {
  case "$FLOW" in /tmp/tollgate-p3a/flow) ;; *) echo "percorso inatteso: $FLOW" >&2; return 1 ;; esac
  rm -rf "$FLOW"
  mkdir -p "$LOGS" "$STATE" || return 1
  [ "$PLUGIN" = "$PLUGIN_REAL" ] || ln -s "$PLUGIN_REAL" "$PLUGIN" || return 1
  : > "$STATE/.tollgate-test"
  git init -q --bare -b main "$BARE" || return 1
  git init -q -b main "$REPO" || return 1
  cd "$REPO" || return 1
  git config user.name prova; git config user.email prova@example.com; git config commit.gpgsign false
  mkdir -p src tests .github/workflows .github/tollgate
  cat > tollgate.toml <<'TOML'
schema_version = 1

[project]
allow_no_tests = true

[gate]
mode = "protected"

[commands]
verify = "python3 -m unittest discover -s tests -t ."
gate = ["verify"]
TOML
  : > src/__init__.py
  : > tests/__init__.py
  cat > src/calc.py <<'PY'
def somma(a, b):
    return a + b
PY
  cat > tests/test_calc.py <<'PY'
import unittest

from src.calc import somma


class CalcTest(unittest.TestCase):
    def test_somma(self):
        self.assertEqual(somma(1, 2), 3)


if __name__ == "__main__":
    unittest.main()
PY
  printf 'reports/\n__pycache__/\n' > .gitignore
  for n in guard run verdict base sentinel; do printf 'name: tollgate-%s\n' "$n" > ".github/workflows/tollgate-$n.yml"; done
  python3 -B - "$PLUGIN" > .github/tollgate/VERSION <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/bin")
from tollgate_core import VERSION
print(VERSION)
PY
  git add -A && git commit -qm base || return 1
  git remote add origin "$BARE"
  git push -q -u origin main || return 1
  git remote set-head origin main
  git config tollgate.defaultBranch main
  # come FlowLab: l'URL grezzo è quello di GitHub (prereq.is_github), il fetch va al repo nudo
  git config remote.origin.url "$ORIGIN_URL"
  git config "url.$BARE.insteadOf" "$ORIGIN_URL"
  local sha; sha="$(git rev-parse origin/main)"
  python3 -B - "$GH_DATA" "$sha" <<'PY'
import json, sys
path, sha = sys.argv[1:3]
json.dump({"auth": True,
           "issues": {"1": {"number": 1, "title": "Aggiungi sottrai a calc", "state": "OPEN",
                            "body": "Aggiungere la funzione sottrai(a, b) in src/calc.py, con il suo test.",
                            "labels": [], "author_association": "OWNER"}},
           "prs": [], "issue_list": [],
           "statuses": {sha: {"statuses": [{"context": "tollgate/guard", "state": "success"},
                                           {"context": "tollgate/verdict", "state": "success"}]}}},
          open(path, "w"))
PY
  cat > "$PLAN_SRC" <<'MD'
# Piano di prova: sottrai

## Fatti verificati

- `src/calc.py` contiene solo `somma(a, b)`; `tests/test_calc.py` ha `CalcTest.test_somma`.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `sottrai(a, b)` restituisce `a - b`, senza altri argomenti né controlli di tipo.

## Interfacce

- `src.calc.sottrai(a, b)` restituisce il risultato di `a - b`.

## Must-have

- M1. `sottrai(a, b)` restituisce la differenza — test: tests.test_calc.CalcTest::test_sottrai

## Scope

- `src/calc.py`, `tests/test_calc.py`.

## Punti di arresto

- Nessuno: il task è un'unica funzione.

## Rischi

- Nessuno di rilievo.

### Task 1: Funzione sottrai

- Modify: `src/calc.py`
- Test: `tests/test_calc.py`
- Must-have: M1

In TDD: scrivi in `CalcTest` un `test_sottrai` che verifica `sottrai(5, 3) == 2` e `sottrai(0, 4) == -4`,
poi aggiungi `sottrai` a `src/calc.py`. Esegui `python3 -m unittest discover -s tests -t .`, committa.
MD
  # il piano deve passare plan-check PRIMA della prova reale
  python3 -B - "$PLUGIN" "$REPO" "$PLAN_SRC" <<'PY' || return 1
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
  echo "pronto: $REPO"
}

claude_step() { # id, prompt
  local id="$1"; shift
  local cont=()
  [ "$id" != passo1 ] && cont=(--continue)
  ( cd "$REPO" && claude -p "${cont[@]}" --plugin-dir "$PLUGIN" --model "$MODEL" \
      --permission-mode acceptEdits --allowedTools "$TOOLS" --output-format stream-json --verbose \
      --include-hook-events "$1" < /dev/null ) > "$LOGS/$id.jsonl" 2> "$LOGS/$id.err"
  echo "$id: uscita $?" | tee -a "$LOGS/exit-codes.txt"
}

registra() { # copia i log degli hook e gli eventi del DB
  cp "$STATE/hook-errors.log" "$LOGS/hooks.log" 2>/dev/null || : > "$LOGS/hooks.log"
  [ -f "$STATE/skipped.log" ] && cp "$STATE/skipped.log" "$LOGS/skipped.log"
  ( cd "$REPO" && "${TG[@]}" events > "$LOGS/events.jsonl" 2> "$LOGS/events.err"
    "${TG[@]}" stats > "$LOGS/stats.json" 2> "$LOGS/stats.err"
    "${TG[@]}" status > "$LOGS/status.txt" 2>&1 )
}

passo1() { claude_step passo1 "/tollgate:start #1 L1"; registra; }
passo2() { claude_step passo2 "Nel worktree del lavoro, se non c'è ancora un piano in docs/superpowers/plans/, scrivilo copiando il file $PLAN_SRC in docs/superpowers/plans/2026-10-16-prova.md. Poi controlla che sia committato (il commit del piano è del coordinatore) e, se non lo è, committalo."; registra; }
passo3() { claude_step passo3 "/tollgate:execute"; registra; }

case "${1:-tutto}" in
  prepara) prepara ;;
  passo1) passo1 ;;
  passo2) passo2 ;;
  passo3) passo3 ;;
  tutto) prepara && passo1 && passo2 && passo3 ;;
  *) echo "uso: $0 [prepara|passo1|passo2|passo3|tutto]" >&2; exit 2 ;;
esac
