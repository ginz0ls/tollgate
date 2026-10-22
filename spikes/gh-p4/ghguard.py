#!/usr/bin/env python3
"""Lista degli ammessi per i comandi gh di run-p4-checks.sh (decisione 25): unica fonte.

  ghguard.py check -- <argomenti di gh...>   exit 0 se ammesso, 1 con il motivo su stderr
  ghguard.py log <registro>                  registro del gh finto (argomenti separati da tab)
  ghguard.py comandi <comandi.log>           registro delle uscite (`<ora> gh <argomenti>`), righe «(controller...)» escluse

Un comando è ammesso solo se la coppia (comando, sottocomando) è nella tabella, ogni opzione è nell'elenco
di quella coppia con un valore del tipo previsto, i posizionali sono numeri (PR, issue, run) o nomi di ramo
semplici, esattamente un --repo/-R vale uno dei due repo. `-D` e la cartella di `repo clone` devono stare
sotto le cartelle dell'ambiente (P4_OUT: uscite; P4_WORK: cloni). `gh api` è solo in lettura.

Le scritture `gh api` della decisione 25 sono tre forme esatte, con endpoint fisso, mai un'apertura di
-X/-f/-F (vedi `_check_api_write`): POST statuses di `tollgate/verdict` (prova del token personale),
PUT e DELETE di branches/main/protection solo su protected.

Il profilo `flow` (P4_PROFILE=flow, gh del `claude -p` di run-p4-flow.sh) è lo stesso elenco meno
`issue create`, `pr merge`, `pr close`, `run download` e ogni scrittura `gh api`.
"""
import os
import re
import sys

OWNER = "ginz0ls"
PROT = OWNER + "/tollgate-p4-protected"
DET = OWNER + "/tollgate-p4-detect"
REPOS = (PROT, DET)

REPO_CREATE_OPTS = {"--public", "--private", "--add-readme"}
API_FLAGS = {"--include", "--paginate", "--silent"}
API_VALUED = {"--jq", "-q"}

BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
FIELDS_RE = re.compile(r"^[A-Za-z][A-Za-z,]*$")
NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
STATES = {"open", "closed", "merged", "all"}
PROFILES = ("script", "flow")
FLOW_FORBIDDEN = {("issue", "create"), ("pr", "merge"), ("pr", "close"), ("run", "download")}
# scritture `gh api` ammesse (decisione 25): descrizione senza spazi, che `comandi.log` non conserva
STATUS_DESCRIPTION = "prova-token-personale-p4"
STATUS_CONTEXT = "tollgate/verdict"
STATUS_STATES = {"success", "failure", "error", "pending"}
PROTECTION_ENDPOINT = "repos/%s/branches/main/protection"


def _ok_branch(v):
    return bool(BRANCH_RE.match(v)) and not v.startswith("-") and ".." not in v


def _under(var, v):
    base = os.environ.get(var, "")
    if not base or not os.path.isabs(v):
        return False
    base = os.path.normpath(base)
    return os.path.normpath(v) == v and v.startswith(base + os.sep)


def _temp_roots():
    """Cartelle dei file temporanei dei programmi che chiamano gh (mktemp di protect.sh, file del corpo di
    tollgate): /tmp e $TMPDIR, mai altrove."""
    roots = {"/tmp"}
    if os.environ.get("TMPDIR"):
        roots.add(os.path.normpath(os.environ["TMPDIR"]))
    return roots


def _infile(v):
    """File di ingresso letto da gh (--body-file, --input): percorso assoluto normalizzato sotto le cartelle
    dell'ambiente (P4_OUT, P4_WORK, P4_TMP) o sotto i file temporanei."""
    if _under("P4_OUT", v) or _under("P4_WORK", v) or _under("P4_TMP", v):
        return True
    return os.path.isabs(v) and os.path.normpath(v) == v and any(v.startswith(r + os.sep) for r in _temp_roots())


# tipo di valore -> funzione di controllo
KINDS = {
    "repo": lambda v: v in REPOS,
    "int": lambda v: v.isdigit(),
    "branch": _ok_branch,
    "text": lambda v: True,
    "fields": lambda v: bool(FIELDS_RE.match(v)),
    "state": lambda v: v in STATES,
    "name": lambda v: bool(NAME_RE.match(v)) and ".." not in v,
    "outdir": lambda v: _under("P4_OUT", v),
    "infile": _infile,
}
LENIENT_KINDS = {"text", "outdir", "infile"}   # nel formato di comandi.log gli spazi dei valori sono andati persi

REPO_OPTS = {"--repo": "repo", "-R": "repo"}


def _spec(valued, flags=(), pos=None, exactly_one_of=()):
    return {"valued": dict(REPO_OPTS, **valued), "flags": set(flags), "pos": pos, "one_of": set(exactly_one_of)}


SPECS = {
    ("pr", "create"): _spec({"--base": "branch", "--head": "branch", "--title": "text", "--body": "text",
                             "--body-file": "infile"}),
    ("pr", "edit"): _spec({"--base": "branch", "--title": "text", "--body": "text", "--body-file": "infile"},
                          pos="ref"),
    ("pr", "close"): _spec({}, pos="ref"),
    ("pr", "merge"): _spec({}, flags=("--merge", "--squash", "--rebase"), pos="ref",
                           exactly_one_of=("--merge", "--squash", "--rebase")),
    ("pr", "view"): _spec({"--json": "fields"}, pos="ref"),
    ("pr", "list"): _spec({"--state": "state", "--limit": "int", "--json": "fields", "--head": "branch"}),
    ("pr", "comment"): _spec({"--body": "text", "--body-file": "infile"}, pos="ref"),
    ("issue", "create"): _spec({"--title": "text", "--body": "text", "--body-file": "infile"}),
    ("issue", "close"): _spec({}, pos="int"),
    ("issue", "comment"): _spec({"--body": "text", "--body-file": "infile"}, pos="int"),
    ("issue", "view"): _spec({"--json": "fields"}, pos="int"),
    ("issue", "list"): _spec({"--state": "state", "--limit": "int", "--json": "fields"}),
    ("run", "list"): _spec({"--workflow": "name", "--limit": "int", "--json": "fields"}),
    ("run", "view"): _spec({"--json": "fields"}, flags=("--log", "--log-failed"), pos="int"),
    ("run", "watch"): _spec({}, flags=("--exit-status",), pos="int"),
    ("run", "download"): _spec({"-D": "outdir", "--dir": "outdir", "-n": "name", "--name": "name"}, pos="int"),
}


def _parse(cmd, args, lenient):
    """Controlla opzioni e posizionali di (comando, sottocomando); ValueError con il motivo."""
    spec = SPECS[cmd]
    valued, flags = spec["valued"], spec["flags"]
    repos, positionals, seen_flags = [], [], []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if name in flags:
                if eq:
                    raise ValueError("%s non vuole un valore" % name)
                seen_flags.append(name)
                i += 1
                continue
            if name not in valued:
                raise ValueError("opzione non ammessa: %s" % name)
            if eq:
                value, i = val, i + 1
            else:
                if i + 1 >= len(args):
                    raise ValueError("%s senza valore" % name)
                value, i = args[i + 1], i + 2
                if lenient and valued[name] in LENIENT_KINDS:
                    while i < len(args) and not args[i].startswith("-"):
                        value, i = value + " " + args[i], i + 1
        elif a.startswith("-") and len(a) > 1:
            name = a[:2]
            if name in valued:
                if len(a) > 2:
                    value, i = a[2:], i + 1   # valore attaccato: -Rvalore, -Dcartella
                else:
                    if i + 1 >= len(args):
                        raise ValueError("%s senza valore" % name)
                    value, i = args[i + 1], i + 2
                    if lenient and valued[name] in LENIENT_KINDS:
                        while i < len(args) and not args[i].startswith("-"):
                            value, i = value + " " + args[i], i + 1
            else:
                raise ValueError("opzione non ammessa: %s" % a)
        else:
            positionals.append(a)
            i += 1
            continue
        if not KINDS[valued[name]](value):
            raise ValueError("valore non ammesso per %s: %s" % (name, value))
        if valued[name] == "repo":
            repos.append(value)
    if len(repos) != 1:
        raise ValueError("serve esattamente un --repo/-R (trovati %d)" % len(repos))
    want = spec["pos"]
    if want is None and positionals:
        raise ValueError("argomenti posizionali non ammessi: %s" % " ".join(positionals))
    if want is not None:
        if len(positionals) != 1:
            raise ValueError("serve un solo argomento posizionale (trovati %d)" % len(positionals))
        p = positionals[0]
        if want == "int" and not p.isdigit():
            raise ValueError("serve un numero: %s" % p)
        if want == "ref" and not (p.isdigit() or _ok_branch(p)):
            raise ValueError("serve un numero o un nome di ramo semplice: %s" % p)
    if spec["one_of"] and len([f for f in seen_flags if f in spec["one_of"]]) != 1:
        raise ValueError("serve esattamente una tra %s" % ", ".join(sorted(spec["one_of"])))
    if len(seen_flags) != len(set(seen_flags)):
        raise ValueError("opzione ripetuta")


def _check_endpoint(ep):
    m = re.match(r"^repos/([^/?]+)/([^/?]+)", ep)
    if not m or "%s/%s" % (m[1], m[2]) not in REPOS:
        raise ValueError("endpoint non ammesso: %s" % ep)
    if not re.match(r"^[A-Za-z0-9._~/?&=%:,@+-]+$", ep):
        raise ValueError("endpoint con caratteri non ammessi: %s" % ep)
    if re.search(r"%2e|%2f|%5c|%00", ep, re.IGNORECASE) or ".." in ep or "//" in ep:
        raise ValueError("endpoint con '..', '//' o codifiche sospette: %s" % ep)
    if any(seg == "." for seg in re.split(r"[/?&=]", ep)):
        raise ValueError("endpoint con segmento '.': %s" % ep)
    rest = ep[len("repos/%s/%s" % (m[1], m[2])):]
    if rest and rest[0] not in "/?":
        raise ValueError("endpoint non ammesso: %s" % ep)


def _repo_of_endpoint(ep):
    m = re.match(r"^repos/([^/?]+/[^/?]+)/", ep)
    return m.group(1) if m else None


def _check_api_write(args):
    """Scrittura `gh api` (argomenti dopo `api`): solo le tre forme esatte della decisione 25, ValueError
    altrimenti. Nessuna opzione fuori da `--method|-X`, `-f` (una per chiave) e `--input`."""
    method = endpoint = infile = None
    fields = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--method", "-X", "-f", "--input"):
            if i + 1 >= len(args):
                raise ValueError("gh api: %s senza valore" % a)
            v = args[i + 1]
            i += 2
            if a in ("--method", "-X"):
                if method is not None:
                    raise ValueError("gh api: metodo ripetuto")
                method = v
            elif a == "-f":
                key, eq, val = v.partition("=")
                if not eq or key in fields:
                    raise ValueError("gh api: campo -f non valido o ripetuto")
                fields[key] = val
            else:
                if infile is not None:
                    raise ValueError("gh api: --input ripetuto")
                infile = v
        elif a.startswith("-"):
            raise ValueError("gh api: opzione di scrittura non ammessa (%s)" % a)
        else:
            if endpoint is not None:
                raise ValueError("gh api: più di un endpoint")
            endpoint = a
            i += 1
    if endpoint is None:
        raise ValueError("gh api senza endpoint")
    _check_endpoint(endpoint)
    repo = _repo_of_endpoint(endpoint)
    if method == "POST" and infile is None:
        ok = (re.match(r"^repos/[^/]+/[^/]+/statuses/[0-9a-f]{40}$", endpoint)
              and set(fields) == {"state", "context", "description"}
              and fields["state"] in STATUS_STATES and fields["context"] == STATUS_CONTEXT
              and fields["description"] == STATUS_DESCRIPTION)
        if ok:
            return
        raise ValueError("gh api POST: solo statuses/<sha> con state, context=%s e la descrizione di prova"
                         % STATUS_CONTEXT)
    if method == "PUT" and not fields and infile is not None:
        if repo == PROT and endpoint == PROTECTION_ENDPOINT % PROT and _infile(infile):
            return
        raise ValueError("gh api PUT: solo branches/main/protection su protected, con --input da un file temporaneo")
    if method == "DELETE" and not fields and infile is None:
        if repo == PROT and endpoint == PROTECTION_ENDPOINT % PROT:
            return
        raise ValueError("gh api DELETE: solo branches/main/protection su protected")
    raise ValueError("gh api: scrittura non ammessa")


_WRITE_OPTS = ("--method", "-X", "-f", "-F", "--input", "--field", "--raw-field")


def _is_write(arg):
    return arg.startswith("-") and arg.split("=", 1)[0] in _WRITE_OPTS or arg[:2] in ("-X", "-f", "-F")


def violation(args, lenient=False, profile="script"):
    """None se il comando è ammesso, altrimenti il motivo. `profile` è `script` (gli script di prova) o
    `flow` (il `claude -p` del flusso: niente creazione di issue, merge, chiusure, scritture `gh api`)."""
    if not args:
        return "comando vuoto"
    if profile not in PROFILES:
        return "profilo sconosciuto: %s" % profile
    first, second = args[0], (args[1] if len(args) > 1 else "")
    if profile == "flow" and (first == "repo" or (first, second) in FLOW_FORBIDDEN):
        return "gh %s %s non ammesso nel flusso" % (first, second)
    try:
        if first == "--version":
            return None if len(args) == 1 else "--version con altro"
        if first == "auth":
            return None if args == ["auth", "status"] else "solo `gh auth status`"
        if first == "repo":
            if second == "create":
                if len(args) < 3 or args[2] not in REPOS:
                    return "repo create: repo non ammesso"
                opts = args[3:]
                if any(o not in REPO_CREATE_OPTS for o in opts):
                    return "repo create: opzione non ammessa (solo --public|--private --add-readme)"
                if len(set(opts) & {"--public", "--private"}) != 1:
                    return "repo create: serve esattamente una tra --public e --private"
                return None
            if second == "clone":
                if len(args) < 3 or args[2] not in REPOS:
                    return "repo clone: repo non ammesso"
                rest = args[3:]
                if rest and not rest[0].startswith("-"):
                    if not _under("P4_WORK", rest[0]):
                        return "repo clone: la cartella deve stare sotto P4_WORK"
                    rest = rest[1:]
                if rest not in ([], ["--", "-q"]):
                    return "repo clone: argomenti non ammessi"
                return None
            if second == "view":
                return None if len(args) == 3 and args[2] in REPOS else "repo view: solo `repo view <repo>`"
            return "gh repo %s non ammesso" % second
        if (first, second) in SPECS:
            _parse((first, second), args[2:], lenient)
            return None
        if first == "api":
            if any(_is_write(a) for a in args[1:]):
                if profile == "flow":
                    return "gh api in scrittura non ammesso nel flusso"
                _check_api_write(args[1:])
                return None
            ep = None
            i = 1
            while i < len(args):
                a = args[i]
                if a in API_FLAGS:
                    i += 1
                elif a in API_VALUED:
                    if i + 1 >= len(args):
                        return "gh api: %s senza valore" % a
                    i += 2
                    if lenient:     # nel registro gli spazi del filtro jq sono andati persi
                        while i < len(args) and not args[i].startswith(("-", "repos/")):
                            i += 1
                elif a.startswith("-"):
                    return "gh api: opzione non ammessa (%s): solo lettura" % a
                else:
                    if ep is not None:
                        return "gh api: più di un endpoint"
                    ep = a
                    i += 1
            if ep is None:
                return "gh api senza endpoint"
            _check_endpoint(ep)
            return None
        if first in ("pr", "issue", "run"):
            return "gh %s %s non ammesso" % (first, second)
        return "gh %s non ammesso" % first
    except ValueError as exc:
        return str(exc)


def _report(n, subs, bad, extra=""):
    print("comandi gh controllati: %d%s" % (n, extra))
    for k in sorted(subs):
        print("  %4d  gh %s" % (subs[k], k))
    for why, cmd in bad:
        print("VIOLAZIONE (%s): %s" % (why, cmd))
    return 1 if bad else 0


def _key(args):
    return " ".join(args[:2]) if args[0] in ("repo", "auth", "pr", "run", "issue") else args[0]


def check_log(path):
    n, subs, bad = 0, {}, []
    for line in open(path):
        args = line.rstrip("\n").split("\t")
        if args and args[-1] == "":
            args = args[:-1]
        if not args:
            continue
        n += 1
        subs[_key(args)] = subs.get(_key(args), 0) + 1
        why = violation(args)
        if why:
            bad.append((why, " ".join(args)))
        for t in re.findall(r"%s/[\w.-]+" % OWNER, " ".join(args)):
            if t not in REPOS:
                bad.append(("repo non ammesso", " ".join(args)))
    if n == 0:
        bad.append(("registro vuoto", ""))
    return _report(n, subs, bad)


def check_comandi(path):
    """comandi.log: `<ora> gh <argomenti separati da spazi>`; le righe git e quelle annotate «(controller...)»
    (comandi a mano del controller, con annotazione nel testo) non sono comandi dello script e si escludono."""
    n, excluded, subs, bad = 0, 0, {}, []
    if "P4_OUT" not in os.environ:
        os.environ["P4_OUT"] = os.path.dirname(os.path.abspath(path))
    os.environ.setdefault("P4_WORK", "/tmp/tollgate-p4/gh")
    for line in open(path):
        m = re.match(r"^\S+ gh (.*)$", line.rstrip("\n"))
        if not m:
            continue
        if "(controller" in m.group(1):
            excluded += 1
            continue
        args = m.group(1).split(" ")
        n += 1
        subs[_key(args)] = subs.get(_key(args), 0) + 1
        why = violation(args, lenient=True)
        if why:
            bad.append((why, m.group(1)))
    if n == 0:
        bad.append(("nessun comando gh nel registro", ""))
    return _report(n, subs, bad, " (escluse %d righe annotate «(controller...)»)" % excluded)


def main(argv):
    if len(argv) >= 3 and argv[1] == "check" and argv[2] == "--":
        why = violation(argv[3:], profile=os.environ.get("P4_PROFILE", "script"))
        if why:
            print(why, file=sys.stderr)
            return 1
        return 0
    if len(argv) == 3 and argv[1] == "log":
        return check_log(argv[2])
    if len(argv) == 3 and argv[1] == "comandi":
        return check_comandi(argv[2])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
