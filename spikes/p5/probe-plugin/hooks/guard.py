#!/usr/bin/env python3
"""Sonda VE5: nega `touch NEGATO` con un motivo riconoscibile e lascia passare tutto il resto (`touch AMMESSO`)."""
import json
import re
import sys

REASON = "SONDA-MOTIVO-NEGATO-7f3a: la sonda vieta touch NEGATO"

try:
    event = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
tool_input = event.get("tool_input") if isinstance(event, dict) else None
command = tool_input.get("command") if isinstance(tool_input, dict) else None
if isinstance(command, str) and re.search(r"\btouch\s+NEGATO\b", command):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": REASON}}))
sys.exit(0)
