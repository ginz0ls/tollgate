import os
import subprocess
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


def _done(rc=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(["gh"], rc, stdout, stderr)


EMPTY_500 = _done(1, stderr="unexpected end of JSON input\n")       # 500 a corpo vuoto, --paginate
HTTP_500 = _done(1, stderr="gh: Server Error (HTTP 500)\n")


class RetryTest(unittest.TestCase):
    """Le letture di `gh api` ritentano sui 5xx transitori; le scritture e i 4xx no."""

    def setUp(self):
        self.sleeps = []
        patch = mock.patch.object(ghcli, "_sleep", self.sleeps.append)
        patch.start()
        self.addCleanup(patch.stop)

    def answers(self, *results):
        patch = mock.patch.object(ghcli, "run", side_effect=list(results))
        run = patch.start()
        self.addCleanup(patch.stop)
        return run

    def test_get_500_then_ok(self):
        run = self.answers(HTTP_500, _done(stdout='{"a": 1}'))
        self.assertEqual(ghcli.api(None, ".", "p/x").data, {"a": 1})
        self.assertEqual((run.call_count, self.sleeps), (2, [2]))

    def test_paginate_empty_body_then_ok(self):
        run = self.answers(EMPTY_500, _done(stdout='{"n":1}\n{"n":2}\n'))
        got = ghcli.api(None, ".", "p/x", paginate=True, jq=".[]")
        self.assertEqual(got.data, [{"n": 1}, {"n": 2}])
        self.assertEqual(run.call_count, 2)

    def test_always_500_gives_todays_error(self):
        run = self.answers(HTTP_500, HTTP_500, HTTP_500)
        with self.assertRaises(ghcli.GhError) as e:
            ghcli.api(None, ".", "p/x")
        self.assertEqual(str(e.exception), "gh api p/x: gh: Server Error (HTTP 500)")
        self.assertEqual((run.call_count, self.sleeps), (3, [2, 4]))
        self.assertEqual(ghcli.RETRY_DELAYS_S, (2, 4))

    def test_writes_are_not_retried(self):
        for method in ("POST", "PATCH", "PUT", "DELETE"):
            with self.subTest(method=method):
                run = self.answers(HTTP_500, _done(stdout="{}"))
                with self.assertRaises(ghcli.GhError):
                    ghcli.api(None, ".", "p/x", method=method)
                self.assertEqual(run.call_count, 1)
        self.assertEqual(self.sleeps, [])

    def test_include_4xx_is_a_result_and_5xx_is_retried(self):
        def status(code):
            return _done(1, f"HTTP/2.0 {code} X\nA: b\r\n\r\n{{\"message\": \"m\"}}",
                         f"gh: m (HTTP {code})\n")
        for code in (403, 404):
            with self.subTest(code=code):
                run = self.answers(status(code), status(200))
                got = ghcli.api(None, ".", "p/x", include=True)
                self.assertEqual((got.status, got.data, run.call_count), (code, {"message": "m"}, 1))
        self.assertEqual(self.sleeps, [])
        # una riga di stato 502 ritenta anche se lo stderr non dice HTTP 5xx
        run = self.answers(_done(1, "HTTP/2.0 502 Bad Gateway\nA: b\r\n\r\n", "gh: boom\n"),
                           status(404))
        self.assertEqual(ghcli.api(None, ".", "p/x", include=True).status, 404)
        self.assertEqual((run.call_count, self.sleeps), (2, [2]))

    def test_4xx_without_include_is_not_retried(self):
        for code in (404, 422):
            with self.subTest(code=code):
                run = self.answers(_done(1, stderr=f"gh: m (HTTP {code})\n"), _done(stdout="{}"))
                with self.assertRaises(ghcli.GhError):
                    ghcli.api(None, ".", "p/x")
                self.assertEqual(run.call_count, 1)
        self.assertEqual(self.sleeps, [])

    def test_timeout_is_not_retried(self):
        run = self.answers(ghcli.GhError("gh api p/x: timeout dopo 60 s"), _done(stdout="{}"))
        with self.assertRaises(ghcli.GhError):
            ghcli.api(None, ".", "p/x")
        self.assertEqual((run.call_count, self.sleeps), (1, []))

    def test_run_json_lines_retries_api_reads_only(self):
        run = self.answers(EMPTY_500, _done(stdout='{"n":1}\n'))
        self.assertEqual(ghcli.run_json_lines(None, ".", ["api", "--paginate", "--jq", ".[]", "p"]),
                         [{"n": 1}])
        self.assertEqual(run.call_count, 2)
        for args in (["api", "--method", "POST", "p"], ["api", "-X", "POST", "p"],
                     ["api", "--method=POST", "p"], ["pr", "list", "--json", "number"]):
            with self.subTest(args=args):
                run = self.answers(HTTP_500, _done(stdout='{"n":1}\n'))
                with self.assertRaises(ghcli.GhError):
                    ghcli.run_json_lines(None, ".", args)
                self.assertEqual(run.call_count, 1)

    def test_run_json_retries_api_reads_only(self):
        run = self.answers(HTTP_500, _done(stdout='{"a": 1}'))
        self.assertEqual(ghcli.run_json(None, ".", ["api", "p"]), {"a": 1})
        self.assertEqual(run.call_count, 2)
        run = self.answers(HTTP_500, _done(stdout="[]"))
        with self.assertRaises(ghcli.GhError):
            ghcli.run_json(None, ".", ["pr", "create", "--title", "t"])
        self.assertEqual(run.call_count, 1)


class FakeGhFlakyTest(FakeGhCase):
    """`api_flaky` del gh finto: risponde prima con gli errori elencati, poi normalmente."""

    def test_flaky_path_fails_then_answers(self):
        sha = "a" * 40
        self.set(commit_pulls={sha: [{"number": 1}]},
                 api_flaky={f"repos/o/r/commits/{sha}/pulls": ["unexpected end of JSON input"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            got = ghcli.api(self.state, self.tmp, f"repos/o/r/commits/{sha}/pulls?per_page=100",
                            paginate=True, jq=".[]")
        self.assertEqual(got.data, [{"number": 1}])
        self.assertEqual(len(self.calls()), 2)
        sleep.assert_called_once_with(2)
        self.assertEqual(self.read()["api_flaky"], {f"repos/o/r/commits/{sha}/pulls": []})


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
