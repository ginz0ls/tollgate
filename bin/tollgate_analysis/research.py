"""Passo «informati prima» (B1): forma e controllo della nota di ricerca, percorsi e URL
normalizzati, strumenti MCP di documentazione. Tutto puro: nessuna lettura di file né del DB."""
from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

RULES_BASE = "skills/rules-base/SKILL.md"

SECTION_FILES = "Letto nel progetto"
SECTION_DOCS = "Documentazione"
SECTION_FOUND = "Cosa ho trovato"
SECTION_NONE = "Nessuna fonte esterna"
MAX_NOTE_CHARS = 8000
HEREDOC_END = "NOTA_DI_RICERCA_FINE"

# Strumenti con cui un implementatore legge un file / apre una fonte (kind di `lookups`).
FILE_KINDS = ("read", "grep", "bash_read")
URL_KIND = "fetch"
DOCS_KIND = "docs"

# Nessun ripiego di attribuzione attivo (B1-V1: gli strumenti dei subagenti portano `agent_id`).
ATTRIBUTE_UNNAMED_TOOLS: frozenset[str] = frozenset()

# Pattern fnmatch dei soli strumenti di lettura della documentazione (decisione 6).
DOC_MCP_TOOLS: tuple[str, ...] = (
    "mcp__*context7*__resolve-library-id",
    "mcp__*context7*__query-docs",
    "mcp__*context7*__get-library-docs",
)
_LIBRARY_PARAMS = ("libraryId", "context7CompatibleLibraryID")

# Valori YAML che non sono una data di approvazione.
_YAML_EMPTY = {"null", "~", "|", ">", "|-", ">-", "|+", ">+", "false"}
_DEFAULT_PORTS = {"http": 80, "https": 443}


def active(work_research: int, component_on: bool) -> bool:
    """Il passo vale solo per i lavori nati con B1 e se il componente `research_note` è acceso."""
    return work_research == 1 and component_on


def enforced(skill_text: str | None) -> bool:
    """Vero se il frontmatter di `rules-base` ha un campo `approved` non vuoto (decisione 8)."""
    if not skill_text:
        return False
    lines = skill_text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            return False
        m = re.match(r"approved\s*:(.*)$", line)
        if m:
            raw = m.group(1).split(" #")[0].strip()
            if raw.lower() in _YAML_EMPTY:
                return False
            return raw.strip("'\"").strip() != ""
    return False


def is_doc_tool(name: str) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in DOC_MCP_TOOLS)


def doc_library(tool_input: dict) -> str | None:
    """Il `libraryId` di una chiamata a uno strumento di documentazione."""
    for key in _LIBRARY_PARAMS:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_url(url: str) -> str | None:
    """Schema e host in minuscolo, porta predefinita, credenziali, frammento e barra finale
    tolti, query mantenuta. None per uno schema diverso da http/https o senza host."""
    try:
        p = urlsplit(url.strip())
        scheme = p.scheme.lower()
        host = p.hostname
        port = p.port
    except ValueError:
        return None
    if scheme not in _DEFAULT_PORTS or not host:
        return None
    if ":" in host:
        host = f"[{host}]"
    netloc = host if port in (None, _DEFAULT_PORTS[scheme]) else f"{host}:{port}"
    path = p.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, p.query, ""))


def normalize_path(path: str, *, cwd: str, worktree: str) -> str | None:
    """Percorso relativo POSIX al worktree; None se vuoto, con `~` (non si espande) o fuori."""
    if not path or path.startswith("~"):
        return None
    root = os.path.normpath(worktree)
    full = os.path.normpath(os.path.join(cwd, path))
    rel = os.path.relpath(full, root)
    if rel == "." or rel == ".." or rel.startswith("../") or os.path.isabs(rel):
        return None
    return rel.replace(os.sep, "/")


@dataclass
class Source:
    ref: str   # URL come scritto nella nota, oppure il libraryId (senza il prefisso `context7:`)
    kind: str  # "url" | "context7"
    text: str


@dataclass
class Note:
    files: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    no_external: str | None = None  # None: sezione assente; "": presente senza motivo
    findings: str = ""
    problems: list[str] = field(default_factory=list)


_BULLET = re.compile(r"^[-*][ \t]+(.*)$")
_SEP_LONG = " — "
_SEP_ANY = (" — ", " - ")
_CONTEXT7 = "context7:"


def _sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("##") and line[2:3] in (" ", "\t") and line[2:].strip():
            current = out.setdefault(line[2:].strip(), [])
        elif current is not None:
            current.append(line)
    return out


def _split_description(body: str, separators: tuple[str, ...]) -> tuple[str, str]:
    """Spezza al primo separatore, con ricerche lineari (la nota è testo non fidato)."""
    cuts = [(i, sep) for sep in separators if (i := body.find(sep)) >= 0]
    if not cuts:
        return body, ""
    i, sep = min(cuts)
    return body[:i], body[i + len(sep):]


def _item(line: str, separators: tuple[str, ...]) -> tuple[str, str] | None:
    """(riferimento, descrizione) di una riga di elenco; None se non è un elemento."""
    m = _BULLET.match(line.strip())
    if not m:
        return None
    body = m.group(1).strip()
    ref, desc = _split_description(body, separators)
    ref = ref.strip().strip("`").strip().strip("<>").strip()
    return (ref, desc.strip()) if ref else None


def parse_note(text: str) -> Note:
    """Legge la nota (decisione 2). I problemi di forma vanno in `problems`, mai un'eccezione."""
    note = Note()
    if len(text) > MAX_NOTE_CHARS:
        note.problems.append(f"nota oltre {MAX_NOTE_CHARS} caratteri")
        return note
    sec = _sections(text)

    if SECTION_FILES not in sec:
        note.problems.append(f"manca la sezione «{SECTION_FILES}»")
    else:
        for line in sec[SECTION_FILES]:
            item = _item(line, (_SEP_LONG,))
            if item:
                note.files.append(item[0])
        if not note.files:
            note.problems.append(f"la sezione «{SECTION_FILES}» non elenca nessun file")

    if SECTION_DOCS in sec:
        for line in sec[SECTION_DOCS]:
            item = _item(line, _SEP_ANY)
            if not item:
                continue
            ref, desc = item
            if ref.startswith(_CONTEXT7) and ref[len(_CONTEXT7):].strip():
                note.sources.append(Source(ref[len(_CONTEXT7):].strip(), "context7", desc))
            elif re.match(r"https?://", ref, re.IGNORECASE):
                note.sources.append(Source(ref, "url", desc))
            else:
                note.problems.append(f"fonte non riconosciuta in «{SECTION_DOCS}»: {ref} "
                                     f"(serve un URL http/https o {_CONTEXT7}<libraryId>)")
        if not note.sources and not any(_item(line, _SEP_ANY) for line in sec[SECTION_DOCS]):
            note.problems.append(f"la sezione «{SECTION_DOCS}» non elenca nessuna fonte")
    if SECTION_NONE in sec:
        note.no_external = "\n".join(sec[SECTION_NONE]).strip()
    if SECTION_DOCS in sec and SECTION_NONE in sec:
        note.problems.append(f"«{SECTION_DOCS}» e «{SECTION_NONE}» insieme: tieni una sola "
                             f"delle due sezioni")
    elif SECTION_DOCS not in sec and SECTION_NONE not in sec:
        note.problems.append(f"manca la sezione «{SECTION_DOCS}» (o, al suo posto, "
                             f"«{SECTION_NONE}» con il motivo)")

    if SECTION_FOUND not in sec:
        note.problems.append(f"manca la sezione «{SECTION_FOUND}»")
    else:
        note.findings = "\n".join(sec[SECTION_FOUND]).strip()
        if not note.findings:
            note.problems.append(f"la sezione «{SECTION_FOUND}» è vuota")
    return note


def check_note(note: Note, lookups: list[tuple[str, str]], *, worktree: str) -> list[str]:
    """Problemi della nota (decisione 3); lista vuota = valida. `lookups`: coppie
    `(kind, target)` già normalizzate. Ripete i problemi di forma già trovati da `parse_note`."""
    problems = list(note.problems)
    read_files = {t for k, t in lookups if k in FILE_KINDS}
    fetched = {t for k, t in lookups if k == URL_KIND}
    docs = {t for k, t in lookups if k == DOCS_KIND}

    for f in note.files:
        rel = normalize_path(f, cwd=worktree, worktree=worktree)
        if rel is None:
            problems.append(f"il file «{f}» è fuori dal progetto: non conta come lettura")
        elif rel not in read_files:
            problems.append(f"il file «{rel}» è nella nota ma non l'hai letto in questo task "
                            f"(aprilo con Read)")

    for s in note.sources:
        if s.kind == "url":
            url = normalize_url(s.ref)
            if url is None:
                problems.append(f"la fonte «{s.ref}» non è un URL http/https valido")
            elif url not in fetched:
                problems.append(f"la fonte {url} è nella nota ma non l'hai aperta in questo "
                                f"task (aprila con WebFetch: una ricerca da sola non basta)")
        elif s.ref not in docs:
            problems.append(f"la fonte context7:{s.ref} è nella nota ma non l'hai consultata "
                            f"in questo task")

    if note.no_external is not None and not note.no_external and not note.sources:
        problems.append(f"«{SECTION_NONE}» non dice il motivo: scrivilo sulla riga seguente")
    return problems


def submit_command(program: str, task: int) -> str:
    """Il comando di consegna con il modello della nota in un heredoc a delimitatore quotato."""
    return "\n".join((
        f"{program} research submit {task} <<'{HEREDOC_END}'",
        f"## {SECTION_FILES}",
        "- <percorso di un file letto>",
        "",
        f"## {SECTION_DOCS}",
        "- <URL aperto> — <cosa dice>",
        "- context7:<libraryId> — <cosa dice>",
        "",
        f"## {SECTION_NONE}",
        f"<solo al posto di «{SECTION_DOCS}»: perché non servono fonti esterne>",
        "",
        f"## {SECTION_FOUND}",
        "<cosa hai capito e come ne tieni conto>",
        HEREDOC_END,
    ))
