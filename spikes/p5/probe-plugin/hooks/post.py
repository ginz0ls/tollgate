#!/usr/bin/env python3
"""Sonda D18: hook PostToolUse di Bash che (a) restituisce un `additionalContext` riconoscibile e (b) scrive un file nuovo
`scritto-da-hook.md` nella cartella dell'evento, per sapere se il testo compare nella `trace` e se un file scritto da un
hook conta tra i file creati. Non cambia mai l'esito dell'evento."""
import json
import os
import sys

CONTEXT = "SONDA-CONTESTO-POST: contesto aggiunto dall'hook PostToolUse della sonda"

try:
    event = json.load(sys.stdin)
except ValueError:
    event = {}
cwd = event.get("cwd") if isinstance(event, dict) else None
try:
    path = os.path.join(cwd or os.getcwd(), "scritto-da-hook.md")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("scritto dall'hook PostToolUse della sonda\n")
except OSError as exc:
    sys.stderr.write("sonda: scrittura di scritto-da-hook.md fallita: %s\n" % type(exc).__name__)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": CONTEXT}}))
sys.exit(0)
