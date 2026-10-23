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

Il profilo `p5` (P4_PROFILE=p5, decisioni 20-22 di P5: spikes/p5/run-p5-checks.sh) ammette solo
`ginz0ls/tollgate` e `ginz0ls/tollgate-p4-detect` (mai `tollgate-p4-protected`), con le operazioni per repo di
`P5_REPO_OPS`. Le scritture `gh api` sono due forme esatte su detect: la PATCH del corpo di una PR aperta dal
controller nella stessa prova (numeri registrati con `check` di un `pr create` + `register-pr`, file `P5_PR_REGISTRY`)
e il PUT di `actions/permissions` per `sha_pinning_required`. Per i comandi git con la rete:

  ghguard.py gitcheck [--dir <cartella>] -- <argomenti di git, senza -C>      exit 0 se ammesso (profilo p5)
  ghguard.py register-pr <numero>                                            registra una PR aperta dal controller
"""
import os
import re
import sys

OWNER = "ginz0ls"
PROT = OWNER + "/tollgate-p4-protected"
DET = OWNER + "/tollgate-p4-detect"
REPOS = (PROT, DET)
TOL = OWNER + "/tollgate"
P5_REPOS = (TOL, DET)
FLOW_CLONE = "/tmp/tollgate-p4/flow/protected"      # cartella del clone del flusso (run-p4-flow.sh: $FLOW/protected)

REPO_CREATE_OPTS = {"--public", "--private", "--add-readme"}
API_FLAGS = {"--include", "--paginate", "--silent"}
API_VALUED = {"--jq", "-q"}

# tutte le espressioni si usano con fullmatch: `$` accetterebbe un a-capo finale
BRANCH_RE = re.compile(r"[A-Za-z0-9._/-]+")
FIELDS_RE = re.compile(r"[A-Za-z][A-Za-z,]*")
NAME_RE = re.compile(r"[A-Za-z0-9._-]+")
INT_RE = re.compile(r"[0-9]+")
STATES = {"open", "closed", "merged", "all"}
PROFILES = ("script", "flow", "p5")
FLOW_FORBIDDEN = {("pr", "edit"), ("issue", "create"), ("issue", "close"), ("issue", "comment"), ("pr", "merge"), ("pr", "close"),
                  ("pr", "comment"), ("run", "download")}
PROFILE = {"current": "script"}          # il profilo della chiamata in corso (letto da _infile)
# scritture `gh api` ammesse (decisione 25): descrizione senza spazi, che `comandi.log` non conserva
STATUS_DESCRIPTION = "prova-token-personale-p4"
STATUS_CONTEXT = "tollgate/verdict"
STATUS_STATES = {"success", "failure", "error", "pending"}
PROTECTION_ENDPOINT = "repos/%s/branches/main/protection"


def _ok_branch(v):
    return bool(BRANCH_RE.fullmatch(v)) and not v.startswith("-") and ".." not in v


def _is_int(v):
    return bool(INT_RE.fullmatch(v))     # solo cifre ASCII: str.isdigit() accetta anche quelle Unicode


def _repos():
    return P5_REPOS if PROFILE["current"] == "p5" else REPOS


def _under(var, v):
    base = os.environ.get(var, "")
    if not base or not os.path.isabs(v):
        return False
    base = os.path.normpath(base)
    return os.path.normpath(v) == v and v.startswith(base + os.sep)


def _temp_roots():
    """Cartelle dei file temporanei dei programmi che chiamano gh per il gate (mktemp di protect.sh): /tmp e $TMPDIR.
    Nel profilo flow nessuna: i file di ingresso stanno solo sotto P4_TMP, e $TMPDIR del modello non conta."""
    if PROFILE["current"] == "flow":
        return set()
    return _temp_roots_all()


def _temp_roots_all():
    """Cartelle dei file temporanei dei programmi che chiamano gh (mktemp di protect.sh, file del corpo di
    tollgate): /tmp e $TMPDIR, mai altrove."""
    roots = {"/tmp"}
    if os.environ.get("TMPDIR"):
        roots.add(os.path.normpath(os.environ["TMPDIR"]))
    return roots


def _infile(v):
    """File di ingresso letto da gh (--body-file, --input): percorso assoluto normalizzato sotto le cartelle
    dell'ambiente (P4_OUT, P4_WORK, P4_TMP) o sotto i file temporanei."""
    if PROFILE["current"] == "flow":
        return _under("P4_TMP", v)
    if _under("P4_OUT", v) or _under("P4_WORK", v) or _under("P4_TMP", v):
        return True
    return os.path.isabs(v) and os.path.normpath(v) == v and any(v.startswith(r + os.sep) for r in _temp_roots())


# tipo di valore -> funzione di controllo
KINDS = {
    "repo": lambda v: v in _repos(),
    "int": _is_int,
    "branch": _ok_branch,
    "text": lambda v: True,
    "fields": lambda v: bool(FIELDS_RE.fullmatch(v)),
    "state": lambda v: v in STATES,
    "name": lambda v: bool(NAME_RE.fullmatch(v)) and ".." not in v,
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


def _parse(cmd, args, lenient, spec=None):
    """Controlla opzioni e posizionali di (comando, sottocomando); ValueError con il motivo. Ritorna il repo."""
    spec = spec or SPECS[cmd]
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
        if want == "int" and not _is_int(p):
            raise ValueError("serve un numero: %s" % p)
        if want == "ref" and not (_is_int(p) or _ok_branch(p)):
            raise ValueError("serve un numero o un nome di ramo semplice: %s" % p)
    if spec["one_of"] and len([f for f in seen_flags if f in spec["one_of"]]) != 1:
        raise ValueError("serve esattamente una tra %s" % ", ".join(sorted(spec["one_of"])))
    if len(seen_flags) != len(set(seen_flags)):
        raise ValueError("opzione ripetuta")
    return repos[0]


def _check_endpoint(ep):
    m = re.match(r"repos/([^/?]+)/([^/?]+)", ep)
    if not m or "%s/%s" % (m[1], m[2]) not in _repos():
        raise ValueError("endpoint non ammesso: %s" % ep)
    if not re.fullmatch(r"[A-Za-z0-9._~/?&=%:,@+-]+", ep):
        raise ValueError("endpoint con caratteri non ammessi: %s" % ep)
    if re.search(r"/secrets(/|\?|$)", ep):
        raise ValueError("endpoint dei segreti: vietato (decisione 25): %s" % ep)
    if re.search(r"%2e|%2f|%5c|%00", ep, re.IGNORECASE) or ".." in ep or "//" in ep:
        raise ValueError("endpoint con '..', '//' o codifiche sospette: %s" % ep)
    if any(seg == "." for seg in re.split(r"[/?&=]", ep)):
        raise ValueError("endpoint con segmento '.': %s" % ep)
    rest = ep[len("repos/%s/%s" % (m[1], m[2])):]
    if rest and rest[0] not in "/?":
        raise ValueError("endpoint non ammesso: %s" % ep)


def _repo_of_endpoint(ep):
    m = re.match(r"repos/([^/?]+/[^/?]+)/", ep)
    return m.group(1) if m else None


def _api_write_parts(args, lenient=False):
    """Analizza una scrittura `gh api` (argomenti dopo `api`): ritorna (metodo, endpoint, -f, -F, --input) dopo
    aver controllato l'endpoint. Nessuna opzione fuori da `--method|-X`, `-f`/`-F` (una per chiave) e `--input`."""
    method = endpoint = infile = None
    fields, ffields = {}, {}
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--method", "-X", "-f", "-F", "--input"):
            if i + 1 >= len(args):
                raise ValueError("gh api: %s senza valore" % a)
            v = args[i + 1]
            i += 2
            if lenient and a in ("-F", "--input"):      # nel registro gli spazi di un percorso sono andati persi
                while i < len(args) and not args[i].startswith(("-", "repos/")):
                    v, i = v + " " + args[i], i + 1
            if a in ("--method", "-X"):
                if method is not None:
                    raise ValueError("gh api: metodo ripetuto")
                method = v
            elif a in ("-f", "-F"):
                key, eq, val = v.partition("=")
                target = fields if a == "-f" else ffields
                if not eq or key in fields or key in ffields:
                    raise ValueError("gh api: campo %s non valido o ripetuto" % a)
                target[key] = val
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
    return method, endpoint, fields, ffields, infile


def _check_api_write(args, flow=False, lenient=False):
    """Scrittura `gh api` del profilo script/flow: solo le tre forme esatte della decisione 25, ValueError altrimenti."""
    method, endpoint, fields, ffields, infile = _api_write_parts(args, lenient)
    repo = _repo_of_endpoint(endpoint)
    if method == "PATCH":
        # unica forma: il corpo di una PR di protected da un file (gh pr edit non funziona con gh 2.46)
        body = ffields.get("body", "")
        if (repo == PROT and re.fullmatch(r"repos/[^/]+/[^/]+/pulls/[0-9]+", endpoint) and not fields and infile is None
                and set(ffields) == {"body"} and body.startswith("@") and _infile(body[1:])):
            return
        raise ValueError("gh api PATCH: solo repos/%s/pulls/<n> con -F body=@<file> da una cartella ammessa" % PROT)
    if flow:
        raise ValueError("gh api in scrittura non ammesso nel flusso (solo PATCH del corpo di una PR)")
    if ffields:
        raise ValueError("gh api: -F non ammesso in questa forma")
    if method == "POST" and infile is None:
        ok = (re.fullmatch(r"repos/[^/]+/[^/]+/statuses/[0-9a-f]{40}", endpoint)
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


def _check_api_read(args, lenient=False):
    """Lettura `gh api` (argomenti dopo `api`): None se ammessa, altrimenti il motivo."""
    ep = None
    i = 0
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
    PROFILE["current"] = profile
    if profile == "p5":
        try:
            return _violation_p5(args, lenient)
        except ValueError as exc:
            return str(exc)
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
                want = "--public" if args[2] == PROT else "--private"
                if want not in opts:
                    return "repo create: %s va creato con %s" % (args[2], want)
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
                    if not _under("P4_WORK", rest[0]) and not (args[2] == PROT and rest[0] == FLOW_CLONE):
                        return "repo clone: la cartella deve stare sotto P4_WORK (o essere il clone del flusso di protected)"
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
                _check_api_write(args[1:], flow=(profile == "flow"), lenient=lenient)
                return None
            return _check_api_read(args[1:], lenient)
        if first in ("pr", "issue", "run"):
            return "gh %s %s non ammesso" % (first, second)
        return "gh %s non ammesso" % first
    except ValueError as exc:
        return str(exc)


# ---------------------------------------------------------------- profilo p5 (decisioni 20-22 di P5)

PR_OPS = {("pr", "create"), ("pr", "close"), ("pr", "merge"), ("pr", "view"), ("pr", "list"), ("pr", "comment"),
          ("issue", "close"), ("issue", "comment"), ("issue", "view"), ("issue", "list")}
RUN_OPS = {("run", "list"), ("run", "view"), ("run", "watch"), ("run", "download"), ("run", "rerun")}
P5_REPO_OPS = {TOL: set(RUN_OPS), DET: PR_OPS | RUN_OPS}      # operazioni per repo (decisioni 20 e 21)
P5_SPECS = {key: SPECS[key] for key in PR_OPS | (RUN_OPS - {("run", "rerun")})}
P5_SPECS[("run", "rerun")] = _spec({}, flags=("--failed",), pos="int")
PERMISSIONS_ENDPOINT = "repos/%s/actions/permissions"
ALLOWED_ACTIONS = {"all", "local_only", "selected"}
FOREIGN_RE = re.compile(r"%s/[A-Za-z0-9._-]+" % re.escape(OWNER))


def _registry_path():
    return os.environ.get("P5_PR_REGISTRY", "")


def _registry_lines():
    path = _registry_path()
    if not path:
        return []
    try:
        with open(path) as fh:
            return [line.strip() for line in fh if line.strip()]
    except OSError:
        return []


def registered_prs():
    """Numeri delle PR registrate dal controller nella prova corrente (file P5_PR_REGISTRY)."""
    return {int(line[3:]) for line in _registry_lines() if re.fullmatch(r"pr [0-9]+", line)}


def note_pr_create():
    """Un `gh pr create` è passato dalla guardia: annota che una PR sta per essere aperta. Falso senza registro."""
    path = _registry_path()
    if not path or not os.path.isabs(path):
        return False
    with open(path, "a") as fh:
        fh.write("create\n")
    return True


def register_pr(number):
    """Registra il numero di una PR appena aperta: ammesso solo se c'è un `create` annotato non ancora consumato."""
    if not _is_int(number):
        raise ValueError("numero di PR non valido: %s" % number)
    lines = _registry_lines()
    if lines.count("create") <= len([x for x in lines if x.startswith("pr ")]):
        raise ValueError("nessun `gh pr create` passato dalla guardia in attesa di registrazione")
    with open(_registry_path(), "a") as fh:
        fh.write("pr %d\n" % int(number))


def _foreign_repo(args):
    """Il primo `ginz0ls/<nome>` negli argomenti che non è uno dei due repo ammessi (anche dentro un testo)."""
    for a in args:
        for found in FOREIGN_RE.findall(a):
            found = found.rstrip(".")
            if found not in P5_REPOS:
                return found
    return None


def _check_api_write_p5(args, lenient=False):
    method, endpoint, fields, ffields, infile = _api_write_parts(args, lenient)
    repo = _repo_of_endpoint(endpoint)
    if repo != DET:
        raise ValueError("gh api in scrittura: solo su %s" % DET)
    if method == "PATCH":
        m = re.fullmatch(r"repos/[^/]+/[^/]+/pulls/([0-9]+)", endpoint)
        body = ffields.get("body", "")
        if not (m and not fields and infile is None and set(ffields) == {"body"} and body.startswith("@")
                and _infile(body[1:])):
            raise ValueError("gh api PATCH: solo repos/%s/pulls/<n> con -F body=@<file> da una cartella ammessa" % DET)
        if int(m.group(1)) not in registered_prs():
            raise ValueError("gh api PATCH: la PR %s non è stata aperta dal controller in questa prova" % m.group(1))
        return
    if method == "PUT" and endpoint == PERMISSIONS_ENDPOINT % DET and not fields and infile is None:
        keys = set(ffields)
        if (keys in ({"enabled", "sha_pinning_required"}, {"enabled", "sha_pinning_required", "allowed_actions"})
                and ffields["enabled"] == "true" and ffields["sha_pinning_required"] in ("true", "false")
                and ffields.get("allowed_actions", "all") in ALLOWED_ACTIONS):
            return
        raise ValueError("gh api PUT: actions/permissions solo con -F enabled=true, -F sha_pinning_required=true|false "
                         "e al più -F allowed_actions=all|local_only|selected")
    raise ValueError("gh api: scrittura non ammessa nel profilo p5 (solo PATCH del corpo di una PR registrata e PUT di "
                     "actions/permissions su detect)")


def _violation_p5(args, lenient):
    first, second = args[0], (args[1] if len(args) > 1 else "")
    foreign = _foreign_repo(args)
    if foreign:
        return "repo non ammesso nel profilo p5: %s" % foreign
    if first == "--version":
        return None if len(args) == 1 else "--version con altro"
    if first == "auth":
        return None if args == ["auth", "status"] else "solo `gh auth status`"
    if first == "repo":
        if args == ["repo", "create", TOL, "--private"]:
            return None
        return "gh repo %s non ammesso (solo `repo create %s --private`)" % (second, TOL)
    if (first, second) in P5_SPECS:
        repo = _parse((first, second), args[2:], lenient, P5_SPECS[(first, second)])
        if (first, second) not in P5_REPO_OPS[repo]:
            return "gh %s %s non ammesso su %s" % (first, second, repo)
        return None
    if first == "api":
        if any(_is_write(a) for a in args[1:]):
            _check_api_write_p5(args[1:], lenient)
            return None
        return _check_api_read(args[1:], lenient)
    return "gh %s %s non ammesso nel profilo p5" % (first, second)


# ---------------------------------------------------------------- comandi git con la rete (profilo p5)

GH_URL = "https://github.com/"
TOL_URL, DET_URL = "%s%s.git" % (GH_URL, TOL), "%s%s.git" % (GH_URL, DET)
ACTIONS = ("checkout", "cache", "upload-artifact", "download-artifact", "setup-python")
ACTION_URLS = tuple("%sactions/%s" % (GH_URL, a) for a in ACTIONS)
TAG_RE = re.compile(r"v[0-9]+(?:\.[0-9]+){0,2}")
PINS_DEFAULT = "/tmp/tollgate-p5-pins"


def _below(base, path):
    """`path` è un percorso assoluto normalizzato strettamente sotto `base`."""
    if not base or not path or not os.path.isabs(path) or os.path.normpath(path) != path:
        return False
    base = os.path.normpath(base)
    return path.startswith(base + os.sep)


def git_violation(args, directory=""):
    """None se il comando git con la rete è ammesso nel profilo p5, altrimenti il motivo. `args` sono gli argomenti
    dopo `git` (senza -C), `directory` la cartella in cui il comando agisce (per `clone`, la destinazione).
    Nessuna opzione ammessa fuori da quelle elencate: mai --force, --mirror, --all, --tags, +refspec."""
    if not args:
        return "comando git vuoto"
    verb, rest = args[0], args[1:]
    if verb == "push":
        delete = bool(rest) and rest[0] == "--delete"
        if delete:
            rest = rest[1:]
        if len(rest) != 2 or rest[0] not in (TOL_URL, DET_URL):
            return "push: serve `push [--delete] <url di tollgate o detect> <ramo>`"
        url, ref = rest
        if not _ok_branch(ref):
            return "push: ramo non ammesso: %s" % ref
        if url == TOL_URL:
            probe = ref.startswith("p5-probe-") and len(ref) > len("p5-probe-")
            if delete and not probe:
                return "push --delete su tollgate: solo rami p5-probe-*"
            if not (probe or ref in ("main", "p5-eval-ci")):
                return "push su tollgate: solo main, p5-eval-ci e p5-probe-*"
            return None
        if delete:
            return "push --delete su detect non ammesso"
        return None
    if verb == "ls-remote":
        if len(rest) == 2 and rest[0] == "--tags" and rest[1] in ACTION_URLS:
            return None
        return "ls-remote: solo `--tags https://github.com/actions/<azione>`"
    if verb == "fetch":
        if len(rest) == 5 and rest[:2] == ["--depth", "1"] and rest[2] in ACTION_URLS and rest[3] == "tag":
            if not TAG_RE.fullmatch(rest[4]):
                return "fetch: tag non ammesso: %s" % rest[4]
            if not _below(os.environ.get("P5_PINS", PINS_DEFAULT), directory):
                return "fetch: la cartella deve stare sotto P5_PINS"
            return None
        return "fetch: solo `--depth 1 https://github.com/actions/<azione> tag <tag>` (sotto P5_PINS)"
    if verb == "clone":
        if len(rest) == 3 and rest[0] == "-q" and rest[1] == DET_URL and rest[2] == directory:
            if not _below(os.environ.get("P4_WORK", ""), directory):
                return "clone di detect: la destinazione deve stare sotto P4_WORK"
            return None
        return "clone: solo `-q <url di detect> <destinazione sotto P4_WORK>`"
    return "git %s non ammesso con la rete" % verb



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
    profile = os.environ.get("P4_PROFILE", "script")
    allowed = P5_REPOS if profile == "p5" else REPOS
    for line in open(path):
        args = line.rstrip("\n").split("\t")
        if args and args[-1] == "":
            args = args[:-1]
        if not args:
            continue
        n += 1
        subs[_key(args)] = subs.get(_key(args), 0) + 1
        why = violation(args, profile=profile)
        if why:
            bad.append((why, " ".join(args)))
        for t in re.findall(r"%s/[\w.-]+" % OWNER, " ".join(args)):
            if t not in allowed:
                bad.append(("repo non ammesso", " ".join(args)))
    if n == 0:
        bad.append(("registro vuoto", ""))
    return _report(n, subs, bad)


def check_comandi(path):
    """comandi.log: `<ora> gh <argomenti separati da spazi>`; le righe git e quelle annotate «(controller...)»
    (comandi a mano del controller, con annotazione nel testo) non sono comandi dello script e si escludono."""
    n, excluded, subs, bad = 0, 0, {}, []
    profile = os.environ.get("P4_PROFILE", "script")
    if "P4_OUT" not in os.environ:
        os.environ["P4_OUT"] = os.path.dirname(os.path.abspath(path))
    os.environ.setdefault("P4_WORK", "/tmp/tollgate-p5" if profile == "p5" else "/tmp/tollgate-p4/gh")
    if profile == "p5":
        os.environ.setdefault("P5_PR_REGISTRY", os.path.join(os.path.dirname(os.path.abspath(path)), "prs-aperte.txt"))
    here = os.path.dirname(os.path.abspath(path))
    # le evidenze committate registrano i percorsi del worktree in cui furono prodotte (`…/.claude/worktrees/<nome>/docs/
    # verifiche/evidenze/<cartella>`): per rigiocarle si riportano alla cartella corrente del registro. Solo prefissi di un
    # worktree, mai un percorso qualsiasi.
    moved = re.compile(r"(?<![^\s=@])/(?:(?:(?! -)[^/\n])+/)*?\.claude/worktrees/[^/\n]+/docs/verifiche/evidenze/%s(?=/|\s|$)"
                       % re.escape(os.path.basename(here)))
    for line in open(path):
        line = moved.sub(lambda _m: here, line.rstrip("\n"))
        g = re.match(r"^\S+ git-net dir=(\S*) (.*)$", line)
        if g and profile == "p5":      # `git-net`: i comandi git con la rete dello script (registro di common_p5)
            n += 1
            subs["git " + g.group(2).split(" ")[0]] = subs.get("git " + g.group(2).split(" ")[0], 0) + 1
            why = git_violation(g.group(2).split(" "), g.group(1))
            if why:
                bad.append((why, "git " + g.group(2)))
            continue
        m = re.match(r"^\S+ gh (.*)$", line)
        if not m:
            continue
        if "(controller" in m.group(1):
            excluded += 1
            continue
        args = m.group(1).split(" ")
        n += 1
        subs[_key(args)] = subs.get(_key(args), 0) + 1
        why = violation(args, lenient=True, profile=profile)
        if why:
            bad.append((why, m.group(1)))
    if n == 0:
        bad.append(("nessun comando gh nel registro", ""))
    return _report(n, subs, bad, " (escluse %d righe annotate «(controller...)»)" % excluded)


def main(argv):
    if len(argv) >= 3 and argv[1] == "check" and argv[2] == "--":
        profile = os.environ.get("P4_PROFILE", "script")
        why = violation(argv[3:], profile=profile)
        if why:
            print(why, file=sys.stderr)
            return 1
        if profile == "p5" and argv[3:5] == ["pr", "create"] and not note_pr_create():
            print("pr create: serve P5_PR_REGISTRY (percorso assoluto) per registrare la PR", file=sys.stderr)
            return 1
        return 0
    if len(argv) >= 3 and argv[1] == "gitcheck":
        rest, directory = argv[2:], ""
        if rest[:1] == ["--dir"] and len(rest) >= 2:
            directory, rest = rest[1], rest[2:]
        if rest[:1] != ["--"]:
            print(__doc__, file=sys.stderr)
            return 2
        why = git_violation(rest[1:], directory)
        if why:
            print(why, file=sys.stderr)
            return 1
        return 0
    if len(argv) == 3 and argv[1] == "register-pr":
        try:
            register_pr(argv[2])
        except (ValueError, OSError) as exc:
            print(str(exc), file=sys.stderr)
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
