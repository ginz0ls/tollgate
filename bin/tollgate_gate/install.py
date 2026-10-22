"""I file del gate da installare nel repo del progetto (spec 9.1, decisione 17): i cinque
workflow, la copia del CLI in `.github/tollgate/bin/`, `VERSION` e `FINGERPRINT`."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from tollgate_core import VERSION

WORKFLOWS_DIR = "gate/workflows"
WORKFLOW_NAMES = ("guard", "run", "verdict", "base", "sentinel")
INSTALL_DIR = ".github/tollgate"
BRANCH_PLACEHOLDER = "__DEFAULT_BRANCH__"
SERVICES_MARKER = "# __SERVICES__"

# valori che finiscono in YAML senza virgolette: solo caratteri che YAML legge come testo semplice
_BRANCH = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._/-]*$")
_SERVICE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]*$")
_IMAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:@-]*$")


def _sources(bin_root: Path) -> list[Path]:
    """I file di `bin_root` senza cache di Python, in ordine stabile."""
    return sorted(p for p in Path(bin_root).rglob("*")
                  if p.is_file() and "__pycache__" not in p.relative_to(bin_root).parts
                  and p.suffix != ".pyc")


def fingerprint(bin_root: Path) -> str:
    """`sha256` del contenuto di `bin_root` (percorsi relativi e byte), senza `__pycache__`."""
    digest = hashlib.sha256()
    for path in _sources(bin_root):
        rel = path.relative_to(bin_root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(rel).to_bytes(8, "big") + rel + len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def _services_block(services: dict[str, str], ports: dict[str, int]) -> str:
    unknown = sorted(set(ports) - set(services))
    if unknown:
        raise ValueError(f"porta per un servizio non dichiarato: {unknown[0]!r}")
    lines = ["    services:"]
    for name, image in services.items():
        if not _SERVICE_NAME.match(name):
            raise ValueError(f"nome di servizio non valido: {name!r}")
        if not _IMAGE.match(image):
            raise ValueError(f"immagine del servizio {name!r} non valida: {image!r}")
        lines += [f"      {name}:", f"        image: {image}"]
        if name in ports:
            port = ports[name]
            if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
                raise ValueError(f"porta del servizio {name!r} non valida: {port!r}")
            # i servizi girano in container sull'host del job: senza `ports` il job non li raggiunge
            lines += ["        ports:", f'          - "{port}:{port}"']
    return "\n".join(lines)


def _render(name: str, text: str, default_branch: str, services: dict[str, str],
            ports: dict[str, int]) -> str:
    text = text.replace(BRANCH_PLACEHOLDER, default_branch)
    if name != "run":
        return text
    marker = "    " + SERVICES_MARKER
    if marker not in text:
        raise ValueError("tollgate-run.yml senza il segnaposto dei servizi")
    block = _services_block(services, ports) + "\n" if services else ""
    return text.replace(marker + "\n", block)


def files(plugin_root: Path, *, default_branch: str, services: dict[str, str],
          ports: dict[str, int] | None = None) -> dict[str, bytes]:
    """Percorso nel repo del progetto → contenuto. Il ramo predefinito sostituisce
    `__DEFAULT_BRANCH__` nei workflow dei `push`; i servizi entrano nel job `head` di
    `tollgate-run`, e `ports` (nome del servizio → porta) li rende raggiungibili dal job
    con `ports: ["P:P"]` (9.6)."""
    if not _BRANCH.match(default_branch):
        raise ValueError(f"nome del ramo predefinito non valido: {default_branch!r}")
    root = Path(plugin_root)
    out: dict[str, bytes] = {}
    for name in WORKFLOW_NAMES:
        text = (root / WORKFLOWS_DIR / f"tollgate-{name}.yml").read_text(encoding="utf-8")
        out[f".github/workflows/tollgate-{name}.yml"] = _render(
            name, text, default_branch, services, ports or {}).encode("utf-8")
    out[f"{INSTALL_DIR}/VERSION"] = f"{VERSION}\n".encode()
    out[f"{INSTALL_DIR}/FINGERPRINT"] = f"{fingerprint(root / 'bin')}\n".encode()
    for path in _sources(root / "bin"):
        out[f"{INSTALL_DIR}/bin/{path.relative_to(root / 'bin').as_posix()}"] = path.read_bytes()
    return out
