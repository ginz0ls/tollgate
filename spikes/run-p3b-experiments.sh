#!/usr/bin/env bash
# spikes/run-p3b-experiments.sh — G1-G5: interfaccia di `gh` dal testo d'aiuto della versione installata.
# Nessuna rete: solo `gh --version` e `gh <comando> --help`.
set -uo pipefail
H=/tmp/tollgate-p3b/help; mkdir -p "$H" || exit 1
gh --version > "$H/version.txt" 2>&1
gh api --help > "$H/api.txt" 2>&1
gh pr create --help > "$H/pr-create.txt" 2>&1
gh pr edit --help > "$H/pr-edit.txt" 2>&1
gh pr list --help > "$H/pr-list.txt" 2>&1
gh pr view --help > "$H/pr-view.txt" 2>&1
echo "fatto: $(ls "$H")"
