import sys
sys.path.insert(0, sys.argv[1] + "/bin")
from tollgate_analysis import bash
for line in sys.stdin:
    t = line.strip()
    if not t or t.startswith("#"): continue
    for c in bash.parse(t, "/tmp/x"):
        ins = bash.true_inner_commands(c)
        print(t, "=>", [(" ".join(i.argv), bash.script_path(i, inner=True)) for i in ins])
