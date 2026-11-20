import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, "bin")
from tollgate_analysis import bash
cfg = bash.EffectsCfg([], ["deploy","release"], [])
def r(t):
    out=[]
    try:
        for c in bash.parse(t, "/tmp"):
            x = bash.effect_reason(c, cfg)
            if x: return x
    except Exception as e:
        return "EXC %r" % e
    return None
import fileinput
for line in sys.stdin:
    line=line.rstrip("\n")
    if line: print("ASK " if r(line) else "PASS", line, "|", r(line) or "")
