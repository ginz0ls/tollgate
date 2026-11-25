import json, sys, collections
from pathlib import Path
names = collections.Counter(); big = []; outs = collections.Counter()
for p in sorted(Path(sys.argv[1]).rglob("claude.jsonl")):
    for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        try: o = json.loads(line)
        except Exception: continue
        if o.get("subtype") in ("hook_started", "hook_response"):
            names[(o.get("hook_event"), o.get("hook_name"), o.get("subtype"))] += 1
            if o.get("subtype") == "hook_response":
                tot = sum(len(str(o.get(k) or "")) for k in ("output", "stdout", "stderr"))
                outs[(o.get("hook_name"), min(tot, 99999) // 500 * 500)] += 1
                if tot > 400: big.append((p.parts[-3], n, o.get("hook_name"), tot, str(o.get("stdout") or o.get("output"))[:300].replace("\n", " ")))
for k, v in sorted(names.items(), key=str): print(v, k)
print("uscite per taglia:", sorted(outs.items(), key=str))
for b in big[:25]: print(b)
print(len(big), "risposte di hook sopra 400 caratteri")
