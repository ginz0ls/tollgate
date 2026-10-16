import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.flowkit import FlowLab
from tollgate_flow import prereq

REGISTRY = "plugins/installed_plugins.json"


class PrereqTest(unittest.TestCase):
    def setUp(self):
        self.claude = Path(tempfile.mkdtemp(prefix="tollgate claude ")) / ".claude"
        (self.claude / "plugins").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.claude.parent, ignore_errors=True)

    def registry(self, plugins):
        (self.claude / REGISTRY).write_text(json.dumps({"version": 2, "plugins": plugins}))

    def test_superpowers_version_from_registry(self):
        self.registry({"superpowers@claude-plugins-official": [
            {"scope": "user", "version": "7.0.0", "installPath": "/x"}]})
        self.assertEqual(prereq.superpowers_version(self.claude), (7, 0, 0))

    def test_superpowers_other_marketplace_and_highest_entry(self):
        self.registry({"superpowers@altro": [{"version": "6.4.1"}, {"version": "6.10.0"}]})
        self.assertEqual(prereq.superpowers_version(self.claude), (6, 10, 0))

    def test_superpowers_exact_key_wins_over_prefix(self):
        self.registry({"superpowers@altro": [{"version": "9.0.0"}],
                       "superpowers@claude-plugins-official": [{"version": "7.0.0"}]})
        self.assertEqual(prereq.superpowers_version(self.claude), (7, 0, 0))

    def test_superpowers_missing_or_malformed(self):
        self.assertIsNone(prereq.superpowers_version(self.claude))
        (self.claude / REGISTRY).write_text("{rotto")
        self.assertIsNone(prereq.superpowers_version(self.claude))
        (self.claude / REGISTRY).write_text("[1, 2]")
        self.assertIsNone(prereq.superpowers_version(self.claude))
        self.registry({"superpowers@x": "non una lista"})
        self.assertIsNone(prereq.superpowers_version(self.claude))
        self.registry({"superpowers@x": [{"version": "boh"}, {"nome": "senza versione"}]})
        self.assertIsNone(prereq.superpowers_version(self.claude))
        self.registry({"altro@x": [{"version": "7.0.0"}]})
        self.assertIsNone(prereq.superpowers_version(self.claude))

    def test_range_bounds(self):
        lo, hi = prereq.SUPERPOWERS_RANGE
        self.assertTrue(lo <= (6, 4, 1) < hi)
        self.assertFalse(lo <= (6, 3, 0) < hi)
        self.assertFalse(lo <= (8, 0, 0) < hi)

    def test_gate_status(self):
        fl = FlowLab()
        try:
            self.assertEqual(prereq.gate_status(fl.main, "origin/main"), ([], "0.1.0"))
        finally:
            fl.close()
        fl = FlowLab(gate=False)
        try:
            missing, version = prereq.gate_status(fl.main, "origin/main")
            self.assertIn(".github/workflows/tollgate-run.yml", missing)
            self.assertIn(".github/tollgate/VERSION", missing)
            self.assertIsNone(version)
        finally:
            fl.close()

    def test_gate_status_missing_one_workflow(self):
        fl = FlowLab()
        try:
            fl.git("rm", "-q", ".github/workflows/tollgate-run.yml")
            fl.git("commit", "-qm", "senza run")
            fl.git("push", "-q", "origin", "main")
            self.assertEqual(prereq.gate_status(fl.main, "origin/main"),
                             ([".github/workflows/tollgate-run.yml"], "0.1.0"))
        finally:
            fl.close()

    def test_is_github_reads_raw_url(self):
        fl = FlowLab()
        try:
            # get-url espanderebbe insteadOf e darebbe il percorso locale: qui si legge il grezzo
            self.assertTrue(prereq.is_github(fl.main))
            fl.git("config", "remote.origin.url", "git@github.com:O/R.git")
            self.assertTrue(prereq.is_github(fl.main))
            fl.git("config", "remote.origin.url", "https://gitlab.com/o/r.git")
            self.assertFalse(prereq.is_github(fl.main))
            fl.git("config", "remote.origin.url", "https://github.com.evil.example/o/r.git")
            self.assertFalse(prereq.is_github(fl.main))
        finally:
            fl.close()

    def test_skill_installed(self):
        plug = self.claude.parent / "plug dir"
        (plug / "skills" / "x").mkdir(parents=True)
        (plug / "skills" / "x" / "SKILL.md").write_text("---\n---\n")
        self.registry({"mioplug@mkt": [{"version": "1.0.0", "installPath": str(plug)}]})
        (self.claude / "skills" / "y").mkdir(parents=True)
        (self.claude / "skills" / "y" / "SKILL.md").write_text("y")
        wt = self.claude.parent / "wt"
        (wt / ".claude" / "skills" / "z").mkdir(parents=True)
        (wt / ".claude" / "skills" / "z" / "SKILL.md").write_text("z")

        def ok(name, worktree=None):
            return prereq.skill_installed(name, claude_dir=self.claude, worktree=worktree)

        self.assertTrue(ok("mioplug:x"))
        self.assertTrue(ok("y"))
        self.assertTrue(ok("z", wt))
        self.assertFalse(ok("z"))
        self.assertFalse(ok("mioplug:inesistente"))
        self.assertFalse(ok("altroplug:x"))
        self.assertFalse(ok("inesistente"))
        self.assertFalse(ok("../plug dir/skills/x"))
        self.assertFalse(ok("mioplug:../x"))


if __name__ == "__main__":
    unittest.main()
