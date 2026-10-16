"""Banco di prova degli hook: input reali di Claude Code (P0) e un repo attivo con un lavoro."""
import copy
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.helpers import ROOT, TempState, git, make_origin_repo
from tollgate_core import db, git as core_git, phases
from tollgate_core.paths import repo_key
from tollgate_hooks import runner

SAMPLES = json.loads((ROOT / "spikes/fixtures/hook-inputs/samples.json").read_text())
SESSION = "sess-lab"
T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
DROP = object()
DEFAULT_TOML = """schema_version = 1
[gate]
mode = "protected"
[commands]
verify = "true"
gate = ["verify"]
"""
DEFAULT_FILES = {
    "src/app.py": "def somma(a, b):\n    return a + b\n",
    "tests/test_app.py": "from src.app import somma\n\n\ndef test_somma():\n"
                         "    assert somma(1, 2) == 3\n\n\ndef test_zero():\n"
                         "    assert somma(0, 0) == 0\n",
    "docs/superpowers/README.md": "doc\n",
    ".gitignore": "reports/\n",
}


def sample(name, **changes):
    """Un input reale con i campi cambiati; i nomi di Task 1 mancanti si costruiscono dalla
    busta di PreToolUse-Bash con tool_name e tool_input della documentazione."""
    if name in SAMPLES:
        s = copy.deepcopy(SAMPLES[name])
    else:
        event, _, tool = name.partition("-")
        s = copy.deepcopy(SAMPLES[f"{event}-Bash"] if event in ("PreToolUse", "PostToolUse")
                          else SAMPLES["SessionStart-none"])
        s["hook_event_name"] = event
        if tool:
            s["tool_name"] = tool.split("-")[0]
    for k, v in changes.items():
        if v is DROP:
            s.pop(k, None)
        else:
            s[k] = v
    return s


class Lab:
    def __init__(self, *, level="L1", phase="execution", toml=DEFAULT_TOML, files=None,
                 bind=True, work=True, session=SESSION, issue=7, origin_url=None):
        self.session = session
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate lab "))
        self.main, self.origin, self.base = make_origin_repo(self.tmp, files or DEFAULT_FILES,
                                                             toml)
        if origin_url:
            # remote.origin.url resta l'URL finto; il fetch va al repo nudo (insteadOf)
            git(self.main, "config", "remote.origin.url", origin_url)
            git(self.main, "config", f"url.{self.origin}.insteadOf", origin_url)
        # la chiave del repo è ovunque repo_key(git.origin_url(repo)) (get-url espande insteadOf)
        key_source = core_git.origin_url(self.main)
        self.wt = self.tmp / f"wt {issue}"
        git(self.main, "worktree", "add", "-q", "-b", f"tg/{issue}-demo", str(self.wt))
        self.conn = db.open_db(self.ts.state)
        self.work = None
        self.now = T0 + timedelta(minutes=1)
        if work:
            self.work = phases.create_work(
                self.conn, repo_key=repo_key(key_source), issue=issue, level=level, now=T0,
                session=session if bind else None, branch=f"tg/{issue}-demo",
                worktree=str(self.wt),
                work_base_sha=self.base, gate_mode="protected")
            self.goto(phase)

    def goto(self, phase):
        row = phases.get_work(self.conn, self.work)
        seq = phases.SEQUENCES[row["level"]]
        cur = row["phase"]
        while cur != phase:
            nxt = seq[seq.index(cur) + 1]
            cause = phases._FORWARD_CONDITION.get((cur, nxt), "advance")
            phases.set_phase(self.conn, self.ts.state, self.work, nxt, cause, now=T0)
            cur = nxt

    def hook(self, payload, now=None):
        self.now = now or (self.now + timedelta(seconds=1))
        return runner.run_hook(payload["hook_event_name"], json.dumps(payload),
                               env=self.ts.env(), now=self.now, plugin_root=ROOT)

    def _base(self, name, agent_id, cwd, **kw):
        extra = {"session_id": self.session, "cwd": str(cwd or self.wt)}
        if agent_id:
            extra.update(agent_id=agent_id, agent_type=kw.pop("agent_type",
                                                              "tollgate:implementer"))
        else:
            extra.update(agent_id=DROP, agent_type=DROP)
        extra.update(kw)
        return sample(name, **extra)

    def pre_edit(self, path, *, agent_id=None, tool="Write", content="x", cwd=None, **kw):
        ti = {"file_path": str(path), "content": content} if tool == "Write" else \
            {"file_path": str(path), "old_string": "a", "new_string": "b"}
        return self.hook(self._base(f"PreToolUse-{tool}", agent_id, cwd, tool_name=tool,
                                    tool_input=ti, **kw))

    def post_edit(self, path, *, agent_id=None, tool="Write", cwd=None, **kw):
        ti = {"file_path": str(path), "content": Path(path).read_text()
              if Path(path).exists() else ""}
        return self.hook(self._base(f"PostToolUse-{tool}", agent_id, cwd, tool_name=tool,
                                    tool_input=ti, tool_response={"filePath": str(path)}, **kw))

    def bash(self, command, *, post=False, agent_id=None, cwd=None, response=None, **kw):
        name = "PostToolUse-Bash" if post else "PreToolUse-Bash"
        extra = {"tool_input": {"command": command, "description": "x"}}
        if post:
            extra["tool_response"] = response or {"stdout": "", "stderr": "",
                                                  "interrupted": False}
        return self.hook(self._base(name, agent_id, cwd, **extra, **kw))

    def events(self, type_):
        return [json.loads(r["data"]) for r in self.conn.execute(
            "SELECT data FROM events WHERE type = ? ORDER BY seq", (type_,))]

    def close(self):
        self.conn.close()
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)
