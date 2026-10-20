#!/usr/bin/env python3
"""Finto `gh` per i test (spec 3.1): risponde dai dati in $TOLLGATE_FAKEGH_DATA.

Dati (JSON):
  {"auth": true,
   "issues": {"7": {"number": 7, "title": "...", "body": "...", "state": "OPEN",
                    "labels": [{"name": "security"}], "author_association": "OWNER"}},
   "issue_list": [{...}],
   "prs": [{"number": 3, "headRefName": "tg/7-x", "state": "OPEN", "url": "...",
            "headRefOid": "<sha>", "mergedAt": null, "body": "", "comments": []}],
   "fail": ["pr create"],
   "statuses": {"<sha>": {"statuses": [{"context": "tollgate/guard", "state": "success"}]}}}

Le PR stanno in `prs`: `pr create` ne aggiunge una (numero successivo al più alto, stato OPEN) e
`pr edit` riscrive `body`; entrambi riscrivono il file dei dati. `fail` elenca i comandi (le prime
due parole, "pr create") che escono con 1 senza fare nulla, per simulare i guasti. Un campo di
`--json` che `gh` non ha per le PR esce con 1: un nome sbagliato nel codice fa fallire i test.

Ogni chiamata si registra in $TOLLGATE_FAKEGH_LOG (una riga JSON). Una risposta che manca dai
dati esce con 1: un test che chiede qualcosa di non previsto fallisce, non passa in silenzio."""
import json
import os
import re
import subprocess
import sys

_COMMITS_STATUS = re.compile(r"^repos/[^/]+/[^/]+/commits/([^/]+)/status$")
_ISSUE_REST = re.compile(r"^repos/[^/]+/[^/]+/issues/(\d+)$")
_PULLS = re.compile(r"^repos/[^/]+/[^/]+/pulls(\?.*)?$")
PR_FIELDS = frozenset({"number", "state", "url", "headRefName", "headRefOid", "mergedAt",
                       "title", "body", "comments"})
PULLS_FIELDS = ("number", "headRefName", "state", "url")
DEFAULT_LIMIT = 30


def _flag(args, name):
    for i, a in enumerate(args):
        if a == name and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return None


def _fields(obj, args):
    wanted = _flag(args, "--json")
    if not wanted:
        return obj
    return {k: obj[k] for k in wanted.split(",") if k in obj}


def _pr_fields(obj, args):
    wanted = _flag(args, "--json")
    if not wanted:
        _fail("serve --json")
    names = wanted.split(",")
    unknown = [n for n in names if n not in PR_FIELDS]
    if unknown:
        _fail(f"Unknown JSON field: {', '.join(unknown)}")
    return {k: obj[k] for k in names if k in obj}


def _save(path, data):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def _remote_oid(branch):
    """Lo SHA del ramo su origin (il finto repo nudo del banco), se si legge."""
    r = subprocess.run(["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"],
                       capture_output=True, text=True)
    return r.stdout.split()[0] if r.returncode == 0 and r.stdout.split() else None


def _fail(msg):
    sys.stderr.write(f"fakegh: {msg}\n")
    sys.exit(1)


def main(argv):
    log = os.environ.get("TOLLGATE_FAKEGH_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"argv": argv, "cwd": os.getcwd()}) + "\n")
    path = os.environ.get("TOLLGATE_FAKEGH_DATA")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, TypeError, ValueError):
        data = {}
    if argv[:2] == ["auth", "status"]:
        if data.get("auth", True):
            sys.stdout.write("Logged in to github.com\n")
            return 0
        _fail("You are not logged into any GitHub hosts")
    if argv[:2] == ["issue", "view"] and len(argv) > 2:
        issue = (data.get("issues") or {}).get(argv[2].lstrip("#"))
        if issue is None:
            _fail(f"issue {argv[2]} assente dai dati")
        print(json.dumps(_fields(issue, argv[3:])))
        return 0
    if argv[:2] == ["issue", "list"]:
        if "issue_list" not in data:
            _fail("issue_list assente dai dati")
        print(json.dumps([_fields(i, argv[2:]) for i in data["issue_list"]]))
        return 0
    if argv[:2] in (["pr", "list"], ["pr", "create"], ["pr", "edit"], ["pr", "view"]) \
            and " ".join(argv[:2]) in (data.get("fail") or []):
        _fail(f"{' '.join(argv[:2])}: guasto simulato")
    if argv[:2] == ["pr", "list"]:
        if "prs" not in data:
            _fail("prs assente dai dati")
        head = _flag(argv[2:], "--head")
        _pr_fields({}, argv[2:])        # i nomi dei campi si controllano anche senza PR
        want = (_flag(argv[2:], "--state") or "open").upper()
        limit = int(_flag(argv[2:], "--limit") or DEFAULT_LIMIT)
        prs = [p for p in data["prs"] if (head is None or p.get("headRefName") == head)
               and want in ("ALL", p.get("state", "OPEN"))]
        print(json.dumps([_pr_fields(p, argv[2:]) for p in prs[:limit]]))
        return 0
    if argv[:2] == ["pr", "view"] and len(argv) > 2:
        _pr_fields({}, argv[3:])
        pr = next((p for p in data.get("prs") or [] if str(p.get("number")) == argv[2]), None)
        if pr is None:
            _fail(f"pull request {argv[2]} assente dai dati")
        print(json.dumps(_pr_fields(pr, argv[3:])))
        return 0
    if argv[:2] == ["pr", "create"]:
        head, base = _flag(argv[2:], "--head"), _flag(argv[2:], "--base")
        title, body_file = _flag(argv[2:], "--title"), _flag(argv[2:], "--body-file")
        if not (head and base and title and body_file):
            _fail("pr create vuole --head, --base, --title e --body-file")
        try:
            with open(body_file, encoding="utf-8") as f:
                body = f.read()
        except OSError as e:
            _fail(f"corpo non leggibile: {e}")
        prs = data.setdefault("prs", [])
        number = max((p.get("number", 0) for p in prs), default=0) + 1
        url = f"https://github.com/prova/flow/pull/{number}"
        prs.append({"number": number, "headRefName": head, "baseRefName": base, "title": title,
                    "state": "OPEN", "url": url, "headRefOid": _remote_oid(head),
                    "mergedAt": None, "body": body, "comments": []})
        _save(path, data)
        print(url)
        return 0
    if argv[:2] == ["pr", "edit"] and len(argv) > 2:
        body_file = _flag(argv[3:], "--body-file")
        pr = next((p for p in data.get("prs") or [] if str(p.get("number")) == argv[2]), None)
        if pr is None or not body_file:
            _fail(f"pull request {argv[2]} assente dai dati o senza --body-file")
        try:
            with open(body_file, encoding="utf-8") as f:
                pr["body"] = f.read()
        except OSError as e:
            _fail(f"corpo non leggibile: {e}")
        _save(path, data)
        return 0
    if argv[:2] == ["api", "--paginate"] and len(argv) > 2 and _PULLS.match(argv[2]):
        if _flag(argv, "--jq") is None or "prs" not in data:
            _fail("api --paginate pulls vuole --jq e prs nei dati")
        for p in data["prs"]:
            out = {k: p.get(k) for k in PULLS_FIELDS}
            if p.get("mergedAt"):       # il jq normalizza: unita = MERGED, il resto maiuscolo
                out["state"] = "MERGED"
            out["state"] = (out["state"] or "").upper()
            print(json.dumps(out, separators=(",", ":")))
        return 0
    if argv[:1] == ["api"] and len(argv) > 1:
        m = _COMMITS_STATUS.match(argv[1])
        if m:
            status = (data.get("statuses") or {}).get(m.group(1))
            if status is None:
                _fail(f"stati del commit {m.group(1)} assenti dai dati")
            print(json.dumps(status))
            return 0
        m = _ISSUE_REST.match(argv[1])
        if m:
            issue = (data.get("issues") or {}).get(m.group(1))
            if issue is None:
                _fail(f"issue {m.group(1)} assente dai dati")
            print(json.dumps(issue))
            return 0
    _fail(f"chiamata non prevista: {' '.join(argv)}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
