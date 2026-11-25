import json, sys, collections
from pathlib import Path
root = Path(sys.argv[1])
for step in ("passo5", "passo6"):
    p = root / step / "tentativo-1" / "claude.jsonl"
    tools = collections.defaultdict(collections.Counter); models = collections.defaultdict(collections.Counter)
    cmds = collections.defaultdict(list); checklist = collections.Counter(); agents = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try: o = json.loads(line)
        except Exception: continue
        st = o.get("subagent_type") or "(sessione)"
        m = o.get("message") or {}
        if not isinstance(m, dict): continue
        if o.get("type") == "assistant":
            models[st][m.get("model")] += 1
        for c in (m.get("content") if isinstance(m.get("content"), list) else []):
            if not isinstance(c, dict): continue
            if c.get("type") == "tool_use":
                tools[st][c.get("name")] += 1
                inp = c.get("input") or {}
                if c.get("name") == "Bash": cmds[st].append(str(inp.get("command"))[:110].replace("\n", " "))
                if c.get("name") == "Agent": agents.append((inp.get("subagent_type"), inp.get("name"), inp.get("model"), inp.get("run_in_background"), str(inp.get("prompt"))[:90]))
            if c.get("type") == "tool_result":
                t = json.dumps(c.get("content"), ensure_ascii=False)
                if "Lista di controllo dell'area" in t: checklist[st] += 1
                if "accesso negato provato da un test" in t: checklist[st + " (voce security)"] += 1
    print("==", step)
    for st in models: print("  ", st, "modelli:", dict(models[st]), "strumenti:", dict(tools[st]))
    print("   lista di controllo letta da:", dict(checklist))
    for a in agents: print("   Agent:", a)
    for st in cmds:
        if "final" in st or "reviewer" in st or "verifier" in st:
            print("   comandi di", st, ":", cmds[st][:14])
