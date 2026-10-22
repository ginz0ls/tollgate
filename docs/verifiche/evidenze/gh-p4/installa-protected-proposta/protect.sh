#!/usr/bin/env bash
# Attiva la protezione del ramo main per tollgate (spec 9.3).
# Lo lanci tu, dalla radice del repo e con le tue credenziali di gh, dopo aver unito sul ramo
# predefinito il commit che installa i workflow e dopo che `tollgate-base` è finito.
# Uso: protect.sh [SHA]   (SHA: il commit su cui cercare il check-run; per difetto origin/main)
set -euo pipefail

BRANCH='main'
JOB='tollgate-base'
HERE=$(cd "$(dirname "$0")" && pwd)

if [ "$#" -gt 1 ]; then
  echo "uso: protect.sh [SHA]" >&2
  exit 2
fi
SHA=${1:-$(git rev-parse "origin/$BRANCH")}
if ! [[ $SHA =~ ^[0-9a-f]{40}$ ]]; then
  echo "SHA non valido: serve un commit di 40 cifre esadecimali" >&2
  exit 2
fi

runs=$(gh api --paginate --jq '.check_runs[] | select(.name == "tollgate-base" and .app.slug == "github-actions") | [.status, (.conclusion // ""), (.app.id | tostring)] | @tsv' "repos/{owner}/{repo}/commits/$SHA/check-runs?per_page=100")
if [ -z "$runs" ]; then
  echo "check-run di $JOB non trovato sul commit $SHA: unisci prima i workflow sul ramo $BRANCH" >&2
  exit 1
fi
finished=$(printf '%s\n' "$runs" | awk -F '\t' '$1 == "completed" {print $3}' | sort -u)
if [ -z "$finished" ]; then
  echo "$JOB non è ancora finito sul commit $SHA: aspetta e rilancia" >&2
  exit 1
fi
if [ "$(printf '%s\n' "$finished" | wc -l)" -ne 1 ]; then
  echo "il check-run di $JOB ha più app.id diversi ($finished): mi fermo" >&2
  exit 1
fi
APP_ID=$finished
if ! [[ $APP_ID =~ ^[1-9][0-9]*$ ]]; then
  echo "app.id non valido ($APP_ID): mi fermo" >&2
  exit 1
fi

body=$(mktemp)
trap 'rm -f "$body"' EXIT
sed 's/"__APP_ID__"/'"$APP_ID"'/' "$HERE/protection.json" > "$body"
echo "Protezione di $BRANCH con app_id $APP_ID (controlli: tollgate/guard, tollgate/verdict)."
gh api --method PUT --input "$body" "repos/{owner}/{repo}/branches/$BRANCH/protection"
