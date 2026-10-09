import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import ROOT, git, make_repo
from tests.hookkit import Lab
from tollgate_core import git as core_git, phases
from tollgate_core.paths import repo_key


class BoundSessionTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def code(self, command, **kw):
        return self.lab.bash(command, **kw).exit

    def test_push_and_pr_denied(self):
        self.assertEqual(self.code("git push origin tg/7-demo"), 2)
        self.assertEqual(self.code("gh pr create --fill"), 2)
        self.assertEqual(self.code("bash -c 'git push'"), 2)
        self.assertEqual(self.code("bash -lc 'git push'"), 2)

    def test_branch_changes_in_worktree(self):
        for cmd in ("git switch -c altro", "git checkout -B altro", "git branch -m nuovo",
                    "git checkout main"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd), 2)
        self.assertEqual(self.code("git checkout -- src/app.py"), 0)
        self.assertEqual(self.code("git status"), 0)
        self.assertEqual(self.code("git branch -a"), 0)

    def test_main_checkout(self):
        self.assertEqual(self.code(f"cd '{self.lab.main}' && touch x.txt"), 2)
        self.assertEqual(self.code(f"cd '{self.lab.main}' && gh pr create"), 2)
        self.assertEqual(self.code(f"echo x > '{self.lab.main}/src/app.py'"), 2)
        self.assertEqual(self.code(f"git -C '{self.lab.main}' status"), 0)
        self.assertEqual(self.code(f"git -C '{self.lab.main}' worktree list"), 0)
        self.assertEqual(self.code(f"git -C '{self.lab.main}' commit -m x"), 2)

    def test_coordinator_code_writes(self):
        self.assertEqual(self.code("echo x > src/app.py"), 2)
        self.assertEqual(self.code("sed -i 's/a/b/' src/app.py"), 2)
        self.assertEqual(self.code("echo x > src/app.py", agent_id="a1"), 0)
        self.assertEqual(self.code("echo x > docs/superpowers/n.md"), 0)
        self.assertEqual(self.code("echo x > reports/junit.xml"), 0)

    def test_destructive_and_forbidden(self):
        for cmd in ("git push -f origin tg/7-demo", "git reset --hard HEAD~1",
                    "git commit --no-verify -m x", "git commit -n -m x", "rm -rf /tmp/qualcosa",
                    "claude -p ciao", "TOLLGATE_STATE=/tmp ls", "TOLLGATE_STATE=/tmp; ls",
                    f"'{ROOT}/bin/tollgate' hook PreToolUse", "echo x > tollgate.toml",
                    "echo x >> .tollgate/waivers/7.toml"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd, agent_id="a1"), 2)
        self.assertEqual(self.code("rm -rf build", agent_id="a1"), 0)
        self.assertEqual(self.code("rm -rf build 2>/dev/null", agent_id="a1"), 0)

    def test_rm_rf_of_the_worktree_itself_is_denied(self):
        self.assertEqual(self.code("rm -rf .", agent_id="a1"), 2)
        self.assertEqual(self.code(f"rm -rf '{self.lab.main}/build'", agent_id="a1"), 2)

    def test_unparsable_dangerous_text(self):
        self.assertEqual(self.code("echo 'x; git push --force"), 2)
        self.assertEqual(self.code("echo 'ciao"), 0)
        self.assertEqual(self.code("bash <<EOF\ngit push origin tg/7-demo\nEOF"), 2)

    def test_l0_coordinator_writes(self):
        lab = Lab(level="L0")
        try:
            self.assertEqual(lab.bash("echo x > src/app.py").exit, 0)
        finally:
            lab.close()

    def test_second_command_of_the_line_is_checked(self):
        self.assertEqual(self.code("ls && git push origin tg/7-demo", agent_id="a1"), 2)
        self.assertEqual(self.code("ls; echo x > tollgate.toml", agent_id="a1"), 2)


class GitInternalsTest(unittest.TestCase):
    """C3: .git/hooks e .git/config sono protetti anche con Bash."""

    def hooks_commands(self, lab):
        main = lab.main
        return (f"echo x > '{main}/.git/hooks/pre-commit'",
                f"echo x >> '{main}/.git/config'",
                f"touch '{main}/.git/hooks/post-commit'",
                f"touch '{main}/.git/config'",
                f"cp /dev/null '{main}/.git/hooks/pre-push'",
                f"echo x | tee '{main}/.git/config'",
                f"echo x | tee -a '{main}/.git/hooks/commit-msg'",
                f"git config --file '{main}/.git/config' core.hooksPath /x")

    def test_bound_session(self):
        lab = Lab()
        try:
            for cmd in self.hooks_commands(lab) + (
                    "echo x > .git/hooks/pre-commit", "git config core.hooksPath /x",
                    "git config --unset user.name", f"git -C '{lab.main}' config a b",
                    "git config user.email x@example.com"):
                with self.subTest(cmd=cmd):
                    r = lab.bash(cmd, agent_id="a1")
                    self.assertEqual(r.exit, 2, r.stderr)
                    self.assertIn("protett", r.stderr)
            for cmd in ("git config --get user.name", "git config --list", "git config -l",
                        "git config --global user.name x"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd, agent_id="a1").exit, 0)
        finally:
            lab.close()

    def test_unbound_session(self):
        lab = Lab(bind=False)
        try:
            for cmd in self.hooks_commands(lab) + ("git config core.hooksPath /x",
                                                   "echo x > .git/hooks/pre-commit"):
                with self.subTest(cmd=cmd):
                    r = lab.bash(cmd, cwd=lab.main, session_id="altra")
                    self.assertEqual(r.exit, 2, r.stderr)
                    self.assertIn("protett", r.stderr)
            self.assertEqual(lab.bash("git config --get user.name", cwd=lab.main,
                                      session_id="altra").exit, 0)
            self.assertEqual(lab.bash("echo x > src/nuovo.txt", cwd=lab.main,
                                      session_id="altra").exit, 0)
        finally:
            lab.close()

    def test_no_work_at_all(self):
        lab = Lab(work=False)
        try:
            self.assertEqual(lab.bash("git config core.hooksPath /x", cwd=lab.main).exit, 2)
            self.assertEqual(lab.bash("touch .git/hooks/x", cwd=lab.main).exit, 2)
        finally:
            lab.close()


class RemovalTest(unittest.TestCase):
    """mv toglie la sorgente; rm, rmdir e mv su un antenato di un file protetto."""
    ANCESTORS = ("rm -rf .tollgate", "rm -rf docs/superpowers/reviews", "rm -r .tollgate/waivers",
                 "rm -rf .git", "rm -rf .", "rm -rf ./", "rmdir .tollgate", "rm -rf ..",
                 "rm -rf docs", "rm -rf docs/superpowers", "rm -f tollgate.toml",
                 "mv .tollgate /tmp/zz", "mv docs/superpowers/reviews /tmp/zz",
                 "mv tollgate.toml /tmp/zz", "mv .tollgate/waivers/7.toml /tmp/zz",
                 "mv -t /tmp/zz .tollgate", "mv src/app.py tollgate.toml")

    def test_bound_session(self):
        lab = Lab()
        try:
            (lab.wt / ".tollgate/waivers").mkdir(parents=True)
            (lab.wt / ".tollgate/waivers/7.toml").write_text("x\n")
            for cmd in self.ANCESTORS:
                with self.subTest(cmd=cmd):
                    r = lab.bash(cmd, agent_id="a1")
                    self.assertEqual(r.exit, 2, r.stderr)
            for cmd in ("rm -rf build", "rm -rf docs/altro", "rmdir vuota", "mv src/app.py "
                        "src/b.py", "mv src/app.py docs/superpowers/", "rm src/app.py",
                        "mv -t src docs/superpowers/README.md", "cp src/app.py src/c.py",
                        "cp tollgate.toml /tmp/copia.toml"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd, agent_id="a1").exit, 0)
        finally:
            lab.close()

    def test_main_checkout_git_dir(self):
        lab = Lab(bind=False)
        try:
            for cmd in ("rm -rf .git", "rm -rf .git/hooks", "mv .git/config /tmp/zz",
                        "rm -rf .tollgate", "rm -rf ."):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd, cwd=lab.main, session_id="altra").exit, 2)
            self.assertEqual(lab.bash("rm -rf build", cwd=lab.main, session_id="altra").exit, 0)
        finally:
            lab.close()

    def test_state_directory_ancestor(self):
        lab = Lab()
        try:
            r = lab.bash(f"rm -rf '{lab.ts.dir.parent}'", agent_id="a1")
            self.assertEqual(r.exit, 2, r.stderr)
        finally:
            lab.close()


class GitHooksPathTest(unittest.TestCase):
    def test_denied_at_every_level(self):
        lab = Lab()
        try:
            for cmd in ("git -c core.hooksPath=/x commit -m y", "git -c core.hookspath=/x status",
                        "git config core.hooksPath /x", "git config --global core.hooksPath /x",
                        "git config --system core.hooksPath /x",
                        "git config --unset core.hooksPath",
                        "git --config-env=core.hooksPath=V status",
                        "GIT_CONFIG_KEY_0=core.hooksPath git status"):
                with self.subTest(cmd=cmd):
                    r = lab.bash(cmd, agent_id="a1")
                    self.assertEqual(r.exit, 2, r.stderr)
                    self.assertIn("hooksPath", r.stderr)
            for cmd in ("git config --get core.hooksPath", "git -c user.name=x status",
                        "git config --global user.name x"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd, agent_id="a1").exit, 0)
        finally:
            lab.close()

    def test_unbound_session(self):
        lab = Lab(bind=False)
        try:
            for cmd in ("git -c core.hooksPath=/x commit -m y", "git config --global "
                        "core.hooksPath /x"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd, cwd=lab.main, session_id="altra").exit, 2)
        finally:
            lab.close()


class RoutingTest(unittest.TestCase):
    """Stessa logica di writes.py: ogni radice, altro lavoro, worktree illeggibili, fuori repo."""

    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def test_nested_repo_does_not_move_the_root(self):
        for nested, f in (("docs/superpowers/reviews/7", "r.md"), (".tollgate", "waivers/7.toml")):
            with self.subTest(nested=nested):
                (self.lab.wt / nested).mkdir(parents=True, exist_ok=True)
                git(self.lab.wt / nested, "init", "-q")
                r = self.lab.bash(f"echo x > '{self.lab.wt / nested / f}'", agent_id="a1")
                self.assertEqual(r.exit, 2, r.stderr)
                self.assertIn("protett", r.stderr)

    def test_other_active_work_is_denied_but_outside_passes(self):
        wt8 = self.lab.tmp / "wt 8"
        git(self.lab.main, "worktree", "add", "-q", "-b", "tg/8-altro", str(wt8))
        phases.create_work(self.lab.conn, repo_key=repo_key(str(self.lab.origin)), issue=8,
                           level="L1", now=self.lab.now, branch="tg/8-altro",
                           worktree=str(wt8), work_base_sha=self.lab.base,
                           gate_mode="protected")
        for cmd in (f"echo x > '{wt8}/src/app.py'", f"cd '{wt8}' && touch y",
                    f"cd '{wt8}' && git commit -am x"):
            with self.subTest(cmd=cmd):
                r = self.lab.bash(cmd, agent_id="a1")
                self.assertEqual(r.exit, 2, r.stderr)
                self.assertIn("#8", r.stderr)
        self.assertEqual(self.lab.bash(f"git -C '{wt8}' status", agent_id="a1").exit, 0)
        self.assertEqual(self.lab.bash(f"echo x > '{self.lab.tmp}/fuori.txt'",
                                       agent_id="a1").exit, 0)

    def test_worktrees_failure_denies_writes_outside(self):
        with mock.patch.object(core_git, "worktrees", side_effect=core_git.GitError("boom")):
            r = self.lab.bash(f"echo x > '{self.lab.tmp}/fuori.txt'", agent_id="a1")
            self.assertEqual(r.exit, 2)
            self.assertIn("worktree", r.stderr)
            self.assertIn("verificare", r.stderr)
            r = self.lab.bash(f"cd '{self.lab.tmp}' && git commit -m x", agent_id="a1")
            self.assertEqual(r.exit, 2)
            self.assertIn("verificare", r.stderr)
            self.assertEqual(self.lab.bash("echo x > src/app.py", agent_id="a1").exit, 0)
            self.assertEqual(self.lab.bash("git status", agent_id="a1").exit, 0)

    def test_nested_worktree_inside_main_is_not_main_checkout(self):
        nested = self.lab.main / "nested wt"
        git(self.lab.main, "worktree", "add", "-q", "-b", "altro", str(nested))
        r = self.lab.bash(f"echo x > '{nested}/src/app.py'", agent_id="a1")
        self.assertNotIn("checkout principale", r.stderr)

    def test_symlink_to_main_checkout_is_followed(self):
        import os
        os.symlink(self.lab.main / "src", self.lab.wt / "src/lnk")
        r = self.lab.bash("echo x > src/lnk/app.py", agent_id="a1")
        self.assertEqual(r.exit, 2)
        self.assertIn("checkout principale", r.stderr)


class RepoLevelTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(bind=False)

    def tearDown(self):
        self.lab.close()

    def code(self, command):
        return self.lab.bash(command, cwd=self.lab.main, session_id="altra").exit

    def test_push_to_default_branch(self):
        self.assertEqual(self.code("git push origin main"), 2)
        self.assertEqual(self.code("git push"), 2)
        self.assertEqual(self.code("git push origin HEAD:main"), 2)
        self.assertEqual(self.code("git push --all origin"), 2)

    def test_push_head_resolves_to_current_branch(self):
        self.assertEqual(self.code("git push origin HEAD"), 2)
        self.assertEqual(self.code("git push -u origin HEAD"), 2)
        self.assertEqual(self.code("git push origin"), 2)
        git(self.lab.main, "checkout", "-q", "-b", "feat")
        self.assertEqual(self.code("git push origin HEAD"), 0)
        self.assertEqual(self.code("git push -u origin HEAD"), 0)
        self.assertEqual(self.code("git push"), 0)
        self.assertEqual(self.code("git push origin HEAD:main"), 2)

    def test_force_push_denied(self):
        self.assertEqual(self.code("git push --force-with-lease origin tg/7-demo"), 2)
        self.assertEqual(self.code("git push origin +tg/7-demo"), 2)

    def test_force_if_includes_alone_is_not_a_force_push(self):
        self.assertEqual(self.code("git push --force-if-includes origin tg/7-demo"), 0)
        self.assertEqual(self.code("git push --force --force-if-includes origin tg/7-demo"), 2)
        self.assertEqual(self.code("git push --force-with-lease --force-if-includes origin "
                                   "tg/7-demo"), 2)

    def test_tag_listing_is_not_a_write(self):
        lab = Lab(work=False)
        try:
            git(lab.wt, "checkout", "-q", "-b", "tg/7-orfano")
            for cmd in ("git tag -n", "git tag --contains HEAD", "git tag --list", "git tag -l"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd).exit, 0)
            self.assertEqual(lab.bash("git tag v1").exit, 2)
        finally:
            lab.close()

    def test_work_branch_and_worktree_protection(self):
        self.assertEqual(self.code("git merge tg/7-demo"), 2)
        self.assertEqual(self.code("git merge --no-ff origin/tg/7-demo"), 2)
        self.assertEqual(self.code("git branch -D tg/7-demo"), 2)
        self.assertEqual(self.code(f"git worktree remove '{self.lab.wt}'"), 2)
        self.assertEqual(self.code("git worktree add ../doppio tg/7-demo"), 2)
        self.assertEqual(self.code(f"git worktree add '{self.lab.wt}'"), 2)
        self.assertEqual(self.code("git log --oneline"), 0)
        self.assertEqual(self.code("git worktree list"), 0)
        self.assertEqual(self.code("git branch -d altro"), 0)
        self.assertEqual(self.code("git merge altro"), 0)

    def test_main_checkout_is_free_for_the_unbound_session(self):
        self.assertEqual(self.code("touch x.txt"), 0)
        self.assertEqual(self.code("git commit --allow-empty -m x"), 0)

    def test_inactive_repo_push_passes(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-inattivo-"))
        try:
            repo = make_repo(tmp / "r")
            r = self.lab.bash("git push origin main", cwd=repo, session_id="altra")
            self.assertEqual(r.exit, 0)
            self.assertEqual(self.code(f"cd '{repo}' && git push origin main"), 0)
            self.assertEqual(self.code(f"git -C '{repo}' push origin main"), 0)
            self.assertEqual(self.code(f"cd '{repo}' && git push -f origin main"), 0)
            self.assertEqual(self.code(f"cd '{repo}' && git reset --hard"), 2)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_global_rules_apply_unbound_too(self):
        for cmd in ("claude -p x", "git reset --hard", "git commit -n -m x", "rm -rf /tmp/x",
                    "echo x > tollgate.toml", "TOLLGATE_STATE=/x ls"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd), 2)


class OrphanBashTest(unittest.TestCase):
    def test_writes_denied_reads_allowed(self):
        lab = Lab(work=False)
        try:
            r = lab.bash("git commit -am x")
            self.assertEqual(r.exit, 2)
            self.assertIn("/tollgate:adopt #7", r.stderr)
            self.assertEqual(lab.bash("echo x > src/app.py").exit, 2)
            self.assertEqual(lab.bash("sed -i 's/a/b/' src/app.py").exit, 2)
            for cmd in ("git status", "git log", "git branch", "git branch -a",
                        "git worktree list", "git stash list", "git config --get user.name",
                        "cat src/app.py", "echo x > docs/superpowers/n.md"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(lab.bash(cmd).exit, 0)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
