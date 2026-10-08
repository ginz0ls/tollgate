#!/usr/bin/env bash
# spikes/run-hook-experiments.sh — esegue E1-E5 e salva i log in $P0
set -uo pipefail
P0=/tmp/tollgate-p0; mkdir -p "$P0"
PLUGIN="$(cd "$(dirname "$0")/hookprobe" && pwd)"
export PROBE_LOG="$P0/probe.jsonl"
run() { # id, mode, prompt
  rm -f "$PROBE_LOG"
  ( cd /tmp && claude -p --plugin-dir "$PLUGIN" --permission-mode "$2" "$3" ) > "$P0/$1.out" 2>&1
  cp "$PROBE_LOG" "$P0/$1.jsonl" 2>/dev/null || echo '' > "$P0/$1.jsonl"
}
run e1 manual "Lancia con lo strumento Agent un subagente general-purpose in background con il compito: rispondi solo 'uno'. Quando ha finito, riprendilo con lo strumento SendMessage chiedendo: rispondi solo 'due'. Riporta entrambe le risposte."
run e2 auto "Lancia con lo strumento Agent un subagente general-purpose con il compito: rispondi solo 'uno'. Riporta la risposta."
# controprove di E2: stessa richiesta in manual (primo piano esplicito) e di nuovo in auto
run e2b manual "Lancia con lo strumento Agent un subagente general-purpose (non in background) con il compito: rispondi solo 'uno'. Riporta la risposta."
run e2c auto "Lancia con lo strumento Agent un subagente general-purpose con il compito: rispondi solo 'uno'. Riporta la risposta."
rm -f "$P0/e3-side.txt"
run e3 bypassPermissions "Esegui con Bash esattamente: echo PROBE_DENY > /tmp/tollgate-p0/e3-side.txt"
run e4-long manual "/hookprobe:probe-only-user"
run e4-short manual "/probe-only-user"
run e5 manual "Lancia con lo strumento Agent il subagente hookprobe:probe-agent e riporta la sua risposta esatta."
# E6: taglio di maxTurns (agente con maxTurns: 2) ed E6b controprova senza limite, con i file nella cartella di lavoro
W="$P0/turns"; rm -rf "$W"; mkdir -p "$W"; for i in 1 2 3 4 5; do echo "contenuto $i" > "$W/$i.txt"; done
runw() { rm -f "$PROBE_LOG"; ( cd "$W" && claude -p --plugin-dir "$PLUGIN" --permission-mode manual "$2" < /dev/null ) > "$P0/$1.out" 2>&1; cp "$PROBE_LOG" "$P0/$1.jsonl"; }
runw e6 "Lancia con lo strumento Agent il subagente hookprobe:probe-turns (in primo piano) con il compito descritto nelle sue istruzioni, e riporta alla lettera la sua risposta e ogni messaggio d'errore o di interruzione che ricevi."
runw e6b "Lancia con lo strumento Agent un subagente general-purpose in primo piano con il compito: leggi con Read il file 1.txt nella cartella corrente e rispondi solo con il suo contenuto. Riporta la risposta."
echo "fatto: $(ls "$P0")"
