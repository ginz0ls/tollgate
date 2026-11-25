import json, sys, collections
from pathlib import Path
ids = {}; res = []
for p in sorted(Path(sys.argv[1]).rglob("claude.jsonl")):
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try: o = json.loads(line)
        except Exception: continue
        m = o.get("message") or {}
        for c in (m.get("content") if isinstance(m, dict) and isinstance(m.get("content"), list) else []):
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") in ("WebFetch", "WebSearch"):
                ids[c["id"]] = (p.parts[-3], (c.get("input") or {}).get("url"))
            if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") in ids:
                t = c.get("content"); t = json.dumps(t, ensure_ascii=False) if not isinstance(t, str) else t
                res.append((ids[c["tool_use_id"]], len(t), t[:90]))
        tr = o.get("tool_use_result")
        if isinstance(tr, dict) and ("url" in tr or "result" in tr and "durationMs" in tr and "code" in tr):
            res.append((("tool_use_result", tr.get("url")), len(json.dumps(tr, ensure_ascii=False)), json.dumps(tr, ensure_ascii=False)[:160]))
for r in res: print(r)
