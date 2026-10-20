"""Violazioni di test-guard e scope su un intero diff (spec 7.4, 8.2): fonte unica per gli hook
(commit) e per `finish check`. Nessuna dipendenza da `Ctx`."""
from __future__ import annotations

import posixpath
from collections.abc import Mapping
from pathlib import Path

from tollgate_analysis import approvals, globs, profiles as prof, testguard, waivers
from tollgate_analysis.approvals import REVIEWS_DIR
from tollgate_analysis.testguard import DEFAULT_TEST_GLOBS, GuardConfig, Violation

from . import git, scope as scope_mod
from .config import Config, output_excludes

# Ordine delle fasi di un lavoro (phases.SEQUENCES): la spec si scrive in spec_audit e il
# piano in plan. Oltre quelle fasi la spec e il piano sono bloccati (6.2).
_ORDER = ("spec_audit", "plan", "approval", "execution", "review", "pr_open", "closed")


def _rank(phase: str | None) -> int:
    return _ORDER.index(phase) if phase in _ORDER else len(_ORDER)


def guard_config(cfg: Config, files) -> GuardConfig:
    tg = cfg.get("test_guard")
    profs = cfg.profiles
    active = prof.active_profiles(files, profs, cfg.get("profiles.active"))
    extra = lambda k: [x for n in active for x in profs[n].get(k, [])]  # noqa: E731
    commands = " ".join(str(v) for v in cfg.get("commands").values())
    return GuardConfig(
        test_globs=list(DEFAULT_TEST_GLOBS) + tg["test_globs"] + extra("test_globs"),
        fixture_globs=tg["fixture_globs"], ci_globs=tg["ci_globs"],
        verification_globs=tg["verification_globs"],
        verification_watch=tg["verification_watch"],
        skip_markers=tg["skip_markers"] + extra("skip_markers"),
        assert_markers=tg["assert_markers"] + extra("assert_markers"),
        js_form="jest" if "jest" in commands else "vitest")


def is_docs_md(rel: str | None) -> bool:
    return bool(rel) and rel.startswith("docs/superpowers/") and rel.endswith(".md")


def _approval_files(wt: Path) -> dict[str, str]:
    """`{percorso relativo: testo}` dei `spec-approval.md` presenti sul disco del worktree, anche
    di altre issue (fette successive, decisione 19). Illeggibili e collegamenti simbolici no."""
    out: dict[str, str] = {}
    folder = wt / REVIEWS_DIR
    try:
        found = sorted(folder.glob("*/spec-approval.md"))
    except OSError:
        return out
    for p in found:
        try:
            if p.is_symlink() or not p.is_file():
                continue
            out[p.relative_to(wt).as_posix()] = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return out


def locked_docs(work) -> set[str]:
    """Spec bloccata dopo approve spec, piano bloccato dopo la registrazione dello scope (6.2).
    Un lavoro in blocco vale la fase precedente al blocco. Un ritorno con reopen riporta la
    fase alla spec o al piano, e quei file tornano modificabili (l'approvazione resta storica).
    """
    phase = work["phase_before_block"] if work["phase"] == "blocked" else work["phase"]
    out = set()
    if work["plan_sha"] and work["plan_path"] and _rank(phase) > _rank("plan"):
        out.add(work["plan_path"])
    if work["spec_path"] and work["worktree"] and _rank(phase) > _rank("spec_audit") \
            and approvals.locate_spec_approval(
                _approval_files(Path(work["worktree"])), issue=work["issue"],
                spec_path=work["spec_path"], spec_blob=None) is not None:
        out.add(work["spec_path"])
    return out


def active_profile_names(cfg: Config, wt: Path, work, *, head: str | None = None) -> list[str]:
    """I profili attivi sul diff del lavoro (dalla base del lavoro, o da `default_ref` se manca,
    fino a `head` o alla punta del worktree), senza i file cancellati. Sta qui perché la usano
    sia `review prepare` sia l'applicazione dei riporti degli hook. Senza base né
    `default_ref`, o senza nessun commit (`head` nullo): nessun profilo, perché `changes` senza
    `head` includerebbe working tree e file non tracciati. Un diff illeggibile solleva
    `git.GitError`."""
    base = work["work_base_sha"] or git.default_ref(wt)
    tip = head or git.head(wt)
    if base is None or tip is None:
        return []
    files = [c.path for c in git.changes(wt, base, head=tip) if c.status != "D"]
    return prof.active_profiles(files, cfg.profiles, cfg.get("profiles.active"))


def scope_exempt(cfg: Config, work, rel: str, scope: set[str], *,
                 locked: set[str] | None = None) -> bool:
    """Esenzioni dallo scope (7.4); quella di `docs/superpowers/reviews/<N>/` (report e
    approvazioni del lavoro) vale a ogni livello, non solo in L2. I percorsi di `scope` sono nomi letterali (possono
    contenere `[ ]`): si confrontano per uguaglianza, mai come pattern. Solo `[scope] always`
    è fatto di pattern. `locked` sono i documenti bloccati (`locked_docs`): chi esamina molti
    file lo calcola una volta sola e lo passa."""
    if rel.startswith(".superpowers/") or rel == f".tollgate/waivers/{work['issue']}.toml":
        return True
    # I report e le approvazioni del lavoro li scrivono solo la CLI e gli hook e il
    # coordinatore li committa con spec e piano (decisione 26).
    if rel.startswith(f"{REVIEWS_DIR}/{work['issue']}/"):
        return True
    if git.excluded(rel, output_excludes(cfg)):
        return True
    if is_docs_md(rel) and not rel.startswith(f"{REVIEWS_DIR}/") \
            and rel not in (locked_docs(work) if locked is None else locked):
        return True
    if globs.match_any(cfg.get("scope.always"), rel):
        return True
    manifest = cfg.get("scope.lockfiles").get(posixpath.basename(rel))
    return bool(manifest and posixpath.join(posixpath.dirname(rel), manifest) in scope)


def is_registered_plan(work, wt: Path, path: str, head_ref: str | None) -> bool:
    """Il piano registrato, tale e quale (stesso blob di `plan_sha`): è bloccato, ma committarlo
    non lo modifica (lo fa il coordinatore dopo la registrazione)."""
    if path != work["plan_path"] or not work["plan_sha"] or (wt / path).is_symlink():
        return False
    try:
        sha = git.blob_sha(wt, path) if head_ref is None \
            else git.run(wt, "rev-parse", f"{head_ref}:{path}").strip()
    except git.GitError:
        return False
    return sha == work["plan_sha"]


def waiver_file(work) -> waivers.WaiverFile | None:
    if work is None or not work["worktree"]:
        return None
    p = Path(work["worktree"]) / waivers.path_for(work["issue"])
    try:
        return waivers.parse(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def diff_violations(cfg: Config, conn, work, wt: Path, base_ref: str, head_ref: str | None,
                    changes, *, components: Mapping[str, bool]) -> list[Violation]:
    """Violazioni di test-guard e scope su `changes` (da `base_ref` a `head_ref`; `None` è il
    working tree), senza le cartelle di output e `.tollgate-run/`. Restano solo quelle non
    coperte da una deroga, anche in attesa (decisione 9). Un componente assente è acceso."""
    skip = output_excludes(cfg)
    changes = [c for c in changes if not git.excluded(c.path, skip)]
    out: list[Violation] = []
    if components.get("test_guard", True):
        tg = []
        for c in changes:
            base_text = None if c.status == "A" else git.text_at(wt, base_ref,
                                                                 c.old_path or c.path)
            if c.status == "D":
                head_text = None
            elif head_ref is None:
                head_text = git.worktree_text(wt, c.path)
            else:
                head_text = git.text_at(wt, head_ref, c.path)
            tg.append(testguard.Change(c.status, c.path, c.old_path, base_text, head_text,
                                       c.binary))
        out += testguard.check(tg, guard_config(cfg, [c.path for c in changes])).violations
    if components.get("scope_check", True) and work["level"] != "L0" and work["plan_sha"]:
        scope = scope_mod.paths(conn, work["id"])
        locked = locked_docs(work)
        for c in changes:
            if c.path not in scope and not scope_exempt(cfg, work, c.path, scope, locked=locked) \
                    and not is_registered_plan(work, wt, c.path, head_ref):
                out.append(Violation("out_of_scope", c.path, "file fuori dallo scope del piano",
                                     "scope"))
    return waivers.unresolved(out, waiver_file(work))
