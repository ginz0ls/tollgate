import shutil
import tempfile
import unittest
from pathlib import Path

from tests.helpers import git as g, make_repo
from tollgate_core import git


class GitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate git "))
        self.repo = make_repo(self.tmp / "repo con spazi")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.py").write_text("uno\ndue\n")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "base")
        self.base = g(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_toplevel_of_missing_path(self):
        self.assertEqual(git.toplevel(self.repo / "src" / "nuova" / "x.py"), self.repo.resolve())
        self.assertIsNone(git.toplevel(self.tmp / "fuori"))

    def test_toplevel_inside_git_dir(self):
        top = self.repo.resolve()
        self.assertEqual(git.toplevel(self.repo / ".git" / "config"), top)
        self.assertEqual(git.toplevel(self.repo / ".git" / "hooks" / "pre-commit"), top)
        wt = self.tmp / "wt 2"
        g(self.repo, "worktree", "add", "-q", "-b", "tg/2-y", str(wt))
        self.assertEqual(git.toplevel(wt / ".git"), wt.resolve())

    def test_toplevel_through_symlink(self):
        link = self.tmp / "collegamento"
        link.symlink_to(self.repo, target_is_directory=True)
        self.assertEqual(git.toplevel(link / "src" / "nuova.py"), self.repo.resolve())
        self.assertEqual(git.toplevel(link / ".git" / "config"), self.repo.resolve())

    def test_text_non_utf8_is_readable(self):
        self.assertEqual(git._text(b"caff\xe8\n"), "caffè\n")
        self.assertIsNone(git._text(b"testo\0binario"))

    def test_changes_worktree_and_untracked(self):
        (self.repo / "src" / "a.py").write_text("uno\ndue\ntre\n")
        (self.repo / "src" / "b.py").write_text("x\ny\n")
        (self.repo / "img.bin").write_bytes(b"\x00\x01\x02")
        g(self.repo, "mv", "tests/test_a.py", "tests/test_b.py")
        got = {c.path: c for c in git.changes(self.repo, self.base)}
        self.assertEqual((got["src/a.py"].status, got["src/a.py"].added), ("M", 1))
        self.assertEqual((got["src/b.py"].status, got["src/b.py"].added), ("A", 2))
        self.assertTrue(got["img.bin"].binary)
        self.assertEqual((got["tests/test_b.py"].status, got["tests/test_b.py"].old_path),
                         ("R", "tests/test_a.py"))
        self.assertGreater(git.diff_size(self.repo, self.base), 0)

    def test_commits_and_text(self):
        (self.repo / "src" / "a.py").unlink()
        g(self.repo, "commit", "-qam", "via a")
        head = git.head(self.repo)
        self.assertEqual(git.rev_list(self.repo, self.base, head), [head])
        self.assertEqual([(c.status, c.path) for c in git.commit_changes(self.repo, head)],
                         [("D", "src/a.py")])
        self.assertEqual(git.text_at(self.repo, self.base, "src/a.py"), "uno\ndue\n")
        self.assertIsNone(git.text_at(self.repo, head, "src/a.py"))
        self.assertTrue(git.exists_at(self.repo, self.base, "src/a.py"))
        self.assertFalse(git.exists_at(self.repo, head, "src/a.py"))
        root = git.commit_changes(self.repo, self.base)
        self.assertEqual({c.path for c in root}, {"src/a.py", "tests/test_a.py"})

    def test_default_ref_order(self):
        origin = self.tmp / "origin.git"
        g(self.tmp, "init", "-q", "--bare", "-b", "main", str(origin))
        g(self.repo, "remote", "add", "origin", str(origin))
        g(self.repo, "push", "-q", "origin", "main")
        self.assertEqual(git.default_ref(self.repo), "origin/main")
        g(self.repo, "config", "tollgate.defaultBranch", "main")
        self.assertEqual(git.default_ref(self.repo), "origin/main")
        self.assertEqual(git.default_branch(self.repo), "main")
        self.assertEqual(git.origin_url(self.repo), str(origin))

    def test_worktrees_and_branches(self):
        wt = self.tmp / "wt 1"
        g(self.repo, "worktree", "add", "-q", "-b", "tg/1-x", str(wt))
        self.assertEqual(git.main_worktree(wt), self.repo.resolve())
        self.assertIn((wt.resolve(), "tg/1-x"), git.worktrees(self.repo))
        self.assertEqual(git.branch(wt), "tg/1-x")
        self.assertIn("tg/1-x", git.local_branches(self.repo))
        self.assertEqual(git.common_dir(wt), (self.repo / ".git").resolve())

    def test_fingerprint_and_clean(self):
        f0 = git.fingerprint(self.repo, ["reports/"])
        (self.repo / "reports").mkdir()
        (self.repo / "reports" / "j.xml").write_text("x")
        self.assertEqual(git.fingerprint(self.repo, ["reports/"]), f0)
        self.assertTrue(git.is_clean(self.repo, ["reports/"]))
        (self.repo / "nuovo.txt").write_text("x")
        self.assertNotEqual(git.fingerprint(self.repo, ["reports/"]), f0)
        self.assertFalse(git.is_clean(self.repo, ["reports/"]))


if __name__ == "__main__":
    unittest.main()
