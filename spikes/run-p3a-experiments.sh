#!/usr/bin/env bash
# spikes/run-p3a-experiments.sh — V1 (radice del plugin nelle skill), V2 (variabili d'ambiente, solo nomi),
# V3 (segnale dell'hook visibile alla CLI), V5 (input di NotebookEdit). V4 si fa a parte con `claude plugin validate`.
set -uo pipefail
P3=/tmp/tollgate-p3a; mkdir -p "$P3" || exit 1
PLUGIN="$(cd "$(dirname "$0")/hookprobe" && pwd)" || exit 1
export PROBE_LOG="$P3/probe.jsonl"
rm -f "$P3/hs.txt"
printf '%s' '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}' > "$P3/n.ipynb"
run() { # id, modo, prompt
  rm -f "$PROBE_LOG"
  ( cd "$P3" && claude -p --plugin-dir "$PLUGIN" --permission-mode "$2" "$3" < /dev/null ) > "$P3/$1.out" 2>&1
  cp "$PROBE_LOG" "$P3/$1.jsonl" 2>/dev/null || : > "$P3/$1.jsonl"
}
run v1 manual "invoca con lo strumento Skill la skill hookprobe:probe-root e riporta alla lettera ciò che dice"
run v2 acceptEdits "esegui con Bash \`env | grep -i -E 'claude|session' | sed 's/=.*//'\` e riporta i nomi"
run v3 acceptEdits "esegui con Bash \`cat /tmp/tollgate-p3a/hs.txt # PROBE_HS\` e riporta l'uscita"
run v5 acceptEdits "crea con lo strumento NotebookEdit una cella nel notebook /tmp/tollgate-p3a/n.ipynb"
echo "fatto: $(ls "$P3")"
