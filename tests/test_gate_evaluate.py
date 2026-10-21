import dataclasses
import unittest

from tests.flowkit import PLAN, plan_text
from tests.gatekit import BRANCH, DEFAULT_IDS, GATE_TOML, GateLab
from tollgate_analysis import waivers
from tollgate_gate import attention
from tollgate_gate.evaluate import base_path, evaluate
from tollgate_gate.model import BASE_FROM_RUN, CommandResult, Evaluation, Item

NO_REPORT_TOML = """schema_version = 1
[gate]
mode = "protected"
[commands]
verify = "true"
gate = ["verify"]
"""
ALLOW_NO_TESTS_TOML = NO_REPORT_TOML + "[project]\nallow_no_tests = true\n"
PROFILE_TOML = GATE_TOML + """
[profiles.web]
paths = ["web/**"]
gate = ["test"]
[profiles.web.commands]
test = "true"
"""
SOMMA, ZERO = DEFAULT_IDS


def keys(items, family=None):
    return [i.key for i in items if family is None or i.family == family]


def wtext(*items, issue=7, branch=BRANCH):
    """Il file delle deroghe; `items` sono `(tipo, file, pattern, tests)`."""
    out = [waivers.Waiver(f"w-{issue}-{n}", t, f, p, list(tests), "scelta", "perché", "costo")
           for n, (t, f, p, tests) in enumerate(items, 1)]
    return waivers.dumps(waivers.WaiverFile(issue, branch, out))


class LabCase(unittest.TestCase):
    toml = GATE_TOML
    plan = None

    def setUp(self):
        self.lab = GateLab(toml=self.toml, plan=self.plan)
        self.addCleanup(self.lab.close)

    def run_gate(self, **override):
        return evaluate(self.lab.inputs(**override))

    def local_like_pr(self, ref="fix/x"):
        """Una PR manuale: ramo non `tg/*`, nessun blocco."""
        return self.lab.with_pr(head_ref=ref, body="")


class CommandsTest(LabCase):
    def verify(self, state, exit_code, junit=None):
        return [CommandResult("verify", state, exit_code, None, junit)]

    def test_green_run_has_no_red(self):
        ev = self.run_gate()
        self.assertEqual((ev.red, ev.errors, ev.verdict_state), ([], [], "success"))
        self.assertEqual(ev.attention, [])

    def test_red_empty_uncounted_unverified(self):
        cases = {
            "command_red": self.verify("red", 1, self.lab.junit(DEFAULT_IDS)),
            "command_empty": self.verify("empty", 0, self.lab.junit([])),
            "command_unverified": self.verify("unverified", None),
        }
        for want, commands in cases.items():
            with self.subTest(want):
                ev = self.run_gate(commands=commands)
                self.assertIn(want, keys(ev.red, "commands"))
                self.assertEqual(ev.verdict_state, "failure")

    def test_uncounted_is_red_without_allow(self):
        lab = GateLab(toml=NO_REPORT_TOML)
        self.addCleanup(lab.close)
        ev = evaluate(lab.inputs(commands=self.verify("uncounted", 0)))
        self.assertEqual(keys(ev.red, "commands"), ["command_uncounted"])

    def test_allow_no_tests_counts_empty_and_uncounted_with_attention(self):
        lab = GateLab(toml=ALLOW_NO_TESTS_TOML)
        self.addCleanup(lab.close)
        for state, junit in (("empty", lab.junit([])), ("uncounted", None)):
            with self.subTest(state):
                ev = evaluate(lab.inputs(commands=self.verify(state, 0, junit), block=None,
                                         pr=self.local_like_pr_of(lab)))
                self.assertEqual(keys(ev.red, "commands"), [])
                self.assertIn("no_tests_counted", keys(ev.attention))
                self.assertEqual(ev.attention_state, "failure")

    def local_like_pr_of(self, lab):
        return lab.with_pr(head_ref="fix/x", body="")

    def test_allow_no_tests_with_green_receipts_is_info(self):
        lab = GateLab(toml=ALLOW_NO_TESTS_TOML)
        self.addCleanup(lab.close)
        ev = evaluate(lab.inputs(commands=self.verify("green", 0, lab.junit(DEFAULT_IDS))))
        self.assertEqual(keys(ev.attention), ["allow_no_tests"])
        self.assertEqual(ev.attention_state, "success")

    def test_allow_no_tests_does_not_rescue_a_failed_exit(self):
        lab = GateLab(toml=ALLOW_NO_TESTS_TOML)
        self.addCleanup(lab.close)
        ev = evaluate(lab.inputs(commands=self.verify("empty", 1, lab.junit([]))))
        self.assertEqual(keys(ev.red, "commands"), ["command_red"])

    def test_unverified_green_with_declared_act_and_attention(self):
        block = self.lab.block(acts=[{"act_id": "a-1", "type": "approve",
                                      "object": "unverified-tests", "target": None,
                                      "at": "2026-10-21T10:00:00Z", "state": "consumed"}])
        ev = self.run_gate(block=block, commands=self.verify("unverified", None))
        self.assertEqual(keys(ev.red, "commands"), [])
        self.assertIn("unverified_tests", keys(ev.attention))
        self.assertEqual(ev.attention_state, "failure")

    def test_other_act_does_not_approve_unverified(self):
        block = self.lab.block(acts=[{"act_id": "a-1", "type": "approve", "object": "waiver",
                                      "target": "w-7-1", "at": "x"}])
        ev = self.run_gate(block=block, commands=self.verify("unverified", None))
        self.assertEqual(keys(ev.red, "commands"), ["command_unverified"])

    def test_or_true_with_failure_is_red(self):
        failed = self.lab.junit(DEFAULT_IDS, ids_failed=[SOMMA])
        ev = self.run_gate(commands=[CommandResult("verify", "green", 0, 2, failed)])
        self.assertEqual(keys(ev.red, "commands"), ["command_red"])

    def test_stated_green_is_recomputed_from_exit_and_report(self):
        ev = self.run_gate(commands=[CommandResult("verify", "green", 1,
                                                   2, self.lab.junit(DEFAULT_IDS))])
        self.assertEqual(keys(ev.red, "commands"), ["command_red"])
        ev = self.run_gate(commands=[CommandResult("verify", "green", 0, None, None)])
        self.assertEqual(keys(ev.red, "commands"), ["command_red"])   # report assente

    def test_setup_red_is_a_red_command(self):
        lab = GateLab(toml=PROFILE_TOML)
        self.addCleanup(lab.close)
        for name in ("setup", "profile:web:setup"):
            with self.subTest(name):
                commands = lab.inputs().commands + [CommandResult(name, "red", 1, None, None)]
                ev = evaluate(lab.inputs(commands=commands))
                self.assertEqual(keys(ev.red, "commands"), ["command_red"])
                self.assertIn(name, ev.red[0].text)

    def test_artifact_names_never_reach_item_text(self):
        hostile = "profile:inventato:setup"
        for name in (hostile, "evil:setup", "`@x` setup"):
            with self.subTest(name):
                commands = self.lab.inputs().commands + [CommandResult(name, "red", 1, None,
                                                                       None)]
                ev = self.run_gate(commands=commands)
                for item in ev.red + ev.attention:
                    self.assertNotIn(name, item.text)
                self.assertNotIn(name, " ".join(i.text for i in ev.red))

    def test_missing_result_is_red(self):
        ev = self.run_gate(commands=[])
        self.assertEqual(keys(ev.red, "commands"), ["command_missing"])

    def test_no_results_on_github_is_error_but_not_local(self):
        ev = self.run_gate(commands=None)
        self.assertEqual(ev.verdict_state, "error")
        ev = self.run_gate(commands=None, where="local", pr=None, base_ids=None)
        self.assertEqual((ev.errors, keys(ev.red, "commands")), ([], []))


class ProfileCommandsTest(LabCase):
    toml = PROFILE_TOML

    def web_result(self, ids=()):
        return CommandResult("profile:web:test", "green", 0, len(ids), self.lab.junit(ids))

    def test_profile_gate_command_required(self):
        self.lab.commit("web/app.js", "x\n", "web")
        ev = self.run_gate()
        missing = [i for i in ev.red if i.key == "command_missing"]
        self.assertEqual(len(missing), 1)
        self.assertIn("profile:web:test", missing[0].text)
        commands = self.lab.inputs().commands + [self.web_result(["web.t::ok"])]
        self.assertEqual(keys(self.run_gate(commands=commands).red, "commands"), [])

    def test_profile_command_not_required_outside_its_paths(self):
        self.assertEqual(keys(self.run_gate().red, "commands"), [])


class BaseIdsTest(LabCase):
    def test_missing_base_id_is_red(self):
        ev = self.run_gate(base_ids={"verify": {SOMMA, ZERO, "tests.test_app::test_extra"}})
        self.assertEqual(keys(ev.red, "base_ids"), ["base_id_missing"])
        self.assertIn("tests.test_app::test_extra", ev.red[0].data)
        self.assertNotIn("tests.test_app::test_extra", ev.red[0].text)

    def test_all_base_ids_run_is_green(self):
        self.assertEqual(keys(self.run_gate().red, "base_ids"), [])

    def test_violations_grouped_by_path(self):
        ids = {"web/a.test.js::uno", "web/a.test.js::due", "tests.test_b.TestB::tre"}
        ev = self.run_gate(base_ids={"verify": set(DEFAULT_IDS) | ids})
        paths = sorted(i.data.split(":")[0] for i in ev.red if i.family == "base_ids")
        self.assertEqual(paths, ["tests/test_b.py", "web/a.test.js"])

    def test_base_path(self):
        self.assertEqual(base_path("tests.test_app::test_somma"), "tests/test_app.py")
        self.assertEqual(base_path("tests.test_app.TestApp::test_a"), "tests/test_app.py")
        self.assertEqual(base_path("web/src/a.test.ts::suite uno"), "web/src/a.test.ts")
        self.assertEqual(base_path("suite"), "suite.py")

    def test_inactive_profile_ids_not_compared(self):
        lab = GateLab(toml=PROFILE_TOML)
        self.addCleanup(lab.close)
        base = {"verify": set(DEFAULT_IDS), "profile:web:test": {"web.t::uno", "web.t::due"}}
        ev = evaluate(lab.inputs(base_ids=base))
        self.assertEqual(keys(ev.red), [])
        lab.commit("web/app.js", "x\n", "web")
        web = CommandResult("profile:web:test", "green", 0, 1, lab.junit(["web.t::uno"]))
        ev = evaluate(lab.inputs(base_ids=base, commands=lab.inputs().commands + [web]))
        self.assertEqual(keys(ev.red, "base_ids"), ["base_id_missing"])
        self.assertIn("web.t::due", ev.red[0].data)

    def test_skipped_in_head_is_missing(self):
        junit = self.lab.junit([SOMMA], ids_skipped=[ZERO])
        ev = self.run_gate(commands=[CommandResult("verify", "green", 0, 1, junit)])
        self.assertIn(ZERO, ev.red[0].data)
        self.assertEqual(keys(ev.red, "base_ids"), ["base_id_missing"])

    def test_test_waiver_covers_only_with_all_ids(self):
        junit = self.lab.junit([])
        commands = [CommandResult("verify", "green", 0, 0, junit)]
        partial = wtext(("test", "tests/test_app.py", None, [SOMMA]))
        ev = self.run_gate(commands=commands, waiver_text=partial)
        self.assertEqual(keys(ev.red, "base_ids"), ["base_id_missing"])
        full = wtext(("test", "tests/test_app.py", None, [SOMMA, ZERO]))
        ev = self.run_gate(commands=commands, waiver_text=full)
        self.assertEqual(keys(ev.red, "base_ids"), [])
        self.assertIn("waiver_test", keys(ev.attention))

    def test_component_off_skips(self):
        toml = GATE_TOML + "[components]\nbase_test_ids = false\n"
        lab = GateLab(toml=toml)
        self.addCleanup(lab.close)
        ev = evaluate(lab.inputs(base_ids={"verify": {"tests.x::falso"}}))
        self.assertEqual(keys(ev.red, "base_ids"), [])
        self.assertEqual(ev.errors, [])
        self.assertIn("components_off", keys(ev.attention))
        self.assertIn("base_test_ids", ev.attention[0].text)
        self.assertEqual(keys(evaluate(lab.inputs(base_ids=None)).red), [])

    def test_local_has_no_base_ids(self):
        ev = self.run_gate(where="local", pr=None, base_ids=None, base_ids_source=None)
        self.assertEqual((ev.red, ev.errors), ([], []))
        ev = self.run_gate(where="local", pr=None, base_ids={"verify": {"tests.x::falso"}})
        self.assertEqual(keys(ev.red, "base_ids"), [])

    def test_missing_base_ids_on_github_is_error(self):
        ev = self.run_gate(base_ids=None)
        self.assertEqual((ev.verdict_state, ev.red), ("error", []))

    def test_base_ids_from_run_is_read_attention(self):
        ev = self.run_gate(base_ids_source=BASE_FROM_RUN)
        self.assertEqual(keys(ev.attention), ["base_ids_from_run"])
        self.assertEqual(ev.attention_state, "failure")

    def test_base_failing_on_head_is_info(self):
        junit = self.lab.junit(DEFAULT_IDS, ids_failed=[SOMMA])
        ev = self.run_gate(commands=[CommandResult("verify", "red", 1, 2, junit)])
        self.assertIn("base_failing_on_head", keys(ev.attention))
        self.assertEqual(ev.attention_state, "success")


class DiffTest(LabCase):
    def test_testguard_on_every_pr(self):
        self.lab.delete("tests/test_app.py")
        self.lab.commit("tests/test_new.py", "import pytest\n\n\n@pytest.mark.skip\n"
                        "def test_n():\n    assert 1\n", "salta")
        for name, override in (("tg", {}), ("manual", {"pr": self.local_like_pr(),
                                                       "block": None})):
            with self.subTest(name):
                ev = self.run_gate(**override)
                self.assertTrue({"test_deleted", "skip_added"} <= set(keys(ev.red, "diff")))

    def test_out_of_scope_tg_only(self):
        self.lab.commit("src/stray.py", "x = 1\n", "fuori scope")
        ev = self.run_gate()
        self.assertEqual(keys(ev.red, "diff"), ["out_of_scope"])
        self.assertEqual(ev.red[0].data, "src/stray.py")
        self.assertNotIn("src/stray.py", ev.red[0].text)
        ev = self.run_gate(pr=self.local_like_pr(), block=None)
        self.assertEqual(keys(ev.red, "diff"), [])

    def test_in_scope_files_and_registered_plan_are_clean(self):
        self.lab.commit("src/app.py", "y = 2\n", "in scope")
        self.lab.commit("docs/uso.md", "uso\n", "in scope")
        ev = self.run_gate()
        self.assertEqual((ev.red, ev.attention), ([], []))

    def test_plan_changed_after_registration(self):
        changed = plan_text(task2="- Create: `docs/uso.md`\n- Create: `src/extra.py`")
        self.lab.commit(PLAN, changed, "piano cambiato")
        self.lab.commit("src/extra.py", "x = 1\n", "il file in più")
        ev = self.run_gate()
        self.assertEqual([(i.key, i.data) for i in ev.red if i.family == "diff"],
                         [("out_of_scope", "src/extra.py")])
        self.assertEqual(keys(ev.attention), ["plan_changed"])
        diff = ev.attention[0].data
        self.assertIn("+- Create: `src/extra.py`", diff)
        self.assertTrue(diff.startswith("--- registrato\n+++ testa"))
        self.assertEqual(ev.attention_state, "failure")

    def test_plan_changed_is_scope_violation_in_local(self):
        changed = plan_text(task2="- Create: `docs/uso.md`\n- Create: `src/extra.py`")
        self.lab.commit(PLAN, changed, "piano cambiato")
        self.lab.commit("src/extra.py", "x = 1\n", "il file in più")
        ev = self.run_gate(where="local", pr=None, base_ids=None)
        self.assertEqual(sorted(i.data for i in ev.red if i.family == "diff"),
                         [PLAN, "src/extra.py"])
        self.assertNotIn("plan_changed", keys(ev.attention))

    def test_plan_diff_is_capped(self):
        many = plan_text() + "".join(f"riga {n}\n" for n in range(500))
        self.lab.commit(PLAN, many, "piano molto cambiato")
        diff = self.run_gate().attention[0].data.splitlines()
        self.assertEqual(len(diff), 201)
        self.assertEqual(diff[-1], "…")

    def test_plan_sha_absent_is_red(self):
        for plan_sha in (None, "0" * 40):
            with self.subTest(plan_sha):
                ev = self.run_gate(block=self.lab.block(plan_sha=plan_sha))
                self.assertIn("plan_sha_absent", keys(ev.red, "diff"))
        ev = self.run_gate(block=self.lab.block(level="L2", plan_sha=None))
        self.assertIn("plan_sha_absent", keys(ev.red, "diff"))

    def test_blob_outside_history_is_not_a_registered_plan(self):
        import subprocess
        loose = subprocess.run(
            ["git", "-C", str(self.lab.repo), "hash-object", "-w", "--stdin"],
            input=plan_text().encode() + b"altro\n", capture_output=True,
            check=True).stdout.decode().strip()
        ev = self.run_gate(block=self.lab.block(plan_sha=loose))
        self.assertIn("plan_sha_absent", keys(ev.red, "diff"))

    def test_l0_without_plan_over_thresholds_is_red(self):
        block = self.lab.block(level="L0", plan=None, plan_sha=None, dod={"L": "L0",
                                                                          "items": {}})
        self.assertNotIn("plan_absent", keys(self.run_gate(block=block).red))
        self.lab.commit("src/big.py", "".join(f"x{n} = {n}\n" for n in range(80)), "grande")
        ev = self.run_gate(block=block)
        self.assertEqual(keys(ev.red, "diff"), ["plan_absent"])
        # un L0 con un piano registrato non ha scope: le soglie le giudica il livello (Task 5)
        self.assertNotIn("plan_absent", keys(self.run_gate(block=self.lab.block(level="L0")).red))

    def test_waiver_of_other_issue_ignored(self):
        self.lab.commit("src/stray.py", "x = 1\n", "fuori scope")
        other = wtext(("scope", "src/stray.py", None, []), issue=3)
        ev = self.run_gate(waiver_text=other)
        self.assertEqual(keys(ev.red, "diff"), ["out_of_scope"])
        self.assertEqual(ev.attention, [])
        mine = wtext(("scope", "src/stray.py", None, []))
        self.assertEqual(keys(self.run_gate(waiver_text=mine).red, "diff"), [])

    def test_waiver_branch_must_match(self):
        self.lab.commit("src/stray.py", "x = 1\n", "fuori scope")
        wrong = wtext(("scope", "src/stray.py", None, []), branch="tg/7-altro")
        ev = self.run_gate(waiver_text=wrong)
        self.assertEqual(keys(ev.red, "diff"), ["out_of_scope"])
        self.assertEqual(ev.attention, [])

    def test_waivers_do_not_apply_without_a_valid_issue(self):
        self.lab.commit("src/stray.py", "x = 1\n", "fuori scope")
        text = wtext(("scope", "src/stray.py", None, []))
        closed = dataclasses.replace(self.lab.inputs().issue, state="closed")
        for name, override in (("closed", {"issue": closed}),
                               ("no issue", {"issue": None}),
                               ("closes other", {"pr": self.lab.with_pr(body="Closes #3\n")}),
                               ("block other", {"block": self.lab.block(issue=3)})):
            with self.subTest(name):
                ev = self.run_gate(waiver_text=text, **override)
                self.assertIn("out_of_scope", keys(ev.red, "diff"))

    def test_waiver_groups(self):
        for n in range(3):
            self.lab.commit(f"src/stray{n}.py", "x = 1\n", f"fuori {n}")
        one = wtext(("scope", "src/stray0.py", None, []))
        ev = self.run_gate(waiver_text=one)
        self.assertEqual(keys(ev.red, "diff"), ["out_of_scope", "out_of_scope"])
        self.assertEqual((keys(ev.attention), ev.attention_state), (["waiver_scope"], "success"))
        three = wtext(*[("scope", f"src/stray{n}.py", None, []) for n in range(3)])
        ev = self.run_gate(waiver_text=three)
        self.assertEqual(keys(ev.red, "diff"), [])
        self.assertEqual(keys(ev.attention),
                         ["waiver_scope", "waiver_scope", "waiver_scope_over_two"])
        self.assertEqual(ev.attention_state, "failure")

    def test_each_waiver_type_has_its_group(self):
        cases = {"test": "waiver_test", "ci": "waiver_ci", "threshold": "waiver_threshold",
                 "command": "waiver_command"}
        for type_, key in cases.items():
            with self.subTest(type_):
                tests = [SOMMA] if type_ == "test" else []
                ev = self.run_gate(waiver_text=wtext((type_, "tests/test_app.py", None, tests)))
                self.assertEqual(keys(ev.attention), [key])
                self.assertEqual((attention.group(key), ev.attention_state),
                                 (attention.READ, "failure"))

    def test_pattern_waiver_is_read(self):
        self.lab.commit("src/gen/a.py", "x = 1\n", "generato")
        self.lab.commit("src/gen/b.py", "x = 2\n", "generato")
        ev = self.run_gate(waiver_text=wtext(("scope", None, "src/gen/**", [])))
        self.assertEqual(keys(ev.red, "diff"), [])
        self.assertEqual(keys(ev.attention), ["waiver_pattern"])
        self.assertEqual(ev.attention_state, "failure")

    def test_sensitive_scope_waiver_is_over_two(self):
        self.lab.commit("src/auth/login.py", "x = 1\n", "sensibile")
        ev = self.run_gate(waiver_text=wtext(("scope", "src/auth/login.py", None, [])))
        self.assertEqual(keys(ev.attention), ["waiver_scope_over_two"])

    def test_waiver_data_is_untrusted_text_only_in_data(self):
        text = wtext(("scope", "src/a.py", None, []))
        ev = self.run_gate(waiver_text=text)
        item = ev.attention[0]
        self.assertNotIn("perché", item.text)
        self.assertIn("perché", item.data)

    def test_reviews_dir_exempt(self):
        self.lab.commit("docs/superpowers/reviews/7/spec-adversarial-1.md", "r\n", "report")
        self.assertEqual(keys(self.run_gate().red, "diff"), [])
        self.lab.commit("docs/superpowers/reviews/3/spec-adversarial-1.md", "r\n", "altrui")
        self.assertEqual(keys(self.run_gate().red, "diff"), ["out_of_scope"])

    def test_verification_watch_is_listed_not_attention(self):
        self.lab.commit("package.json", "{}\n", "manifest")
        ev = self.run_gate(pr=self.local_like_pr(), block=None)
        self.assertEqual(ev.watch, ["package.json"])

    def test_diff_error_is_an_error_not_a_traceback(self):
        ev = self.run_gate(base_sha="0" * 40)
        self.assertEqual(ev.verdict_state, "error")
        self.assertTrue(ev.errors)


class MustHaveTest(LabCase):
    def test_must_have_recomputed_from_head_junit(self):
        absent = [CommandResult("verify", "green", 0, 1, self.lab.junit([ZERO]))]
        ev = self.run_gate(commands=absent)
        self.assertEqual(keys(ev.red, "must_have"), ["must_have_missing"])
        self.assertIn(f"M1: {SOMMA}", next(i for i in ev.red if i.family == "must_have").data)
        failed = [CommandResult("verify", "red", 1, 2,
                                self.lab.junit(DEFAULT_IDS, ids_failed=[SOMMA]))]
        ev = self.run_gate(commands=failed)
        self.assertEqual(keys(ev.red, "must_have"), ["must_have_failed"])
        self.assertEqual(keys(self.run_gate().red, "must_have"), [])
        skipped = [CommandResult("verify", "green", 0, 1,
                                 self.lab.junit([ZERO], ids_skipped=[SOMMA]))]
        self.assertEqual(keys(self.run_gate(commands=skipped).red, "must_have"),
                         ["must_have_missing"])

    def test_must_have_ids_from_all_commands(self):
        lab = GateLab(toml=PROFILE_TOML)
        self.addCleanup(lab.close)
        lab.commit("web/app.js", "x\n", "web")
        commands = [CommandResult("verify", "green", 0, 1, lab.junit([ZERO])),
                    CommandResult("profile:web:test", "green", 0, 1, lab.junit([SOMMA]))]
        ev = evaluate(lab.inputs(commands=commands, base_ids={}))
        self.assertEqual(keys(ev.red, "must_have"), [])

    def test_manual_must_have_is_attention(self):
        plan = plan_text().replace(f"M1. Somma — test: {SOMMA}", "M1. Somma — test: manuale")
        lab = GateLab(plan=plan)
        self.addCleanup(lab.close)
        ev = evaluate(lab.inputs())
        self.assertEqual(keys(ev.red), [])
        self.assertEqual(keys(ev.attention), ["manual_must_have"])
        self.assertIn("M1", ev.attention[0].text)
        self.assertEqual(attention.group("manual_must_have"), attention.READ)

    def test_component_off(self):
        lab = GateLab(toml=GATE_TOML + "[components]\nmust_have_tests = false\n")
        self.addCleanup(lab.close)
        junit = lab.junit([])
        ev = evaluate(lab.inputs(commands=[CommandResult("verify", "green", 0, 0, junit)],
                                 base_ids={}))
        self.assertEqual(keys(ev.red, "must_have"), [])
        self.assertIn("components_off", keys(ev.attention))
        self.assertIn("must_have_tests", ev.attention[0].text)

    def test_not_for_manual_prs_or_l0(self):
        empty = [CommandResult("verify", "green", 0, 1, self.lab.junit([ZERO]))]
        ev = self.run_gate(commands=empty, pr=self.local_like_pr(), block=None)
        self.assertEqual(keys(ev.red, "must_have"), [])
        ev = self.run_gate(commands=empty, block=self.lab.block(level="L0"))
        self.assertEqual(keys(ev.red, "must_have"), [])


class EvaluationTest(unittest.TestCase):
    def test_states(self):
        item = Item("waiver_test", "diff", "x")
        self.assertEqual(Evaluation().verdict_state, "success")
        self.assertEqual(Evaluation(red=[item]).verdict_state, "failure")
        self.assertEqual(Evaluation(red=[item], errors=["e"]).verdict_state, "error")

    def test_attention_state_by_group(self):
        read, info = Item("waiver_test", "diff", "x"), Item("waiver_scope", "diff", "x")
        self.assertEqual(Evaluation().attention_state, "success")
        self.assertEqual(Evaluation(attention=[info]).attention_state, "success")
        self.assertEqual(Evaluation(attention=[info, read]).attention_state, "failure")

    def test_group_of_unknown_key_is_keyerror(self):
        self.assertEqual((attention.READ, attention.INFO), ("read", "info"))
        with self.assertRaises(KeyError):
            attention.group("inventata")

    def test_groups_follow_decision_7(self):
        self.assertEqual(attention.group("task_over_max"), attention.INFO)
        for key in ("plan_changed", "approval_stale", "components_off", "audit_off",
                    "base_ids_from_run", "ci_waived_workflow", "no_tests_counted"):
            self.assertEqual(attention.group(key), attention.READ, key)
        for key in ("waiver_scope", "allow_no_tests", "no_issue", "existing_workflow_rules"):
            self.assertEqual(attention.group(key), attention.INFO, key)


if __name__ == "__main__":
    unittest.main()
