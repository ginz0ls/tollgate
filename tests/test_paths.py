import subprocess
import sys
import tempfile
import unittest
from datetime import timezone
from pathlib import Path

from tests.helpers import BIN, TempState
from tollgate_core import VERSION, clock
from tollgate_core.paths import (
    default_state_root, ensure_dirs, repo_key, resolve_state, test_env,
)


class StateTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()

    def tearDown(self):
        self.t.cleanup()

    def test_state_with_sentinel_is_test_mode(self):
        s = resolve_state({"TOLLGATE_STATE": str(self.t.dir)})
        self.assertEqual(s.root, self.t.dir)
        self.assertTrue(s.test_mode)
        self.assertEqual(s.db_path, self.t.dir / "tollgate.db")
        self.assertEqual(s.backup_dir, self.t.dir / "backup")

    def test_state_without_sentinel_is_ignored(self):
        bare = Path(tempfile.mkdtemp())
        s = resolve_state({"TOLLGATE_STATE": str(bare)})
        self.assertEqual(s.root, default_state_root())
        self.assertFalse(s.test_mode)

    def test_default_root(self):
        self.assertEqual(default_state_root(), Path.home() / ".local" / "state" / "tollgate")

    def test_test_env_only_in_test_mode(self):
        env = {"TOLLGATE_STATE": str(self.t.dir), "TOLLGATE_GH": "/tmp/fake-gh"}
        self.assertEqual(test_env(resolve_state(env), "TOLLGATE_GH", env), "/tmp/fake-gh")
        env2 = {"TOLLGATE_GH": "/tmp/fake-gh"}
        self.assertIsNone(test_env(resolve_state(env2), "TOLLGATE_GH", env2))

    def test_test_env_rejects_unknown_name(self):
        with self.assertRaises(ValueError):
            test_env(self.t.state, "PATH", {})

    def test_ensure_dirs(self):
        ensure_dirs(self.t.state)
        self.assertTrue(self.t.state.backup_dir.is_dir())


class RepoKeyTest(unittest.TestCase):
    def test_forms(self):
        cases = {
            "https://github.com/Owner/Name.git": "github.com/owner/name",
            "https://github.com/owner/name/": "github.com/owner/name",
            "git@github.com:Owner/Name.git": "github.com/owner/name",
            "ssh://git@github.com/owner/name.git": "github.com/owner/name",
            "https://user@github.com/owner/name": "github.com/owner/name",
            "https://github.com:443/owner/name.git": "github.com/owner/name",
        }
        for url, key in cases.items():
            with self.subTest(url=url):
                self.assertEqual(repo_key(url), key)


class ClockTest(unittest.TestCase):
    def test_roundtrip_and_order(self):
        a = clock.now()
        self.assertEqual(a.tzinfo, timezone.utc)
        self.assertEqual(clock.parse(clock.fmt(a)), a)
        b = clock.parse("2026-10-08T10:00:00.000000Z")
        c = clock.parse("2026-10-08T10:00:01.000000Z")
        self.assertLess(clock.fmt(b), clock.fmt(c))


class EntryPointTest(unittest.TestCase):
    def test_version(self):
        r = subprocess.run([sys.executable, str(BIN / "tollgate"), "--version"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), f"tollgate {VERSION}")
