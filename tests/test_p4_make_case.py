"""I casi della prova reale (`spikes/p4/make_case.py`), provati in locale e senza rete.

Ogni caso si costruisce in un clone di un repo nudo con il progetto di prova e l'installazione di tollgate;
per i casi che il calcolo del gate sa giudicare (`oracle`), gli stati attesi si confrontano con quelli che
danno `gate run` (i comandi veri del progetto) e `evaluate.evaluate`, con le stesse funzioni del gate su
GitHub: così il rapporto della prova reale non parte da attese sbagliate."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, git
from tollgate_analysis import prblock
from tollgate_core import git as core_git
from tollgate_core.config import load_config_at
from tollgate_gate import artifacts, baseids, evaluate, guard, install
from tollgate_gate import run as gate_run
from tollgate_gate.model import BASE_FROM_CACHE, GITHUB, GateInputs, IssueFacts, PrFacts

SPEC = importlib.util.spec_from_file_location("make_case", ROOT / "spikes" / "p4" / "make_case.py")
make_case = importlib.util.module_from_spec(SPEC)
sys.modules["make_case"] = make_case
SPEC.loader.exec_module(make_case)


def make_origin(root: Path, repo: str):
    """Origin nudo con il progetto di prova e l'installazione di tollgate, e un clone di lavoro."""
    origin = root / f"{repo}.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True,
                   capture_output=True)
    seed = root / f"seed-{repo}"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    make_case.write_baseline(repo, seed)
    for rel, data in install.files(ROOT, default_branch="main", services={}).items():
        path = seed / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "base")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-q", "-u", "origin", "main")
    clone = root / f"clone-{repo}"
    subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True, capture_output=True)
    git(clone, "remote", "set-head", "origin", "main")
    return clone


class Lab:
    """Un clone per repo e il numero di issue di ogni caso."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate p4 casi "))
        self.clones = {repo: make_origin(self.tmp, repo) for repo in make_case.REPOS}
        self.n = 100

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, name: str) -> dict:
        spec = make_case.CASES[name]
        self.n += 1
        clone = self.clones[spec.repo]
        git(clone, "switch", "-q", "--detach", "origin/main")
        out = self.tmp / "out"
        return make_case.build_case(name, clone, self.n, f"20261022-{self.n:06d}", out, f"{name}-{self.n}",
                                    extra_issue=self.n + 1000)


class CasesBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = Lab()
        cls.data = {name: cls.lab.build(name) for name in make_case.CASES}

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def test_every_case_has_operations_and_expectations(self):
        for name, data in self.data.items():
            with self.subTest(name):
                ops = [o["op"] for o in data["ops"]]
                self.assertTrue({"push", "direct"} & set(ops))
                self.assertTrue(data["expect"])
                pushes = [o["id"] for o in data["ops"] if o["op"] in ("push", "merge", "direct")]
                for e in data["expect"]:
                    self.assertIn(e["push"], pushes)
                for op in data["ops"]:
                    if op["op"] == "pr":
                        self.assertGreater(ops.index("pr"), ops.index("push"))

    def test_pushed_shas_exist_in_the_clone_and_branches_are_not_main(self):
        for name, data in self.data.items():
            clone = self.lab.clones[data["repo"]]
            for op in data["ops"]:
                if op["op"] != "push":
                    continue
                with self.subTest(name, branch=op["branch"]):
                    self.assertEqual(git(clone, "cat-file", "-t", op["sha"]), "commit")
                    if op["branch"] not in ("main", "other"):
                        self.assertNotEqual(op["sha"], git(clone, "rev-parse", "origin/main"))

    def test_pr_bodies_carry_a_readable_block(self):
        for name, data in self.data.items():
            for op in data["ops"]:
                if op["op"] != "pr" or not data["branch"].startswith("tg/"):
                    continue
                with self.subTest(name, branch=op["branch"]):
                    body = Path(op["body_file"]).read_text()
                    block = prblock.parse(body)
                    self.assertIsNotNone(block)
                    self.assertEqual(block["issue"], data["issue"])
                    self.assertEqual(block["schema_version"], 1)
                    if name != "detect-closes":
                        self.assertTrue(body.startswith(f"Closes #{data['issue']}\n"))
                    self.assertRegex(op["title"], r"^[^\n]+$")

    def test_superseded_sha_case_judges_merge_state_only_on_the_last_push(self):
        first, last = self.data["error-sha-superato"]["expect"]
        self.assertIsNone(first["merge_state"])
        self.assertEqual(last["merge_state"], "CLEAN")

    def test_merge_state_follows_the_rule_for_every_protected_case(self):
        """Regola (esito reale su GitHub): guard o verdict non verdi -> BLOCKED; verdi con attention rossa o in errore -> UNSTABLE
        (un controllo non obbligatorio rosso, la PR resta unibile); tutto verde -> CLEAN. Solo il caso del token personale la nega."""
        checked = 0
        for name, spec in make_case.CASES.items():
            if spec.repo != "protected":
                continue
            for exp in spec.expect:
                if exp.merge_state is None:
                    continue
                st = exp.states
                if name == "token-personale":
                    self.assertEqual(exp.merge_state, "BLOCKED")
                    continue
                if st["tollgate/guard"] != "success" or st["tollgate/verdict"] != "success":
                    want = "BLOCKED"
                elif st["tollgate/attention"] in ("failure", "error"):
                    want = "UNSTABLE"
                else:
                    want = "CLEAN"
                with self.subTest(name, push=exp.push):
                    self.assertEqual(exp.merge_state, want)
                    checked += 1
        self.assertGreaterEqual(checked, 25)

    def test_the_six_attention_cases_expect_unstable(self):
        for name in ("verde-config", "verde-ramo-libero", "verde-workflow-ci", "attenzione-deroga-test",
                     "attenzione-piano-testo", "attenzione-tetto-livello"):
            with self.subTest(name):
                self.assertEqual(make_case.CASES[name].expect[-1].merge_state, "UNSTABLE")

    def test_the_destructive_detect_case_is_the_last_detect_case(self):
        detect = [n for n, c in make_case.CASES.items() if c.repo == "detect"]
        self.assertEqual(detect[-1], "detect-merge-rosso")

    def test_branch_names(self):
        for name, data in self.data.items():
            with self.subTest(name):
                branch = data["branch"]
                if name == "verde-config":
                    self.assertTrue(branch.startswith("tollgate-config/"))
                elif name in ("verde-ramo-libero", "non-applicabile"):
                    self.assertTrue(branch.startswith("prova/"))
                elif name.startswith(("guard-", "rosso-", "attenzione-", "error-", "token-", "detect-closes",
                                      "verde-", "detect-pulita", "detect-merge")):
                    self.assertRegex(branch, rf"^tg/{data['issue']}-[a-z0-9-]+$")

    def test_files_of_the_clean_case(self):
        clone = self.lab.clones["protected"]
        data = self.data["verde-pulita"]
        head = data["ops"][0]["sha"]
        changed = git(clone, "diff", "--name-only", "origin/main", head).split("\n")
        self.assertEqual(sorted(changed), sorted([
            f"docs/superpowers/plans/2026-10-21-pulita.md", "src/calc.py", "tests/test_calc.py"]))

    def test_workflow_variants_are_inert(self):
        """Nessun workflow di prova parte da solo sul ramo: sono eventi che il ramo non può attivare."""
        for variant in make_case.WORKFLOWS:
            data = self.data[f"guard-wf-{variant}"]
            clone = self.lab.clones["protected"]
            text = git(clone, "show", f"{data['ops'][0]['sha']}:.github/workflows/p4-{variant}.yml")
            self.assertNotRegex(text, r"(?m)^on:\s*(push|pull_request)\b")
            self.assertNotIn("push:", text)

    def test_judge_compares_states_comments_and_merge_state(self):
        data = self.data["rosso-test-tolti"]
        push = data["expect"][0]["push"]
        statuses = [{"context": "tollgate/guard", "state": "success", "creator": make_case.BOT},
                    {"context": "tollgate/verdict", "state": "failure", "creator": make_case.BOT},
                    {"context": "tollgate/attention", "state": "success", "creator": make_case.BOT}]
        comments = [{"id": 1, "user": make_case.BOT, "body": "<!-- tollgate-verdict sha=" + "a" * 40 + " -->\nx"}]
        ok, row = make_case.judge(data, push, statuses=statuses, comments=comments, merge_state="BLOCKED",
                                  sentinel_issues=None, pr="7", sha="b" * 40)
        self.assertTrue(ok, row)
        self.assertIn("riuscito", row)
        ok, row = make_case.judge(data, push, statuses=statuses[:1], comments=[], merge_state="CLEAN",
                                  sentinel_issues=None, pr="7", sha="b" * 40)
        self.assertFalse(ok)
        self.assertIn("non riuscito", row)
        for fragment in ("tollgate/verdict: atteso failure, ottenuto none", "manca il commento",
                         "mergeStateStatus"):
            self.assertIn(fragment, row)

    def test_a_duplicated_verdict_comment_is_a_failure(self):
        data = self.data["verde-edit"]
        push = data["expect"][0]["push"]
        statuses = [{"context": c, "state": "success", "creator": make_case.BOT}
                    for c in ("tollgate/guard", "tollgate/verdict", "tollgate/attention")]
        one = [{"id": 1, "user": make_case.BOT, "body": "<!-- tollgate-verdict sha=" + "a" * 40 + " -->"}]
        ok, row = make_case.judge(data, push, statuses=statuses, comments=one, merge_state="CLEAN",
                                  sentinel_issues=None, pr="1", sha="b" * 40)
        self.assertTrue(ok, row)
        ok, row = make_case.judge(data, push, statuses=statuses, comments=one + [dict(one[0], id=2)],
                                  merge_state="CLEAN", sentinel_issues=None, pr="1", sha="b" * 40)
        self.assertFalse(ok)
        self.assertIn("2 invece di uno", row)

    def test_a_status_by_a_user_is_shown_with_its_author(self):
        data = self.data["token-personale"]
        push = data["expect"][0]["push"]
        statuses = [{"context": "tollgate/verdict", "state": "success", "creator": "ginz0ls"},
                    {"context": "tollgate/verdict", "state": "failure", "creator": make_case.BOT},
                    {"context": "tollgate/guard", "state": "success", "creator": make_case.BOT},
                    {"context": "tollgate/attention", "state": "success", "creator": make_case.BOT}]
        ok, row = make_case.judge(data, push, statuses=statuses, comments=[], merge_state="BLOCKED",
                                  sentinel_issues=None, pr="3", sha="c" * 40)
        self.assertTrue(ok, row)
        self.assertIn("verdict=success (ginz0ls)", row)


class OracleTest(unittest.TestCase):
    """I casi con `oracle`: gli stati attesi sono quelli che il calcolo del gate dà sui comandi veri."""

    @classmethod
    def setUpClass(cls):
        cls.lab = Lab()
        cls.environ = {"PATH": os.environ["PATH"], "HOME": str(cls.lab.tmp), "LANG": "C.UTF-8"}
        cls.base_ids = {}
        for repo, clone in cls.lab.clones.items():
            tip = core_git.resolve_ref(clone, "origin/main")
            checkout = cls.lab.tmp / f"base-{repo}"
            git(clone, "worktree", "add", "-q", "--detach", str(checkout), tip)
            ids = baseids.compute(checkout, config_sha=tip, sha=tip, out=cls.lab.tmp / f"ids-{repo}",
                                  environ=cls.environ, cfg_repo=clone)
            cls.base_ids[repo] = {k: set(v) for k, v in ids["ids"].items()}

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def judge(self, name: str):
        data = self.lab.build(name)
        repo = data["repo"]
        clone = self.lab.clones[repo]
        tip = core_git.resolve_ref(clone, "origin/main")
        branch = data["branch"]
        git(clone, "switch", "-q", branch)
        head = git(clone, "rev-parse", "HEAD")
        body = next(Path(o["body_file"]).read_text() for o in data["ops"] if o["op"] == "pr")
        problems = guard.check(clone, base_tip=tip, head=head, head_ref=branch, cross_repo=False)
        out = self.lab.tmp / f"art-{name}"
        base_sha = core_git.run(clone, "merge-base", tip, head).strip()
        self.assertEqual(gate_run.run(clone, config_sha=tip, base_sha=base_sha, out=out, environ=self.environ,
                                      applicable=True), 0)
        meta = {}
        results, applicable, problems_art = artifacts.read_results(out, meta=meta)
        self.assertEqual(problems_art, [], name)
        pr = PrFacts(1, head, branch, "main", "main", body, False)
        number = evaluate.pr_issue_number(pr)
        inputs = GateInputs(
            where=GITHUB, repo=clone, cfg=load_config_at(clone, tip), base_sha=base_sha, head_sha=head,
            pr=pr, block=prblock.parse(body),
            issue=IssueFacts(number, "open", ()) if number else None, commands=results,
            base_ids=self.base_ids[repo], base_ids_source=BASE_FROM_CACHE,
            waiver_text=core_git.text_at(clone, head, f".tollgate/waivers/{number}.toml") if number else None,
            sentinel_open=[])
        ev = evaluate.evaluate(inputs)
        git(clone, "switch", "-q", "--detach", "origin/main")
        return data, bool(problems), ev

    def test_expected_states_match_the_gate_calculation(self):
        names = [n for n, c in make_case.CASES.items() if c.oracle]
        self.assertGreaterEqual(len(names), 20)
        for name in names:
            with self.subTest(name):
                data, guard_red, ev = self.judge(name)
                want = data["expect"][-1]["states"]
                got = {"tollgate/guard": "failure" if guard_red else "success",
                       "tollgate/verdict": ev.verdict_state,
                       "tollgate/attention": "error" if ev.errors else ev.attention_state}
                for context, state in want.items():
                    if state in (make_case.ANY, make_case.NONE):
                        continue
                    if context == "tollgate/guard" and data["repo"] == "detect":
                        pass            # guard gira anche su detect: lo stato è quello calcolato
                    self.assertEqual(got[context], state, f"{name} {context}: {[i.text for i in ev.red]} "
                                                          f"{[i.key for i in ev.attention]} {ev.errors}")

    def test_the_xml_entity_case_is_red_not_error_when_only_tools_change(self):
        data, _, ev = self.judge("rosso-entita-tools")
        self.assertEqual(ev.errors, [])
        self.assertIn("command_red", [i.key for i in ev.red])

    def test_the_clean_case_has_no_red_item(self):
        _, guard_red, ev = self.judge("verde-pulita")
        self.assertFalse(guard_red)
        self.assertEqual([i.key for i in ev.red], [])
        self.assertEqual([i.key for i in ev.attention if i.key not in ()], [])

    def test_the_red_items_of_selected_cases(self):
        expected = {
            "rosso-test-tolti": {"test_id_missing", "base_id_missing"},
            "rosso-skip": {"skip_added"},
            "rosso-fuori-scope": {"out_of_scope"},
            "rosso-or-true": {"command_red"},
            "rosso-livello": {"level_below_minimum"},
            "rosso-l2-mancante": {"l2_missing"},
            "rosso-zero-test": {"command_empty"},
            "rosso-piano-file-nuovo": {"out_of_scope"},
            "rosso-deroga-altra-issue": {"test_id_missing", "out_of_scope"},
        }
        for name, keys in expected.items():
            with self.subTest(name):
                _, _, ev = self.judge(name)
                self.assertTrue(keys <= {i.key for i in ev.red}, f"{name}: {[i.key for i in ev.red]}")

    def test_the_attention_items_of_selected_cases(self):
        expected = {
            "verde-config": {"tollgate_config"},
            "verde-ramo-libero": {"not_tg_branch"},
            "verde-workflow-ci": {"waiver_ci", "ci_waived_workflow"},
            "attenzione-deroga-test": {"waiver_test"},
            "attenzione-piano-testo": {"plan_changed"},
            "attenzione-tetto-livello": {"level_cap"},
            "attenzione-zero-test": {"no_tests_counted"},
            "rosso-piano-file-nuovo": {"plan_changed"},
        }
        for name, keys in expected.items():
            with self.subTest(name):
                _, _, ev = self.judge(name)
                self.assertTrue(keys <= {i.key for i in ev.attention},
                                f"{name}: {[i.key for i in ev.attention]}")


class ErrorCasesTest(unittest.TestCase):
    """I casi `error` si ottengono cambiando la copia di `gate run` installata nel repo: la esegue `tollgate-run` dal
    checkout della testa. Qui si lancia quella copia (nessuna rete) e si guardano gli artefatti che scrive."""

    @classmethod
    def setUpClass(cls):
        cls.lab = Lab()

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def run_patched(self, name: str) -> list[str]:
        data = self.lab.build(name)
        clone = self.lab.clones[data["repo"]]
        head = git(clone, "rev-parse", data["branch"])
        checkout = self.lab.tmp / f"head-{name}"
        git(clone, "worktree", "add", "-q", "--detach", str(checkout), head)
        event = self.lab.tmp / f"event-{name}.json"
        event.write_text(json.dumps({"pull_request": {"base": {"ref": "main"}, "head": {"ref": data["branch"]}},
                                     "repository": {"default_branch": "main"}}))
        out = self.lab.tmp / f"art-{name}"
        r = subprocess.run([sys.executable, "-B", ".github/tollgate/bin/tollgate", "gate", "run", "--event",
                            str(event), "--out", str(out)], cwd=checkout, capture_output=True, text=True,
                           env={"PATH": os.environ["PATH"], "HOME": str(self.lab.tmp), "LANG": "C.UTF-8"})
        self.assertEqual(r.returncode, 0, r.stderr)
        return artifacts.validate(out)

    def test_dotdot_report_is_rejected_by_the_artifact_check(self):
        problems = self.run_patched("error-dotdot")
        self.assertTrue(any("'..'" in p for p in problems), problems)

    def test_entity_report_is_rejected_by_the_artifact_check(self):
        problems = self.run_patched("error-entita")
        self.assertTrue(any("evil.xml" in p for p in problems), problems)


class BaselineTest(unittest.TestCase):
    def test_baseline_config_loads_for_both_repos(self):
        from tollgate_core import config
        for repo in make_case.REPOS:
            cfg = config.load_config_text(make_case.toml_text(repo))
            self.assertEqual(cfg.get("gate.mode"), repo)
            self.assertEqual(cfg.get("project.allow_no_tests"), repo == "detect")
            self.assertEqual(sorted(cfg.profiles), ["notes", "web"])

    def test_cli_lists_every_case(self):
        out = subprocess.run([sys.executable, "-B", str(ROOT / "spikes" / "p4" / "make_case.py"), "list"],
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual([line.split("\t")[0] for line in out.splitlines()], list(make_case.CASES))


if __name__ == "__main__":
    unittest.main()
