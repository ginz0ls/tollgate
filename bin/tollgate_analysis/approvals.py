"""File di approvazione `spec-approval.md` e `plan-approval.md` (spec 18.3)."""
from __future__ import annotations

import re

KINDS = ("spec-approval", "plan-approval")
REQUIRED = ("kind", "path", "sha")
REVIEWS_DIR = "docs/superpowers/reviews"
_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)$")
_INT = re.compile(r"^-?\d{1,6}$")


def approval_paths(issue: int) -> tuple[str, str]:
    """Percorsi (relativi al worktree) di `spec-approval.md` e `plan-approval.md`."""
    base = f"{REVIEWS_DIR}/{issue}"
    return f"{base}/spec-approval.md", f"{base}/plan-approval.md"


def _value(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    raw = re.sub(r"\s+#.*$", "", raw)
    if raw in ("null", "~", ""):
        return None
    return int(raw) if _INT.match(raw) else raw


def parse_approval(text: str) -> dict | None:
    """L'intestazione tra le due righe `---` come dizionario, oppure `None` se manca, non si
    chiude, ha una riga che non è `chiave: valore`, non è di un `kind` di approvazione o le
    manca `path` o `sha`. Valori tra virgolette o nudi; `null` è `None`."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    header: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if m is None:
            return None
        header[m.group(1)] = _value(m.group(2))
    else:
        return None
    if header.get("kind") not in KINDS or any(not header.get(k) for k in REQUIRED):
        return None
    return header
