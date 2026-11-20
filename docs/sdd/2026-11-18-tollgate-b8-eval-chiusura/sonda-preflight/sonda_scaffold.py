"""Decisione 8: scaffold.build con extra_files per i tre casi nuovi (prototipo dei dati, fuori dal repo)."""
import sys, os, shutil, tempfile, json, subprocess, tomllib
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, WT); sys.path.insert(0, os.path.join(WT, "bin"))
os.chdir(WT)
from pathlib import Path
from evals._kit import recipes, scaffold
from tollgate_flow import init
from tollgate_analysis import naming

print("slug:", [naming.slug(t) for t in ("Aggiorna il modello Gemini", "Reindirizza la pagina vecchia", "Aggiungi la divisione")])

PLAN = """# Piano: {t}

## Fatti verificati
Nessuno: piano di prova del banco degli eval.

## Decisioni
Nessuno: piano di prova del banco degli eval.

## Interfacce
Nessuno: piano di prova del banco degli eval.

## Must-have
M1. {m} — test: {tid}

## Scope
Il file del task, e nessun altro.

## Punti di arresto
Nessuno: piano di prova del banco degli eval.

## Rischi
Nessuno: piano di prova del banco degli eval.

### Task 1: {t}
- Modify: `{f}`
{test}**Must-have**: M1
"""
CASES = {
 "ai": dict(title="Aggiorna il modello Gemini", plan="ai-modello", files={"ai/client.py": 'MODEL = "gemini-1.5-flash"\n',
            "ai/__init__.py": "", "tests/test_client.py": "import unittest\nfrom ai import client\n\nclass ClientTest(unittest.TestCase):\n    def test_model(self):\n        self.assertTrue(client.MODEL)\n"},
            modify="ai/client.py", test="tests/test_client.py", tid="tests.test_client.ClientTest::test_model", area="ai"),
 "infra": dict(title="Reindirizza la pagina vecchia", plan="infra-redirect", files={"vercel.json": '{"rewrites": [{"source": "/api/(.*)", "destination": "/api/index.py"}]}\n'},
            modify="vercel.json", test=None, tid="tests.test_calc.CalcTest::test_somma", area="infra"),
 "calc": dict(title="Aggiungi la divisione", plan="calc-dividi", files={"src/operazioni/__init__.py": "", "src/operazioni/divisione.py": "def dividi(a, b):\n    return a / b\n"},
            modify="src/calc.py", test="tests/test_calc.py", tid="tests.test_calc.CalcTest::test_somma", area=None),
}
tmp = Path(tempfile.mkdtemp(prefix="tollgate-sonda-"))
try:
    fx = tmp / "fixtures"
    shutil.copytree(scaffold.FIXTURES, fx)
    scaffold.FIXTURES = fx
    for key, c in CASES.items():
        testline = f"- Test: `{c['test']}`\n" if c["test"] else ""
        (fx / "plans" / f"{c['plan']}.md").write_text(PLAN.format(t=c["title"], m="Il comportamento resta", tid=c["tid"], f=c["modify"], test=testline))
        extra = dict(c["files"])
        toml = recipes._TOML
        if c["area"]:
            got = init.profile_blocks({f: 10 for f in list(extra) + ["src/calc.py", "tests/test_calc.py"]}, toml, Path(WT))
            print(f"--- init propone per {key}:")
            print(got.text)
            for l in got.lines: print("  riga:", l)
            toml = toml + got.text
            extra["tollgate.toml"] = toml
        r = recipes.Recipe(f"prova-{key}", "L1", issue_title=c["title"], plan=c["plan"], task_started=1, phase="execution", extra_files=extra,
                           issue_body=c["title"])
        ws = tmp / f"ws-{key}"; home = tmp / f"home-{key}"
        ws.mkdir(); home.mkdir()
        try:
            b = scaffold.build(r, workspace=ws, home=home)
            print(key, "worktree:", os.path.relpath(b.worktree, ws), "ramo", b.work_branch)
            brief = (b.worktree / ".tollgate-run" / "1" / "task-1.md")
            head = brief.read_text().splitlines()[:6]
            print("  brief:", [l for l in head if "agente" in l.lower() or "implementer" in l.lower() or "name" in l.lower()][:4] or head[:3])
            out = subprocess.run([sys.executable, "-B", os.path.join(WT, "bin/tollgate"), "status", "--json"], cwd=str(ws), env={**os.environ, "HOME": str(home), "TOLLGATE_STATE": str(home/".local/state/tollgate")}, capture_output=True, text=True)
            print("  status:", out.stdout[:200].replace("\n", " "))
        except Exception as e:
            print(key, "ERRORE", str(e)[:600])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
