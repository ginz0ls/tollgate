import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import MODEL_KEY_VARS

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "tests" / "run"


class ProbeTest(unittest.TestCase):
    """Sonda lanciata da RunScriptTest dentro `tests/run`: non fa nulla da sola."""

    @unittest.skipUnless(os.environ.get("RUN_TMP_PROBE"), "sonda di tests/run")
    def test_tmpdir_probe(self):
        Path(os.environ["RUN_TMP_PROBE"]).write_text(tempfile.gettempdir())
        if os.environ.get("RUN_TMP_PROBE_FAIL"):
            self.fail("fallimento voluto")
        if os.environ.get("RUN_TMP_PROBE_SEAL"):
            sealed = Path(tempfile.gettempdir()) / "sigillata"
            (sealed / "sotto").mkdir(parents=True)
            (sealed / "sotto").chmod(0)
            sealed.chmod(0o500)


class RunScriptTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="tollgate-runtest-"))
        self.addCleanup(self._rm)
        self.probe = self.base / "probe.txt"

    def _rm(self):
        subprocess.run(["chmod", "-R", "u+rwX", str(self.base)], check=False)
        subprocess.run(["rm", "-rf", str(self.base)], check=False)

    def launch(self, **extra):
        env = {k: v for k, v in os.environ.items()
               if k not in MODEL_KEY_VARS and k != "PYTHONWARNINGS"}
        env.update(TMPDIR=str(self.base), PYTHONS=sys.executable,
                   RUN_TMP_PROBE=str(self.probe), **extra)
        return subprocess.run([str(RUN), "-k", "test_tmpdir_probe"], env=env,
                              capture_output=True, text=True)

    def seen(self):
        return Path(self.probe.read_text())

    def test_run_sets_and_removes_tmpdir(self):
        r = self.launch()
        self.assertEqual(r.returncode, 0, r.stderr)
        seen = self.seen()
        self.assertTrue(seen.name.startswith("tollgate-run-"), seen)
        self.assertEqual(seen.parent.resolve(), self.base.resolve())
        self.assertFalse(seen.exists())

    def test_run_removes_tmpdir_on_failure(self):
        r = self.launch(RUN_TMP_PROBE_FAIL="1")
        self.assertNotEqual(r.returncode, 0)
        seen = self.seen()
        self.assertTrue(seen.name.startswith("tollgate-run-"), seen)
        self.assertFalse(seen.exists())

    @unittest.skipIf(os.geteuid() == 0, "da root i permessi non contano")
    def test_run_removes_sealed_dirs_and_keeps_exit_code(self):
        r = self.launch(RUN_TMP_PROBE_SEAL="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.seen().exists())


class KnownLeaksTest(unittest.TestCase):
    def check_gone(self, case, folder):
        case.doCleanups()
        self.assertFalse(Path(folder).exists(), folder)

    def test_known_leaks_closed(self):
        from tests.test_gh import PrReadTest
        from tests.test_hook_engine import RunnerTest
        from tests.test_statusline import CtxTest

        # FakeGhCase non ha test propri: si usa una sottoclasse con test.
        case = PrReadTest("test_pr_for_branch_latest")
        case.setUp()
        self.check_gone(case, case.tmp)

        ctx = CtxTest("test_executable")
        ctx.setUp()
        self.check_gone(ctx, ctx.home)

        RunnerTest.setUpClass()
        self.addCleanup(RunnerTest.tearDownClass)
        folder = RunnerTest.tmp
        self.assertTrue(folder.exists())
        self.doCleanups()
        self.assertFalse(folder.exists())


if __name__ == "__main__":
    unittest.main()
