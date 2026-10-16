### Task 9: Git in sola lettura

**Files:**
- Create: `bin/tollgate_core/git.py`
- Test: `tests/test_git.py`

**Interfaces:**
- Produces:
  - `git.GitError`; `git.Change(status, path, old_path, added, removed, binary)` (stessi attributi di `level.FileChange`).
  - `git.run(repo, *args, check=True) -> str`; `git.ok(repo, *args) -> bool`.
  - `git.toplevel(path) -> Path | None` (risale alla prima cartella esistente); `git.head(repo) -> str | None`; `git.branch(repo) -> str | None`; `git.common_dir(repo) -> Path`; `git.worktrees(repo) -> list[tuple[Path, str | None]]`; `git.main_worktree(repo) -> Path`; `git.local_branches(repo) -> set[str]`.
  - `git.resolve_ref(repo, ref) -> str | None`; `git.default_ref(repo) -> str | None`; `git.default_branch(repo) -> str | None`; `git.origin_url(repo) -> str | None`.
  - `git.changes(repo, base, *, head=None) -> list[Change]` (con `head=None`: dalla base al working tree, non tracciati compresi); `git.commit_changes(repo, sha) -> list[Change]`; `git.diff_size(repo, base, *, head=None) -> int`.
  - `git.show(repo, ref, path) -> bytes | None`; `git.text_at(repo, ref, path) -> str | None`; `git.worktree_text(repo, path) -> str | None`; `git.exists_at(repo, ref, path) -> bool`; `git.blob_sha(repo, path) -> str`.
  - `git.rev_list(repo, base, head) -> list[str]` (dal più vecchio); `git.fingerprint(repo, exclude) -> str`; `git.is_clean(repo, exclude) -> bool`.

- [ ] **Step 1: Test**

`tests/test_git.py`:

```python
import shutil
import tempfile
import unittest
from pathlib import Path

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

    def test_toplevel_of_missing_path(self):
        self.assertEqual(git.toplevel(self.repo / "src" / "nuova" / "x.py"), self.repo.resolve())
        self.assertIsNone(git.toplevel(self.tmp / "fuori"))

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_git -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_core.git'`.

- [ ] **Step 3: `git.py`**

```python
"""Git in sola lettura per hook e CLI (spec 3.2): diff dalla base, file, impronte."""
from __future__ import annotations

import hashlib
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


def toplevel(path) -> Path | None:
    p = Path(path)
    while not p.exists():
        if p.parent == p:
            return None
        p = p.parent
    if not p.is_dir():
        p = p.parent
    try:
        out = run(p, "rev-parse", "--show-toplevel").strip()
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
    if data is None or b"\0" in data[:8000]:
        return None
    return data.decode("utf-8", "replace")


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
```

- [ ] **Step 4: Verificare che passi**

Run: `python3 -B -m unittest tests.test_git -v`
Expected: PASS. Nota: `git worktree list --porcelain` e `--show-toplevel` restituiscono percorsi risolti; i test confrontano con `.resolve()` perché `/tmp` può essere un collegamento simbolico.

- [ ] **Step 5: Suite e commit**

Run: `tests/run`
Expected: OK.

```bash
git add bin/tollgate_core/git.py tests/test_git.py
git commit -m "tollgate P2: accesso a git in sola lettura"
```

---

