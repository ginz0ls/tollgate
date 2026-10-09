"""Lettura del report JUnit (spec 7.5, 8.1): identificativi classname::name, niente entità."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_DANGER = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


class JunitError(ValueError):
    pass


@dataclass
class Junit:
    total: int = 0
    skipped: int = 0
    failed: int = 0
    ids_run: list[str] = field(default_factory=list)
    ids_skipped: list[str] = field(default_factory=list)
    ids_failed: list[str] = field(default_factory=list)


def parse_junit(data: bytes) -> Junit:
    if _DANGER.search(data):
        raise JunitError("XML con DOCTYPE o entità: report rifiutato")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise JunitError(f"XML non valido: {e}") from e
    j = Junit()
    for case in root.iter("testcase"):
        tid = f"{case.get('classname', '')}::{case.get('name', '')}"
        j.total += 1
        if case.find("skipped") is not None:
            j.skipped += 1
            j.ids_skipped.append(tid)
            continue
        j.ids_run.append(tid)
        if case.find("failure") is not None or case.find("error") is not None:
            j.failed += 1
            j.ids_failed.append(tid)
    return j
