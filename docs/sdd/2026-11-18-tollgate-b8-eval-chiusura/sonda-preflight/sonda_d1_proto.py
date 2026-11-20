import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proto_b8  # applica le patch
import sonda_d1
from sonda_d1 import FORMS, asks
bad = 0
for tag, text, want in FORMS:
    now = asks(text) is not None
    if now != want:
        bad += 1
        print("DIFF", tag, "prototipo:", "chiede" if now else "passa", "| voluto:", "chiede" if want else "passa", "|", text)
print("forme", len(FORMS), "diverse dal voluto:", bad)
