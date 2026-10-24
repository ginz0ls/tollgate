"""`gate sentinel` (spec 9.3, decisione 16): dopo un push sul ramo predefinito controlla che ogni
commit arrivato venga da una PR unita la cui testa aveva `tollgate/guard` e `tollgate/verdict`
verdi, scritti dal bot di GitHub Actions. Se no, stato `tollgate/sentinel` rosso sul commit e un
commento sull'unica issue di sentinel (creata se manca). Nel testo di issue e commenti entrano
solo SHA, numeri di PR e motivi di tollgate: niente titoli né corpi.

Ogni push controllato lascia su `after` lo stato `success` «controllato fino a qui» (se `after`
non è rosso): il push successivo risale fino a lì, così i commit di un push saltato con
`[skip ci]` si controllano al push dopo."""
from __future__ import annotations

import json
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from tollgate_core import ghcli, git, paths
from tollgate_core.config import load_config_at

from . import github

WORKFLOW = ".github/workflows/tollgate-sentinel.yml"
CONTEXT = "tollgate/sentinel"
REQUIRED = ("tollgate/guard", "tollgate/verdict")
ATTEMPTS = 3        # `commits/<sha>/pulls` può restare vuoto per qualche secondo dopo il merge (V5)
WAIT_S = 5.0
_ZEROS = "0" * 40
NO_PR = "nessuna PR unita nel ramo predefinito contiene il commit"
CHECKED_DESCRIPTION = "controllato fino a qui"
WALK_LIMIT = 200    # commit risaliti in cerca del segnale: oltre, si riparte da `before`


FORCED = "push forzato: intervallo non calcolabile"


def _is_marker(row: dict) -> bool:
    """Uno stato `tollgate/sentinel` (di qualunque valore) scritto dal bot di GitHub Actions."""
    return row.get("context") == CONTEXT and \
        (row.get("creator") or {}).get("login") == ghcli.STATUS_BOT


def last_checked(repo: Path, after: str, statuses: Callable[[str], list[dict]], *,
                 limit: int = WALK_LIMIT) -> str | None:
    """Il primo commit con uno stato `tollgate/sentinel` del bot, risalendo da `after` (escluso)
    lungo il primo genitore, di qualunque valore: un `failure` vuol dire che è già stato
    controllato e segnalato. `None` se non c'è nessuno entro `limit` commit (una GET di stati per
    commit) o la storia finisce. Gli stati di altri utenti non contano: lo stato è per commit e
    chiunque con `statuses: write` potrebbe scriverlo."""
    sha = after
    for _ in range(limit):
        parent = git.resolve_ref(repo, f"{sha}^")
        if parent is None:
            return None
        if any(_is_marker(row) for row in statuses(parent)):
            return parent
        sha = parent
    return None


def _commits(repo: Path, before: str, after: str, statuses: Callable[[str], list[dict]]
             ) -> tuple[list[str], bool]:
    """I commit nuovi del push, dal più vecchio, e se il push è forzato. Con `before` tutto zeri
    (ramo nuovo) solo `after`. Un `before` che non si risolve o non è antenato di `after` (storia
    riscritta, ramo tornato indietro) è un push forzato: l'intervallo, se si calcola, vale
    comunque, ma `after` è non verificato. Altrimenti l'intervallo parte dall'ultimo commit
    controllato (`last_checked`), che arriva prima di `before` se un push è stato saltato; senza
    segnale entro `WALK_LIMIT` commit parte da `before`."""
    if before == _ZEROS:
        return [after], False
    if git.resolve_ref(repo, before) is None:
        return [after], True
    if not git.ok(repo, "merge-base", "--is-ancestor", before, after):
        return git.rev_list(repo, before, after), True
    return git.rev_list(repo, last_checked(repo, after, statuses) or before, after), False


def _introduces_workflow(repo: Path, sha: str) -> bool:
    parent = git.resolve_ref(repo, f"{sha}^")
    return git.exists_at(repo, sha, WORKFLOW) and not (
        parent is not None and git.exists_at(repo, parent, WORKFLOW))


def _first_install(repo: Path, commits: list[str]) -> set[str]:
    """I commit che introducono il workflow di sentinel e i loro antenati nel push: il primo push
    che lo installa non apre l'issue (criterio 34)."""
    introducers = [c for c in commits if _introduces_workflow(repo, c)]
    return {c for c in commits
            if any(git.ok(repo, "merge-base", "--is-ancestor", c, i) for i in introducers)}


def _pr_problem(pr: dict, statuses: Callable[[str], list[dict]]) -> str | None:
    """Perché la testa della PR unita non basta (`None` se è verificata). Per ogni contesto conta
    solo lo stato più recente, e solo se scritto da `github-actions[bot]`."""
    number = pr.get("number") if isinstance(pr.get("number"), int) else "?"
    try:
        rows = statuses((pr.get("head") or {}).get("sha"))
    except ValueError:
        return f"PR #{number}: testa non valida"
    latest: dict[str, dict] = {}
    for row in rows:                    # dal più recente
        context = row.get("context")
        if context in REQUIRED and context not in latest:
            latest[context] = row
    problems = []
    for context in REQUIRED:
        row = latest.get(context)
        if row is None:
            problems.append(f"{context} assente")
        elif row.get("state") != "success":
            problems.append(f"{context} {row.get('state')}")
        elif (row.get("creator") or {}).get("login") != ghcli.STATUS_BOT:
            problems.append(f"{context} non scritto da github-actions[bot]")
    return f"PR #{number}: {', '.join(problems)}" if problems else None


def _commit_problem(sha: str, default: str, prs_for_commit: Callable[[str], list[dict]],
                    statuses: Callable[[str], list[dict]], attempts: int, wait: float,
                    sleep: Callable[[float], object]) -> str | None:
    merged: list[dict] = []
    for attempt in range(attempts):
        merged = [p for p in prs_for_commit(sha)
                  if p.get("merged_at") and (p.get("base") or {}).get("ref") == default]
        if merged or attempt == attempts - 1:
            break
        sleep(wait)
    if not merged:
        return NO_PR
    problems = []
    for pr in merged:
        problem = _pr_problem(pr, statuses)
        if problem is None:             # basta una PR unita e verificata
            return None
        problems.append(problem)
    return "; ".join(problems)


def unverified(repo: Path, *, before: str, after: str,
               prs_for_commit: Callable[[str], list[dict]],
               statuses: Callable[[str], list[dict]], default_branch: str | None = None,
               attempts: int = ATTEMPTS, wait: float = WAIT_S,
               sleep: Callable[[float], object] = time.sleep) -> list[tuple[str, str]]:
    """I commit del push non verificati, con il motivo. Le funzioni di lettura sono parametri
    (nei test sono finte); `default_branch` è quello di `git.default_branch` se manca. Un elenco
    di PR vuoto si rilegge `attempts` volte, con `wait` secondi tra una e l'altra. L'intervallo
    parte dall'ultimo commit controllato (`last_checked`), non da `before`."""
    default = default_branch or git.default_branch(repo)
    if not default:
        raise git.GitError("ramo predefinito non determinabile")
    commits, forced = _commits(repo, before, after, statuses)
    skip = _first_install(repo, commits)
    found: dict[str, str] = {}
    for sha in commits:
        if sha in skip:
            continue
        reason = _commit_problem(sha, default, prs_for_commit, statuses, attempts, wait, sleep)
        if reason is not None:
            found[sha] = reason
    if forced:
        found[after] = "; ".join([FORCED, *([found[after]] if after in found else [])])
    return list(found.items())


def _body(found: list[tuple[str, str]]) -> str:
    lines = [f"- `{sha}`: {reason}" for sha, reason in found]
    return ("## tollgate: merge non verificato\n\nCommit arrivati sul ramo predefinito senza una "
            "PR unita con `tollgate/guard` e `tollgate/verdict` verdi:\n\n" + "\n".join(lines)
            + "\n\nChiudi l'issue su GitHub dopo averla letta.\n")


def run(event_path: Path, *, publish: bool, environ: Mapping[str, str], repo: Path | None = None,
        sleep: Callable[[float], object] = time.sleep, attempts: int = ATTEMPTS,
        wait: float = WAIT_S) -> int:
    """Controlla il push dell'evento. Senza `publish` stampa i commit non verificati (una stringa
    JSON per riga) e risponde 1 se ce ne sono, senza scrivere su GitHub. Con `publish` scrive lo
    stato rosso sui commit, il `success` «controllato fino a qui» su `after` se non è rosso, e
    segnala sull'issue di sentinel, poi risponde 0: il segnale sono lo stato e l'issue.
    Con `sentinel = false` nel `tollgate.toml` della punta esce subito."""
    repo = Path.cwd() if repo is None else repo
    event = github.read_event(event_path)
    ref, before, after = github.push_from_event(event)
    default = github.event_repo(event)[1]
    if ref != f"refs/heads/{default}" or after == _ZEROS:
        print(f"sentinel: il push non è su {default} (o cancella il ramo): niente da controllare")
        return 0
    if not load_config_at(repo, after).get("components.sentinel"):
        print("sentinel: componente disattivato (components.sentinel = false)")
        return 0
    state = paths.resolve_state(environ)
    # GITHUB_REPOSITORY serve solo a `--publish`; da leggere, il repository è quello dell'evento
    slug = github.repo_slug(
        environ if publish else {"GITHUB_REPOSITORY": github.event_repo(event)[0]})
    found = unverified(
        repo, before=before, after=after, default_branch=default,
        prs_for_commit=lambda sha: github.prs_for_commit(state, repo, slug, sha),
        statuses=lambda sha: github.statuses(state, repo, slug, sha),
        attempts=attempts, wait=wait, sleep=sleep)
    if not found:
        print("sentinel: tutti i commit del push vengono da una PR verificata")
    if not publish:
        for sha, reason in found:
            print(json.dumps(f"{sha}: {reason}", ensure_ascii=False))
        if found:
            print(f"sentinel: {len(found)} commit non verificati")
        return 1 if found else 0
    for sha, reason in found:           # prima gli stati, che sono il segnale; poi l'issue
        github.set_status(state, repo, slug, sha, context=CONTEXT, status="failure",
                          description=f"merge non verificato: {reason}")
    if after not in dict(found):        # il segnale «controllato fino a qui» per il push dopo
        github.set_status(state, repo, slug, after, context=CONTEXT, status="success",
                          description=CHECKED_DESCRIPTION)
    if not found:
        return 0
    with tempfile.TemporaryDirectory(prefix="tollgate-sentinel-") as tmp:
        body = Path(tmp) / "body.md"
        body.write_text(_body(found), encoding="utf-8")
        github.report_sentinel(state, repo, slug, body_file=body)
    return 0
