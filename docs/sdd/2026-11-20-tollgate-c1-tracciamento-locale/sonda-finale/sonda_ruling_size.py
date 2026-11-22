"""Sonda della revisione finale: etichette delle ruling e righe della taglia (sola lettura, funzioni pure)."""
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "bin"))
from tollgate_flow import ruling_cmd
from tollgate_analysis import worksize as ws

for label in ("perché", "perche", "PERCHÉ", "perchè", "Perchè"):
    f, p = ruling_cmd.parse_text(f"cosa: a\n{label}: b\ncosto: c\n")
    print(repr(label), "ok" if f else p)

S = ws.Signals
print(ws.preview(S("L2", 3, 0, 1), "small", "rules", cause="level"))
print(ws.preview(S("L1", 2, 0, 3), "small", "rules", cause="plan"))
print(ws.preview(S("L2", 0, 0, 3), "medium", "rules", cause="approve_spec", confirmed=True))
print(ws.preview(S("L2", 0, 0, 1), "large", "user", cause="approve_spec", confirmed=False))
print(ws.preview(S("L1", 0, 0, 1), None, None, cause="plan"))
