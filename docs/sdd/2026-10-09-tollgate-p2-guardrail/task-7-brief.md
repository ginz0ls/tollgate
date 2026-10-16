### Task 7: Analisi: comandi Bash

**Files:**
- Create: `bin/tollgate_analysis/bash.py`
- Test: `tests/test_bash.py`

**Interfaces:**
- Produces:
  - `bash.BashParseError`; `bash.Cmd(argv, cwd, env, redirects, nested=False)`; `bash.parse(command: str, cwd: str) -> list[Cmd]` (solleva `BashParseError`).
  - `bash.git_call(cmd) -> tuple[str | None, list[str], str | None]` (sottocomando, argomenti, `-C`); `bash.effective_dir(cmd) -> str`.
  - `bash.is_push(cmd)`, `bash.push_is_force(cmd)`, `bash.push_targets(cmd) -> list[str]`, `bash.is_commit(cmd)`, `bash.commit_all(cmd)`, `bash.is_gh_pr_create(cmd)`, `bash.branch_change(cmd) -> str | None`, `bash.checkout_args(cmd) -> list[str]`, `bash.destructive(cmd) -> str | None`, `bash.rm_rf_targets(cmd) -> list[str]`, `bash.write_targets(cmd) -> list[str]`, `bash.writes(cmd) -> bool`, `bash.is_claude(cmd)`, `bash.is_tollgate_hook(cmd)`, `bash.uses_tollgate_bin(cmd, plugin_bin: str) -> bool`, `bash.merge_args(cmd) -> list[str]`, `bash.worktree_op(cmd)`, `bash.branch_deletes(cmd) -> list[str]`.
  - `bash.EffectsCfg(commands=(), project_scripts=(), allow=())`; `bash.normalized(cmd) -> str`; `bash.effect_reason(cmd, cfg) -> str | None`; `bash.script_path(cmd) -> str | None` (percorso assoluto normalizzato dello script eseguito); `bash.text_danger(raw) -> str | None`.

- [ ] **Step 1: Test**

`tests/test_bash.py`:

```python
import unittest

from tollgate_analysis import bash

CWD = "/r/wt"


def cmds(text, cwd=CWD):
    return bash.parse(text, cwd)


def one(text):
    out = cmds(text)
    return out[-1]


class ParseTest(unittest.TestCase):
    def test_chain_and_cd(self):
        out = cmds("cd /r/main && git status; ls")
        self.assertEqual([c.argv[0] for c in out], ["cd", "git", "ls"])
        self.assertEqual(out[1].cwd, "/r/main")

    def test_git_c(self):
        c = one("git -C ../main commit -am x")
        self.assertEqual(bash.git_call(c)[0], "commit")
        self.assertEqual(bash.effective_dir(c), "/r/main")
        self.assertTrue(bash.commit_all(c))

    def test_redirects_and_env(self):
        c = one("FOO=1 echo x > src/a.py 2>&1")
        self.assertEqual(c.env, {"FOO": "1"})
        self.assertEqual(c.redirects, ["src/a.py"])
        self.assertEqual(bash.write_targets(c), ["src/a.py"])

    def test_heredoc_body_ignored(self):
        out = cmds("cat > notes.txt <<'EOF'\ngit push --force\nEOF\necho ok")
        self.assertEqual([c.argv[0] for c in out], ["cat", "echo"])
        self.assertEqual(out[0].redirects, ["notes.txt"])

    def test_nested_shell_and_substitution(self):
        out = cmds("bash -c 'git push origin main'")
        self.assertTrue(any(bash.is_push(c) and c.nested for c in out))
        out = cmds("echo $(gh pr create --fill)")
        self.assertTrue(any(bash.is_gh_pr_create(c) for c in out))

    def test_wrappers_stripped(self):
        self.assertEqual(one("env A=1 sudo git push").argv[:2], ["git", "push"])

    def test_unparsable_falls_back_to_text(self):
        with self.assertRaises(bash.BashParseError):
            cmds("echo 'non chiuso")
        self.assertIsNotNone(bash.text_danger("echo 'x; git push --force"))
        self.assertIsNone(bash.text_danger("echo 'ciao"))


class ClassifyTest(unittest.TestCase):
    def test_push(self):
        self.assertTrue(bash.push_is_force(one("git push -f origin tg/1-x")))
        self.assertTrue(bash.push_is_force(one("git push origin +tg/1-x")))
        self.assertEqual(bash.push_targets(one("git push origin HEAD:refs/heads/main")), ["main"])
        self.assertEqual(bash.push_targets(one("git push")), [])

    def test_branch_change(self):
        for text in ["git switch -c altro", "git checkout -B altro", "git branch -m nuovo",
                     "git switch main"]:
            with self.subTest(text=text):
                self.assertIsNotNone(bash.branch_change(one(text)))
        self.assertIsNone(bash.branch_change(one("git checkout -- src/a.py")))
        self.assertEqual(bash.checkout_args(one("git checkout altro")), ["altro"])

    def test_destructive(self):
        self.assertIsNotNone(bash.destructive(one("git reset --hard HEAD~1")))
        self.assertIsNotNone(bash.destructive(one("git commit --no-verify -m x")))
        self.assertEqual(bash.rm_rf_targets(one("rm -rf /tmp/x build")), ["/tmp/x", "/r/wt/build"])
        self.assertEqual(bash.rm_rf_targets(one("rm -r x")), [])

    def test_writes(self):
        self.assertEqual(bash.write_targets(one("sed -i 's/a/b/' src/a.py")), ["src/a.py"])
        self.assertEqual(bash.write_targets(one("cp a.txt dest/b.txt")), ["dest/b.txt"])
        self.assertEqual(bash.write_targets(one("echo x | tee -a out.txt")), ["out.txt"])
        self.assertTrue(bash.writes(one("git add -A")))
        self.assertFalse(bash.writes(one("git status")))

    def test_claude_and_tollgate(self):
        self.assertTrue(bash.is_claude(one("claude -p ciao")))
        self.assertTrue(bash.is_claude(one("npx @anthropic-ai/claude-code -p x")))
        self.assertTrue(bash.is_tollgate_hook(one("/p/bin/tollgate hook PreToolUse")))
        self.assertFalse(bash.is_tollgate_hook(one("/p/bin/tollgate verify")))

    def test_worktree_merge_branch_delete(self):
        self.assertEqual(bash.worktree_op(one("git worktree add ../x -b tg/2-y")),
                         ("add", "/r/x", "tg/2-y"))
        self.assertEqual(bash.worktree_op(one("git worktree remove ../x")), ("remove", "/r/x", None))
        self.assertEqual(bash.merge_args(one("git merge --no-ff tg/1-x")), ["tg/1-x"])
        self.assertEqual(bash.branch_deletes(one("git branch -D tg/1-x")), ["tg/1-x"])


class EffectsTest(unittest.TestCase):
    CFG = bash.EffectsCfg(commands=["make prod*"], project_scripts=["deploy"],
                          allow=["kubectl get *"])

    def eff(self, text):
        return bash.effect_reason(one(text), self.CFG)

    def test_effects(self):
        for text in ["ssh host ls", "docker push img", "terraform apply", "npm publish",
                     "curl -X POST https://x", "curl -d a=1 https://x", "wget --post-data=a https://x",
                     "gh pr edit 3 --title x", "gh api -X PATCH repos/o/r", "gh api repos/o/r -f a=b",
                     "gh api graphql -f query='mutation { x }'", "gh issue create -t x",
                     "npm run deploy", "make production", "supabase db push",
                     "wrangler deploy", "gh release create v1"]:
            with self.subTest(text=text):
                self.assertIsNotNone(self.eff(text))

    def test_not_effects(self):
        for text in ["curl https://x", "gh pr view 3", "gh api repos/o/r",
                     "gh api graphql -f query='query { x }'", "kubectl get pods", "npm test",
                     "git push", "supabase status"]:
            with self.subTest(text=text):
                self.assertIsNone(self.eff(text))

    def test_script_path(self):
        self.assertEqual(bash.script_path(one("./scripts/x.sh a")), "/r/wt/scripts/x.sh")
        self.assertEqual(bash.script_path(one("python3 tools/y.py")), "/r/wt/tools/y.py")
        self.assertIsNone(bash.script_path(one("python3 -m pytest")))
        self.assertIsNone(bash.script_path(one("ls -la")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_bash -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `bash.py`**

```python
"""Lettura dei comandi Bash e classificazione per le regole di 7.4 e gli effetti di 8.5.
Best effort: ciò che sfugge lo prende PostToolUse Bash (spec 7.2)."""
from __future__ import annotations

import fnmatch
import os
import re
import shlex
from dataclasses import dataclass, field


class BashParseError(ValueError):
    pass


@dataclass
class Cmd:
    argv: list[str]
    cwd: str
    env: dict[str, str] = field(default_factory=dict)
    redirects: list[str] = field(default_factory=list)
    nested: bool = False


_OPS = {";", "&&", "||", "|", "&", "|&", ";;", "(", ")"}
_REDIR_OUT = {">", ">>", ">|", "&>", "&>>"}
_REDIR_SKIP = {"<", "<<<", "<&", ">&", "<>"}
_WRAPPERS = {"sudo", "nohup", "time", "command", "exec", "nice", "env", "xargs", "timeout",
             "stdbuf", "builtin"}
_SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_SUBST = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")


def _strip_heredocs(text: str) -> str:
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in _HEREDOC.finditer(line):
            delim = m.group(2)
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1
    return "\n".join(out)


def _norm(cwd: str, path: str) -> str:
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))


def _unwrap(argv: list[str], env: dict) -> list[str]:
    while argv and os.path.basename(argv[0]) in _WRAPPERS:
        argv = argv[1:]
        while argv and (argv[0].startswith("-") or _ASSIGN.match(argv[0])
                        or argv[0].replace(".", "", 1).isdigit()):
            if _ASSIGN.match(argv[0]):
                k, _, v = argv[0].partition("=")
                env[k] = v
            argv = argv[1:]
    return argv


def parse(command: str, cwd: str) -> list[Cmd]:
    text = _strip_heredocs(command.replace("\\\n", " "))
    extra: list[Cmd] = []
    for m in _SUBST.finditer(text):
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        for c in parse(inner, cwd):
            c.nested = True
            extra.append(c)
    lex = shlex.shlex(text.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        tokens = list(lex)
    except ValueError as e:
        raise BashParseError(str(e)) from e
    out: list[Cmd] = []
    seg: list[str] = []

    def flush():
        nonlocal cwd, seg
        if not seg:
            return
        env: dict[str, str] = {}
        redirects: list[str] = []
        argv: list[str] = []
        i = 0
        while i < len(seg):
            t = seg[i]
            if t in _REDIR_OUT or (t[:-1].isdigit() and t[-1:] == ">"):
                if i + 1 < len(seg):
                    redirects.append(seg[i + 1])
                i += 2
                continue
            if t in _REDIR_SKIP or t == "<<":
                i += 2
                continue
            if not argv and _ASSIGN.match(t):
                k, _, v = t.partition("=")
                env[k] = v
            else:
                argv.append(t)
            i += 1
        argv = _unwrap(argv, env)
        seg = []
        if not argv and not redirects:
            return
        cmd = Cmd(argv, cwd, env, redirects)
        out.append(cmd)
        if argv and argv[0] in ("cd", "pushd"):
            cwd = _norm(cwd, argv[1] if len(argv) > 1 else "~")
        elif argv and os.path.basename(argv[0]) in _SHELLS and "-c" in argv:
            k = argv.index("-c")
            if k + 1 < len(argv):
                for c in parse(argv[k + 1], cmd.cwd):
                    c.nested = True
                    out.append(c)
        elif argv and argv[0] == "eval" and len(argv) > 1:
            for c in parse(" ".join(argv[1:]), cmd.cwd):
                c.nested = True
                out.append(c)

    for t in tokens:
        if t in _OPS:
            flush()
        else:
            seg.append(t)
    flush()
    return out + extra


# --- git -------------------------------------------------------------------------------------

_GIT_OPT_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
_GIT_MUTATING = {"add", "commit", "checkout", "switch", "reset", "restore", "rm", "mv", "merge",
                 "rebase", "cherry-pick", "revert", "am", "stash", "apply", "pull", "clean",
                 "tag", "branch", "worktree", "push"}


def git_call(cmd: Cmd):
    a = cmd.argv
    if not a or os.path.basename(a[0]) != "git":
        return None, [], None
    i, c_dir = 1, None
    while i < len(a) and a[i].startswith("-"):
        if a[i] == "-C" and i + 1 < len(a):
            c_dir = a[i + 1]
            i += 2
        elif a[i] in _GIT_OPT_ARG:
            i += 2
        else:
            i += 1
    return (a[i] if i < len(a) else None), a[i + 1:], c_dir


def effective_dir(cmd: Cmd) -> str:
    _, _, c_dir = git_call(cmd)
    return _norm(cmd.cwd, c_dir) if c_dir else cmd.cwd


def _positional(args: list[str]) -> list[str]:
    return [x for x in args if not x.startswith("-")]


def is_push(cmd: Cmd) -> bool:
    return git_call(cmd)[0] == "push"


def push_is_force(cmd: Cmd) -> bool:
    sub, args, _ = git_call(cmd)
    if sub != "push":
        return False
    if any(x in ("-f", "--mirror") or x.startswith("--force") for x in args):
        return True
    return any(x.startswith("+") for x in _positional(args)[1:])


def push_targets(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    if sub != "push":
        return []
    out = []
    for spec in _positional(args)[1:]:
        dst = spec.split(":")[-1].lstrip("+")
        out.append(dst.removeprefix("refs/heads/"))
    return out


def is_commit(cmd: Cmd) -> bool:
    return git_call(cmd)[0] == "commit"


def commit_all(cmd: Cmd) -> bool:
    sub, args, _ = git_call(cmd)
    if sub != "commit":
        return False
    return any(x in ("-a", "--all") or (x.startswith("-") and not x.startswith("--")
                                         and "a" in x[1:]) for x in args)


def is_gh_pr_create(cmd: Cmd) -> bool:
    return cmd.argv[:3] == ["gh", "pr", "create"]


def checkout_args(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    if sub != "checkout" or "--" in args:
        return []
    return _positional(args)


def branch_change(cmd: Cmd) -> str | None:
    sub, args, _ = git_call(cmd)
    if sub == "switch":
        return "git switch"
    if sub == "checkout" and any(x in ("-b", "-B", "--orphan") for x in args):
        return "git checkout -b/-B"
    if sub == "branch" and any(x in ("-m", "-M", "--move") for x in args):
        return "git branch -m/-M"
    return None


def rm_rf_targets(cmd: Cmd) -> list[str]:
    a = cmd.argv
    if not a or os.path.basename(a[0]) != "rm":
        return []
    flags = "".join(x[1:] for x in a[1:] if x.startswith("-") and not x.startswith("--"))
    long = {x for x in a[1:] if x.startswith("--")}
    recursive = "r" in flags or "R" in flags or "--recursive" in long
    force = "f" in flags or "--force" in long
    if not (recursive and force):
        return []
    return [_norm(cmd.cwd, x) for x in _positional(a[1:])]


def destructive(cmd: Cmd) -> str | None:
    sub, args, _ = git_call(cmd)
    if sub == "reset" and "--hard" in args:
        return "git reset --hard"
    if sub is not None and "--no-verify" in args:
        return "--no-verify"
    return None


def write_targets(cmd: Cmd) -> list[str]:
    a = cmd.argv
    out = list(cmd.redirects)
    if not a:
        return out
    base = os.path.basename(a[0])
    pos = _positional(a[1:])
    if base == "tee":
        out += pos
    elif base in ("sed", "perl") and any(x == "-i" or x.startswith("-i") or x == "--in-place"
                                          for x in a[1:]):
        has_e = any(x in ("-e", "--expression") for x in a[1:])
        out += pos if has_e else pos[1:]
    elif base in ("cp", "mv", "install", "ln") and len(pos) >= 2:
        out.append(pos[-1])
    elif base in ("rm", "touch", "mkdir", "rmdir", "truncate", "chmod", "chown"):
        out += pos[1:] if base in ("chmod", "chown") else pos
    elif base == "dd":
        out += [x[3:] for x in a[1:] if x.startswith("of=")]
    return out


def writes(cmd: Cmd) -> bool:
    return bool(write_targets(cmd)) or git_call(cmd)[0] in _GIT_MUTATING


def is_claude(cmd: Cmd) -> bool:
    a = cmd.argv
    if not a:
        return False
    base = os.path.basename(a[0])
    if base in ("claude", "claude-code"):
        return True
    return base in ("npx", "bunx", "pnpx", "pnpm", "yarn", "npm") and any(
        "@anthropic-ai/claude-code" in x for x in a[1:])


def is_tollgate_hook(cmd: Cmd) -> bool:
    a = cmd.argv
    for i, x in enumerate(a[:2]):
        if os.path.basename(x) == "tollgate":
            return len(a) > i + 1 and a[i + 1] == "hook"
    return False


def uses_tollgate_bin(cmd: Cmd, plugin_bin: str) -> bool:
    a = cmd.argv
    target = os.path.realpath(plugin_bin)
    cands = a[:1] + (a[1:2] if a and os.path.basename(a[0]).startswith("python") else [])
    return any(os.path.realpath(_norm(cmd.cwd, x)) == target for x in cands)


def merge_args(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    return _positional(args) if sub == "merge" else []


def worktree_op(cmd: Cmd):
    sub, args, _ = git_call(cmd)
    if sub != "worktree" or not args:
        return None
    op, rest = args[0], args[1:]
    branch = None
    if "-b" in rest or "-B" in rest:
        k = rest.index("-b") if "-b" in rest else rest.index("-B")
        branch = rest[k + 1] if k + 1 < len(rest) else None
        rest = rest[:k] + rest[k + 2:]
    pos = _positional(rest)
    if op == "add" and pos:
        return ("add", _norm(cmd.cwd, pos[0]), branch or (pos[1] if len(pos) > 1 else None))
    if op == "remove" and pos:
        return ("remove", _norm(cmd.cwd, pos[0]), None)
    return None


def branch_deletes(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    if sub != "branch" or not any(x in ("-d", "-D", "--delete") for x in args):
        return []
    return _positional(args)


# --- effetti esterni (8.5) --------------------------------------------------------------------

@dataclass(frozen=True)
class EffectsCfg:
    commands: tuple | list = ()
    project_scripts: tuple | list = ()
    allow: tuple | list = ()


_DEFAULT_EFFECTS = [("ssh",), ("scp",), ("rsync",), ("psql",), ("docker", "push"),
                    ("kubectl",), ("terraform", "apply"), ("aws",), ("gcloud",), ("az",),
                    ("vercel",), ("netlify",), ("firebase", "deploy"), ("wrangler", "deploy"),
                    ("wrangler", "publish"), ("npm", "publish"), ("pnpm", "publish"),
                    ("yarn", "publish")]
_SUPABASE_WRITE = {"db", "functions", "secrets", "link", "migration", "storage", "projects",
                   "orgs", "branches"}
_SUPABASE_READ = {"list", "diff", "dump", "ls", "download", "--help", "-h"}
_GH_WRITE = {("pr", "create"), ("pr", "edit"), ("pr", "review"), ("pr", "close"),
             ("pr", "merge"), ("workflow", "run"), ("issue", "edit"), ("issue", "close"),
             ("issue", "create")}
_GH_WRITE_ANY = {"release", "secret", "project"}
_INTERPRETERS = {"bash", "sh", "zsh", "python", "python3", "node", "ruby", "perl", "deno",
                 "bun", "tsx", "ts-node", "php"}


def normalized(cmd: Cmd) -> str:
    return " ".join(cmd.argv)


def _matches(patterns, text: str) -> bool:
    return any(text == p or text.startswith(p + " ") or fnmatch.fnmatchcase(text, p)
               for p in patterns)


def _curl_write(a: list[str]) -> bool:
    for i, x in enumerate(a):
        if x in ("-X", "--request") and i + 1 < len(a) and a[i + 1].upper() != "GET":
            return True
        if x.startswith("-X") and len(x) > 2 and x[2:].upper() != "GET":
            return True
        if x in ("-d", "-F", "-T", "--json", "--form", "--upload-file") or \
                x.startswith(("--data", "--form", "-d")):
            return True
    return False


def _wget_write(a: list[str]) -> bool:
    for x in a:
        if x.startswith(("--post-data", "--post-file", "--body-data", "--body-file")):
            return True
        if x.startswith("--method") and x.split("=", 1)[-1].upper() != "GET":
            return True
    return False


def _gh_write(a: list[str]) -> bool:
    if len(a) < 2:
        return False
    if a[1] in _GH_WRITE_ANY:
        return True
    if len(a) >= 3 and (a[1], a[2]) in _GH_WRITE:
        return True
    if a[1] == "api":
        rest = a[2:]
        for i, x in enumerate(rest):
            if x in ("-X", "--method") and i + 1 < len(rest) and rest[i + 1].upper() != "GET":
                return True
            if x.startswith("--method=") and x.split("=", 1)[1].upper() != "GET":
                return True
        graphql = "graphql" in rest
        fields = [rest[i + 1] for i, x in enumerate(rest[:-1])
                  if x in ("-f", "-F", "--field", "--raw-field")]
        if graphql:
            return any(re.search(r"\bmutation\b", f) for f in fields) or "--input" in rest
        return bool(fields) or "--input" in rest
    return False


def effect_reason(cmd: Cmd, cfg: EffectsCfg) -> str | None:
    a = cmd.argv
    if not a:
        return None
    text = normalized(cmd)
    if _matches(cfg.allow, text):
        return None
    if _matches(cfg.commands, text):
        return "comando dichiarato in [external_effects] commands"
    base = os.path.basename(a[0])
    for prefix in _DEFAULT_EFFECTS:
        if [base] + a[1:len(prefix)] == list(prefix):
            return f"effetto esterno: {' '.join(prefix)}"
    if base == "supabase" and len(a) > 1 and a[1] in _SUPABASE_WRITE \
            and not (len(a) > 2 and a[2] in _SUPABASE_READ):
        return "effetto esterno: supabase in scrittura"
    if base in ("npm", "pnpm", "yarn", "bun") and len(a) > 1:
        script = a[2] if a[1] == "run" and len(a) > 2 else a[1]
        if script in cfg.project_scripts:
            return f"script del progetto: {script}"
    if base in ("make", "just") and any(x in cfg.project_scripts for x in a[1:]):
        return "script del progetto"
    if base == "curl" and _curl_write(a[1:]):
        return "curl con metodo diverso da GET o con dati"
    if base == "wget" and _wget_write(a[1:]):
        return "wget con metodo diverso da GET o con dati"
    if base == "gh" and _gh_write(a):
        return "gh in scrittura"
    return None


def script_path(cmd: Cmd) -> str | None:
    a = cmd.argv
    if not a:
        return None
    if "/" in a[0] and os.path.basename(a[0]) not in _INTERPRETERS:
        return _norm(cmd.cwd, a[0])
    if os.path.basename(a[0]) in _INTERPRETERS:
        rest = a[1:]
        if any(x in ("-c", "-m", "-e") for x in rest[:1]):
            return None
        pos = [x for x in rest if not x.startswith("-")]
        if pos and ("/" in pos[0] or re.search(r"\.(sh|py|js|mjs|ts|rb|pl|php)$", pos[0])):
            return _norm(cmd.cwd, pos[0])
    return None


_TEXT_DANGER = [
    (re.compile(r"\bgit\b[^;&|]*\bpush\b"), "git push"),
    (re.compile(r"--force\b"), "--force"),
    (re.compile(r"\breset\s+--hard\b"), "reset --hard"),
    (re.compile(r"--no-verify\b"), "--no-verify"),
    (re.compile(r"TOLLGATE_"), "TOLLGATE_"),
    (re.compile(r"(^|[\s;&|(])claude(\s|$)"), "claude"),
]


def text_danger(raw: str) -> str | None:
    """Ripiego per i comandi che shlex non legge: si cerca per testo."""
    for rx, label in _TEXT_DANGER:
        if rx.search(raw):
            return label
    return None
```

- [ ] **Step 4: Verificare che passi**

Run: `python3 -B -m unittest tests.test_bash -v`
Expected: PASS. Se un caso fallisce, correggere `bash.py` (non il test) e registrare nel ledger un caso che si è deciso di non coprire solo con una `Ruling:`.

- [ ] **Step 5: Suite e commit**

Run: `tests/run`
Expected: OK.

```bash
git add bin/tollgate_analysis/bash.py tests/test_bash.py
git commit -m "tollgate P2: lettura e classificazione dei comandi Bash"
```

---

