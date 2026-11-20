import sys, os, glob, importlib.util
sys.dont_write_bytecode = True
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
spec = importlib.util.spec_from_file_location("flowreg", os.path.join(WT, "spikes/b1/flowreg.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tot = 0; n = 0; nz = 0
for f in sorted(glob.glob(os.path.join(WT, "docs/verifiche/evidenze/eval-p5/*/runs/*/trace.jsonl"))):
    b = m.third_party_blocks(f)
    n += 1; tot += len(b)
    if b:
        nz += 1
        print(os.path.relpath(f, WT), len(b), b[:2])
print("trace", n, "con blocchi", nz, "blocchi totali", tot)
# trace sintetica: forma di tool_result di WebFetch
