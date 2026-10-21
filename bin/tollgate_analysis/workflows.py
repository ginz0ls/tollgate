"""Regole sui workflow del progetto (spec 9.2, decisione 15). Puro: nessun accesso a git né al
disco. Non è un parser YAML: legge per righe e, nel dubbio, dà rosso (fail-closed)."""
from __future__ import annotations

import re

FORBIDDEN_EVENTS = ("pull_request_target", "workflow_run")
GUARDED_SCOPES = ("statuses", "checks")
SAFE_VALUES = ("read", "none")

_PATH = re.compile(r"^\.github/workflows/[^/]+\.ya?ml$")
_EVENT = re.compile(r"(?<![\w-])(" + "|".join(FORBIDDEN_EVENTS) + r")(?![\w-])")
_WRITE_ALL = re.compile(r"(?<![\w-])write-all(?![\w-])")
_SCOPE = re.compile(r"(?:^|[\s{,\[-])[\"']?(" + "|".join(GUARDED_SCOPES) + r")[\"']?[ ]*:"
                    r"(?:[ ]+|(?=[,}\]]|$))(\"[^\"]*\"|'[^']*'|[^\s,}\]]*)")
# àncora, alias o chiave di fusione: a inizio nodo (riga, `- `, dopo `chiave: `, `[`, `{` o `,`)
_ANCHOR = re.compile(r"(?:^\s*(?:-\s+)*|:\s+|[\[{,]\s*)[&*]\S")
_MERGE = re.compile(r"^\s*(?:-\s+)?<<\s*:")
_TOP_PERMISSIONS = re.compile(r"^[\"']?permissions[\"']?[ ]*:")
# chiave complessa `? `
_COMPLEX_KEY = re.compile(r"^\s*(?:-\s+)*\?(?:\s|$)")
_TAB_INDENT = re.compile(r"^[ ]*\t")
_BLOCK_HEADER = re.compile(r"^(\s*(?:-\s+)*)(?:\S.*?)?[:-]\s+[|>][-+0-9]*\s*$")
_RUN_KEY = re.compile(r"^\s*(?:-\s+)*[\"']?run[\"']?\s*:\s*$")
_NODE_START = "-:[{,?"


def is_workflow_path(rel: str) -> bool:
    """`.github/workflows/<nome>.yml` o `.yaml`, direttamente nella cartella."""
    return _PATH.match(rel) is not None


def _strip_comment(line: str) -> str:
    """La riga senza il commento (`#` a inizio riga o dopo uno spazio, fuori dalle virgolette)."""
    quote, i = "", 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\" and quote == '"':
                i += 1
            elif c == quote:
                quote = ""
        elif c in "\"'":
            quote = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
        i += 1
    return line


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _next_value(lines: list[str], index: int) -> str:
    """Il valore di una chiave senza valore sulla sua riga: la riga seguente, se più rientrata
    e senza `:` né `- ` (un valore su più righe); altrimenti vuoto (la chiave apre una mappa)."""
    here = _indent(lines[index])
    for line in lines[index + 1:]:
        text = _strip_comment(line)
        if not text.strip():
            continue
        if _indent(text) > here and ":" not in text and not text.lstrip().startswith("-"):
            return _unquote(text)
        return ""
    return ""


def _escape_lines(lines: list[str]) -> list[int]:
    """I numeri di riga con un `\\` dentro una stringa a doppie virgolette, in qualunque punto,
    tranne il valore di una chiave `run:`. Segue lo stato «dentro una stringa» da una riga
    all'altra; le virgolette si aprono a inizio nodo (dopo `:`, `-`, `[`, `{`, `,`, `?` o a
    inizio riga); nelle virgolette singole `\\` non è un escape; il contenuto di uno scalare a
    blocco (`|`, `>`) è testo e non si guarda."""
    found: list[int] = []
    in_dq = in_sq = dq_run = False
    block_base: int | None = None
    for number, line in enumerate(lines, 1):
        if block_base is not None and not in_dq and not in_sq:
            if not line.strip() or _indent(line) > block_base:
                continue
            block_base = None
        i, flagged = 0, False
        while i < len(line):
            c = line[i]
            if in_dq:
                if c == "\\":
                    if not dq_run and not flagged:
                        found.append(number)
                        flagged = True
                    i += 1
                elif c == '"':
                    in_dq = False
            elif in_sq:
                in_sq = c != "'"
            elif c == "#" and (i == 0 or line[i - 1] in " \t"):
                break
            elif c in "\"'":
                before = line[:i].rstrip()
                if not before or before[-1] in _NODE_START:
                    if c == '"':
                        in_dq, dq_run = True, _RUN_KEY.match(line[:i]) is not None
                    else:
                        in_sq = True
            i += 1
        if not in_dq and not in_sq:
            m = _BLOCK_HEADER.match(_strip_comment(line))
            if m:
                block_base = len(m.group(1))
    return found


def problems(text: str) -> list[str]:
    """Le regole che il workflow `text` viola, una frase ciascuna (`[]` se nessuna): niente
    `pull_request_target` né `workflow_run` (nemmeno in una stringa), una chiave `statuses` o
    `checks` a qualunque livello solo con `read` o `none`, niente `write-all`, un blocco
    `permissions` di primo livello. Fail-closed: un testo che non si legge (tabulazione di
    rientro, byte non UTF-8) o un'àncora, un alias o `<<:` YAML sono un problema."""
    if any(c == "�" or c == "\x00" or "\ud800" <= c <= "\udfff" for c in text):
        return ["il file non si legge: byte non UTF-8 o caratteri di controllo"]
    lines = text.lstrip("﻿").splitlines()
    for number, line in enumerate(lines, 1):
        if _TAB_INDENT.match(line):
            return [f"il file non si legge: tabulazione nel rientro (riga {number})"]
    found: list[str] = []
    top_permissions = False
    for number, raw in enumerate(lines, 1):
        line = _strip_comment(raw)
        if _TOP_PERMISSIONS.match(line):
            top_permissions = True
        for m in _EVENT.finditer(line):
            found.append(f"usa {m.group(1)} (riga {number})")
        if _WRITE_ALL.search(line):
            found.append(f"permissions: write-all (riga {number})")
        for m in _SCOPE.finditer(line):
            value = _unquote(m.group(2))
            if not value:
                value = _next_value(lines, number - 1)
            if value and value not in SAFE_VALUES:
                found.append(f"{m.group(1)}: {value} invece di read o none (riga {number})")
        if _COMPLEX_KEY.match(line):
            found.append(f"chiave complessa YAML `?` (riga {number}): non si controlla")
        if _ANCHOR.search(line) or _MERGE.match(line):
            found.append(f"àncora, alias o chiave di fusione YAML (riga {number}): non si "
                         f"controlla")
    found += [f"escape (\\) in una stringa tra virgolette doppie fuori da run: (riga {n}): non "
              f"si controlla" for n in _escape_lines(lines)]
    if not top_permissions:
        found.append("manca il blocco permissions di primo livello")
    return found
