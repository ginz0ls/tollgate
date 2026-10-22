"""Il gate parla con GitHub solo da qui, e solo attraverso `ghcli` (decisione 1). Nessun testo non
fidato entra in un argomento di `gh`: i commenti passano da file (`-F body=@file`), gli stati da
un file JSON (`--input`); in un percorso entrano solo numeri, SHA e il repository."""
from __future__ import annotations

import json
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path

from tollgate_core import ghcli

from .model import IssueFacts, PrFacts

STATUS_CONTEXTS = ("tollgate/guard", "tollgate/verdict", "tollgate/attention", "tollgate/base",
                   "tollgate/sentinel")
STATUS_STATES = ("success", "failure", "error", "pending")
DESCRIPTION_MAX = 140

_SHA = re.compile(r"[0-9a-f]{40}")
_SLUG = re.compile(r"(?!-)[\w.-]+/(?!-)[\w.-]+")
_PER_PAGE = "per_page=100"


def repo_slug(environ: Mapping[str, str]) -> str:
    """`proprietario/repo` da `GITHUB_REPOSITORY`, controllato: finisce in un percorso di `gh`."""
    slug = environ.get("GITHUB_REPOSITORY", "")
    if not _SLUG.fullmatch(slug) or ".." in slug:
        raise ValueError("GITHUB_REPOSITORY assente o non valido (serve proprietario/repo)")
    return slug


def _sha(sha: str) -> str:
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise ValueError(f"SHA non valido: {sha!r}")
    return sha


def _number(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError(f"numero non valido: {n!r}")
    return n


def read_event(path) -> dict:
    """L'evento di GitHub Actions (JSON, UTF-8); un file che non lo è è un `ValueError`."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except UnicodeDecodeError as e:
        raise ValueError(f"{path}: codifica non UTF-8") from e
    if not isinstance(data, dict):
        raise ValueError(f"{path}: l'evento non è un oggetto JSON")
    return data


def _node(data, *keys):
    for k in keys:
        data = data.get(k) if isinstance(data, dict) else None
    return data


def _text(data, *keys) -> str:
    value = _node(data, *keys)
    if not isinstance(value, str) or not value:
        raise ValueError(f"evento senza {'.'.join(keys)}")
    return value


def pr_from_event(event: dict) -> PrFacts | None:
    """Le informazioni della PR in un evento `pull_request_target`; `None` se l'evento non ha
    una PR. Un campo che manca o non ha la forma attesa è un `ValueError`. Una testa senza
    repository (fork cancellato) vale come fork."""
    pull = event.get("pull_request")
    if pull is None:
        return None
    number = event.get("number", _node(pull, "number"))
    head_repo = _node(pull, "head", "repo", "full_name")
    body = pull.get("body") if isinstance(pull, dict) else None
    return PrFacts(
        number=_number(number), head_sha=_sha(_text(pull, "head", "sha")),
        head_ref=_text(pull, "head", "ref"), base_ref=_text(pull, "base", "ref"),
        default_branch=_text(event, "repository", "default_branch"),
        body=body if isinstance(body, str) else "",
        cross_repo=head_repo != _text(event, "repository", "full_name"))


def set_status(state, cwd, slug: str, sha: str, *, context: str, status: str,
               description: str) -> None:
    """Pubblica uno stato `tollgate/*` sul commit `sha`; la descrizione (di tollgate) è su una
    riga e al più di 140 caratteri."""
    if context not in STATUS_CONTEXTS:
        raise ValueError(f"contesto non valido: {context!r}")
    if status not in STATUS_STATES:
        raise ValueError(f"stato non valido: {status!r}")
    text = " ".join(description.split())[:DESCRIPTION_MAX]
    with tempfile.TemporaryDirectory(prefix="tollgate-status-") as tmp:
        body = Path(tmp) / "status.json"
        body.write_text(json.dumps({"state": status, "context": context, "description": text}),
                        encoding="utf-8")
        ghcli.api(state, cwd, f"repos/{slug}/statuses/{_sha(sha)}", method="POST",
                  input_file=body)


def statuses(state, cwd, slug: str, sha: str) -> list[dict]:
    """Gli stati del commit dal più recente: `context`, `state`, `creator.login`."""
    jq = ".[] | {context, state, creator: {login: .creator.login}}"
    return ghcli.api(state, cwd, f"repos/{slug}/commits/{_sha(sha)}/statuses?{_PER_PAGE}",
                     paginate=True, jq=jq).data


def issue(state, cwd, slug: str, n: int) -> IssueFacts | None:
    """L'issue `n`; `None` se non esiste o se il numero è quello di una PR."""
    got = ghcli.api(state, cwd, f"repos/{slug}/issues/{_number(n)}", include=True)
    if got.status == 404:
        return None
    data = got.data
    if got.status != 200 or not isinstance(data, dict):
        raise ghcli.GhError(f"issue {n}: risposta inattesa (HTTP {got.status})")
    if data.get("pull_request"):
        return None
    labels = tuple(x["name"] for x in data.get("labels") or []
                   if isinstance(x, dict) and isinstance(x.get("name"), str))
    return IssueFacts(n, str(data.get("state", "")).lower(), labels)


def pr_comments(state, cwd, slug: str, n: int) -> list[dict]:
    """I commenti della PR (REST): `id`, `user.login`, `body`."""
    jq = ".[] | {id, user: {login: .user.login}, body}"
    return ghcli.api(state, cwd, f"repos/{slug}/issues/{_number(n)}/comments?{_PER_PAGE}",
                     paginate=True, jq=jq).data


def upsert_comment(state, cwd, slug: str, n: int, *, prefix: str, body_file: Path) -> None:
    """Un solo commento del bot che comincia con `prefix` (decisione 14): se c'è lo riscrive, se
    no lo crea. Il testo viene dal file; un commento di un utente con lo stesso prefisso non
    conta."""
    for c in pr_comments(state, cwd, slug, n):
        login = (c.get("user") or {}).get("login")
        if login in ghcli.BOT_LOGINS and str(c.get("body", "")).lstrip().startswith(prefix):
            if not isinstance(c.get("id"), int):
                raise ghcli.GhError("commento senza id")
            ghcli.api(state, cwd, f"repos/{slug}/issues/comments/{c['id']}", method="PATCH",
                      file_fields={"body": body_file})
            return
    comment_issue(state, cwd, slug, n, body_file=body_file)


def comment_issue(state, cwd, slug: str, n: int, *, body_file: Path) -> None:
    """Un commento nuovo su una issue o una PR, col testo preso dal file."""
    ghcli.api(state, cwd, f"repos/{slug}/issues/{_number(n)}/comments", method="POST",
              file_fields={"body": body_file})


def create_issue(state, cwd, slug: str, *, title: str, body_file: Path) -> dict:
    """Crea una issue (`number`, `title`, `url`); il titolo lo scrive tollgate."""
    got = ghcli.api(state, cwd, f"repos/{slug}/issues", method="POST", fields={"title": title},
                    file_fields={"body": body_file})
    data = got.data
    if not isinstance(data, dict) or not isinstance(data.get("number"), int):
        raise ghcli.GhError("issue create: risposta inattesa")
    return {"number": data["number"], "title": title, "url": data.get("html_url", "")}


def prs_for_commit(state, cwd, slug: str, sha: str) -> list[dict]:
    """Le PR associate al commit (aperte con questa testa, o unite): `number`, `state`,
    `merged_at`, `base.ref`, `head.sha`."""
    jq = (".[] | {number, state, merged_at, base: {ref: .base.ref}, head: {sha: .head.sha}}")
    return ghcli.api(state, cwd, f"repos/{slug}/commits/{_sha(sha)}/pulls?{_PER_PAGE}",
                     paginate=True, jq=jq).data


def shared_sha_prs(state, cwd, slug: str, sha: str, default_branch: str) -> list[dict]:
    """Le PR aperte verso il ramo predefinito che hanno `sha` come testa (decisione 5): più di
    una vuol dire `error`. Un numero compare una volta sola."""
    seen, found = set(), []
    for pr in prs_for_commit(state, cwd, slug, sha):
        number = pr.get("number")
        if (pr.get("state") == "open" and (pr.get("base") or {}).get("ref") == default_branch
                and number not in seen):
            seen.add(number)
            found.append(pr)
    return found


def open_sentinel_issues(state, cwd, slug: str) -> list[dict]:
    """Le issue aperte «tollgate: merge non verificato» (`number`, `title`, `url`), con
    `--paginate`: niente limite di 100 (decisione 16). Le PR non contano."""
    jq = (f".[] | select(.pull_request == null and .title == {json.dumps(ghcli.SENTINEL_TITLE)})"
          " | {number, title, url: .html_url}")
    rows = ghcli.api(state, cwd, f"repos/{slug}/issues?state=open&{_PER_PAGE}", paginate=True,
                     jq=jq).data
    return [r for r in rows if r.get("title") == ghcli.SENTINEL_TITLE]
