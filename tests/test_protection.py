import unittest

from tests.test_gh import FakeGhCase
from tollgate_gate import protection

DETECT_MSG = "Upgrade to GitHub Pro or make this repository public to enable this feature."
PATH = "repos/{owner}/{repo}/branches/main/protection"


def good(app_id=15368) -> dict:
    """Una protezione completa, nella forma della GET di GitHub."""
    return {
        "required_pull_request_reviews": {"required_approving_review_count": 0},
        "required_status_checks": {
            "strict": True, "contexts": ["tollgate/guard", "tollgate/verdict"],
            "checks": [{"context": "tollgate/guard", "app_id": app_id},
                       {"context": "tollgate/verdict", "app_id": app_id}]},
        "enforce_admins": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
    }


class ClassifyTest(unittest.TestCase):
    def test_classify(self):
        c = protection.classify
        self.assertEqual(c(403, DETECT_MSG), "detect")
        self.assertEqual(c(403, "Must have admin rights to Repository."), "undetermined")
        self.assertEqual(c(200, ""), "protected")
        self.assertEqual(c(404, "Branch not protected"), "protected_unset")
        self.assertEqual(c(None, ""), "undetermined")

    def test_other_answers_are_never_protected(self):
        c = protection.classify
        for status, message in ((404, "Not Found"), (403, ""), (500, "Branch not protected"),
                                (401, "Bad credentials"), (302, ""), (200 + 1, "")):
            self.assertEqual(c(status, message), "undetermined", (status, message))


class MissingTest(unittest.TestCase):
    def test_complete_protection_has_nothing_missing(self):
        self.assertEqual(protection.missing(good()), [])

    def test_missing_fields(self):
        data = good()
        data["required_status_checks"]["strict"] = False
        data["required_status_checks"]["checks"][0]["app_id"] = -1
        got = protection.missing(data)
        self.assertEqual(len(got), 2, got)
        self.assertTrue(any("tollgate/guard" in m and "-1" in m for m in got), got)
        self.assertTrue(any("strict" in m for m in got), got)

    def test_every_field_is_checked(self):
        got = protection.missing({})
        self.assertEqual(len(got), 5, got)       # PR, i due controlli, strict, admin
        data = good()
        data.update(required_pull_request_reviews=None, enforce_admins={"enabled": False},
                    allow_force_pushes={"enabled": True}, allow_deletions={"enabled": True})
        got = protection.missing(data)
        self.assertEqual(len(got), 4, got)

    def test_context_without_a_source_is_missing(self):
        data = good()
        data["required_status_checks"]["checks"] = [{"context": "tollgate/guard",
                                                     "app_id": 15368}]
        got = protection.missing(data)       # verdict resta solo in `contexts`: nessuna sorgente
        self.assertEqual(len(got), 1, got)
        self.assertIn("tollgate/verdict", got[0])

    def test_unreadable_values_count_as_missing(self):
        data = good()
        data["required_status_checks"] = "x"
        data["enforce_admins"] = None
        self.assertGreaterEqual(len(protection.missing(data)), 4)


class BodyTest(unittest.TestCase):
    def test_body_never_minus_one(self):
        body = protection.protection_body(15368)
        self.assertEqual([c["app_id"] for c in body["required_status_checks"]["checks"]],
                         [15368, 15368])
        self.assertEqual([c["context"] for c in body["required_status_checks"]["checks"]],
                         ["tollgate/guard", "tollgate/verdict"])
        self.assertEqual(protection.missing({**body, "enforce_admins": {"enabled": True}}), [])
        for bad in (-1, 0, None, "15368", True, 1.5):
            with self.assertRaises(ValueError, msg=bad):
                protection.protection_body(bad)

    def test_body_has_every_required_rule(self):
        body = protection.protection_body(1)
        self.assertTrue(body["required_status_checks"]["strict"])
        self.assertTrue(body["enforce_admins"])
        self.assertIn("required_pull_request_reviews", body)
        self.assertIsNone(body["restrictions"])
        self.assertFalse(body["allow_force_pushes"])
        self.assertFalse(body["allow_deletions"])

    def test_template_has_a_placeholder_and_never_minus_one(self):
        text = protection.body_template()
        self.assertEqual(text.count(f'"{protection.APP_ID_PLACEHOLDER}"'), 2)
        self.assertNotIn("-1", text)


class ReadTest(FakeGhCase):
    def read(self, branch="main"):
        return protection.read(self.state, self.tmp, branch)

    def status(self, status, message="", body=None):
        entry = {"status": status, "message": message}
        if body is not None:
            entry["body"] = body
        self.set(api_status={PATH: entry})

    def test_detect(self):
        self.status(403, DETECT_MSG, {"message": DETECT_MSG})
        got = self.read()
        self.assertEqual((got.kind, got.missing), ("detect", []))

    def test_protected_lists_missing(self):
        data = good()
        data["enforce_admins"] = {"enabled": False}
        self.status(200, "", data)
        got = self.read()
        self.assertEqual(got.kind, "protected")
        self.assertEqual(len(got.missing), 1, got)
        self.assertEqual(self.calls()[0], ["api", "--include", PATH])

    def test_unset(self):
        self.status(404, "Branch not protected", {"message": "Branch not protected"})
        got = self.read()
        self.assertEqual((got.kind, got.missing), ("protected_unset", []))

    def test_no_admin_rights_is_undetermined_with_the_message(self):
        self.status(403, "Must have admin rights to Repository.",
                    {"message": "Must have admin rights to Repository."})
        got = self.read()
        self.assertEqual(got.kind, "undetermined")
        self.assertIn("admin rights", got.note)

    def test_gh_failure_is_undetermined(self):
        self.set()                           # il finto non sa rispondere: nessuna riga di stato
        got = self.read()
        self.assertEqual(got.kind, "undetermined")
        self.assertTrue(got.note)

    def test_bad_branch_name_is_undetermined_without_calling_gh(self):
        got = self.read("main/../x y")
        self.assertEqual(got.kind, "undetermined")
        self.assertFalse(self.log.exists())

    def test_actions_enabled(self):
        path = "repos/{owner}/{repo}/actions/permissions"
        self.set(api_status={path: {"status": 200, "body": {"enabled": False}}})
        self.assertIs(protection.actions_enabled(self.state, self.tmp), False)
        self.set(api_status={path: {"status": 200, "body": {"enabled": True}}})
        self.assertIs(protection.actions_enabled(self.state, self.tmp), True)
        self.set()
        self.assertIsNone(protection.actions_enabled(self.state, self.tmp))
        self.set(api_status={path: {"status": 200, "body": {"x": 1}}})
        self.assertIsNone(protection.actions_enabled(self.state, self.tmp))


if __name__ == "__main__":
    unittest.main()
