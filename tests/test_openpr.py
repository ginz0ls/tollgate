import json
import os
import unittest
from datetime import timedelta
from unittest import mock

from tests.flowkit import JUNIT_TOML, PLAN, SESSION, SPEC, FlowLab, plan_text
from tollgate_analysis import approvals, prblock, waivers
from tollgate_core import (VERSION, acts, clock, config, effects, events, git as core_git,
                           intents, phases, reviews)
from tollgate_flow import finishcheck, gitw, openpr, prstate

BRANCH = "tg/7-demo"
BOTH_OK = "tests.test_app::test_somma ok\ntests.test_app::test_zero ok\n"
SOMMA = "def somma(a, b):\n    return b + a\n"
TOML = JUNIT_TOML + '[scope]\nalways = ["tests/ids.txt"]\n'
REVIEWER = "tollgate:final-reviewer"
ISSUES = {"7": {"number": 7, "title": "Aggiungi export CSV", "body": "b", "state": "open", "labels": [],
                "author_association": "OWNER"}}


class GitwPushTest(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab(issue=7)
        self.addCleanup(self.fl.close)
        self.fl.commit("src/app.py", "def somma(a, b):\n    return b + a\n", "uno")
        self.head = core_git.head(self.fl.wt)

    def diverge(self):
        """Un commit sul ramo remoto che non è antenato di HEAD (qualcuno ha spinto a mano)."""
        self.fl.git("commit", "--allow-empty", "-qm", "altrove")
        sha = self.fl.git("rev-parse", "HEAD")
        self.fl.git("push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
        self.fl.git("reset", "-q", "--hard", "HEAD~1")      # il checkout principale torna com'era
        return sha

    def test_push_then_remote_sha(self):
        self.assertIsNone(gitw.remote_sha(self.fl.wt, BRANCH))
        gitw.push_sha(self.fl.wt, self.head, BRANCH, lease=None)
        self.assertEqual(gitw.remote_sha(self.fl.wt, BRANCH), self.head)
        self.assertIsNone(gitw.remote_sha(self.fl.wt, "tg/7-altro"))
        gitw.push_sha(self.fl.wt, self.head, BRANCH, lease=None)      # già allineato: nulla

    def test_non_fast_forward_needs_lease(self):
        remote = self.diverge()
        with self.assertRaises(gitw.GitWriteError):
            gitw.push_sha(self.fl.wt, self.head, BRANCH, lease=None)
        self.assertEqual(gitw.remote_sha(self.fl.wt, BRANCH), remote)
        with self.assertRaises(gitw.GitWriteError):
            gitw.push_sha(self.fl.wt, self.head, BRANCH, lease="0" * 40)
        self.assertEqual(gitw.remote_sha(self.fl.wt, BRANCH), remote)
        gitw.push_sha(self.fl.wt, self.head, BRANCH, lease=remote)
        self.assertEqual(gitw.remote_sha(self.fl.wt, BRANCH), self.head)

    def test_merge_base(self):
        base = self.fl.lab.base
        self.assertEqual(gitw.merge_base(self.fl.wt, "HEAD", base), base)
        self.assertEqual(gitw.merge_base(self.fl.wt, base, "HEAD"), base)
        self.assertIsNone(gitw.merge_base(self.fl.wt, "HEAD", "0" * 40))
        self.assertIsNone(gitw.merge_base(self.fl.wt, "HEAD", "nonesiste"))

    def test_is_ancestor(self):
        base = self.fl.lab.base
        self.assertTrue(gitw.is_ancestor(self.fl.wt, base, self.head))
        self.assertFalse(gitw.is_ancestor(self.fl.wt, self.head, base))
        self.assertTrue(gitw.is_ancestor(self.fl.wt, self.head, self.head))
        self.assertFalse(gitw.is_ancestor(self.fl.wt, "0" * 40, self.head))



def head(fl):
    return core_git.head(fl.wt)


def work(fl):
    return phases.get_work(fl.conn, fl.work)


def pr(number=1, state="OPEN", branch=BRANCH, **kw):
    d = {"number": number, "headRefName": branch, "state": state,
         "url": f"https://github.com/prova/flow/pull/{number}", "mergedAt": None,
         "body": "vecchio", "comments": []}
    d.update(kw)
    return d


class OpenCase(unittest.TestCase):
    def lab(self, *, toml=TOML, level="L1", cycle="ok", finish_act=True, prs=(), files=None,
            app=SOMMA, **gh):
        """Lavoro in fase review: piano registrato (L1), task chiusi, `finish check` verde sullo
        SHA di HEAD, ciclo di revisione `ok` su HEAD e l'atto `finish` registrato."""
        fl = FlowLab(issue=7, phase="plan" if level != "L0" else "execution", toml=toml,
                     level=level, files=files)
        self.addCleanup(fl.close)
        env = mock.patch.dict(os.environ, fl.env())
        env.start()
        self.addCleanup(env.stop)
        if level != "L0":
            fl.register_plan(tasks=1)
            fl.commit(PLAN, plan_text(tasks=1), "piano")
        fl.commit("tests/ids.txt", BOTH_OK, "ids")
        fl.commit("src/app.py", app, "somma")
        if level != "L0":
            fl.close_tasks()
        gh.setdefault("issues", ISSUES)
        fl.set_gh(prs=list(prs), **gh)
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        if cycle == "ok" and level != "L0":
            self.ok_cycle(fl)
        if finish_act:
            self.finish_act(fl)
        return fl

    def check(self, fl):
        return finishcheck.check(fl.ts.state, fl.wt, environ=fl.env(), now=fl.now)

    def facts(self, fl, **kw):
        cfg = config.load_config(fl.ts.state, fl.wt, work(fl)["work_base_sha"])
        kw.setdefault("now", fl.now + timedelta(hours=1))
        return openpr.facts(fl.conn, fl.ts.state, work(fl), cfg, fl.wt, head(fl), **kw)

    def ok_cycle(self, fl, findings=(), confirm=False):
        base = work(fl)["work_base_sha"]
        n = reviews.open_cycle(fl.conn, fl.work, sha=head(fl),
                               patch_id=core_git.patch_id(fl.wt, base, head(fl)),
                               code="c0de", reviewers=[REVIEWER], now=fl.now)
        reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="ok",
                           findings=list(findings), rejected=[], blocking_rules=set(),
                           known_rules=set(), now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, n, max_findings=15, now=fl.now)
        reviews.apply_verification(
            fl.conn, fl.work, n,
            [{"id": r["id"], "verification": "confirmed", "reason": "ok"} for r in rows],
            now=fl.now)
        return reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now), n

    def finish_act(self, fl, *, work_id=None, session=SESSION, at=None):
        return acts.record_act(fl.conn, type_="finish", typed_text="/tollgate:finish",
                               session=session, work=work_id or fl.work, head_sha=head(fl),
                               now=at or fl.now, ttl_minutes=10)

    def go(self, fl, *, minutes=30, **kw):
        kw.setdefault("environ", fl.env())
        return openpr.open_pr(fl.ts.state, fl.wt, now=fl.now + timedelta(minutes=minutes), **kw)

    def prs(self, fl):
        return json.loads(fl.gh_data.read_text())["prs"]

    def refusals(self, r):
        return [x for x in r.lines if x.startswith("rifiuto:")]

    def calls(self, fl, *words):
        return [c for c in fl.gh_calls() if c["argv"][:len(words)] == list(words)]

    def act_state(self, fl, act_id):
        return fl.conn.execute("SELECT state FROM acts WHERE act_id = ?", (act_id,)).fetchone()[0]


class OpenSuccessTest(OpenCase):
    def test_finish_act_after_long_review_opens_pr(self):
        fl = self.lab(finish_act=False)
        act_id = self.finish_act(fl)       # senza scadenza: la revisione dura 30 minuti
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        (created,) = self.prs(fl)
        self.assertEqual((created["title"], created["headRefName"], created["state"]),
                         ("#7 demo", BRANCH, "OPEN"))
        self.assertEqual(r.url, created["url"])
        self.assertTrue(created["body"].startswith("Closes #7\n"))
        w = work(fl)
        self.assertEqual((w["phase"], w["pr_number"], w["pr_url"]), ("pr_open", 1, r.url))
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))
        self.assertEqual(fl.events("pr_opened"), [{"pr": 1, "sha": head(fl)}])
        self.assertEqual(fl.events("pr_updated"), [])
        intent = fl.conn.execute("SELECT * FROM intents WHERE action = 'pr'").fetchone()
        self.assertEqual((intent["idempotency_key"], intent["state"]),
                         (f"pr:{fl.work}:{head(fl)}", "executed"))
        self.assertEqual(self.act_state(fl, act_id), "consumed")
        create = self.calls(fl, "pr", "create")[0]["argv"]
        self.assertEqual(create[create.index("--base") + 1], "main")
        self.assertTrue(any(x.startswith("PR #1") for x in r.lines))
        self.assertNotIn("export", " ".join(" ".join(c["argv"]) for c in fl.gh_calls()
                                            if c["argv"][:1] == ["pr"]))
        self.assertTrue(r.lines[-1].startswith("prossimo passo:"))

    def test_finish_act_valid_without_session_signal(self):
        fl = self.lab(finish_act=False)
        act_id = self.finish_act(fl)
        r = self.go(fl, argv=["finish", "open-pr"])      # nessun segnale della CLI
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(self.act_state(fl, act_id), "consumed")

    def test_finish_survives_clear(self):
        fl = self.lab(finish_act=False)
        self.finish_act(fl, session="sess-prima-del-clear")
        r = fl.cli("finish", "open-pr", cwd=fl.wt, session="sess-dopo-il-clear")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.prs(fl)), 1)
        self.assertEqual(work(fl)["phase"], "pr_open")

    def test_approve_pr_act_of_the_session_opens_pr(self):
        fl = self.lab(finish_act=False)
        act_id = acts.record_act(fl.conn, type_="approve", object_="pr", target=head(fl),
                                 typed_text="/tollgate:approve pr", session=SESSION,
                                 work=fl.work, head_sha=head(fl), now=clock.now(),
                                 ttl_minutes=10)
        r = fl.cli("finish", "open-pr", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.act_state(fl, act_id), "consumed")
        self.assertEqual(work(fl)["phase"], "pr_open")

    def test_l0_opens_without_review(self):
        fl = self.lab(level="L0")
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        self.assertEqual((block["level"], block["verdict"]["outcome"], block["verdict"]["cycles"]),
                         ("L0", None, 0))
        self.assertEqual(sorted(block["dod"]["items"]), ["guard_scope", "receipt"])

    def test_block_in_body_parses(self):
        fl = self.lab()
        acts.record_act(fl.conn, type_="approve", object_="level", target="L1",
                        typed_text="/tollgate:approve level L1 x", session=SESSION,
                        work=fl.work, now=fl.now, ttl_minutes=10)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        w = work(fl)
        self.assertEqual((block["issue"], block["head_sha"], block["plan_sha"]),
                         (7, head(fl), w["plan_sha"]))
        self.assertEqual(block["plan"], w["plan_path"])
        self.assertEqual(block["verdict"], {"outcome": "ok", "cycles": 1,
                                            "findings_confirmed": 0, "unverified": False})
        self.assertEqual(list(block), list(prblock.FIELDS))
        self.assertEqual((block["schema_version"], block["level"], block["gate_mode"]),
                         (1, "L1", "protected"))
        self.assertEqual(block["level_minimum"], "L1")
        self.assertEqual(block["waivers_file"], ".tollgate/waivers/7.toml")
        self.assertEqual({(a["type"], a["object"], a["state"]) for a in block["acts"]},
                         {("approve", "level", "pending")})
        self.assertEqual([x["command"] for x in block["receipts"]], ["verify"])
        self.assertEqual(block["receipts"][0]["state"], "green")
        self.assertTrue(all(v is True for k, v in block["dod"]["items"].items()
                            if k != "specialists"))
        self.assertEqual(block["dod"]["L"], "L1")
        self.assertEqual(block["spec_audit"], {"adversarial": None, "lens": None})
        self.assertEqual((block["blocks"], block["findings"], block["fix_rounds"],
                          block["components_off"], block["off_periods"], block["effects"]),
                         ([], [], {}, [], [], []))
        self.assertEqual(block["subagents"], {"count": 0, "tokens": 0})

    def test_notes_in_body_and_no_untrusted_text_in_arguments(self):
        fl = self.lab(cycle=None)
        hostile = "@utente ```\n--> <!-- x"
        self.ok_cycle(fl, findings=[{"severity": "minor", "confidence": 0.5, "file": "src/app.py",
                                     "line": 2, "rule": "R-9", "text": hostile}])
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        body = self.prs(fl)[0]["body"]
        self.assertIn("src/app.py:2", body)
        self.assertNotIn("@utente", body)
        self.assertEqual(body.count("<!-- tollgate"), 1)
        for call in fl.gh_calls():
            self.assertNotIn("utente", " ".join(call["argv"]))
        self.assertEqual(prblock.parse(body)["findings"][0]["severity"], "minor")


class OpenRefusalTest(OpenCase):
    def test_refused_without_finish_or_approve_pr(self):
        fl = self.lab(finish_act=False)
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertEqual(len(self.refusals(r)), 1, r.lines)
        self.assertIn("/tollgate:finish", r.lines[0])
        self.assertEqual(self.calls(fl, "pr", "create"), [])
        self.assertIsNone(gitw.remote_sha(fl.wt, BRANCH))
        self.assertEqual(work(fl)["phase"], "review")
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM intents").fetchone()[0], 0)

    def test_commit_after_finish_invalidates(self):
        fl = self.lab(finish_act=False)
        old = self.finish_act(fl)
        old_head = head(fl)
        fl.commit("tests/ids.txt", BOTH_OK + "\n", "ritocco")
        fl.git("reset", "-q", "--hard", old_head, repo=fl.wt)       # HEAD torna allo SHA dell'atto
        self.assertEqual(head(fl), old_head)
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("/tollgate:finish", " ".join(self.refusals(r)))
        self.assertEqual(self.act_state(fl, old), "pending")
        self.assertEqual(self.prs(fl), [])
        self.finish_act(fl, at=fl.now + timedelta(minutes=1))       # un atto nuovo vale
        self.assertEqual(self.go(fl, minutes=40).code, 0)

    def test_new_commit_after_finish_check_refuses(self):
        fl = self.lab()
        fl.commit("tests/ids.txt", BOTH_OK + "\n", "ritocco")
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertIn("finish check", " ".join(self.refusals(r)))
        self.assertEqual(self.prs(fl), [])

    def test_finish_of_other_work_refused(self):
        fl = self.lab(finish_act=False)
        other = phases.create_work(fl.conn, repo_key="github.com/prova/altro", issue=9,
                                   level="L1", now=fl.now)
        act_id = self.finish_act(fl, work_id=other)
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("/tollgate:finish", " ".join(self.refusals(r)))
        self.assertEqual(self.act_state(fl, act_id), "pending")
        self.assertEqual(self.prs(fl), [])

    def test_session_error_without_act_is_reported(self):
        fl = self.lab(finish_act=False)
        r = self.go(fl, argv=["finish", "open-pr"])
        self.assertEqual(r.code, 1)
        self.assertIn("sessione non riconosciuta", " ".join(r.lines))

    def test_refusals_collected(self):
        fl = self.lab()
        wf = waivers.WaiverFile(issue=7, branch=BRANCH, waivers=[waivers.Waiver(
            "w-7-1", "test", "tests/test_app.py", None, ["tests.test_app::test_zero"], "x", "y",
            "z")])
        path = fl.wt / waivers.path_for(7)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(waivers.dumps(wf))
        effects.request(fl.conn, key=effects.effect_key("git push", fl.work, head(fl)),
                        command="git push", work=fl.work, sha=head(fl), now=fl.now)
        fl.conn.execute("INSERT INTO findings (id, work, cycle, source, severity, file, line, "
                        "text, rule, blocking) VALUES ('f-1-9', ?, 1, 'x', 'minor', 'a.py', 1, "
                        "'t', 'R-1', 1)", (fl.work,))
        fl.conn.commit()
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        lines = self.refusals(r)
        self.assertEqual(len(lines), 3, r.lines)
        text = "\n".join(lines)
        for needle in ("w-7-1", "effetto", "f-1-9"):
            self.assertIn(needle, text)
        self.assertEqual(self.prs(fl), [])
        self.assertIsNone(gitw.remote_sha(fl.wt, BRANCH))

    def test_external_items_come_from_finish_report(self):
        fl = self.lab()
        report = json.loads(work(fl)["finish_report"])
        self.assertEqual({k: report["items"][k] for k in ("guard_scope", "must_have")},
                         {"guard_scope": True, "must_have": True})
        report["items"]["guard_scope"] = False
        report["items"]["must_have"] = None
        phases.set_finish(fl.conn, fl.work, head(fl), report, now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        text = "\n".join(self.refusals(r))
        self.assertIn("test-guard e scope", text)
        self.assertIn("must-have", text)
        self.assertEqual(self.prs(fl), [])

    def test_open_block_refused(self):
        fl = self.lab()
        phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "decidi tu", now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertIn("decidi tu", " ".join(r.lines))

    def test_task_not_done_refused(self):
        fl = self.lab()
        fl.conn.execute("UPDATE tasks SET state = 'review' WHERE work = ?", (fl.work,))
        fl.conn.commit()
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertTrue(any("task" in x.lower() and "approved" in x for x in self.refusals(r)),
                        r.lines)
        self.assertEqual(self.prs(fl), [])

    def test_no_ok_cycle_refused_and_unverified_review_allowed(self):
        fl = self.lab(cycle=None)
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertIn("review prepare", " ".join(self.refusals(r)))
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        self.assertTrue(block["verdict"]["unverified"])
        self.assertIn("non verificata", self.prs(fl)[0]["body"])

    def test_dod_component_off_does_not_block(self):
        fl = self.lab(toml=TOML + "[components]\ndefinition_of_done = false\n")
        fl.conn.execute("UPDATE tasks SET state = 'review' WHERE work = ?", (fl.work,))
        fl.conn.commit()
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertTrue(any(x.startswith("[no]") for x in r.lines), r.lines)
        self.assertEqual(len(self.prs(fl)), 1)
        self.assertIn("definition_of_done", self.prs(fl)[0]["body"])
        self.assertEqual(prblock.parse(self.prs(fl)[0]["body"])["components_off"],
                         ["definition_of_done"])

    def test_final_review_off_skips_cycle(self):
        fl = self.lab(toml=TOML + "[components]\nfinal_review = false\n", cycle=None)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        self.assertEqual((block["verdict"]["outcome"], block["verdict"]["cycles"]), (None, 0))

    def test_non_fast_forward_without_intent_refused(self):
        fl = self.lab()
        fl.git("commit", "--allow-empty", "-qm", "altrove")
        remote = fl.git("rev-parse", "HEAD")
        fl.git("push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
        fl.git("reset", "-q", "--hard", "HEAD~1")
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("antenato", " ".join(self.refusals(r)))
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), remote)
        self.assertEqual(self.prs(fl), [])
        self.assertEqual(self.calls(fl, "pr", "create"), [])
        # con un intento force_push autorizzato il push forzato (con lease) riesce, una volta
        intents.authorize_force(fl.conn, fl.work, reason="rebase", now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))
        self.assertFalse(intents.force_authorized(fl.conn, fl.work))

    def test_cli_update_flag_without_open_pr_refused(self):
        fl = self.lab(finish_act=False)
        acts.record_act(fl.conn, type_="approve", object_="pr", target=head(fl),
                        typed_text="/tollgate:approve pr", session=SESSION, work=fl.work,
                        head_sha=head(fl), now=clock.now(), ttl_minutes=10)
        r = fl.cli("finish", "open-pr", "--update", cwd=fl.wt)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--update", r.stdout)
        self.assertEqual(self.prs(fl), [])

    def test_update_without_open_pr_refused(self):
        fl = self.lab()
        r = self.go(fl, update=True)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("--update", " ".join(self.refusals(r)))
        self.assertEqual(self.prs(fl), [])
        self.assertIsNone(gitw.remote_sha(fl.wt, BRANCH))

    def test_closed_pr_not_cleared_refused_with_hint(self):
        fl = self.lab(prs=[pr(3, "CLOSED")])
        phases.set_pr(fl.conn, fl.work, 3, "https://x/pull/3", now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertIn(prstate.CLOSED_HINT, "\n".join(r.lines))
        self.assertEqual(len(self.prs(fl)), 1)
        self.assertEqual(work(fl)["phase"], "review")

    def test_merged_pr_closes_work_and_refuses(self):
        fl = self.lab(prs=[pr(3, "MERGED", mergedAt="2026-10-19T00:00:00Z")])
        phases.set_pr(fl.conn, fl.work, 3, "https://x/pull/3", now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertEqual(work(fl)["phase"], "closed")
        self.assertEqual(fl.events("merge_detected"), [{"pr": 3, "merged_at":
                                                         "2026-10-19T00:00:00Z"}])

    def test_gh_error_becomes_refusal_not_traceback(self):
        fl = self.lab(fail=["pr list"])
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertIn("pr list", " ".join(self.refusals(r)))
        self.assertIsNone(gitw.remote_sha(fl.wt, BRANCH))


class OpenUnverifiedTest(OpenCase):
    def test_unverified_review_still_stops_on_confirmed_blocker(self):
        fl = self.lab(cycle=None)
        base = work(fl)["work_base_sha"]
        for _ in range(7):
            n = reviews.open_cycle(fl.conn, fl.work, sha="vecchio", patch_id=None, code="c",
                                   reviewers=[REVIEWER], now=fl.now)
            reviews.supersede(fl.conn, fl.work, n, now=fl.now)
        n = reviews.open_cycle(fl.conn, fl.work, sha=head(fl),
                               patch_id=core_git.patch_id(fl.wt, base, head(fl)), code="c8",
                               reviewers=[REVIEWER], now=fl.now)
        self.assertEqual(n, 8)
        reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="needs_fix",
                           findings=[{"severity": "major", "confidence": 0.9, "file": "src/app.py",
                                      "line": 2, "rule": "R-1", "text": "manca lo zero"}],
                           rejected=[], blocking_rules=set(), known_rules=set(), now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, n, max_findings=15, now=fl.now)
        reviews.apply_verification(fl.conn, fl.work, n, [
            {"id": r["id"], "verification": "confirmed", "reason": "ok"} for r in rows],
            now=fl.now)
        reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now)
        self.assertEqual(self.check(fl).code, finishcheck.OK)       # di nuovo in review
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        self.finish_act(fl, at=fl.now + timedelta(seconds=1))
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("Nessun rilievo", " ".join(self.refusals(r)))
        self.assertEqual(self.prs(fl), [])
        reviews.set_decision(fl.conn, fl.work, "f-8-1", "dismissed", now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        body = self.prs(fl)[0]["body"]
        self.assertIn("non verificata", body)
        block = prblock.parse(body)
        self.assertTrue(block["verdict"]["unverified"])
        self.assertTrue(block["dod"]["items"]["findings"])

    def test_unverified_without_closed_cycle_passes_with_null_outcome(self):
        fl = self.lab(cycle=None)
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertIsNone(prblock.parse(self.prs(fl)[0]["body"])["verdict"]["outcome"])


class OpenOrphanFindingTest(OpenCase):
    """I-1: un rilievo senza esito di un ciclo superato, o di una revisione dichiarata non
    verificata, non blocca `open-pr` per sempre."""
    FINDING = {"severity": "major", "confidence": 0.9, "file": "src/app.py", "line": 2,
               "rule": "R-1", "text": "manca lo zero"}

    def open_with_finding(self, fl):
        base = work(fl)["work_base_sha"]
        n = reviews.open_cycle(fl.conn, fl.work, sha=head(fl),
                               patch_id=core_git.patch_id(fl.wt, base, head(fl)), code="c1",
                               reviewers=[REVIEWER], now=fl.now)
        stage = reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="needs_fix",
                                   findings=[self.FINDING], rejected=[], blocking_rules=set(),
                                   known_rules=set(), now=fl.now)
        self.assertEqual(stage, "verify")
        return n

    def verification(self, fl, fid):
        r = fl.conn.execute("SELECT verification, verification_reason FROM findings "
                            "WHERE work = ? AND id = ?", (fl.work, fid)).fetchone()
        return r[0], r[1]

    def test_finding_of_superseded_cycle_does_not_block(self):
        fl = self.lab(cycle=None, finish_act=False)
        n = self.open_with_finding(fl)
        fl.commit("src/app.py", SOMMA + "\n\n# dopo\n", "dopo")
        reviews.supersede(fl.conn, fl.work, n, now=fl.now)
        self.assertEqual(self.verification(fl, "f-1-1"), ("unverified", "ciclo superato"))
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.ok_cycle(fl)
        self.finish_act(fl, at=fl.now + timedelta(seconds=1))
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(len(self.prs(fl)), 1)

    def test_unverified_findings_are_listed_in_the_body(self):
        fl = self.lab(cycle=None, finish_act=False)
        n = self.open_with_finding(fl)
        reviews.mark_unverified(fl.conn, fl.work, n, reviews.UNVERIFIED_REVIEW_REASON, now=fl.now)
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now)
        self.finish_act(fl, at=fl.now + timedelta(seconds=1))
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        body = self.prs(fl)[0]["body"]
        self.assertIn("## Rilievi non verificati", body)
        self.assertIn("manca lo zero", body)
        self.assertIn("revisione non verificata", body)

    def test_unverified_review_marks_findings_without_outcome(self):
        fl = self.lab(cycle=None, finish_act=False)
        for _ in range(7):
            k = reviews.open_cycle(fl.conn, fl.work, sha="vecchio", patch_id=None, code="c",
                                   reviewers=[REVIEWER], now=fl.now)
            reviews.supersede(fl.conn, fl.work, k, now=fl.now)
        n = self.open_with_finding(fl)
        self.assertEqual(n, 8)
        self.assertIsNone(self.verification(fl, "f-8-1")[0])
        reviews.mark_unverified(fl.conn, fl.work, n, reviews.UNVERIFIED_REVIEW_REASON,
                                now=fl.now)
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        self.finish_act(fl, at=fl.now + timedelta(seconds=1))
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)


class OpenForceTest(OpenCase):
    def diverged_lab(self):
        fl = self.lab()
        fl.git("commit", "--allow-empty", "-qm", "altrove")
        fl.git("push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
        fl.git("reset", "-q", "--hard", "HEAD~1")
        key = intents.authorize_force(fl.conn, fl.work, reason="rebase", now=fl.now)
        return fl, key

    def force_state(self, fl, key):
        return fl.conn.execute("SELECT state FROM intents WHERE idempotency_key = ?",
                               (key,)).fetchone()[0]

    def test_failed_push_keeps_force_authorization(self):
        fl, key = self.diverged_lab()
        with mock.patch.object(gitw, "push_sha", side_effect=gitw.GitWriteError("rete assente")):
            r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertEqual(self.force_state(fl, key), "authorized")
        self.assertEqual(self.prs(fl), [])
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(self.force_state(fl, key), "used")
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))


class OpenForkPrTest(OpenCase):
    """I-3: una PR da fork con lo stesso nome di ramo non è la nostra."""

    def test_fork_pr_with_same_branch_is_left_alone(self):
        fl = self.lab(prs=[pr(1, isCrossRepository=True, headRefOid="f" * 40,
                              body="corpo del fork")])
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(self.calls(fl, "pr", "edit"), [])
        by_number = {p["number"]: p for p in self.prs(fl)}
        self.assertEqual(by_number[1]["body"], "corpo del fork")
        self.assertIn("tollgate", by_number[2]["body"])
        self.assertEqual(work(fl)["pr_number"], 2)

    def test_pr_not_at_pushed_sha_is_not_edited(self):
        fl = self.lab(prs=[pr(1, headRefOid="e" * 40)])
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("#1", " ".join(self.refusals(r)))
        self.assertEqual(self.calls(fl, "pr", "edit"), [])
        self.assertEqual(self.prs(fl)[0]["body"], "vecchio")
        self.assertIsNone(work(fl)["pr_number"])


class OpenResumeTest(OpenCase):
    def test_interrupted_after_push_no_duplicate_pr(self):
        fl = self.lab(fail=["pr create"])
        act_id = self.finish_act(fl)
        r = self.go(fl)
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("pr create", " ".join(r.lines))
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))       # il push c'è stato
        self.assertEqual(self.prs(fl), [])
        self.assertEqual(self.act_state(fl, act_id), "pending")          # atto ancora valido
        self.assertEqual(work(fl)["phase"], "review")
        key = f"pr:{fl.work}:{head(fl)}"
        self.assertEqual(fl.conn.execute("SELECT state FROM intents WHERE idempotency_key = ?",
                                         (key,)).fetchone()[0], "requested")
        fl.set_gh(prs=[], issues=ISSUES)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(len(self.prs(fl)), 1)
        self.assertEqual(self.act_state(fl, act_id), "consumed")

    def test_pr_created_but_process_died_edits_instead_of_creating(self):
        fl = self.lab(prs=[pr(1)])
        fl.git("push", "-q", "origin", f"{head(fl)}:refs/heads/{BRANCH}", repo=fl.wt)
        intents.request(fl.conn, work=fl.work, action="pr", key=f"pr:{fl.work}:{head(fl)}",
                        data={"sha": head(fl)}, now=fl.now)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(self.calls(fl, "pr", "create"), [])
        self.assertEqual(len(self.calls(fl, "pr", "edit")), 1)
        (only,) = self.prs(fl)
        self.assertTrue(only["body"].startswith("Closes #7"))
        w = work(fl)
        self.assertEqual((w["phase"], w["pr_number"]), ("pr_open", 1))
        self.assertEqual(fl.events("pr_opened"), [{"pr": 1, "sha": head(fl)}])

    def test_died_after_phase_change_resumes_from_pr_open(self):
        fl = self.lab()
        act_id = self.finish_act(fl)
        self.assertEqual(self.go(fl).code, 0)
        # simula la morte dopo `pr_open` e prima di intento eseguito e consumo dell'atto
        fl.conn.execute("UPDATE intents SET state = 'requested' WHERE action = 'pr'")
        fl.conn.execute("UPDATE acts SET state = 'pending', consumed_at = NULL "
                        "WHERE act_id = ?", (act_id,))
        fl.conn.commit()
        r = self.go(fl, minutes=40)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(len(self.prs(fl)), 1)
        self.assertEqual(len(self.calls(fl, "pr", "create")), 1)
        self.assertEqual(self.act_state(fl, act_id), "consumed")
        self.assertEqual(work(fl)["phase"], "pr_open")

    def test_pr_open_without_pending_intent_refused(self):
        fl = self.lab()
        self.assertEqual(self.go(fl).code, 0)
        self.finish_act(fl, at=fl.now + timedelta(minutes=1))
        r = self.go(fl, minutes=60)
        self.assertEqual(r.code, 1)
        self.assertIn("pr_open", " ".join(self.refusals(r)))

    def test_update_edits_open_pr_and_emits_pr_updated(self):
        fl = self.lab(prs=[pr(2)])
        phases.set_pr(fl.conn, fl.work, 2, "https://github.com/prova/flow/pull/2", now=fl.now)
        r = self.go(fl, update=True)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(self.calls(fl, "pr", "create"), [])
        self.assertEqual(fl.events("pr_updated"), [{"pr": 2, "sha": head(fl)}])
        self.assertEqual(fl.events("pr_opened"), [])
        self.assertTrue(self.prs(fl)[0]["body"].startswith("Closes #7"))

    def test_via_sync_replaces_finish_act(self):
        fl = self.lab(finish_act=False, prs=[pr(2)])
        phases.set_pr(fl.conn, fl.work, 2, "https://github.com/prova/flow/pull/2", now=fl.now)
        r = self.go(fl, update=True, via_sync="a-99")
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(len(self.calls(fl, "pr", "edit")), 1)
        self.assertEqual(work(fl)["phase"], "pr_open")

    def test_closed_pr_then_confirm_creates_new_pr(self):
        fl = self.lab(prs=[pr(1, "CLOSED")])
        self.assertIsNone(work(fl)["pr_number"])        # `start --confirm` ha azzerato il numero
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(len(self.calls(fl, "pr", "create")), 1)
        self.assertEqual(self.calls(fl, "pr", "edit"), [])
        self.assertEqual([p["number"] for p in self.prs(fl)], [1, 2])
        self.assertEqual(work(fl)["pr_number"], 2)

    def test_open_pr_after_needs_fix_then_ok_cycle(self):
        fl = self.lab(cycle=None)
        base = work(fl)["work_base_sha"]
        n = reviews.open_cycle(fl.conn, fl.work, sha=head(fl),
                               patch_id=core_git.patch_id(fl.wt, base, head(fl)), code="c1",
                               reviewers=[REVIEWER], now=fl.now)
        reviews.add_report(fl.conn, fl.work, n, source=REVIEWER, outcome="needs_fix",
                           findings=[{"severity": "major", "confidence": 0.9, "file": "src/app.py",
                                      "line": 2, "rule": "R-1", "text": "manca lo zero"}],
                           rejected=[], blocking_rules=set(), known_rules=set(), now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, n, max_findings=15, now=fl.now)
        reviews.apply_verification(fl.conn, fl.work, n, [
            {"id": r["id"], "verification": "confirmed", "reason": "ok"} for r in rows],
            now=fl.now)
        self.assertEqual(reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now),
                         "needs_fix")
        self.assertEqual(work(fl)["phase"], "execution")
        fl.conn.execute("INSERT INTO tasks (work, number, kind, source, state, verdict) "
                        "VALUES (?, 2, 'fix', 'cycle:1', 'done', 'approved')", (fl.work,))
        fl.conn.commit()
        fl.commit("src/app.py", SOMMA + "\n", "correzione")
        self.assertEqual(self.check(fl).code, finishcheck.OK)
        self.assertEqual(self.ok_cycle(fl), ("ok", 2))
        self.finish_act(fl)
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        self.assertEqual((block["verdict"]["cycles"], block["verdict"]["outcome"]), (2, "ok"))
        self.assertEqual([f["id"] for f in block["findings"]], ["f-1-1"])
        self.assertTrue(block["dod"]["items"]["findings"])
        self.assertEqual(block["fix_rounds"], {})


class FactsTest(OpenCase):
    def test_facts_keys_match_block_fields(self):
        fl = self.lab()
        data = self.facts(fl)
        self.assertEqual(set(data), set(prblock.FIELDS))
        self.assertEqual((data["head_sha"], data["tollgate_version"]), (head(fl), VERSION))
        self.assertEqual((data["verdict"]["outcome"], data["verdict"]["cycles"]), ("ok", 1))
        self.assertEqual(self.facts(fl, cycle=None)["verdict"]["outcome"], None)

    def test_level_minimum_from_issue_labels(self):
        fl = self.lab(issues={"7": dict(ISSUES["7"], labels=[{"name": "security"}])})
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        self.assertEqual((block["level"], block["level_minimum"]), ("L1", "L2"))

    def test_unreadable_issue_labels_warn_and_use_diff_only(self):
        fl = self.lab(issues={})
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertTrue(any(x.startswith("avviso:") and "level_minimum" in x for x in r.lines))
        self.assertEqual(prblock.parse(self.prs(fl)[0]["body"])["level_minimum"], "L1")

    def test_counters_and_reviews_dirs(self):
        fl = self.lab()
        fl.write_spec()
        fl.approve_spec_file()                  # il lavoro ha spec_path: le cartelle 18.1 valgono
        fl.commit("docs/superpowers/reviews/7/spec-approval.md", approvals.render_approval(
            {"kind": "spec-approval", "path": SPEC, "sha": core_git.blob_at(fl.wt, "HEAD", SPEC),
             "adversarial": "closed", "lens": "suspended"}), "approvazione")
        for n in (1, 2):
            fl.conn.execute("INSERT INTO subagents (id, work, tokens) VALUES (?, ?, 100)",
                            (f"ag-{n}", fl.work))
        fl.conn.execute("UPDATE tasks SET fix_rounds = 2 WHERE work = ? AND number = 1",
                        (fl.work,))
        fl.conn.commit()
        effects.request(fl.conn, key="k" * 8, command="git push", work=fl.work, sha=head(fl),
                        now=fl.now)
        effects.mark_executed(fl.conn, key="k" * 8, act_id="a-1", now=fl.now)
        events.record_event(fl.conn, "off", {}, now=fl.now)
        data = self.facts(fl)
        self.assertEqual(data["spec_reviews_dir"], "docs/superpowers/reviews/7/")
        self.assertIsNone(data["plan_reviews_dir"])
        self.assertEqual(data["spec_audit"], {"adversarial": "closed", "lens": "suspended"})
        self.assertEqual(data["subagents"], {"count": 2, "tokens": 200})
        self.assertEqual(data["fix_rounds"], {"1": 2})
        self.assertEqual(data["effects"], [{"command_hash": "k" * 8, "at": clock.fmt(fl.now)}])
        (period,) = data["off_periods"]
        self.assertIsNone(period["to"])


class L2FactsTest(OpenCase):
    """Le cartelle 18.1 e `spec_audit` dall'approvazione trovata (decisione 15)."""

    def spec_approval(self, fl, issue, sha=None, **extra):
        fields = {"kind": "spec-approval", "path": SPEC, "slices": 3,
                  "sha": sha or core_git.blob_at(fl.wt, "HEAD", SPEC), **extra}
        fl.commit(approvals.approval_paths(issue)[0], approvals.render_approval(fields),
                  f"approvazione {issue}")

    def test_without_spec_path_dirs_and_spec_audit_are_null(self):
        fl = self.lab()
        fl.commit("docs/superpowers/reviews/7/spec-approval.md", "---\nkind: spec-approval\n"
                  f"path: {SPEC}\nsha: abc\nadversarial: closed\n---\n", "approvazione orfana")
        data = self.facts(fl)
        self.assertIsNone(data["spec_reviews_dir"])
        self.assertEqual(data["spec_audit"], {"adversarial": None, "lens": None})

    def test_dirs_and_spec_audit_from_located_approval(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        phases.set_spec_path(fl.conn, fl.work, SPEC, now=fl.now)
        self.spec_approval(fl, 7, adversarial="closed", lens="suspended")
        fl.approve_plan_file()
        data = self.facts(fl)
        self.assertEqual(data["spec_reviews_dir"], "docs/superpowers/reviews/7/")
        self.assertEqual(data["plan_reviews_dir"], "docs/superpowers/reviews/7/")
        self.assertEqual(data["spec_audit"], {"adversarial": "closed", "lens": "suspended"})
        self.assertEqual(data["spec"], SPEC)

    def test_later_slice_points_to_the_first_slice_folder(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        phases.set_spec_path(fl.conn, fl.work, SPEC, now=fl.now)
        self.spec_approval(fl, 3, adversarial="closed", lens="closed")
        data = self.facts(fl)
        self.assertEqual(data["spec_reviews_dir"], "docs/superpowers/reviews/3/")
        self.assertIsNone(data["plan_reviews_dir"])         # il piano non è ancora approvato
        self.assertEqual(data["spec_audit"], {"adversarial": "closed", "lens": "closed"})
        fl.approve_plan_file()
        data = self.facts(fl)
        self.assertEqual(data["plan_reviews_dir"], "docs/superpowers/reviews/7/")
        self.assertEqual(data["spec_reviews_dir"], "docs/superpowers/reviews/3/")

    def test_approval_with_other_sha_in_other_issue_is_not_the_spec_approval(self):
        fl = self.lab()
        fl.write_spec(slices=3)
        phases.set_spec_path(fl.conn, fl.work, SPEC, now=fl.now)
        self.spec_approval(fl, 3, sha="0" * 40, adversarial="closed", lens="closed")
        data = self.facts(fl)
        self.assertIsNone(data["spec_reviews_dir"])
        self.assertEqual(data["spec_audit"], {"adversarial": None, "lens": None})


class OpenReviewMatchTest(OpenCase):
    def test_cycle_with_same_patch_id_counts_after_rebase(self):
        fl = self.lab()
        fl.conn.execute("UPDATE review_cycles SET sha = 'vecchio' WHERE work = ?", (fl.work,))
        fl.conn.commit()
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        block = prblock.parse(self.prs(fl)[0]["body"])
        self.assertEqual(block["verdict"]["outcome"], "ok")

    def test_cycle_with_other_patch_id_refused(self):
        fl = self.lab()
        fl.conn.execute("UPDATE review_cycles SET sha = 'vecchio', patch_id = 'altro' "
                        "WHERE work = ?", (fl.work,))
        fl.conn.commit()
        r = self.go(fl)
        self.assertEqual(r.code, 1)
        self.assertIn("review prepare", " ".join(self.refusals(r)))

    def test_open_cycle_not_closed_refused(self):
        fl = self.lab(cycle=None)
        reviews.open_cycle(fl.conn, fl.work, sha=head(fl), patch_id=None, code="c",
                           reviewers=[REVIEWER], now=fl.now)
        self.assertEqual(self.go(fl).code, 1)


if __name__ == "__main__":
    unittest.main()
