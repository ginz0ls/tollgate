"""Sonda dello scan: quali casi della tabella sono GIÀ verdi senza il frammento `security`
(Task 4, Step 2 del piano: «S6, S11, S12, S23, S25, S32, S37, S38, S43, S48, S60»).
Uso: cd <copia git archive> && python3 -B <questo file>"""
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path.cwd() / "bin"))
import sonda  # noqa: E402
from tollgate_analysis import profiles  # noqa: E402
from tollgate_core import fragments  # noqa: E402
from tollgate_flow import init  # noqa: E402

with tempfile.TemporaryDirectory(prefix="tollgate-sonda-") as tmp:
    root = Path(tmp)
    (root / "templates" / "profiles").mkdir(parents=True)
    for fr in fragments.load(Path.cwd()):
        if fr.area == "security":
            continue
        shutil.copy(fr.source, root / "templates" / "profiles" / fr.source.name)
        skill = root / "skills" / f"rules-{fr.area}"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\napproved: 2026-11-01\n---\nR-{fr.area.upper()}-01 [blocca] x\n", encoding="utf-8")
    base = (Path.cwd() / "templates" / "tollgate.toml").read_text(encoding="utf-8").replace("__MODE__", "detect")
    green = []
    for name, files, detected, proposal, runtime, _ in sonda.CASES:
        got = init.profile_blocks({f: 10 for f in files}, base, root, detected=detected or None)
        declared = {k: v for k, v in tomllib.loads(base + got.text).get("profiles", {}).items()
                    if isinstance(v, dict)}
        ok = {a: sorted(p["paths"]) for a, p in declared.items()} == {a: sorted(p) for a, p in proposal.items()} \
            and all(profiles.vertical_for(f, declared) == a for f, a in runtime.items())
        if ok:
            green.append(name)
    print("già verdi senza il frammento security:", ", ".join(green))
