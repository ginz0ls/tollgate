#!/usr/bin/env python3
"""Finto `gh` per i test (spec 3.1): risponde dai dati in $TOLLGATE_FAKEGH_DATA.

Dati (JSON):
  {"auth": true,
   "issues": {"7": {"number": 7, "title": "...", "body": "...", "state": "OPEN", ...}},
   "issue_list": [{...}],
   "prs": [{"headRefName": "tg/7-x", ...}],
   "statuses": {"<sha>": {"statuses": [{"context": "tollgate/guard", "state": "success"}]}}}

Ogni chiamata si registra in $TOLLGATE_FAKEGH_LOG (una riga JSON). Una risposta che manca dai
dati esce con 1: un test che chiede qualcosa di non previsto fallisce, non passa in silenzio."""
import json
import os
import re
import sys

_COMMITS_STATUS = re.compile(r"^repos/[^/]+/[^/]+/commits/([^/]+)/status$")


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
    if argv[:2] == ["pr", "list"]:
        if "prs" not in data:
            _fail("prs assente dai dati")
        head = _flag(argv[2:], "--head")
        prs = [p for p in data["prs"] if head is None or p.get("headRefName") == head]
        print(json.dumps([_fields(p, argv[2:]) for p in prs]))
        return 0
    if argv[:1] == ["api"] and len(argv) > 1:
        m = _COMMITS_STATUS.match(argv[1])
        if m:
            status = (data.get("statuses") or {}).get(m.group(1))
            if status is None:
                _fail(f"stati del commit {m.group(1)} assenti dai dati")
            print(json.dumps(status))
            return 0
    _fail(f"chiamata non prevista: {' '.join(argv)}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
