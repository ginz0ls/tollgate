import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from tollgate_core.paths import SENTINEL, State

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"


class TempState:
    """Cartella di stato temporanea con la sentinella dei test (spec 3.1)."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="tollgate-test-"))
        (self.dir / SENTINEL).write_text("")
        self.state = State(self.dir, True)

    def env(self):
        e = dict(os.environ)
        e["TOLLGATE_STATE"] = str(self.dir)
        return e

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def git(repo, *args):
    r = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True)
    return r.stdout.strip()


def make_repo(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    return path
