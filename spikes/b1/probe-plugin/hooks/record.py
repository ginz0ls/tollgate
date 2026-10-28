#!/usr/bin/env python3
"""Sonda B1: aggiunge a un file JSONL l'input JSON che l'hook riceve su stdin (con `hook_event_name`), una riga per
evento. Non registra mai l'ambiente né altro: le evidenze si committano. Il file è `$B1_PROBE_LOG` (lo fissa lo script
della sonda), altrimenti `/tmp/tollgate-b1/hooks.jsonl`; mai sotto la HOME. Non cambia mai l'esito dell'evento."""
import json
import os
import sys

DEFAULT_LOG = "/tmp/tollgate-b1/hooks.jsonl"


def under_home(path):
    home = os.environ.get("HOME")
    if not home:
        return False
    real_home = os.path.realpath(home)
    return os.path.realpath(path) == real_home or os.path.realpath(path).startswith(real_home + os.sep)


def main():
    text = sys.stdin.read()
    try:
        event = json.loads(text)
    except ValueError:
        event = {"_non_json": text[:200]}
    if not isinstance(event, dict):
        event = {"_non_oggetto": True}
    path = os.environ.get("B1_PROBE_LOG") or DEFAULT_LOG
    if not os.path.isabs(path) or under_home(path):
        sys.stderr.write("sonda: percorso del registro non ammesso (relativo o sotto la HOME)\n")
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
    except OSError as exc:
        sys.stderr.write("sonda: scrittura fallita: %s\n" % type(exc).__name__)


if __name__ == "__main__":
    main()
    sys.exit(0)
