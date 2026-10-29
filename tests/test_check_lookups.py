"""Letture registrate dagli hook (B1, Task 4): chi ha letto cosa, per quale task."""
import json
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from tests.hookkit import DEFAULT_TOML, DROP, SESSION, Lab, sample_b1
from tollgate_analysis import research
from tollgate_checks import lookup_rec
from tollgate_core import lookups, scope, subagents, tasks
from tollgate_hooks import registry, runner
from tollgate_hooks.context import ReadDb

IMPL = "tollgate:implementer"
REVIEWER = "tollgate:task-reviewer"
MCP_DOCS = "mcp__plugin_context7_context7__query-docs"


def rows(lab):
    return [(r["task"], r["kind"], r["target"], r["agent_id"]) for r in lab.conn.execute(
        "SELECT task, kind, target, agent_id FROM lookups ORDER BY id")]


def start_impl(lab, agent_id, task, *, type_=IMPL):
    subagents.start(lab.conn, agent_id=agent_id, type_=type_, session=SESSION, work=lab.work,
                    task=task, base_sha=lab.base, fingerprint="f", now=lab.now)


def setup_tasks(lab, numbers=(1, 2)):
    """Un piano con i task dati, ognuno assegnato a un implementatore e già `running`."""
    scope.register_plan(lab.conn, lab.ts.state, lab.work, plan_path="docs/superpowers/plans/p.md",
                        plan_sha="s", scope_paths=["src/app.py"],
                        plan_tasks=[(n, []) for n in numbers], advance=False, now=lab.now)
    for n in numbers:
        tasks.assign(lab.conn, lab.work, n, implementer=f"impl-{n}", agent_type=IMPL,
                     reviewer_type=REVIEWER, pending="launch", now=lab.now)
        tasks.task_event(lab.conn, lab.work, n, "start", now=lab.now)


class LookupBase(unittest.TestCase):
    research = True

    def setUp(self):
        self.lab = Lab(research=self.research)
        setup_tasks(self.lab)
        start_impl(self.lab, "impl1", 1)
        start_impl(self.lab, "impl2", 2)
        self.app = str(self.lab.wt / "src/app.py")

    def tearDown(self):
        self.lab.close()

    def read(self, path=None, **kw):
        return self.lab.lookup("read", tool_input={"file_path": path or self.app}, **kw)

    def assertRows(self, expected):
        self.assertEqual(rows(self.lab), expected)


class ReadAttributionTest(LookupBase):
    def test_read_recorded_for_task(self):
        r = self.read(agent_id="impl1")
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertRows([(1, "read", "src/app.py", "impl1")])

    def test_read_by_other_task_not_counted(self):
        self.read(agent_id="impl2")
        self.assertRows([(2, "read", "src/app.py", "impl2")])
        self.assertEqual([x for x in rows(self.lab) if x[0] == 1], [])

    def test_readonly_agent_reads_not_recorded(self):
        start_impl(self.lab, "rev1", 1, type_=REVIEWER)
        self.read(agent_id="rev1", agent_type=REVIEWER)
        self.assertRows([])

    def test_main_session_read_not_recorded(self):
        self.assertEqual(research.ATTRIBUTE_UNNAMED_TOOLS, frozenset())
        self.read()
        self.lab.lookup("webfetch")
        self.assertRows([])

    def test_unknown_agent_not_recorded(self):
        self.read(agent_id="sconosciuto")
        self.assertRows([])

    def test_failed_read_not_recorded(self):
        r = self.read(agent_id="impl1", hook_event_name="PostToolUseFailure")
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertRows([])

    def test_same_read_twice_is_one_row(self):
        self.read(agent_id="impl1")
        self.read(agent_id="impl1")
        self.assertEqual(len(rows(self.lab)), 1)

    def test_read_outside_worktree_not_recorded(self):
        self.read(str(self.lab.main / "src/app.py"), agent_id="impl1")
        self.read("/etc/hostname", agent_id="impl1")
        self.read(str(self.lab.wt / ".." / "altro.py"), agent_id="impl1")
        self.assertRows([])

    def test_relative_and_dot_forms_match(self):
        self.read("./src/app.py", agent_id="impl1")
        self.read("src/../src/app.py", agent_id="impl1")
        self.assertRows([(1, "read", "src/app.py", "impl1")])

    def test_symlink_pointing_outside_not_recorded(self):
        link = self.lab.wt / "src" / "esterno.py"
        os.symlink(self.lab.main / "src/app.py", link)
        self.read(str(link), agent_id="impl1")
        self.assertRows([])

    def test_worktree_behind_symlink(self):
        link = self.lab.tmp / "collegamento"
        os.symlink(self.lab.wt, link)
        self.read(str(link / "src/app.py"), agent_id="impl1", cwd=link)
        self.assertRows([(1, "read", "src/app.py", "impl1")])
        # lo stesso con il worktree registrato attraverso il collegamento
        self.lab.conn.execute("UPDATE work_items SET worktree = ?", (str(link),))
        self.lab.conn.commit()
        self.read(str(self.lab.wt / "src/app.py"), agent_id="impl1")
        self.assertRows([(1, "read", "src/app.py", "impl1")])


class LegacyTest(LookupBase):
    research = False

    def test_legacy_work_not_recorded(self):
        self.read(agent_id="impl1")
        self.lab.bash("cat src/app.py", post=True, agent_id="impl1")
        self.assertRows([])


class WebTest(LookupBase):
    def test_webfetch_recorded_normalized(self):
        self.lab.lookup("webfetch", agent_id="impl1", tool_input={
            "url": "HTTPS://Docs.Python.org:443/3/library/tomllib.html/#anchor", "prompt": "x"})
        self.assertRows([(1, "fetch", "https://docs.python.org/3/library/tomllib.html",
                          "impl1")])

    def test_webfetch_sample_recorded(self):
        self.lab.lookup("webfetch", agent_id="impl1")
        self.assertRows([(1, "fetch", "https://docs.python.org/3/library/tomllib.html",
                          "impl1")])

    def test_webfetch_redirect_records_only_requested_url(self):
        self.lab.lookup("webfetch_redirect", agent_id="impl1")
        self.assertRows([(1, "fetch", "https://docs.python.org/library/json.html", "impl1")])

    def test_webfetch_error_code_not_recorded(self):
        post = sample_b1("webfetch", "post")
        post["tool_response"]["code"] = 404
        self.lab.lookup("webfetch", agent_id="impl1", tool_response=post["tool_response"])
        self.assertRows([])

    def test_webfetch_bad_url_not_recorded(self):
        self.lab.lookup("webfetch", agent_id="impl1", tool_input={"url": "ftp://x/y"})
        self.assertRows([])

    def test_websearch_is_search_only(self):
        self.lab.lookup("websearch", agent_id="impl1")
        self.assertRows([(1, "search", "python tomllib", "impl1")])
        self.assertEqual(lookups.for_task(self.lab.conn, self.lab.work, 1),
                         [lookups.Lookup("search", "python tomllib")])

    def test_doc_mcp_recorded(self):
        self.lab.lookup("webfetch", agent_id="impl1", tool_name=MCP_DOCS,
                        tool_input={"libraryId": "/python/cpython", "query": "tomllib"},
                        tool_response={"content": [{"type": "text", "text": "ok"}]})
        self.assertRows([(1, "docs", "/python/cpython", "impl1")])

    def test_other_mcp_not_recorded(self):
        self.lab.lookup("webfetch", agent_id="impl1", tool_name="mcp__altro__scrivi",
                        tool_input={"libraryId": "/python/cpython"})
        self.lab.lookup("webfetch", agent_id="impl1", tool_name=MCP_DOCS,
                        tool_input={"query": "senza libreria"})
        self.assertRows([])


class GrepTest(LookupBase):
    def test_grep_on_file_recorded(self):
        self.lab.lookup("grep_content", agent_id="impl1",
                        tool_input={"output_mode": "content", "path": self.app,
                                    "pattern": "somma"})
        self.assertRows([(1, "grep", "src/app.py", "impl1")])

    def test_grep_files_with_matches_not_recorded(self):
        self.lab.lookup("grep_files", agent_id="impl1",
                        tool_input={"output_mode": "files_with_matches", "path": self.app,
                                    "pattern": "somma"})
        self.assertRows([])

    def test_grep_on_dir_not_recorded(self):
        self.lab.lookup("grep_content_dir", agent_id="impl1",
                        tool_input={"output_mode": "content", "path": str(self.lab.wt / "src"),
                                    "pattern": "somma"})
        self.assertRows([])

    def test_grep_default_mode_not_recorded(self):
        self.lab.lookup("grep_default", agent_id="impl1",
                        tool_input={"path": self.app, "pattern": "somma"})
        self.assertRows([])

    def test_grep_without_path_not_recorded(self):
        self.lab.lookup("grep_content", agent_id="impl1",
                        tool_input={"output_mode": "content", "pattern": "somma"})
        self.assertRows([])

    def test_grep_direct_event_through_the_module(self):
        """`Grep` è fuori dal matcher di hooks.json, ma il modulo lo sa registrare."""
        from tollgate_hooks import adapter
        raw = sample_b1("grep_content", "post", session_id=SESSION, cwd=str(self.lab.wt),
                        agent_id="impl1", agent_type=IMPL,
                        tool_input={"output_mode": "content", "path": self.app, "pattern": "s"})
        event = adapter.to_event("PostToolUse", raw)
        work = self.lab.conn.execute("SELECT * FROM work_items").fetchone()
        ctx = SimpleNamespace(db=ReadDb(self.lab.conn), work=work, bound=True,
                              now=self.lab.now, stale_minutes=30,
                              readonly=lambda t: t == REVIEWER)
        out = lookup_rec.decide(event, ctx)
        self.assertEqual([(d.op, d.data["kind"], d.data["target"], d.data["task"])
                          for d in out], [("lookup", "grep", "src/app.py", 1)])


class BashTest(LookupBase):
    def test_bash_cat_recorded(self):
        r = self.lab.bash("cat src/app.py", post=True, agent_id="impl1")
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertRows([(1, "bash_read", "src/app.py", "impl1")])

    def test_failed_bash_cat_not_recorded(self):
        self.lab.bash("cat src/app.py", post=True, agent_id="impl1",
                      hook_event_name="PostToolUseFailure")
        self.assertRows([])

    def test_bash_cat_by_main_session_not_recorded(self):
        self.lab.bash("cat src/app.py", post=True)
        self.assertRows([])

    def test_bash_target_after_cd(self):
        self.lab.bash("cd src && cat app.py", post=True, agent_id="impl1")
        self.assertRows([(1, "bash_read", "src/app.py", "impl1")])

    def test_bash_directory_and_missing_targets_not_recorded(self):
        self.lab.bash("grep -r somma src", post=True, agent_id="impl1")
        self.lab.bash("cat src/non_esiste.py", post=True, agent_id="impl1")
        self.lab.bash("cat /etc/hostname", post=True, agent_id="impl1")
        self.assertRows([])

    def test_bash_not_a_reader_not_recorded(self):
        self.lab.bash("wc -l src/app.py && ls src", post=True, agent_id="impl1")
        self.assertRows([])

    def test_bash_two_files(self):
        self.lab.bash("head -n 3 src/app.py tests/test_app.py", post=True, agent_id="impl1")
        self.assertRows([(1, "bash_read", "src/app.py", "impl1"),
                         (1, "bash_read", "tests/test_app.py", "impl1")])

    def test_bash_via_sample(self):
        start = self.lab.hook(sample_b1("bash_cat", "post", session_id=SESSION,
                                        cwd=str(self.lab.wt), agent_id="impl1", agent_type=IMPL))
        self.assertEqual(start.exit, 0, start.stderr)
        self.assertRows([])    # pyproject.toml non esiste nel banco


class UnnamedTest(LookupBase):
    def patched(self):
        return mock.patch.object(research, "ATTRIBUTE_UNNAMED_TOOLS",
                                 frozenset({"WebFetch", "WebSearch"}))

    def test_unnamed_fetch_attributed_when_enabled(self):
        # un solo implementatore vivo: il task 2 non ha chi lo esegua
        subagents.finish(self.lab.conn, "impl2", state="done", now=self.lab.now)
        with self.patched():
            self.lab.lookup("webfetch")
            self.lab.lookup("websearch")
            self.read()   # Read non è nell'insieme: mai attribuita
        self.assertEqual([(t, k) for t, k, _, _ in rows(self.lab)], [(1, "fetch"), (1, "search")])
        self.assertIsNone(rows(self.lab)[0][3])

    def test_unnamed_without_running_implementer_not_attributed(self):
        subagents.finish(self.lab.conn, "impl1", state="done", now=self.lab.now)
        subagents.finish(self.lab.conn, "impl2", state="done", now=self.lab.now)
        with self.patched():
            self.lab.lookup("webfetch")
        self.assertRows([])

    def test_unnamed_ambiguous_writers_not_attributed(self):
        with self.patched():
            self.lab.lookup("webfetch")
        self.assertRows([])

    def test_unnamed_readonly_agent_ignored(self):
        subagents.finish(self.lab.conn, "impl2", state="done", now=self.lab.now)
        start_impl(self.lab, "rev1", 2, type_=REVIEWER)
        with self.patched():
            self.lab.lookup("webfetch")
        self.assertEqual([x[0] for x in rows(self.lab)], [1])

    def test_unnamed_stale_writer_ignored(self):
        self.lab.conn.execute("UPDATE subagents SET last_seen = '2026-10-09T08:00:00.000000Z' "
                              "WHERE id = 'impl2'")
        self.lab.conn.commit()
        with self.patched():
            self.lab.lookup("webfetch")
        self.assertEqual([x[0] for x in rows(self.lab)], [1])


class WorkFromSubagentTest(LookupBase):
    def decide(self, command, cwd):
        from tollgate_hooks import adapter
        raw = sample_b1("bash_cat", "post", session_id=SESSION, cwd=str(cwd),
                        agent_id="impl1", agent_type=IMPL, tool_input={"command": command})
        event = adapter.to_event("PostToolUse", raw)
        ctx = SimpleNamespace(db=ReadDb(self.lab.conn), work=None, bound=False,
                              now=self.lab.now, stale_minutes=30,
                              readonly=lambda t: t == REVIEWER, work_for_path=lambda p: None)
        return lookup_rec.decide(event, ctx)

    def test_bash_read_with_cwd_outside_the_worktree(self):
        out = self.decide(f"cat '{self.app}'", self.lab.tmp)
        self.assertEqual([(d.op, d.data["kind"], d.data["target"], d.data["task"])
                          for d in out], [("lookup", "bash_read", "src/app.py", 1)])

    def test_closed_work_not_tracked(self):
        self.lab.conn.execute("UPDATE work_items SET phase = 'closed' WHERE id = ?",
                              (self.lab.work,))
        self.lab.conn.commit()
        self.assertEqual(self.decide(f"cat '{self.app}'", self.lab.wt), [])


class ComponentOffTest(unittest.TestCase):
    """`[components] research_note = false`: la via breve registra lo stesso (dati inutilizzati,
    potati da `prune`); `lookup_rec` no, perché il suo componente è spento."""

    def setUp(self):
        self.lab = Lab(research=True, toml=DEFAULT_TOML + "\n[components]\nresearch_note = false\n")
        setup_tasks(self.lab, (1,))
        start_impl(self.lab, "impl1", 1)

    def tearDown(self):
        self.lab.close()

    def test_short_path_records_with_component_off(self):
        r = self.lab.lookup("read", agent_id="impl1",
                            tool_input={"file_path": str(self.lab.wt / "src/app.py")})
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(rows(self.lab), [(1, "read", "src/app.py", "impl1")])

    def test_bash_read_not_recorded_with_component_off(self):
        self.lab.bash("cat src/app.py", post=True, agent_id="impl1")
        self.assertEqual(rows(self.lab), [])


class ShortPathTest(LookupBase):
    def test_post_lookup_short_path_skips_config(self):
        boom = mock.Mock(side_effect=AssertionError("la via breve non carica la configurazione"))
        with mock.patch.object(runner, "load_config", boom), \
                mock.patch.object(registry, "load", boom):
            r = self.read(agent_id="impl1")
        self.assertEqual(r.exit, 0, r.stderr)
        boom.assert_not_called()
        self.assertRows([(1, "read", "src/app.py", "impl1")])

    def test_short_path_touches_the_subagent(self):
        before = subagents.get(self.lab.conn, "impl1")["last_seen"]
        self.read(agent_id="impl1")
        self.assertGreater(subagents.get(self.lab.conn, "impl1")["last_seen"], before)

    def test_glob_is_not_a_lookup(self):
        r = self.lab.lookup("glob", agent_id="impl1")
        self.assertEqual(r.exit, 0)
        self.assertRows([])

    def test_cwd_outside_any_work_relative_path_not_recorded(self):
        r = self.read("src/app.py", agent_id="impl1", cwd=self.lab.tmp)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertRows([])

    def test_work_comes_from_the_subagent_not_from_the_cwd(self):
        """Minor 1: il gate usa il lavoro dell'implementatore; la lettura deve contare anche con
        il cwd fuori dal worktree."""
        r = self.read(agent_id="impl1", cwd=self.lab.tmp)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertRows([(1, "read", "src/app.py", "impl1")])

    def test_error_in_recording_is_informative(self):
        with mock.patch.object(lookups, "record", side_effect=ValueError("guasto")):
            r = self.read(agent_id="impl1")
        self.assertEqual(r.exit, 0)
        self.assertIn("guasto", r.stderr)


if __name__ == "__main__":
    unittest.main()
