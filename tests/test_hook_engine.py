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
    "sub.py": '''
CHECK = {"api": 1, "events": ["subagent_stop", "subagent_handback", "prompt_submit"],
         "component": None, "order": 1}
def decide(event, ctx):
    from tollgate_hooks.model import deny, inject
    out = [inject("testo iniettato")]
    if event.kind == "prompt_submit":
        out.append(deny("non deve bloccare"))
    return out
''',
    "dberr.py": '''
import sqlite3
CHECK = {"api": 1, "events": ["pre_send_message", "post_skill"], "component": None, "order": 1}
def decide(event, ctx):
    raise sqlite3.DatabaseError("pagina illeggibile")
''',
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
                 ("UserPromptSubmit-none", "prompt_submit"),
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
        for ev in ("SessionStart", "UserPromptExpansion", "UserPromptSubmit", "PreToolUse",
                   "PostToolUse", "SubagentStart"):
            with self.subTest(ev=ev):
                self.assertEqual(adapter.INJECT_MODE[ev], "context")
        self.assertEqual(adapter.render("SubagentStop", None, "x"), (0, "", ""))
        self.assertEqual(adapter.render("SubagentStop", "no", None)[:1], (2,))


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
        self.assertEqual(self.run_with(p).exit, 2)
        r = runner.run_hook("PreToolUse", json.dumps(p), env=self.lab.ts.env(), now=self.lab.now,
                            plugin_root=ROOT, checks=([], []))
        self.assertEqual(r.exit, 2)
        self.assertIn("file_path", r.stderr)
        self.assertIn("touch", r.stderr)
        p = self.lab._base("PostToolUse-Write", None, None, tool_name="Write", tool_input={},
                           tool_response={})
        self.assertEqual(self.run_with(p).exit, 0)
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

    def test_database_error_during_operations(self):
        p = self.lab._base("PreToolUse-Bash", None, None, tool_name="SendMessage",
                           tool_input={"to": "x", "message": "y"})
        r = self.run_with(p)
        self.assertEqual(r.exit, 2)
        self.assertIn("db restore", r.stderr)
        self.assertIn("touch", r.stderr)
        p = self.lab._base("PostToolUse-Bash", None, None, tool_name="Skill",
                           tool_input={"skill": "x"}, tool_response={})
        r = self.run_with(p)
        self.assertEqual(r.exit, 0)
        self.assertIn("db restore", r.stderr)

    def test_prompt_submit_never_blocks(self):
        r = self.run_with(self.lab._base("UserPromptSubmit-none", None, None, prompt="ciao"))
        self.assertEqual((r.exit, r.stderr), (0, ""))
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"],
                         {"hookEventName": "UserPromptSubmit",
                          "additionalContext": "testo iniettato"})
        self.assertEqual(self.lab.events("veto"), [])
        r = runner.run_hook("UserPromptSubmit", "{rotto", env=self.lab.ts.env(), plugin_root=ROOT)
        self.assertEqual(r.exit, 0)

    def test_inject_on_subagent_stop_and_handback_goes_to_log(self):
        for name in ("SubagentStop-none", "PostToolUse-SubagentHandback"):
            with self.subTest(name=name):
                r = self.run_with(self.lab._base(name, None, None))
                self.assertEqual((r.exit, r.stdout, r.stderr), (0, "", ""))
        log = (self.lab.ts.dir / runner.HOOKS_LOG).read_text()
        self.assertIn("subagent_stop: testo iniettato", log)
        self.assertIn("subagent_handback: testo iniettato", log)

    def test_empty_session_ignores_bound_marker(self):
        (self.lab.ts.dir / "bound").mkdir()
        p = self.lab._base("PreToolUse-Bash", None, "/non/esiste", session_id="",
                           tool_input={"command": "echo vietato"})
        r = self.run_with(p)
        self.assertEqual(r.exit, 0)
        self.assertEqual(self.lab.events("veto"), [])
        (self.lab.ts.dir / "bound" / SESSION).touch()
        p = self.lab._base("PreToolUse-Bash", None, "/non/esiste",
                           tool_input={"command": "echo vietato"})
        self.assertEqual(self.run_with(p).exit, 2)

    def test_session_seen_and_offlog_import(self):
        (self.lab.ts.dir / "off.log").write_text("2026-10-09T08:00:00.000000Z off\n")
        self.run_with(self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "ls"}))
        seen = self.lab.conn.execute("SELECT session FROM session_seen").fetchall()
        self.assertEqual([r[0] for r in seen], [SESSION])
        self.assertEqual(len(self.lab.events("off")), 1)


class CliHookTest(unittest.TestCase):
    def test_hook_subcommand(self):
        import subprocess
        ts = TempState()
        try:
            run = lambda ev, text: subprocess.run(  # noqa: E731
                [sys.executable, "-B", str(ROOT / "bin" / "tollgate"), "hook", ev],
                input=text, capture_output=True, text=True, env=ts.env())
            r = run("PreToolUse", "{rotto")
            self.assertEqual(r.returncode, 2)
            self.assertIn("touch", r.stderr)
            self.assertEqual(run("PostToolUse", "{rotto").returncode, 0)
            p = sample("PreToolUse-Bash", cwd=str(ts.dir))
            self.assertEqual(run("PreToolUse", json.dumps(p)).returncode, 0)
        finally:
            ts.cleanup()


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def make_ctx(self, repo):
        from tollgate_core.config import load_config_text
        from tollgate_hooks.context import Ctx, ReadDb
        ev = adapter.to_event("PreToolUse", self.lab._base("PreToolUse-Bash", None, None))
        return Ctx(ev, self.lab.ts.state, ReadDb(self.lab.conn), load_config_text(DEFAULT_TOML),
                   repo, None, False, self.lab.now, ROOT)

    def test_read_db_is_select_only(self):
        ctx = self.make_ctx(self.lab.wt)
        self.assertEqual(ctx.db.execute("select count(*) from work_items").fetchone()[0], 1)
        with self.assertRaises(PermissionError):
            ctx.db.execute("DELETE FROM work_items")

    def test_protected_roots_follow_the_context_repo(self):
        ctx = self.make_ctx(self.lab.wt)
        roots = ctx.protected_roots(self.lab.wt)
        common = (self.lab.main / ".git").resolve()
        self.assertIn(common / "hooks", roots)
        self.assertIn(common / "config", roots)
        self.assertIn(self.lab.ts.state.root.resolve(), roots)
        self.assertNotIn(common / "hooks", ctx.protected_roots(None))


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
