import unittest

from tollgate_analysis import brief, plan, report

FENCE_TEXT = "usa ``` e ````` nel testo\n```python\nx = 1\n```"


def impl(**kw):
    base = dict(issue=7, task=2, name="tg-7-t2", agent_type="tollgate:implementer",
                model_hint=None, task_text="### Task 2: Somma\n\n- Create: `a.py`",
                scope=["a.py", "tests/test_a.py"], related_tests=["tests/test_a.py"],
                must_haves=[plan.MustHave("M1", "Somma corretta", ["t::a"])],
                skills=["ui-ux-pro-max"], absent_skills=[],
                verify_cmd="'/p/bin/tollgate' verify", fix_findings=[], fix_round=0)
    base.update(kw)
    return brief.ImplBrief(**base)


def review(**kw):
    base = dict(issue=7, task=2, sha="a" * 40, code="CODE-123", base="b" * 40, head="a" * 40,
                brief_path=".tollgate-run/7/task-2.md", diff_path=".tollgate-run/7/diff-2.patch",
                lines=50, lines_warn=200, lines_max=500, concerns="", reviewer_skills=[],
                standard=False)
    base.update(kw)
    return brief.ReviewBrief(**base)


class FenceTest(unittest.TestCase):
    def test_fence_longer_than_content(self):
        self.assertEqual(brief.fence("niente"), "```")
        self.assertEqual(brief.fence(FENCE_TEXT), "`" * 6)
        self.assertEqual(brief.fence("````"), "`" * 5)


class ImplementerBriefTest(unittest.TestCase):
    def test_implementer_brief_has_name_verify_and_report_fields(self):
        out = brief.implementer_brief(impl())
        self.assertIn("tg-7-t2", out)
        self.assertIn("'/p/bin/tollgate' verify", out)
        self.assertIn("18.5", out)
        self.assertIn("block open test_spec_conflict", out)
        for field in report.REQUIRED:
            self.assertIn(f'"{field}"', out)
        order = [out.index(x) for x in ("tg-7-t2", "### Task 2: Somma", "tests/test_a.py",
                                        "Somma corretta", "ui-ux-pro-max", "TDD",
                                        "'/p/bin/tollgate' verify")]
        self.assertEqual(order, sorted(order))

    def test_task_text_in_longer_fence(self):
        out = brief.implementer_brief(impl(task_text=FENCE_TEXT))
        self.assertIn("`" * 6 + "\n" + FENCE_TEXT + "\n" + "`" * 6, out)

    def test_absent_skill_marked(self):
        out = brief.implementer_brief(impl(skills=["a", "b:c"], absent_skills=["b:c"]))
        self.assertIn("- a\n", out)
        self.assertIn("- b:c (assente)", out)

    def test_fix_brief_includes_findings_in_fence(self):
        f = [{"severity": "major", "file": "a.py", "line": 3, "rule": "R-1",
              "text": "usa ``` male"}]
        out = brief.implementer_brief(impl(fix_findings=f, fix_round=4, model_hint="inherit"))
        self.assertIn("giro di correzione 4", out)
        self.assertIn("a.py:3", out)
        self.assertIn("usa ``` male", out)
        self.assertIn("````\n- [major]", out)
        self.assertIn("model: inherit", out)
        self.assertNotIn("giro di correzione", brief.implementer_brief(impl()))


class ReviewBriefTest(unittest.TestCase):
    def test_review_brief_has_sha_code_and_size_warning(self):
        out = brief.review_brief(review(lines=250))
        self.assertIn('"sha": "' + "a" * 40 + '", "code": "CODE-123"', out)
        self.assertIn("AVVISO DIMENSIONE", out)
        self.assertNotIn("AVVISO DIMENSIONE", brief.review_brief(review(lines=50)))

    def test_concerns_fenced_and_standard(self):
        out = brief.review_brief(review(concerns="dubbio ``` qui", standard=True,
                                        reviewer_skills=["axe"]))
        self.assertIn("````\ndubbio ``` qui\n````", out)
        self.assertIn("blocker", out)
        self.assertIn("axe", out)
        self.assertNotIn("salute del codice", brief.review_brief(review()))


def final(**kw):
    base = dict(issue=7, cycle=2, sha="a" * 40, code="c0de1234", base="b" * 40, head="a" * 40,
                diff_path=".tollgate-run/7/final-2.diff", plan_path="docs/p.md",
                plan_sha="c" * 40,
                must_haves=[plan.MustHave("M1", "Somma corretta", ["t::a"])],
                scope=["src/app.py"], checklists=["controlla il contrasto"],
                severity={"blocker": "perdita di dati", "major": "fallisce così com'è"},
                issue_file=".tollgate-run/7/issue.md", role="tollgate:final-reviewer")
    base.update(kw)
    return brief.FinalBrief(**base)


class FinalBriefTest(unittest.TestCase):
    def test_final_brief_has_sha_code_rules_and_format(self):
        out = brief.final_review_brief(final())
        self.assertIn('"sha": "' + "a" * 40 + '", "code": "c0de1234"', out)
        self.assertIn('"outcome": "ok" | "needs_fix" | "needs_you"', out)
        self.assertIn('"confidence"', out)
        for needle in ("R-", "passo del piano", "asserzioni", "casi speciali", "perdita di dati",
                       "Somma corretta", "src/app.py", "controlla il contrasto",
                       "non modificare", "test che scrivono file", "final-reviewer",
                       "docs/p.md", "c" * 40):
            self.assertIn(needle, out)

    def test_specialist_role_named_and_text_fenced(self):
        out = brief.final_review_brief(final(role="probe:final-security",
                                             checklists=["usa ``` qui"]))
        self.assertIn("probe:final-security", out)
        self.assertIn("````\n- usa ``` qui\n````", out)


class VerifierBriefTest(unittest.TestCase):
    def test_verifier_brief_fences_findings(self):
        f = [{"id": "f-1-1", "severity": "major", "file": "a.py", "line": 3, "rule": "R-1",
              "text": "usa ``` male"}]
        out = brief.verifier_brief(brief.VerifierBrief(
            issue=7, cycle=1, sha="a" * 40, code="c0de", diff_path="d.diff", findings=f))
        self.assertIn("````\n- f-1-1", out)
        self.assertIn("usa ``` male", out)
        self.assertIn('"results"', out)
        self.assertIn("senza discutere con il revisore", out)
        self.assertIn("un rilievo senza prova si scarta", out)
        self.assertIn('"code": "c0de"', out)


if __name__ == "__main__":
    unittest.main()
