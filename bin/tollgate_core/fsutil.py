"""Scrittura di file condivisa dagli strati sopra il nucleo."""
from __future__ import annotations

import os
from pathlib import Path


def write_atomic(path: Path, text: str) -> None:
    """Scrive `path` con un file temporaneo accanto e `os.replace`; `OSError` o `ValueError` (testo
    non codificabile) se non riesce, e in ogni caso il temporaneo non resta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except (OSError, ValueError):
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
