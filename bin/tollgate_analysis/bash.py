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
_OPS_RE = re.compile(r"&&|\|\||\|&|;;|[;&|()]")
_REDIR_OUT = {">", ">>", ">|", "&>", "&>>"}
_REDIR_SKIP = {"<", "<<<", "<&", ">&", "<>"}
_KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "{", "!", "time"}
_WRAPPERS = {"sudo", "nohup", "time", "command", "exec", "nice", "env", "xargs", "timeout",
             "stdbuf", "builtin"}
# Opzioni che prendono un argomento separato, per ciascun wrapper (`sudo -u bob git ...`).
_WRAP_ARGS = {
    "sudo": {"-u", "-g", "-C", "-h", "-p", "-r", "-t", "-U", "-T", "--user", "--group",
             "--chdir", "--host", "--prompt", "--role", "--type", "--other-user"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "nice": {"-n", "--adjustment"},
    "timeout": {"-k", "-s", "--kill-after", "--signal"},
    "xargs": {"-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a", "--max-args", "--max-procs",
              "--delimiter", "--arg-file", "--max-lines"},
    "stdbuf": {"-i", "-o", "-e"},
    "time": {"-f", "-o"},
    "exec": {"-a"},
}
_SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# `<<` di heredoc, non `<<<` (here-string).
_HEREDOC_AT = re.compile(r"(?<!<)<<(?!<)-?[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_SHELL_LINE = re.compile(r"(?:^|[\s;&|(])(?:bash|sh|zsh|dash|ksh)(?=[\s;&|)]|$)")


def _skip_heredoc_bodies(text: str, start: int, delims: list[str]) -> int:
    """Indice dopo le righe di corpo di ogni heredoc in attesa, a partire da `start`."""
    i = start
    for delim in delims:
        while True:
            nl = text.find("\n", i)
            end = nl if nl >= 0 else len(text)
            line = text[i:end]
            i = end + 1
            if line.strip() == delim:
                break
            if nl < 0:
                raise BashParseError(f"heredoc senza delimitatore '{delim}'")
    return i


def _balanced(text: str, i: int) -> tuple[str, int]:
    """Contenuto di `$(` che inizia prima di `i`, e indice dopo la `)` di chiusura.
    Salta virgolette e corpi di heredoc, così le parentesi dentro di loro non contano."""
    depth, pending, n, start = 1, [], len(text), i
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            j = text.find("'", i + 1)
            if j < 0:
                raise BashParseError("virgolette non chiuse")
            i = j + 1
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise BashParseError("virgolette non chiuse")
            i = j + 1
            continue
        if c == "<" and not text.startswith("<<<", i):
            m = _HEREDOC_AT.match(text, i)
            if m:
                pending.append(m.group(2))
                i = m.end()
                continue
        if c == "\n":
            i = _skip_heredoc_bodies(text, i + 1, pending) if pending else i + 1
            pending = []
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    raise BashParseError("sostituzione $(...) non chiusa")


def _split(text: str) -> tuple[str, list[str]]:
    """Testo esterno (con `$(...)` sostituito da SUBST e corpi di heredoc tolti) e
    contenuti delle sostituzioni, da analizzare a parte."""
    out: list[str] = []
    inners: list[str] = []
    pending: list[str] = []
    in_dq = False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            out.append(text[i:i + 2])
            i += 2
            continue
        if c == "'" and not in_dq:
            j = text.find("'", i + 1)
            if j < 0:
                raise BashParseError("virgolette non chiuse")
            out.append(text[i:j + 1])
            i = j + 1
            continue
        if c == '"':
            in_dq = not in_dq
            out.append(c)
            i += 1
            continue
        if c == "`":
            j = text.find("`", i + 1)
            if j < 0:
                raise BashParseError("backtick non chiuso")
            inners.append(text[i + 1:j])
            out.append(" SUBST ")
            i = j + 1
            continue
        if text.startswith("$(", i):
            inner, end = _balanced(text, i + 2)
            inners.append(inner)
            out.append(" SUBST ")
            i = end
            continue
        if c == "<" and not in_dq and not text.startswith("<<<", i):
            m = _HEREDOC_AT.match(text, i)
            if m:
                line_start = text.rfind("\n", 0, i) + 1
                line_end = text.find("\n", i)
                line = text[line_start:line_end if line_end >= 0 else n]
                if _SHELL_LINE.search(line):
                    raise BashParseError("heredoc verso una shell: il corpo non si legge")
                pending.append(m.group(2))
                out.append(m.group(0))
                i = m.end()
                continue
        if c == "\n":
            out.append("\n")
            i = _skip_heredoc_bodies(text, i + 1, pending) if pending else i + 1
            pending = []
            continue
        out.append(c)
        i += 1
    if in_dq:
        raise BashParseError("virgolette non chiuse")
    return "".join(out), inners


def _norm(cwd: str, path: str) -> str:
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))


def _unwrap(argv: list[str], env: dict) -> list[str]:
    while argv and os.path.basename(argv[0]) in _WRAPPERS:
        name = os.path.basename(argv[0])
        takes = _WRAP_ARGS.get(name, set())
        argv = argv[1:]
        while argv:
            x = argv[0]
            if x == "--":
                argv = argv[1:]
                break
            if _ASSIGN.match(x):
                k, _, v = x.partition("=")
                env[k] = v
                argv = argv[1:]
                continue
            if x.startswith("-") and len(x) > 1:
                argv = argv[1:]
                if x in takes and argv:
                    argv = argv[1:]
                continue
            if name == "timeout" and x.replace(".", "", 1).isdigit():
                argv = argv[1:]
                continue
            break
    return argv


def _shell_command(argv: list[str]) -> str | None:
    """Stringa passata a `-c` di una shell, anche nei flag combinati (`bash -lc`, `sh -ec`).
    None se la shell esegue uno script o legge da stdin."""
    i = 1
    while i < len(argv):
        x = argv[i]
        if x == "--" or not x.startswith(("-", "+")) or x.startswith("--"):
            return None
        if x in ("-o", "+o"):
            i += 2
            continue
        if x.startswith("-") and "c" in x[1:]:
            return argv[i + 1] if i + 1 < len(argv) else None
        i += 1
    return None


def _ops(tokens):
    """shlex fonde la punteggiatura (`);`, `)&&`, `&&(`): la spezza negli operatori noti.
    I token con redirezioni (`>&`, `&>`) restano interi."""
    for t in tokens:
        if t and set(t) <= set(";&|()<>") and not any(ch in "<>" for ch in t):
            yield from _OPS_RE.findall(t)
        else:
            yield t


def parse(command: str, cwd: str) -> list[Cmd]:
    outer, inners = _split(command.replace("\\\n", " "))
    extra: list[Cmd] = []
    for inner in inners:
        for c in parse(inner, cwd):
            c.nested = True
            extra.append(c)
    lex = shlex.shlex(outer.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        tokens = list(_ops(lex))
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
            # Descrittore numerato (`2>&1`, `1>x`): shlex lo lascia come parola a sé.
            if t.isdigit() and i + 1 < len(seg) and seg[i + 1][:1] in ("<", ">"):
                i += 1
                continue
            if t in _REDIR_OUT:
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
        while argv and argv[0] in _KEYWORDS:
            argv = argv[1:]
        argv = _unwrap(argv, env)
        seg = []
        if not argv and not redirects:
            return
        cmd = Cmd(argv, cwd, env, redirects)
        out.append(cmd)
        if argv and argv[0] in ("cd", "pushd"):
            cwd = _norm(cwd, argv[1] if len(argv) > 1 else "~")
        elif argv and os.path.basename(argv[0]) in _SHELLS:
            inner = _shell_command(argv)
            if inner is not None:
                for c in parse(inner, cmd.cwd):
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

_GIT_OPT_ARG = {"-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
_GIT_MUTATING = {"add", "commit", "checkout", "switch", "reset", "restore", "rm", "mv", "merge",
                 "rebase", "cherry-pick", "revert", "am", "stash", "apply", "pull", "clean",
                 "tag", "branch", "worktree", "push", "update-ref", "remote", "filter-branch",
                 "symbolic-ref", "submodule", "gc"}
_CONFIG_WRITE = {"--unset", "--unset-all", "--add", "--replace-all", "--rename-section",
                 "--remove-section"}
_CONFIG_READ = {"--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "-l",
                "--show-origin", "--show-scope", "--name-only"}


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


def _is_mutating(sub: str | None, args: list[str]) -> bool:
    if sub == "config":
        if any(x in _CONFIG_WRITE for x in args):
            return True
        if any(x in _CONFIG_READ for x in args):
            return False
        return len(_positional(args)) >= 2  # `git config chiave valore`
    return sub in _GIT_MUTATING


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
    if any(x == "--mirror" or x.startswith("--force") for x in args):
        return True
    # `-f` anche nei gruppi corti (`-fu`, `-uf`).
    if any(x.startswith("-") and not x.startswith("--") and "f" in x[1:] for x in args):
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
    # `git commit -n` è l'alias di --no-verify, anche nei gruppi di opzioni corti (`-nm`).
    if sub == "commit" and any(x == "-n" or (x.startswith("-") and not x.startswith("--")
                                              and "n" in x[1:]) for x in args):
        return "--no-verify"
    return None


def _inplace(args: list[str]) -> bool:
    return any(x == "--in-place" or x.startswith("--in-place=")
               or (x.startswith("-") and not x.startswith("--") and "i" in x[1:])
               for x in args)


def _inplace_files(args: list[str]) -> list[str]:
    """File modificati da sed/perl -i: le posizionali, senza il programma se non è dato con -e/-f."""
    files: list[str] = []
    code = False
    i = 0
    while i < len(args):
        x = args[i]
        if x in ("-e", "--expression", "-f", "--file"):
            code = True
            i += 2
            continue
        if x.startswith(("--expression=", "--file=")):
            code = True
            i += 1
            continue
        if x.startswith("-") and x != "-":
            i += 1
            continue
        files.append(x)
        i += 1
    if not code and files:
        files = files[1:]
    return files


def _target_dir(args: list[str]) -> str | None:
    """Directory di `cp/mv/install -t dir` (anche `-tdir` e `--target-directory=dir`)."""
    for i, x in enumerate(args):
        if x in ("-t", "--target-directory") and i + 1 < len(args):
            return args[i + 1]
        if x.startswith("--target-directory="):
            return x.split("=", 1)[1]
        if x.startswith("-t") and not x.startswith("--") and len(x) > 2:
            return x[2:]
    return None


def write_targets(cmd: Cmd) -> list[str]:
    a = cmd.argv
    out = list(cmd.redirects)
    if not a:
        return out
    base = os.path.basename(a[0])
    args = a[1:]
    pos = _positional(args)
    if base == "tee":
        out += pos
    elif base in ("sed", "perl") and _inplace(args):
        out += _inplace_files(args)
    elif base in ("cp", "mv", "install", "ln"):
        target = _target_dir(args)
        if target is not None:
            out.append(target)
        elif len(pos) >= 2:
            out.append(pos[-1])
    elif base in ("rm", "touch", "mkdir", "rmdir", "truncate"):
        out += pos
    elif base in ("chmod", "chown"):
        out += pos[1:]
    elif base == "dd":
        out += [x[3:] for x in args if x.startswith("of=")]
    return out


def writes(cmd: Cmd) -> bool:
    sub, args, _ = git_call(cmd)
    return bool(write_targets(cmd)) or _is_mutating(sub, args)


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
_GH_GLOBAL_ARG = {"-R", "--repo", "--hostname"}


def normalized(cmd: Cmd) -> str:
    return " ".join(cmd.argv)


def _matches(patterns, text: str) -> bool:
    # Per i comandi `*` attraversa `/` (fnmatch), come da decisione del controller.
    return any(text == p or text.startswith(p + " ") or fnmatch.fnmatchcase(text, p)
               for p in patterns)


def _curl_write(a: list[str]) -> bool:
    for i, x in enumerate(a):
        if x in ("-X", "--request") and i + 1 < len(a) and a[i + 1].upper() != "GET":
            return True
        if x.startswith("-X") and len(x) > 2 and x[2:].upper() != "GET":
            return True
        if x.startswith("--request=") and x.split("=", 1)[1].upper() != "GET":
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


def _gh_args(a: list[str]) -> list[str]:
    """`gh` senza i flag globali (`-R o/r`, `--repo=o/r`) che precedono o seguono il sottocomando."""
    out: list[str] = []
    i = 1
    while i < len(a):
        x = a[i]
        if x in _GH_GLOBAL_ARG:
            i += 2
            continue
        if x.startswith(("--repo=", "--hostname=")) or (
                x.startswith("-R") and len(x) > 2 and not x.startswith("--")):
            i += 1
            continue
        out.append(x)
        i += 1
    return ["gh"] + out


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
            if x.startswith("-X") and len(x) > 2 and x[2:].upper() != "GET":
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
    if base == "gh" and _gh_write(_gh_args(a)):
        return "gh in scrittura"
    return None


_INTERPRETERS = {"bash", "sh", "zsh", "python", "python3", "node", "ruby", "perl", "deno",
                 "bun", "tsx", "ts-node", "php"}


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
    (re.compile(r"\breset\b[^;&|]*--hard\b"), "reset --hard"),
    (re.compile(r"--no-verify\b"), "--no-verify"),
    (re.compile(r"\bcommit\b[^;&|]*\s-[a-zA-Z]*n[a-zA-Z]*\b"), "--no-verify"),
    (re.compile(r"TOLLGATE_"), "TOLLGATE_"),
    (re.compile(r"(^|[\s;&|(])claude(\s|$)"), "claude"),
]


def text_danger(raw: str) -> str | None:
    """Ripiego per i comandi che shlex non legge: si cerca per testo."""
    for rx, label in _TEXT_DANGER:
        if rx.search(raw):
            return label
    return None
