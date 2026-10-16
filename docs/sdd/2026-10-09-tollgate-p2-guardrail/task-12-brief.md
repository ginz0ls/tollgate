### Task 12: Motore degli hook: modello, adattatore, contesto, registro, runner, `tollgate hook`

**Files:**
- Create: `bin/tollgate_hooks/__init__.py`
- Create: `bin/tollgate_hooks/model.py`
- Create: `bin/tollgate_hooks/adapter.py`
- Create: `bin/tollgate_hooks/context.py`
- Create: `bin/tollgate_hooks/registry.py`
- Create: `bin/tollgate_hooks/apply.py`
- Create: `bin/tollgate_hooks/runner.py`
- Create: `bin/tollgate_checks/__init__.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `hook`)
- Create: `tests/hookkit.py`
- Test: `tests/test_hook_engine.py`

**Interfaces:**
- Consumes: tutto `tollgate_core` dei Task 2-3 e 9; `tollgate_analysis.testguard.GuardConfig`, `waivers`, `profiles`.
- Produces (i Task 14-19 li usano così):
  - `model.INPUT_EVENTS`, `model.CONTROL_EVENTS`; `model.Event(kind, hook_event, session, cwd, agent_id, agent_type, tool_name, tool_input, tool_response, raw)`; `model.Decision`; costruttori `model.allow()`, `model.deny(reason, rule="")`, `model.inject(text)`, `model.record(op, **data)`.
  - `adapter.to_event(hook_event: str, raw: dict) -> Event | None`; `adapter.edit_path(event) -> str | None`; `adapter.INJECT_MODE`; `adapter.render(hook_event, deny_text, inject_text) -> tuple[int, str, str]`.
  - `context.ReadDb(conn)` (solo `SELECT`); `context.Ctx` con: `event`, `state`, `db`, `config`, `repo`, `work`, `bound`, `now`, `plugin_root`; metodi `cfg(dotted)`, `component(name)`, `readonly(agent_type)`, `stale_minutes`, `work_for_path(path)`, `rel(path, root)`, `waiver_file(work)`, `approved_waivers(work)`, `scope(work)`, `guard_config(work, files)`, `protected_roots(repo)`, `plugin_bin`.
  - `registry.API = 1`; `registry.Loaded(name, module, check)`; `registry.Broken(name, events, reason)`; `registry.load(package="tollgate_checks") -> tuple[list[Loaded], list[Broken]]`.
  - `apply.OPS` (insieme dei nomi); `apply.apply(conn, state, ctx, decision) -> None`. Operazioni e campi di `data`:
    - `bind {work}`; `act {type, object, target, args, typed_text, work, head_sha}`; `expire_acts {}`;
    - `block {work, type, reason}`; `level {work, level}`; `phase {work, to, cause}`;
    - `plan {work, plan_path, plan_sha, scope, tasks, advance}`; `plan_path {work, plan_path}`;
    - `subagent_start {agent_id, type, work, task, base_sha, fingerprint, take_pending, resume}`;
    - `subagent_name {agent_id, name, work}`; `subagent_report {agent_id, text}`; `subagent_veto {agent_id}`;
    - `subagent_finish {agent_id, state, declared_status, tokens}`; `subagent_interrupt {agent_id}`;
    - `task {work, number, event}`; `task_commit {work, number, sha}`; `skill_used {work, number, skill}`;
    - `commit {work, sha, head}`; `effect_request {key, command, work, sha}`; `effect_execute {key, act_id, work}`;
    - `event {type, data, work}`.
  - `runner.HookResult(exit, stdout, stderr)`; `runner.run_hook(hook_event, stdin_text, *, env=None, now=None, plugin_root=None, checks=None, alarm=False) -> HookResult`; `runner.BUDGET` (limiti di iniezione per evento).
  - Contratto di un modulo di `tollgate_checks`: `CHECK = {"api": 1, "events": [...], "component": str | None, "order": int}` e `decide(event, ctx) -> list[Decision]`.
  - `tests.hookkit`: `SAMPLES`, `sample(name, **campi)`, `DROP`, `SESSION`, `T0`, `DEFAULT_TOML`, `Lab(level=, phase=, toml=, files=, bind=, work=)` con `lab.hook(payload)`, `lab.pre_edit(path, agent_id=None, tool="Write", content="x")`, `lab.post_edit(...)`, `lab.bash(command, post=False, agent_id=None, cwd=None, response=None)`, `lab.events(type_)`, `lab.close()`, e i campi `ts`, `main`, `wt`, `base`, `conn`, `work`.

- [ ] **Step 1: Banco degli hook**

`tests/hookkit.py`:

```python
"""Banco di prova degli hook: input reali di Claude Code (P0) e un repo attivo con un lavoro."""
import copy
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.helpers import ROOT, TempState, git, make_origin_repo
from tollgate_core import db, phases
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
                 bind=True, work=True):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate lab "))
        self.main, self.origin, self.base = make_origin_repo(self.tmp, files or DEFAULT_FILES,
                                                             toml)
        self.wt = self.tmp / "wt 7"
        git(self.main, "worktree", "add", "-q", "-b", "tg/7-demo", str(self.wt))
        self.conn = db.open_db(self.ts.state)
        self.work = None
        self.now = T0 + timedelta(minutes=1)
        if work:
            self.work = phases.create_work(
                self.conn, repo_key=repo_key(str(self.origin)), issue=7, level=level, now=T0,
                session=SESSION if bind else None, branch="tg/7-demo", worktree=str(self.wt),
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
        extra = {"session_id": SESSION, "cwd": str(cwd or self.wt)}
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
```

- [ ] **Step 2: Test del motore**

`tests/test_hook_engine.py`:

```python
import json
import multiprocessing
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.helpers import ROOT, TempState
from tollgate_hooks import adapter, registry, runner
from tollgate_hooks.model import Event, deny, inject, record

FAKE = {
    "uno.py": '''
CHECK = {"api": 1, "events": ["pre_bash", "session_start"], "component": None, "order": 10}
def decide(event, ctx):
    from tollgate_hooks.model import deny, inject, record
    cmd = (event.tool_input or {}).get("command", "")
    if "vietato" in cmd:
        return [deny("comando vietato", rule="uno"), record("event", type="off", data={})]
    if event.kind == "session_start":
        return [inject("riga\\n" * 30)]
    return []
''',
    "due.py": '''
CHECK = {"api": 2, "events": ["pre_edit"], "component": None, "order": 20}
def decide(event, ctx):
    return []
''',
    "tre.py": '''
CHECK = {"api": 1, "events": ["pre_bash"], "component": "scope_check", "order": 5}
def decide(event, ctx):
    from tollgate_hooks.model import deny
    if "tre" in (event.tool_input or {}).get("command", ""):
        return [deny("controllo tre", rule="tre")]
    return []
''',
    "lento.py": '''
CHECK = {"api": 1, "events": ["pre_mcp"], "component": None, "order": 1}
def decide(event, ctx):
    import time
    time.sleep(5)
    return []
''',
}


def fake_checks(tmp: Path):
    pkg = tmp / "finti_checks"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    for name, body in FAKE.items():
        (pkg / name).write_text(textwrap.dedent(body))
    sys.path.insert(0, str(tmp))
    try:
        return registry.load("finti_checks")
    finally:
        sys.path.remove(str(tmp))


class AdapterTest(unittest.TestCase):
    def test_mapping(self):
        cases = [("SessionStart-none", "session_start"), ("PreToolUse-Bash", "pre_bash"),
                 ("PostToolUse-Bash", "post_bash"), ("PreToolUse-Agent", "pre_agent"),
                 ("PostToolUse-Agent", "post_agent"), ("PreToolUse-SendMessage",
                                                       "pre_send_message"),
                 ("SubagentStart-none", "subagent_start"), ("SubagentStop-none", "subagent_stop"),
                 ("PostToolUse-SubagentHandback", "subagent_handback"),
                 ("UserPromptExpansion-none", "prompt_expansion"),
                 ("PreToolUse-Read", None), ("PreToolUse-ToolSearch", None)]
        for name, kind in cases:
            s = sample(name)
            ev = adapter.to_event(s["hook_event_name"], s)
            with self.subTest(name=name):
                self.assertEqual(ev.kind if ev else None, kind)
        mcp = sample("PreToolUse-Bash", tool_name="mcp__srv__scrivi", tool_input={"a": 1})
        self.assertEqual(adapter.to_event("PreToolUse", mcp).kind, "pre_mcp")
        w = sample("PreToolUse-Write", tool_name="Write", tool_input={"file_path": "/x/a.py"})
        self.assertEqual(adapter.edit_path(adapter.to_event("PreToolUse", w)), "/x/a.py")
        nb = sample("PreToolUse-Bash", tool_name="NotebookEdit",
                    tool_input={"notebook_path": "/x/n.ipynb"})
        self.assertEqual(adapter.edit_path(adapter.to_event("PreToolUse", nb)), "/x/n.ipynb")

    def test_render(self):
        self.assertEqual(adapter.render("PreToolUse", "no", None)[:1], (2,))
        code, out, _ = adapter.render("SessionStart", None, "ciao")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["hookSpecificOutput"],
                         {"hookEventName": "SessionStart", "additionalContext": "ciao"})
        self.assertEqual(adapter.render("PostToolUse", None, None), (0, "", ""))


class RunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="tollgate-finti-"))
        cls.checks = fake_checks(cls.tmp)

    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def run_with(self, payload, **kw):
        return runner.run_hook(payload["hook_event_name"], json.dumps(payload),
                               env=self.lab.ts.env(), now=self.lab.now, plugin_root=ROOT,
                               checks=self.checks, **kw)

    def test_deny_records_veto_and_records_after_deny(self):
        r = self.run_with(self.lab._base("PreToolUse-Bash", None, None,
                                         tool_input={"command": "echo vietato"}))
        self.assertEqual(r.exit, 2)
        self.assertIn("comando vietato", r.stderr)
        self.assertEqual(self.lab.events("veto"), [{"event": "pre_bash", "rule": "uno",
                                                    "reason": "comando vietato"}])
        self.assertEqual(len(self.lab.events("off")), 1)

    def test_api_mismatch_denies_its_events(self):
        r = self.run_with(self.lab._base("PreToolUse-Write", None, None, tool_name="Write",
                                         tool_input={"file_path": str(self.lab.wt / "x")}))
        self.assertEqual(r.exit, 2)
        self.assertIn("due", r.stderr)

    def test_component_off_skips_module(self):
        toml = DEFAULT_TOML + "[components]\nscope_check = false\n"
        lab = Lab(toml=toml)
        try:
            p = lab._base("PreToolUse-Bash", None, None, tool_input={"command": "echo tre"})
            r = runner.run_hook("PreToolUse", json.dumps(p), env=lab.ts.env(), now=lab.now,
                                plugin_root=ROOT, checks=self.checks)
            self.assertEqual(r.exit, 0)
        finally:
            lab.close()
        p = self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "echo tre"})
        self.assertEqual(self.run_with(p).exit, 2)

    def test_inject_budget_session_start(self):
        r = self.run_with(self.lab._base("SessionStart-none", None, None))
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(ctx.splitlines()), 10)
        self.assertLessEqual(len(ctx), 1500)

    def test_malformed_input_control_and_info(self):
        r = runner.run_hook("PreToolUse", "{rotto", env=self.lab.ts.env(), plugin_root=ROOT)
        self.assertEqual(r.exit, 2)
        self.assertIn("touch", r.stderr)
        r = runner.run_hook("PostToolUse", "{rotto", env=self.lab.ts.env(), plugin_root=ROOT)
        self.assertEqual(r.exit, 0)

    def test_malformed_input_missing_fields(self):
        p = self.lab._base("PreToolUse-Write", None, None, tool_name="Write", tool_input={})
        self.assertIn(self.run_with(p).exit, (0, 2))
        p = self.lab._base("PreToolUse-Bash", None, "/non/esiste",
                           tool_input={"command": "ls"})
        self.assertEqual(self.run_with(p).exit, 0)

    def test_inactive_repo_and_off(self):
        ts = TempState()
        try:
            p = sample("PreToolUse-Bash", cwd=str(ts.dir), tool_input={"command": "vietato"})
            self.assertEqual(runner.run_hook("PreToolUse", json.dumps(p), env=ts.env(),
                                             plugin_root=ROOT, checks=self.checks).exit, 0)
        finally:
            ts.cleanup()
        (self.lab.ts.dir / "OFF").write_text("")
        before = self.lab.events("veto")
        r = self.run_with(self.lab._base("PreToolUse-Bash", None, None,
                                         tool_input={"command": "echo vietato"}))
        self.assertEqual((r.exit, self.lab.events("veto")), (0, before))

    def test_off_does_not_open_db(self):
        ts = TempState()
        try:
            (ts.dir / "OFF").write_text("")
            p = sample("PreToolUse-Bash", cwd=str(self.lab.wt), tool_input={"command": "x"})
            runner.run_hook("PreToolUse", json.dumps(p), env=ts.env(), plugin_root=ROOT)
            self.assertFalse((ts.dir / "tollgate.db").exists())
        finally:
            ts.cleanup()

    def test_corrupt_db(self):
        self.lab.conn.close()
        db_path = self.lab.ts.dir / "tollgate.db"
        for suffix in ("-wal", "-shm"):
            Path(str(db_path) + suffix).unlink(missing_ok=True)
        db_path.write_bytes(b"non sono un db" * 100)
        p = self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "ls"})
        r = self.run_with(p)
        self.assertEqual(r.exit, 2)
        self.assertIn("db restore", r.stderr)
        p = self.lab._base("PostToolUse-Bash", None, None, tool_input={"command": "ls"},
                           tool_response={})
        self.assertEqual(self.run_with(p).exit, 0)
        import sqlite3
        self.lab.conn = sqlite3.connect(":memory:")  # il DB guasto non si riapre in tearDown

    def test_internal_timeout(self):
        lab = Lab(toml=DEFAULT_TOML + "[hooks]\ntimeout_s = 1\n")
        try:
            p = lab._base("PreToolUse-Bash", None, None, tool_name="mcp__x__y", tool_input={})
            t0 = time.monotonic()
            r = runner.run_hook("PreToolUse", json.dumps(p), env=lab.ts.env(), now=lab.now,
                                plugin_root=ROOT, checks=self.checks, alarm=True)
            self.assertEqual(r.exit, 2)
            self.assertLess(time.monotonic() - t0, 4)
        finally:
            lab.close()

    def test_session_seen_and_offlog_import(self):
        (self.lab.ts.dir / "off.log").write_text("2026-10-09T08:00:00.000000Z off\n")
        self.run_with(self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "ls"}))
        seen = self.lab.conn.execute("SELECT session FROM session_seen").fetchall()
        self.assertEqual([r[0] for r in seen], [SESSION])
        self.assertEqual(len(self.lab.events("off")), 1)


def _worker(env, payload, q):
    r = runner.run_hook("PreToolUse", payload, env=env, plugin_root=ROOT)
    q.put(r.exit)


class ConcurrencyTest(unittest.TestCase):
    def test_concurrent_hooks(self):
        lab = Lab()
        try:
            payload = json.dumps(lab._base("PreToolUse-Bash", None, None,
                                           tool_input={"command": "ls"}))
            q = multiprocessing.get_context("spawn").Queue()
            procs = [multiprocessing.get_context("spawn").Process(
                target=_worker, args=(lab.ts.env(), payload, q)) for _ in range(4)]
            for p in procs:
                p.start()
            for p in procs:
                p.join(30)
            self.assertEqual(sorted(q.get(timeout=5) for _ in procs), [0, 0, 0, 0])
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_hook_engine -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_hooks'`.

- [ ] **Step 4: `model.py` e `adapter.py`**

`bin/tollgate_hooks/__init__.py`:

```python
"""Motore degli hook di tollgate: adattatore per Claude Code, contesto, registro, runner."""
```

`bin/tollgate_checks/__init__.py`:

```python
"""Registro dei controlli (spec 3.2): un modulo per controllo, con CHECK e decide(event, ctx)."""
```

`bin/tollgate_hooks/model.py`:

```python
"""Eventi d'ingresso e decisioni (spec 3.2, revisione 21)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

INPUT_EVENTS = ("session_start", "prompt_expansion", "pre_edit", "post_edit", "pre_bash",
                "post_bash", "pre_agent", "post_agent", "pre_send_message", "pre_mcp",
                "subagent_start", "subagent_stop", "subagent_handback", "post_skill")
CONTROL_EVENTS = frozenset({"pre_edit", "pre_bash", "pre_agent", "pre_send_message", "pre_mcp"})


@dataclass(frozen=True)
class Event:
    kind: str
    hook_event: str
    session: str
    cwd: Path
    agent_id: str | None
    agent_type: str | None
    tool_name: str | None
    tool_input: dict
    tool_response: dict | None
    raw: dict


@dataclass(frozen=True)
class Decision:
    kind: str                      # allow | deny | inject | record
    text: str = ""
    rule: str = ""
    op: str = ""
    data: dict = field(default_factory=dict)


def allow() -> Decision:
    return Decision("allow")


def deny(reason: str, rule: str = "") -> Decision:
    return Decision("deny", text=reason, rule=rule)


def inject(text: str) -> Decision:
    return Decision("inject", text=text)


def record(op: str, **data) -> Decision:
    return Decision("record", op=op, data=data)
```

`bin/tollgate_hooks/adapter.py`:

```python
"""Adattatore per Claude Code (spec 3.2): input degli hook → Event; esito → risposta."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Event

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_PRE = {"Bash": "pre_bash", "Agent": "pre_agent", "SendMessage": "pre_send_message"}
_POST = {"Bash": "post_bash", "Agent": "post_agent", "Skill": "post_skill",
         "SubagentHandback": "subagent_handback"}
_PLAIN = {"SessionStart": "session_start", "UserPromptExpansion": "prompt_expansion",
          "SubagentStart": "subagent_start", "SubagentStop": "subagent_stop"}
# Come arriva un'iniezione al modello, per evento (decisione 3; esito di D2 nel Task 1).
# "context": hookSpecificOutput.additionalContext; "system": systemMessage; "stderr": solo stderr.
INJECT_MODE = {"SessionStart": "context", "UserPromptExpansion": "context",
               "PreToolUse": "context", "PostToolUse": "context", "SubagentStart": "context",
               "SubagentStop": "stderr"}


def _kind(hook_event: str, tool: str | None) -> str | None:
    if hook_event in _PLAIN:
        return _PLAIN[hook_event]
    if hook_event == "PreToolUse":
        if tool in EDIT_TOOLS:
            return "pre_edit"
        if tool and tool.startswith("mcp__"):
            return "pre_mcp"
        return _PRE.get(tool)
    if hook_event == "PostToolUse":
        if tool in EDIT_TOOLS:
            return "post_edit"
        return _POST.get(tool)
    return None


def to_event(hook_event: str, raw: dict) -> Event | None:
    if not isinstance(raw, dict):
        raise ValueError("input dell'hook non è un oggetto JSON")
    tool = raw.get("tool_name") if isinstance(raw.get("tool_name"), str) else None
    kind = _kind(hook_event, tool)
    if kind is None:
        return None
    ti = raw.get("tool_input")
    tr = raw.get("tool_response")
    return Event(kind=kind, hook_event=hook_event, session=str(raw.get("session_id") or ""),
                 cwd=Path(str(raw.get("cwd") or ".")), agent_id=raw.get("agent_id") or None,
                 agent_type=raw.get("agent_type") if raw.get("agent_type") is not None else None,
                 tool_name=tool, tool_input=ti if isinstance(ti, dict) else {},
                 tool_response=tr if isinstance(tr, dict) else None, raw=raw)


def edit_path(event: Event) -> str | None:
    p = event.tool_input.get("file_path") or event.tool_input.get("notebook_path")
    return p if isinstance(p, str) and p else None


def render(hook_event: str, deny_text: str | None, inject_text: str | None):
    """Solo l'uscita 2 blocca (7.1). Mai permissionDecision allow (decisione 3)."""
    if deny_text:
        return 2, "", f"tollgate: {deny_text}\n"
    if inject_text:
        mode = INJECT_MODE.get(hook_event, "context")
        if mode == "context":
            out = {"hookSpecificOutput": {"hookEventName": hook_event,
                                          "additionalContext": inject_text}}
            return 0, json.dumps(out, ensure_ascii=False), ""
        if mode == "system":
            return 0, json.dumps({"systemMessage": inject_text}, ensure_ascii=False), ""
        return 0, "", inject_text + "\n"
    return 0, "", ""
```

- [ ] **Step 5: `context.py`**

```python
"""Contesto in sola lettura dei controlli (spec 3.2)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from tollgate_analysis import profiles as prof, waivers
from tollgate_analysis.testguard import DEFAULT_TEST_GLOBS, GuardConfig

from tollgate_core import git, scope, sessions
from tollgate_core.config import Config
from tollgate_core.paths import State

from .model import Event

_AREA_READONLY = re.compile(r"^[^:]+:(reviewer|final)-")


class ReadDb:
    """Il DB visto dai controlli: solo SELECT (un modulo non scrive mai, spec 3.2)."""
    in_transaction = False

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=()):
        if not sql.lstrip().upper().startswith("SELECT"):
            raise PermissionError("il contesto dei controlli è in sola lettura")
        return self._conn.execute(sql, params)


@dataclass
class Ctx:
    event: Event
    state: State
    db: ReadDb
    config: Config
    repo: Path | None
    work: object | None
    bound: bool
    now: object
    plugin_root: Path

    def cfg(self, dotted: str):
        return self.config.get(dotted)

    def component(self, name: str) -> bool:
        return bool(self.config.data["components"].get(name, True))

    def readonly(self, agent_type: str | None) -> bool:
        if not agent_type:
            return False
        return agent_type in self.cfg("review.readonly_agents") or bool(
            _AREA_READONLY.match(agent_type))

    @property
    def stale_minutes(self) -> int:
        return self.cfg("review.stale_minutes")

    @property
    def plugin_bin(self) -> Path:
        return self.plugin_root / "bin" / "tollgate"

    def work_for_path(self, path):
        return sessions.work_for_path(self.db, path)

    @staticmethod
    def rel(path, root) -> str | None:
        try:
            return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return None

    def waiver_file(self, work):
        if work is None or not work["worktree"]:
            return None
        p = Path(work["worktree"]) / waivers.path_for(work["issue"])
        try:
            return waivers.parse(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def approved_waivers(self, work) -> set[str]:
        """Decisione 10: un approve waiver vale in ogni stato dell'atto."""
        if work is None:
            return set()
        return {r[0] for r in self.db.execute(
            "SELECT target FROM acts WHERE type = 'approve' AND object = 'waiver' "
            "AND work = ? AND target IS NOT NULL", (work["id"],))}

    def scope(self, work) -> set[str]:
        return scope.paths(self.db, work["id"]) if work is not None else set()

    def guard_config(self, work, files) -> GuardConfig:
        tg = self.cfg("test_guard")
        profs = self.config.profiles
        active = prof.active_profiles(files, profs, self.cfg("profiles.active"))
        extra = lambda k: [x for n in active for x in profs[n].get(k, [])]  # noqa: E731
        commands = " ".join(str(v) for v in self.cfg("commands").values())
        return GuardConfig(
            test_globs=list(DEFAULT_TEST_GLOBS) + tg["test_globs"] + extra("test_globs"),
            fixture_globs=tg["fixture_globs"], ci_globs=tg["ci_globs"],
            verification_globs=tg["verification_globs"],
            verification_watch=tg["verification_watch"],
            skip_markers=tg["skip_markers"] + extra("skip_markers"),
            assert_markers=tg["assert_markers"] + extra("assert_markers"),
            js_form="jest" if "jest" in commands else "vitest")

    def protected_roots(self, repo) -> list[Path]:
        home = Path(os.path.expanduser("~"))
        roots = [self.state.root.resolve(), (home / ".claude" / "plugins").resolve(),
                 home / ".claude" / "settings.json", home / ".claude" / "settings.local.json"]
        if repo is not None:
            try:
                common = git.common_dir(repo)
                roots += [common / "hooks", common / "config"]
            except git.GitError:
                pass
        return roots
```

- [ ] **Step 6: `registry.py`**

```python
"""Caricamento dei moduli del registro (spec 3.2): ordine, api, componenti."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass

from .model import INPUT_EVENTS

API = 1


@dataclass(frozen=True)
class Loaded:
    name: str
    module: object
    check: dict


@dataclass(frozen=True)
class Broken:
    name: str
    events: tuple | None      # None: eventi ignoti, vale per ogni evento di controllo
    reason: str


def _validate(check) -> str | None:
    if not isinstance(check, dict):
        return "CHECK mancante o non è un dizionario"
    if check.get("api") != API:
        return f"api {check.get('api')!r}, questa versione di tollgate carica api {API}"
    events = check.get("events")
    if not isinstance(events, list) or not events or not set(events) <= set(INPUT_EVENTS):
        return f"eventi non validi: {events!r}"
    if not isinstance(check.get("order"), int):
        return "order mancante"
    comp = check.get("component")
    if comp is not None and not isinstance(comp, str):
        return "component non valido"
    return None


def load(package: str = "tollgate_checks"):
    pkg = importlib.import_module(package)
    loaded, broken = [], []
    for info in pkgutil.iter_modules(pkg.__path__):
        if info.name.startswith("_"):
            continue
        name = f"{package}.{info.name}"
        try:
            mod = importlib.import_module(name)
        except Exception as e:  # un controllo che manca non deve passare in silenzio
            broken.append(Broken(info.name, None, f"import fallito: {e}"))
            continue
        check = getattr(mod, "CHECK", None)
        reason = _validate(check)
        if reason is None and not callable(getattr(mod, "decide", None)):
            reason = "decide mancante"
        if reason is not None:
            events = tuple(check["events"]) if isinstance(check, dict) and isinstance(
                check.get("events"), list) else None
            broken.append(Broken(info.name, events, reason))
            continue
        loaded.append(Loaded(info.name, mod, check))
    loaded.sort(key=lambda m: (m.check["order"], m.name))
    return loaded, broken
```

- [ ] **Step 7: `apply.py`**

```python
"""Operazioni `record` dei controlli (decisione 6): ognuna scrive con tollgate_core."""
from __future__ import annotations

import getpass

from tollgate_core import (acts, effects, events, phases, scope, sessions, subagents, tasks)


def _actor() -> str | None:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return None


def _bind(conn, state, ctx, d):
    phases.bind_session(conn, d["work"], ctx.event.session, now=ctx.now)
    sessions.mark_bound(state, ctx.event.session)


def _act(conn, state, ctx, d):
    acts.record_act(conn, type_=d["type"], object_=d.get("object"), target=d.get("target"),
                    args=d.get("args"), typed_text=d.get("typed_text", ""), actor=_actor(),
                    session=ctx.event.session, work=d.get("work"), head_sha=d.get("head_sha"),
                    now=ctx.now, ttl_minutes=ctx.cfg("acts.ttl_minutes"))


def _subagent_start(conn, state, ctx, d):
    task = d.get("task")
    if d.get("take_pending") and d.get("work") is not None:
        task = tasks.take_pending(conn, d["work"], agent_type=d["type"],
                                  resume=bool(d.get("resume"))) or task
    subagents.start(conn, agent_id=d["agent_id"], type_=d["type"], session=ctx.event.session,
                    work=d.get("work"), task=task, base_sha=d.get("base_sha"),
                    fingerprint=d.get("fingerprint"), now=ctx.now)


def _commit(conn, state, ctx, d):
    events.record_event(conn, "commit", {"sha": d["sha"]}, now=ctx.now,
                        session=ctx.event.session, work=d["work"])
    acts.invalidate_finish(conn, d["work"], d.get("head") or d["sha"], now=ctx.now,
                           session=ctx.event.session)


def _effect_execute(conn, state, ctx, d):
    act = acts.find_usable(conn, type_="approve", object_="effect",
                           target=effects.effect_id(d["key"]), work=d.get("work"),
                           session=ctx.event.session, now=ctx.now)
    if act is None:
        raise acts.ActError("atto approve effect non più valido")
    acts.consume(conn, act["act_id"], type_="approve", object_="effect",
                 target=effects.effect_id(d["key"]), now=ctx.now, work=d.get("work"),
                 session=ctx.event.session)
    effects.mark_executed(conn, key=d["key"], act_id=act["act_id"], now=ctx.now,
                          session=ctx.event.session)


_OPS = {
    "event": lambda c, s, x, d: events.record_event(c, d["type"], d.get("data"), now=x.now,
                                                    session=x.event.session, work=d.get("work")),
    "bind": _bind,
    "act": _act,
    "expire_acts": lambda c, s, x, d: acts.expire_stale(c, now=x.now, session=x.event.session),
    "block": lambda c, s, x, d: phases.open_block(c, s, d["work"], d["type"], d["reason"],
                                                  now=x.now, session=x.event.session),
    "level": lambda c, s, x, d: phases.set_level(c, d["work"], d["level"], now=x.now,
                                                 session=x.event.session),
    "phase": lambda c, s, x, d: phases.set_phase(c, s, d["work"], d["to"], d["cause"],
                                                 now=x.now, session=x.event.session),
    "plan": lambda c, s, x, d: scope.register_plan(
        c, s, d["work"], plan_path=d["plan_path"], plan_sha=d["plan_sha"],
        scope_paths=d["scope"], plan_tasks=[tuple(t) for t in d["tasks"]],
        advance=d["advance"], now=x.now, session=x.event.session),
    "plan_path": lambda c, s, x, d: scope.set_plan_path(c, d["work"], d["plan_path"], now=x.now),
    "subagent_start": _subagent_start,
    "subagent_name": lambda c, s, x, d: subagents.set_name(c, d["agent_id"], d["name"],
                                                           session=x.event.session,
                                                           work=d.get("work"), now=x.now),
    "subagent_report": lambda c, s, x, d: subagents.set_report(c, d["agent_id"], d["text"]),
    "subagent_veto": lambda c, s, x, d: subagents.add_veto(c, d["agent_id"]),
    "subagent_finish": lambda c, s, x, d: subagents.finish(
        c, d["agent_id"], state=d["state"], declared_status=d.get("declared_status"),
        tokens=d.get("tokens"), now=x.now, session=x.event.session),
    "subagent_interrupt": lambda c, s, x, d: subagents.interrupt(c, d["agent_id"], now=x.now,
                                                                 session=x.event.session),
    "task": lambda c, s, x, d: tasks.task_event(c, d["work"], d["number"], d["event"],
                                                now=x.now, session=x.event.session),
    "task_commit": lambda c, s, x, d: tasks.add_commit(c, d["work"], d["number"], d["sha"]),
    "skill_used": lambda c, s, x, d: tasks.add_skill_used(c, d["work"], d["number"], d["skill"]),
    "commit": _commit,
    "effect_request": lambda c, s, x, d: effects.request(
        c, key=d["key"], command=d["command"], work=d.get("work"), sha=d.get("sha"), now=x.now,
        session=x.event.session),
    "effect_execute": _effect_execute,
}
OPS = frozenset(_OPS)


def apply(conn, state, ctx, decision) -> None:
    fn = _OPS.get(decision.op)
    if fn is None:
        raise ValueError(f"operazione record sconosciuta: {decision.op}")
    fn(conn, state, ctx, decision.data)
```

- [ ] **Step 8: `runner.py`**

```python
"""Il percorso di un hook (spec 7.1 dal punto 5, 3.2, 12.1)."""
from __future__ import annotations

import json
import os
import signal
import sqlite3
import traceback
from dataclasses import dataclass
from pathlib import Path

from tollgate_core import clock, db, git, offlog, sessions, subagents
from tollgate_core.acts import ActError
from tollgate_core.config import ConfigError, ConfigNotFound, load_config
from tollgate_core.phases import TransitionError
from tollgate_core.tasks import TaskTransitionError
from tollgate_core.events import record_event
from tollgate_core.paths import resolve_state

from . import adapter, apply as applier, registry
from .context import Ctx, ReadDb
from .model import CONTROL_EVENTS

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
BUDGET = {"session_start": (10, 1500), "subagent_start": (None, 2000)}
DEFAULT_BUDGET = (None, 1500)
_CONTROL_HOOKS = {"PreToolUse"}


@dataclass(frozen=True)
class HookResult:
    exit: int
    stdout: str = ""
    stderr: str = ""


class _Timeout(Exception):
    pass


def _footer(state_root: Path) -> str:
    return (f"Programma: {db.BIN_PATH}. Per spegnere tollgate: /tollgate:off, "
            f"oppure dal terminale: touch {state_root / 'OFF'}")


def _fail(control: bool, msg: str, state_root: Path) -> HookResult:
    text = f"tollgate: {msg}\n{_footer(state_root)}\n"
    if control:
        return HookResult(2, "", text + "Azione negata perché il controllo non è riuscito.\n")
    return HookResult(0, "", text + "Avviso: controllo informativo saltato.\n")


def _off_active(state_root: Path, now) -> bool:
    off = state_root / "OFF"
    if not off.exists():
        return False
    try:
        for line in off.read_text().splitlines():
            if line.startswith("until="):
                return now.timestamp() < int(line[6:])
    except (OSError, ValueError):
        pass
    return True


def _budget(kind: str, text: str) -> str:
    max_lines, max_chars = BUDGET.get(kind, DEFAULT_BUDGET)
    lines = text.splitlines()
    if max_lines is not None and len(lines) > max_lines:
        text = "\n".join(lines[:max_lines - 1] + ["…"])
    if len(text) > max_chars:
        text = text[:max_chars - 1] + "…"
    return text


def _set_alarm(seconds: int) -> None:
    def handler(signum, frame):
        raise _Timeout()
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(max(1, int(seconds)))


def _corrupt(e: BaseException) -> bool:
    code = getattr(e, "sqlite_errorcode", None)
    return code is not None and (code & 0xFF) in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB)


def run_hook(hook_event: str, stdin_text: str, *, env=None, now=None, plugin_root=None,
             checks=None, alarm: bool = False) -> HookResult:
    env = os.environ if env is None else env
    state = resolve_state(env)
    control = hook_event in _CONTROL_HOOKS
    now = now or clock.now()
    if alarm:
        _set_alarm(20)
    conn = None
    try:
        try:
            raw = json.loads(stdin_text)
            event = adapter.to_event(hook_event, raw)
        except (ValueError, TypeError) as e:
            return _fail(control, f"input dell'hook non valido ({e})", state.root)
        if event is None or _off_active(state.root, now):
            return HookResult(0)
        control = event.kind in CONTROL_EVENTS
        cwd_ok = event.cwd.is_dir()
        root = git.toplevel(event.cwd) if cwd_ok else None
        marker = state.root / sessions.BOUND_DIR / event.session
        if root is None and not marker.exists():
            return HookResult(0)
        conn = db.open_db(state)
        offlog.import_log(conn, state)
        if event.session:
            sessions.touch(conn, event.session, now=now)
        if event.agent_id and subagents.get(conn, event.agent_id) is not None:
            subagents.touch(conn, event.agent_id, now=now)
        bound = sessions.bound_work(conn, event.session) if event.session else None
        work = bound or (sessions.work_for_path(conn, event.cwd) if cwd_ok else None)
        if work is not None and work["work_base_sha"] and work["worktree"] \
                and Path(work["worktree"]).is_dir():
            cfg_repo, ref = Path(work["worktree"]), work["work_base_sha"]
        elif root is not None:
            cfg_repo, ref = root, git.default_ref(root)
        else:
            return HookResult(0)
        if ref is None:
            return HookResult(0, "", "tollgate: nessun riferimento remoto (origin/HEAD, main, "
                                     "master): repo trattato come non attivo\n")
        try:
            config = load_config(state, cfg_repo, ref, env=env)
        except ConfigNotFound:
            return HookResult(0)
        except ConfigError as e:
            return _fail(control, f"tollgate.toml non valido: {e}", state.root)
        if alarm:
            _set_alarm(config.get("hooks.timeout_s"))
        ctx = Ctx(event, state, ReadDb(conn), config, root, work,
                  bound is not None and work is not None and bound["id"] == work["id"], now,
                  Path(plugin_root) if plugin_root else PLUGIN_ROOT)
        loaded, broken = checks if checks is not None else registry.load()
        denial, rule, injects, records = None, "", [], []
        for b in broken:
            if (b.events is None and control) or (b.events and event.kind in b.events):
                if denial is None:
                    denial, rule = f"controllo «{b.name}» non caricato: {b.reason}", b.name
        for m in loaded:
            if event.kind not in m.check["events"]:
                continue
            comp = m.check.get("component")
            if comp and not ctx.component(comp):
                continue
            try:
                decisions = m.module.decide(event, ctx) or []
            except _Timeout:
                raise
            except Exception as e:
                if control and denial is None:
                    denial, rule = f"controllo «{m.name}» in errore: {e}", m.name
                elif not control:
                    injects.append(f"(tollgate: controllo «{m.name}» in errore: {e})")
                continue
            for d in decisions:
                if d.kind == "deny" and denial is None:
                    denial, rule = d.text, d.rule or m.name
                elif d.kind == "inject" and d.text:
                    injects.append(d.text)
                elif d.kind == "record":
                    records.append(d)
        for d in records:
            try:
                applier.apply(conn, state, ctx, d)
            except (TransitionError, TaskTransitionError, ActError, ValueError) as e:
                # una registrazione non più possibile (fase cambiata, atto scaduto) non
                # annulla le altre né il veto: si riporta e si va avanti
                injects.append(f"(tollgate: registrazione «{d.op}» non applicata: {e})")
        if denial:
            record_event(conn, "veto", {"event": event.kind, "rule": rule, "reason": denial},
                         now=now, session=event.session or None,
                         work=work["id"] if work is not None else None)
        inject_text = _budget(event.kind, "\n".join(injects)) if injects else None
        code, out, err = adapter.render(hook_event, denial, inject_text)
        return HookResult(code, out, err)
    except _Timeout:
        return _fail(control, "controllo oltre la scadenza ([hooks] timeout_s)", state.root)
    except db.DbCorrupt as e:
        return _fail(control, str(e), state.root)
    except db.DbError as e:
        return _fail(control, str(e), state.root)
    except sqlite3.DatabaseError as e:
        if _corrupt(e):
            return _fail(control, f"DB di tollgate guasto: {e}. Ripristino dal terminale: "
                                  f"{db.restore_hint()}", state.root)
        return _fail(control, f"errore del DB: {e}", state.root)
    except Exception as e:
        tb = traceback.format_exc(limit=3)
        return _fail(control, f"errore interno: {e}\n{tb}", state.root)
    finally:
        if alarm:
            signal.alarm(0)
        if conn is not None:
            conn.close()
```

- [ ] **Step 9: Sottocomando `hook`**

In `build_parser` di `bin/tollgate_core/cli.py`:

```python
    hp = sub.add_parser("hook", help="solo per hooks/run: adattatore per Claude Code")
    hp.add_argument("event", metavar="evento")
```

In `main`, subito dopo `if args.cmd is None:` e prima di `state = resolve_state()`:

```python
    if args.cmd == "hook":
        from tollgate_hooks.runner import run_hook
        r = run_hook(args.event, sys.stdin.read(), alarm=True)
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        return r.exit
```

- [ ] **Step 10: Verificare che passino**

Run: `tests/run`
Expected: OK. Se `test_concurrent_hooks` dà `database is locked`, la causa è nel runner (transazioni lunghe), non nel test: le scritture devono restare brevi, una per operazione.

- [ ] **Step 11: Commit**

```bash
git add bin/tollgate_hooks bin/tollgate_checks/__init__.py bin/tollgate_core/cli.py tests/hookkit.py tests/test_hook_engine.py
git commit -m "tollgate P2: motore degli hook (adattatore, contesto, registro, runner) e tollgate hook"
```

---
