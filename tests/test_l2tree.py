import shutil
import tempfile
import unittest
from pathlib import Path

from tests.helpers import git as g, make_repo
from tollgate_analysis import approvals
from tollgate_flow import l2tree as flow_l2tree
from tollgate_gate import l2tree

SPEC = "docs/superpowers/specs/s.md"
OLD = "0" * 40


def approval(sha: str) -> str:
    return approvals.render_approval({"kind": "spec-approval", "path": SPEC, "sha": sha,
                                      "slices": 3, "adversarial": "closed", "lens": None})


class L2TreeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate l2tree "))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = make_repo(self.tmp / "repo con spazi")
        self.write(SPEC, "spec\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "spec")
        self.blob = g(self.repo, "rev-parse", f"HEAD:{SPEC}")

    def write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def approve(self, issue: int, sha: str) -> None:
        self.write(approvals.approval_paths(issue)[0], approval(sha))
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", f"approvazione {issue}")

    def state(self, spec_blob=None):
        return l2tree.spec_approval(self.repo, "HEAD", issue=7, spec_path=SPEC,
                                    spec_blob=spec_blob or self.blob)

    def test_reexport_is_the_same_code(self):
        for name in ("listing", "spec_approvals", "locate", "spec_approval", "collect",
                     "CURRENT", "STALE", "MISSING"):
            with self.subTest(name=name):
                self.assertIs(getattr(flow_l2tree, name), getattr(l2tree, name))

    def test_spec_approval_current_when_other_issue_approved_same_blob(self):
        self.approve(7, OLD)
        self.approve(9, self.blob)
        status, found = self.state()
        self.assertEqual((status, found[0]), (l2tree.CURRENT, approvals.approval_paths(9)[0]))
        self.assertEqual(l2tree.locate(self.repo, "HEAD", issue=7, spec_path=SPEC,
                                       spec_blob=self.blob)[0], approvals.approval_paths(9)[0])

    def test_own_stale_alone_is_stale(self):
        self.approve(7, OLD)
        status, found = self.state()
        self.assertEqual((status, found[0]), (l2tree.STALE, approvals.approval_paths(7)[0]))

    def test_only_another_stale_is_stale_without_found(self):
        self.approve(3, OLD)
        self.assertEqual(self.state(), (l2tree.STALE, None))

    def test_agrees_with_check_l2_detail_on_only_another_issue_stale(self):
        self.approve(3, OLD)
        status, found = self.state()
        problems = approvals.check_l2_detail(
            l2tree.spec_approvals(self.repo, "HEAD"), issue=7, spec_path=SPEC,
            spec_blob=self.blob, plan_path=None, plan_blob=None)
        self.assertEqual((status, found), (l2tree.STALE, None))
        self.assertEqual(problems[0].kind, status)

    def test_none_is_missing(self):
        self.assertEqual(self.state(), (l2tree.MISSING, None))

    def test_collect_takes_reports_of_the_current_approval_folder(self):
        self.approve(7, OLD)
        self.approve(9, self.blob)
        report = approvals.render_report(
            {"kind": "spec-adversarial", "number": 1, "spec_sha": self.blob,
             "counts": {"blocker": 0, "major": 0, "moderate": 0, "minor": 0}}, "ok\n")
        self.write("docs/superpowers/reviews/9/spec-adversarial-1.md", report)
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "report")
        files, found = l2tree.collect(self.repo, "HEAD", issue=7, spec_path=SPEC,
                                      spec_blob=self.blob)
        self.assertEqual(found[0], approvals.approval_paths(9)[0])
        self.assertIn("docs/superpowers/reviews/9/spec-adversarial-1.md", files)


if __name__ == "__main__":
    unittest.main()
