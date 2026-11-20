"""PROTOTIPO delle decisioni 1-3 scritto alla lettera dal piano, innestato su bash in-process (fuori dal repo)."""
import os, re, shlex, sys
sys.dont_write_bytecode = True
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, os.path.join(WT, "bin"))
from tollgate_analysis import bash
from tollgate_analysis.bash import Cmd, BashParseError

ENV_LOADERS = ("dotenv", "dotenvx", "cross-env", "env-cmd", "doppler", "infisical", "op")
LOADER_PACKAGES = {"dotenv-cli": "dotenv", "@dotenvx/dotenvx": "dotenvx", "@infisical/cli": "infisical"}
CMD_OPTIONS = ("--command", "--cmd")
bash.ENV_LOADERS, bash.LOADER_PACKAGES = ENV_LOADERS, LOADER_PACKAGES

# ---- decisione 3
def launcher_candidates(argv):
    if not argv or os.path.basename(argv[0]) not in bash.LAUNCHERS:
        return []
    programs = {p[0] for p in bash._DEFAULT_EFFECTS} | {"supabase"}
    out = []; manager_seen = package_command_seen = False
    for i, tok in enumerate(argv):
        norm = bash._launcher_token(os.path.basename(tok) if i == 0 else tok)
        if i >= 1 and not package_command_seen and norm in programs:
            rest = argv[i + 1:]
            while rest[:1] == ["--"]:
                rest = rest[1:]
            out.append([norm] + rest)
        if manager_seen and tok in bash.PACKAGE_COMMANDS:
            package_command_seen = True
        if norm in bash._PACKAGE_MANAGERS:
            manager_seen = True
    return out
bash.launcher_candidates = launcher_candidates

# ---- decisione 1
def _path_ok(tok, for_effect=True):
    if "/" not in tok:
        return True
    if tok.startswith("/") or "/bin/" in tok or tok.startswith(("bin/", ".bin/")) or "/.bin/" in tok:
        return True
    if tok.endswith((".sh", ".bash")):
        return True
    if tok.startswith(("./", "../")) and "." not in os.path.basename(tok):
        return not for_effect          # solo a _script_reason
    return False

def _cand(words, cwd):
    try:
        return bash.parse(shlex.join(words), cwd)
    except BashParseError:
        return shlex.join(words)

def inner_commands(cmd):
    if os.path.basename(cmd.argv[0]) not in ENV_LOADERS:
        return []
    words = cmd.argv[1:]
    out = []
    if "--" in words:
        i = words.index("--"); prefix, after = words[:i], words[i + 1:]
    else:
        prefix, after = words, []
    if after:
        out.append(after)
    for j, tok in enumerate(prefix):
        if tok.startswith("-") or bash._ASSIGN.match(tok) or not _path_ok(tok):
            continue
        out.append(words[j:])
    for j, tok in enumerate(prefix):
        val = None
        if tok in CMD_OPTIONS and j + 1 < len(prefix):
            val = prefix[j + 1]
        elif tok.split("=", 1)[0] in CMD_OPTIONS and "=" in tok:
            val = tok.split("=", 1)[1]
        if val is not None:
            try:
                out.append(("parse", bash.parse(val, cmd.cwd)))
            except BashParseError:
                out.append(("text", val))
    res = []
    for w in out:
        if isinstance(w, tuple):
            if w[0] == "parse": res.extend(w[1])
            else: res.append(w[1])
        else:
            c = _cand(w, cmd.cwd)
            res.extend(c) if isinstance(c, list) else res.append(c)
    return res
bash.inner_commands = inner_commands

_orig_effect = bash.effect_reason
_depth = [0]

def effect_reason(cmd, cfg):
    a = cmd.argv
    if not a:
        return None
    text = bash.normalized(cmd)
    if bash._matches(cfg.allow, text):
        return None
    base = os.path.basename(a[0])
    if base in ENV_LOADERS:
        if _depth[0] >= 3:
            return "effetto esterno: involucro annidato"
        _depth[0] += 1
        try:
            for c in inner_commands(cmd):
                r = effect_reason(c, cfg) if isinstance(c, Cmd) else bash.text_effect(c)
                if r:
                    return r
        finally:
            _depth[0] -= 1
    if base in bash.LAUNCHERS:
        mseen = pseen = False
        for i, tok in enumerate(a):
            norm = bash._launcher_token(os.path.basename(tok) if i == 0 else tok)
            norm = LOADER_PACKAGES.get(norm, norm)
            if i >= 1 and not pseen and norm in ENV_LOADERS:
                r = effect_reason(Cmd([norm] + a[i + 1:], cmd.cwd, cmd.env, cmd.redirects), cfg)
                if r:
                    return r
            if mseen and tok in bash.PACKAGE_COMMANDS:
                pseen = True
            if norm in bash._PACKAGE_MANAGERS:
                mseen = True
    return _orig_effect(cmd, cfg)
bash.effect_reason = effect_reason

# ---- decisione 2
bash.SUPABASE_COMMAND_VALUE_OPTIONS = {
    ("db", "push"): ("-p", "--password"), ("db", "pull"): ("-p", "--password", "-s", "--schema"),
    ("db", "reset"): ("--version", "--last"), ("migration", "down"): ("--last",),
    ("migration", "repair"): ("--status",)}

def _supabase_option_tokens(prefix, rest):
    own = bash.SUPABASE_COMMAND_VALUE_OPTIONS.get(tuple(prefix[1:3]), ())
    out = []; i = 0
    while i < len(rest):
        t = rest[i]
        if t == "--":
            return out + rest[i:]
        if t in bash.SUPABASE_VALUE_OPTIONS or t in own:
            i += 2
        elif "=" in t and t.split("=", 1)[0] in (*bash.SUPABASE_VALUE_OPTIONS, *own):
            i += 1
        else:
            out.append(t); i += 1
    return out

def _present(tokens, name):
    for tok in tokens:
        if tok == "--":
            return False
        if tok == name:
            return True
        if tok.startswith(name + "="):
            return name != "--local" or tok[len(name) + 1:] in bash._SUPABASE_TRUE
    return False

def _supabase_reason(argv):
    words = bash._supabase_args(argv)
    # aiuto senza sottocomando (supabase --help/-h/--version)
    toks = bash._strip_value_options(argv[1:])
    entry = None
    if words is not None:
        w = bash._strip_value_options(words)
        entry = next((p for p, m in bash.FLAG_EFFECTS if p[0] == "supabase" and ["supabase"] + w[:len(p) - 1] == list(p)), None)
        if entry:
            rest = w[len(entry) - 1:]
            opt = _supabase_option_tokens(entry, rest)
            for t in opt:
                if t == "--":
                    break
                if t in ("--help", "-h"):
                    return None
            mode = dict(bash.FLAG_EFFECTS)[entry]
            remote = bash.REMOTE_FLAGS["supabase"]
            label = " ".join(entry)
            if mode == "unless_local":
                local = _present(opt, "--local") and not any(_present(opt, f) for f in remote)
                return None if local else f"effetto esterno: {label} (senza --local)"
            for f in remote:
                if _present(opt, f):
                    return f"effetto esterno: {label} con {f}"
            return None
    return _orig_supabase(argv)
_orig_supabase = bash._supabase_reason
bash._supabase_reason = _supabase_reason
bash._supabase_option_tokens = _supabase_option_tokens
