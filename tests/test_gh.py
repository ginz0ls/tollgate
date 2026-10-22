import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.flowkit import FAKEGH
from tests.helpers import TempState
from tollgate_flow import gh


class FakeGhCase(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.addCleanup(self.ts.cleanup)
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate gh "))
        self.data = self.tmp / "data.json"
        self.log = self.tmp / "log"
        patch = mock.patch.dict(os.environ, {
            "TOLLGATE_GH": str(FAKEGH), "TOLLGATE_FAKEGH_DATA": str(self.data),
            "TOLLGATE_FAKEGH_LOG": str(self.log)})
        patch.start()
        self.addCleanup(patch.stop)
        self.set()

    def set(self, **data):
        self.data.write_text(json.dumps(data))

    def read(self):
        return json.loads(self.data.read_text())

    def calls(self):
        return [json.loads(x)["argv"] for x in self.log.read_text().splitlines()]

    @property
    def state(self):
        return self.ts.state

    def pr(self, number, branch="tg/7-x", state="OPEN", **kw):
        d = {"number": number, "headRefName": branch, "state": state,
             "url": f"https://github.com/o/r/pull/{number}", "headRefOid": f"sha{number}",
             "mergedAt": None, "body": "", "comments": []}
        d.update(kw)
        return d


class PrReadTest(FakeGhCase):
    def test_pr_for_branch_latest(self):
        self.set(prs=[self.pr(3, state="CLOSED"), self.pr(9, "tg/8-y"), self.pr(5),
                      self.pr(4, state="MERGED", mergedAt="2026-10-01T00:00:00Z")])
        got = gh.pr_for_branch(self.state, self.tmp, "tg/7-x")
        self.assertEqual((got["number"], got["state"], got["url"], got["headRefOid"]),
                         (5, "OPEN", "https://github.com/o/r/pull/5", "sha5"))
        self.assertIn("mergedAt", got)
        self.assertNotIn("body", got)
        self.assertIsNone(gh.pr_for_branch(self.state, self.tmp, "tg/7-assente"))
        argv = self.calls()[0]
        self.assertEqual(argv[:2], ["pr", "list"])
        self.assertEqual(argv[argv.index("--head") + 1], "tg/7-x")
        self.assertEqual(argv[argv.index("--state") + 1], "all")
        self.assertEqual(argv[argv.index("--limit") + 1], "100")
        self.assertEqual(argv[argv.index("--json") + 1],
                         "number,state,url,headRefOid,mergedAt,isCrossRepository")

    def test_pr_for_branch_skips_fork_prs(self):
        self.set(prs=[self.pr(5), self.pr(9, isCrossRepository=True)])
        self.assertEqual(gh.pr_for_branch(self.state, self.tmp, "tg/7-x")["number"], 5)
        self.set(prs=[self.pr(9, isCrossRepository=True)])
        self.assertIsNone(gh.pr_for_branch(self.state, self.tmp, "tg/7-x"))

    def test_pr_for_branch_failure_is_error_not_no_pr(self):
        self.set(prs=[], fail=["pr list"])
        with self.assertRaises(gh.GhError):
            gh.pr_for_branch(self.state, self.tmp, "tg/7-x")

    def test_pr_view_and_comments(self):
        self.set(prs=[self.pr(5, comments=[{"body": "<!-- tollgate-verdict {} -->"}])])
        got = gh.pr_view(self.state, self.tmp, 5)
        self.assertEqual((got["number"], got["state"], got["mergedAt"]), (5, "OPEN", None))
        self.assertEqual(gh.pr_comments(self.state, self.tmp, 5),
                         [{"body": "<!-- tollgate-verdict {} -->"}])
        with self.assertRaises(gh.GhError):
            gh.pr_view(self.state, self.tmp, 6)

    def test_pr_body(self):
        self.set(prs=[self.pr(5, body="corpo\n<!-- tollgate {} -->")])
        self.assertEqual(gh.pr_body(self.state, self.tmp, 5), "corpo\n<!-- tollgate {} -->")
        with self.assertRaises(gh.GhError):
            gh.pr_body(self.state, self.tmp, 6)

    def test_unknown_json_field_is_rejected_by_fake(self):
        self.set(prs=[])
        for args in (["pr", "list", "--json", "number,nonEsiste"],
                     ["pr", "view", "1", "--json", "inventato"]):
            r = subprocess.run([sys.executable, str(FAKEGH), *args], capture_output=True,
                               text=True, env={**os.environ})
            self.assertEqual(r.returncode, 1, args)
            self.assertIn("nonEsiste" if "nonEsiste" in args[-1] else "inventato", r.stderr)

    def test_prs_for_branch_prefix_paginated(self):
        prs = [self.pr(n, f"tg/{n}-z") for n in range(2, 252)]
        prs.append(self.pr(1, "tg/70-vecchia", state="CLOSED"))
        self.set(prs=prs)
        got = gh.prs_for_branch_prefix(self.state, self.tmp, "tg/70-")
        self.assertEqual([p["number"] for p in got], [70, 1])
        self.assertEqual(set(got[0]), {"number", "headRefName", "state", "url"})
        argv = self.calls()[0]
        self.assertEqual(argv[:2], ["api", "--paginate"])
        self.assertEqual(argv[2], "repos/{owner}/{repo}/pulls?state=all&per_page=100")
        self.assertEqual(argv[3], "--jq")
        self.assertEqual(argv[4], ".[] | {number, headRefName: .head.ref, state: (if .merged_at "
                         'then "MERGED" else (.state | ascii_upcase) end), url: .html_url}')
        self.assertEqual(len(gh.prs_for_branch_prefix(self.state, self.tmp, "tg/")), 251)


class RunJsonLinesTest(unittest.TestCase):
    def test_decodes_lines_and_multiline_objects(self):
        text = '{"a":1}\n{"b": 2}\n\n{\n  "c": 3\n}  {"d": 4}'
        self.assertEqual(gh.decode_json_values(text), [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}])
        self.assertEqual(gh.decode_json_values(""), [])
        self.assertEqual(gh.decode_json_values("  \n"), [])

    def test_garbage_is_error(self):
        for text in ("non json", '{"a":1}\nerrore', '[1, 2]', '{"a":1} 5'):
            with self.assertRaises(gh.GhError, msg=text):
                gh.decode_json_values(text)


class PrWriteTest(FakeGhCase):
    def test_pr_create_and_edit_roundtrip(self):
        self.set(prs=[])
        body = self.tmp / "corpo con spazi.md"
        body.write_text("Closes #7\n")
        gh.pr_create(self.state, self.tmp, branch="tg/7-x", base="main", title="#7 x",
                     body_file=body)
        (created,) = self.read()["prs"]
        self.assertEqual((created["number"], created["headRefName"], created["state"],
                          created["body"]), (1, "tg/7-x", "OPEN", "Closes #7\n"))
        found = gh.pr_for_branch(self.state, self.tmp, "tg/7-x")
        self.assertEqual((found["number"], found["state"]), (1, "OPEN"))
        self.assertTrue(found["url"].endswith("/pull/1"))
        argv = [a for a in self.calls() if a[:2] == ["pr", "create"]][0]
        self.assertEqual(argv[argv.index("--head") + 1], "tg/7-x")
        self.assertEqual(argv[argv.index("--base") + 1], "main")
        self.assertEqual(argv[argv.index("--title") + 1], "#7 x")
        self.assertEqual(argv[argv.index("--body-file") + 1], str(body))
        body.write_text("Closes #7\nnuovo\n")
        gh.pr_edit(self.state, self.tmp, 1, body_file=body)
        (edited,) = self.read()["prs"]
        self.assertEqual(edited["body"], "Closes #7\nnuovo\n")
        edit = [a for a in self.calls() if a[:2] == ["pr", "edit"]][0]
        self.assertEqual(edit[:3], ["pr", "edit", "1"])

    def test_injected_failure_leaves_no_pr(self):
        self.set(prs=[], fail=["pr create"])
        body = self.tmp / "b.md"
        body.write_text("x")
        with self.assertRaises(gh.GhError):
            gh.pr_create(self.state, self.tmp, branch="tg/7-x", base="main", title="#7 x",
                         body_file=body)
        self.assertEqual(self.read()["prs"], [])

    def test_edit_unknown_pr_is_error(self):
        self.set(prs=[])
        body = self.tmp / "b.md"
        body.write_text("x")
        with self.assertRaises(gh.GhError):
            gh.pr_edit(self.state, self.tmp, 4, body_file=body)


class SentinelIssuesTest(FakeGhCase):
    def test_sentinel_issues_paginated(self):
        rows = [{"number": n, "title": f"issue {n}", "url": f"https://x/{n}"}
                for n in range(1, 111)]
        rows[104] = {"number": 105, "title": gh.SENTINEL_TITLE, "url": "https://x/105"}
        rows[10] = {"number": 11, "title": gh.SENTINEL_TITLE, "url": "https://x/11",
                    "pull_request": {}}
        self.set(open_issues=rows)
        self.assertEqual(gh.sentinel_issues(self.state, self.tmp),
                         [{"number": 105, "title": gh.SENTINEL_TITLE, "url": "https://x/105"}])
        [argv] = self.calls()
        self.assertEqual(argv[0], "api")
        self.assertIn("--paginate", argv)
        self.assertNotIn("--limit", argv)
        self.assertTrue(argv[-1].startswith("repos/{owner}/{repo}/issues?state=open"), argv)


if __name__ == "__main__":
    unittest.main()
