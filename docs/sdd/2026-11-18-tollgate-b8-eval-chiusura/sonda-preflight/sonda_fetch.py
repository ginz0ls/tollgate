"""Decisione 7: un PostToolUse di WebFetch (passo `fetch` della prova a secco) arriva in lookups?"""
import sys, os, sqlite3, glob
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, WT); sys.path.insert(0, os.path.join(WT, "bin"))
os.chdir(WT)
import tests.test_eval_cases as tec

def _do_fetch(self, ev):
    agent, url = ev["agent"], ev["url"]
    ti = {"url": url, "prompt": "p"}
    uid = self._use("WebFetch", ti, agent)
    resp = ev.get("response", {"code": 200, "result": "testo finto della pagina"})
    post = self.hook("PostToolUse", tool="WebFetch", tool_input=ti, agent=agent, response=resp)
    self._result(uid, "pagina finta", error=False, agent=agent)
    return {"denied": False, "rc": post.returncode, "text": post.stdout}
tec._Session._do_fetch = _do_fetch

case = tec.load_case(tec.EVALS / "s1-done-senza-ricevuta" / "case.yaml")
URL = "https://ai.google.dev/gemini-api/docs/models/"
for label, resp in (("code200", {"code": 200, "result": "x"}), ("code404", {"code": 404, "result": "x"}), ("senza_code", {"result": "x"}), ("code_str", {"code": "200"})):
    s = tec._Session(case, "worktree")
    try:
        s.step(tec.impl_launch())
        s.step({"do": "fetch", "agent": "ag-1", "url": URL, "response": resp})
        s.step({"do": "read", "agent": "ag-1", "path": "{wt}/src/calc.py"})
        dbs = glob.glob(str(s.built.state_root / "**" / "*.db"), recursive=True)
        rows = []
        for d in dbs:
            c = sqlite3.connect(f"file:{d}?mode=ro&immutable=1", uri=True)
            try:
                rows += c.execute("SELECT kind, target, task, agent_id FROM lookups").fetchall()
            except sqlite3.Error as e:
                rows.append(("errore", str(e)))
            c.close()
        print(label, rows)
    finally:
        s.close()
