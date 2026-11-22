"""Sonda: forma di ctx.config.profiles, vertical_for, specdoc.slices sul testo del piano."""
import sys
from pathlib import Path
W = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(W / "bin")); sys.path.insert(0, str(W))
sys.dont_write_bytecode = True
from tollgate_core import config
from tollgate_analysis import profiles as prof, specdoc, plan as planmod
from tests.test_check_post_edit import plan_text

toml = '''schema_version = 1
[gate]
mode = "detect"
[profiles.ai]
kind = "vertical"
paths = ["ai/**"]
[profiles.infra]
kind = "vertical"
paths = ["/vercel.json", "infra/**"]
[profiles.base]
kind = "cross"
paths = ["**"]
'''
c = config.load_config_text(toml)
p = c.profiles
print("tipo:", type(p).__name__, sorted(p), "kind base:", p["base"]["kind"])
for f in ("ai/a.py", "ai/b.py", "vercel.json", "README.md", "src/x.py"):
    print(f, "->", prof.vertical_for(f, p))
# profilo senza paths: default "**"
c2 = config.load_config_text('schema_version = 1\n[gate]\nmode="detect"\n[profiles.web]\nkind="vertical"\n')
print("profilo senza paths vertical_for(src/x.py):", prof.vertical_for("src/x.py", c2.profiles), c2.profiles["web"]["paths"])
t = plan_text()
print("slices(plan) =", specdoc.slices(t))
t3 = t + "\n## Fette previste\n1. A\n2. B\n3. C\n"
print("slices(plan con 3 voci) =", specdoc.slices(t3))
r = planmod.check_plan(t, required_sections=["Fatti verificati","Decisioni","Interfacce","Must-have","Scope","Punti di arresto","Rischi"], max_scope_files=20, must_have_tests=False, level="L1", profiles=p, active_always=[])
print("ok:", r.ok, r.problems, "scope:", r.scope, "tasks:", [(t.number, t.files) for t in r.tasks])
