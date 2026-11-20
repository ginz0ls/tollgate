import sys
sys.path.insert(0, sys.argv[1] + "/bin")
from tollgate_analysis import bash
cfg = bash.EffectsCfg(project_scripts=["deploy"])
def r(t):
    out = []
    try:
        cmds = bash.parse(t, "/tmp/x")
    except bash.BashParseError as e:
        return "PARSEERR " + str(bash.text_effect(t))
    for c in cmds:
        out.append(bash.effect_reason(c, cfg))
    return [o for o in out if o] or None
for line in sys.stdin:
    t = line.rstrip("\n")
    if not t or t.startswith("#"):
        continue
    print(f"{'ASK ' if r(t) else 'PASS'} | {t} | {r(t)}")
