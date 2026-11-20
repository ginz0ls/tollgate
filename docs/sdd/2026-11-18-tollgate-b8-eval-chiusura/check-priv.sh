#!/bin/bash
# controllo di utente, host, token, -wal e pagine lunghe su tutta eval-b8 (mai stampa i valori)
D=docs/verifiche/evidenze/eval-b8; U="$(id -un)"; H="$(hostname)"
a=$(/usr/bin/grep -raFl -- "$U" $D | /usr/bin/grep -v "/\.claude/worktrees/" | wc -l); b=$(/usr/bin/grep -raFil -- "$H" $D | wc -l); c=$(/usr/bin/grep -raElI 'gh[pos]_[A-Za-z0-9_]{8,}|github_pat_|sk-ant-|AKIA[0-9A-Z]{16}' $D | wc -l); w=$(find $D -name "*-wal" -o -name "*-shm" | wc -l)
echo "file con utente: $a; con host: $b; con token: $c; wal/shm: $w"
python3 -B -m unittest tests.test_b1_scripts -k test_committed_evidence_has_no_long_web_results 2>&1 | tail -1
git status --short | cut -c1-120
