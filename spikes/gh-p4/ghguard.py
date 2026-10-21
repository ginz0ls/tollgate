#!/usr/bin/env python3
"""Lista degli ammessi per i comandi gh di run-p4-checks.sh (decisione 25): unica fonte.

  ghguard.py check -- <argomenti di gh...>   exit 0 se ammesso, 1 con il motivo su stderr
  ghguard.py log <registro>                  controlla un registro del gh finto (argomenti separati da tab)

Un comando è ammesso solo se la coppia (comando, sottocomando) è nella tabella, ogni opzione è nell'elenco
di quel comando e ogni repo nominato è uno dei due. `gh api` è solo in lettura: ogni opzione che non sia
nell'elenco (qualunque forma di -X, --method, -f, -F, --field, --raw-field, --input) è rifiutata.
"""
import re
import sys

OWNER = "ginz0ls"
PROT = OWNER + "/tollgate-p4-protected"
DET = OWNER + "/tollgate-p4-detect"
REPOS = (PROT, DET)

PR_SUBS = {"create", "edit", "close", "merge", "view", "list", "comment"}
ISSUE_SUBS = {"create", "close", "comment", "view", "list"}
RUN_SUBS = {"list", "view", "download", "watch"}
REPO_CREATE_OPTS = {"--public", "--private", "--add-readme"}
API_FLAGS = {"--include", "--paginate", "--silent"}
API_VALUED = {"--jq", "-q"}
FORBIDDEN_PR_FLAGS = {"merge": {"--admin", "--auto"}}


def _repo_flag(args):
    """Il repo di --repo/-R (anche --repo=R), None se assente, ValueError se doppio o senza valore."""
    found = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--repo", "-R"):
            if i + 1 >= len(args):
                raise ValueError("--repo senza valore")
            found.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--repo="):
            found.append(a[len("--repo="):])
        i += 1
    if len(found) > 1:
        raise ValueError("più di un --repo")
    return found[0] if found else None


def _check_endpoint(ep):
    m = re.match(r"^repos/([^/?]+)/([^/?]+)", ep)
    if not m or "%s/%s" % (m[1], m[2]) not in REPOS:
        raise ValueError("endpoint non ammesso: %s" % ep)
    path = ep.split("?", 1)[0]
    if re.search(r"%2e|%2f|%5c|\\", ep, re.IGNORECASE):
        raise ValueError("endpoint con codifiche sospette: %s" % ep)
    if any(seg in ("", ".", "..") for seg in path.split("/")):
        raise ValueError("endpoint con segmento vuoto o '..': %s" % ep)
    rest = ep[len("repos/%s/%s" % (m[1], m[2])):]
    if rest and rest[0] not in "/?":
        raise ValueError("endpoint non ammesso: %s" % ep)


def violation(args):
    """None se il comando è ammesso, altrimenti il motivo."""
    if not args:
        return "comando vuoto"
    first, second = args[0], (args[1] if len(args) > 1 else "")
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
                    rest = rest[1:]
                if rest not in ([], ["--", "-q"]):
                    return "repo clone: argomenti non ammessi"
                return None
            if second == "view":
                return None if len(args) == 3 and args[2] in REPOS else "repo view: solo `repo view <repo>`"
            return "gh repo %s non ammesso" % second
        if first in ("pr", "issue", "run"):
            subs = {"pr": PR_SUBS, "issue": ISSUE_SUBS, "run": RUN_SUBS}[first]
            if second not in subs:
                return "gh %s %s non ammesso" % (first, second)
            repo = _repo_flag(args[2:])
            if repo not in REPOS:
                return "gh %s %s: --repo mancante o non ammesso (%s)" % (first, second, repo)
            bad = FORBIDDEN_PR_FLAGS.get(second, set()) if first == "pr" else set()
            if bad & set(args):
                return "gh pr %s: opzione non ammessa" % second
            return None
        if first == "api":
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
        return "gh %s non ammesso" % first
    except ValueError as exc:
        return str(exc)


def check_log(path):
    n, subs, bad = 0, {}, []
    for line in open(path):
        args = line.rstrip("\n").split("\t")
        if args and args[-1] == "":
            args = args[:-1]
        if not args:
            continue
        n += 1
        key = " ".join(args[:2]) if args[0] in ("repo", "auth", "pr", "run", "issue") else args[0]
        subs[key] = subs.get(key, 0) + 1
        why = violation(args)
        if why:
            bad.append((why, " ".join(args)))
        for t in re.findall(r"%s/[\w.-]+" % OWNER, " ".join(args)):
            if t not in REPOS:
                bad.append(("repo non ammesso", " ".join(args)))
    if n == 0:
        bad.append(("registro vuoto", ""))
    print("comandi gh registrati: %d" % n)
    for k in sorted(subs):
        print("  %4d  gh %s" % (subs[k], k))
    for why, cmd in bad:
        print("VIOLAZIONE (%s): %s" % (why, cmd))
    return 1 if bad else 0


def main(argv):
    if len(argv) >= 3 and argv[1] == "check" and argv[2] == "--":
        why = violation(argv[3:])
        if why:
            print(why, file=sys.stderr)
            return 1
        return 0
    if len(argv) == 3 and argv[1] == "log":
        return check_log(argv[2])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
