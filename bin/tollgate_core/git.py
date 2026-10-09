"""Git in sola lettura per hook e CLI (spec 3.2): diff dalla base, file, impronte."""
from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class GitError(Exception):
    pass


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None
    added: int
    removed: int
    binary: bool


def _proc(repo, args, input_=None):
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              input=input_)
    except FileNotFoundError as e:
        raise GitError("git non disponibile") from e


def run(repo, *args, check=True) -> str:
    r = _proc(repo, args)
    if check and r.returncode != 0:
        raise GitError(f"git {' '.join(args)}: "
                       f"{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "surrogateescape")


def ok(repo, *args) -> bool:
    try:
        return _proc(repo, args).returncode == 0
    except GitError:
        return False


def _resolved(path) -> Path:
    """Percorso assoluto con i collegamenti risolti; la coda che non esiste ancora resta lessicale."""
    p = Path(os.path.abspath(path))
    tail = []
    while not p.exists() and p.parent != p:
        tail.insert(0, p.name)
        p = p.parent
    return p.resolve().joinpath(*tail)


def toplevel(path) -> Path | None:
    """Radice del repo di `path`. Dentro una cartella `.git` (anche se non esiste) vale il repo che la
    possiede; altrimenti la prima cartella esistente risalendo dal percorso. Un `.git` file
    (worktree collegato) da' il worktree."""
    p = _resolved(path)
    if ".git" in p.parts:
        last = len(p.parts) - 1 - p.parts[::-1].index(".git")
        p = Path(*p.parts[:last])
    while not p.is_dir():
        if p.parent == p:
            return None
        p = p.parent
    try:
        out = run(p, "rev-parse", "--show-toplevel", check=False).strip()
    except GitError:
        return None
    return Path(out).resolve() if out else None


def head(repo) -> str | None:
    out = run(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).strip()
    return out or None


def branch(repo) -> str | None:
    out = run(repo, "symbolic-ref", "--short", "-q", "HEAD", check=False).strip()
    return out or None


def common_dir(repo) -> Path:
    out = run(repo, "rev-parse", "--git-common-dir").strip()
    p = Path(out)
    return (p if p.is_absolute() else Path(repo) / p).resolve()


def worktrees(repo) -> list[tuple[Path, str | None]]:
    out, path, br = [], None, None
    for line in run(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if line.startswith("worktree "):
            path, br = Path(line[9:]).resolve(), None
        elif line.startswith("branch "):
            br = line[7:].removeprefix("refs/heads/")
        elif not line and path is not None:
            out.append((path, br))
            path = None
    return out


def main_worktree(repo) -> Path:
    return worktrees(repo)[0][0]


def local_branches(repo) -> set[str]:
    return {b for b in run(repo, "for-each-ref", "--format=%(refname:short)",
                           "refs/heads").splitlines() if b}


def resolve_ref(repo, ref: str) -> str | None:
    out = run(repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}", check=False).strip()
    return out or None


def default_branch(repo) -> str | None:
    b = run(repo, "config", "--get", "tollgate.defaultBranch", check=False).strip()
    if b:
        return b
    sym = run(repo, "symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False).strip()
    if sym:
        return sym.removeprefix("refs/remotes/origin/")
    for b in ("main", "master"):
        if resolve_ref(repo, f"origin/{b}"):
            return b
    return None


def default_ref(repo) -> str | None:
    """Ordine di 7.1: tollgate.defaultBranch, origin/HEAD, origin/main, origin/master."""
    b = run(repo, "config", "--get", "tollgate.defaultBranch", check=False).strip()
    for ref in ([f"origin/{b}"] if b else []) + ["origin/HEAD", "origin/main", "origin/master"]:
        if resolve_ref(repo, ref):
            return ref
    return None


def origin_url(repo) -> str | None:
    out = run(repo, "remote", "get-url", "origin", check=False).strip()
    return out or None


def _parse_z(numstat: str, status: str) -> list[Change]:
    st_tokens = status.split("\0")
    statuses: dict[str, tuple[str, str | None]] = {}
    i = 0
    while i < len(st_tokens) and st_tokens[i]:
        code = st_tokens[i]
        if code[0] in "RC":
            statuses[st_tokens[i + 2]] = ("R", st_tokens[i + 1])
            i += 3
        else:
            statuses[st_tokens[i + 1]] = (code[0], None)
            i += 2
    out = []
    ns = numstat.split("\0")
    i = 0
    while i < len(ns) and ns[i]:
        added, removed, path = ns[i].split("\t", 2)
        if path == "":
            path = ns[i + 2]
            i += 3
        else:
            i += 1
        binary = added == "-"
        st, old = statuses.get(path, ("M", None))
        out.append(Change("M" if st == "T" else st, path, old,
                          0 if binary else int(added), 0 if binary else int(removed), binary))
    return out


def _untracked(repo) -> list[Change]:
    out = []
    for rel in run(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not rel:
            continue
        try:
            data = (Path(repo) / rel).read_bytes()
        except OSError:
            continue
        binary = b"\0" in data[:8000]
        lines = 0 if binary else data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
        out.append(Change("A", rel, None, lines, 0, binary))
    return out


def changes(repo, base: str, *, head: str | None = None) -> list[Change]:
    refs = [base] if head is None else [base, head]
    numstat = run(repo, "diff", "-M", "--numstat", "-z", *refs, "--")
    status = run(repo, "diff", "-M", "--name-status", "-z", *refs, "--")
    out = _parse_z(numstat, status)
    if head is None:
        out += _untracked(repo)
    return out


def commit_changes(repo, sha: str) -> list[Change]:
    parent = resolve_ref(repo, f"{sha}^") or EMPTY_TREE
    return changes(repo, parent, head=sha)


def diff_size(repo, base: str, *, head: str | None = None) -> int:
    refs = [base] if head is None else [base, head]
    size = len(run(repo, "diff", "--no-color", *refs, "--").encode("utf-8", "surrogateescape"))
    if head is None:
        for rel in run(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
            if rel:
                try:
                    size += (Path(repo) / rel).stat().st_size
                except OSError:
                    pass
    return size


def show(repo, ref: str, path: str) -> bytes | None:
    r = _proc(repo, ["show", f"{ref}:{path}"])
    return r.stdout if r.returncode == 0 else None


def _text(data: bytes | None) -> str | None:
    """Testo di un blob: None se binario o assente. Se non è UTF-8 si ripiega su Latin-1 (mai un crash)."""
    if data is None or b"\0" in data[:8000]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def text_at(repo, ref: str, path: str) -> str | None:
    return _text(show(repo, ref, path))


def worktree_text(repo, path: str) -> str | None:
    try:
        return _text((Path(repo) / path).read_bytes())
    except OSError:
        return None


def exists_at(repo, ref: str, path: str) -> bool:
    return ok(repo, "cat-file", "-e", f"{ref}:{path}")


def blob_sha(repo, path: str) -> str:
    return run(repo, "hash-object", "--", path).strip()


def rev_list(repo, base: str, head: str) -> list[str]:
    return [s for s in run(repo, "rev-list", "--reverse", f"{base}..{head}").split() if s]


def _excluded(rel: str, exclude) -> bool:
    return any(rel == e.rstrip("/") or rel.startswith(e.rstrip("/") + "/") for e in exclude)


def fingerprint(repo, exclude) -> str:
    """Impronta dei file tracciati e non tracciati non ignorati (7.3), esclusi output_dirs."""
    h = hashlib.sha256()
    files = run(repo, "ls-files", "-co", "--exclude-standard", "-z").split("\0")
    for rel in sorted({f for f in files if f}):
        if _excluded(rel, exclude):
            continue
        try:
            digest = hashlib.sha1((Path(repo) / rel).read_bytes()).hexdigest()
        except FileNotFoundError:
            digest = "cancellato"
        except IsADirectoryError:
            digest = "cartella"
        h.update(f"{rel}\0{digest}\n".encode("utf-8", "surrogateescape"))
    return h.hexdigest()


def is_clean(repo, exclude) -> bool:
    out = run(repo, "status", "--porcelain", "-z", "--untracked-files=all")
    entries = [e for e in out.split("\0") if e]
    paths, skip = [], False
    for e in entries:
        if skip:
            skip = False
            continue
        code, rel = e[:2], e[3:]
        paths.append(rel)
        if code[0] in "RC":
            skip = True
    return all(_excluded(p, exclude) for p in paths)
