#!/usr/bin/env bash
# spikes/run-p3b-flow.sh — prova reale del flusso di chiusura P3b con `claude -p` (Task 17).
# Percorso: skill -> CLI -> hook -> agenti, su un repo locale: start/execute di P3a fino a
# «task 1 done», poi /tollgate:finish fino a `finish open-pr`. Nessuna rete verso GitHub, nessun
# plugin installato. Tutto sotto /tmp/tollgate-p3b/flow. Il solo push (dello script e di
# `finish open-pr`) va al repo nudo locale dietro l'URL finto con insteadOf (decisione 24); prima
# di ogni passo lo script controlla che `git remote get-url --push origin` sia quel repo nudo.
#
# Uso: [PLUGIN_REAL_PATH=1] bash spikes/run-p3b-flow.sh \
#        [prepara|passo1|passo2|passo3|passo4|passo4-radice|passo5|passo6|tutto]
# (predefinito: tutto). passo5 si puo' ripetere (nuovo atto /tollgate:finish).
set -uo pipefail

PLUGIN_REAL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
FLOW=/tmp/tollgate-p3b/flow
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
  case "$FLOW" in /tmp/tollgate-p3b/flow) ;; *) echo "percorso inatteso: $FLOW" >&2; return 1 ;; esac
  rm -rf "$FLOW"
  mkdir -p "$LOGS" "$STATE" || return 1
  [ "$PLUGIN" = "$PLUGIN_REAL" ] || ln -s "$PLUGIN_REAL" "$PLUGIN" || return 1
  : > "$STATE/.tollgate-test"
  git init -q --bare -b main "$BARE" || return 1
  git init -q -b main "$REPO" || return 1
  cd "$REPO" || return 1
  git config user.name prova; git config user.email prova@example.com; git config commit.gpgsign false
  mkdir -p src tests tools .github/workflows .github/tollgate
  cat > tollgate.toml <<'TOML'
schema_version = 1

[project]
allow_no_tests = true

[gate]
mode = "protected"

[commands]
verify = "python3 tools/unittest_junit.py"
gate = ["verify"]
report = "junit:reports/junit.xml"
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
  # esegue unittest e scrive reports/junit.xml con classname::name nella forma dei must-have
  # (tests.test_calc.CalcTest::test_sottrai); esce 1 se un test fallisce o la suite e' vuota
  cat > tools/unittest_junit.py <<'PY'
import pathlib
import sys
import unittest
from xml.sax.saxutils import quoteattr


class Result(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.cases = []

    def _add(self, test, kind=None):
        classname, _, name = test.id().rpartition(".")
        self.cases.append((classname, name, kind))

    def addSuccess(self, test):
        super().addSuccess(test); self._add(test)

    def addFailure(self, test, err):
        super().addFailure(test, err); self._add(test, "failure")

    def addError(self, test, err):
        super().addError(test, err); self._add(test, "error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self._add(test, "skipped")


suite = unittest.defaultTestLoader.discover("tests", top_level_dir=".")
res = unittest.TextTestRunner(resultclass=Result, stream=sys.stderr).run(suite)
body = "".join(
    f"<testcase classname={quoteattr(c)} name={quoteattr(n)}>"
    + (f'<{k} message="x"/>' if k else "") + "</testcase>" for c, n, k in res.cases)
out = pathlib.Path("reports")
out.mkdir(exist_ok=True)
(out / "junit.xml").write_text("<testsuite>" + body + "</testsuite>")
sys.exit(0 if res.wasSuccessful() and res.cases else 1)
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
  verifica_push || return 1
  echo "pronto: $REPO"
}

# decisione 24: nessun push in rete. Ferma lo script se il push di origin non va al repo nudo locale.
verifica_push() {
  local url
  url="$(git -C "$REPO" remote get-url --push origin 2>/dev/null)"
  if [ "$url" != "$BARE" ]; then
    echo "STOP: git remote get-url --push origin = '$url', atteso '$BARE'" >&2
    return 1
  fi
}

worktree_lavoro() { # worktree del ramo tg/* del lavoro, sempre sotto $FLOW
  local wt
  wt="$(git -C "$REPO" worktree list --porcelain | awk '/^worktree /{p=$2} /^branch refs\/heads\/tg\//{print p}' | head -1)"
  case "$wt" in "$FLOW"/*) echo "$wt" ;; *) echo "worktree del lavoro non trovato: '$wt'" >&2; return 1 ;; esac
}

claude_step() { # id, prompt
  local id="$1"; shift
  verifica_push || return 1
  # passo1-3: cwd = checkout principale, --continue (come P3a). Dalla chiusura (passo4 in poi)
  # cwd = worktree del lavoro e sessione nuova: una sessione di `claude -p` parte sempre dalla
  # radice, e /tollgate:finish vale solo in una sessione legata al lavoro (SessionStart la lega
  # se il cwd e' nel worktree). Nell'uso interattivo la sessione e' gia' nel worktree.
  local cont=() dir="$REPO"
  case "$id" in
    passo1) ;;
    passo4-radice) cont=(--continue) ;;   # riproduce il tentativo a: radice del checkout
    passo4|passo5*) dir="$(worktree_lavoro)" || return 1 ;;
    *) cont=(--continue) ;;
  esac
  ( cd "$dir" && timeout 1800 claude -p "${cont[@]}" --plugin-dir "$PLUGIN" --model "$MODEL" \
      --permission-mode acceptEdits --allowedTools "$TOOLS" --output-format stream-json --verbose \
      --include-hook-events "$1" < /dev/null ) > "$LOGS/$id.jsonl" 2> "$LOGS/$id.err"
  local rc=$?
  echo "$id: uscita $rc" | tee -a "$LOGS/exit-codes.txt"
}

registra() { # copia i log degli hook e gli eventi del DB
  cp "$STATE/hook-errors.log" "$LOGS/hooks.log" 2>/dev/null || : > "$LOGS/hooks.log"
  [ -f "$STATE/skipped.log" ] && cp "$STATE/skipped.log" "$LOGS/skipped.log"
  ( cd "$REPO" && "${TG[@]}" events > "$LOGS/events.jsonl" 2> "$LOGS/events.err"
    "${TG[@]}" stats > "$LOGS/stats.json" 2> "$LOGS/stats.err"
    "${TG[@]}" status > "$LOGS/status.txt" 2>&1 )
  [ -f "$GH_DATA" ] && cp "$GH_DATA" "$LOGS/fakegh-data-finale.json"
  git -C "$BARE" for-each-ref > "$LOGS/origin-refs.txt" 2>&1
}

passo1() { claude_step passo1 "/tollgate:start #1 L1"; registra; }
passo2() { claude_step passo2 "Nel worktree del lavoro, se non c'è ancora un piano in docs/superpowers/plans/, scrivilo copiando il file $PLAN_SRC in docs/superpowers/plans/2026-10-19-prova.md. Poi controlla che sia committato (il commit del piano è del coordinatore) e, se non lo è, committalo."; registra; }
passo3() { claude_step passo3 "/tollgate:execute"; registra; }
passo4() { claude_step passo4 "/tollgate:finish"; registra; }
# ripetibile: il prompt e' il parametro (predefinito: nuovo atto /tollgate:finish)
# tentativo a della prova (cwd = radice, --continue): l'atto viene rifiutato. Non fa parte di `tutto`.
passo4_radice() { claude_step passo4-radice "/tollgate:finish"; registra; }
passo5() { claude_step "passo5-${2:-1}" "${1:-/tollgate:finish}"; registra; }
passo6() { ( cd "$REPO" && "${TG[@]}" status; "${TG[@]}" events; "${TG[@]}" stats ) > "$LOGS/passo6.txt" 2>&1; registra; }

case "${1:-tutto}" in
  prepara) prepara ;;
  passo1) passo1 ;;
  passo2) passo2 ;;
  passo3) passo3 ;;
  passo4) passo4 ;;
  passo4-radice) passo4_radice ;;
  passo5) passo5 "${2:-}" "${3:-1}" ;;
  passo6) passo6 ;;
  tutto) prepara && passo1 && passo2 && passo3 && passo4 && passo6 ;;
  *) echo "uso: $0 [prepara|passo1|passo2|passo3|passo4|passo5 [prompt [n]]|passo6|tutto]" >&2; exit 2 ;;
esac
