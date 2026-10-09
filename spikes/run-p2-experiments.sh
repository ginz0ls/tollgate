#!/usr/bin/env bash
# spikes/run-p2-experiments.sh — E7 (taglio in background), E8 (taglio alla ripresa), E9 (campioni)
set -uo pipefail
P2=/tmp/tollgate-p2; mkdir -p "$P2" || exit 1
PLUGIN="$(cd "$(dirname "$0")/hookprobe" && pwd)" || exit 1
export PROBE_LOG="$P2/probe.jsonl"
W="$P2/turns"; rm -rf "$W"; mkdir -p "$W" || exit 1
for i in 1 2 3 4 5 6 7 8; do echo "contenuto $i" > "$W/$i.txt"; done
run() { # id, modo, prompt
  rm -f "$PROBE_LOG"
  ( cd "$W" && claude -p --plugin-dir "$PLUGIN" --permission-mode "$2" "$3" < /dev/null ) > "$P2/$1.out" 2>&1
  cp "$PROBE_LOG" "$P2/$1.jsonl" 2>/dev/null || : > "$P2/$1.jsonl"
}
run e7 manual "Lancia con lo strumento Agent il subagente hookprobe:probe-turns IN BACKGROUND (run_in_background: true) con il compito descritto nelle sue istruzioni. Aspetta la notifica di fine e riporta alla lettera ogni testo che ricevi, compresi gli avvisi di interruzione."
run e8 manual "Lancia con lo strumento Agent, in primo piano, il subagente hookprobe:probe-turns3 con name 'sonda3' e il compito: leggi 1.txt e scrivi FATTO. Poi riprendilo con SendMessage verso 'sonda3' chiedendo: leggi 2.txt, 3.txt, 4.txt, 5.txt, 6.txt uno per turno e scrivi FATTO. Riporta alla lettera ogni risposta e ogni avviso di interruzione."
run e9 manual "Esegui in ordine: 1) con lo strumento Write crea il file nota.txt con il testo 'uno'; 2) con lo strumento Edit sostituisci 'uno' con 'due' in nota.txt; 3) lancia con lo strumento Agent un subagente general-purpose in primo piano con il compito: con lo strumento Write crea sub.txt con il testo 'tre' e rispondi FATTO; 4) invoca con lo strumento Skill la skill hookprobe:probe-preload. Riporta l'esito di ogni passo."
echo "fatto: $(ls "$P2")"
