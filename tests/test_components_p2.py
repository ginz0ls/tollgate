"""Chiavi di [components] usate da P2 senza un test a parte: ognuna spenta spegne il suo controllo.

Ogni test confronta con la stessa situazione a componente acceso, così il test vede davvero il
controllo e non una scorciatoia (spec 18: ogni pratica è un componente spegnibile)."""
import json
import unittest

from tests.hookkit import DEFAULT_TOML, SESSION, Lab
from tests.test_check_agents import IMPL, agent_payload
from tests.test_check_post_edit import plan_text
from tests.test_check_subagent_stop import Base, report
from tests.test_check_writes import with_scope
from tollgate_core import phases, subagents, tasks


def off(name):
    return DEFAULT_TOML + f"[components]\n{name} = false\n"


class ContextGuardOffTest(unittest.TestCase):
    def test_context_over_stop_passes_when_off(self):
        for toml, code in ((DEFAULT_TOML, 2), (off("context_guard"), 0)):
            with self.subTest(component_off=toml != DEFAULT_TOML):
                lab = Lab(toml=toml)
                try:
                    with_scope(lab)
                    d = lab.ts.dir / "ctx"
                    d.mkdir()
                    (d / f"{SESSION}.json").write_text(json.dumps({"used_pct": 60}))
                    self.assertEqual(lab.hook(agent_payload(lab, "Explore")).exit, code)
                finally:
                    lab.close()


class SingleWriterOffTest(unittest.TestCase):
    def test_second_writer_passes_when_off(self):
        for toml, code in ((DEFAULT_TOML, 2), (off("single_writer"), 0)):
            with self.subTest(component_off=toml != DEFAULT_TOML):
                lab = Lab(toml=toml)
                try:
                    with_scope(lab)
                    subagents.start(lab.conn, agent_id="a-vecchio", type_=IMPL, session=SESSION,
                                    work=lab.work, task=None, base_sha=lab.base, fingerprint="f",
                                    now=lab.now)
                    tasks.assign(lab.conn, lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                                 pending="launch", now=lab.now)
                    self.assertEqual(lab.hook(agent_payload(lab, IMPL, "tg-7-t1")).exit, code)
                finally:
                    lab.close()


class TaskSizeOffTest(Base):
    toml = off("task_size")

    def test_big_task_without_size_reason_passes_when_off(self):
        sha = self.commit("".join(f"x{i} = {i}\n" for i in range(600)), path="src/big.py")
        self.green(sha)
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReportFieldsOffTest(Base):
    toml = off("report_fields")

    def test_invalid_report_passes_when_off(self):
        r = self.stop(text='{"status": "DONE"}')
        self.assertEqual(r.exit, 0)
        self.assertNotIn("non valido", r.stderr)


class MustHaveTestsOffTest(unittest.TestCase):
    def test_must_have_without_test_registers_when_off(self):
        cases = ((DEFAULT_TOML, 2, "plan"), (off("must_have_tests"), 0, "execution"))
        for toml, code, phase in cases:
            with self.subTest(component_off=toml != DEFAULT_TOML):
                lab = Lab(phase="plan", toml=toml)
                try:
                    plan = lab.wt / "docs/superpowers/plans/2026-10-09-somma.md"
                    plan.parent.mkdir(parents=True)
                    plan.write_text(plan_text(must_have="M1. Somma senza test"))
                    self.assertEqual(lab.post_edit(plan).exit, code)
                    self.assertEqual(phases.get_work(lab.conn, lab.work)["phase"], phase)
                finally:
                    lab.close()


if __name__ == "__main__":
    unittest.main()
