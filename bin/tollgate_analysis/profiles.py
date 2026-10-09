"""Profili: verticale di un file, profili attivi, skill di un task (spec 6.3, 9.2, 11.4)."""
from __future__ import annotations

from . import globs

_LEVELS = ("L0", "L1", "L2")


def _score(path: str, patterns) -> int | None:
    scores = [globs.literal_segments(p) for p in patterns if globs.match(p, path)]
    return max(scores) if scores else None


def vertical_for(path: str, profiles: dict[str, dict]) -> str | None:
    """Vince il pattern con più segmenti letterali; a parità il primo dichiarato."""
    best, best_score = None, -1
    for name, prof in profiles.items():
        if prof.get("kind", "vertical") != "vertical":
            continue
        s = _score(path, prof.get("paths", []))
        if s is not None and s > best_score:
            best, best_score = name, s
    return best


def active_profiles(files, profiles: dict[str, dict], always) -> list[str]:
    files = list(files)
    return [name for name, prof in profiles.items()
            if name in always or any(globs.match_any(prof.get("paths", []), f) for f in files)]


def task_skills(files, profiles: dict[str, dict]) -> list[str]:
    skills: list[str] = []
    for f in files:
        name = vertical_for(f, profiles)
        if name:
            for s in profiles[name].get("skills", []):
                if s not in skills:
                    skills.append(s)
    return skills


def min_level(names, profiles: dict[str, dict]) -> str:
    level = "L0"
    for n in names:
        lv = profiles.get(n, {}).get("min_level", "L0")
        if lv in _LEVELS and _LEVELS.index(lv) > _LEVELS.index(level):
            level = lv
    return level
