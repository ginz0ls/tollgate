import sys
from pathlib import Path

_BIN = Path(__file__).resolve().parents[1] / "bin"
if str(_BIN) not in sys.path:
    sys.path.insert(0, str(_BIN))
