import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tollgate_gate import artifacts

XML = '<testsuite><testcase classname="t" name="a"/><testcase classname="t" name="b"/></testsuite>'
COMMAND = {"name": "verify", "state": "green", "exit": 0, "tests_run": 2, "tests_skipped": 0,
           "report": "junit/0.xml"}


class ArtifactsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tollgate artifacts "))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "junit").mkdir()
        (self.root / "junit" / "0.xml").write_text(XML)
        self.write_results([COMMAND])

    def write_results(self, commands, **extra):
        data = {"v": 1, "applicable": True, "sha": "a" * 40, "config_sha": "b" * 40,
                "commands": commands, **extra}
        (self.root / "results.json").write_text(json.dumps(data))

    def test_valid_dir(self):
        self.assertEqual(artifacts.validate(self.root), [])
        results, applicable, problems = artifacts.read_results(self.root)
        self.assertEqual((applicable, problems), (True, []))
        self.assertEqual([(r.name, r.state, r.exit, r.tests_run) for r in results],
                         [("verify", "green", 0, 2)])
        self.assertEqual(results[0].junit.ids_run, ["t::a", "t::b"])

    def test_not_applicable_dir(self):
        self.write_results([], applicable=False)
        self.assertEqual(artifacts.read_results(self.root), ([], False, []))

    def test_dotdot_absolute_symlink_rejected(self):
        outside = Path(tempfile.mkdtemp(prefix="tollgate outside "))
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "secret").write_text("x")
        for name, target in (("abs", outside / "secret"), ("dotdot", "../../etc/passwd"),
                             ("dir", outside)):
            with self.subTest(name=name):
                link = self.root / "junit" / f"{name}.xml"
                os.symlink(target, link)
                problems = artifacts.validate(self.root)
                self.assertTrue(any(f"junit/{name}.xml" in p for p in problems), problems)
                link.unlink()
        self.assertEqual(artifacts.validate(self.root), [])

    def test_report_path_in_results_json_rejected(self):
        for report in ("../x.xml", "/etc/passwd", "junit/../../x.xml", "logs/a.xml", "junit",
                       "other/0.xml", 7):
            with self.subTest(report=report):
                self.write_results([{**COMMAND, "report": report}])
                problems = artifacts.validate(self.root)
                self.assertTrue(any("report" in p for p in problems), problems)
                self.assertEqual(artifacts.read_results(self.root)[0], None)

    def test_control_characters_in_report_rejected(self):
        for report in ("junit/a\u0000.xml", "junit/a\n.xml", "junit/a\x1b.xml"):
            with self.subTest(report=repr(report)):
                self.write_results([{**COMMAND, "report": report}])
                self.assertTrue(any("report" in p for p in artifacts.validate(self.root)))
                results, applicable, problems = artifacts.read_results(self.root)
                self.assertEqual((results, applicable), (None, False))
                self.assertTrue(problems)

    def test_read_failures_are_problems_not_exceptions(self):
        with mock.patch.object(Path, "read_bytes", side_effect=OSError("boom")):
            results, applicable, problems = artifacts.read_results(self.root)
        self.assertEqual((results, applicable), (None, False))
        self.assertTrue(problems)
        with mock.patch.object(artifacts, "parse_junit", side_effect=ValueError("boom")):
            results, _, problems = artifacts.read_results(self.root)
        self.assertIsNone(results)
        self.assertTrue(problems)

    def test_results_json_size_checked_before_reading(self):
        (self.root / "results.json").write_text(" " * 200)
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("letto")):
            problems = artifacts.validate(self.root, max_file=100)
        self.assertTrue(any("results.json" in p for p in problems), problems)

    def test_deeply_nested_results_json_is_a_problem(self):
        (self.root / "results.json").write_text("[" * 100000)
        self.assertTrue(artifacts.validate(self.root))
        results, applicable, problems = artifacts.read_results(self.root)
        self.assertEqual((results, applicable), (None, False))
        self.assertTrue(problems)

    def test_results_json_is_read_once(self):
        real = Path.read_text
        reads = []

        def counting(path, *a, **k):
            if path.name == "results.json":
                reads.append(path)
            return real(path, *a, **k)
        with mock.patch.object(Path, "read_text", counting):
            self.assertEqual(artifacts.read_results(self.root)[2], [])
        self.assertEqual(len(reads), 1)

    def test_bogus_xml_encoding_is_a_problem(self):
        (self.root / "junit" / "0.xml").write_text(
            '<?xml version="1.0" encoding="bogus"?><testsuite/>')
        self.assertTrue(any("junit/0.xml" in p for p in artifacts.validate(self.root)))
        results, applicable, problems = artifacts.read_results(self.root)
        self.assertEqual((results, applicable), (None, False))
        self.assertTrue(problems)

    def test_any_exception_at_the_boundary_is_a_problem(self):
        with mock.patch.object(artifacts, "parse_junit", side_effect=RuntimeError("boom")):
            problems = artifacts.validate(self.root)
            self.assertTrue(any("RuntimeError" in p and "boom" in p for p in problems), problems)
            results, applicable, found = artifacts.read_results(self.root)
        self.assertEqual((results, applicable), (None, False))
        self.assertTrue(found)
        with mock.patch.object(artifacts.os, "walk", side_effect=KeyError("boom")):
            self.assertTrue(any("KeyError" in p for p in artifacts.validate(self.root)))
            self.assertIsNone(artifacts.read_results(self.root)[0])
        with mock.patch.object(artifacts, "_check", return_value=([], {"applicable": True,
                                                                     "commands": [object()]})):
            self.assertIsNone(artifacts.read_results(self.root)[0])

    def test_stat_failure_after_is_file_is_a_problem(self):
        with mock.patch.object(Path, "is_file", return_value=True), \
                mock.patch.object(Path, "stat", side_effect=OSError("gone")):
            problems = artifacts.validate(self.root)
        self.assertTrue(problems)

    def test_size_limits(self):
        (self.root / "big.log").write_bytes(b"x" * 100)
        self.assertEqual(artifacts.validate(self.root, max_file=1000), [])
        problems = artifacts.validate(self.root, max_file=50)
        self.assertTrue(any("big.log" in p for p in problems), problems)
        total = artifacts.validate(self.root, max_total=100)
        self.assertTrue(any("totale" in p for p in total), total)

    def test_xml_entity_rejected(self):
        bomb = ('<?xml version="1.0"?><!DOCTYPE t [<!ENTITY a "aaaa">]>'
                '<testsuite><testcase classname="&a;" name="x"/></testsuite>')
        (self.root / "junit" / "0.xml").write_text(bomb)
        problems = artifacts.validate(self.root)
        self.assertTrue(any("junit/0.xml" in p for p in problems), problems)
        results, applicable, found = artifacts.read_results(self.root)
        self.assertEqual((results, applicable), (None, False))
        self.assertTrue(found)

    def test_missing_or_broken_results_json(self):
        (self.root / "results.json").write_text("{")
        self.assertTrue(artifacts.validate(self.root))
        (self.root / "results.json").unlink()
        self.assertTrue(artifacts.validate(self.root))

    def test_malformed_entries_are_problems(self):
        for bad in ({**COMMAND, "state": "great"}, {**COMMAND, "name": 3}, {**COMMAND, "exit": "0"},
                    "x", {**COMMAND, "report": "junit/missing.xml"}):
            with self.subTest(bad=bad):
                self.write_results([bad])
                results, _, problems = artifacts.read_results(self.root)
                self.assertIsNone(results)
                self.assertTrue(problems)


if __name__ == "__main__":
    unittest.main()
