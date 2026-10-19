import unittest

from tollgate_analysis import approvals

SPEC = """---
schema_version: 1
kind: spec-approval
path: docs/superpowers/specs/s.md
sha: "0123456789abcdef0123456789abcdef01234567"
slices: 2
adversarial: closed
lens: null
act_id: a-1
approved_at: 2026-10-20T10:00:00Z
---
corpo
"""


class ApprovalTest(unittest.TestCase):
    def test_valid_header(self):
        h = approvals.parse_approval(SPEC)
        self.assertEqual((h["kind"], h["path"], h["slices"], h["lens"], h["adversarial"]),
                         ("spec-approval", "docs/superpowers/specs/s.md", 2, None, "closed"))
        self.assertEqual(h["sha"], "0123456789abcdef0123456789abcdef01234567")
        self.assertEqual(h["approved_at"], "2026-10-20T10:00:00Z")

    def test_plan_approval_with_bare_sha(self):
        h = approvals.parse_approval(
            "---\nkind: plan-approval\npath: p.md\nsha: abc123\nspec_sha: 'def456'\n---\n")
        self.assertEqual((h["kind"], h["sha"], h["spec_sha"]), ("plan-approval", "abc123", "def456"))

    def test_without_front_matter_is_none(self):
        self.assertIsNone(approvals.parse_approval("kind: spec-approval\nsha: x\npath: p\n"))
        self.assertIsNone(approvals.parse_approval(""))

    def test_unclosed_or_malformed_or_foreign_is_none(self):
        self.assertIsNone(approvals.parse_approval("---\nkind: spec-approval\nsha: x\npath: p\n"))
        self.assertIsNone(approvals.parse_approval("---\nkind: spec-approval\nsha x\n---\n"))
        self.assertIsNone(approvals.parse_approval("---\nkind: spec-adversarial\npath: p\n"
                                                   "sha: x\n---\n"))

    def test_missing_sha_or_path_is_none(self):
        self.assertIsNone(approvals.parse_approval("---\nkind: spec-approval\npath: p\n---\n"))
        self.assertIsNone(approvals.parse_approval("---\nkind: spec-approval\nsha: null\n"
                                                   "path: p\n---\n"))

    def test_approval_paths(self):
        self.assertEqual(approvals.approval_paths(7),
                         ("docs/superpowers/reviews/7/spec-approval.md",
                          "docs/superpowers/reviews/7/plan-approval.md"))


if __name__ == "__main__":
    unittest.main()
