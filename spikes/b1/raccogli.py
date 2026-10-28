#!/usr/bin/env python3
"""Raccolta delle evidenze di B1 (lo lancia `run-b1-checks.sh raccogli`; senza rete e senza `claude`).

  raccogli.py atteso --skill SKILL.md
      stampa il testo che l'heredoc della skill `leggi` deve far arrivare a bin/eco (B1-V5).
  raccogli.py raccogli --tentativo DIR --out DIR --samples FILE --skill SKILL.md [--home HOME]
      copia (anonimizzati) i file del tentativo in <out>/<nome del tentativo>/, scrive l'esito dell'heredoc
      (eco-esito.txt: integro | diverso | assente), un riepilogo degli eventi (riepilogo.txt) e i campioni
      anonimizzati per le funzioni dei Task 3 e 4 (<samples>, chiavi read, grep_content (Grep su un file),
      grep_content_dir (Grep content su una cartella), grep_default (Grep su un file senza
      output_mode), grep_files, glob,
      bash_cat, webfetch, webfetch_redirect, websearch, mcp_docs, ognuna con pre e post; una chiave senza
      campione resta assente).

Anonimizzazione: i percorsi della HOME diventano /home/USER, `session_id`, `transcript_path` e simili diventano
segnaposto, nessuna variabile d'ambiente (gli hook della sonda non la registrano). Ciò che esiste già in uscita si
rinomina in <nome>.prev-<tempo>: niente si cancella."""
import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

HEREDOC = re.compile(r"<<'NOTA_DI_RICERCA_FINE'\n(.*?)\nNOTA_DI_RICERCA_FINE\n", re.S)
PLACEHOLDER_KEYS = {"session_id": "SESSION-ID", "transcript_path": "/home/USER/.claude/projects/TRANSCRIPT.jsonl",
                    "agent_transcript_path": "/home/USER/.claude/projects/AGENT-TRANSCRIPT.jsonl",
                    "scratchpad_dir": "SCRATCHPAD-DIR"}
SAMPLE_KEYS = ("read", "grep_content", "grep_content_dir", "grep_default", "grep_files", "glob", "bash_cat", "webfetch", "webfetch_redirect",
               "websearch", "mcp_docs")
MAX_STRING = 4000                                    # nei campioni una stringa più lunga si tronca (il registro resta intero)
COPIED = ("argv.txt", "versione.txt", "claude.err", "uscita.txt", "redirect-url.txt")


def rot(path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        path.rename(path.with_name(path.name + ".prev-" + time.strftime("%Y%m%d-%H%M%S") + "-%d" % time.monotonic_ns()))


def expected_eco(skill_path):
    m = HEREDOC.search(Path(skill_path).read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("heredoc NOTA_DI_RICERCA_FINE non trovato in %s" % skill_path)
    return m.group(1) + "\n"


def scrub_text(text, home, session_ids=()):
    if home:
        text = text.replace(home.rstrip("/"), "/home/USER")
    for sid in session_ids:
        text = text.replace(sid, "SESSION-ID")
    return text


def scrub(value, home, session_ids, truncate=False):
    """Copia anonimizzata di un valore JSON."""
    if isinstance(value, str):
        value = scrub_text(value, home, session_ids)
        if truncate and len(value) > MAX_STRING:
            value = value[:MAX_STRING] + "…[troncato, %d caratteri]" % len(value)
        return value
    if isinstance(value, list):
        return [scrub(v, home, session_ids, truncate) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in PLACEHOLDER_KEYS and isinstance(v, str):
                out[k] = PLACEHOLDER_KEYS[k]
            elif k == "env":
                continue
            else:
                out[k] = scrub(v, home, session_ids, truncate)
        return out
    return value


def read_events(path):
    events, bad = [], 0
    if not Path(path).exists():
        return events, bad
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(e, dict):
            events.append(e)
        else:
            bad += 1
    return events, bad


def _tail(tool):
    return re.sub(r"[-_]", "", tool.rsplit("__", 1)[-1])


def classify(e, redirect):
    """Il nome della chiave dei campioni a cui l'evento appartiene (o None)."""
    tool = e.get("tool_name") or ""
    ti = e.get("tool_input") if isinstance(e.get("tool_input"), dict) else {}
    if tool == "Read" and str(ti.get("file_path", "")).endswith("src/app.py"):
        return "read"
    if tool == "Grep":
        if ti.get("output_mode") == "content":
            return "grep_content" if str(ti.get("path", "")).endswith(".py") else "grep_content_dir"
        if ti.get("output_mode") is None and str(ti.get("path", "")).endswith(".py"):
            return "grep_default"
        return (
            "grep_files" if ti.get("output_mode") in (None, "files_with_matches") else None)
    if tool == "Glob":
        return "glob"
    if tool == "Bash" and str(ti.get("command", "")).strip().startswith("cat ") and "eco" not in str(ti.get("command")):
        return "bash_cat"
    if tool == "WebFetch":
        url = str(ti.get("url", "")).strip()
        if redirect and url == redirect:
            return "webfetch_redirect"
        return "webfetch" if "tomllib" in url else None
    if tool == "WebSearch":
        return "websearch"
    if tool.startswith("mcp__") and "context7" in tool and _tail(tool) in ("querydocs", "getlibrarydocs"):
        return "mcp_docs"
    return None


def build_samples(events, redirect, home, session_ids):
    """Per ogni chiave la prima coppia pre/post, con preferenza per gli strumenti del subagente (agent_id)."""
    pres = [e for e in events if e.get("hook_event_name") == "PreToolUse"]
    posts = [e for e in events if e.get("hook_event_name") in ("PostToolUse", "PostToolUseFailure")]
    used, samples = set(), {}
    for key in SAMPLE_KEYS:
        cands = [e for e in pres if classify(e, redirect) == key]
        cands.sort(key=lambda e: 0 if e.get("agent_id") else 1)          # stabile: a parità, l'ordine del registro
        if not cands:
            # senza PreToolUse (hook non arrivato) un campione può nascere dal solo post
            cands = [e for e in posts if classify(e, redirect) == key and id(e) not in used]
            cands.sort(key=lambda e: 0 if e.get("agent_id") else 1)
            if cands:
                used.add(id(cands[0]))
                samples[key] = {"post": scrub(cands[0], home, session_ids, True)}
            continue
        pre = cands[0]
        entry = {"pre": scrub(pre, home, session_ids, True)}
        post = next((p for p in posts if id(p) not in used and p.get("tool_use_id") and p.get("tool_use_id") == pre.get("tool_use_id")), None)
        if post is None:
            post = next((p for p in posts if id(p) not in used and p.get("tool_name") == pre.get("tool_name")
                         and p.get("tool_input") == pre.get("tool_input")), None)
        if post is not None:
            used.add(id(post))
            entry["post"] = scrub(post, home, session_ids, True)
        samples[key] = entry
    return samples


def summary_lines(events, bad, samples, eco_state, redirect):
    lines = ["eventi: %d (righe non valide: %d)" % (len(events), bad)]
    counts = {}
    for e in events:
        k = (e.get("hook_event_name"), e.get("tool_name") or "-", "agent_id" if e.get("agent_id") else "senza agent_id")
        counts[k] = counts.get(k, 0) + 1
    for (ev, tool, who), c in sorted(counts.items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2])):
        lines.append("  %-20s %-45s %-15s %d" % (ev, tool, who, c))
    starts = sorted({(e.get("agent_type"), bool(e.get("agent_id"))) for e in events if e.get("hook_event_name") == "SubagentStart"}, key=str)
    lines.append("SubagentStart: %s" % (", ".join("%s%s" % (t, "" if a else " (senza agent_id)") for t, a in starts) or "nessuno"))
    failures = [e for e in events if e.get("hook_event_name") == "PostToolUseFailure"]
    for e in failures:
        lines.append("PostToolUseFailure: %s %s" % (e.get("tool_name"), json.dumps(e.get("tool_input"), ensure_ascii=False)[:120]))
    lines.append("URL con reindirizzamento: %s" % (redirect or "non registrato"))
    lines.append("campioni: " + (", ".join(k for k in SAMPLE_KEYS if k in samples) or "nessuno"))
    lines.append("senza campione: " + (", ".join(k for k in SAMPLE_KEYS if k not in samples) or "nessuno"))
    lines.append("heredoc di B1-V5: " + eco_state)
    return lines


def eco_state(att, expected):
    path = Path(att) / "eco.txt"
    if not path.exists():
        return "assente", "eco.txt non c'è: bin/eco non è stato lanciato o non ha scritto"
    actual = path.read_bytes().decode("utf-8", "replace")
    if actual == expected:
        return "integro", "%d byte, uguale al testo atteso" % len(expected.encode())
    a, b = actual.splitlines(), expected.splitlines()
    i = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
    return "diverso", "atteso %d righe, ricevuto %d; prima differenza alla riga %d: atteso %r, ricevuto %r" % (
        len(b), len(a), i + 1, b[i] if i < len(b) else None, a[i] if i < len(a) else None)


def cmd_raccogli(args):
    att = Path(args.tentativo)
    if not att.is_dir():
        raise SystemExit("manca la cartella del tentativo: %s" % att)
    home = (args.home or "").strip()
    if not home or home == "/":
        raise SystemExit("--home vuoto o assente: senza non si può anonimizzare (le evidenze si committano)")
    dest = Path(args.out) / att.name
    rot(dest)
    dest.mkdir(parents=True)
    events, bad = read_events(att / "hooks.jsonl")
    session_ids = sorted({e["session_id"] for e in events if isinstance(e.get("session_id"), str) and len(e["session_id"]) > 8})
    with open(dest / "hooks.jsonl", "w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(scrub(e, home, session_ids), sort_keys=True, ensure_ascii=False) + "\n")
    for name in ("claude.json",) + COPIED:
        src = att / name
        if src.exists():
            (dest / name).write_text(scrub_text(src.read_text(encoding="utf-8", errors="replace"), home, session_ids), encoding="utf-8")
    redirect = ""
    if (att / "redirect-url.txt").exists():
        redirect = (att / "redirect-url.txt").read_text(encoding="utf-8").strip()
    state, detail = eco_state(att, expected_eco(args.skill))
    (dest / "eco-esito.txt").write_text("%s\n%s\n" % (state, detail), encoding="utf-8")
    samples = build_samples(events, redirect, home, session_ids)
    samples_path = Path(args.samples)
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    rot(samples_path)
    samples_path.write_text(json.dumps(samples, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = summary_lines(events, bad, samples, state, redirect)
    (dest / "riepilogo.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("evidenze in %s; campioni in %s" % (dest, samples_path))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("atteso")
    a.add_argument("--skill", required=True)
    r = sub.add_parser("raccogli")
    r.add_argument("--tentativo", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--samples", required=True)
    r.add_argument("--skill", required=True)
    r.add_argument("--home", default="")
    args = ap.parse_args(argv)
    if args.cmd == "atteso":
        sys.stdout.write(expected_eco(args.skill))
    else:
        cmd_raccogli(args)


if __name__ == "__main__":
    main()
