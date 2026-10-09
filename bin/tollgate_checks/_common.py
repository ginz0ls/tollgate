"""Aiuti condivisi dai controlli (non è un controllo: il registro salta i nomi con _)."""
from __future__ import annotations

import re
from pathlib import Path

from tollgate_core import git
from tollgate_core.paths import repo_key

_TG = re.compile(r"^tg/(\d+)-")


def repo_key_of(repo) -> str | None:
    url = git.origin_url(repo) if repo else None
    return repo_key(url) if url else None


def orphan_tg(ctx, repo) -> int | None:
    """Ramo tg/<N>-* senza lavoro attivo per (repo, N): DB perso, serve adopt (12.4)."""
    if repo is None:
        return None
    m = _TG.match(git.branch(repo) or "")
    if not m:
        return None
    key = repo_key_of(repo)
    row = ctx.db.execute("SELECT 1 FROM work_items WHERE repo_key = ? AND issue = ? "
                         "AND phase <> 'closed'", (key, int(m.group(1)))).fetchone()
    return None if row else int(m.group(1))


def governing_work(ctx, path):
    """Le regole complete valgono nella sessione legata e per ogni percorso nel worktree (6.6)."""
    if ctx.bound and ctx.work is not None:
        return ctx.work
    return ctx.work_for_path(path) if path is not None else None


def is_docs_md(rel: str | None) -> bool:
    return bool(rel) and rel.startswith("docs/superpowers/") and rel.endswith(".md")


def locked_docs(work) -> set[str]:
    """Spec bloccata dopo approve spec, piano bloccato dopo la registrazione dello scope (6.2)."""
    out = set()
    if work["plan_sha"] and work["plan_path"]:
        out.add(work["plan_path"])
    if work["spec_path"] and work["worktree"]:
        approval = Path(work["worktree"]) / f"docs/superpowers/reviews/{work['issue']}" \
                                           "/spec-approval.md"
        if approval.exists():
            out.add(work["spec_path"])
    return out


def waiver_hint(v, issue) -> str:
    target = f"--test {' --test '.join(v.ids)} " if v.ids else ""
    return (f"tollgate waiver add {v.waiver_type} {v.path} {target}"
            f"--choice … --why … --cost …")


def explain(violations, issue) -> str:
    lines = [f"- {v.path}: {v.detail} (deroga: {waiver_hint(v, issue)})" for v in violations]
    return "\n".join(lines)


def status_lines(ctx, work) -> list[str]:
    lines = [f"tollgate: lavoro #{work['issue']} ({work['level']}), fase {work['phase']}"
             + (f" (prima: {work['phase_before_block']})" if work["phase"] == "blocked" else "")]
    for b in ctx.db.execute("SELECT id, type, reason FROM blocks WHERE work = ? AND closed "
                            "IS NULL ORDER BY id LIMIT 3", (work["id"],)):
        lines.append(f"blocco {b['id']} ({b['type']}): {b['reason'][:120]}")
    counts = {r[0]: r[1] for r in ctx.db.execute(
        "SELECT state, count(*) FROM tasks WHERE work = ? GROUP BY state", (work["id"],))}
    if counts:
        lines.append("task: " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    return lines
