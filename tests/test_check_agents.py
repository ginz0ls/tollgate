import json
import unittest
from datetime import timedelta

from tests.hookkit import DEFAULT_TOML, SESSION, T0, Lab, sample
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import phases, subagents, tasks

IMPL = "tollgate:implementer"


def agent_payload(lab, atype, name=None, bg=False):
    ti = {"description": "d", "prompt": "p", "subagent_type": atype, "run_in_background": bg}
    if name:
        ti["name"] = name
    return sample("PreToolUse-Agent", session_id=SESSION, cwd=str(lab.wt), tool_input=ti)


def send(lab, to, agent_id=None):
    extra = {"agent_id": agent_id, "agent_type": IMPL} if agent_id else {}
    return lab.hook(sample("PreToolUse-SendMessage", session_id=SESSION, cwd=str(lab.wt),
                           tool_input={"to": to, "message": "continua", "summary": "s"},
                           **extra))


def start(lab, agent_id, atype=IMPL):
    return lab.hook(sample("SubagentStart-none", session_id=SESSION, cwd=str(lab.wt),
                           agent_id=agent_id, agent_type=atype))


class PreAgentTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def assign(self, pending="launch"):
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending=pending, now=self.lab.now)

    def test_general_purpose_denied_with_execute_hint(self):
        r = self.lab.hook(agent_payload(self.lab, "general-purpose"))
        self.assertEqual(r.exit, 2)
        self.assertIn("/tollgate:execute", r.stderr)

    def test_implementer_rules(self):
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 2)
        self.assign()
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL)).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1", bg=True)).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 0)

    def test_profile_agent_replaces_generic_implementer(self):
        # Criterio 38: su un task con l'agente di profilo il generico tollgate:implementer è negato.
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1",
                     agent_type="probe:implementer-frontend", pending="launch", now=self.lab.now)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(
            self.lab, "probe:implementer-frontend", "tg-7-t1")).exit, 0)

    def test_readonly_always_allowed(self):
        for t in ("tollgate:task-reviewer", "Explore", "probe:reviewer-frontend"):
            self.assertEqual(self.lab.hook(agent_payload(self.lab, t)).exit, 0)

    def test_single_writer_and_stale(self):
        subagents.start(self.lab.conn, agent_id="a-vecchio", type_=IMPL, session=SESSION,
                        work=self.lab.work, task=None, base_sha=self.lab.base, fingerprint="f",
                        now=self.lab.now)
        self.assign()
        r = self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1"))
        self.assertEqual(r.exit, 2)
        self.assertIn("/tollgate:resolve writer", r.stderr)
        r = self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1"),
                          now=self.lab.now + timedelta(minutes=31))
        self.assertEqual(r.exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a-vecchio")["state"], "interrupted")

    def test_context_guard(self):
        d = self.lab.ts.dir / "ctx"
        d.mkdir()
        for pct, code in ((60, 2), (50, 0), (None, 0)):
            (d / f"{SESSION}.json").write_text(json.dumps({"used_pct": pct}))
            with self.subTest(pct=pct):
                r = self.lab.hook(agent_payload(self.lab, "Explore"))
                self.assertEqual(r.exit, code)
                if pct == 50:
                    self.assertIn("contesto", r.stdout)


class ResumeTaskTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)
        tasks.add_task(self.lab.conn, self.lab.work, 2, source="plan", now=self.lab.now)
        for n in (1, 2):
            tasks.assign(self.lab.conn, self.lab.work, n, implementer=f"tg-7-t{n}",
                         agent_type=IMPL, pending="launch", now=self.lab.now)

    def tearDown(self):
        self.lab.close()

    def test_resume_takes_its_own_task(self):
        start(self.lab, "a1")  # prende il task 1
        start(self.lab, "a2")  # prende il task 2
        for agent in ("a1", "a2"):
            subagents.finish(self.lab.conn, agent, state="done", declared_status="DONE",
                             now=self.lab.now)
        for n in (1, 2):
            tasks.assign(self.lab.conn, self.lab.work, n, implementer=f"tg-7-t{n}",
                         agent_type=IMPL, pending="resume", now=self.lab.now)
        start(self.lab, "a2")
        self.assertEqual(subagents.get(self.lab.conn, "a2")["task"], 2)
        self.assertIsNone(tasks.get_task(self.lab.conn, self.lab.work, 2)["pending"])
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["pending"], "resume")

    def test_resumed_implementer_keeps_fingerprint(self):
        start(self.lab, "a1")
        before = subagents.get(self.lab.conn, "a1")["fingerprint"]
        (self.lab.wt / "src/app.py").write_text("x = 2\n")
        git(self.lab.wt, "commit", "-qam", "lavoro")
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        start(self.lab, "a1")
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["resumes"], row["fingerprint"]), (1, before))


class StartAndResumeTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)

    def tearDown(self):
        self.lab.close()

    def test_start_associates_task_and_keeps_base_on_resume(self):
        r = start(self.lab, "a1")
        self.assertIn("verify", r.stdout)
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["task"], row["agent_base_sha"]), (1, self.lab.base))
        self.assertIsNone(tasks.get_task(self.lab.conn, self.lab.work, 1)["pending"])
        (self.lab.wt / "src/app.py").write_text("x = 2\n")
        git(self.lab.wt, "commit", "-qam", "lavoro")
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        start(self.lab, "a1")
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["agent_base_sha"], row["resumes"]), (self.lab.base, 1))

    def test_name_registry_and_send_message(self):
        start(self.lab, "a1")
        post = sample("PostToolUse-Agent-foreground-manual", session_id=SESSION,
                      cwd=str(self.lab.wt))
        post["tool_input"]["name"] = "tg-7-t1"
        post["tool_response"]["agentId"] = "a1"
        self.lab.hook(post)
        self.assertEqual(subagents.by_name(self.lab.conn, "tg-7-t1", work=self.lab.work)["id"],
                         "a1")
        subagents.finish(self.lab.conn, "a1", state="done", declared_status="DONE",
                         now=self.lab.now)
        self.assertEqual(send(self.lab, "mai-visto").exit, 2)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 2)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 0)
        self.assertEqual(send(self.lab, "a1").exit, 0)

    def test_needs_context_resume_allowed(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        start(self.lab, "a1")
        subagents.set_name(self.lab.conn, "a1", "tg-7-t1", session=SESSION, work=self.lab.work,
                           now=self.lab.now)
        subagents.finish(self.lab.conn, "a1", state="done", declared_status="NEEDS_CONTEXT",
                         now=self.lab.now)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 0)

    def test_turn_cut_closes_row_and_blocks_task(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        cut = sample("PostToolUse-Agent-maxturns-cut", session_id=SESSION, cwd=str(self.lab.wt))
        aid = cut["tool_response"]["agentId"]
        start(self.lab, aid)
        self.lab.hook(cut)
        self.assertEqual(subagents.get(self.lab.conn, aid)["state"], "cut")
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["state"], "blocked")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")
        self.assertEqual(subagents.running(self.lab.conn, work=self.lab.work), [])

    def test_skill_and_handback(self):
        start(self.lab, "a1")
        self.lab.hook(sample("PostToolUse-Skill", session_id=SESSION, cwd=str(self.lab.wt),
                             agent_id="a1", agent_type=IMPL, tool_name="Skill",
                             tool_input={"skill": "superpowers:test-driven-development"},
                             tool_response={"success": True}))
        self.assertIn("test-driven-development",
                      tasks.get_task(self.lab.conn, self.lab.work, 1)["skills_used"])
        hb = sample("PostToolUse-SubagentHandback", session_id=SESSION, cwd=str(self.lab.wt),
                    agent_id="a1", agent_type=IMPL, tool_input={"message": "{\"status\":\"DONE\"}"})
        self.lab.hook(hb)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["report"], '{"status":"DONE"}')


def notification(agent_id, text="stopped at its 2-turn limit (partial result; SendMessage "
                                "to task-id to continue)", tokens=15677):
    """Il prompt di UserPromptSubmit visto in E7/E8 (docs/verifiche/2026-10-09-p2-verifiche.md)."""
    return (f"<task-notification>\n<task-id>{agent_id}</task-id>\n"
            f"<tool-use-id>toolu_016RfaW6bHifgQuEhW2btMeY</tool-use-id>\n"
            f"<output-file>/tmp/x/{agent_id}.output</output-file>\n<status>completed</status>\n"
            f'<summary>Agent "Sonda taglio maxTurns" {text}</summary>\n'
            f"<note>A task-notification fires each time this agent stops.</note>\n"
            f"<result>NOTE: {text}</result>\n"
            f"<usage><subagent_tokens>{tokens}</subagent_tokens><tool_uses>2</tool_uses>"
            f"<duration_ms>5943</duration_ms></usage>\n</task-notification>")


class PromptSubmitCutTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        start(self.lab, "a-bg")

    def tearDown(self):
        self.lab.close()

    def prompt(self, text):
        return self.lab.hook(sample("UserPromptSubmit-none", session_id=SESSION,
                                    cwd=str(self.lab.wt), prompt=text))

    def state(self):
        return (subagents.get(self.lab.conn, "a-bg")["state"],
                tasks.get_task(self.lab.conn, self.lab.work, 1)["state"],
                phases.get_work(self.lab.conn, self.lab.work)["phase"])

    def test_plain_prompt_and_other_notifications_do_nothing(self):
        for text in ("/hookprobe:probe-worktree", "stopped at its 2-turn limit",
                     notification("a-bg", "completed normally")):
            with self.subTest(text=text[:30]):
                self.assertEqual(self.prompt(text).exit, 0)
                self.assertEqual(self.state(), ("running", "running", "execution"))

    def test_background_cut_closes_row_budgets_task_and_blocks(self):
        r = self.prompt(notification("a-bg"))
        self.assertEqual(r.exit, 0)
        self.assertEqual(self.state(), ("cut", "blocked", "blocked"))
        self.assertEqual(subagents.get(self.lab.conn, "a-bg")["tokens"], 15677)
        blk = self.lab.conn.execute("SELECT type, reason FROM blocks").fetchone()
        self.assertEqual(blk["type"], "needs_you")
        self.assertIn("budget superato", blk["reason"])

    def test_cut_after_resume_is_recognized_again(self):
        subagents.finish(self.lab.conn, "a-bg", state="done", declared_status="DONE",
                         now=self.lab.now)
        start(self.lab, "a-bg")
        self.prompt(notification("a-bg", "stopped at its 3-turn limit (partial result)"))
        self.assertEqual(self.state(), ("cut", "blocked", "blocked"))

    def test_unknown_agent_and_closed_row_change_nothing(self):
        self.prompt(notification("mai-visto"))
        self.assertEqual(self.state(), ("running", "running", "execution"))
        subagents.finish(self.lab.conn, "a-bg", state="done", now=self.lab.now)
        self.prompt(notification("a-bg"))
        self.assertEqual(self.state(), ("done", "running", "execution"))

    def test_budget_component_off_still_closes_row_without_block(self):
        self.lab.close()
        self.setUp_with("[components]\ntask_budget = false\n")
        self.prompt(notification("a-bg"))
        self.assertEqual(self.state(), ("cut", "running", "execution"))
        self.assertEqual(subagents.running(self.lab.conn, work=self.lab.work), [])
        self.assertIsNone(self.lab.conn.execute("SELECT 1 FROM blocks").fetchone())

    def test_two_notifications_cut_only_the_matching_one(self):
        start(self.lab, "a-ok")
        self.prompt(notification("a-ok", "completed normally") + "\n"
                    + notification("a-bg"))
        self.assertEqual(subagents.get(self.lab.conn, "a-ok")["state"], "running")
        self.assertEqual(subagents.get(self.lab.conn, "a-bg")["state"], "cut")

    def test_two_cut_notifications_cut_both(self):
        start(self.lab, "a-2")
        self.prompt(notification("a-bg") + "\n" + notification("a-2"))
        self.assertEqual(subagents.get(self.lab.conn, "a-bg")["state"], "cut")
        self.assertEqual(subagents.get(self.lab.conn, "a-2")["state"], "cut")

    def test_user_quoting_a_notification_cuts_nothing(self):
        self.prompt("guarda cosa mi è arrivato:\n" + notification("a-bg"))
        self.assertEqual(self.state(), ("running", "running", "execution"))

    def test_phrase_only_in_result_cuts_nothing(self):
        text = notification("a-bg", "completed normally").replace(
            "<result>NOTE: completed normally", "<result>NOTE: stopped at its 2-turn limit")
        self.assertIn("2-turn limit</result>", text)
        self.prompt(text)
        self.assertEqual(self.state(), ("running", "running", "execution"))

    def test_leading_whitespace_is_allowed(self):
        self.prompt("\n  " + notification("a-bg"))
        self.assertEqual(self.state()[0], "cut")

    def setUp_with(self, extra):
        self.lab = Lab(toml=DEFAULT_TOML + extra)
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        start(self.lab, "a-bg")

    def test_task_not_running_only_closes_row(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "report_done", now=self.lab.now)
        self.prompt(notification("a-bg"))
        self.assertEqual(self.state(), ("cut", "review", "execution"))


class PostAgentExtraTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def test_async_launch_registers_name_but_no_cut(self):
        post = sample("PostToolUse-Agent-background", session_id=SESSION, cwd=str(self.lab.wt))
        aid = post["tool_response"]["agentId"]
        self.assertEqual(self.lab.hook(post).exit, 0)
        row = subagents.get(self.lab.conn, aid)
        self.assertEqual(row["name"], "contatore")
        self.assertIsNone(row["ended"])

    def test_handback_report_from_auto_mode(self):
        start(self.lab, "aaf79e12a030de3c4", "general-purpose")
        self.lab.hook(sample("PostToolUse-Agent-auto-handback", session_id=SESSION,
                             cwd=str(self.lab.wt)))
        self.assertEqual(subagents.get(self.lab.conn, "aaf79e12a030de3c4")["report"], "uno")

    def test_foreground_cut_with_budget_off_closes_row_only(self):
        self.lab.close()
        self.lab = Lab(toml=DEFAULT_TOML + "[components]\ntask_budget = false\n")
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        cut = sample("PostToolUse-Agent-maxturns-cut", session_id=SESSION, cwd=str(self.lab.wt))
        aid = cut["tool_response"]["agentId"]
        start(self.lab, aid)
        self.lab.hook(cut)
        row = subagents.get(self.lab.conn, aid)
        self.assertEqual((row["state"], row["tokens"]), ("cut", 15247))
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["state"], "running")
        self.assertIsNone(self.lab.conn.execute("SELECT 1 FROM blocks").fetchone())

    def test_foreground_cut_records_tokens(self):
        cut = sample("PostToolUse-Agent-maxturns-cut", session_id=SESSION, cwd=str(self.lab.wt))
        start(self.lab, cut["tool_response"]["agentId"])
        self.lab.hook(cut)
        row = subagents.get(self.lab.conn, cut["tool_response"]["agentId"])
        self.assertEqual((row["state"], row["tokens"]), ("cut", 15247))


class SendMessageExtraTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)
        start(self.lab, "a1")
        subagents.set_name(self.lab.conn, "a1", "tg-7-t1", session=SESSION, work=self.lab.work,
                           now=self.lab.now)

    def tearDown(self):
        self.lab.close()

    def test_subagent_cannot_resume_a_writer_and_main_cannot_while_one_runs(self):
        self.assertEqual(send(self.lab, "tg-7-t1", agent_id="altro").exit, 2)
        start(self.lab, "r1", "tollgate:task-reviewer")
        subagents.set_name(self.lab.conn, "r1", "rev", session=SESSION, work=self.lab.work,
                           now=self.lab.now)
        self.assertEqual(send(self.lab, "rev").exit, 0)

    def test_subagent_sender_allowed_outside_execution(self):
        self.lab.goto("review")
        self.assertEqual(send(self.lab, "tg-7-t1", agent_id="altro").exit, 0)

    def test_stale_target_is_not_interrupted_before_resume(self):
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        r = self.lab.hook(sample("PreToolUse-SendMessage", session_id=SESSION,
                                 cwd=str(self.lab.wt),
                                 tool_input={"to": "tg-7-t1", "message": "m"}),
                          now=self.lab.now + timedelta(minutes=31))
        self.assertEqual(r.exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "running")

    def test_resume_blocked_by_another_live_writer(self):
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        start(self.lab, "a2", "general-purpose")
        r = send(self.lab, "tg-7-t1")
        self.assertEqual(r.exit, 2)
        self.assertIn("scrittore unico", r.stderr)

    def test_stale_writer_does_not_block_resume(self):
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        start(self.lab, "a2", "general-purpose")
        r = self.lab.hook(sample("PreToolUse-SendMessage", session_id=SESSION,
                                 cwd=str(self.lab.wt),
                                 tool_input={"to": "tg-7-t1", "message": "m"}),
                          now=self.lab.now + timedelta(minutes=31))
        self.assertEqual(r.exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a2")["state"], "interrupted")


if __name__ == "__main__":
    unittest.main()
