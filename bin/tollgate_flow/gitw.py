"""Git in scrittura per il flusso (spec 6.1). La lettura sta in `tollgate_core.git`."""
from __future__ import annotations

import fnmatch
import os
import subprocess
from pathlib import Path

from tollgate_core import git

FETCH_TIMEOUT_S = 120
LS_REMOTE_TIMEOUT_S = 60
WRITE_TIMEOUT_S = 60


class GitWriteError(Exception):
    pass


def _run(repo, *args, timeout=WRITE_TIMEOUT_S) -> subprocess.CompletedProcess:
    cmd = ["git", "-c", "core.fsmonitor=false", "-C", str(repo), *args]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except FileNotFoundError as e:
        raise GitWriteError("git non disponibile") from e
    except subprocess.TimeoutExpired as e:
        raise GitWriteError(f"git {' '.join(args)}: timeout dopo {timeout} s") from e


def _checked(repo, *args, timeout=WRITE_TIMEOUT_S) -> str:
    r = _run(repo, *args, timeout=timeout)
    if r.returncode != 0:
        raise GitWriteError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def fetch(repo) -> bool:
    """`git fetch origin`. Falso senza rete (o per qualunque errore): mai un'eccezione."""
    try:
        return _run(repo, "fetch", "origin", timeout=FETCH_TIMEOUT_S).returncode == 0
    except GitWriteError:
        return False


def worktree_add(repo, path, *, branch: str, start_point: str | None, new_branch: bool) -> None:
    """Nuovo ramo da `start_point` (senza ramo a monte, C18) o ramo esistente."""
    if new_branch:
        if not start_point:
            raise GitWriteError("serve il punto di partenza per un ramo nuovo")
        _checked(repo, "worktree", "add", "--no-track", "-b", branch, str(path), start_point)
    else:
        _checked(repo, "worktree", "add", str(path), branch)


def delete_branch(repo, branch: str, expected_sha: str) -> bool:
    """Toglie `branch` solo se punta ancora a `expected_sha` (atomico: `update-ref -d` con il
    vecchio valore fallisce se il ramo punta altrove). Mai `branch -D`. Vero se tolto."""
    try:
        return _run(repo, "update-ref", "-d", f"refs/heads/{branch}",
                    expected_sha).returncode == 0
    except GitWriteError:
        return False


def add_excludes(repo, lines: list[str]) -> None:
    """Righe nuove in `info/exclude` della cartella comune, senza duplicati."""
    target = git.common_dir(repo) / "info" / "exclude"
    try:
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        have = set(current.splitlines())
        new = [ln for ln in dict.fromkeys(lines) if ln not in have]
        if not new:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if not current or current.endswith("\n") else "\n"
        target.write_text(current + prefix + "\n".join(new) + "\n", encoding="utf-8")
    except OSError as e:
        raise GitWriteError(f"info/exclude: {e.strerror}") from e


def set_config(repo, key: str, value: str) -> None:
    _checked(repo, "config", key, value)


def remote_branches(repo, pattern: str) -> list[str]:
    """Rami di `origin` che combaciano con il glob (`tg/7-*`). Vuoto senza rete."""
    try:
        r = _run(repo, "ls-remote", "--heads", "origin", timeout=LS_REMOTE_TIMEOUT_S)
    except GitWriteError:
        return []
    if r.returncode != 0:
        return []
    names = []
    for line in r.stdout.splitlines():
        _, _, ref = line.partition("\t")
        if ref.startswith("refs/heads/"):
            names.append(ref.removeprefix("refs/heads/"))
    return sorted(n for n in names if fnmatch.fnmatchcase(n, pattern))


def worktree_dir(main: Path, branch: str) -> Path:
    """`<checkout principale>/.claude/worktrees/tg-<N>-<slug>` (decisione 4)."""
    return main / ".claude" / "worktrees" / branch.replace("/", "-")
