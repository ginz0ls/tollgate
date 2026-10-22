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
   "statuses": {"<sha>": {"statuses": [{"context": "tollgate/guard", "state": "success"}]}},
   "api_status": {"repos/o/r/branches/main/protection": {"status": 403, "message": "...",
                                                          "body": {"message": "..."}}}}

`api_status` risponde a `gh api --include <percorso>` come `gh` vero (V2): su stdout la riga di
stato `HTTP/2.0 403 Forbidden` terminata da `\n`, le intestazioni terminate da `\r\n`, una riga
vuota `\r\n`, il corpo JSON senza a capo finale; con codice >= 400 esce con 1 e su stderr
`gh: <message> (HTTP <codice>)`. Senza `--include` il corpo è il solo stdout.
Scritture (REST, `--method POST|PATCH`): `repos/o/r/statuses/<sha>` (corpo da `--input`) si
accoda in testa a `commit_statuses[<sha>]` con `creator.login = "github-actions[bot]"`; i
commenti (`-F body=@<file>`) si accodano a `comments` della PR o dell'issue, anche di
`open_issues` (`POST issues/<n>/comments`), o si riscrivono (`PATCH issues/comments/<id>`);
`POST repos/o/r/issues` accoda a `open_issues` (con `body`).
`PUT repos/o/r/branches/<ramo>/protection` (corpo da `--input`) si accoda a `protection_puts` e
risponde 200. La GET della protezione si dà con `api_status` (il percorso è quello letterale con
`{owner}/{repo}`, come lo passa il codice) e `actions/permissions` lo stesso.
Letture: `commits/<sha>/check-runs` (da `check_runs[<sha>]`, righe `{name, status, conclusion,
app: {id, slug}}`): senza `--jq` il corpo REST `{"check_runs": [...]}`; con `--jq` il finto
valuta **solo** il filtro di `protect.sh` (`.name == "<job>"`, e `.app.slug == "..."` se c'è) e
stampa per riga `status<TAB>conclusion<TAB>app.id`. Poi `commits/<sha>/statuses` (da
`commit_statuses`, vuoto se manca), `commits/<sha>/pulls` (da `commit_pulls`, vuoto se manca),
`pulls/<n>` (da `pulls[<n>]`, come la REST: `body`, `head.sha|ref|repo.full_name`, `base.ref`,
`state`; 404 se manca) e `issues?state=open` (da `open_issues`, senza le righe con `pull_request`, che il filtro scarta), un valore per riga; il
`--jq` non si valuta: i dati hanno già la forma che il filtro produce.
`prs[].comments` si leggono con `pr view --json comments` come li dà GraphQL
(`author.login = "github-actions"`) e con `api repos/o/r/issues/<n>/comments` come li dà REST
(`user.login = "github-actions[bot]"`, `user.type = "Bot"`); il `--jq` non si valuta.

Le PR stanno in `prs`: `pr create` ne aggiunge una (numero successivo al più alto, stato OPEN) e
`api --method PATCH repos/o/r/pulls/<n> -F body=@<file>` riscrive `body` (come `pr edit`, che con gh 2.46 non funziona; `fail` lo chiama "pr edit"); entrambi riscrivono il file dei dati. `fail` elenca i comandi (le prime
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
_PR_COMMENTS = re.compile(r"^repos/[^/]+/[^/]+/issues/(\d+)/comments(\?.*)?$")
_STATUS_POST = re.compile(r"^repos/[^/]+/[^/]+/statuses/([0-9a-f]{40})$")
_STATUS_LIST = re.compile(r"^repos/[^/]+/[^/]+/commits/([0-9a-f]{40})/statuses(\?.*)?$")
_CHECK_RUNS = re.compile(r"^repos/[^/]+/[^/]+/commits/([0-9a-f]{40})/check-runs(\?.*)?$")
_PULL_PATCH = re.compile(r"^repos/[^/]+/[^/]+/pulls/(\d+)$")
_PROTECTION_PUT = re.compile(r"^repos/[^/]+/[^/]+/branches/[^?]+/protection$")
_JQ_NAME = re.compile(r'\.name == "([^"]+)"')
_JQ_SLUG = re.compile(r'\.app\.slug == "([^"]+)"')
_COMMIT_PULLS = re.compile(r"^repos/[^/]+/[^/]+/commits/([0-9a-f]{40})/pulls(\?.*)?$")
_ISSUES_OPEN = re.compile(r"^repos/[^/]+/[^/]+/issues\?.*state=open")
_ISSUES_NEW = re.compile(r"^repos/[^/]+/[^/]+/issues$")
_COMMENT_EDIT = re.compile(r"^repos/[^/]+/[^/]+/issues/comments/(\d+)$")
_PULLS = re.compile(r"^repos/[^/]+/[^/]+/pulls(\?.*)?$")
_PULL_ONE = re.compile(r"^repos/[^/]+/[^/]+/pulls/(\d+)$")
PR_FIELDS = frozenset({"number", "state", "url", "headRefName", "headRefOid", "mergedAt",
                       "title", "body", "comments", "isCrossRepository"})
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


# Campi che una PR dei dati ottiene da sola se non li dichiara: `isCrossRepository` è falso (PR
# dal repo stesso), `headRefOid` è la punta attuale del ramo su origin (come per GitHub: segue i
# push). Una PR da fork o con un SHA fisso li dichiara nei dati.
_PR_DEFAULTS = {"isCrossRepository": lambda obj: False,
                "headRefOid": lambda obj: _remote_oid(obj["headRefName"]) if obj.get("headRefName")
                else None}


def _pr_fields(obj, args):
    wanted = _flag(args, "--json")
    if not wanted:
        _fail("serve --json")
    names = wanted.split(",")
    unknown = [n for n in names if n not in PR_FIELDS]
    if unknown:
        _fail(f"Unknown JSON field: {', '.join(unknown)}")
    return {k: _pr_value(obj, k) for k in names if k in obj or k in _PR_DEFAULTS}


def _pr_value(obj, key):
    if key in obj:
        return obj[key]
    return _PR_DEFAULTS[key](obj)


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


_REASONS = {200: "OK", 403: "Forbidden", 404: "Not Found"}


def _api_status(entry, include):
    """Risposta di `gh api` per un percorso di `api_status`, nella forma osservata in V2."""
    status = int(entry["status"])
    body = json.dumps(entry.get("body")) if "body" in entry else ""
    if include:
        sys.stdout.write(f"HTTP/2.0 {status} {_REASONS.get(status, '')}\n"
                         "Content-Type: application/json; charset=utf-8\r\n"
                         "X-Github-Request-Id: ABCD:1234\r\n\r\n" + body)
    else:
        sys.stdout.write(body)
    if status >= 400:
        sys.stderr.write(f"gh: {entry.get('message', '')} (HTTP {status})\n")
        return 1
    return 0


def _rest_comment(comment):
    """Un commento di `pr view` (GraphQL) come lo darebbe l'API REST."""
    login = (comment.get("author") or {}).get("login", "")
    bot = login == "github-actions"
    return {"id": comment.get("id"), "body": comment.get("body", ""),
            "user": {"login": "github-actions[bot]" if bot else login,
                     "type": "Bot" if bot else "User"}}


def _ok(argv, obj):
    """`obj` come lo stampa `gh api`: con `--include` preceduto da riga di stato e intestazioni."""
    text = json.dumps(obj, separators=(",", ":"))
    if "--include" in argv:
        sys.stdout.write("HTTP/2.0 200 OK\nContent-Type: application/json; charset=utf-8\r\n\r\n"
                         + text)
    else:
        print(text)
    return 0


def _file_field(argv, name):
    """Il contenuto del file di `-F <name>=@<file>`."""
    for i, a in enumerate(argv[:-1]):
        if a == "-F" and argv[i + 1].startswith(f"{name}=@"):
            with open(argv[i + 1].split("@", 1)[1], encoding="utf-8") as f:
                return f.read()
    _fail(f"manca -F {name}=@<file>")


def _commented(data, number):
    """La PR o l'issue `number` dei dati, con la lista dei commenti."""
    for group in _groups(data):
        for item in group:
            if str(item.get("number")) == str(number):
                item.setdefault("comments", [])
                return item
    _fail(f"PR o issue {number} assente dai dati")


def _groups(data):
    """PR, issue e issue aperte dei dati: dove stanno i commenti."""
    return (data.get("prs") or [], list((data.get("issues") or {}).values()),
            data.get("open_issues") or [])


def _all_comments(data):
    for group in _groups(data):
        for item in group:
            yield from item.get("comments") or []


def _api_write(data, path_data, argv):
    """POST e PATCH di `gh api` che i test del gate usano; `None` se il percorso non è noto."""
    method, path = _flag(argv, "--method"), argv[-1]
    if method == "POST" and (m := _STATUS_POST.match(path)):
        with open(_flag(argv, "--input"), encoding="utf-8") as f:
            body = json.load(f)
        entry = {**body, "creator": {"login": "github-actions[bot]"}}
        data.setdefault("commit_statuses", {}).setdefault(m.group(1), []).insert(0, entry)
        _save(path_data, data)
        return _ok(argv, entry)
    if method == "POST" and (m := _PR_COMMENTS.match(path)):
        target = _commented(data, m.group(1))
        ids = [c.get("id") or 0 for c in _all_comments(data)]
        comment = {"id": max(ids, default=1000) + 1, "author": {"login": "github-actions"},
                   "body": _file_field(argv, "body")}
        target["comments"].append(comment)
        _save(path_data, data)
        return _ok(argv, _rest_comment(comment))
    if method == "PATCH" and (m := _COMMENT_EDIT.match(path)):
        comment = next((c for c in _all_comments(data) if str(c.get("id")) == m.group(1)), None)
        if comment is None:
            _fail(f"commento {m.group(1)} assente dai dati")
        comment["body"] = _file_field(argv, "body")
        _save(path_data, data)
        return _ok(argv, _rest_comment(comment))
    if method == "PATCH" and (m := next((x for a in argv[1:] if (x := _PULL_PATCH.match(a))), None)):
        # il corpo di una PR (sostituisce `pr edit`, rotto con gh 2.46): un solo campo, `-F body=@<file>`
        if "pr edit" in (data.get("fail") or []):
            _fail("pulls PATCH: guasto simulato")
        pr = next((p for p in data.get("prs") or [] if str(p.get("number")) == m.group(1)), None)
        if pr is None:
            _fail(f"pull request {m.group(1)} assente dai dati (HTTP 404)")
        pr["body"] = _file_field(argv, "body")
        _save(path_data, data)
        return _ok(argv, {"number": pr["number"], "body": pr["body"]})
    if method == "PUT" and _PROTECTION_PUT.match(path):
        with open(_flag(argv, "--input"), encoding="utf-8") as f:
            data.setdefault("protection_puts", []).append(json.load(f))
        _save(path_data, data)
        return _ok(argv, {})
    if method == "POST" and _ISSUES_NEW.match(path):
        issues = data.setdefault("open_issues", [])
        number = max([i["number"] for i in issues] + [100]) + 1
        issues.append({"number": number, "title": _flag(argv, "-f").split("=", 1)[1],
                       "url": f"https://github.com/prova/flow/issues/{number}",
                       "body": _file_field(argv, "body")})
        _save(path_data, data)
        return _ok(argv, {"number": number, "html_url": issues[-1]["url"]})
    return None


def _check_runs(data, argv, sha):
    """`commits/<sha>/check-runs`: il corpo REST, o il filtro di `protect.sh` valutato a mano."""
    rows = (data.get("check_runs") or {}).get(sha) or []
    jq = _flag(argv, "--jq")
    if jq is None:
        return _ok(argv, {"total_count": len(rows), "check_runs": rows})
    name, slug = _JQ_NAME.search(jq), _JQ_SLUG.search(jq)
    for row in rows:
        app = row.get("app") or {}
        if (name and row.get("name") != name.group(1)) or (
                slug and app.get("slug") != slug.group(1)):
            continue
        print("\t".join([row.get("status") or "", row.get("conclusion") or "",
                         str(app.get("id"))]))
    return 0


def _api_list(data, argv):
    """Le letture a più valori del gate, un valore per riga; `None` se il percorso non è noto."""
    path = argv[-1]
    if (m := _STATUS_LIST.match(path)):
        rows = (data.get("commit_statuses") or {}).get(m.group(1), [])
    elif (m := _COMMIT_PULLS.match(path)):
        rows = (data.get("commit_pulls") or {}).get(m.group(1), [])
    elif _ISSUES_OPEN.match(path):
        if "open_issues" not in data:
            _fail("open_issues assente dai dati")
        rows = [r for r in data["open_issues"] if r.get("pull_request") is None]  # come il jq
    else:
        return None
    for row in rows:
        print(json.dumps(row, separators=(",", ":")))
    return 0


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
                    "state": "OPEN", "url": url, "mergedAt": None, "body": body, "comments": []})
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
        entry = next((e for a in argv[1:] if (e := (data.get("api_status") or {}).get(a))), None)
        if entry is not None:
            return _api_status(entry, "--include" in argv)
        if _flag(argv, "--method") in ("POST", "PATCH", "PUT"):
            done = _api_write(data, path, argv)
            if done is not None:
                return done
        elif "--paginate" in argv:
            done = _api_list(data, argv)
            if done is not None:
                return done
        m = _CHECK_RUNS.match(argv[-1])
        if m:
            return _check_runs(data, argv, m.group(1))
        m = _PR_COMMENTS.match(argv[-1])
        if m:
            pr = next((p for p in data.get("prs") or [] if str(p.get("number")) == m.group(1)),
                      None)
            if pr is None:
                _fail(f"pull request {m.group(1)} assente dai dati")
            for c in pr.get("comments") or []:
                print(json.dumps(_rest_comment(c), separators=(",", ":")))
            return 0
        m = _COMMITS_STATUS.match(argv[1])
        if m:
            status = (data.get("statuses") or {}).get(m.group(1))
            if status is None:
                _fail(f"stati del commit {m.group(1)} assenti dai dati")
            print(json.dumps(status))
            return 0
        m = _PULL_ONE.match(argv[-1])
        if m:
            pull = (data.get("pulls") or {}).get(m.group(1))
            if pull is None:
                _fail(f"pulls/{m.group(1)} assente dai dati (HTTP 404)")
            return _ok(argv, pull)
        m = _ISSUE_REST.match(argv[-1])
        if m:
            issue = (data.get("issues") or {}).get(m.group(1))
            if issue is None:
                _fail(f"issue {m.group(1)} assente dai dati")
            return _ok(argv, issue)
    _fail(f"chiamata non prevista: {' '.join(argv)}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
