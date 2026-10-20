#!/usr/bin/env bash
# spikes/run-p3c-flow.sh — prova reale del percorso L2 di P3c con `claude -p` (Task 14).
# Percorso: skill -> CLI -> hook -> agenti, su un repo locale: /tollgate:start #1 L2, spec e giri
# avversariali, `approve spec 1`, piano e avversario del piano, `approve plan`, esecuzione del task 1.
# Nessuna rete verso GitHub, nessun plugin installato. Tutto sotto /tmp/tollgate-p3c/flow. Il solo
# push ammesso va al repo nudo locale dietro l'URL finto con insteadOf (decisione 23); prima di
# ogni passo lo script controlla che `git remote get-url --push origin` sia quel repo nudo.
# Dal passo 2 ogni `claude -p` parte dalla cartella del worktree del lavoro (sessione nuova, legata
# da SessionStart) e lo script lo verifica prima di lanciare; mai --continue.
#
# Uso: bash spikes/run-p3c-flow.sh \
#        [prepara|passo1|passo2|passo3|passo4|passo5|passo6|libero "<prompt>"|registra|tutto]
# (predefinito: tutto). `libero` si ripete (per esempio /tollgate:resolve <id> <nota> a un tetto).
# PLUGIN_LINK=1 usa il link senza spazi $FLOW/plugin al posto del percorso reale del worktree.
set -uo pipefail

PLUGIN_REAL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
FLOW=/tmp/tollgate-p3c/flow
if [ "${PLUGIN_LINK:-0}" = 1 ]; then PLUGIN="$FLOW/plugin"; else PLUGIN="$PLUGIN_REAL"; fi
REPO="$FLOW/repo"          # checkout principale (cwd del solo passo 1)
BARE="$FLOW/origin.git"    # repo nudo locale, dietro l'URL finto
STATE="$FLOW/state"
LOGS="$FLOW/logs"
SPEC_SRC="$FLOW/spec-L2.md"
PLAN_SRC="$FLOW/piano-L2.md"
GH_DATA="$FLOW/fakegh-data.json"
ORIGIN_URL=https://github.com/prova/flow.git
MODEL=sonnet
TOOLS="Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob"

export TOLLGATE_STATE="$STATE"
export TOLLGATE_GH="$PLUGIN_REAL/tests/fakegh.py"
export TOLLGATE_FAKEGH_DATA="$GH_DATA"
export TOLLGATE_FAKEGH_LOG="$LOGS/fakegh.log"
TG=(python3 "$PLUGIN/bin/tollgate")

prepara() {
  case "$FLOW" in /tmp/tollgate-p3c/flow) ;; *) echo "percorso inatteso: $FLOW" >&2; return 1 ;; esac
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
  cat > "$SPEC_SRC" <<'MD'
# Spec di prova: sottrai

## Obiettivo

Aggiungere a `src/calc.py` la funzione `sottrai(a, b)`, con il suo test in `tests/test_calc.py`.

## Fette previste

1. Funzione `sottrai(a, b)` con il test in `CalcTest`.

## Tane di coniglio

- Argomenti non numerici: scelta fatta, nessun controllo di tipo; `sottrai` restituisce `a - b` e lascia a Python l'errore.
- Risultato negativo: scelta fatta, è ammesso e restituito com'è (`sottrai(0, 4) == -4`).
- Nuovo modulo o classe: scelta fatta, la funzione sta in `src/calc.py` accanto a `somma`, senza classi.

## Cosa non fare

- Nessuna altra operazione (moltiplica, dividi) e nessuna validazione degli argomenti.
- Nessuna modifica a `somma` né a `tools/unittest_junit.py`.
MD
  cat > "$PLAN_SRC" <<'MD'
# Piano di prova: sottrai

## Fatti verificati

- `src/calc.py` contiene solo `somma(a, b)`; `tests/test_calc.py` ha `CalcTest.test_somma`.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `sottrai(a, b)` restituisce `a - b`, senza altri argomenti né controlli di tipo (tana «argomenti non numerici» della spec).
- Il risultato negativo è ammesso (tana «risultato negativo» della spec).

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
  # spec e piano di prova devono passare i controlli PRIMA della prova reale
  python3 -B - "$PLUGIN" "$REPO" "$SPEC_SRC" "$PLAN_SRC" <<'PY' || return 1
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1] + "/bin")
from tollgate_core import config
from tollgate_analysis import plan, specdoc
cfg = config.load_config_at(Path(sys.argv[2]), "origin/main")
c = cfg.data
spec = Path(sys.argv[3]).read_text()
problems = specdoc.pitch_problems(spec)
print("spec-check:", "ok" if not problems else problems, "fette:", specdoc.slices(spec))
r = plan.check_plan(Path(sys.argv[4]).read_text(), required_sections=c["plan"]["required_sections"],
                    max_scope_files=c["plan"]["max_scope_files"], must_have_tests=True, level="L2",
                    profiles=cfg.profiles, active_always=c["profiles"]["active"])
print("plan-check:", "ok" if r.ok else r.problems, r.warnings)
sys.exit(0 if (r.ok and not problems and specdoc.slices(spec) == 1) else 1)
PY
  verifica_push || return 1
  echo "pronto: $REPO"
}

# decisione 23: nessun push in rete. Ferma lo script se il push di origin non va al repo nudo locale.
verifica_push() {
  local url
  url="$(git -C "$REPO" remote get-url --push origin 2>/dev/null)"
  if [ "$url" != "$BARE" ]; then
    echo "STOP: git remote get-url --push origin = '$url', atteso '$BARE'" >&2
    return 1
  fi
}

worktree_lavoro() { # worktree del ramo tg/1-* del lavoro, sempre sotto $FLOW
  local wt
  wt="$(git -C "$REPO" worktree list --porcelain | awk '/^worktree /{p=$2} /^branch refs\/heads\/tg\/1-/{print p}' | head -1)"
  case "$wt" in "$FLOW"/*) echo "$wt" ;; *) echo "worktree del lavoro non trovato: '$wt'" >&2; return 1 ;; esac
}

# $1 = id del passo (log), $2 = prompt. Passo 1: cwd = checkout principale. Ogni altro passo: cwd
# = worktree del lavoro (verificato: ramo tg/1-*, sotto $FLOW), sessione nuova. Mai --continue.
claude_step() {
  local id="$1" prompt="$2" dir="$REPO"
  verifica_push || return 1
  if [ "$id" != passo1 ]; then
    dir="$(worktree_lavoro)" || return 1
    case "$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null)" in tg/1-*) ;; *)
      echo "STOP: $dir non e' sul ramo tg/1-*" >&2; return 1 ;; esac
    case "$dir" in "$FLOW"/*) ;; *) echo "STOP: $dir fuori da $FLOW" >&2; return 1 ;; esac
  fi
  ( cd "$dir" && timeout 1800 claude -p --add-dir "$FLOW" --plugin-dir "$PLUGIN" --model "$MODEL" \
      --permission-mode acceptEdits --allowedTools "$TOOLS" --output-format stream-json --verbose \
      --include-hook-events "$prompt" < /dev/null ) > "$LOGS/$id.jsonl" 2> "$LOGS/$id.err"
  local rc=$?
  echo "$id: uscita $rc (cwd $dir)" | tee -a "$LOGS/exit-codes.txt"
}

registra() { # copia i log degli hook, gli eventi del DB, i report e le sessioni dei passi
  cp "$STATE/hook-errors.log" "$LOGS/hooks.log" 2>/dev/null || : > "$LOGS/hooks.log"
  [ -f "$STATE/skipped.log" ] && cp "$STATE/skipped.log" "$LOGS/skipped.log"
  ( cd "$REPO" && "${TG[@]}" events > "$LOGS/events.jsonl" 2> "$LOGS/events.err"
    "${TG[@]}" stats > "$LOGS/stats.json" 2> "$LOGS/stats.err"
    "${TG[@]}" status > "$LOGS/status.txt" 2>&1 )
  local wt; wt="$(worktree_lavoro 2>/dev/null)" && {
    rm -rf "$LOGS/reviews-1"; cp -r "$wt/docs/superpowers/reviews/1" "$LOGS/reviews-1" 2>/dev/null
    git -C "$wt" log --format='%h %s' > "$LOGS/git-log-worktree.txt" 2>&1
    git -C "$wt" status --short > "$LOGS/git-status-worktree.txt" 2>&1
  }
  [ -f "$GH_DATA" ] && cp "$GH_DATA" "$LOGS/fakegh-data-finale.json"
  git -C "$BARE" for-each-ref > "$LOGS/origin-refs.txt" 2>&1
  python3 -B - "$LOGS" > "$LOGS/sessioni.txt" <<'PY'
import json, sys
from pathlib import Path
for f in sorted(Path(sys.argv[1]).glob("*.jsonl")):
    if f.name == "events.jsonl":
        continue
    sid = cwd = "?"
    for line in f.read_text(errors="replace").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "system" and d.get("subtype") == "init":
            sid, cwd = d.get("session_id", "?"), d.get("cwd", "?")
            break
    print(f"{f.stem}\t{sid}\t{cwd}")
PY
}

spec_nel_ramo() { # 0 se nel worktree c'e' gia' qualcosa sotto docs/superpowers/specs/
  local wt; wt="$(worktree_lavoro)" || return 1
  [ -d "$wt/docs/superpowers/specs" ] && [ -n "$(ls -A "$wt/docs/superpowers/specs")" ]
}

passo1() {
  claude_step passo1 "/tollgate:start #1 L2"; registra
  # In L2 senza --spec la skill start manda il modello al brainstorming e lui scrive e committa una
  # spec sua (provato in due esecuzioni su due: vedi il rapporto). Non e' un errore: il passo 2
  # usa quella spec al posto di $SPEC_SRC. Si ferma solo se le spec sono piu' di una (il «primo file
  # nuovo» di audit prepare sarebbe ambiguo).
  if spec_nel_ramo; then
    local wt n; wt="$(worktree_lavoro)" || return 1
    n="$(ls "$wt/docs/superpowers/specs" | wc -l)"
    echo "NOTA: il passo 1 ha scritto la spec del modello ($n file: $(ls "$wt/docs/superpowers/specs" | tr '\n' ' '))" | tee -a "$LOGS/exit-codes.txt"
    [ "$n" = 1 ] || { echo "STOP: piu' di una spec: rifare il passo 1" >&2; return 1; }
  fi
}
passo2() {
  local wt f; wt="$(worktree_lavoro)" || return 1
  if spec_nel_ramo; then
    f="$(ls "$wt/docs/superpowers/specs")"
    claude_step passo2 "La spec è già scritta e committata in docs/superpowers/specs/$f: segui /tollgate:spec-audit finché audit prepare non chiede /tollgate:approve spec 1."
  else
    claude_step passo2 "La spec è in $SPEC_SRC: copiala in docs/superpowers/specs/2026-10-20-prova.md senza cambiarla, committala, poi segui /tollgate:spec-audit finché audit prepare non chiede /tollgate:approve spec 1."
  fi
  registra
}
passo3() { claude_step passo3 "/tollgate:approve spec 1"; registra; }
passo4() { claude_step passo4 "Il piano è in $PLAN_SRC: scrivilo con lo strumento Write in docs/superpowers/plans/2026-10-20-prova.md (così passa da plan-check), committalo, poi segui /tollgate:spec-audit per l'avversario del piano finché non chiede /tollgate:approve plan."; registra; }
passo5() { claude_step passo5 "/tollgate:approve plan"; registra; }
passo6() { claude_step passo6 "/tollgate:execute"; registra; }
# libero "<prompt>": un prompt dal worktree, per esempio /tollgate:resolve <id> <nota> a un tetto
libero() {
  [ -n "${1:-}" ] || { echo "uso: $0 libero \"<prompt>\"" >&2; return 2; }
  local n=1; while [ -e "$LOGS/libero-$n.jsonl" ]; do n=$((n + 1)); done
  claude_step "libero-$n" "$1"; registra
}

case "${1:-tutto}" in
  prepara) prepara ;;
  passo1) passo1 ;;
  passo2) passo2 ;;
  passo3) passo3 ;;
  passo4) passo4 ;;
  passo5) passo5 ;;
  passo6) passo6 ;;
  libero) libero "${2:-}" ;;
  registra) registra ;;
  tutto) prepara && passo1 && passo2 && passo3 && passo4 && passo5 && passo6 ;;
  *) echo "uso: $0 [prepara|passo1|passo2|passo3|passo4|passo5|passo6|libero \"<prompt>\"|registra|tutto]" >&2; exit 2 ;;
esac
