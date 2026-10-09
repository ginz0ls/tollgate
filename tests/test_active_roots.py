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

from tests.helpers import ROOT, make_repo
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

    def wrapper(self, payload):
        r = subprocess.run([str(ROOT / "hooks" / "run"), "PreToolUse"], input=json.dumps(payload),
                           capture_output=True, text=True, env=self.lab.ts.env(),
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
