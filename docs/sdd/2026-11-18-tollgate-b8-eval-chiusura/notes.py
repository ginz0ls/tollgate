import json,sys,pathlib,re
d=pathlib.Path(sys.argv[1])
for t in sorted(d.glob("runs/*/trace.jsonl")):
    for line in open(t,encoding="utf-8",errors="replace"):
        try:o=json.loads(line)
        except Exception: continue
        m=o.get("message") if isinstance(o,dict) else None
        if isinstance(m,dict) and isinstance(m.get("content"),list):
            for b in m["content"]:
                if isinstance(b,dict) and b.get("type")=="tool_use" and b.get("name")=="Bash" and "research submit" in str(b["input"].get("command","")):
                    c=b["input"]["command"]; doc=re.search(r"## Documentazione(.*?)(##|$)",c,re.S)
                    print(t.parent.name, "| doc:", (doc.group(1).strip()[:500] if doc else "-").replace("\n"," / "))
