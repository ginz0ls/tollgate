import re
import unittest
from unittest import mock

from tollgate_analysis import junit
from tollgate_analysis.junit import JunitError, parse_junit

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites><testsuite name="s">
  <testcase classname="src/a.test.ts" name="g &gt; passes"/>
  <testcase classname="src/a.test.ts" name="g &gt; skipped"><skipped/></testcase>
  <testcase classname="tests.test_x" name="test_fail"><failure message="x"/></testcase>
  <testcase classname="tests.test_x" name="test_err"><error message="y"/></testcase>
</testsuite></testsuites>"""

BOMB = ('<?xml version="1.0" encoding="{enc}"?>'
        '<!DOCTYPE x [<!ENTITY a "bbbbbbbbbb">]>'
        '<testsuite><testcase classname="c" name="&a;"/></testsuite>')

# Nessun DOCTYPE: il regex sui byte è disattivato per provare che la protezione regge da sola.
NEVER = re.compile(rb"(?!x)x")


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

    def test_utf16_bom_doctype_rejected(self):
        data = BOMB.format(enc="UTF-16").encode("utf-16")
        self.assertTrue(data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"))
        with self.assertRaises(JunitError):
            parse_junit(data)

    def test_utf8_bom_doctype_rejected(self):
        data = b"\xef\xbb\xbf" + BOMB.format(enc="UTF-8").encode("utf-8")
        with self.assertRaises(JunitError):
            parse_junit(data)

    def test_doctype_rejected_by_parser_alone(self):
        # Senza il controllo sui byte, il parser da solo deve rifiutare DOCTYPE ed entità.
        with mock.patch.object(junit, "_DANGER", NEVER):
            with self.assertRaises(JunitError):
                parse_junit(BOMB.format(enc="UTF-8").encode("utf-8"))
            with self.assertRaises(JunitError):
                parse_junit(BOMB.format(enc="UTF-16").encode("utf-16"))

    def test_utf16_and_utf8_bom_without_doctype_parse(self):
        xml16 = XML.replace(b'encoding="UTF-8"', b'encoding="UTF-16"').decode("utf-8")
        self.assertEqual(parse_junit(xml16.encode("utf-16")).total, 4)
        self.assertEqual(parse_junit(b"\xef\xbb\xbf" + XML).total, 4)

    def test_size_limit(self):
        self.assertEqual(junit.MAX_BYTES, 32 * 1024 * 1024)
        with self.assertRaises(JunitError) as ctx:
            parse_junit(XML, max_bytes=10)
        self.assertIn("troppo grande", str(ctx.exception))
        self.assertEqual(parse_junit(XML, max_bytes=len(XML)).total, 4)

    def test_wrong_root_rejected(self):
        data = b'<?xml version="1.0"?><report><testcase classname="a" name="b"/></report>'
        with self.assertRaises(JunitError):
            parse_junit(data)

    def test_nested_testcase_rejected(self):
        data = (b'<testsuite><testcase classname="a" name="outer">'
                b'<testcase classname="a" name="inner"/></testcase></testsuite>')
        with self.assertRaises(JunitError):
            parse_junit(data)

    def test_empty_bytes_rejected(self):
        with self.assertRaises(JunitError):
            parse_junit(b"")

    def test_undecodable_bytes_rejected(self):
        with self.assertRaises(JunitError):
            parse_junit(b"<testsuite>\xff\xfe\x80</testsuite>")
        with self.assertRaises(JunitError):
            parse_junit(b"\xff\xfe\xfd\x80garbage")


if __name__ == "__main__":
    unittest.main()
