import dataclasses
import io
import sys
import unittest

from tests.flowkit import PLAN, plan_text, spec_text
from tests.gatekit import BRANCH, DEFAULT_IDS, GATE_TOML, ISSUE, GateLab
from tests.helpers import git
from tests.hookkit import DEFAULT_FILES
from tollgate_analysis import approvals, waivers
from tollgate_gate import attention, evaluate as evaluate_module
from tollgate_gate.evaluate import base_path, tollgate_files_changed, tollgate_files_in_work
from tollgate_gate.model import (BASE_FROM_RUN, LOCAL, CommandResult, Evaluation, IssueFacts,
                                 Item)

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
# Le chiavi di `attenzione` che ogni caso di `evaluate` produce, raccolte per
# `CoverageTest.test_every_group_key_is_produced`.
SEEN: set[str] = set()


def evaluate(inputs):
    ev = evaluate_module.evaluate(inputs)
    SEEN.update(i.key for i in ev.attention)
    return ev


def keys(items, family=None):
    return [i.key for i in items if family is None or i.family == family]


def only(items, family):
    """L'unica voce della famiglia."""
    (found,) = [i for i in items if i.family == family]
    return found


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
        self.assertEqual(ev.attention[0].text, "must-have con test manuale: 1")
        self.assertIn("M1", ev.attention[0].data)
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


SPEC = "docs/superpowers/specs/s.md"
REVIEWS = approvals.REVIEWS_DIR
COUNTS = {"blocker": 0, "major": 0, "moderate": 0, "minor": 0}
WORKFLOW_OK = "on: pull_request\npermissions:\n  contents: read\njobs: {}\n"
WORKFLOW_BAD = "on: pull_request\npermissions:\n  statuses: write\njobs: {}\n"
CONFIG_TOML = GATE_TOML + "[project]\nallow_no_tests = true\n"


def l2_report(kind, **over):
    fields = {"schema_version": 1, "kind": kind, "number": 1, "viewpoint": None,
              "counts": dict(COUNTS), "outcome": "clean"}
    fields.update(over)
    return approvals.render_report(fields, "corpo\n")


def set_up_l2(lab, *, folder=ISSUE, slices=1, adversarial="closed", lens=None,
              spec_reports=("spec-adversarial",), plan_report=True):
    """Spec, approvazioni e report di L2 committati sul ramo del lavoro; ritorna il blob della
    spec. `folder` è la cartella dell'approvazione della spec: un'altra issue per una fetta
    successiva."""
    lab.commit(SPEC, spec_text(slices), "spec")
    blob = git(lab.repo, "rev-parse", f"HEAD:{SPEC}")
    lab.commit(f"{REVIEWS}/{folder}/spec-approval.md", approvals.render_approval(
        {"kind": "spec-approval", "path": SPEC, "sha": blob, "slices": slices,
         "adversarial": adversarial, "lens": lens}), "approvazione della spec")
    for kind in spec_reports:
        lab.commit(f"{REVIEWS}/{folder}/{kind}-1.md", l2_report(kind, spec_sha=blob), "report")
    lab.commit(f"{REVIEWS}/{ISSUE}/plan-approval.md", approvals.render_approval(
        {"kind": "plan-approval", "path": PLAN, "sha": lab.plan_sha, "spec_sha": blob,
         "adversarial": "closed"}), "approvazione del piano")
    if plan_report:
        lab.commit(f"{REVIEWS}/{ISSUE}/plan-adversarial-1.md",
                   l2_report("plan-adversarial", plan_sha=lab.plan_sha), "report del piano")
    return blob


def l2_block(lab, *, folder=ISSUE, **over):
    return lab.block(level="L2", level_minimum="L2", spec=SPEC,
                     spec_reviews_dir=f"{REVIEWS}/{folder}/",
                     plan_reviews_dir=f"{REVIEWS}/{ISSUE}/", **over)


def finding(n=1, cycle=1, **over):
    f = {"id": f"f-{cycle}-{n}", "severity": "major", "confidence": "high",
         "verification": "confirmed", "user_decision": None}
    f.update(over)
    return f


def verdict(cycles=1, unverified=False):
    return {"outcome": "needs_fix", "cycles": cycles, "findings_confirmed": 1,
            "unverified": unverified}


class LevelTest(LabCase):
    def sensitive(self):
        self.lab.commit("db/migrations/001.sql", "select 1;\n", "migrazione")

    def test_declared_below_minimum_without_cap_is_red(self):
        self.sensitive()
        ev = self.run_gate()
        self.assertEqual(keys(ev.red, "level"), ["level_below_minimum"])
        self.assertEqual(only(ev.red, "level").text, "livello dichiarato L1 sotto il minimo L2")
        self.assertEqual(ev.verdict_state, "failure")

    def test_with_cap_is_attention(self):
        self.sensitive()
        ev = self.run_gate(block=self.lab.block(level_cap="L1", level_cap_reason="solo un SQL"))
        self.assertEqual(keys(ev.red, "level"), [])
        self.assertEqual(keys(ev.attention, "level"), ["level_cap"])
        item = only(ev.attention, "level")
        self.assertIn("solo un SQL", item.data)
        self.assertNotIn("solo un SQL", item.text)
        self.assertEqual((attention.group("level_cap"), ev.attention_state),
                         (attention.READ, "failure"))

    def test_cap_that_is_not_a_level_does_not_hide_the_red(self):
        self.sensitive()
        ev = self.run_gate(block=self.lab.block(level_cap="boh"))
        self.assertEqual(keys(ev.red, "level"), ["level_below_minimum"])

    def test_labels_and_profile_min_level(self):
        security = IssueFacts(ISSUE, "open", ("security",))
        ev = self.run_gate(issue=security)
        self.assertEqual(keys(ev.red, "level"), ["level_below_minimum"])
        self.assertIn("minimo L2", only(ev.red, "level").text)
        self.assertEqual(keys(self.run_gate(issue=IssueFacts(ISSUE, "open", ("bug",))).red,
                              "level"), [])
        lab = GateLab(toml=PROFILE_TOML.replace('paths = ["web/**"]',
                                                'paths = ["web/**"]\nmin_level = "L2"'))
        self.addCleanup(lab.close)
        self.assertEqual(keys(evaluate(lab.inputs()).red, "level"), [])
        lab.commit("web/app.js", "x\n", "web")
        ev = evaluate(lab.inputs())
        self.assertEqual(keys(ev.red, "level"), ["level_below_minimum"])

    def test_at_or_above_minimum_is_clean(self):
        self.sensitive()
        ev = self.run_gate(block=self.lab.block(level="L2"))
        self.assertEqual(keys(ev.red, "level") + keys(ev.attention, "level"), [])

    def test_unknown_declared_level_is_red(self):
        ev = self.run_gate(block=self.lab.block(level="L9"))
        self.assertEqual(keys(ev.red, "level"), ["level_invalid"])

    def test_manual_pr_has_no_level_check(self):
        self.sensitive()
        ev = self.run_gate(pr=self.local_like_pr(), block=None)
        self.assertEqual(keys(ev.red, "level"), [])


class L2Test(LabCase):
    def l2_gate(self, folder=ISSUE, **over):
        return self.run_gate(block=l2_block(self.lab, folder=folder), **over)

    def test_complete_l2_is_clean(self):
        set_up_l2(self.lab)
        ev = self.l2_gate()
        self.assertEqual(keys(ev.red, "l2") + keys(ev.attention, "l2"), [])

    def test_missing_report_is_red(self):
        set_up_l2(self.lab, spec_reports=())
        ev = self.l2_gate()
        self.assertEqual(keys(ev.red, "l2"), ["l2_missing"])
        item = only(ev.red, "l2")
        self.assertEqual(item.text, "1 problema nei file di approvazione e nei report di L2")
        self.assertIn("spec-adversarial", item.data)
        self.assertEqual(ev.verdict_state, "failure")

    def test_missing_approvals_are_red(self):
        ev = self.l2_gate_without_files()
        self.assertEqual(keys(ev.red, "l2"), ["l2_missing"])
        self.assertIn("spec-approval.md", only(ev.red, "l2").data)

    def l2_gate_without_files(self):
        return self.run_gate(block=l2_block(self.lab))

    def test_stale_approval_is_attention_with_diff(self):
        set_up_l2(self.lab)
        self.lab.commit(SPEC, spec_text(note="una riga nuova"), "spec cambiata")
        ev = self.l2_gate()
        self.assertEqual(keys(ev.red, "l2"), [])
        self.assertEqual(keys(ev.attention, "l2"), ["approval_stale"])
        item = only(ev.attention, "l2")
        self.assertIn("+una riga nuova", item.data)
        self.assertNotIn("una riga nuova", item.text)
        self.assertEqual((attention.group("approval_stale"), ev.attention_state),
                         (attention.READ, "failure"))

    def test_stale_plan_approval_is_attention_with_diff(self):
        set_up_l2(self.lab)
        self.lab.commit(PLAN, plan_text() + "\nmodifica\n", "piano cambiato")
        ev = self.l2_gate()
        self.assertEqual(keys(ev.attention, "l2"), ["approval_stale"])
        self.assertIn("+modifica", only(ev.attention, "l2").data)

    def test_spec_audit_off_three_slices_attention_not_red(self):
        lab = GateLab(toml=GATE_TOML + "[components]\nspec_audit = false\n")
        self.addCleanup(lab.close)
        set_up_l2(lab, slices=3, lens="off")
        block = l2_block(lab, spec_audit={"adversarial": "closed", "lens": "off"})
        ev = evaluate(lab.inputs(block=block))
        self.assertEqual(keys(ev.red, "l2"), [])
        self.assertEqual(sorted(keys(ev.attention, "l2") + keys(ev.attention, "components")),
                         ["audit_off", "components_off"])
        self.assertEqual(attention.group("audit_off"), attention.READ)

    def test_suspended_is_attention(self):
        set_up_l2(self.lab, adversarial="suspended")
        ev = self.run_gate(block=l2_block(
            self.lab, spec_audit={"adversarial": "suspended", "lens": None}))
        self.assertEqual(keys(ev.red, "l2"), [])
        self.assertEqual(keys(ev.attention, "l2"), ["audit_suspended"])
        self.assertEqual(only(ev.attention, "l2").text, "audit della spec sospeso: avversario")

    def test_later_slice_reports_in_other_folder(self):
        set_up_l2(self.lab, folder=3)
        ev = self.l2_gate(folder=3)
        self.assertEqual(keys(ev.red, "l2") + keys(ev.attention, "l2"), [])

    def test_reviews_dir_other_than_the_found_one_is_stale(self):
        set_up_l2(self.lab, folder=3)
        ev = self.run_gate(block=l2_block(self.lab, folder=9))
        self.assertEqual(keys(ev.red, "l2"), [])
        self.assertEqual(keys(ev.attention, "l2"), ["approval_stale"])
        self.assertIn(f"{REVIEWS}/9/", only(ev.attention, "l2").data)
        self.assertIn(f"{REVIEWS}/3", only(ev.attention, "l2").data)

    def test_default_components_passed_to_check_l2(self):
        # spec_adversary è acceso sul predefinito: l'intestazione `adversarial: off` non basta
        set_up_l2(self.lab, adversarial="off", spec_reports=())
        ev = self.l2_gate()
        self.assertEqual(keys(ev.red, "l2"), ["l2_missing"])
        self.assertIn("spec_adversary", only(ev.red, "l2").data)

    def test_only_l2_declared_blocks_are_checked(self):
        ev = self.run_gate()
        self.assertEqual(keys(ev.red, "l2") + keys(ev.attention, "l2"), [])


class IssueTest(LabCase):
    def test_tg_branch_with_other_closed_issue_is_red_and_no_waivers(self):
        self.lab.commit("src/stray.py", "x = 1\n", "fuori scope")
        text = wtext(("scope", "src/stray.py", None, []))
        pr = self.lab.with_pr(body="Closes #3\n")
        closed = IssueFacts(3, "closed", ())
        ev = self.run_gate(pr=pr, issue=closed, waiver_text=text)
        self.assertEqual(sorted(keys(ev.red, "issue")), ["closes_mismatch", "issue_invalid"])
        self.assertIn("out_of_scope", keys(ev.red, "diff"))
        self.assertEqual([k for k in keys(ev.attention) if k.startswith("waiver")], [])

    def test_block_issue_mismatch(self):
        ev = self.run_gate(block=self.lab.block(issue=3))
        self.assertEqual(keys(ev.red, "issue"), ["block_issue_mismatch"])
        self.assertIn("#7", only(ev.red, "issue").text)

    def test_issue_closed_or_missing_is_red(self):
        closed = dataclasses.replace(self.lab.inputs().issue, state="closed")
        for name, issue in (("closed", closed), ("absent", None)):
            with self.subTest(name):
                ev = self.run_gate(issue=issue)
                self.assertEqual(keys(ev.red, "issue"), ["issue_invalid"])

    def test_valid_tg_pr_has_no_issue_voice(self):
        ev = self.run_gate()
        self.assertEqual(keys(ev.red, "issue") + keys(ev.attention, "issue"), [])

    def test_block_missing_on_tg_is_red(self):
        ev = self.run_gate(block=None)
        self.assertEqual(keys(ev.red, "issue"), ["block_missing"])
        self.assertEqual(ev.verdict_state, "failure")

    def test_manual_pr_without_closes(self):
        ev = self.run_gate(pr=self.local_like_pr(), block=None, issue=None)
        self.assertEqual(keys(ev.red, "issue"), [])
        self.assertEqual(sorted(keys(ev.attention, "issue")), ["no_issue", "not_tg_branch"])
        self.assertEqual(attention.group("no_issue"), attention.INFO)
        self.assertEqual((attention.group("not_tg_branch"), ev.attention_state),
                         (attention.READ, "failure"))

    def test_manual_pr_with_closes_needs_an_open_issue(self):
        pr = self.lab.with_pr(head_ref="fix/x", body="Fixes #5\n")
        ok = self.run_gate(pr=pr, block=None, issue=IssueFacts(5, "open", ()))
        self.assertEqual(keys(ok.red, "issue"), [])
        self.assertEqual(keys(ok.attention, "issue"), ["not_tg_branch"])
        for issue in (IssueFacts(5, "closed", ()), None):
            with self.subTest(issue):
                ev = self.run_gate(pr=pr, block=None, issue=issue)
                self.assertEqual(keys(ev.red, "issue"), ["issue_invalid"])

    def test_config_branch(self):
        branch = "tollgate-config/0.2.0"
        git(self.lab.repo, "checkout", "-q", "-b", branch, self.lab.base)
        self.lab.commit("tollgate.toml", CONFIG_TOML, "configurazione")
        self.lab.commit(".github/tollgate/FINGERPRINT", "abc123\n", "impronta")
        self.lab.commit("tests/test_new.py", "import pytest\n\n\n@pytest.mark.skip\n"
                        "def test_n():\n    assert 1\n", "salta")
        self.lab.commit("src/stray.py", "x = 1\n", "fuori scope")
        pr = self.lab.with_pr(head_ref=branch, body="")
        ev = self.run_gate(pr=pr, block=None, issue=None)
        self.assertEqual(keys(ev.red, "diff"), [])
        self.assertEqual(keys(ev.attention, "issue"), ["tollgate_config"])
        item = only(ev.attention, "issue")
        self.assertIn("project.allow_no_tests", item.data)
        self.assertNotIn("gate.mode", item.data)
        self.assertIn("FINGERPRINT: abc123", item.data)
        self.assertEqual((attention.group("tollgate_config"), ev.attention_state),
                         (attention.READ, "failure"))


class DeclaredTest(LabCase):
    def declared(self, **override):
        return self.run_gate(block=self.lab.block(**override))

    def test_blocking_finding_last_cycle_red_even_unverified(self):
        ev = self.declared(findings=[finding()], verdict=verdict(unverified=True))
        self.assertEqual(keys(ev.red, "declared"), ["finding_blocking"])
        self.assertEqual(only(ev.red, "declared").data, "f-1-1")
        self.assertEqual(keys(ev.attention, "notes"), ["review_unverified"])
        self.assertEqual(attention.group("review_unverified"), attention.READ)

    def test_old_cycle_finding_ignored(self):
        ev = self.declared(findings=[finding(cycle=1)], verdict=verdict(cycles=2))
        self.assertEqual(keys(ev.red, "declared"), [])
        ev = self.declared(findings=[finding(cycle=2)], verdict=verdict(cycles=2))
        self.assertEqual(keys(ev.red, "declared"), ["finding_blocking"])

    def test_blocking_missing_is_blocking(self):
        self.assertEqual(keys(self.declared(findings=[finding()]).red, "declared"),
                         ["finding_blocking"])
        ev = self.declared(findings=[finding(blocking=False)])
        self.assertEqual(keys(ev.red, "declared") + keys(ev.attention, "declared"), [])
        ev = self.declared(findings=[finding(blocking=True)])
        self.assertEqual(keys(ev.red, "declared"), ["finding_blocking"])

    def test_not_confirmed_or_minor_findings_do_not_block(self):
        for name, f in (("rejected", finding(verification="rejected")),
                        ("unverified", finding(verification="unverified")),
                        ("moderate", finding(severity="moderate"))):
            with self.subTest(name):
                self.assertEqual(keys(self.declared(findings=[f]).red, "declared"), [])

    def test_dismissed_is_attention(self):
        for decision in ("dismissed", "downgraded:moderate", "downgraded:minor"):
            with self.subTest(decision):
                ev = self.declared(findings=[finding(user_decision=decision)])
                self.assertEqual(keys(ev.red, "declared"), [])
                self.assertEqual(keys(ev.attention, "declared"), ["findings_overridden"])
                self.assertIn("f-1-1", only(ev.attention, "declared").data)
        self.assertEqual(attention.group("findings_overridden"), attention.READ)
        ev = self.declared(findings=[finding(user_decision="downgraded:major")])
        self.assertEqual(keys(ev.red, "declared"), ["finding_blocking"])

    def test_declared_dod_false_is_red_unless_component_off(self):
        block = self.lab.block(dod={"L": "L1", "items": {"receipt": True, "tasks_approved": False}},
                               findings=[finding()])
        ev = self.run_gate(block=block)
        self.assertEqual(keys(ev.red, "declared"), ["dod_false", "finding_blocking"])
        self.assertEqual(ev.red[0].data, "tasks_approved")
        lab = GateLab(toml=GATE_TOML + "[components]\ndefinition_of_done = false\n")
        self.addCleanup(lab.close)
        block = lab.block(dod={"L": "L1", "items": {"tasks_approved": False}},
                          findings=[finding()])
        ev = evaluate(lab.inputs(block=block))
        self.assertEqual(keys(ev.red, "declared"), [])
        self.assertIn("components_off", keys(ev.attention))

    def test_recomputed_items_override_declared(self):
        items = {"receipt": False, "guard_scope": False, "must_have": False, "approvals": False}
        ev = self.declared(dod={"L": "L1", "items": items})
        self.assertEqual((ev.red, ev.attention), ([], []))

    def test_none_items_are_not_declared_false(self):
        ev = self.declared(dod={"L": "L1", "items": {"skills": None}})
        self.assertEqual(keys(ev.red, "declared"), [])

    def test_tasks_over_and_skills_absent_info(self):
        ev = self.declared(
            tasks_over=[{"task": 2, "lines": 250, "size_reason": None},
                        {"task": 3, "lines": 600, "size_reason": "migrazione unica"}],
            skills_absent=[{"task": 1, "skills": ["pdf", "docx"]}])
        self.assertEqual(ev.red, [])
        self.assertEqual(keys(ev.attention), ["task_over_warn", "task_over_max", "skills_absent"])
        by_key = {i.key: i for i in ev.attention}
        self.assertIn("task 3: 600 righe: migrazione unica", by_key["task_over_max"].data)
        self.assertIn("task 2: 250 righe", by_key["task_over_warn"].data)
        self.assertNotIn("migrazione unica", by_key["task_over_max"].text)
        self.assertIn("pdf, docx", by_key["skills_absent"].data)
        self.assertEqual(ev.attention_state, "success")

    def test_malformed_block_fields_do_not_crash(self):
        ev = self.declared(findings="x", dod={"items": ["receipt"]}, tasks_over=5,
                           skills_absent=[{"task": 1, "skills": 7}], off_periods="x",
                           verdict="x", spec_audit="x")
        self.assertEqual(ev.errors, [])
        self.assertEqual(keys(ev.red, "declared"), [])

    def test_existing_workflow_rules_info(self):
        lab = GateLab(files={**DEFAULT_FILES, ".github/workflows/ci.yml": WORKFLOW_BAD,
                             ".github/workflows/ok.yml": WORKFLOW_OK})
        self.addCleanup(lab.close)
        ev = evaluate(lab.inputs())
        self.assertEqual(ev.red, [])
        self.assertEqual(keys(ev.attention), ["existing_workflow_rules"])
        item = only(ev.attention, "workflows")
        self.assertIn(".github/workflows/ci.yml: ", item.data)
        self.assertNotIn("ok.yml", item.data)
        self.assertEqual((attention.group("existing_workflow_rules"), ev.attention_state),
                         (attention.INFO, "success"))

    def test_changed_workflow_is_not_an_existing_one(self):
        lab = GateLab(files={**DEFAULT_FILES, ".github/workflows/ci.yml": WORKFLOW_BAD})
        self.addCleanup(lab.close)
        lab.commit(".github/workflows/ci.yml", WORKFLOW_OK, "sistemato")
        self.assertNotIn("existing_workflow_rules", keys(evaluate(lab.inputs()).attention))


class NotesTest(LabCase):
    def test_off_periods_sentinel_and_unverified_review(self):
        block = self.lab.block(off_periods=[{"from": "2026-10-21T10:00:00Z", "to": None}],
                               verdict={"outcome": "ok", "cycles": 1, "findings_confirmed": 0,
                                        "unverified": True})
        ev = self.run_gate(block=block, sentinel_open=[4, 5])
        self.assertEqual(sorted(keys(ev.attention)),
                         ["off_periods", "review_unverified", "sentinel_open"])
        by_key = {i.key: i for i in ev.attention}
        self.assertEqual(by_key["sentinel_open"].data, "4, 5")
        self.assertEqual(by_key["off_periods"].text, "periodi con tollgate spento dichiarati: 1")
        self.assertIn("2026-10-21T10:00:00Z", by_key["off_periods"].data)
        self.assertEqual(ev.attention_state, "failure")

    def test_sentinel_open_needs_no_block(self):
        ev = self.run_gate(pr=self.local_like_pr(), block=None, sentinel_open=[9])
        self.assertIn("sentinel_open", keys(ev.attention))


class LockfileTest(LabCase):
    def test_lockfile_without_manifest_is_info(self):
        self.lab.commit("package-lock.json", "{}\n", "lock")
        ev = self.run_gate()
        self.assertEqual(keys(ev.attention), ["lockfile_without_manifest"])
        self.assertEqual(only(ev.attention, "diff").data, "package-lock.json")
        self.assertEqual((attention.group("lockfile_without_manifest"), ev.attention_state),
                         (attention.INFO, "success"))

    def test_lockfile_with_its_manifest_is_clean(self):
        self.lab.commit("package.json", "{}\n", "manifest")
        self.lab.commit("package-lock.json", "{}\n", "lock")
        self.assertNotIn("lockfile_without_manifest", keys(self.run_gate().attention))

    def test_manifest_in_another_folder_does_not_count(self):
        self.lab.commit("web/package.json", "{}\n", "manifest")
        self.lab.commit("package-lock.json", "{}\n", "lock")
        self.assertIn("lockfile_without_manifest", keys(self.run_gate().attention))


class WorkflowWaiverTest(LabCase):
    def test_ci_waiver_covering_a_changed_workflow_is_read(self):
        self.lab.commit(".github/workflows/ci.yml", WORKFLOW_OK, "workflow")
        text = wtext(("ci", ".github/workflows/ci.yml", None, []))
        ev = self.run_gate(waiver_text=text)
        self.assertIn("ci_waived_workflow", keys(ev.attention))
        item = next(i for i in ev.attention if i.key == "ci_waived_workflow")
        self.assertEqual(item.data, ".github/workflows/ci.yml")
        self.assertEqual(attention.group("ci_waived_workflow"), attention.READ)

    def test_no_voice_without_a_waiver_or_for_other_files(self):
        self.lab.commit(".github/workflows/ci.yml", WORKFLOW_OK, "workflow")
        self.assertNotIn("ci_waived_workflow", keys(self.run_gate().attention))
        other = wtext(("ci", ".github/workflows/other.yml", None, []))
        self.assertNotIn("ci_waived_workflow", keys(self.run_gate(waiver_text=other).attention))


class TollgateFilesTest(LabCase):
    def test_changed_against_the_default_tip(self):
        self.assertEqual(tollgate_files_changed(self.lab.repo, self.lab.base, self.lab.head), [])
        self.lab.commit("tollgate.toml", CONFIG_TOML, "config")
        self.lab.commit(".github/workflows/tollgate-verdict.yml", "x\n", "verdict")
        self.lab.commit(".github/tollgate/VERSION", "9\n", "versione")
        self.lab.commit(".github/workflows/ci.yml", WORKFLOW_OK, "ci")
        self.lab.commit("src/app.py", "x = 1\n", "codice")
        self.assertEqual(tollgate_files_changed(self.lab.repo, self.lab.base, self.lab.head),
                         [".github/tollgate/VERSION", ".github/workflows/tollgate-verdict.yml",
                          "tollgate.toml"])

    def test_deleted_and_moved_tollgate_files_count(self):
        lab = GateLab(files={**DEFAULT_FILES, ".github/tollgate/VERSION": "1\n"})
        self.addCleanup(lab.close)
        lab.delete(".github/tollgate/VERSION")
        self.assertEqual(tollgate_files_changed(lab.repo, lab.base, lab.head),
                         [".github/tollgate/VERSION"])

    def test_in_work_reads_the_changes_of_the_work(self):
        self.lab.commit("tollgate.toml", CONFIG_TOML, "config")
        self.lab.commit("src/app.py", "x = 1\n", "codice")
        changes = git_changes(self.lab)
        self.assertEqual(tollgate_files_in_work(changes), ["tollgate.toml"])
        self.assertEqual(tollgate_files_in_work([]), [])


def git_changes(lab):
    from tollgate_core import git as core_git
    return core_git.changes(lab.repo, lab.base, head=lab.head)


class LocalTest(LabCase):
    def local(self, **override):
        values = dict(where=LOCAL, pr=None, issue=None, commands=None, base_ids=None,
                      base_ids_source=None)
        values.update(override)
        return self.run_gate(**values)

    def test_local_skips_issue_declared_base(self):
        block = self.lab.block(findings=[finding()], issue=3,
                               dod={"L": "L1", "items": {"tasks_approved": False}},
                               tasks_over=[{"task": 1, "lines": 900, "size_reason": "x"}],
                               verdict={"outcome": "needs_fix", "cycles": 1,
                                        "findings_confirmed": 1, "unverified": True})
        ev = self.local(block=block)
        families = {i.family for i in ev.red + ev.attention}
        self.assertEqual(families & {"issue", "declared", "base_ids", "notes"}, set())
        self.assertEqual(ev.errors, [])

    def test_local_runs_level_and_l2(self):
        self.lab.commit("db/migrations/001.sql", "select 1;\n", "migrazione")
        ev = self.local(block=self.lab.block())
        self.assertEqual(keys(ev.red, "level"), ["level_below_minimum"])
        set_up_l2(self.lab, spec_reports=())
        ev = self.local(block=l2_block(self.lab))
        self.assertEqual(keys(ev.red, "l2"), ["l2_missing"])

    def test_guard_local_tollgate_file_changed(self):
        self.lab.commit("tollgate.toml", CONFIG_TOML, "config")
        ev = self.local(block=self.lab.block())
        self.assertEqual(keys(ev.red, "guard_local"), ["guard_local"])
        guard = only(ev.red, "guard_local")
        self.assertEqual(guard.data, "tollgate.toml")
        self.assertEqual(guard.text,
                         "file di tollgate modificati rispetto alla base del lavoro: 1")
        self.assertEqual(keys(self.run_gate().red, "guard_local"), [])

    def test_guard_local_workflow_rules(self):
        self.lab.commit(".github/workflows/ci.yml", WORKFLOW_BAD, "workflow")
        ev = self.local(block=self.lab.block())
        self.assertEqual(keys(ev.red, "guard_local"), ["guard_workflow"])
        self.assertIn(".github/workflows/ci.yml: statuses: write", only(ev.red, "guard_local").data)
        self.assertEqual(keys(self.run_gate().red, "guard_local"), [])
        self.lab.commit(".github/workflows/ci.yml", WORKFLOW_OK, "sistemato")
        self.assertEqual(keys(self.local(block=self.lab.block()).red, "guard_local"), [])

    def test_clean_local_run_has_nothing(self):
        ev = self.local(block=self.lab.block())
        self.assertEqual((ev.red, ev.attention, ev.errors), ([], [], []))


class CoverageTest(unittest.TestCase):
    """Ogni chiave di `attention.GROUPS` è prodotta da almeno un caso di `evaluate` (nessuna
    chiave è prodotta fuori da `evaluate`: `sentinel_open` arriva dagli ingressi)."""

    def test_every_group_key_is_produced(self):
        missing = set(attention.GROUPS) - SEEN
        if missing:     # eseguito da solo: si riesegue il resto del modulo e si raccoglie
            module = sys.modules[__name__]
            suite = unittest.TestSuite(
                unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, name))
                for name in dir(module)
                if name != type(self).__name__ and isinstance(getattr(module, name), type)
                and issubclass(getattr(module, name), unittest.TestCase)
                and getattr(module, name).__module__ == __name__)
            unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            missing = set(attention.GROUPS) - SEEN
        self.assertEqual(missing, set())


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
