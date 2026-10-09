"""I1 e M1 della revisione finale: la protezione segue il bersaglio, non il `cwd`.

Un registro delle radici attive (`<stato>/active/<hash>`) permette al wrapper di accorgersi che
un `PreToolUse` nomina un repo attivo anche quando il `cwd` sta altrove; il runner prende allora
repo e configurazione dal bersaglio (file per Edit/Write, `-C` o `cd` per Bash)."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, git as run_git, make_repo
from tests.hookkit import Lab
from tollgate_core import active

OTHER = "sess-altra"   # sessione non legata a nessun lavoro


class ActiveRootsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.addCleanup(self.lab.close)
        # Un primo hook dentro il repo attivo fa scrivere il registro al runner.
        self.assertEqual(self.lab.bash("ls", agent_id="a1").exit, 0)
        self.outside = Path(tempfile.mkdtemp(prefix="tollgate parent "))
        self.addCleanup(shutil.rmtree, self.outside, True)
        self.neighbor = make_repo(self.outside / "vicino")   # repo senza tollgate.toml

    def wrapper(self, payload, extra_env=None):
        env = dict(self.lab.ts.env(), **(extra_env or {}))
        r = subprocess.run([str(ROOT / "hooks" / "run"), "PreToolUse"], input=json.dumps(payload),
                           capture_output=True, text=True, env=env,
                           cwd=payload["cwd"], timeout=60)
        return r

    def bash_payload(self, command, cwd):
        return self.lab._base("PreToolUse-Bash", None, cwd, session_id=OTHER,
                              tool_input={"command": command, "description": "x"})

    def edit_payload(self, path, cwd):
        return self.lab._base("PreToolUse-Write", None, cwd, session_id=OTHER, tool_name="Write",
                              tool_input={"file_path": str(path), "content": "x"})

    def test_runner_registers_checkout_and_worktrees(self):
        files = list((self.lab.ts.dir / "active").iterdir())
        self.assertEqual(len(files), 1)
        lines = files[0].read_text().splitlines()
        self.assertIn(str(self.lab.main.resolve()), lines)
        self.assertIn(str(self.lab.wt.resolve()), lines)
        self.assertNotIn("", lines)

    def test_protected_write_with_cwd_outside_any_repo(self):
        for cwd in (self.outside, self.neighbor):
            with self.subTest(cwd=str(cwd)):
                r = self.wrapper(self.edit_payload(self.lab.main / "tollgate.toml", cwd))
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("protetto", r.stderr)

    def test_push_to_default_branch_with_cwd_outside(self):
        for cwd in (self.outside, self.neighbor):
            with self.subTest(cwd=str(cwd)):
                r = self.wrapper(self.bash_payload(
                    f"git -C '{self.lab.main}' push origin main", cwd))
                self.assertEqual(r.returncode, 2, r.stderr)
                r = self.wrapper(self.bash_payload(f"cd '{self.lab.main}' && git push origin main",
                                                   cwd))
                self.assertEqual(r.returncode, 2, r.stderr)

    def test_write_into_a_work_worktree_from_outside(self):
        r = self.wrapper(self.edit_payload(self.lab.wt / ".tollgate/waivers/7.toml",
                                           self.outside))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_relative_and_home_forms_from_a_parent_directory(self):
        # Fix round 2: il cwd e' la cartella madre che contiene il repo attivo.
        parent = self.lab.tmp
        main = self.lab.main
        env_home = {"HOME": str(parent)}
        forms = {
            "write relativo": ("w", "main/tollgate.toml"),
            "redirect con ~": ("b", "echo x > ~/main/tollgate.toml"),
            "cd relativo e push": ("b", "cd main && git push origin main"),
            "git -C relativo": ("b", "git -C main push origin main"),
            "redirect assoluto": ("b", f"echo x > '{main}/tollgate.toml'"),
            "sed -i assoluto": ("b", f"sed -i s/a/b/ '{main}/tollgate.toml'"),
            "cd relativo e redirect": ("b", "cd main && echo x > tollgate.toml"),
            "rm assoluto": ("b", f"rm '{main}/tollgate.toml'"),
        }
        for name, (kind, arg) in forms.items():
            payload = self.edit_payload(arg, parent) if kind == "w" \
                else self.bash_payload(arg, parent)
            with self.subTest(form=name):
                r = self.wrapper(payload, env_home)
                self.assertEqual(r.returncode, 2, r.stderr)

    def test_command_touching_no_active_repo_passes_from_outside(self):
        for cwd in (self.outside, self.neighbor, self.lab.tmp):
            for cmd in ("ls /tmp", "echo x > note.txt", "cd vicino && git status"):
                with self.subTest(cwd=str(cwd), cmd=cmd):
                    r = self.wrapper(self.bash_payload(cmd, cwd))
                    self.assertEqual(r.returncode, 0, r.stderr)

    def test_main_checkout_and_its_worktree_are_one_repo(self):
        # Fix round 3: checkout principale e worktree condividono il repo git.
        main, wt = self.lab.main, self.lab.wt
        for cmd in (f"git -C '{main}' status; git -C '{wt}' status",
                    f"git -C '{wt}' diff && git -C '{main}' log",
                    f"echo x > '{main}/a.txt'; echo y > '{wt}/b.txt'",
                    f"rm '{main}/x' '{wt}/y'"):
            for cwd in (self.outside, self.lab.tmp):
                with self.subTest(cmd=cmd, cwd=str(cwd)):
                    r = self.wrapper(self.bash_payload(cmd, cwd))
                    self.assertEqual(r.returncode, 0, r.stderr)

    def test_worktree_is_preferred_when_main_and_worktree_are_both_named(self):
        main, wt = self.lab.main, self.lab.wt
        r = self.wrapper(self.bash_payload(
            f"echo x > '{main}/a.txt'; echo y > '{wt}/.tollgate/waivers/7.toml'", self.outside))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertNotIn("più repo attivi", r.stderr)

    def test_git_c_targets_resolve_against_the_c_directory(self):
        # Fix round 3: il bersaglio di checkout/restore/rm e' relativo alla directory di -C.
        main = self.lab.main
        for cmd in ("git -C main checkout origin/main -- tollgate.toml",
                    "git -C main restore tollgate.toml",
                    "git -C main rm tollgate.toml",
                    f"git -C '{main}' checkout origin/main -- tollgate.toml",
                    f"git -C '{main}' restore tollgate.toml"):
            with self.subTest(cmd=cmd):
                r = self.wrapper(self.bash_payload(cmd, self.lab.tmp))
                self.assertEqual(r.returncode, 2, r.stderr)

    def test_command_touching_two_active_repos_is_denied_with_a_message(self):
        second = make_repo(self.outside / "secondo")
        (second / "tollgate.toml").write_text(
            'schema_version = 1\n[gate]\nmode = "protected"\n[commands]\nverify = "true"\n'
            'gate = ["verify"]\n')
        run_git(second, "add", "-A")
        run_git(second, "commit", "-qm", "x")
        run_git(second, "update-ref", "refs/remotes/origin/main", "HEAD")
        active.register(self.lab.ts.state, second)
        r = self.wrapper(self.bash_payload(
            f"echo x > '{self.lab.main}/a.txt'; echo y > '{second}/b.txt'", self.outside))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("più repo attivi", r.stderr)

    def test_unrelated_actions_outside_still_pass(self):
        r = self.wrapper(self.edit_payload(self.outside / "note.txt", self.outside))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.wrapper(self.bash_payload(f"git -C '{self.neighbor}' push origin main",
                                           self.outside))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_runner_nonexistent_cwd_uses_the_target_repo(self):
        r = self.lab.pre_edit(self.lab.main / "tollgate.toml", cwd="/non/esiste",
                              session_id=OTHER)
        self.assertEqual(r.exit, 2, r.stderr)
        r = self.lab.bash(f"git -C '{self.lab.main}' push origin main", cwd="/non/esiste",
                          session_id=OTHER)
        self.assertEqual(r.exit, 2, r.stderr)
        self.assertEqual(self.lab.bash("ls", cwd="/non/esiste", session_id=OTHER).exit, 0)

    def test_registry_helpers(self):
        self.assertTrue(active.prefixes(self.lab.ts.state))
        self.assertIn(str(self.lab.wt.resolve()), active.prefixes(self.lab.ts.state))


if __name__ == "__main__":
    unittest.main()
