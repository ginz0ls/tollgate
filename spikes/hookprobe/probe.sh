#!/usr/bin/env bash
# spikes/hookprobe/probe.sh — registra l'input di un hook; nega i PreToolUse con PROBE_DENY
event="${1:-unknown}"
log="${PROBE_LOG:-/tmp/tollgate-p0/probe.jsonl}"
mkdir -p "$(dirname "$log")"
input="$(cat)"
printf '%s' "$input" | jq -c --arg e "$event" '{event: $e, input: .}' >> "$log"
if [ "$event" = "PreToolUse" ] && printf '%s' "$input" | grep -q 'PROBE_DENY'; then
  echo "probe deny" >&2
  exit 2
fi
exit 0
