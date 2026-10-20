"""I file di approvazione e i report di L2 letti dall'albero di un commit (spec 6.2, 8.7, 18.1).

Chi chiama sceglie il commit (decisione 13): la punta del ramo predefinito per `start --spec`,
HEAD per `finish check` e `open-pr`, la punta del ramo per `adopt`; mai il disco. Si legge il
testo solo dei file che servono, non di ogni file di ogni issue."""
from __future__ import annotations

from tollgate_analysis import approvals
from tollgate_core import git


def listing(repo, ref: str) -> list[str]:
    """Tutti i file sotto `docs/superpowers/reviews/` nell'albero di `ref`."""
    return git.ls_files_at(repo, ref, approvals.REVIEWS_DIR + "/")


def spec_approvals(repo, ref: str, paths=None) -> dict[str, str]:
    """`{percorso: testo}` di ogni `spec-approval.md` dell'albero, di qualunque issue."""
    paths = listing(repo, ref) if paths is None else paths
    return {p: git.text_at(repo, ref, p) or "" for p in approvals.approval_listing(paths)}


def locate(repo, ref: str, *, issue: int, spec_path: str, spec_blob: str | None
           ) -> tuple[str, dict] | None:
    """L'approvazione della spec nell'albero di `ref` (`approvals.locate_spec_approval`): legge
    solo i `spec-approval.md`, non i report."""
    return approvals.locate_spec_approval(spec_approvals(repo, ref), issue=issue,
                                          spec_path=spec_path, spec_blob=spec_blob)


def collect(repo, ref: str, *, issue: int, spec_path: str | None, spec_blob: str | None
            ) -> tuple[dict[str, str], tuple[str, dict] | None]:
    """I file per `approvals.check_l2` e l'approvazione della spec trovata (come
    `locate_spec_approval`, `None` se manca). `files` ha: le approvazioni delle spec, il
    `plan-approval.md` del lavoro, i report della cartella dell'approvazione trovata e della
    cartella del lavoro."""
    paths = listing(repo, ref)
    files = spec_approvals(repo, ref, paths)
    plan_approval = approvals.approval_paths(issue)[1]
    if plan_approval in paths:
        files[plan_approval] = git.text_at(repo, ref, plan_approval) or ""
    found = None
    if spec_path:
        found = approvals.locate_spec_approval(files, issue=issue, spec_path=spec_path,
                                               spec_blob=spec_blob)
    folders = {plan_approval.rpartition("/")[0]}
    if found is not None:
        folders.add(found[0].rpartition("/")[0])
    for p in approvals.report_listing(paths, folders):
        files[p] = git.text_at(repo, ref, p) or ""
    return files, found
