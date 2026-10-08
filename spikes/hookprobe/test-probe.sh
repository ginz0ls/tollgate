#!/usr/bin/env bash
# spikes/hookprobe/test-probe.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
export PROBE_LOG="$(mktemp)"
echo '{"tool_name":"Bash","tool_input":{"command":"echo ok"}}' | "$here/probe.sh" PreToolUse
rc_ok=$?
set +e
echo '{"tool_name":"Bash","tool_input":{"command":"echo PROBE_DENY"}}' | "$here/probe.sh" PreToolUse 2>/dev/null
rc_deny=$?
set -e
lines=$(wc -l < "$PROBE_LOG")
first_event=$(head -1 "$PROBE_LOG" | jq -r .event)
[ "$rc_ok" -eq 0 ] && [ "$rc_deny" -eq 2 ] && [ "$lines" -eq 2 ] && [ "$first_event" = "PreToolUse" ] \
  && echo "PASS" || { echo "FAIL rc_ok=$rc_ok rc_deny=$rc_deny lines=$lines event=$first_event"; exit 1; }
