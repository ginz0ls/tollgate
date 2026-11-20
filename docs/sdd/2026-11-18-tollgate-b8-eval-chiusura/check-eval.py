"""Controllo del controller sulle evidenze di un caso (mai stampa testo di pagine né utente/host)."""
import json, sys, pathlib, sqlite3, re, os, subprocess
d = pathlib.Path(sys.argv[1]).resolve()
print((d / "tabella.md").read_text() if (d / "tabella.md").exists() else "NO tabella")
print((d / "nota.md").read_text() if (d / "nota.md").exists() else "NO nota")
r = json.load(open(d / "result.json"))
for c in r["cases"]:
    for arm, runs in c["arms"].items():
        for i, run in enumerate(runs):
            print(f"{arm}[{i}] score={run['score']} turns={run['turns']} dur={run['durationSeconds']} err={run.get('error')}")
            for g in run["graders"]:
                print(f"     {'OK ' if g['passed'] else 'no '} {g['name']}: {g['explanation'][:100]}")
for t in sorted(d.glob("runs/*/trace.jsonl")):
    ids = {}; out = []
    for line in open(t, encoding="utf-8", errors="replace"):
        try: o = json.loads(line)
        except Exception: out.append("RIGA NON JSON"); continue
        if not isinstance(o, dict): continue
        if o.get("subtype") == "permission_denied": out.append(f"DENIED {o.get('tool_name')}")
        m = o.get("message")
        if isinstance(m, dict) and isinstance(m.get("content"), list):
            for b in m["content"]:
                if not isinstance(b, dict): continue
                if b.get("type") == "tool_use" and b.get("name") in ("WebFetch", "WebSearch"):
                    ids[b["id"]] = b["name"]; out.append(f"{b['name']} {json.dumps(b['input'].get('url') or b['input'].get('query'))}")
                if b.get("type") == "tool_result" and b.get("tool_use_id") in ids:
                    c = b.get("content"); s = c if isinstance(c, str) else json.dumps(c)
                    if not s.startswith("[pagina di terzi tolta") and "tolt" not in s[:60]: out.append(f"  !!! RISULTATO WEB NON SEGNAPOSTO len={len(s)}")
                if b.get("type") == "text" and not o.get("parent_tool_use_id"):
                    out.append("MAIN: " + b["text"][:400].replace("\n", " "))
    print("== trace", t.parent.name); print("\n".join(out[-14:]))
