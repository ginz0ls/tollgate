"""Frammenti di profilo (`templates/profiles/<area>.toml`): il profilo verticale di un'area
senza le regole, che `init` completa con quelle estratte dalla skill (B3, decisioni 2-5)."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from tollgate_analysis import research
from tollgate_core import config

FRAGMENTS_DIR = ("templates", "profiles")
RESERVED = ("base", "active")
_AREA = re.compile(r"[a-z0-9-]+")
# Fino a B4 un frammento accetta solo pattern `**/<cartella>/**` (decisione 5).
_PATTERN = re.compile(r"\*\*/(?!\.{1,2}/)([^/*?\[\]!\\]+)/\*\*")
_FORBIDDEN_KEYS = ("rules", "blocking_rules")


class FragmentError(ValueError):
    """Frammento illeggibile o non valido; il messaggio nomina il file."""


@dataclass(frozen=True)
class Fragment:
    area: str
    profile: dict
    detect: tuple[str, ...]
    skill_path: Path
    source: Path


def _parse(path: Path, plugin_root: Path) -> Fragment:
    area = path.stem
    name = path.name
    if not _AREA.fullmatch(area):
        raise FragmentError(f"{name}: nome d'area non valido (ammesso [a-z0-9-]+)")
    if area in RESERVED:
        raise FragmentError(f"{name}: «{area}» è un nome riservato")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise FragmentError(f"{name}: illeggibile: {e}") from e
    unknown = sorted(set(raw) - {"profile", "detect"})
    if unknown:
        raise FragmentError(f"{name}: sezione sconosciuta: {', '.join(unknown)}")
    profile = raw.get("profile", {})
    detect = raw.get("detect", {})
    if not isinstance(profile, dict) or not isinstance(detect, dict):
        raise FragmentError(f"{name}: [profile] e [detect] devono essere tabelle")
    for key in profile:
        if key in _FORBIDDEN_KEYS:
            raise FragmentError(f"{name}: [profile] non ha «{key}»: le calcola init dalla skill")
        if key not in config.PROFILE_DEFAULTS:
            raise FragmentError(f"{name}: chiave sconosciuta in [profile]: {key}")
        if key != "paths":  # `paths` ha il suo controllo, più stretto, qui sotto
            try:
                config._set_key({}, key, profile[key], config.PROFILE_DEFAULTS[key],
                                key, f"profiles.*.{key}")
            except config.ConfigError as e:
                raise FragmentError(f"{name}: [profile] {e}") from e
    paths = profile.get("paths", [])
    if not isinstance(paths, list) or not all(
            isinstance(p, str) and _PATTERN.fullmatch(p) for p in paths):
        raise FragmentError(f"{name}: i pattern di paths devono avere la forma **/<cartella>/**")
    extra = sorted(set(detect) - {"content"})
    if extra:
        raise FragmentError(f"{name}: chiave sconosciuta in [detect]: {', '.join(extra)}")
    content = detect.get("content", [])
    if not isinstance(content, list) or not all(isinstance(c, str) and c for c in content):
        raise FragmentError(f"{name}: [detect] content deve essere una lista di stringhe")
    if not paths:
        raise FragmentError(f"{name}: [profile] paths è obbligatorio e non vuoto "
                            f"(senza, il profilo si accenderebbe su ogni file)")
    skill = plugin_root / "skills" / f"rules-{area}" / "SKILL.md"
    return Fragment(area, profile, tuple(content), skill, path)


def load(plugin_root) -> list[Fragment]:
    """I frammenti del plugin, ordinati per area; cartella assente: nessun frammento."""
    root = Path(plugin_root)
    directory = root.joinpath(*FRAGMENTS_DIR)
    if not directory.is_dir():
        return []
    return [_parse(p, root) for p in sorted(directory.glob("*.toml")) if p.is_file()]


def _skill_text(fragment: Fragment) -> str | None:
    try:
        return fragment.skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def approved(fragment: Fragment) -> bool:
    """Vero se la skill dell'area ha `approved` (decisione 4); skill assente: falso."""
    return research.enforced(_skill_text(fragment))


def rules(fragment: Fragment) -> tuple[list[str], list[str]]:
    """`(rules, blocking_rules)` ordinate, dalle righe `R-<AREA>-NN` della skill."""
    known, blocking = research.area_rules(_skill_text(fragment) or "", fragment.area)
    return sorted(known), sorted(blocking)
