"""Identificativi di test della base (spec 9.5, decisione 12): `gate base-ids` esegue la suite
della base e scrive `ids.json`; `load` lo rilegge, solo se è dello stesso albero."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from tollgate_core import git, runner
from tollgate_core.config import load_config_at

from . import run as gate_run

IDS_VERSION = 1


def compute(repo: Path, *, config_sha: str, sha: str, out: Path, environ: Mapping[str, str],
            cfg_repo: Path | None = None) -> dict:
    """Esegue in `repo` (il checkout di `sha`) i comandi di `runner.ids_commands`, con la
    configurazione di `config_sha` letta in `cfg_repo` (di norma `repo`), e scrive
    `out/ids.json`. Un `setup` fallito lascia i comandi `red` e senza identificativi."""
    cfg = load_config_at(cfg_repo or repo, config_sha)
    tree = git.run(repo, "rev-parse", f"{sha}^{{tree}}").strip()
    specs = runner.ids_commands(cfg)
    setups = gate_run.setup_commands(cfg, list(cfg.profiles))
    entries = gate_run.run_commands(repo, cfg, setups, specs, files=[], environ=environ,
                                    out=out, tag=f"base-{sha[:7]}")
    ids, commands = {}, {}
    for spec, entry in zip(specs, entries[len(setups):]):
        junit = entry.get("_junit")
        ids[spec.name] = sorted(runner.executed_ids(junit)) if junit is not None else []
        commands[spec.name] = entry["state"]
    result = {"v": IDS_VERSION, "tree": tree, "sha": sha, "ids": ids, "commands": commands}
    out.mkdir(parents=True, exist_ok=True)
    (out / "ids.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def load(path: Path, *, tree: str) -> dict[str, set[str]] | None:
    """Gli identificativi per comando, `None` se il file è illeggibile, malformato o di un altro
    albero."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(data, dict) or data.get("v") != IDS_VERSION or data.get("tree") != tree:
        return None
    ids = data.get("ids")
    if not isinstance(ids, dict):
        return None
    out: dict[str, set[str]] = {}
    for name, values in ids.items():
        if (not isinstance(name, str) or not isinstance(values, list)
                or not all(isinstance(v, str) for v in values)):
            return None
        out[name] = set(values)
    return out
