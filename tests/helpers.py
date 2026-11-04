import contextlib
import http.client  # noqa: F401
import os
import shutil
import socket
import ssl  # noqa: F401
import subprocess
import tempfile
import urllib.request  # noqa: F401
from pathlib import Path
from unittest import mock

from tollgate_core.paths import SENTINEL, State

# `ssl`, `http.client` e `urllib.request` si importano qui, prima di ogni patch di `socket`: sotto
# `no_network()` il primo import di `urllib.request` definirebbe classi derivate da un
# `socket.socket` sostituito (con un finto che fosse una semplice funzione darebbe `TypeError`
# se `ssl` non fosse già caricato). Così derivano sempre dalla classe vera.

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"

# Tutte le variabili da cui il controllo dei modelli legge una chiave (B3-bis, decisione 4).
MODEL_KEY_VARS = (
    "TOLLGATE_MODELS_ANTHROPIC_KEY", "ANTHROPIC_API_KEY",
    "TOLLGATE_MODELS_GEMINI_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY",
    "TOLLGATE_MODELS_OPENAI_KEY", "OPENAI_API_KEY",
    "TOLLGATE_MODELS_OPENROUTER_KEY", "OPENROUTER_API_KEY",
)


class _NoSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        raise AssertionError("rete in un test")


def _no_connection(*args, **kwargs):
    raise AssertionError("rete in un test")


@contextlib.contextmanager
def no_network():
    """Per i test che toccano il controllo dei modelli: toglie da `os.environ` le variabili delle
    chiavi e fa fallire ogni socket nuovo e `socket.create_connection`. Vale solo nel processo
    del test (i processi figli non sono coperti)."""
    with mock.patch.dict(os.environ), \
            mock.patch.object(socket, "socket", _NoSocket), \
            mock.patch.object(socket, "create_connection", _no_connection):
        for name in MODEL_KEY_VARS:
            os.environ.pop(name, None)
        yield


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


def make_origin_repo(root, files: dict, toml: str):
    """Origin nudo e checkout principale con tollgate.toml sul predefinito (repo attivo, 7.1)."""
    root = Path(root)
    origin = root / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True,
                   capture_output=True)
    main = make_repo(root / "main")
    (main / "tollgate.toml").write_text(toml)
    for rel, text in files.items():
        p = main / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    git(main, "add", "-A")
    git(main, "commit", "-qm", "base")
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "-u", "origin", "main")
    git(main, "remote", "set-head", "origin", "main")
    git(main, "config", "tollgate.defaultBranch", "main")
    return main, origin, git(main, "rev-parse", "HEAD")
