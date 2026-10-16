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


def prs_for_branch_prefix(state, repo, prefix: str) -> list[dict]:
    data = run_json(state, repo, ["pr", "list", "--state", "all", "--limit", "200", "--json",
                                  "number,headRefName,state,url"])
    if not isinstance(data, list):
        raise GhError("pr list: risposta inattesa")
    return [p for p in data if isinstance(p, dict)
            and str(p.get("headRefName", "")).startswith(prefix)]


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
