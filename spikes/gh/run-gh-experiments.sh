#!/usr/bin/env bash
# spikes/gh/run-gh-experiments.sh — G1-G4; richiede il consenso dello Step 1
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; P0=/tmp/tollgate-p0/gh
owner="$(gh api user --jq .login)" && [ -n "$owner" ] || { echo "gh non autenticato" >&2; exit 1; }
rm -rf "$P0"; mkdir -p "$P0"   # solo dopo il controllo: le uscite precedenti restano se gh manca
gh api user --jq '.plan.name' > "$P0/g1-plan.txt" 2>&1

setup_repo() { # nome, visibilità
  gh repo create "$owner/$1" --"$2" --add-readme >/dev/null || exit 1
  rm -rf "$P0/$1"; gh repo clone "$owner/$1" "$P0/$1" -- -q || exit 1
  mkdir -p "$P0/$1/.github/workflows"; cp "$here"/workflows/*.yml "$P0/$1/.github/workflows/"
  ( cd "$P0/$1" && git add -A && git commit -qm "probe workflows" && git push -q ) || exit 1
}
setup_repo tollgate-probe private
setup_repo tollgate-probe-public public

# G1: protezione e ruleset sul privato
gh api "repos/$owner/tollgate-probe/branches/main/protection" > "$P0/g1-get.txt" 2>&1; echo "exit=$?" >> "$P0/g1-get.txt"
gh api -X POST "repos/$owner/tollgate-probe/rulesets" --input - > "$P0/g1-ruleset.txt" 2>&1 <<'JSON'
{"name":"probe","target":"branch","enforcement":"active",
 "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
 "rules":[{"type":"required_status_checks","parameters":{"strict_required_status_checks_policy":true,
   "required_status_checks":[{"context":"tollgate/verdict"}]}}]}
JSON
echo "exit=$?" >> "$P0/g1-ruleset.txt"

# G2 e G3: PR verso main e verso other, sul privato
# senza questa guardia i comandi git e gh seguenti girerebbero nella cartella di lancio
cd "$P0/tollgate-probe" || exit 1
git switch -qc other && git push -qu origin other && git switch -q main
git switch -qc feature && echo x > x.txt && git add x.txt && git commit -qm x && git push -qu origin feature
gh pr create --base main --head feature --title probe-main --body probe >/dev/null
git switch -qc feature2 main && echo y > y.txt && git add y.txt && git commit -qm y && git push -qu origin feature2
gh pr create --base other --head feature2 --title probe-other --body probe >/dev/null
echo "attendere 3 minuti, poi lanciare lo Step 5"
