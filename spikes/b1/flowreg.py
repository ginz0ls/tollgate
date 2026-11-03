#!/usr/bin/env python3
"""Aiuti di `spikes/run-b1-flow.sh registra` (Task 9): solo lettura, libreria standard.

  comandi <stream.jsonl>...   i comandi Bash del modello e il conto degli strumenti (Grep compresi)
  lookups <tollgate.db>       le righe di `lookups` e la nota salvata di ogni task (sola lettura)
  eventi <events.jsonl>       gli eventi research_note, research_reminder e veto
  grep <comandi.txt> <lookups.txt>   quanti Grep del modello, quante letture registrate: i Grep non sono registrati (B1-V6)
  precarico <stream.jsonl>... il titolo della rules-base vera nelle trascrizioni dei subagenti (prova) o, senza percorsi, le righe con R-BASE- (indizio)
  trascrizioni <home> <stream.jsonl>...   (B3) i titoli delle regole nelle trascrizioni dei subagenti, cercate solo nelle cartelle
                              di sessione ricavate da `cwd` e `session_id` di ogni flusso; si stampano solo le righe col titolo
  tipi <tollgate.db>          (B3) agent_type e reviewer_type di ogni task (sola lettura)
  togli-pagine <stream.jsonl>...   (B3) UNICO comando che scrive: riscrive il flusso al suo posto, sostituendo il testo delle pagine dei
                              fornitori (risultati lunghi di WebFetch e WebSearch) e quello delle skill che non sono di tollgate
                              (blocchi "Base directory for this skill:" lunghi) con un segnaposto che dice nome o URL e lunghezza
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

WANTED = ("research_note", "research_reminder", "veto")
RULES_TITLE = "# Regole di base (versione 1)"
AI_TITLES = ("# Regole ai (versione 1)", RULES_TITLE)
WEB_TOOLS = ("WebFetch", "WebSearch")
MAX_WEB_RESULT = 5000  # caratteri: oltre, il risultato di WebFetch/WebSearch è una pagina di terzi e non entra nelle evidenze pubbliche


def tool_uses(path):
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "assistant":
            continue
        content = (obj.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield block.get("name", "?"), block.get("input") or {}, obj.get("parent_tool_use_id") is not None


def comandi(paths):
    counts, sub = {}, {}
    for path in paths:
        print(f"# {path}")
        for name, ti, in_sub in tool_uses(path):
            counts[name] = counts.get(name, 0) + 1
            sub[name] = sub.get(name, 0) + (1 if in_sub else 0)
            if name == "Bash":
                cmd = str(ti.get("command", "")).replace("\n", " ⏎ ")
                print(f"bash{' (subagente)' if in_sub else ''}: {cmd}")
            elif name == "Grep":
                print(f"grep{' (subagente)' if in_sub else ''}: {json.dumps(ti, ensure_ascii=False)}")
    print("# strumenti del modello (totale, di cui da subagenti)")
    for name in sorted(counts):
        print(f"{name}: {counts[name]} ({sub[name]})")


def lookups(db):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        print("# lookups: id, work, task, agent_id, kind, target, at")
        for row in conn.execute("SELECT id, work, task, agent_id, kind, target, at FROM lookups ORDER BY id"):
            print("\t".join("" if v is None else str(v) for v in row))
        print("# per tipo")
        for kind, n in conn.execute("SELECT kind, COUNT(*) FROM lookups GROUP BY kind ORDER BY kind"):
            print(f"{kind}: {n}")
        print("# task: work, number, state, research_ok")
        for row in conn.execute("SELECT work, number, state, research_ok FROM tasks ORDER BY work, number"):
            print("\t".join(str(v) for v in row))
        for work, number, note in conn.execute("SELECT work, number, research_note FROM tasks WHERE research_note IS NOT NULL ORDER BY work, number"):
            print(f"# nota salvata, lavoro {work} task {number}")
            print(note)
    finally:
        conn.close()


def eventi(path):
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("type") in WANTED:
            print(json.dumps(obj, ensure_ascii=False, sort_keys=True))


def _count(path, prefix):
    """Somma i valori di tutte le righe che cominciano per `prefix` (una per file di flusso, se mai ce ne fossero più blocchi)."""
    total = 0
    for line in Path(path).read_text().splitlines():
        if line.startswith(prefix):
            total += int(line[len(prefix):].split()[0])
    return total


def grep(comandi_txt, lookups_txt):
    print(f"Grep del modello: {_count(comandi_txt, 'Grep: ')}; letture registrate (read): {_count(lookups_txt, 'read: ')}")
    print("I Grep dell'implementatore non sono registrati (B1-V6): non entrano in lookups.")


def _transcript_paths(obj):
    """I valori di `agent_transcript_path` (le trascrizioni dei subagenti) ovunque nell'oggetto JSON."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "agent_transcript_path" and isinstance(value, str):
                yield value
            else:
                yield from _transcript_paths(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _transcript_paths(value)


def precarico(paths):
    """Prova del precaricamento: il titolo delle regole nelle trascrizioni dei subagenti, se i loro percorsi sono nelle uscite.
    Altrimenti solo un indizio: le righe del flusso con `R-BASE-`. Dei percorsi si stampa il solo nome del file."""
    transcripts, rbase = [], 0
    for path in paths:
        for line in Path(path).read_text(errors="replace").splitlines():
            if "R-BASE-" in line:
                rbase += 1
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            for found in _transcript_paths(obj):
                if found not in transcripts:
                    transcripts.append(found)
    readable = []
    for found in transcripts:
        try:
            text = Path(found).read_text(errors="replace")
        except OSError:
            print(f"{Path(found).name}: non leggibile")
            continue
        readable.append(RULES_TITLE in text)
        print(f"{Path(found).name}: titolo {'trovato' if readable[-1] else 'assente'}")
    if readable:
        print("metodo: trascrizioni")
        print(f"titolo trovato in {sum(readable)} di {len(readable)} trascrizioni")
    else:
        print("metodo: indizio")
        print("nessuna trascrizione di subagente leggibile nelle uscite: vale solo l'indizio, non è una prova del precaricamento")
    print(f"righe con R-BASE-: {rbase}")


def project_dir_name(cwd):
    """Il nome della cartella di una sessione in `~/.claude/projects/`: il `cwd` con ogni carattere non alfanumerico sostituito da `-`."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _session(path):
    """`(cwd, session_id)` dal primo messaggio `system` del flusso stream-json, o `(None, None)`."""
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("type") == "system" and obj.get("cwd") and obj.get("session_id"):
            return str(obj["cwd"]), str(obj["session_id"])
    return None, None


def _message_text(obj):
    content = (obj.get("message") or {}).get("content") if isinstance(obj.get("message"), dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def trascrizioni(home, paths):
    """Per ogni flusso, la cartella `<home>/.claude/projects/<cwd>/<session_id>/subagents/` (e nessun'altra): di ogni trascrizione
    `agent-*.jsonl` si stampano solo i titoli delle regole trovati in una riga di messaggio, con il flag `isMeta`."""
    if not home:
        print("trascrizioni: HOME vuota", file=sys.stderr)
        return 1
    base = Path(home) / ".claude" / "projects"
    order = {}
    for path in paths:
        cwd, sid = _session(path)
        if cwd is None:
            print(f"# {Path(path).parent.name}: nessun messaggio system con cwd e session_id: nessuna cartella da guardare")
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
            print(f"# {Path(path).parent.name}: session_id non valido: sessione saltata")
            continue
        folder = project_dir_name(cwd)
        key = (folder, sid)
        fresh = key not in order
        order.setdefault(key, len(order) + 1)
        shown = f", cartella {folder}" if (cwd + "/").startswith("/tmp/tollgate-b1/") else ""
        print(f"# {Path(path).parent.name}: sessione {order[key]}{shown}")
        if not fresh:
            continue
        subs = sorted((base / folder / sid / "subagents").glob("agent-*.jsonl"))
        if not subs:
            print("nessuna trascrizione di subagente")
        for sub in subs:
            found = []
            try:
                lines = sub.read_text(errors="replace").splitlines()
            except OSError:
                print(f"{sub.name}: non leggibile")
                continue
            for line in lines:
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                for text_line in _message_text(obj).splitlines():
                    if text_line.strip() in AI_TITLES:
                        found.append((text_line.strip(), bool(obj.get("isMeta"))))
            if not found:
                print(f"{sub.name}: nessun titolo")
            for title, meta in found:
                print(f"{sub.name}: {title} (isMeta: {'sì' if meta else 'no'})")
    return 0


def tipi(db):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        print("# task: work, number, agent_type, reviewer_type")
        for work, number, agent, reviewer in conn.execute("SELECT work, number, agent_type, reviewer_type FROM tasks ORDER BY work, number"):
            print(f"{work}\t{number}\tagent_type={agent}\treviewer_type={reviewer}")
    finally:
        conn.close()


def _content_text(content):
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text") if isinstance(content, list) else ""


def web_results(obj, names):
    """Gli (indice del blocco, testo) dei tool_result di WebFetch/WebSearch di una riga di stream, con il nome dello strumento."""
    content = (obj.get("message") or {}).get("content") if isinstance(obj, dict) else None
    for i, block in enumerate(content if isinstance(content, list) else []):
        if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in names:
            yield i, block, names[block["tool_use_id"]]


SKILL_PREFIX = "Base directory for this skill:"


def external_skill(text):
    """Il nome della skill se il blocco è il testo di una skill che non è di tollgate e supera MAX_WEB_RESULT, altrimenti None."""
    if not text.startswith(SKILL_PREFIX) or len(text) <= MAX_WEB_RESULT:
        return None
    path = text[len(SKILL_PREFIX):].split("\n", 1)[0].strip()
    if "tollgate" in path.lower():
        return None
    return path.rstrip("/").rsplit("/", 1)[-1] or "?"


def _placeholder(url, length):
    return f"[pagina di terzi tolta dalle evidenze: {url}, {length} caratteri]"


def togli_pagine(paths):
    """Riscrive ogni flusso sostituendo i risultati lunghi di WebFetch/WebSearch (tetto MAX_WEB_RESULT) con un segnaposto."""
    total = 0
    for path in paths:
        names, out, changed = {}, [], 0
        for line in Path(path).read_text(errors="replace").splitlines():
            try:
                obj = json.loads(line)
            except ValueError:
                out.append(line)
                continue
            msg = obj.get("message") if isinstance(obj, dict) else None
            blocks = msg.get("content") if isinstance(msg, dict) else None
            for block in blocks if isinstance(blocks, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") in WEB_TOOLS:
                    ti = block.get("input") or {}
                    names[block.get("id")] = str(ti.get("url") or ti.get("query") or block.get("name"))
            dirty = False
            for block in blocks if isinstance(blocks, list) else []:
                if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                    skill = external_skill(block["text"])
                    if skill:
                        block["text"] = f"[skill di terzi tolta dalle evidenze: {skill}, {len(block['text'])} caratteri]"
                        dirty = True
            for _, block, label in web_results(obj, names):
                text = _content_text(block.get("content"))
                if len(text) > MAX_WEB_RESULT:
                    block["content"] = _placeholder(label, len(text))
                    dirty = True
                    res = obj.get("tool_use_result")
                    if isinstance(res, dict) and isinstance(res.get("result"), str):
                        res["result"] = block["content"]
                    elif isinstance(res, str) and len(res) > MAX_WEB_RESULT:
                        obj["tool_use_result"] = block["content"]
            changed += dirty
            out.append(json.dumps(obj, ensure_ascii=False) if dirty else line)
        if changed:
            Path(path).write_text("\n".join(out) + "\n")
        print(f"{path}: {changed} risultati sostituiti")
        total += changed
    return total


def main(argv):
    if len(argv) >= 2 and argv[0] == "comandi":
        comandi(argv[1:])
    elif len(argv) == 2 and argv[0] == "lookups":
        lookups(argv[1])
    elif len(argv) == 2 and argv[0] == "eventi":
        eventi(argv[1])
    elif len(argv) == 3 and argv[0] == "grep":
        grep(argv[1], argv[2])
    elif len(argv) >= 2 and argv[0] == "precarico":
        precarico(argv[1:])
    elif len(argv) >= 3 and argv[0] == "trascrizioni":
        return trascrizioni(argv[1], argv[2:])
    elif len(argv) == 2 and argv[0] == "tipi":
        tipi(argv[1])
    elif len(argv) >= 2 and argv[0] == "togli-pagine":
        togli_pagine(argv[1:])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
