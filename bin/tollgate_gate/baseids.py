"""Identificativi di test della base (spec 9.5, decisione 12): `gate base-ids` esegue la suite
della base e scrive `ids.json`; `load` lo rilegge, solo se è dello stesso albero. `gate
base-publish` pubblica `tollgate/base` da quel file senza eseguire codice del progetto."""
from __future__ import annotations

import json
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from tollgate_core import git, paths, runner
from tollgate_core.config import ConfigError, load_config_at

from . import github
from . import run as gate_run

IDS_VERSION = 1
MAX_IDS_FILE = 50 * 2**20
CONTEXT = "tollgate/base"
DESC_INVALID = "identificativi della base assenti o non validi"
DESC_ERROR = "errore nella lettura della configurazione o dell'albero della base"
DESC_COMPONENT_OFF = "componente base_test_ids spento"


def compute(repo: Path, *, config_sha: str, sha: str, out: Path, environ: Mapping[str, str],
            cfg_repo: Path | None = None) -> dict:
    """Esegue in `repo` (il checkout di `sha`) i comandi di `runner.ids_commands`, con la
    configurazione di `config_sha` letta in `cfg_repo` (di norma `repo`), e scrive
    `out/ids.json`. Un `setup` fallito lascia i comandi `red` e senza identificativi. Con il
    componente `base_test_ids` spento (decisione 12) non esegue nulla e scrive un `ids.json`
    valido senza comandi: `base-publish` lo accetta e `verdict` non trova identificativi."""
    cfg = load_config_at(cfg_repo or repo, config_sha)
    tree = git.run(repo, "rev-parse", f"{sha}^{{tree}}").strip()
    ids, commands = {}, {}
    if cfg.get("components.base_test_ids"):
        specs = runner.ids_commands(cfg)
        setups = gate_run.setup_commands(cfg, list(cfg.profiles))
        entries = gate_run.run_commands(repo, cfg, setups, specs, files=[], environ=environ,
                                        out=out, tag=f"base-{sha[:7]}")
        for spec, entry in zip(specs, entries[len(setups):]):
            junit = entry.get("_junit")
            ids[spec.name] = sorted(runner.executed_ids(junit)) if junit is not None else []
            commands[spec.name] = entry["state"]
    result = {"v": IDS_VERSION, "tree": tree, "sha": sha, "ids": ids, "commands": commands}
    out.mkdir(parents=True, exist_ok=True)
    (out / "ids.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


@dataclass(frozen=True)
class BaseIds:
    """`ids.json` riletto: gli identificativi per comando e lo stato con cui la base ha eseguito
    ogni comando (`commands`, vuoto se il file non lo porta)."""
    ids: dict[str, set[str]]
    commands: dict[str, str]


def load(path: Path, *, tree: str) -> dict[str, set[str]] | None:
    """Gli identificativi per comando, `None` se il file è illeggibile, malformato o di un altro
    albero."""
    full = load_full(path, tree=tree)
    return None if full is None else full.ids


def load_full(path: Path, *, tree: str) -> BaseIds | None:
    """Come `load`, con anche gli stati dei comandi (decisione 14). `None` se il file è
    illeggibile, malformato, di un altro albero o con `commands` che non è una mappa di stati
    noti."""
    try:
        return _load(path, tree)
    except Exception:   # confine fail-closed su dati non fidati: illeggibile = assente
        return None


def _load(path: Path, tree: str) -> BaseIds | None:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
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
    commands = data.get("commands", {})
    if not isinstance(commands, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and v in gate_run.STATES
            for k, v in commands.items()):
        return None
    return BaseIds(out, dict(commands))


def publish(repo: Path, *, config_sha: str, sha: str, result: dict,
            environ: Mapping[str, str]) -> int:
    """In `detect` pubblica `tollgate/base` sul commit `sha` (spec 9.1): `failure` se qualche
    comando della suite della base è `red`, e allora commenta anche l'issue di sentinel (la crea
    se manca). In `protected` non scrive nulla. In entrambe le modalità risponde 1 se la suite è
    rossa, così il job `tollgate-base` è rosso, e 0 se è verde."""
    return _publish(repo, load_config_at(repo, config_sha), sha=sha, result=result,
                    environ=environ)


def _red(result: dict) -> list[str]:
    return sorted(name for name, st in result["commands"].items() if st == "red")


def _publish(repo: Path, cfg, *, sha: str, result: dict, environ: Mapping[str, str]) -> int:
    red = _red(result)
    if cfg.get("gate.mode") != "detect":
        return 1 if red else 0
    state, slug = paths.resolve_state(environ), github.repo_slug(environ)
    if not cfg.get("components.base_test_ids"):    # `ids.json` è vuoto: non c'è una suite da dire
        github.set_status(state, repo, slug, sha, context=CONTEXT, status="success",
                          description=DESC_COMPONENT_OFF)
        return 0
    open_ = sorted(name for name, st in result["commands"].items() if st == "unverified")
    extra = f"; non verificati: {', '.join(open_)}" if open_ else ""
    if not red:
        github.set_status(state, repo, slug, sha, context=CONTEXT, status="success",
                          description=f"suite della base verde{extra}")
        return 0
    github.set_status(state, repo, slug, sha, context=CONTEXT, status="failure",
                      description=f"suite della base rossa: {len(red)} comandi{extra}")
    with tempfile.TemporaryDirectory(prefix="tollgate-base-") as tmp:
        body = Path(tmp) / "body.md"
        body.write_text(
            "## tollgate: merge non verificato\n\nLa suite della base è rossa sul commit "
            f"`{sha}`. Comandi rossi: {', '.join(f'`{n}`' for n in red)}.\n\n"
            "Chiudi l'issue su GitHub dopo averla letta.\n", encoding="utf-8")
        github.report_sentinel(state, repo, slug, body_file=body)
    return 1


def read_result(path: Path, *, tree: str, names: set[str]) -> dict | None:
    """Il risultato di `ids.json` per `publish`, `None` se il file è assente, un collegamento
    simbolico, troppo grande, malformato, di un altro albero, o ha comandi che la configurazione
    non conosce o stati fuori da `run.STATES`. Il file viene da un job che esegue codice del
    progetto: nulla del suo testo entra in uno stato o in un commento se non è tra i `names`."""
    try:
        p = Path(path)
        if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_IDS_FILE:
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("v") != IDS_VERSION or data.get("tree") != tree:
            return None
        commands = data.get("commands")
        if not isinstance(commands, dict) or not set(commands) <= names:
            return None
        if not all(isinstance(v, str) and v in gate_run.STATES for v in commands.values()):
            return None
        return {"commands": dict(commands)}
    except Exception:   # confine fail-closed su dati non fidati: illeggibile = assente
        return None


def publish_from(repo: Path, *, config_sha: str, sha: str, ids_dir: Path,
                 environ: Mapping[str, str], publish: bool) -> int:
    """Pubblica da `ids_dir/ids.json` (l'artefatto di `ids`, dati non fidati) come `publish`.
    Il file deve essere dell'albero di `sha` (su un cache hit il suo `sha` è un altro commit con
    lo stesso albero). Se non è valido: in `detect` stato `error` con il motivo, e codice 1 in
    ogni modalità, così il job è rosso; lo stesso codice 1 se la suite della base è rossa. Lo stesso
    se la lettura dell'albero o dei comandi dà `ConfigError` o `GitError` (la configurazione della
    punta, invece, deve leggersi: senza non si conosce la modalità). Senza `publish` legge e
    basta."""
    cfg = load_config_at(repo, config_sha)
    try:
        tree = git.run(repo, "rev-parse", f"{sha}^{{tree}}").strip()
        names = {spec.name for spec in runner.ids_commands(cfg)}
    except (ConfigError, git.GitError) as e:
        return _invalid(cfg, repo, sha, environ, publish, DESC_ERROR,
                        log=json.dumps(str(e), ensure_ascii=False))
    result = read_result(Path(ids_dir) / "ids.json", tree=tree, names=names)
    if result is None:
        return _invalid(cfg, repo, sha, environ, publish, DESC_INVALID)
    if publish:
        return _publish(repo, cfg, sha=sha, result=result, environ=environ)
    return 1 if _red(result) else 0


def _invalid(cfg, repo: Path, sha: str, environ: Mapping[str, str], publish: bool,
             description: str, *, log: str | None = None) -> int:
    """Gli identificativi non si possono usare: in `detect` stato `error`, in ogni modalità
    uscita 1, così il job `tollgate-base` è rosso (in `protected` il segnale è il job)."""
    sys.stderr.write(f"base-publish: {description if log is None else log}\n")
    if publish and cfg.get("gate.mode") == "detect":
        github.set_status(paths.resolve_state(environ), repo, github.repo_slug(environ), sha,
                          context=CONTEXT, status="error", description=description)
    return 1
