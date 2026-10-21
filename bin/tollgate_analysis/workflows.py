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
# stringa a doppie virgolette con un escape (`\x73`, `\u0073`) dove si legge un nome: chiave di
# mappa, voce di elenco, riga `on:`; chiave complessa `? `
_ESCAPED = r'"(?:[^"\\]|\\.)*\\(?:[^"\\]|\\.)*"'
_ESCAPED_KEY = re.compile(r"(?:^|[\s{,\[-])" + _ESCAPED + r"\s*:")
_ESCAPED_ITEM = re.compile(r"^\s*-\s+" + _ESCAPED + r"\s*$")
_ESCAPED_ON = re.compile(r"^[\"']?on[\"']?\s*:.*\\")
_COMPLEX_KEY = re.compile(r"^\s*(?:-\s+)*\?(?:\s|$)")
_TAB_INDENT = re.compile(r"^[ ]*\t")


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
        if _ESCAPED_KEY.search(line) or _ESCAPED_ITEM.match(line) or _ESCAPED_ON.match(line):
            found.append(f"escape in una stringa tra virgolette doppie dove si legge un nome "
                         f"(riga {number}): non si controlla")
        if _COMPLEX_KEY.match(line):
            found.append(f"chiave complessa YAML `?` (riga {number}): non si controlla")
        if _ANCHOR.search(line) or _MERGE.match(line):
            found.append(f"àncora, alias o chiave di fusione YAML (riga {number}): non si "
                         f"controlla")
    if not top_permissions:
        found.append("manca il blocco permissions di primo livello")
    return found
