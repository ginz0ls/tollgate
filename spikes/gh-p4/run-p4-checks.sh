#!/usr/bin/env bash
# spikes/gh-p4/run-p4-checks.sh — verifiche reali P4 (V1-V9) su due repo GitHub, decisione 25.
# Lo esegue solo il controller. Modo `controlla`: nessuna rete, `gh` finto.
# Uso: run-p4-checks.sh prepara | v1 | v2 | v3 | v3b | v4 | v4b | v5 | v5b | v6 | v7 | v8 | v9 | raccogli | pulisci-sonde | controlla
#
# Lezione dell'incidente di P0: nessuna cartella di uscite si cancella mai. Le uscite stanno in
# docs/verifiche/evidenze/gh-p4/ del worktree; un file che esiste già si rinomina in <nome>.prev-<tempo>.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
MODE="${1:-}"

OWNER=ginz0ls
PROT="$OWNER/tollgate-p4-protected"   # pubblico, modalità protected
DET="$OWNER/tollgate-p4-detect"       # privato, GitHub Free, modalità detect
OUT="${P4_OUT:-$root/docs/verifiche/evidenze/gh-p4}"
WORK="${P4_WORK:-/tmp/tollgate-p4/gh}"   # cloni di lavoro, non sono uscite
export P4_OUT="$OUT" P4_WORK="$WORK"   # ghguard.py li legge: -D e i cloni devono stare qui sotto
WAIT_MAX="${P4_WAIT_MAX:-600}"           # tetto di attesa per ogni run, in secondi
POLL="${P4_POLL:-10}"
RETRY_SLEEP="${P4_RETRY_SLEEP:-5}"
CHECK="${P4_CHECK:-0}"                   # 1 solo dentro il modo controlla

. "$here/common.sh"

# open_pr <etichetta> <ramo> <file> [protected|detect] [da]: ramo da main (o dal ramo locale <da>) con un file nuovo,
# push, PR verso main. Imposta PR_NUM e PR_SHA.
open_pr() {
  local label="$1" br="$2" file="$3" n="${4:-protected}" from="${5:-main}" d repo url
  d="$WORK/$n"; repo="$(repo_of "$n")"
  git -C "$d" switch -q main && git -C "$d" merge -q --ff-only origin/main || die "main locale non allineato"
  git -C "$d" switch -q -c "$br" "$from" || die "ramo $br non creato"
  mkdir -p "$(dirname "$d/$file")"
  printf 'sonda %s %s\n' "$label" "$br" > "$d/$file"
  git -C "$d" add "$file" && git -C "$d" commit -qm "sonda $label" || die "commit della sonda fallito"
  PR_SHA="$(git -C "$d" rev-parse HEAD)"
  git_call "$label-push" "$n" push -u origin "$br"
  [ "$RC" = 0 ] || die "push di $br fallito (vedi $label-push.err)"
  gh_call "$label-pr-create" pr create --repo "$repo" --base main --head "$br" --title "sonda $label" --body "sonda tollgate P4 ($label), da chiudere"
  [ "$RC" = 0 ] || die "creazione della PR fallita (vedi $label-pr-create.err)"
  url="$(tail -n 1 "$OUT/$label-pr-create.out")"
  PR_NUM="${url##*/}"
  case "$PR_NUM" in ''|*[!0-9]*) die "numero della PR non leggibile da: $url" ;; esac
}

commit_on_main() { # <file> <testo>: commit su main locale. Imposta MAIN_SHA.
  local d="$WORK/protected"
  git -C "$d" switch -q main && git -C "$d" merge -q --ff-only origin/main || die "main locale non allineato"
  mkdir -p "$(dirname "$d/$1")"
  printf '%s\n' "$2" > "$d/$1"
  git -C "$d" add "$1" && git -C "$d" commit -qm "sonda $2" || die "commit su main fallito"
  MAIN_SHA="$(git -C "$d" rev-parse HEAD)"
}


# ---------------------------------------------------------------- modi

modo_prepara() {
  local n repo vis
  mkdir -p "$OUT" "$WORK"
  gh_call prepara-auth auth status
  gh_call prepara-versione-gh --version
  if [ "$CHECK" != 1 ] && command -v claude >/dev/null 2>&1; then
    rot "$OUT/prepara-versione-claude.out"
    timeout 30 claude --version >"$OUT/prepara-versione-claude.out" 2>&1 </dev/null
  fi
  for n in protected detect; do
    repo="$(repo_of "$n")"
    gh_call "prepara-$n-esiste" api "repos/$repo"
    if [ "$RC" != 0 ]; then
      grep -q 404 "$OUT/prepara-$n-esiste.err" || die "stato di $repo non determinato (vedi prepara-$n-esiste.err)"
      vis=--public; [ "$n" = detect ] && vis=--private
      gh_call "prepara-$n-crea" repo create "$repo" "$vis" --add-readme
      [ "$RC" = 0 ] || die "creazione di $repo fallita (vedi prepara-$n-crea.err)"
      sleep "$POLL"
      gh_call "prepara-$n-esiste-dopo" api "repos/$repo"
      [ "$RC" = 0 ] || die "$repo non risponde dopo la creazione"
    fi
    clone_or_update "$n"
  done
  # sonde nel pubblico; sul privato solo probe-fetch, installata da v3b
  local d="$WORK/protected"
  mkdir -p "$d/.github/workflows"
  cp "$here"/workflows/probe-{target,run,verdict,base}.yml "$d/.github/workflows/"
  [ -e "$d/.github/probe-tag" ] || date +%Y%m%d%H%M%S > "$d/.github/probe-tag"
  if [ -n "$(git -C "$d" status --porcelain)" ]; then
    git -C "$d" add .github && git -C "$d" commit -qm "sonde tollgate P4: workflow delle verifiche" || die "commit delle sonde fallito"
    git_call prepara-push-protected protected push origin main
    [ "$RC" = 0 ] || die "push delle sonde fallito (vedi prepara-push-protected.err)"
    save_text "$OUT/prepara-sonde-sha.txt" "$(git -C "$d" rev-parse HEAD)"
  else
    save_text "$OUT/prepara-sonde-sha.txt" "sonde già installate: $(git -C "$d" rev-parse HEAD)"
  fi
}

# V1 (e dati di V3, V4, V6, V7, V8): una PR sul repo protected, un commento dell'utente, un commento del workflow
modo_v1() {
  local ts br
  clone_or_update protected
  ts="$(date +%Y%m%d-%H%M%S)"; br="p4-v1-$ts"
  open_pr v1 "$br" "sonde/v1-$ts.txt"
  save_text "$OUT/v1-pr.env" "PR=$PR_NUM" "SHA=$PR_SHA" "BRANCH=$br"
  gh_call v1-comment-utente pr comment "$PR_NUM" --repo "$PROT" --body "commento dell'utente (sonda V1)"
  track_run v1-target "$PROT" probe-target.yml "$PR_SHA" "$br" 1
  track_run v1-run "$PROT" probe-run.yml "$PR_SHA" "$br" 0
  track_run v1-verdict "$PROT" probe-verdict.yml "$PR_SHA" "$br" 1
  gh_call v1-pr-list pr list --repo "$PROT" --state all --limit 100 \
    --json number,headRefName,headRefOid,mergedAt,isCrossRepository,mergeStateStatus
  gh_call v1-pr-view-comments pr view "$PR_NUM" --repo "$PROT" --json comments
  gh_call v1-api-comments api --paginate "repos/$PROT/issues/$PR_NUM/comments"
  rot "$OUT/v1-login.txt"
  {
    echo "# gh pr view --json comments: author.login e lunghezza del corpo"
    jq -r '.comments[] | [.author.login, (.body | length | tostring)] | @tsv' "$OUT/v1-pr-view-comments.out" 2>&1
    echo "# GET issues/<n>/comments: user.login, user.type, lunghezza del corpo"
    jq -r '.[] | [.user.login, .user.type, (.body | length | tostring)] | @tsv' "$OUT/v1-api-comments.out" 2>&1
  } > "$OUT/v1-login.txt"
}

# V2: forma di gh api --include con 403 (detect) e 404 (protected non protetto)
modo_v2() {
  gh_call v2-detect api --include "repos/$DET/branches/main/protection"
  gh_call v2-protected api --include "repos/$PROT/branches/main/protection"
  gh_call v2-detect-senza-include api "repos/$DET/branches/main/protection"
  gh_call v2-protected-senza-include api "repos/$PROT/branches/main/protection"
}

# V3: riepilogo dei campi degli eventi dagli artefatti scaricati da v1; fetch di refs/pull/<n>/head dal clone
modo_v3() {
  local f d="$WORK/protected"
  load_env "$OUT/v1-pr.env"
  rot "$OUT/v3-riepilogo.jsonl"
  : > "$OUT/v3-riepilogo.jsonl"
  for f in "$OUT"/v1-*-artifacts-*/event-keys.json "$OUT"/v1-*-artifacts-*/*/event-keys.json; do
    [ -f "$f" ] || continue
    jq -c --arg f "${f#"$OUT"/}" '{file: $f, data: .}' "$f" >> "$OUT/v3-riepilogo.jsonl"
  done
  [ -s "$OUT/v3-riepilogo.jsonl" ] || echo "non determinato: nessun event-keys.json (v1 non completato?)" >> "$OUT/v3-riepilogo.jsonl"
  clone_or_update protected
  git_call v3-fetch-pull protected fetch origin "refs/pull/$PR/head"
  git_call v3-fetch-pull-sha protected rev-parse FETCH_HEAD
}

# V3b: git fetch di refs/pull/<n>/head dentro pull_request_target sul PRIVATO, senza e con credenziali.
# Unica sonda sul privato: la installa questo modo (commit e push su detect), poi apre e chiude una PR.
modo_v3b() {
  local ts br d="$WORK/detect"
  clone_or_update detect
  mkdir -p "$d/.github/workflows"
  cp "$here/workflows/probe-fetch.yml" "$d/.github/workflows/"
  if [ -n "$(git -C "$d" status --porcelain)" ]; then
    git -C "$d" add .github && git -C "$d" commit -qm "sonda tollgate P4: probe-fetch" || die "commit della sonda fallito"
    git_call v3b-push-sonda detect push origin main
    [ "$RC" = 0 ] || die "push della sonda su detect fallito (vedi v3b-push-sonda.err)"
  fi
  ts="$(date +%Y%m%d-%H%M%S)"; br="p4-v3b-$ts"
  open_pr v3b "$br" "sonde/v3b-$ts.txt" detect
  save_text "$OUT/v3b-pr.env" "PR=$PR_NUM" "SHA=$PR_SHA" "BRANCH=$br"
  track_run v3b-fetch "$DET" probe-fetch.yml "$PR_SHA" "$br" 1
  gh_call v3b-pr-close pr close "$PR_NUM" --repo "$DET"
  rot "$OUT/v3b-riepilogo.txt"
  find "$OUT"/v3b-fetch-artifacts-* -name info.json -exec jq -c . {} \; > "$OUT/v3b-riepilogo.txt" 2>&1
  [ -s "$OUT/v3b-riepilogo.txt" ] || echo "non determinato: nessun info.json (run non completato?)" > "$OUT/v3b-riepilogo.txt"
}

# V4: la cache salvata da probe-verdict (v1) si ripristina in un job pull_request (PR2) e in un job push (main)
modo_v4() {
  local ts br
  [ -s "$OUT/v1-verdict-runid.txt" ] || die "manca v1-verdict-runid.txt: lancia prima v1"
  clone_or_update protected
  ts="$(date +%Y%m%d-%H%M%S)"; br="p4-v4-$ts"
  open_pr v4 "$br" "sonde/v4-$ts.txt"
  save_text "$OUT/v4-pr.env" "PR=$PR_NUM" "SHA=$PR_SHA" "BRANCH=$br"
  track_run v4-run "$PROT" probe-run.yml "$PR_SHA" "$br" 0
  commit_on_main "sonde/v4-push-$ts.txt" "v4 push $ts"
  git_call v4-push-main protected push origin main
  [ "$RC" = 0 ] || die "push su main fallito (vedi v4-push-main.err)"
  save_text "$OUT/v4-push.env" "SHA=$MAIN_SHA"
  track_run v4-base "$PROT" probe-base.yml "$MAIN_SHA" "" 0
  gh_call v4-pr-close pr close "$PR_NUM" --repo "$PROT"
}

# V4b: dove si può scrivere una cache. probe-base (push) SALVA probe-v4b-<tag>; poi una PR: probe-run (pull_request)
# e probe-verdict (workflow_run) la RIPRISTINANO. Il tag (data e ora) è nuovo a ogni corsa: un salvataggio su una
# chiave esistente fallirebbe.
modo_v4b() {
  local ts br f
  clone_or_update protected
  ts="$(date +%Y%m%d-%H%M%S)"; br="p4-v4b-$ts"
  commit_on_main .github/probe-v4b-tag "$ts"
  git_call v4b-push-main protected push origin main
  [ "$RC" = 0 ] || die "push su main fallito (vedi v4b-push-main.err)"
  save_text "$OUT/v4b-push.env" "SHA=$MAIN_SHA" "TAG=$ts"
  track_run v4b-base "$PROT" probe-base.yml "$MAIN_SHA" "" 0
  open_pr v4b "$br" "sonde/v4b-$ts.txt"
  save_text "$OUT/v4b-pr.env" "PR=$PR_NUM" "SHA=$PR_SHA" "BRANCH=$br"
  track_run v4b-run "$PROT" probe-run.yml "$PR_SHA" "$br" 0
  track_run v4b-verdict "$PROT" probe-verdict.yml "$PR_SHA" "$br" 1
  gh_call v4b-pr-close pr close "$PR_NUM" --repo "$PROT"
  rot "$OUT/v4b-riepilogo.txt"
  {
    echo "# tag $ts; v4b_save per il salvataggio (base), v4b_cache_hit e v4b_matched_key per i ripristini"
    for f in "$OUT"/v4b-*-artifacts-*/info.json "$OUT"/v4b-*-artifacts-*/*/info.json; do
      [ -f "$f" ] || continue
      echo "# ${f#"$OUT"/}"
      jq -c '{v4b_tag, v4b_save, v4b_cache_hit, v4b_matched_key, v4b_value}' "$f" 2>&1
    done
  } > "$OUT/v4b-riepilogo.txt"
}

get_pulls() { # <etichetta> <sha>: GET commits/<sha>/pulls, con qualche ripetizione finché non è vuota
  local i
  for i in 1 2 3 4; do
    gh_q api "repos/$PROT/commits/$2/pulls" >"$WORK/pulls.json"
    [ "$(jq 'length' "$WORK/pulls.json" 2>/dev/null)" -gt 0 ] 2>/dev/null && break
    [ "$i" -lt 4 ] && sleep "$RETRY_SLEEP"
  done
  gh_call "$1" api "repos/$PROT/commits/$2/pulls"
  save_text "$OUT/$1.tentativi" "$i"
}

merge_pr() { # <etichetta> <pr> <--merge|--squash|--rebase>
  local i
  for i in 1 2 3 4 5; do
    gh_call "$1" pr merge "$2" --repo "$PROT" "$3"
    [ "$RC" = 0 ] && return 0
    sleep "$RETRY_SLEEP"
  done
  return 1
}

# V5: commits/<sha>/pulls per merge commit, squash, rebase e push diretto
modo_v5() {
  local ts kind flag d="$WORK/protected" before after sha pr
  local -a kinds=(merge squash rebase) flags=(--merge --squash --rebase) prs=()
  clone_or_update protected
  ts="$(date +%Y%m%d-%H%M%S)"
  for kind in "${kinds[@]}"; do
    open_pr "v5-$kind" "p4-v5-$kind-$ts" "sonde/v5-$kind-$ts.txt"
    prs+=("$PR_NUM")
  done
  rot "$OUT/v5-shas.txt" "$OUT/v5-riepilogo.tsv"
  : > "$OUT/v5-shas.txt"; : > "$OUT/v5-riepilogo.tsv"
  local i=0
  for kind in "${kinds[@]}"; do
    flag="${flags[$i]}"; pr="${prs[$i]}"; i=$((i + 1))
    git -C "$d" fetch -q origin; before="$(git -C "$d" rev-parse origin/main)"
    merge_pr "v5-$kind-merge" "$pr" "$flag" || { echo "merge $kind fallito" >&2; continue; }
    git -C "$d" fetch -q origin; after="$(git -C "$d" rev-parse origin/main)"
    for sha in $(git -C "$d" rev-list "$before..$after"); do
      get_pulls "v5-$kind-${sha:0:8}" "$sha"
      printf '%s %s\n' "$kind" "$sha" >> "$OUT/v5-shas.txt"
      printf '%s\t%s\t%s\n' "$kind" "$sha" "$(jq -c '[.[] | {number, state, merged_at, base: .base.ref}]' "$OUT/v5-$kind-${sha:0:8}.out" 2>&1)" >> "$OUT/v5-riepilogo.tsv"
    done
    [ "$before" = "$after" ] && printf '%s\t-\tnessun commit nuovo su origin/main\n' "$kind" >> "$OUT/v5-riepilogo.tsv"
  done
  commit_on_main "sonde/v5-diretto-$ts.txt" "v5 push diretto $ts"
  git_call v5-diretto-push protected push origin main
  [ "$RC" = 0 ] || die "push diretto fallito (vedi v5-diretto-push.err)"
  get_pulls "v5-diretto-${MAIN_SHA:0:8}" "$MAIN_SHA"
  printf 'diretto %s\n' "$MAIN_SHA" >> "$OUT/v5-shas.txt"
  printf '%s\t%s\t%s\n' diretto "$MAIN_SHA" "$(jq -c '[.[] | {number, state, merged_at, base: .base.ref}]' "$OUT/v5-diretto-${MAIN_SHA:0:8}.out" 2>&1)" >> "$OUT/v5-riepilogo.tsv"
}

# V5b: due PR aperte insieme, B costruita sopra la testa di A; commits/<testa>/pulls per entrambe (prima di unire A)
modo_v5b() {
  local ts br_a br_b pr_a pr_b sha_a sha_b
  clone_or_update protected
  ts="$(date +%Y%m%d-%H%M%S)"; br_a="p4-v5b-a-$ts"; br_b="p4-v5b-b-$ts"
  open_pr v5b-a "$br_a" "sonde/v5b-a-$ts.txt"
  pr_a="$PR_NUM"; sha_a="$PR_SHA"
  open_pr v5b-b "$br_b" "sonde/v5b-b-$ts.txt" protected "$br_a"
  pr_b="$PR_NUM"; sha_b="$PR_SHA"
  save_text "$OUT/v5b-pr.env" "PR_A=$pr_a" "SHA_A=$sha_a" "PR_B=$pr_b" "SHA_B=$sha_b"
  get_pulls v5b-pulls-testa-a "$sha_a"
  get_pulls v5b-pulls-testa-b "$sha_b"
  rot "$OUT/v5b-riepilogo.txt"
  {
    echo "# PR A=$pr_a (testa $sha_a), PR B=$pr_b (testa $sha_b, sopra A)"
    for f in v5b-pulls-testa-a v5b-pulls-testa-b; do
      echo "# $f: numero, state, head.sha, base.ref"
      jq -r '.[] | [(.number | tostring), .state, .head.sha, .base.ref] | @tsv' "$OUT/$f.out" 2>&1
    done
  } > "$OUT/v5b-riepilogo.txt"
  gh_call v5b-pr-close-a pr close "$pr_a" --repo "$PROT"
  gh_call v5b-pr-close-b pr close "$pr_b" --repo "$PROT"
}

# V6: stati e check-run di un job pull_request_target/workflow_run (PR1) e dei job push
modo_v6() {
  local kind sha SHA
  load_env "$OUT/v1-pr.env"
  gh_call v6-pr1-statuses api --paginate "repos/$PROT/commits/$SHA/statuses"
  gh_call v6-pr1-check-runs api "repos/$PROT/commits/$SHA/check-runs"
  if [ -s "$OUT/v4-push.env" ]; then
    # shellcheck disable=SC1090
    . "$OUT/v4-push.env"
    gh_call v6-v4push-statuses api --paginate "repos/$PROT/commits/$SHA/statuses"
    gh_call v6-v4push-check-runs api "repos/$PROT/commits/$SHA/check-runs"
  fi
  if [ -s "$OUT/v5-shas.txt" ]; then
    while read -r kind sha; do
      gh_call "v6-v5-$kind-${sha:0:8}-statuses" api --paginate "repos/$PROT/commits/$sha/statuses"
      gh_call "v6-v5-$kind-${sha:0:8}-check-runs" api "repos/$PROT/commits/$sha/check-runs"
    done < "$OUT/v5-shas.txt"
  fi
  rot "$OUT/v6-riepilogo.txt"
  {
    local f
    for f in "$OUT"/v6-*-statuses.out; do
      [ -f "$f" ] || continue
      echo "# $(basename "$f"): contesto, stato, creator.login"
      jq -r '.[] | [.context, .state, .creator.login] | @tsv' "$f" 2>&1
    done
    for f in "$OUT"/v6-*-check-runs.out; do
      [ -f "$f" ] || continue
      echo "# $(basename "$f"): nome, app.id, app.slug, stato, conclusione"
      jq -r '.check_runs[] | [.name, (.app.id | tostring), .app.slug, .status, .conclusion] | @tsv' "$f" 2>&1
    done
  } > "$OUT/v6-riepilogo.txt"
}

# V7: versione di gh sul runner e autenticazione con GH_TOKEN, dagli artefatti di probe-target (v1) e probe-base (v4)
modo_v7() {
  local f found=0
  rot "$OUT/v7-riepilogo.txt"
  : > "$OUT/v7-riepilogo.txt"
  for f in "$OUT"/v1-target-artifacts-*/info.json "$OUT"/v1-target-artifacts-*/*/info.json \
           "$OUT"/v4-base-artifacts-*/info.json "$OUT"/v4-base-artifacts-*/*/info.json; do
    [ -f "$f" ] || continue
    found=1
    echo "# ${f#"$OUT"/}" >> "$OUT/v7-riepilogo.txt"
    jq -c '{gh_version, gh_api_rc, gh_api_full_name, status_rc, status_creator, image_os, image_version}' "$f" >> "$OUT/v7-riepilogo.txt" 2>&1
  done
  [ "$found" = 1 ] || echo "non determinato: nessun info.json di probe-target o probe-base (lancia v1 e v4)" >> "$OUT/v7-riepilogo.txt"
}

# V8: artefatti con '..' e collegamenti simbolici; upload dal run di PR1, download dal job probe-verdict e da gh
modo_v8() {
  local id name f
  [ -s "$OUT/v1-run-runid.txt" ] || die "manca v1-run-runid.txt: lancia prima v1"
  id="$(cat "$OUT/v1-run-runid.txt")"
  case "$id" in ''|*[!0-9]*) die "v1-run-runid.txt non contiene un numero: $id" ;; esac
  gh_call v8-artefatti api "repos/$PROT/actions/runs/$id/artifacts"
  for name in probe-run-dotdot-out probe-run-dotdot-in probe-run-symlink; do
    gh_call "v8-dl-$name" run download "$id" --repo "$PROT" -n "$name" -D "$OUT/v8-dl-$name-$id"
  done
  rot "$OUT/v8-find.txt" "$OUT/v8-listing-verdict.txt"
  find "$OUT"/v8-dl-*-"$id" -printf '%y %p -> %l\n' > "$OUT/v8-find.txt" 2>&1
  : > "$OUT/v8-listing-verdict.txt"
  for f in "$OUT"/v1-verdict-artifacts-*/listing.txt "$OUT"/v1-verdict-artifacts-*/*/listing.txt; do
    [ -f "$f" ] || continue
    echo "# ${f#"$OUT"/}" >> "$OUT/v8-listing-verdict.txt"
    cat "$f" >> "$OUT/v8-listing-verdict.txt"
  done
}

# V9: GET actions/permissions sui due repo
modo_v9() {
  gh_call v9-protected api "repos/$PROT/actions/permissions"
  gh_call v9-detect api "repos/$DET/actions/permissions"
}

modo_raccogli() {
  local id ids
  gh_call raccogli-versione-gh --version
  gh_call raccogli-runs-protected run list --repo "$PROT" --limit 100 \
    --json databaseId,workflowName,event,headSha,headBranch,status,conclusion,createdAt,updatedAt
  gh_call raccogli-runs-detect run list --repo "$DET" --limit 100 \
    --json databaseId,workflowName,event,headSha,headBranch,status,conclusion,createdAt,updatedAt
  gh_call raccogli-pr pr list --repo "$PROT" --state all --limit 100 \
    --json number,title,state,headRefName,headRefOid,baseRefName,mergedAt,isCrossRepository,mergeStateStatus
  ids="$(jq -r '.[].databaseId' "$OUT/raccogli-runs-protected.out" 2>/dev/null)"
  for id in $ids; do
    gh_call "raccogli-timing-$id" api "repos/$PROT/actions/runs/$id/timing"
  done
  rot "$OUT/raccogli-minuti.txt"
  {
    echo "run sul repo protected (pubblico, minuti non fatturati): $(echo "$ids" | grep -c .)"
    echo "run sul repo detect (privato): $(jq 'length' "$OUT/raccogli-runs-detect.out" 2>&1)"
    for id in $ids; do
      cat "$OUT/raccogli-timing-$id.out" 2>/dev/null
      echo
    done | jq -s '{run_duration_ms_totale: ([.[].run_duration_ms // 0] | add), run: length}' 2>&1
  } > "$OUT/raccogli-minuti.txt"
}

modo_pulisci_sonde() {
  local n d files
  for n in protected detect; do
    clone_or_update "$n"
    d="$WORK/$n"
    files="$(ls "$d"/.github/workflows/probe-*.yml "$d"/.github/probe-tag "$d"/.github/probe-v4b-tag 2>/dev/null)"
    if [ -z "$files" ]; then
      save_text "$OUT/pulisci-$n.txt" "nulla da togliere su $n"
      continue
    fi
    # shellcheck disable=SC2086
    git -C "$d" rm -q $files || die "git rm fallito su $n"
    git -C "$d" commit -qm "togli i workflow sonda (tollgate P4)" || die "commit di pulizia fallito su $n"
    git_call "pulisci-push-$n" "$n" push origin main
    [ "$RC" = 0 ] || die "push di pulizia fallito su $n (vedi pulisci-push-$n.err)"
    save_text "$OUT/pulisci-$n.txt" "sonde tolte: $(git -C "$d" rev-parse HEAD)"
  done
}

# ---------------------------------------------------------------- controlla (nessuna rete)

write_fake_gh() { # <file>
  cat > "$1" <<'FAKE'
#!/usr/bin/env bash
# gh finto del modo controlla: registra gli argomenti, nessuna rete
printf '%s\t' "$@" >> "$P4_FAKE_LOG"; printf '\n' >> "$P4_FAKE_LOG"
st="$P4_FAKE_STATE"; mkdir -p "$st"
counter() { local n; n="$(cat "$st/$1" 2>/dev/null || echo "$2")"; n=$((n + 1)); echo "$n" > "$st/$1"; echo "$n"; }
ident=(-c user.name=fake -c user.email=fake@example.invalid)
case "${1:-}" in
  --version) echo "gh version 2.46.0 (finto)"; exit 0 ;;
  auth) echo "Logged in to github.com account ginz0ls (finto)"; echo "- Token scopes: 'repo', 'workflow'"; exit 0 ;;
  repo)
    case "$2" in
      create)
        bare="$P4_GIT_BASE/$3.git"; mkdir -p "$(dirname "$bare")"; git init -q --bare -b main "$bare"
        tmp="$(mktemp -d)"; git clone -q "$bare" "$tmp/s" 2>/dev/null
        echo "# $3" > "$tmp/s/README.md"; git -C "$tmp/s" add README.md
        git -C "$tmp/s" "${ident[@]}" commit -qm init; git -C "$tmp/s" branch -M main; git -C "$tmp/s" push -q origin main
        exit 0 ;;
      clone) git clone -q "$P4_GIT_BASE/$3.git" "$4"; exit $? ;;
    esac ;;
  api)
    ep=""; incl=0; skip=0
    for a in "${@:2}"; do
      if [ "$skip" = 1 ]; then skip=0; continue; fi
      case "$a" in
        --include) incl=1 ;;
        --jq|-q|-H|--header|--hostname|--cache|-t|--template) skip=1 ;;
        -*) ;;
        *) [ -n "$ep" ] || ep="$a" ;;
      esac
    done
    case "$ep" in
      repos/*/*/branches/main/protection)
        if [[ "$ep" == *detect* ]]; then
          [ "$incl" = 1 ] && printf 'HTTP/2.0 403 Forbidden\r\n\r\n'
          echo '{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","status":"403"}'
          echo "gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)" >&2
        else
          [ "$incl" = 1 ] && printf 'HTTP/2.0 404 Not Found\r\n\r\n'
          echo '{"message":"Branch not protected","status":"404"}'
          echo "gh: Branch not protected (HTTP 404)" >&2
        fi
        exit 1 ;;
      repos/*/*/actions/permissions) echo '{"enabled":true,"allowed_actions":"all"}' ;;
      repos/*/*/actions/runs/*/timing) echo '{"billable":{},"run_duration_ms":60000}' ;;
      repos/*/*/actions/runs/*/artifacts) echo '{"total_count":1,"artifacts":[{"name":"probe-run-info","size_in_bytes":10,"expired":false}]}' ;;
      repos/*/*/commits/*/pulls) echo '[{"number":1,"state":"closed","merged_at":"2026-01-01T00:00:00Z","base":{"ref":"main"}}]' ;;
      repos/*/*/commits/*/statuses) echo '[{"context":"probe/target","state":"success","creator":{"login":"github-actions[bot]"}}]' ;;
      repos/*/*/commits/*/check-runs) echo '{"total_count":1,"check_runs":[{"name":"base","app":{"id":15368,"slug":"github-actions"},"status":"completed","conclusion":"success"}]}' ;;
      repos/*/*/issues/*/comments)
        echo '[{"id":1,"user":{"login":"github-actions[bot]","type":"Bot"},"body":"x"}]' ;;
      repos/*/*)
        if [ -d "$P4_GIT_BASE/${ep#repos/}.git" ]; then echo '{"full_name":"x","private":false,"default_branch":"main"}'
        else echo "gh: Not Found (HTTP 404)" >&2; exit 1; fi ;;
      *) echo '{}' ;;
    esac
    exit 0 ;;
  pr)
    case "$2" in
      create)
        n="$(counter pr 0)"; head=""
        for ((i = 1; i <= $#; i++)); do [ "${!i}" = --head ] && { j=$((i + 1)); head="${!j}"; }; done
        echo "$head" > "$st/pr-$n"
        echo "https://github.com/ginz0ls/tollgate-p4-protected/pull/$n"; exit 0 ;;
      merge)
        br="$(cat "$st/pr-$3")"; mode=""
        for a in "$@"; do case "$a" in --merge|--squash|--rebase) mode="$a" ;; esac; done
        tmp="$(mktemp -d)"; git clone -q "$P4_GIT_BASE/ginz0ls/tollgate-p4-protected.git" "$tmp/m"
        git -C "$tmp/m" fetch -q origin "$br"
        case "$mode" in
          --merge) git -C "$tmp/m" "${ident[@]}" merge -q --no-ff -m "merge $br" FETCH_HEAD ;;
          --squash) git -C "$tmp/m" merge -q --squash FETCH_HEAD && git -C "$tmp/m" "${ident[@]}" commit -qm "squash $br" ;;
          --rebase) git -C "$tmp/m" "${ident[@]}" cherry-pick FETCH_HEAD >/dev/null ;;
        esac
        git -C "$tmp/m" push -q origin HEAD:main; exit $? ;;
      list) echo '[{"number":1,"headRefName":"x","headRefOid":"x","mergedAt":null,"isCrossRepository":false,"mergeStateStatus":"CLEAN"}]'; exit 0 ;;
      view) echo '{"comments":[{"author":{"login":"github-actions"},"body":"x"},{"author":{"login":"ginz0ls"},"body":"y"}]}'; exit 0 ;;
      *) exit 0 ;;
    esac ;;
  run)
    case "$2" in
      list)
        n="$(counter run 100)"
        printf '[{"databaseId":%s,"headSha":"%s","headBranch":"%s","event":"x","status":"completed","conclusion":"success","createdAt":"2099-01-01T00:00:00Z"}]\n' "$n" "$P4_WAIT_SHA" "$P4_WAIT_BRANCH"
        exit 0 ;;
      watch) echo "Run completed (finto)"; exit 0 ;;
      view) echo '{"databaseId":1,"status":"completed","conclusion":"success","jobs":[{"name":"base"}]}'; exit 0 ;;
      download)
        dir=""
        for ((i = 1; i <= $#; i++)); do [ "${!i}" = -D ] && { j=$((i + 1)); dir="${!j}"; }; done
        mkdir -p "$dir"
        echo '{"gh_version":"gh version finto","gh_api_rc":0,"gh_api_full_name":"x","status_rc":0,"status_creator":"github-actions[bot]"}' > "$dir/info.json"
        echo '{"event_keys":["a"]}' > "$dir/event-keys.json"
        echo 'f x -> ' > "$dir/listing.txt"
        exit 0 ;;
    esac ;;
esac
echo "gh finto: comando non previsto: $*" >&2
exit 2
FAKE
  chmod +x "$1"
}

# Controlla il registro dei comandi del gh finto con la stessa lista degli ammessi di guard_args
check_gh_log() { # <registro>
  python3 -B -I "$here/ghguard.py" log "$1"
}

# Prova negativa: ogni comando vietato deve fermare guard_args e dare una violazione in check_gh_log
check_negativi() { # <cartella>
  local T="$1" n=0 stopped=0 viol cmd
  local -a forbidden=(
    "api user" "api /user" "api graphql"
    "api --method=POST repos/$PROT/issues" "api -XPOST repos/$PROT/issues" "api -X POST repos/$PROT/issues"
    "api -fstate=x repos/$PROT/statuses/abc" "api -F a=b repos/$PROT/issues" "api --field=a=b repos/$PROT/issues"
    "api --raw-field=a=b repos/$PROT/issues" "api --input=x repos/$PROT/issues" "api -H X:y repos/$PROT"
    "api repos/$PROT/../../user" "api repos/$PROT//x" "api repos/$PROT/%2e%2e/x" "api repos/${OWNER}/altro/x" "api repos/${PROT}x/y"
    "run delete 1 --repo $PROT" "run cancel 1 --repo $PROT" "run rerun 1 --repo $PROT" "run list"
    "pr review 1 --repo $PROT" "pr ready 1 --repo $PROT" "pr checkout 1 --repo $PROT" "pr list" "pr list --repo ${OWNER}/altro"
    "pr merge 1 --repo $PROT --admin" "issue delete 1 --repo $DET" "issue transfer 1 --repo $DET" "issue pin 1 --repo $DET"
    "repo create $PROT --public --source=." "repo create $PROT --public --push" "repo create ${OWNER}/altro --public"
    "repo create $PROT --private --add-readme --visibility public" "repo create $PROT" "repo delete $PROT"
    "repo edit $PROT --visibility public" "repo fork $PROT" "auth login" "auth refresh" "auth status --show-token"
    "secret set X" "ssh-key add" "extension install x" "--version --help"
    "pr view https://github.com/altro/x/pull/1 --repo $PROT" "pr view altro/x#1 --repo $PROT" "pr view 1 --repo $PROT --web"
    "pr list --repo $PROT -Raltro/x" "pr list --repo $PROT --repo $DET" "pr list --repo=altro/x" "pr list --repo $PROT -R $DET"
    "pr comment 1 --repo $PROT --body-file /etc/passwd" "pr comment 1 2 --repo $PROT --body x" "pr merge 1 --repo $PROT"
    "pr merge 1 --repo $PROT --merge --squash" "pr merge 1 --repo $PROT --merge --delete-branch" "pr create --repo $PROT --fill"
    "run download 1 --repo $PROT -D /etc" "run download 1 --repo $PROT -D $P4_OUT/../x" "run download 1 --repo $PROT -D$P4_OUT/../x"
    "run download 1 --repo $PROT -D relativa" "run download 1 --repo $PROT -n ../x" "run view abc --repo $PROT"
    "run view 1 --repo $PROT --exit-status" "run watch 1 --repo $PROT --json id"
    "api repos/$PROT/issues?x=1/../../" "api repos/$PROT/issues?x=%2e%2e" "api repos/$PROT/issues?x=a//b" "api repos/$PROT/./issues"
    "repo clone $PROT /etc/clone"
  )
  local -a allowed=(
    "pr view 1 --repo=$PROT --json comments" "pr view p4-v1-x/y --repo $PROT --json comments,number"
    "pr list --repo $DET --state all --limit 100 --json number,title" "pr merge 3 --repo $PROT --squash"
    "run download 5 --repo $DET -D $P4_OUT/a -n probe-fetch" "run list --repo $PROT --workflow probe-run.yml --limit 30 --json databaseId"
    "run view 5 --repo $PROT --log" "api --paginate repos/$PROT/issues/1/comments" "api repos/$DET/actions/caches?per_page=100"
    "repo clone $PROT $P4_WORK/protected -- -q"
  )
  : > "$T/negativi.log"
  for cmd in "${forbidden[@]}"; do
    n=$((n + 1))
    # shellcheck disable=SC2086
    if ( guard_args $cmd ) >/dev/null 2>&1; then
      echo "  NON FERMATO da guard_args: $cmd"
    else
      stopped=$((stopped + 1))
    fi
    # shellcheck disable=SC2086
    printf '%s\t' $cmd >> "$T/negativi.log"; printf '\n' >> "$T/negativi.log"
  done
  viol="$(check_gh_log "$T/negativi.log" | grep -c '^VIOLAZIONE')"
  echo "  guard_args: $stopped fermati su $n; check_gh_log: $viol violazioni su $n"
  local ok=0
  for cmd in "${allowed[@]}"; do
    # shellcheck disable=SC2086
    if ( guard_args $cmd ) >/dev/null 2>&1; then ok=$((ok + 1)); else echo "  AMMESSO MA RIFIUTATO: $cmd"; fi
  done
  echo "  comandi legittimi ammessi: $ok su ${#allowed[@]}"
  [ "$stopped" = "$n" ] && [ "$viol" -ge "$n" ] && [ "$ok" = "${#allowed[@]}" ]
}

# Nessuna ${{ }} dentro le righe run: dei workflow sonda (decisione 17); il YAML deve leggersi
check_workflows() {
  python3 -B -I - "$here"/workflows/probe-*.yml <<'PY'
import re, sys
bad = 0
for path in sys.argv[1:]:
    lines = open(path).read().split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", lines[i])
        if not m or not m.group(2):   # un job chiamato "run" non è una riga run:
            i += 1
            continue
        key_indent = len(m.group(1)) + (2 if lines[i].lstrip().startswith("-") else 0)
        block = [m.group(2)] if m.group(2) not in ("|", ">", "|-", ">-") else []
        i += 1
        while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > key_indent):
            block.append(lines[i]); i += 1
        if any("${{" in b for b in block):
            print("espressione dentro run: in %s" % path); bad += 1
try:
    import yaml
    for path in sys.argv[1:]:
        yaml.safe_load(open(path))
except ImportError:
    print("PyYAML assente: sintassi YAML non verificata")
sys.exit(1 if bad else 0)
PY
}

modo_controlla() {
  local T mode f rc=0 missing=0 url
  bash -n "$here/run-p4-checks.sh" || die "bash -n fallito"
  check_workflows || die "controllo dei workflow sonda fallito"
  T="${P4_CHECK_DIR:-$(mktemp -d /tmp/tollgate-p4-controlla.XXXXXX)}"
  mkdir -p "$T/bin" "$T/remote" "$T/out" "$T/work"
  write_fake_gh "$T/bin/gh"
  export P4_CHECK=1 P4_OUT="$T/out" P4_WORK="$T/work" P4_GIT_BASE="$T/remote" \
         P4_FAKE_LOG="$T/gh.log" P4_FAKE_STATE="$T/fake" P4_WAIT_MAX=5 P4_POLL=0 P4_RETRY_SLEEP=0
  export PATH="$T/bin:$PATH"
  [ "$(command -v gh)" = "$T/bin/gh" ] || die "il gh finto non è il primo nel PATH"
  : > "$P4_FAKE_LOG"
  echo "cartella del controllo: $T"
  for mode in prepara v1 v2 v3 v3b v4 v4b v5b v5 v6 v7 v8 v9 raccogli pulisci-sonde; do
    if bash "$here/run-p4-checks.sh" "$mode" >"$T/modo-$mode.log" 2>&1; then
      echo "modo $mode: ok"
    else
      echo "modo $mode: FALLITO (vedi $T/modo-$mode.log)"; tail -n 5 "$T/modo-$mode.log"; rc=1
    fi
  done
  echo "--- registro dei comandi gh"
  check_gh_log "$P4_FAKE_LOG" || rc=1
  echo "--- prova negativa della guardia"
  check_negativi "$T" || { echo "PROVA NEGATIVA FALLITA"; rc=1; }
  echo "--- comandi veri del controller (comandi.log delle evidenze)"
  if [ -f "$root/docs/verifiche/evidenze/gh-p4/comandi.log" ]; then
    env -u P4_OUT -u P4_WORK python3 -B -I "$here/ghguard.py" comandi "$root/docs/verifiche/evidenze/gh-p4/comandi.log" | grep -v "^ *[0-9]* *gh " || true
    env -u P4_OUT -u P4_WORK python3 -B -I "$here/ghguard.py" comandi "$root/docs/verifiche/evidenze/gh-p4/comandi.log" >/dev/null || { echo "COMANDI VERI RIFIUTATI"; rc=1; }
  else
    echo "  comandi.log assente: salto"
  fi
  echo "--- remoti dei cloni"
  for f in protected detect; do
    url="$(git -C "$T/work/$f" remote get-url --push origin 2>&1)"
    echo "  $f -> $url"
    case "$url" in "$T/remote/"*) ;; *) echo "REMOTO FUORI DAL BANCO: $f"; rc=1 ;; esac
  done
  echo "--- uscite attese"
  for f in prepara-auth.out prepara-protected-esiste.rc v1-pr.env v1-target-runid.txt v1-run-runid.txt v1-verdict-runid.txt \
           v1-pr-view-comments.out v1-api-comments.out v1-login.txt v2-detect.out v2-detect.err v2-detect.rc v2-protected.rc \
           v3-riepilogo.jsonl v3b-pr.env v3b-riepilogo.txt v4b-pr.env v4b-push.env v4b-riepilogo.txt v5b-pr.env v5b-riepilogo.txt v4-pr.env v4-push.env v4-base-runid.txt v5-shas.txt v5-riepilogo.tsv v6-riepilogo.txt \
           v7-riepilogo.txt v8-find.txt v8-artefatti.out v9-protected.out v9-detect.out raccogli-runs-protected.out \
           raccogli-minuti.txt pulisci-protected.txt pulisci-detect.txt comandi.log; do
    [ -e "$T/out/$f" ] || { echo "  manca $f"; missing=1; }
  done
  [ "$missing" = 0 ] && echo "  tutte presenti"
  [ "$missing" = 0 ] || rc=1
  echo "--- nel banco di prova, i rami e i commit"
  git -C "$T/remote/ginz0ls/tollgate-p4-protected.git" log --oneline main | head -n 12
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

case "$MODE" in
  prepara|v1|v2|v3|v3b|v4|v4b|v5|v5b|v6|v7|v8|v9|raccogli)
    mkdir -p "$OUT" "$WORK"; "modo_$MODE" ;;
  pulisci-sonde) mkdir -p "$OUT" "$WORK"; modo_pulisci_sonde ;;
  controlla) modo_controlla ;;
  *) echo "uso: $0 prepara|v1|v2|v3|v3b|v4|v4b|v5|v5b|v6|v7|v8|v9|raccogli|pulisci-sonde|controlla" >&2; exit 2 ;;
esac
