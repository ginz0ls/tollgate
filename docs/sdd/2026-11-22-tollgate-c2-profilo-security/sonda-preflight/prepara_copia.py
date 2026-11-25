#!/usr/bin/env python3
"""Porta una copia `git archive` allo stato «dopo i Task 3 e 4» quanto basta per i test delle
precedenze: `keep_paths` simulata se manca, e il frammento candidato con una skill finta approvata
se `templates/profiles/security.toml` manca. Solo sulla copia in /tmp, mai sul repo."""
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sonda  # noqa: E402

copy = Path(sys.argv[1]).resolve()
assert str(copy).startswith("/tmp/tollgate"), "solo su una copia sotto /tmp/tollgate…"
print("keep_paths simulata:", sonda.simulate(copy))
target = copy / "templates" / "profiles" / "security.toml"
if not target.exists():
    import os
    shutil.copy(os.environ.get("SONDA_FRAMMENTO") or HERE / "security.toml", target)
    skill = copy / "skills" / "rules-security"
    skill.mkdir(parents=True, exist_ok=True)
    if not (skill / "SKILL.md").exists():
        (skill / "SKILL.md").write_text(
            "---\nname: rules-security\nversion: 1\napproved: 2026-11-22\n---\n"
            "# Regole security (finta della sonda)\n\nR-SECURITY-01 [blocca] x\n", encoding="utf-8")
    print("frammento candidato e skill finta aggiunti")
