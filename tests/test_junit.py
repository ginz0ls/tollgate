import unittest

from tollgate_analysis.junit import JunitError, parse_junit

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites><testsuite name="s">
  <testcase classname="src/a.test.ts" name="g &gt; passes"/>
  <testcase classname="src/a.test.ts" name="g &gt; skipped"><skipped/></testcase>
  <testcase classname="tests.test_x" name="test_fail"><failure message="x"/></testcase>
  <testcase classname="tests.test_x" name="test_err"><error message="y"/></testcase>
</testsuite></testsuites>"""


class JunitTest(unittest.TestCase):
    def test_counts_and_ids(self):
        j = parse_junit(XML)
        self.assertEqual((j.total, j.skipped, j.failed), (4, 1, 2))
        self.assertEqual(j.ids_run, ["src/a.test.ts::g > passes", "tests.test_x::test_fail",
                                     "tests.test_x::test_err"])
        self.assertEqual(j.ids_skipped, ["src/a.test.ts::g > skipped"])
        self.assertEqual(j.ids_failed, ["tests.test_x::test_fail", "tests.test_x::test_err"])

    def test_entities_rejected(self):
        bad = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><testsuite/>'
        with self.assertRaises(JunitError):
            parse_junit(bad)

    def test_malformed(self):
        with self.assertRaises(JunitError):
            parse_junit(b"<testsuite><testcase")


if __name__ == "__main__":
    unittest.main()
