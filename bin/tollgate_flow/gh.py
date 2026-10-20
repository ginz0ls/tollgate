"""`gh` per il flusso (spec 3.1). Nei test `TOLLGATE_GH` indica il finto `tests/fakegh.py`.

Nessun testo dell'issue entra mai in un argomento: si passano solo numeri, SHA e prefissi
costruiti da numeri."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from tollgate_core import paths

GH_ENV = "TOLLGATE_GH"
GH_TIMEOUT_S = 60
REQUIRED_CONTEXTS = ("tollgate/guard", "tollgate/verdict")
SENTINEL_TITLE = "tollgate: merge non verificato"


class GhError(Exception):
    pass


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    state: str
    labels: tuple[str, ...]
    author_association: str


def gh_cmd(state: paths.State) -> list[str]:
    override = paths.test_env(state, GH_ENV)
    return [override] if override else ["gh"]


def _run(state, repo, args) -> subprocess.CompletedProcess:
    env = {**os.environ, "GH_PROMPT_DISABLED": "1", "NO_COLOR": "1"}
    try:
        return subprocess.run([*gh_cmd(state), *args], cwd=str(repo), capture_output=True,
                              text=True, timeout=GH_TIMEOUT_S, env=env,
                              stdin=subprocess.DEVNULL)
    except FileNotFoundError as e:
        raise GhError("gh non è installato") from e
    except subprocess.TimeoutExpired as e:
        raise GhError(f"gh {' '.join(args[:2])}: timeout dopo {GH_TIMEOUT_S} s") from e


def run_json(state, repo, args):
    r = _run(state, repo, args)
    if r.returncode != 0:
        raise GhError(f"gh {' '.join(args[:2])}: {r.stderr.strip() or 'uscita ' + str(r.returncode)}")
    try:
        return json.loads(r.stdout)
    except ValueError as e:
        raise GhError(f"gh {' '.join(args[:2])}: risposta non JSON") from e


def decode_json_values(text: str) -> list[dict]:
    """I valori JSON dell'uscita in sequenza (G5: niente `--slurp`), uno per riga o su più righe,
    separati da spazi. Un testo non JSON o un valore che non è un oggetto è un errore."""
    decoder, values, i = json.JSONDecoder(), [], 0
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return values
        try:
            value, i = decoder.raw_decode(text, i)
        except ValueError as e:
            raise GhError("risposta non JSON") from e
        if not isinstance(value, dict):
            raise GhError("risposta inattesa: un valore JSON che non è un oggetto")
        values.append(value)


def run_json_lines(state, repo, args) -> list[dict]:
    """Per `--paginate --jq`: un oggetto JSON per elemento. Uscita non zero → `GhError`."""
    r = _run(state, repo, args)
    if r.returncode != 0:
        raise GhError(f"gh {' '.join(args[:2])}: {r.stderr.strip() or 'uscita ' + str(r.returncode)}")
    try:
        return decode_json_values(r.stdout)
    except GhError as e:
        raise GhError(f"gh {' '.join(args[:2])}: {e}") from e


def _run_checked(state, repo, args) -> None:
    r = _run(state, repo, args)
    if r.returncode != 0:
        raise GhError(f"gh {' '.join(args[:2])}: {r.stderr.strip() or 'uscita ' + str(r.returncode)}")


def auth_ok(state, repo) -> bool:
    try:
        return _run(state, repo, ["auth", "status"]).returncode == 0
    except GhError:
        return False


def _label_names(raw) -> tuple[str, ...]:
    out = []
    for item in raw if isinstance(raw, list) else []:
        name = item.get("name") if isinstance(item, dict) else item
        if isinstance(name, str) and name:
            out.append(name)
    return tuple(out)


def issue(state, repo, n: int) -> Issue:
    """L'issue dall'API REST: `gh issue view --json` non ha `authorAssociation` (gh 2.46)."""
    data = run_json(state, repo, ["api", f"repos/{{owner}}/{{repo}}/issues/{int(n)}"])
    if not isinstance(data, dict):
        raise GhError(f"issue #{n}: risposta inattesa")

    def text(key):
        v = data.get(key)
        return v if isinstance(v, str) else ""

    return Issue(number=int(data.get("number") or n), title=text("title"), body=text("body"),
                 state=text("state").upper(), labels=_label_names(data.get("labels")),
                 author_association=text("author_association").upper())


# L'API REST dà `state` in minuscolo e il merge solo in `merged_at`: si porta alla forma di
# `gh pr list` (OPEN, CLOSED, MERGED), che si aspettano `start` e i task successivi.
PR_JQ = (".[] | {number, headRefName: .head.ref, state: (if .merged_at then \"MERGED\" else "
         "(.state | ascii_upcase) end), url: .html_url}")


def prs_for_branch_prefix(state, repo, prefix: str) -> list[dict]:
    """Tutte le PR (aperte e chiuse) i cui rami cominciano per `prefix`: `api --paginate`, una
    riga JSON per PR (G5)."""
    data = run_json_lines(state, repo, ["api", "--paginate",
                                        "repos/{owner}/{repo}/pulls?state=all&per_page=100",
                                        "--jq", PR_JQ])
    return [p for p in data if str(p.get("headRefName", "")).startswith(prefix)]


def pr_for_branch(state, repo, branch: str) -> dict | None:
    """La PR con il numero più alto per il ramo, in qualunque stato (G4). Un errore di `gh` è
    un `GhError`, mai «nessuna PR»."""
    data = run_json(state, repo, ["pr", "list", "--head", branch, "--state", "all", "--limit",
                                  "100", "--json", "number,state,url,headRefOid,mergedAt"])
    if not isinstance(data, list):
        raise GhError("pr list: risposta inattesa")
    found = [p for p in data if isinstance(p, dict) and isinstance(p.get("number"), int)]
    return max(found, key=lambda p: p["number"]) if found else None


def pr_view(state, repo, number: int) -> dict:
    data = run_json(state, repo, ["pr", "view", str(int(number)), "--json",
                                  "number,state,url,mergedAt"])
    if not isinstance(data, dict):
        raise GhError(f"pr view {number}: risposta inattesa")
    return data


def pr_create(state, repo, *, branch: str, base: str, title: str, body_file) -> None:
    """Il titolo viene dal nome del ramo (solo `[a-z0-9-]`), il corpo da un file: nessun testo
    non fidato in un argomento. L'URL non si legge da stdout (G2): si rilegge con
    `pr_for_branch`."""
    _run_checked(state, repo, ["pr", "create", "--head", branch, "--base", base, "--title",
                               title, "--body-file", str(body_file)])


def pr_edit(state, repo, number: int, *, body_file) -> None:
    _run_checked(state, repo, ["pr", "edit", str(int(number)), "--body-file", str(body_file)])


def pr_body(state, repo, number: int) -> str:
    """Il corpo della PR (dato non fidato: `adopt` ne legge solo il blocco JSON)."""
    data = run_json(state, repo, ["pr", "view", str(int(number)), "--json", "body"])
    body = data.get("body") if isinstance(data, dict) else None
    if not isinstance(body, str):
        raise GhError(f"pr view {number}: risposta inattesa")
    return body


def pr_comments(state, repo, number: int) -> list[dict]:
    data = run_json(state, repo, ["pr", "view", str(int(number)), "--json", "comments"])
    comments = data.get("comments") if isinstance(data, dict) else None
    if not isinstance(comments, list):
        raise GhError(f"pr view {number}: risposta inattesa")
    return [c for c in comments if isinstance(c, dict)]


def commit_state(state, repo, sha: str) -> dict[str, str]:
    """Stato dei soli contesti obbligatori (`REQUIRED_CONTEXTS`) presenti sul commit."""
    data = run_json(state, repo, ["api", f"repos/{{owner}}/{{repo}}/commits/{sha}/status"])
    found = {}
    for item in data.get("statuses", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and item.get("context") in REQUIRED_CONTEXTS:
            found[item["context"]] = str(item.get("state", ""))
    return found


def sentinel_issues(state, repo) -> list[dict]:
    data = run_json(state, repo, ["issue", "list", "--state", "open", "--limit", "100",
                                  "--json", "number,title,url"])
    if not isinstance(data, list):
        raise GhError("issue list: risposta inattesa")
    return [i for i in data if isinstance(i, dict) and i.get("title") == SENTINEL_TITLE]
