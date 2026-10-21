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


COUNTS = {"blocker": 0, "major": 1, "moderate": 0, "minor": 2}
SPEC_PATH = "docs/superpowers/specs/s.md"
BLOB = "a" * 40
REV = "docs/superpowers/reviews"


def approval(issue, *, path=SPEC_PATH, sha=BLOB, slices=1, adversarial="closed", lens=None):
    return (f"{REV}/{issue}/spec-approval.md", approvals.render_approval(
        {"kind": "spec-approval", "path": path, "sha": sha, "slices": slices,
         "adversarial": adversarial, "lens": lens, "act_id": "a-1",
         "approved_at": "2026-10-20T10:00:00Z"}))


def report(kind, number=1, **over):
    fields = {"schema_version": 1, "kind": kind, "number": number, "viewpoint": None,
              "spec_sha": BLOB, "counts": dict(COUNTS), "outcome": "findings"}
    fields.update(over)
    return approvals.render_report(fields, "corpo\n")


class HeaderTest(unittest.TestCase):
    def test_quoted_value_with_comment(self):
        h = approvals.parse_header('---\nsha: "abc" # nota\nother: \'x y\'   # c\nn: 30 # n\n---\n')
        self.assertEqual((h["sha"], h["other"], h["n"]), ("abc", "x y", 30))

    def test_counts_become_dict(self):
        h = approvals.parse_header("---\ncounts: {blocker: 0, major: 1}\nbad: {a: x}\n---\n")
        self.assertEqual(h["counts"], {"blocker": 0, "major": 1})
        self.assertEqual(h["bad"], "{a: x}")

    def test_render_parse_roundtrip_approval(self):
        fields = {"schema_version": 1, "kind": "plan-approval", "path": "docs/p.md",
                  "sha": BLOB, "spec_sha": "b" * 40, "adversarial": "off", "lens": None,
                  "act_id": "a-9", "approved_at": "2026-10-20T10:00:00Z"}
        text = approvals.render_approval(fields)
        self.assertEqual(approvals.parse_approval(text), fields)
        self.assertIn(f'sha: "{BLOB}"', text)

    def test_render_parse_roundtrip_report(self):
        fields = {"schema_version": 1, "kind": "spec-lens", "number": 2, "viewpoint": "sicurezza",
                  "spec_sha": BLOB, "counts": dict(COUNTS), "outcome": "findings"}
        text = approvals.render_report(fields, "# Corpo\n")
        self.assertIn("counts: {blocker: 0, major: 1, moderate: 0, minor: 2}", text)
        self.assertEqual(approvals.parse_report_header(text), fields)
        self.assertTrue(text.endswith("# Corpo\n"))

    def test_render_rejects_forbidden_characters(self):
        for bad in ("a\nb", 'a"b', "a\x00b", "a\rb", "a\x1bb"):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(ValueError):
                    approvals.render_approval({"kind": "spec-approval", "path": bad, "sha": "x"})
                with self.assertRaises(ValueError):
                    approvals.render_report({"kind": "spec-lens", "viewpoint": bad,
                                             "number": 1, "counts": dict(COUNTS)}, "")

    def test_report_header_rejects_bad_counts(self):
        def with_(**over):
            fields = {"kind": "spec-adversarial", "number": 1, "counts": dict(COUNTS)}
            fields.update(over)
            return approvals.render_report(fields, "")
        self.assertIsNotNone(approvals.parse_report_header(with_()))
        for over in ({"counts": {"blocker": 0, "major": 0, "moderate": 0}},
                     {"counts": {**COUNTS, "minor": -1}},
                     {"counts": {**COUNTS, "extra": 1}},
                     {"counts": "x"},
                     {"number": 0}, {"number": "1"}, {"kind": "spec-approval"}):
            with self.subTest(over=over):
                self.assertIsNone(approvals.parse_report_header(with_(**over)))

    def test_approval_is_not_a_report_and_vice_versa(self):
        self.assertIsNone(approvals.parse_report_header(SPEC))
        self.assertIsNone(approvals.parse_approval(report("spec-lens")))

    def test_approval_listing(self):
        paths = [f"{REV}/3/spec-approval.md", f"{REV}/3/plan-approval.md",
                 f"{REV}/5/spec-adversarial-1.md", f"{REV}/x/spec-approval.md",
                 f"{REV}/5/spec-approval.md", f"{REV}/5/sub/spec-approval.md"]
        self.assertEqual(approvals.approval_listing(paths),
                         [f"{REV}/3/spec-approval.md", f"{REV}/5/spec-approval.md"])

    def test_report_listing(self):
        paths = [f"{REV}/3/spec-adversarial-1.md", f"{REV}/3/spec-lens-2.md",
                 f"{REV}/3/spec-approval.md", f"{REV}/5/plan-adversarial-1.md",
                 f"{REV}/3/sub/spec-lens-1.md", f"{REV}/3/spec-lens-stato.md",
                 f"{REV}/3/note-1.md", f"{REV}/30/spec-lens-1.md"]
        self.assertEqual(approvals.report_listing(paths, [f"{REV}/3"]),
                         [f"{REV}/3/spec-adversarial-1.md", f"{REV}/3/spec-lens-2.md"])
        self.assertEqual(approvals.report_listing(paths, [f"{REV}/3", f"{REV}/5"]),
                         [f"{REV}/3/spec-adversarial-1.md", f"{REV}/3/spec-lens-2.md",
                          f"{REV}/5/plan-adversarial-1.md"])
        self.assertEqual(approvals.report_listing(paths, []), [])


class LocateTest(unittest.TestCase):
    def test_locate_own_then_other_issue(self):
        own, other = dict([approval(7)]), dict([approval(3)])
        path, header = approvals.locate_spec_approval(
            own | other, issue=7, spec_path=SPEC_PATH, spec_blob=BLOB)
        self.assertEqual(path, f"{REV}/7/spec-approval.md")
        path, header = approvals.locate_spec_approval(
            other, issue=7, spec_path=SPEC_PATH, spec_blob=BLOB)
        self.assertEqual(path, f"{REV}/3/spec-approval.md")
        files = dict([approval(5), approval(3)])
        self.assertEqual(approvals.locate_spec_approval(
            files, issue=7, spec_path=SPEC_PATH, spec_blob=BLOB)[0], f"{REV}/3/spec-approval.md")
        self.assertIsNone(approvals.locate_spec_approval(
            files, issue=7, spec_path=SPEC_PATH, spec_blob="f" * 40))

    def test_current_beats_own_stale(self):
        x, y = "1" * 40, "2" * 40
        files = dict([approval(7, sha=x), approval(3, sha=y)])
        where = {"issue": 7, "spec_path": SPEC_PATH}
        self.assertEqual(approvals.locate_spec_approval(files, spec_blob=y, **where)[0],
                         f"{REV}/3/spec-approval.md")
        self.assertEqual(approvals.locate_spec_approval(files, spec_blob=x, **where)[0],
                         f"{REV}/7/spec-approval.md")
        self.assertEqual(approvals.locate_spec_approval(files, spec_blob=None, **where)[0],
                         f"{REV}/7/spec-approval.md")
        # nessuna corrente: la propria, anche superata
        path, header = approvals.locate_spec_approval(files, spec_blob="f" * 40, **where)
        self.assertEqual((path, header["sha"]), (f"{REV}/7/spec-approval.md", x))

    def test_blob_none_matches_path_only(self):
        files = dict([approval(3, sha="whatever")])
        self.assertEqual(approvals.locate_spec_approval(
            files, issue=7, spec_path=SPEC_PATH, spec_blob=None)[0], f"{REV}/3/spec-approval.md")
        self.assertIsNone(approvals.locate_spec_approval(
            files, issue=7, spec_path="docs/superpowers/specs/other.md", spec_blob=None))

    def test_ignores_invalid_and_wrong_kind(self):
        files = {f"{REV}/3/spec-approval.md": "niente intestazione",
                 f"{REV}/5/spec-approval.md": report("spec-lens")}
        self.assertIsNone(approvals.locate_spec_approval(
            files, issue=7, spec_path=SPEC_PATH, spec_blob=None))


PLAN_BLOB, PLAN_PATH = "c" * 40, "docs/superpowers/plans/p.md"


def plan_approval(issue=7, **over):
    fields = {"kind": "plan-approval", "path": PLAN_PATH, "sha": PLAN_BLOB, "spec_sha": BLOB,
              "adversarial": "closed", "act_id": "a-2", "approved_at": "2026-10-20T11:00:00Z"}
    fields.update(over)
    return f"{REV}/{issue}/plan-approval.md", approvals.render_approval(fields)


def full(issue=7, spec_issue=7, **spec_over):
    files = dict([approval(spec_issue, **spec_over), plan_approval(issue)])
    files[f"{REV}/{spec_issue}/spec-adversarial-1.md"] = report("spec-adversarial")
    files[f"{REV}/{issue}/plan-adversarial-1.md"] = report("plan-adversarial",
                                                           plan_sha=PLAN_BLOB)
    return files


def check_kw(**over):
    kw = dict(issue=7, spec_path=SPEC_PATH, spec_blob=BLOB, plan_path=PLAN_PATH,
              plan_blob=PLAN_BLOB)
    kw.update(over)
    return kw


def check(files, **over):
    return approvals.check_l2(files, **check_kw(**over))


def detail(files, **over):
    return approvals.check_l2_detail(files, **check_kw(**over))


def kinds(problems):
    return [p.kind for p in problems]


class CheckL2Test(unittest.TestCase):
    def test_check_l2_matrix(self):
        self.assertEqual(check(full()), [])
        # approvazione del piano con spec_sha vecchio
        files = full()
        files.update([plan_approval(spec_sha="old")])
        self.assertEqual(len(check(files)), 1)
        # nessun report avversariale della spec
        files = full()
        del files[f"{REV}/7/spec-adversarial-1.md"]
        problems = check(files)
        self.assertEqual(len(problems), 1)
        self.assertIn("spec-adversarial", problems[0])
        files.update([approval(7, adversarial="off")])
        self.assertEqual(check(files), [])
        # lenti chiuse con tre fette, senza report
        files = full(slices=3, lens="closed")
        problems = check(files)
        self.assertEqual(len(problems), 1)
        self.assertIn("spec-lens", problems[0])
        files[f"{REV}/7/spec-lens-1.md"] = report("spec-lens", viewpoint="v")
        self.assertEqual(check(files), [])
        self.assertEqual(check(full(slices=3, lens="suspended")), [])
        self.assertEqual(check(full(slices=1, lens="closed")), [])
        # intestazione non valida: non conta
        files = full()
        files[f"{REV}/7/spec-adversarial-1.md"] = report("spec-adversarial", number=0)
        self.assertEqual(len(check(files)), 1)

    def test_missing_files_are_named(self):
        problems = check({})
        self.assertTrue(any(f"{REV}/7/plan-approval.md" in p for p in problems))
        self.assertTrue(any("spec-approval" in p and SPEC_PATH in p for p in problems))

    def test_plan_changed_or_adversarial_missing(self):
        self.assertEqual(len(check(full(), plan_blob="d" * 40)), 1)
        files = full()
        del files[f"{REV}/7/plan-adversarial-1.md"]
        problems = check(files)
        self.assertEqual(len(problems), 1)
        self.assertIn("plan-adversarial", problems[0])
        files.update([plan_approval(adversarial="off")])
        self.assertEqual(check(files), [])

    def test_later_slice_uses_other_issue_reports(self):
        files = full(issue=9, spec_issue=3)
        self.assertEqual(check(files, issue=9), [])
        del files[f"{REV}/3/spec-adversarial-1.md"]
        problems = check(files, issue=9)
        self.assertEqual(len(problems), 1)
        self.assertIn(f"{REV}/3/", problems[0])

    def test_spec_changed_after_approval(self):
        problems = check(full(), spec_blob="e" * 40)
        self.assertTrue(problems)
        self.assertTrue(all(isinstance(p, str) for p in problems))

    def test_unregistered_paths(self):
        self.assertTrue(any("spec" in p for p in check(full(), spec_path=None, spec_blob=None)))
        self.assertTrue(any("piano" in p for p in check(full(), plan_path=None, plan_blob=None)))


class JudgeSpecTest(unittest.TestCase):
    where = {"issue": 7, "spec_path": SPEC_PATH}

    def judge(self, files, blob=BLOB):
        return approvals.judge_spec(files, spec_blob=blob, **self.where)

    def test_statuses(self):
        self.assertEqual(self.judge({}).status, approvals.MISSING)
        cur = self.judge(dict([approval(3)]))
        self.assertEqual((cur.status, cur.found[0]), (approvals.CURRENT, f"{REV}/3/spec-approval.md"))
        own = self.judge(dict([approval(7, sha="old")]))
        self.assertEqual((own.status, own.found[0]), (approvals.STALE, f"{REV}/7/spec-approval.md"))

    def test_only_another_issue_stale(self):
        j = self.judge(dict([approval(3, sha="old")]))
        self.assertEqual((j.status, j.found), (approvals.STALE, None))
        self.assertEqual(j.approval[0], f"{REV}/3/spec-approval.md")

    def test_check_l2_detail_agrees_on_another_issue_stale(self):
        files = full(issue=9, spec_issue=3)
        files.update([approval(3, sha="old"), plan_approval(9, spec_sha="old")])
        problems = detail(files, issue=9)
        self.assertEqual(kinds(problems), ["stale"])
        self.assertIn(f"{REV}/3/spec-approval.md", problems[0].text)
        self.assertEqual(approvals.judge_spec(files, issue=9, spec_path=SPEC_PATH,
                                              spec_blob=BLOB).status, approvals.STALE)


class CheckL2DetailTest(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(detail(full()), [])
        self.assertEqual(detail(full(), components={"spec_adversary": True, "spec_audit": True,
                                                    "plan_adversary": True}), [])

    def test_check_l2_detail_kinds(self):
        files = full()
        del files[f"{REV}/7/spec-approval.md"]
        self.assertEqual(kinds(detail(files)), ["missing"])
        files = full()
        files.update([approval(7, sha="old"), plan_approval(spec_sha="old")])
        self.assertEqual(kinds(detail(files)), ["stale"])
        files = full()
        files.update([approval(7, slices="tre")])
        problems = detail(files)
        self.assertEqual(kinds(problems), ["missing"])
        files = full()
        files.update([plan_approval(path="docs/superpowers/plans/altro.md")])
        self.assertEqual(kinds(detail(files)), ["missing"])
        # piano superato e nessun report del piano: un solo problema, `stale`
        files = full()
        del files[f"{REV}/7/plan-adversarial-1.md"]
        problems = detail(files, plan_blob="d" * 40)
        self.assertEqual(kinds(problems), ["stale"])
        self.assertNotIn("report", problems[0].text)

    def test_reports_bound_to_approved_sha(self):
        files = full()
        files[f"{REV}/7/spec-adversarial-1.md"] = report("spec-adversarial", spec_sha="old")
        problems = detail(files)
        self.assertEqual(kinds(problems), ["missing"])
        self.assertIn("nessun report della spec sullo sha approvato", problems[0].text)
        # un secondo report sullo sha approvato basta
        files[f"{REV}/7/spec-adversarial-2.md"] = report("spec-adversarial", number=2)
        self.assertEqual(detail(files), [])
        # componenti spenti nell'intestazione: nessun report richiesto
        files = full(adversarial="off", lens="off")
        files[f"{REV}/7/spec-adversarial-1.md"] = report("spec-adversarial", spec_sha="old")
        self.assertEqual(detail(files), [])
        # i report del piano
        files = full()
        files[f"{REV}/7/plan-adversarial-1.md"] = report("plan-adversarial", plan_sha="old")
        problems = detail(files)
        self.assertEqual(kinds(problems), ["missing"])
        self.assertIn("nessun report del piano sullo sha approvato", problems[0].text)
        # un report senza alcun plan_sha non lega nulla
        files[f"{REV}/7/plan-adversarial-1.md"] = report("plan-adversarial")
        self.assertEqual(kinds(detail(files)), ["missing"])

    def test_lens_report_binds_the_spec(self):
        files = full(slices=3, lens="closed", adversarial="off")
        del files[f"{REV}/7/spec-adversarial-1.md"]
        files[f"{REV}/7/spec-lens-1.md"] = report("spec-lens", viewpoint="v", spec_sha="old")
        self.assertEqual(kinds(detail(files)), ["missing"])
        files[f"{REV}/7/spec-lens-1.md"] = report("spec-lens", viewpoint="v")
        self.assertEqual(detail(files), [])

    def test_check_l2_messages(self):
        text = lambda files, **over: [p.text for p in detail(files, **over)]  # noqa: E731
        self.assertEqual(check(full()), [])
        spec_file, plan_file = f"{REV}/7/spec-approval.md", f"{REV}/7/plan-approval.md"
        self.assertEqual(text({}), [
            f"manca il file di approvazione della spec {SPEC_PATH} con lo sha attuale "
            f"({spec_file})",
            f"manca il file di approvazione del piano {plan_file}"])
        self.assertEqual(text(full(), spec_path=None, spec_blob=None, plan_path=None,
                              plan_blob=None), [
            "spec non registrata o assente dall'albero: manca l'approvazione della spec "
            "(spec-approval.md)",
            f"piano non registrato o assente dall'albero: manca l'approvazione del piano "
            f"({plan_file})"])
        files = full()
        files.update([approval(7, sha="old"), plan_approval(spec_sha="old")])
        self.assertEqual(text(files), [f"{spec_file}: la spec {SPEC_PATH} è cambiata dopo "
                                       f"l'approvazione (rifai approve spec)"])
        files = full()
        files.update([approval(7, path="docs/superpowers/specs/altra.md")])
        self.assertEqual(text(files), [
            f"manca il file di approvazione della spec {SPEC_PATH} con lo sha attuale "
            f"({spec_file})"])
        files = full()
        files.update([plan_approval(path="docs/superpowers/plans/altro.md")])
        self.assertEqual(text(files), [f"{plan_file}: approva docs/superpowers/plans/altro.md, "
                                       f"non il piano registrato {PLAN_PATH}"])
        self.assertEqual(text(full(), plan_blob="d" * 40), [
            f"{plan_file}: il piano {PLAN_PATH} è cambiato dopo l'approvazione "
            f"(rifai approve plan)"])
        files = full()
        files.update([plan_approval(spec_sha="old")])
        self.assertEqual(text(files), [f"{plan_file}: approvato su una spec diversa da quella "
                                       f"approvata (rifai approve plan)"])
        files = full(slices="tre")
        self.assertEqual(text(files), [f"{spec_file}: slices non è un intero"])
        files = full()
        del files[f"{REV}/7/spec-adversarial-1.md"]
        self.assertEqual(text(files), [f"manca il report spec-adversarial-<n>.md valido in "
                                       f"{REV}/7/"])
        files = full()
        files[f"{REV}/7/spec-adversarial-1.md"] = report("spec-adversarial", spec_sha="old")
        self.assertEqual(text(files), [f"nessun report della spec sullo sha approvato in "
                                       f"{REV}/7/ (spec_sha {BLOB})"])

    def test_plan_approval_on_other_spec_is_missing(self):
        files = full()
        files.update([plan_approval(spec_sha="9" * 40)])
        problems = detail(files)
        self.assertEqual(kinds(problems), ["missing"])
        self.assertIn("spec diversa", problems[0].text)
        # una spec cambiata dopo l'approvazione, col piano approvato su quella: solo `stale`
        files = full()
        self.assertEqual(kinds(detail(files, spec_blob="e" * 40)), ["stale"])
        files = full()
        files.update([approval(7, sha="old")])
        files.update([plan_approval(spec_sha="old")])
        self.assertEqual(kinds(detail(files)), ["stale"])

    def test_header_off_with_component_on_is_missing(self):
        files = full(adversarial="off")
        problems = detail(files, components={"spec_adversary": True})
        self.assertEqual(kinds(problems), ["missing"])
        self.assertIn("spec_adversary", problems[0].text)
        self.assertEqual(detail(files, components={"spec_adversary": False}), [])
        self.assertEqual(detail(files, components=None), [])
        self.assertEqual(detail(files, components={}), [])
        files = full(lens="off")
        self.assertEqual(kinds(detail(files, components={"spec_audit": True})), ["missing"])
        files = full()
        files.update([plan_approval(adversarial="off")])
        self.assertEqual(kinds(detail(files, components={"plan_adversary": True})), ["missing"])
        self.assertEqual(detail(files, components={"plan_adversary": False}), [])

    def test_check_l2_is_the_texts_of_detail(self):
        files = full()
        files.update([approval(7, sha="old")])
        self.assertEqual(check(files), [p.text for p in detail(files)])


if __name__ == "__main__":
    unittest.main()
