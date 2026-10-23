#!/usr/bin/env python3
"""Sonda VE2/VE10: registra in `sonda-hooks.jsonl` nella cartella dell'evento e in `$HOME/.local/state/sonda/hooks.jsonl`
il nome dell'evento, la cartella dell'evento e del processo, i soli valori di HOME, PATH, CLAUDE_CONFIG_DIR,
CLAUDE_PLUGIN_ROOT, PWD e TMPDIR e l'elenco dei SOLI NOMI delle variabili d'ambiente (mai i valori delle altre: le
evidenze si committano). Non cambia mai l'esito dell'evento."""
import json
import os
import sys

VALUES = ("HOME", "PATH", "CLAUDE_CONFIG_DIR", "CLAUDE_PLUGIN_ROOT", "PWD", "TMPDIR")
EXTRA = ("command_name", "command_args", "expansion_type", "agent_type", "subagent_type")     # se presenti, brevi


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    if not isinstance(event, dict):
        event = {}
    record = {
        "event": sys.argv[1] if len(sys.argv) > 1 else event.get("hook_event_name"),
        "event_cwd": event.get("cwd"),
        "process_cwd": os.getcwd(),
        "tool_name": event.get("tool_name"),
        "event_keys": sorted(event),
        "env": {name: os.environ.get(name) for name in VALUES},
        "env_names": sorted(os.environ),
    }
    for key in EXTRA:
        value = event.get(key)
        if isinstance(value, str) and len(value) <= 200:
            record[key] = value
    line = json.dumps(record, sort_keys=True) + "\n"
    targets = [os.path.join(event.get("cwd") or os.getcwd(), "sonda-hooks.jsonl")]
    home = os.environ.get("HOME")
    if home:
        targets.append(os.path.join(home, ".local", "state", "sonda", "hooks.jsonl"))
    for path in targets:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError as exc:
            sys.stderr.write("sonda: scrittura di %s fallita: %s\n" % (os.path.basename(path), type(exc).__name__))


if __name__ == "__main__":
    main()
    sys.exit(0)
