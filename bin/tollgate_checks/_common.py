"""Aiuti condivisi dai controlli (non è un controllo: il registro salta i nomi con _)."""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path

from tollgate_analysis import globs, level as lv, profiles as prof
from tollgate_core import git
from tollgate_core.paths import repo_key
from tollgate_hooks.adapter import edit_path
from tollgate_hooks.model import inject, record

_TG = re.compile(r"^tg/(\d+)-")


def _inside(p, root) -> bool:
    """`p` è `root` o sta sotto `root` (percorsi già assoluti e risolti)."""
    p, root = Path(p), Path(root)
    return p == root or root in p.parents


def edit_target(event) -> Path | None:
    """Percorso assoluto e risolto (collegamenti compresi) che Edit o Write toccherebbe.
    Si decide sul percorso vero: un collegamento nel worktree non aggira scope né protezioni."""
    raw = edit_path(event)
    if not raw:
        return None
    p = Path(raw)
    return (p if p.is_absolute() else event.cwd / p).resolve()


def output_excludes(ctx) -> list[str]:
    """Cartelle di output (report, copertura, `.tollgate-run/`): fuori da livello e scope."""
    return list(ctx.cfg("review.output_dirs")) + [".tollgate-run/"]


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
    if key is None:
        return None
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


# Ordine delle fasi di un lavoro (phases.SEQUENCES): la spec si scrive in spec_audit e il
# piano in plan. Oltre quelle fasi la spec e il piano sono bloccati (6.2).
_ORDER = ("spec_audit", "plan", "approval", "execution", "review", "pr_open", "closed")


def _rank(phase: str | None) -> int:
    return _ORDER.index(phase) if phase in _ORDER else len(_ORDER)


def locked_docs(work) -> set[str]:
    """Spec bloccata dopo approve spec, piano bloccato dopo la registrazione dello scope (6.2).
    Un lavoro in blocco vale la fase precedente al blocco. Un ritorno con reopen riporta la
    fase alla spec o al piano, e quei file tornano modificabili (l'approvazione resta storica).
    """
    phase = work["phase_before_block"] if work["phase"] == "blocked" else work["phase"]
    out = set()
    if work["plan_sha"] and work["plan_path"] and _rank(phase) > _rank("plan"):
        out.add(work["plan_path"])
    if work["spec_path"] and work["worktree"] and _rank(phase) > _rank("spec_audit"):
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


def scope_exempt(ctx, work, rel: str, scope: set[str]) -> bool:
    """Esenzioni dallo scope (7.4). I percorsi di `scope` sono nomi letterali (possono
    contenere `[ ]`): si confrontano per uguaglianza, mai come pattern. Solo `[scope] always`
    è fatto di pattern."""
    if rel.startswith(".superpowers/") or rel == f".tollgate/waivers/{work['issue']}.toml":
        return True
    if git.excluded(rel, output_excludes(ctx)):
        return True
    if is_docs_md(rel) and not rel.startswith("docs/superpowers/reviews/") \
            and rel not in locked_docs(work):
        return True
    if globs.match_any(ctx.cfg("scope.always"), rel):
        return True
    manifest = ctx.cfg("scope.lockfiles").get(posixpath.basename(rel))
    return bool(manifest and posixpath.join(posixpath.dirname(rel), manifest) in scope)


def level_records(ctx, work) -> list:
    """Ricalcolo del livello sul diff dalla base, working tree e file nuovi compresi
    (decisione 18), senza le cartelle di output. Il livello sale e non scende mai."""
    wt = Path(work["worktree"]) if work["worktree"] else None
    base = work["work_base_sha"]
    if not base or wt is None or not wt.is_dir():
        return []
    skip = output_excludes(ctx)
    changes = git.changes(wt, base, exclude=skip)
    cfg = ctx.cfg("levels")
    paths = [c.path for c in changes] + [c.old_path for c in changes if c.old_path]
    computed = lv.diff_level(changes, diff_bytes=git.diff_size(wt, base, exclude=skip),
                             sensitive_paths=cfg["sensitive_paths"],
                             l0_max_files=cfg["l0_max_files"], l0_max_lines=cfg["l0_max_lines"],
                             l0_max_bytes=cfg["l0_max_bytes"])
    profs = ctx.config.profiles
    computed = lv.max_level(computed, prof.min_level(
        prof.active_profiles(paths, profs, ctx.cfg("profiles.active")), profs))
    new = lv.next_level(current=work["level"], computed=computed, cap=work["level_cap"],
                        cap_paths=json.loads(work["level_cap_paths"] or "[]"),
                        sensitive_now=lv.sensitive_in(paths, cfg["sensitive_paths"]))
    if new == work["level"]:
        return []
    if work["level"] == "L0" and work["phase"] == "execution":
        out = [record("phase", work=work["id"], to="plan", cause="l0_grew")]
        if new == "L2":
            out.append(record("level", work=work["id"], level="L2"))
        out.append(inject(f"tollgate: il diff supera le soglie di L0: il lavoro sale a {new} e "
                          f"torna in fase plan. Serve un piano (writing-plans)."))
        return out
    return [record("level", work=work["id"], level=new),
            inject(f"tollgate: il lavoro sale a {new} (percorsi sensibili o soglie).")]
