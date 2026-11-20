import json, sys, subprocess
files = subprocess.run(["git","ls-files","docs/verifiche/evidenze/eval-b8"],capture_output=True,text=True).stdout.split()
uses = {}; res = []; bash_dom = []
for f in files:
    if not f.endswith("trace.jsonl"): continue
    for line in open(f, encoding="utf-8", errors="replace"):
        try: o = json.loads(line)
        except ValueError: continue
        m = o.get("message")
        c = m.get("content") if isinstance(m, dict) else None
        for b in c if isinstance(c, list) else []:
            if not isinstance(b, dict): continue
            if b.get("type") == "tool_use" and b.get("name") in ("WebFetch","WebSearch"):
                uses[b.get("id")] = (f, b.get("name"))
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                cmd = (b.get("input") or {}).get("command","")
                if any(d in cmd for d in ("ai.google.dev","aistudio.google.com","vercel.com")):
                    bash_dom.append((f.split("/")[4], cmd[:160]))
            if b.get("type") == "tool_result" and b.get("tool_use_id") in uses:
                cc = b.get("content")
                t = cc if isinstance(cc, str) else " ".join(x.get("text","") for x in cc if isinstance(x, dict)) if isinstance(cc, list) else ""
                res.append((uses[b["tool_use_id"]][1], t[:90].replace("\n"," "), len(t), "tool_use_result" in o))
print("tool_use web:", len(uses), "risultati:", len(res))
from collections import Counter
print(Counter(r[0] for r in res))
for r in res:
    if not r[1].startswith("[pagina"): print("NON SEGNAPOSTO:", r)
print("esempio:", res[0][1] if res else None)
print("Bash che nominano un dominio:", len(bash_dom))
for b in bash_dom: print(" ", b)
