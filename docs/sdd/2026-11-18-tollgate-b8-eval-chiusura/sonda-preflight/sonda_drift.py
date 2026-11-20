"""Applica in-process la decisione 4 a init._drift e fa girare tests.test_init: elenca i test che cambiano esito."""
import sys, os, unittest
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, WT); sys.path.insert(0, os.path.join(WT, "bin"))
os.chdir(WT)
from tollgate_flow import init
from tollgate_core import config

_orig = init._drift

def _drift(area, decl, fragment, rules, lighting, detected, plugin_root):
    out = _orig(area, decl, fragment, rules, lighting, detected, plugin_root)
    head = f"profilo {area}: [profiles.{area}]"
    for key in ("min_level", "checklist"):
        value = fragment.profile.get(key)
        if value and value != config.PROFILE_DEFAULTS[key] and key not in decl:
            out.append(f"{head} {key}: aggiungi {key} = {init._toml_item(value)}")
    return out

init._drift = _drift
mod = sys.argv[1] if len(sys.argv) > 1 else "tests.test_init"
suite = unittest.defaultTestLoader.loadTestsFromName(mod)
res = unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0).run(suite)
print("run", res.testsRun, "fail", len(res.failures), "err", len(res.errors))
for t, _ in res.failures + res.errors:
    print("ROSSO", t.id())
