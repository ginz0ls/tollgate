import base64
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_range_base_is_parent_or_empty_tree(self):
        (self.repo / "src" / "b.py").write_text("x\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "due")
        second = g(self.repo, "rev-parse", "HEAD")
        self.assertEqual(git.range_base(self.repo, second), self.base)
        self.assertEqual(git.range_base(self.repo, self.base), git.EMPTY_TREE)

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

    def test_changes_and_size_exclude_dirs(self):
        (self.repo / "reports").mkdir()
        (self.repo / "reports" / "junit.xml").write_text("<x/>\n" * 100)
        (self.repo / ".tollgate-run").mkdir()
        (self.repo / ".tollgate-run" / "o.log").write_text("o\n" * 100)
        (self.repo / "src" / "a.py").write_text("uno\ndue\ntre\n")
        (self.repo / "src" / "reports.py").write_text("r\n")
        exclude = ["reports/", ".tollgate-run/"]
        got = git.changes(self.repo, self.base, exclude=exclude)
        self.assertEqual(sorted(c.path for c in got), ["src/a.py", "src/reports.py"])
        self.assertEqual(len(git.changes(self.repo, self.base)), 4)
        plain = git.diff_size(self.repo, self.base)
        small = git.diff_size(self.repo, self.base, exclude=exclude)
        self.assertLess(small, 200)
        self.assertEqual(plain - small, 700)

    def test_exclude_applies_to_tracked_changes(self):
        (self.repo / "reports").mkdir()
        (self.repo / "reports" / "j.xml").write_text("a\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "reports")
        base = git.head(self.repo)
        (self.repo / "reports" / "j.xml").write_text("a\nb\nc\n")
        self.assertEqual([c.path for c in git.changes(self.repo, base)], ["reports/j.xml"])
        self.assertEqual(git.changes(self.repo, base, exclude=["reports/"]), [])
        self.assertEqual(git.diff_size(self.repo, base, exclude=["reports/"]), 0)

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

    def test_read_only_leaves_index_untouched(self):
        f = self.repo / "src" / "a.py"
        st = f.stat()
        os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
        idx = self.repo / ".git" / "index"
        before = (idx.read_bytes(), idx.stat().st_mtime_ns)
        git.changes(self.repo, self.base)
        git.diff_size(self.repo, self.base)
        git.is_clean(self.repo, [])
        self.assertEqual((idx.read_bytes(), idx.stat().st_mtime_ns), before)

    def test_blob_text_reads_stored_blob_and_none_for_missing(self):
        sha = g(self.repo, "rev-parse", "HEAD:src/a.py")
        self.assertEqual(git.blob_text(self.repo, sha), "uno\ndue\n")
        loose = g(self.repo, "hash-object", "src/a.py")  # non scritto: stesso blob, già presente
        self.assertEqual(loose, sha)
        (self.repo / "nuovo.txt").write_text("mai scritto\n")
        unwritten = g(self.repo, "hash-object", "nuovo.txt")
        self.assertIsNone(git.blob_text(self.repo, unwritten))
        self.assertIsNone(git.blob_text(self.repo, "not-a-sha"))

    def test_blob_text_binary_is_none(self):
        (self.repo / "b.bin").write_bytes(b"a\0b")
        g(self.repo, "add", "b.bin")
        self.assertIsNone(git.blob_text(self.repo, g(self.repo, "rev-parse", ":b.bin")))

    def test_timeout_becomes_git_error(self):
        slow = subprocess.TimeoutExpired(cmd=["git"], timeout=10)
        with patch("tollgate_core.git.subprocess.run", side_effect=slow):
            with self.assertRaises(git.GitError) as cm:
                git.run(self.repo, "status")
            self.assertIn("timeout", str(cm.exception))
            self.assertFalse(git.ok(self.repo, "status"))
            self.assertIsNone(git.toplevel(self.repo))

    def test_fingerprint_survives_symlink_loop(self):
        (self.repo / "loop").symlink_to(self.repo / "loop")
        f0 = git.fingerprint(self.repo, [])
        self.assertEqual(git.fingerprint(self.repo, []), f0)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root legge ogni file")
    def test_fingerprint_survives_unreadable_file(self):
        f = self.repo / "segreto.txt"
        f.write_text("x")
        f.chmod(0)
        try:
            f0 = git.fingerprint(self.repo, [])
            self.assertEqual(git.fingerprint(self.repo, []), f0)
        finally:
            f.chmod(0o644)

    def test_untracked_is_scanned_in_blocks(self):
        (self.repo / "grande.txt").write_text("riga\n" * 100000 + "fine")
        (self.repo / "tardi.txt").write_bytes(b"a\n" * 5000 + b"\0")
        with patch.object(Path, "read_bytes", side_effect=AssertionError("letto tutto")):
            got = {c.path: c for c in git.changes(self.repo, self.base)}
        self.assertEqual((got["grande.txt"].added, got["grande.txt"].binary), (100001, False))
        self.assertFalse(got["tardi.txt"].binary)

    def _sentinel_script(self, name):
        """Script che crea un file sentinella. Il percorso non ha spazi: git lo lancia tramite shell.
        Il test di controllo (git diretto) dimostra che lo script scatta davvero."""
        bindir = Path(tempfile.mkdtemp(prefix="tgexe"))
        self.addCleanup(shutil.rmtree, bindir, True)
        sentinel = bindir / "sentinella"
        script = bindir / name
        script.write_text(f"#!/bin/sh\ntouch '{sentinel}'\nexit 0\n")
        script.chmod(0o755)
        return script, sentinel

    def test_external_diff_driver_never_runs(self):
        script, sentinel = self._sentinel_script("ext.sh")
        g(self.repo, "config", "diff.external", str(script))
        (self.repo / "src" / "a.py").write_text("cambiato\n")
        g(self.repo, "diff")  # controllo: il driver scatta con git diretto (patch, non --stat)
        self.assertTrue(sentinel.exists())
        sentinel.unlink()
        git.changes(self.repo, self.base)
        git.diff_size(self.repo, self.base)
        self.assertFalse(sentinel.exists())

    def test_fsmonitor_hook_never_runs(self):
        script, sentinel = self._sentinel_script("fsmon.sh")
        g(self.repo, "config", "core.fsmonitor", str(script))
        (self.repo / "src" / "a.py").write_text("cambiato\n")
        g(self.repo, "status", "--porcelain")  # controllo: l'hook scatta con git diretto
        self.assertTrue(sentinel.exists())
        sentinel.unlink()
        git.is_clean(self.repo, [])
        git.changes(self.repo, self.base)
        self.assertFalse(sentinel.exists())

    def test_refs_starting_with_dash_refused(self):
        calls = {
            "ls_files_at": lambda r: git.ls_files_at(self.repo, r, "src/"),
            "text_at": lambda r: git.text_at(self.repo, r, "src/a.py"),
            "blob_text": lambda r: git.blob_text(self.repo, r),
            "show": lambda r: git.show(self.repo, r, "src/a.py"),
            "blob_at": lambda r: git.blob_at(self.repo, r, "src/a.py"),
            "exists_at": lambda r: git.exists_at(self.repo, r, "src/a.py"),
            "rev_list base": lambda r: git.rev_list(self.repo, r, "HEAD"),
            "rev_list head": lambda r: git.rev_list(self.repo, "HEAD", r),
            "changes base": lambda r: git.changes(self.repo, r, head="HEAD"),
            "changes head": lambda r: git.changes(self.repo, "HEAD", head=r),
            "diff_size base": lambda r: git.diff_size(self.repo, r, head="HEAD"),
            "diff_size head": lambda r: git.diff_size(self.repo, "HEAD", head=r),
            "patch_id base": lambda r: git.patch_id(self.repo, r, "HEAD"),
            "patch_id head": lambda r: git.patch_id(self.repo, "HEAD", r),
            "resolve_ref": lambda r: git.resolve_ref(self.repo, r),
            "fetch_ref": lambda r: git.fetch_ref(self.repo, r),
            "object_in_history obj": lambda r: git.object_in_history(self.repo, r, "HEAD"),
            "object_in_history ref": lambda r: git.object_in_history(self.repo, self.base, r),
        }
        for name, call in calls.items():
            with self.subTest(name), patch("tollgate_core.git.subprocess.run") as run:
                with self.assertRaises(git.GitError):
                    call("--output=/tmp/x")
                run.assert_not_called()
        self.assertEqual(git.text_at(self.repo, "HEAD", "src/a.py"), "uno\ndue\n")

    def test_object_in_history(self):
        blob = g(self.repo, "rev-parse", "HEAD:src/a.py")
        self.assertTrue(git.object_in_history(self.repo, blob, "HEAD"))
        (self.repo / "src" / "a.py").write_text("tre\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "cambia")
        self.assertTrue(git.object_in_history(self.repo, blob, "HEAD"))   # tolto in un commit
        loose = subprocess.run(["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"],
                               input=b"mai committato\n", capture_output=True,
                               check=True).stdout.decode().strip()
        self.assertEqual(git.blob_text(self.repo, loose), "mai committato\n")
        self.assertFalse(git.object_in_history(self.repo, loose, "HEAD"))
        self.assertFalse(git.object_in_history(self.repo, "0" * 40, "HEAD"))
        self.assertFalse(git.object_in_history(self.repo, blob, "refs/heads/inesistente"))

    def test_fetch_ref_passes_token_only_in_environment(self):
        token = "ghs_segretissimo"
        done = subprocess.CompletedProcess([], 0, b"", b"")
        with patch("tollgate_core.git.subprocess.run", return_value=done) as run:
            git.fetch_ref(self.repo, "refs/pull/5/head", token=token)
        cmd, env = run.call_args.args[0], run.call_args.kwargs["env"]
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(cmd[-2:], ["origin", "refs/pull/5/head"])
        self.assertFalse([a for a in cmd if token in a or "AUTHORIZATION" in a])
        self.assertFalse([a for a in cmd if "extraheader" in a])
        auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        self.assertEqual((env["GIT_CONFIG_COUNT"], env["GIT_CONFIG_KEY_0"],
                          env["GIT_CONFIG_VALUE_0"]),
                         ("1", "http.https://github.com/.extraheader",
                          f"AUTHORIZATION: basic {auth}"))
        self.assertNotIn(token, (self.repo / ".git" / "config").read_text())

    def test_fetch_ref_without_token_sets_no_header_and_fetches(self):
        origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True,
                       capture_output=True)
        g(self.repo, "remote", "add", "origin", str(origin))
        g(self.repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        with patch("tollgate_core.git.subprocess.run", wraps=subprocess.run) as run:
            git.fetch_ref(self.repo, "refs/heads/main")
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertNotIn("GIT_CONFIG_COUNT", {k for k in env if k not in os.environ})
        self.assertEqual(git.resolve_ref(self.repo, "FETCH_HEAD"), self.base)
        with self.assertRaises(git.GitError):
            git.fetch_ref(self.repo, "refs/heads/assente")


class LsFilesAtTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate ls "))
        self.repo = make_repo(self.tmp / "repo con spazi")
        for rel in ("docs/superpowers/reviews/7/spec-approval.md",
                    "docs/superpowers/reviews/8/a b.md", "docs/altro.md", "src/x.py"):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(f"{rel}\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "base")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_lists_files_under_prefix_recursively(self):
        self.assertEqual(
            git.ls_files_at(self.repo, "HEAD", "docs/superpowers/reviews/"),
            ["docs/superpowers/reviews/7/spec-approval.md", "docs/superpowers/reviews/8/a b.md"])

    def test_missing_ref_or_prefix_is_empty(self):
        self.assertEqual(git.ls_files_at(self.repo, "origin/main", "docs/"), [])
        self.assertEqual(git.ls_files_at(self.repo, "HEAD", "nessuna/"), [])

    def test_non_ascii_name_is_not_quoted(self):
        (self.repo / "docs" / "è.md").write_text("x\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "accento")
        self.assertIn("docs/è.md", git.ls_files_at(self.repo, "HEAD", "docs/"))


class BlobAtTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate blob "))
        self.repo = make_repo(self.tmp / "repo")
        (self.repo / "a.md").write_text("uno\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "base")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_blob_at_matches_hash_object_and_none_when_absent(self):
        self.assertEqual(git.blob_at(self.repo, "HEAD", "a.md"), git.blob_sha(self.repo, "a.md"))
        self.assertIsNone(git.blob_at(self.repo, "HEAD", "manca.md"))
        self.assertIsNone(git.blob_at(self.repo, "origin/main", "a.md"))

    def test_blob_at_directory_is_none(self):
        (self.repo / "d").mkdir()
        (self.repo / "d" / "f.md").write_text("x\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "dir")
        self.assertIsNone(git.blob_at(self.repo, "HEAD", "d"))
        self.assertIsNotNone(git.blob_at(self.repo, "HEAD", "d/f.md"))


class FingerprintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate fp "))
        self.repo = make_repo(self.tmp / "repo")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.py").write_text("uno\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "base")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cache_dirs_ignored(self):
        f0 = git.fingerprint(self.repo, [])
        for d in git.CACHE_DIRS:
            cache = self.repo / "tests" / d
            cache.mkdir(parents=True)
            (cache / "x.pyc").write_bytes(b"\0\1")
        self.assertEqual(git.fingerprint(self.repo, []), f0)
        (self.repo / "src" / "a.py").write_text("due\n")
        self.assertNotEqual(git.fingerprint(self.repo, []), f0)


class PatchIdTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate pid "))
        self.repo = make_repo(self.tmp / "repo")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.py").write_text("\n".join(f"riga {i}" for i in range(1, 21)) + "\n")
        (self.repo / "altro.txt").write_text("uno\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "base")
        self.base = g(self.repo, "rev-parse", "HEAD")
        g(self.repo, "checkout", "-qb", "lavoro")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit(self, text, msg="modifica"):
        p = self.repo / "src" / "a.py"
        p.write_text(text(p.read_text()))
        g(self.repo, "commit", "-qam", msg)
        return g(self.repo, "rev-parse", "HEAD")

    def test_empty_diff_is_none(self):
        self.assertIsNone(git.patch_id(self.repo, self.base, self.base))

    def test_same_id_after_rebase_on_advanced_base(self):
        head = self.edit(lambda t: t.replace("riga 15", "riga quindici"))
        before = git.patch_id(self.repo, self.base, head)
        self.assertRegex(before, r"^[0-9a-f]{40}$")
        g(self.repo, "checkout", "-q", "main")
        (self.repo / "altro.txt").write_text("uno\ndue\n")
        g(self.repo, "commit", "-qam", "avanza")
        new_base = g(self.repo, "rev-parse", "HEAD")
        g(self.repo, "checkout", "-q", "lavoro")
        g(self.repo, "rebase", "-q", "main")
        new_head = g(self.repo, "rev-parse", "HEAD")
        self.assertNotEqual(new_head, head)
        self.assertEqual(git.patch_id(self.repo, new_base, new_head), before)

    def test_different_content_different_id(self):
        h1 = self.edit(lambda t: t.replace("riga 15", "riga quindici"))
        h2 = self.edit(lambda t: t.replace("riga 3", "riga tre"))
        self.assertNotEqual(git.patch_id(self.repo, self.base, h1),
                            git.patch_id(self.repo, self.base, h2))

    def test_bad_ref_raises(self):
        with self.assertRaises(git.GitError):
            git.patch_id(self.repo, "nonesiste", "HEAD")


if __name__ == "__main__":
    unittest.main()
