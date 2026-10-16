"""Contesto in sola lettura dei controlli (spec 3.2)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tollgate_analysis import profiles as prof, waivers
from tollgate_analysis.testguard import DEFAULT_TEST_GLOBS, GuardConfig

from tollgate_core import config, git, scope, sessions
from tollgate_core.config import Config
from tollgate_core.paths import State

from .model import Event


class ReadDb:
    """Il DB visto dai controlli: solo SELECT (un modulo non scrive mai, spec 3.2)."""
    in_transaction = False

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=()):
        if not sql.lstrip().upper().startswith("SELECT"):
            raise PermissionError("il contesto dei controlli è in sola lettura")
        return self._conn.execute(sql, params)


@dataclass
class Ctx:
    event: Event
    state: State
    db: ReadDb
    config: Config
    repo: Path | None
    work: object | None
    bound: bool
    now: object
    plugin_root: Path

    def cfg(self, dotted: str):
        return self.config.get(dotted)

    def component(self, name: str) -> bool:
        return bool(self.config.data["components"].get(name, True))

    def readonly(self, agent_type: str | None) -> bool:
        return config.is_readonly(self.config, agent_type)

    @property
    def stale_minutes(self) -> int:
        return self.cfg("review.stale_minutes")

    @property
    def plugin_bin(self) -> Path:
        return self.plugin_root / "bin" / "tollgate"

    def work_for_path(self, path):
        return sessions.work_for_path(self.db, path)

    @staticmethod
    def rel(path, root) -> str | None:
        try:
            return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return None

    def waiver_file(self, work):
        if work is None or not work["worktree"]:
            return None
        p = Path(work["worktree"]) / waivers.path_for(work["issue"])
        try:
            return waivers.parse(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def approved_waivers(self, work) -> set[str]:
        """Decisione 10: un approve waiver vale in ogni stato dell'atto."""
        if work is None:
            return set()
        return {r[0] for r in self.db.execute(
            "SELECT target FROM acts WHERE type = 'approve' AND object = 'waiver' "
            "AND work = ? AND target IS NOT NULL", (work["id"],))}

    def scope(self, work) -> set[str]:
        return scope.paths(self.db, work["id"]) if work is not None else set()

    def guard_config(self, work, files) -> GuardConfig:
        tg = self.cfg("test_guard")
        profs = self.config.profiles
        active = prof.active_profiles(files, profs, self.cfg("profiles.active"))
        extra = lambda k: [x for n in active for x in profs[n].get(k, [])]  # noqa: E731
        commands = " ".join(str(v) for v in self.cfg("commands").values())
        return GuardConfig(
            test_globs=list(DEFAULT_TEST_GLOBS) + tg["test_globs"] + extra("test_globs"),
            fixture_globs=tg["fixture_globs"], ci_globs=tg["ci_globs"],
            verification_globs=tg["verification_globs"],
            verification_watch=tg["verification_watch"],
            skip_markers=tg["skip_markers"] + extra("skip_markers"),
            assert_markers=tg["assert_markers"] + extra("assert_markers"),
            js_form="jest" if "jest" in commands else "vitest")

    def protected_roots(self, repo) -> list[Path]:
        home = Path(os.path.expanduser("~"))
        roots = [self.state.root.resolve(), (home / ".claude" / "plugins").resolve(),
                 home / ".claude" / "settings.json", home / ".claude" / "settings.local.json"]
        # Anche con la cartella personale raggiunta da un collegamento (forma risolta).
        roots += [home.resolve() / ".claude" / n for n in ("settings.json", "settings.local.json")]
        if repo is not None:
            try:
                common = git.common_dir(repo)
                roots += [common / "hooks", common / "config"]
            except git.GitError:
                pass
        return roots
