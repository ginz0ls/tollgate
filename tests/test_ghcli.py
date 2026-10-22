import os
import unittest
from unittest import mock

from tests.test_gh import FakeGhCase
from tollgate_core import ghcli
from tollgate_flow import gh


class ApiIncludeTest(FakeGhCase):
    def api(self, *args, **kw):
        return ghcli.api(self.state, self.tmp, *args, **kw)

    def test_api_include_status_parsed(self):
        self.set(api_status={
            "repos/o/r/branches/main/protection": {
                "status": 403, "message": "Upgrade to GitHub Pro or make this repository public",
                "body": {"message": "Upgrade to GitHub Pro or make this repository public"}},
            "repos/o/r/branches/dev/protection": {
                "status": 404, "message": "Branch not protected",
                "body": {"message": "Branch not protected", "status": "404"}}})
        got = self.api("repos/o/r/branches/main/protection", include=True)
        self.assertEqual(got.status, 403)
        self.assertEqual(got.data["message"], "Upgrade to GitHub Pro or make this repository public")
        self.assertIn("HTTP 403", got.stderr)
        got = self.api("repos/o/r/branches/dev/protection", include=True)
        self.assertEqual((got.status, got.data["message"]), (404, "Branch not protected"))
        self.assertEqual(self.calls()[0], ["api", "--include", "repos/o/r/branches/main/protection"])

    def test_api_include_success_and_empty_body(self):
        self.set(api_status={"p/ok": {"status": 200, "body": {"enabled": True}},
                             "p/none": {"status": 404}})
        got = self.api("p/ok", include=True)
        self.assertEqual((got.status, got.data), (200, {"enabled": True}))
        got = self.api("p/none", include=True)
        self.assertEqual((got.status, got.data), (404, None))

    def test_api_include_accepts_lf_only_separator(self):
        fake = self.tmp / "gh-lf"
        fake.write_text("#!/bin/sh\nprintf 'HTTP/1.1 200 OK\\nX: y\\n\\n{\"a\": 1}'\n")
        fake.chmod(0o755)
        with mock.patch.dict(os.environ, {"TOLLGATE_GH": str(fake)}):
            got = self.api("x", include=True)
        self.assertEqual((got.status, got.data), (200, {"a": 1}))

    def test_without_include_an_error_raises(self):
        self.set(api_status={"p/x": {"status": 404, "message": "Not Found",
                                     "body": {"message": "Not Found"}}})
        with self.assertRaises(ghcli.GhError):
            self.api("p/x")

    def test_include_without_status_line_raises(self):
        self.set()
        with self.assertRaises(ghcli.GhError):
            self.api("repos/o/r/issues/5", include=True)    # il finto non sa rispondere: uscita 1

    def test_plain_get_returns_decoded_body(self):
        self.set(issues={"5": {"number": 5, "title": "t"}})
        got = self.api("repos/o/r/issues/5")
        self.assertEqual((got.status, got.data["number"]), (None, 5))

    def test_paginate_requires_jq(self):
        with self.assertRaises(ValueError):
            self.api("repos/o/r/issues/5/comments", paginate=True)
        with self.assertRaises(ValueError):
            self.api("p", paginate=True, jq=".[]", include=True)

    def test_paginate_with_jq_gives_list_of_values(self):
        self.set(prs=[self.pr(5, comments=[{"id": 1, "body": "a", "author": {"login": "github-actions"}},
                                           {"id": 2, "body": "b", "author": {"login": "mario"}}])])
        got = self.api("repos/o/r/issues/5/comments", paginate=True, jq=".[]")
        self.assertEqual([c["user"]["login"] for c in got.data], ["github-actions[bot]", "mario"])
        self.assertEqual(got.data[0]["user"]["type"], "Bot")
        self.assertEqual(self.calls()[0][:4], ["api", "--paginate", "--jq", ".[]"])

    def test_method_fields_and_input_go_as_arguments(self):
        self.set(api_status={"p/x": {"status": 200, "body": {}}})
        self.api("p/x", method="POST", fields={"state": "success"}, input_file=self.tmp / "in.json")
        self.assertEqual(self.calls()[0], ["api", "--method", "POST", "-f", "state=success",
                                           "--input", str(self.tmp / "in.json"), "p/x"])

    def test_file_fields_go_as_body_from_file(self):
        self.set(api_status={"p/x": {"status": 200, "body": {}}})
        self.api("p/x", method="POST", file_fields={"body": self.tmp / "b.md"})
        self.assertEqual(self.calls()[0], ["api", "--method", "POST", "-F",
                                           f"body=@{self.tmp / 'b.md'}", "p/x"])

    def test_bot_logins_cover_rest_and_graphql(self):
        self.assertEqual(ghcli.BOT_LOGINS, ("github-actions[bot]", "github-actions"))
        self.set(prs=[self.pr(5, comments=[{"body": "x", "author": {"login": "github-actions"}}])])
        graphql = gh.pr_comments(self.state, self.tmp, 5)[0]["author"]["login"]
        rest = self.api("repos/o/r/issues/5/comments", paginate=True, jq=".[]").data[0]["user"]["login"]
        self.assertTrue({graphql, rest} <= set(ghcli.BOT_LOGINS))


class ReexportTest(unittest.TestCase):
    def test_flow_gh_reexports(self):
        self.assertIs(gh.GhError, ghcli.GhError)
        for name in ("GH_ENV", "GH_TIMEOUT_S", "REQUIRED_CONTEXTS", "SENTINEL_TITLE", "gh_cmd",
                     "run_json", "run_json_lines", "decode_json_values"):
            with self.subTest(name=name):
                self.assertIs(getattr(gh, name), getattr(ghcli, name))
        self.assertIs(gh._run, ghcli.run)

    def test_decode_json_values_unchanged(self):
        self.assertEqual(ghcli.decode_json_values('{"a":1}\n{"b":2}'), [{"a": 1}, {"b": 2}])
        with self.assertRaises(ghcli.GhError):
            ghcli.decode_json_values("[1]")


if __name__ == "__main__":
    unittest.main()
