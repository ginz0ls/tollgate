import json, sys, re, collections
from pathlib import Path
root = Path(sys.argv[1])
types = collections.Counter(); initkeys = collections.Counter(); models = collections.Counter()
toolnames = collections.Counter(); longres = []; uuids = collections.Counter(); keys_top = collections.Counter()
susp = collections.Counter()
SUSP = re.compile(r"rate_limit|credential|expires_at|api_?key|organization|account_uuid|email|oauth|mcp_servers|plugins|slash_commands|memory_paths|apiKeySource|permissionMode|cwd", re.I)
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if SUSP.search(k): susp[k] += 1
            walk(v, path + "/" + k)
    elif isinstance(o, list):
        for v in o: walk(v, path)
for p in sorted(root.rglob("claude.jsonl")):
    for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip(): continue
        try: o = json.loads(line)
        except Exception as e:
            print("NON JSON", p, n, line[:80]); continue
        types[(o.get("type"), o.get("subtype"))] += 1
        keys_top.update(o.keys())
        walk(o)
        if o.get("type") == "system" and o.get("subtype") == "init":
            initkeys.update(o.keys())
            print("INIT", p.parts[-3], {k: (v if not isinstance(v, (list, dict)) else (len(v), str(v)[:300])) for k, v in o.items()})
        m = (o.get("message") or {})
        if isinstance(m, dict):
            if m.get("model"): models[m["model"]] += 1
            for c in m.get("content") or [] if isinstance(m.get("content"), list) else []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    toolnames[c.get("name")] += 1
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    t = c.get("content"); t = json.dumps(t, ensure_ascii=False) if not isinstance(t, str) else t
                    if len(t) > 20000: longres.append((p.parts[-3], n, len(t), t[:100]))
        if o.get("type") == "result":
            print("RESULT", p.parts[-3], {k: o.get(k) for k in ("num_turns", "duration_ms", "total_cost_usd", "is_error", "subtype")}, "modelUsage:", {k: round(v.get("costUSD", 0), 3) for k, v in (o.get("modelUsage") or {}).items()})
print("tipi:", dict(types)); print("chiavi sospette:", dict(susp)); print("modelli dei messaggi:", dict(models))
print("strumenti:", dict(toolnames)); print("risultati lunghi:", longres[:10]); print("chiavi:", dict(keys_top))
