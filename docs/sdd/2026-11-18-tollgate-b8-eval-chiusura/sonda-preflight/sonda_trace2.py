import sys, os, json, importlib.util
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("flowreg", os.path.join(WT, "spikes/b1/flowreg.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def trace(path, size, parent=None, tool="WebFetch"):
    rows = [
     {"type": "assistant", "parent_tool_use_id": parent, "message": {"content": [{"type": "tool_use", "id": "t1", "name": tool, "input": {"url": "https://ai.google.dev/gemini-api/docs/models"}}]}},
     {"type": "user", "parent_tool_use_id": parent, "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "x" * size}]},
      "tool_use_result": {"bytes": size, "code": 200, "result": "x" * size}}]
    open(path, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
for size in (1000, 4999, 5001, 20000):
    p = os.path.join(HERE, f"synt_{size}.jsonl"); trace(p, size, parent="toolu_parent")
    print(size, m.third_party_blocks(p))
# Bash curl con pagina: non toccato
p = os.path.join(HERE, "synt_bash.jsonl"); trace(p, 20000, tool="Bash")
print("bash curl 20000", m.third_party_blocks(p))
