"""Comando `research` (B1, Task 6): consegna e lettura della nota di ricerca."""
import unittest
from unittest import mock

from tests.flowkit import FlowLab
from tests.hookkit import DEFAULT_TOML
from tollgate_analysis import research
from tollgate_core import config, lookups, tasks
from tollgate_flow import research_cmd

URL = "https://docs.example.com/guide"
IMPL = "tollgate:implementer"
REVIEWER = "tollgate:task-reviewer"


def note_text(url=URL):
    return (f"## {research.SECTION_FILES}\n- src/app.py\n\n"
            f"## {research.SECTION_DOCS}\n- {url} — descrive il caso\n\n"
            f"## {research.SECTION_FOUND}\nTengo conto del caso zero.\n")


class ResearchCase(unittest.TestCase):
    def make(self, *, toml=DEFAULT_TOML, level="L1", phase="plan", research_flag=1,
             start=True):
        fl = FlowLab(issue=7, phase=phase, toml=toml, level=level)
        self.addCleanup(fl.close)
        self.fl = fl
        if level != "L0" and phase == "plan":
            fl.register_plan(1)
            if start:
                tasks.assign(fl.conn, fl.work, 1, implementer="impl-1", agent_type=IMPL,
                             reviewer_type=REVIEWER, pending="launch", now=fl.now)
                tasks.task_event(fl.conn, fl.work, 1, "start", now=fl.now)
        fl.conn.execute("UPDATE work_items SET research = ? WHERE id = ?",
                        (research_flag, fl.work))
        fl.conn.commit()
        return fl

    def read(self, kind, target, *, task=1, agent_id="impl-1"):
        lookups.record(self.fl.conn, work=self.fl.work, task=task, agent_id=agent_id,
                       session=None, kind=kind, target=target, now=self.fl.now)

    def read_all(self, **kw):
        self.read("read", "src/app.py", **kw)
        self.read(research.URL_KIND, URL, **kw)

    def submit(self, text=None, number=1):
        return research_cmd.submit(self.fl.ts.state, self.fl.wt, number,
                                   note_text() if text is None else text)

    def row(self):
        return tasks.get_task(self.fl.conn, self.fl.work, 1)

    def events(self):
        return self.fl.events("research_note")


class SubmitTest(ResearchCase):
    def test_submit_valid_note(self):
        fl = self.make()
        self.read_all()
        r = self.submit()
        self.assertEqual((r.code, r.lines), (research_cmd.OK, [r.lines[0]]), r.lines)
        self.assertEqual(self.row()["research_ok"], 1)
        self.assertEqual(r.path, research_cmd.note_path(fl.wt, 7, 1))
        self.assertEqual(r.path, fl.wt / ".tollgate-run" / "7" / "research-1.md")
        text = r.path.read_text()
        self.assertTrue(text.startswith(note_text()))
        self.assertEqual(text.splitlines()[-1], "esito: valida")
        ev = self.events()
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0], {"task": 1, "ok": True, "problems": []})

    def test_submit_invalid_lists_problems(self):
        self.make()
        self.read("read", "src/app.py")
        r = self.submit()
        self.assertEqual(r.code, research_cmd.INVALID)
        self.assertTrue(any(URL in line for line in r.lines), r.lines)
        self.assertEqual(self.row()["research_ok"], 0)
        self.assertEqual(self.row()["research_note"], note_text())
        self.assertEqual(r.path.read_text().splitlines()[-1], "esito: non valida")
        self.assertFalse(self.events()[0]["ok"])

    def test_resubmit_replaces(self):
        self.make()
        self.read_all()
        self.assertEqual(self.submit().code, research_cmd.OK)
        r = self.submit(note_text("https://altra.example.com/x"))
        self.assertEqual(r.code, research_cmd.INVALID)
        self.assertEqual(self.row()["research_ok"], 0)
        self.assertEqual(len(self.events()), 2)

    def test_refused_in_l0(self):
        self.make(level="L0", phase="execution")
        r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("L0", " ".join(r.lines))

    def test_refused_outside_execution(self):
        self.make()
        self.fl.goto("review")
        r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("review", " ".join(r.lines))

    def test_refused_legacy_work(self):
        self.make(research_flag=0)
        r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("lavoro iniziato prima del passo informati prima", " ".join(r.lines))
        self.assertIsNone(self.row()["research_note"])

    def test_component_off_submit_refused(self):
        self.make(toml=DEFAULT_TOML + "\n[components]\nresearch_note = false\n")
        r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("componente research_note spento", " ".join(r.lines))
        self.assertIsNone(self.row()["research_note"])

    def test_unreadable_config_refused(self):
        self.make()
        with mock.patch.object(research_cmd.config, "load_config",
                               side_effect=config.ConfigError("TOML rotto")):
            r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("configurazione non leggibile: TOML rotto", " ".join(r.lines))
        self.assertIsNone(self.row()["research_note"])

    def test_note_file_write_failure_refused(self):
        self.make()
        self.read_all()
        with mock.patch.object(research_cmd, "write_atomic", side_effect=OSError("disco pieno")):
            r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("nota non scritta", " ".join(r.lines))
        self.assertIn("disco pieno", " ".join(r.lines))
        self.assertIsNone(self.row()["research_note"])
        self.assertEqual(self.events(), [])

    def test_refused_task_not_running(self):
        self.make(start=False)
        r = self.submit()
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("pending", " ".join(r.lines))

    def test_refused_unknown_task(self):
        self.make()
        r = self.submit(number=9)
        self.assertEqual(r.code, research_cmd.REFUSED)
        self.assertIn("9", " ".join(r.lines))

    def test_refused_without_work(self):
        self.make()
        r = research_cmd.submit(self.fl.ts.state, self.fl.tmp, 1, note_text())
        self.assertEqual(r.code, research_cmd.REFUSED)

    def test_lookups_of_previous_round_count(self):
        self.make()
        self.read_all(agent_id="impl-vecchio")
        self.assertEqual(self.submit().code, research_cmd.OK)

    def test_lookups_of_other_task_do_not_count(self):
        self.make()
        self.read_all(task=2)
        self.assertEqual(self.submit().code, research_cmd.INVALID)


class ShowTest(ResearchCase):
    def test_show_prints_note_and_outcome(self):
        self.make()
        self.read_all()
        self.submit()
        r = research_cmd.show(self.fl.ts.state, self.fl.wt, 1)
        self.assertEqual(r.code, research_cmd.OK)
        self.assertEqual(r.lines[-1], "esito: valida")
        self.assertIn("Tengo conto del caso zero.", "\n".join(r.lines))

    def test_show_invalid_outcome(self):
        self.make()
        self.submit()
        r = research_cmd.show(self.fl.ts.state, self.fl.wt, 1)
        self.assertEqual(r.code, research_cmd.INVALID)
        self.assertEqual(r.lines[-1], "esito: non valida")

    def test_show_refused_without_note(self):
        self.make()
        self.assertEqual(research_cmd.show(self.fl.ts.state, self.fl.wt, 1).code,
                         research_cmd.REFUSED)


if __name__ == "__main__":
    unittest.main()
