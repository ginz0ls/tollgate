#!/usr/bin/env python3
"""Aiuti di `spikes/run-b1-flow.sh registra` (Task 9): solo lettura, libreria standard.

  comandi <stream.jsonl>...   i comandi Bash del modello e il conto degli strumenti (Grep compresi)
  lookups <tollgate.db>       le righe di `lookups` e la nota salvata di ogni task (sola lettura)
  eventi <events.jsonl>       gli eventi research_note, research_reminder e veto
  grep <comandi.txt> <lookups.txt>   quanti Grep del modello, quante letture registrate: i Grep non sono registrati (B1-V6)
  precarico <stream.jsonl>... il titolo della rules-base vera nelle trascrizioni dei subagenti (prova) o, senza percorsi, le righe con R-BASE- (indizio)
"""
import json
import sqlite3
import sys
from pathlib import Path

WANTED = ("research_note", "research_reminder", "veto")
RULES_TITLE = "# Regole di base (versione 1)"


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
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
