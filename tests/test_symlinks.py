"""C2 della revisione finale: i file protetti si riconoscono anche dietro un collegamento
simbolico (al file o a una cartella), sia per Write/Edit sia per Bash."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.hookkit import Lab

IMPL = "a-impl"


class SymlinkProtectionTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.addCleanup(self.lab.close)
        self.home = Path(tempfile.mkdtemp(prefix="tollgate home "))
        self.addCleanup(shutil.rmtree, self.home, True)
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.wt = self.lab.wt

    def edit(self, p):
        return self.lab.pre_edit(p, agent_id=IMPL).exit

    def bash(self, cmd):
        return self.lab.bash(cmd, agent_id=IMPL).exit

    def link_file(self, link: Path, target: Path):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n")
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)

    def link_dir(self, link: Path, target: Path):
        target.mkdir(parents=True, exist_ok=True)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=True)

    def test_repo_settings_symlinked_file(self):
        self.link_file(self.wt / ".claude/settings.json", self.wt / "config/claude.json")
        self.assertEqual(self.edit(self.wt / ".claude/settings.json"), 2)
        self.assertEqual(self.bash("sed -i s/a/b/ .claude/settings.json"), 2)
        self.assertEqual(self.bash("echo x > .claude/settings.json"), 2)

    def test_repo_claude_dir_symlinked(self):
        self.link_dir(self.wt / ".claude", self.wt / "cfg/claudedir")
        self.assertEqual(self.edit(self.wt / ".claude/settings.json"), 2)
        self.assertEqual(self.bash("echo x > .claude/settings.json"), 2)

    def test_home_settings_symlinked_file(self):
        self.link_file(self.home / ".claude/settings.json", self.home / "dotfiles/settings.json")
        self.assertEqual(self.edit(self.home / ".claude/settings.json"), 2)
        self.assertEqual(self.bash(f"echo x > '{self.home}/.claude/settings.json'"), 2)
        self.assertEqual(self.bash("echo x > ~/.claude/settings.json"), 2)

    def test_home_claude_dir_symlinked(self):
        self.link_dir(self.home / ".claude", self.home / "dotfiles/claude")
        self.assertEqual(self.edit(self.home / ".claude/settings.json"), 2)
        self.assertEqual(self.bash("echo x > ~/.claude/settings.json"), 2)

    def test_repo_reached_through_a_symlinked_parent(self):
        alias = self.lab.tmp / "alias"
        alias.symlink_to(self.wt, target_is_directory=True)
        self.assertEqual(self.edit(alias / "tollgate.toml"), 2)
        self.assertEqual(self.edit(alias / ".claude/settings.json"), 2)

    def test_unprotected_targets_still_pass(self):
        self.link_file(self.home / ".claude/other.json", self.home / "dotfiles/other.json")
        self.assertEqual(self.edit(self.home / ".claude/other.json"), 0)
        self.assertEqual(self.edit(self.home / "dotfiles/other.json"), 0)
        self.assertEqual(self.edit(self.wt / "docs/superpowers/note.md"), 0)


if __name__ == "__main__":
    unittest.main()
