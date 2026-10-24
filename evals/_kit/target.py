"""Il bersaglio normale di ogni eval (decisione 9): una copia del plugin fuori dal repo.

La copia contiene il plugin com'è, più `evals/`, `tests/evalbin/` (gli shim di `gh` e `python3` che
`evals/run.sh` mette in testa al `PATH`) e `tests/fakegh.py`. Non contiene `__pycache__`, né la
storia git, né i documenti e le prove. Da `.claude-plugin/plugin.json` toglie `dependencies`: un
plugin con una dipendenza assente non si carica, in silenzio (VE1), e la sandbox non ha Superpowers.
Il repo resta com'è."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

MARKER = ".tollgate-eval-target"
# Cartelle della radice che non servono a valutare il plugin (`tests/` si copia a parte).
SKIP_TOP = frozenset({".git", ".github", ".claude", ".superpowers", "docs", "spikes", "tests",
                      "node_modules", "reports"})
KEEP_TESTS = ("evalbin", "fakegh.py")
MANIFEST = Path(".claude-plugin") / "plugin.json"


def _ignore(_dir, names):
    return [n for n in names if n == "__pycache__" or n.endswith((".pyc", ".pyo"))]


def build(plugin_root: Path, out: Path) -> Path:
    """Copia `plugin_root` in `out` (che si rifà da zero se l'ha creata questa funzione) e lo ritorna."""
    root, out = Path(plugin_root).resolve(), Path(out).resolve()
    if out == root or root in out.parents or out in root.parents:
        raise ValueError(f"{out} non può contenere né stare dentro {root}")
    if out.exists():
        if not (out / MARKER).is_file():
            if any(out.iterdir()):
                raise ValueError(f"{out} esiste e non è un bersaglio di tollgate: non lo tocco")
        else:
            shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / MARKER).write_text("")
    for entry in sorted(root.iterdir()):
        if entry.name in SKIP_TOP:
            continue
        if entry.is_dir():
            shutil.copytree(entry, out / entry.name, symlinks=True, ignore=_ignore)
        else:
            shutil.copy2(entry, out / entry.name)
    for name in KEEP_TESTS:
        src = root / "tests" / name
        dest = out / "tests" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest, symlinks=True, ignore=_ignore)
        else:
            shutil.copy2(src, dest)
    manifest = out / MANIFEST
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data.pop("dependencies", None)
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: target.py <radice del plugin> <cartella di uscita>", file=sys.stderr)
        return 2
    print(build(Path(argv[0]), Path(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
