#!/usr/bin/env bash
# spikes/p5/run-p5-checks.sh — verifiche reali di P5 (Task 1: VE1-VE10 su `claude plugin eval`, VC1/VC2 sulla CI e sugli
# SHA delle azioni, VG1/VG2 su detect). Lo esegue solo il controller. Modo `controlla`: nessuna rete, `gh` e `claude` finti.
# Uso: run-p5-checks.sh eval-sonda | ci-sonda | pins | detect-cache | detect-pin | raccogli | cerca-token | controlla
#
# Regole (decisioni 20-22): ogni `gh` passa da ghguard.py col profilo p5 (P4_PROFILE=p5); ogni git con la rete passa da
# `ghguard.py gitcheck` (git_net); mai un --force, mai un repo diverso da ginz0ls/tollgate e ginz0ls/tollgate-p4-detect.
# Nessuna cartella di uscite si cancella mai: un file che esiste già si rinomina in <nome>.prev-<tempo>.
# Uscite: docs/verifiche/evidenze/p5/ (GitHub) e docs/verifiche/evidenze/eval-p5/ (eval, con il registro budget.tsv).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
GH4="$root/spikes/gh-p4"
MODE="${1:-}"

OWNER=ginz0ls
TOL="$OWNER/tollgate"                 # privato, il repo del plugin (creato da ci-sonda)
DET="$OWNER/tollgate-p4-detect"       # privato, GitHub Free, modalità detect
TOL_URL="https://github.com/$TOL.git"
DET_URL="https://github.com/$DET.git"
OUT="${P5_OUT:-$root/docs/verifiche/evidenze/p5}"
EOUT="${P5_EVAL_OUT:-$root/docs/verifiche/evidenze/eval-p5}"
WORK="${P5_WORK:-/tmp/tollgate-p5}"                  # cloni di lavoro, non sono uscite
PINS="${P5_PINS:-/tmp/tollgate-p5-pins}"             # cloni per la lettura di action.yml
SOURCE="${P5_SOURCE_DIR:-$root}"                     # repo di cui si cerca la storia e da cui si clona main
WAIT_MAX="${P5_WAIT_MAX:-3000}"                      # tetto di attesa per ogni run, in secondi
POLL="${P5_POLL:-15}"
RETRY_SLEEP="${P5_RETRY_SLEEP:-5}"
RETRIES="${P5_RETRIES:-3}"                           # ritentativi di una lettura che risponde 500
CHECK="${P5_CHECK:-0}"                               # 1 solo dentro il modo controlla
BUDGET_TOTAL=80                                      # USD complessivi di costUsd (decisione 8)
CAP_MAX=3                                            # USD per invocazione delle sonde
MODEL=claude-sonnet-5-5
unset GH_REPO GH_HOST GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN GIT_DIR GIT_WORK_TREE GIT_CONFIG_COUNT GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
# ghguard.py li legge: -D e i cloni devono stare qui sotto; il registro delle PR aperte è per questa prova
export P4_OUT="$OUT" P4_WORK="$WORK" P5_PINS="$PINS" P4_PROFILE=p5 P5_PR_REGISTRY="$OUT/prs-aperte.txt"

. "$GH4/common.sh"          # die, rot, log_cmd, gh_call, gh_q, save_text, wait_run (guard_args chiama ghguard.py col profilo p5)
# anche i sondaggi (gh_q) restano in comandi.log: ogni gh eseguito dallo script è registrato
gh_q() { guard_args "$@"; log_cmd "gh $*"; gh "$@" 2>/dev/null </dev/null; }
for _dir in "$OUT" "$EOUT" "$WORK" "$PINS"; do
  case "$_dir" in /*) ;; *) die "i percorsi P5_OUT, P5_EVAL_OUT, P5_WORK e P5_PINS devono essere assoluti: $_dir" ;; esac
done

# ---------------------------------------------------------------- git con la rete

# no_rewrite_rules <cartella>: nessuna regola url.*.insteadOf nelle configurazioni che git legge (reindirizzerebbe un push)
no_rewrite_rules() {
  local d="$1"
  [ -d "$d" ] || d="."
  if env -u GIT_CONFIG_COUNT git -C "$d" config --get-regexp '^url\..*\.(insteadof|pushinsteadof)$' >/dev/null 2>&1; then
    die "la configurazione di git riscrive degli URL (url.*.insteadOf): mi fermo"
  fi
}

# git_net <etichetta> <cartella|-> <argomenti di git senza -C>: il bersaglio lo controlla `ghguard.py gitcheck` (push solo
# verso tollgate e detect, mai forzato; ls-remote/fetch solo dei tag di actions/*; clone solo di detect), poi git gira con
# stdout, stderr e codice d'uscita in tre file. Nel modo controlla gli URL di github.com/ginz0ls e /actions vanno ai nudi locali.
git_net() {
  local label="$1" dir="$2" msg; shift 2
  if [ "$dir" = - ]; then
    msg="$(python3 -B -I "$GH4/ghguard.py" gitcheck -- "$@" 2>&1)" || die "git $*: $msg"
  else
    msg="$(python3 -B -I "$GH4/ghguard.py" gitcheck --dir "$dir" -- "$@" 2>&1)" || die "git $*: $msg"
  fi
  no_rewrite_rules "$dir"
  rot "$OUT/$label".out "$OUT/$label".err "$OUT/$label".rc
  log_cmd "git-net dir=$dir $*"
  local -a genv=(env GIT_TERMINAL_PROMPT=0)      # senza credenziali git fallisce, non chiede su /dev/tty
  if [ "$CHECK" = 1 ] && [ -n "${P5_GIT_BASE:-}" ]; then
    genv+=(GIT_CONFIG_COUNT=2
           "GIT_CONFIG_KEY_0=url.$P5_GIT_BASE/$OWNER/.insteadOf" "GIT_CONFIG_VALUE_0=https://github.com/$OWNER/"
           "GIT_CONFIG_KEY_1=url.$P5_GIT_BASE/actions/.insteadOf" "GIT_CONFIG_VALUE_1=https://github.com/actions/")
  fi
  if [ "$dir" = - ] || [ "$1" = clone ]; then
    "${genv[@]}" git "$@" >"$OUT/$label.out" 2>"$OUT/$label.err" </dev/null
  else
    "${genv[@]}" git -C "$dir" "$@" >"$OUT/$label.out" 2>"$OUT/$label.err" </dev/null
  fi
  RC=$?
  echo "$RC" >"$OUT/$label.rc"
  return 0
}

# ---------------------------------------------------------------- letture con ritentativo

# gh_read <etichetta> <argomenti di gh...>: come gh_call, ma una lettura che risponde 500 (anche a corpo vuoto) si ritenta
# fino a RETRIES volte; ogni tentativo resta (i file precedenti diventano <nome>.prev-<tempo>, ogni chiamata è in comandi.log).
# Le scritture non passano da qui, salvo quelle idempotenti (gh_write_idem).
gh_read() {
  local label="$1" n=0; shift
  while :; do
    gh_call "$label" "$@"
    [ "$RC" = 0 ] && return 0
    if grep -Eq 'HTTP 5[0-9][0-9]' "$OUT/$label.err" 2>/dev/null && [ "$n" -lt "$RETRIES" ]; then
      n=$((n + 1))
      printf '%s %s tentativo %d dopo un 5xx\n' "$(date -u +%FT%TZ)" "$label" "$n" >> "$OUT/ritentativi.log"
      sleep "$RETRY_SLEEP"
      continue
    fi
    return 0
  done
}
gh_write_idem() { gh_read "$@"; }      # solo per scritture idempotenti (PUT con lo stesso corpo)

# add_run <etichetta> <repo> <id> <conclusione>: elenco dei run da cui `raccogli` prende i minuti
add_run() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$OUT/runs.tsv"; }

# fresh_branch <repo> <nome>: imposta BR a <nome>, o a <nome>-<ora> se il ramo esiste già sul repo (mai un push non-ff)
fresh_branch() {
  gh_read "ramo-$2" api "repos/$1/branches/$2"
  if [ "$RC" = 0 ]; then BR="$2-$(date +%Y%m%d-%H%M%S)"; else BR="$2"; fi
}

# ---------------------------------------------------------------- ricerca di token (decisione 20)

# cerca_token <repo>: forme di token in TUTTA la storia (git rev-list --all) con git grep. Stampa solo `commit:percorso`,
# mai il testo trovato. Esce 1 se trova qualcosa che non è ammesso esplicitamente. P5_TOKEN_ALLOW_PATHS (percorsi esatti
# separati da `:`) ammette un file: ogni suo uso è stampato e scritto in token-scan.txt come AMMESSO, mai in silenzio.
# Il modello cerca prefisso + almeno 8 caratteri di token (o 16 per AKIA): il prefisso da solo compare in testi e regex.
TOKEN_PATTERN='gh[pos]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|sk-ant-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}'
cerca_token() {
  local repo="$1" res err i rc hits=0 allowed=0 line path allow=":${P5_TOKEN_ALLOW_PATHS:-}:"
  local -a revs chunk
  mkdir -p "$OUT"
  rot "$OUT/token-scan.txt"
  res="$(mktemp "${TMPDIR:-/tmp}/tollgate-p5-token.XXXXXX")"
  err="$res.err"
  mapfile -t revs < <(git -C "$repo" rev-list --all 2>/dev/null)
  [ "${#revs[@]}" -gt 0 ] || { rm -f "$res"; die "cerca_token: nessun commit in $repo"; }
  for ((i = 0; i < ${#revs[@]}; i += 40)); do
    chunk=("${revs[@]:i:40}")
    git -C "$repo" grep -l -I -E -e "$TOKEN_PATTERN" "${chunk[@]}" -- >>"$res" 2>>"$err"
    rc=$?
    [ "$rc" -le 1 ] || { rm -f "$res" "$err"; die "cerca_token: git grep fallito (codice $rc)"; }
  done
  : > "$OUT/token-scan.txt"
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    path="${line#*:}"
    case "$allow" in
      *":$path:"*) allowed=$((allowed + 1)); echo "AMMESSO (P5_TOKEN_ALLOW_PATHS) ${line:0:12} $path" >> "$OUT/token-scan.txt" ;;
      *) hits=$((hits + 1)); echo "TROVATO ${line:0:12} $path" >> "$OUT/token-scan.txt" ;;
    esac
  done < <(sort -u "$res")
  rm -f "$res" "$err"
  echo "cerca-token: ${#revs[@]} commit controllati, $hits file con forme di token, $allowed ammessi esplicitamente"
  cat "$OUT/token-scan.txt"
  [ "$hits" = 0 ]
}

# ---------------------------------------------------------------- registro dei costi (decisione 8)

BUDGET="$EOUT/budget.tsv"
BUDGET_HEADER=$'ora\tinvocazione\tcostUsd\tdurationSeconds\tcasi'

ensure_budget() {
  mkdir -p "$EOUT"
  [ -s "$BUDGET" ] || printf '%s\n' "$BUDGET_HEADER" > "$BUDGET"
  [ "$(head -n 1 "$BUDGET")" = "$BUDGET_HEADER" ] || die "intestazione di budget.tsv inattesa: controlla a mano"
}

# budget_cap: stampa il minimo tra CAP_MAX e il residuo (BUDGET_TOTAL meno la somma dei costUsd), in centesimi per difetto;
# esce 1 (senza stampare) se non c'è residuo positivo o se una riga non è leggibile.
budget_cap() {
  awk -F'\t' -v total="$BUDGET_TOTAL" -v cap="$CAP_MAX" '
    NR == 1 { next }
    NF == 0 { next }
    $3 !~ /^[0-9]+(\.[0-9]+)?$/ { bad = 1 }
    { spent += $3 }
    END {
      if (bad) exit 1
      left = total - spent
      if (left < 0.01) exit 1
      m = (left < cap) ? left : cap
      printf "%.2f\n", int(m * 100 + 1e-9) / 100
    }' "$BUDGET"
}

# ---------------------------------------------------------------- eval della sonda

# copy_one_run <cartella della corsa tenuta> <cartella di evidenza>: le corse tenute da --keep-temp sono in
# <TMPDIR>/claude-eval-<sigla>/ con out/trace.jsonl e config/settings.json leggibili e home/ e tmp/ sigillati in sealed/ (modo 000):
# si rendono leggibili (chmod 700 della corsa e di sealed) e si copiano SOLO la trace, settings.json (se non contiene credenziali),
# i file della sonda del workspace (sealed/home/cwd), lo stato della sonda e il registro dei plugin scritto dallo scaffold.
SONDA_FILES=(-name 'sonda-*' -o -name esiti.txt -o -name scritto-da-hook.md -o -name ws-file -o -name NEGATO -o -name AMMESSO
             -o -name WT-OK -o -name EW-OK -o -name SONDA-WRITE)
copy_one_run() {
  local run="$1" evid="$2" dest f n=0 name
  name="$(basename "$run")"
  dest="$evid/corse/$name"
  [ -d "$run" ] || { echo "corsa non trovata: $run"; return 1; }
  chmod 700 "$run" 2>/dev/null; [ -d "$run/sealed" ] && chmod 700 "$run/sealed" 2>/dev/null
  mkdir -p "$dest"
  if [ -f "$run/out/trace.jsonl" ]; then cp -n -- "$run/out/trace.jsonl" "$dest/trace.jsonl" && n=$((n + 1)); fi
  if [ -f "$run/config/settings.json" ]; then
    if grep -qiE "$TOKEN_PATTERN|\"[A-Za-z_]*(token|api_?key|secret|password)[A-Za-z_]*\"[[:space:]]*:[[:space:]]*\"[^\"]+\"" "$run/config/settings.json"; then
      echo "settings.json contiene forme di credenziali: non copiato" > "$dest/settings-non-copiato.txt"
    else
      cp -n -- "$run/config/settings.json" "$dest/settings.json" && n=$((n + 1))
    fi
  fi
  if [ -d "$run/sealed/home/cwd" ]; then
    while IFS= read -r f; do
      mkdir -p "$dest/cwd/$(dirname "${f#"$run/sealed/home/cwd/"}")"
      cp -n -- "$f" "$dest/cwd/${f#"$run/sealed/home/cwd/"}" && n=$((n + 1))
    done < <(find "$run/sealed/home/cwd" -maxdepth 6 -type f -size -300k \( "${SONDA_FILES[@]}" \) 2>/dev/null)
  fi
  for f in .local/state/sonda/hooks.jsonl .local/state/sonda/bin-sonda.txt .claude/plugins/installed_plugins.json; do
    if [ -f "$run/sealed/home/$f" ]; then
      mkdir -p "$dest/home/$(dirname "$f")"
      cp -n -- "$run/sealed/home/$f" "$dest/home/$f" && n=$((n + 1))
    fi
  done
  echo "corsa $name: $n file copiati in ${dest#"$root/"}"
}

# copy_run_files <cartella dell'invocazione>: le corse tenute sono quelle che claude stampa in stderr («kept <cartella>:»)
copy_run_files() {
  local dir="$1" run
  grep -ahoE "kept (/[^[:space:]:]+)" "$dir/stdout.txt" "$dir/stderr.txt" 2>/dev/null | sed 's/^kept //' | sort -u > "$dir/cartelle-tenute.txt"
  while IFS= read -r run; do
    case "$run" in */claude-eval-*) copy_one_run "$run" "$dir" ;; *) echo "cartella tenuta ignorata (fuori dallo schema claude-eval-*): $run" ;; esac
  done < "$dir/cartelle-tenute.txt"
}

# raccogli-corse <cartella della corsa>...: la stessa copia per corse già fatte; la cartella di evidenza è quella il cui
# result.json ha una tracePath dentro la corsa
modo_raccogli_corse() {
  local run evid r
  [ "$#" -gt 0 ] || die "uso: raccogli-corse <cartella della corsa tenuta>..."
  mkdir -p "$EOUT"
  for run in "$@"; do
    run="${run%/}"
    evid=""
    for r in "$EOUT"/*/result.json; do
      [ -e "$r" ] || continue
      if jq -e --arg d "$run/" '[.. | objects | select(has("tracePath")) | .tracePath | startswith($d)] | any' "$r" >/dev/null 2>&1; then
        evid="$(dirname "$r")"; break
      fi
    done
    [ -n "$evid" ] || { echo "nessun result.json in $EOUT ha una tracePath dentro $run: salto"; continue; }
    copy_one_run "$run" "$evid"
  done
}

# eval_tmpdir: la cartella dei file temporanei di claude plugin eval, fuori da /tmp, /var/tmp e /dev/shm (la sandbox li ha in
# denyWrite e quel divieto prevale sulle cartelle della corsa); predefinita $HOME/.cache/tollgate-p5-eval-tmp, modo 700
eval_tmpdir() {
  local d="${P5_EVAL_TMPDIR:-$HOME/.cache/tollgate-p5-eval-tmp}"
  case "$d" in /*) ;; *) die "P5_EVAL_TMPDIR deve essere un percorso assoluto: $d" ;; esac
  if [ "$CHECK" != 1 ]; then
    case "$d" in /tmp|/tmp/*|/var/tmp|/var/tmp/*|/dev/shm|/dev/shm/*) die "P5_EVAL_TMPDIR non può stare sotto /tmp, /var/tmp o /dev/shm: $d" ;; esac
  fi
  mkdir -p "$d" && chmod 700 "$d" || die "cartella temporanea $d non creabile"
  printf '%s\n' "$d"
}

# eval_run <etichetta> <ablation> <cartella del plugin> <caso> [cartella dello shim]: UNA invocazione di `claude plugin eval`
# con tutte le cautele. Lo shim (predefinito probe-bin accanto allo script) va in testa al PATH di chi lancia l'eval.
eval_run() {
  local label="$1" abl="$2" target="$3" case_name="$4" shim_dir="${5:-$here/probe-bin}" cap stamp dir rc cost dur casi src shown evtmp
  if [ -n "${P5_ONLY:-}" ]; then
    case ",$P5_ONLY," in *",$label,"*) ;; *) echo "== $label: saltata (P5_ONLY)"; return 0 ;; esac
  fi
  [ ! -e "$EOUT/COSTO-IGNOTO.txt" ] || die "costo ignoto di un'invocazione precedente: controlla a mano prima di continuare (vedi COSTO-IGNOTO.txt)"
  ensure_budget
  cap="$(budget_cap)" || die "tetto di $BUDGET_TOTAL USD esaurito (o budget.tsv illeggibile): non lancio niente"
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  dir="$EOUT/$stamp-$label"
  mkdir -p "$dir"
  evtmp="$(eval_tmpdir)" || die "cartella temporanea dell'eval non pronta"
  printf '%s\n' "TMPDIR dell eval: ${evtmp/#$HOME/\$HOME}" > "$dir/tmpdir.txt"
  local -a cmd=(claude plugin eval "$target" --no-publish --trust-plugin --runs 1 --model "$MODEL" --scaffold
                --allow-tools Bash Write Edit --ablation "$abl" --case "$case_name" --threshold 0 --keep-temp
                --max-cost-usd "$cap" --json "$dir/result.json" --output-dir "$dir" --report "$dir/report.html")
  shown="${cmd[*]}"; shown="${shown//$root\//./}"
  printf '%s claude %s\n' "$(date -u +%FT%TZ)" "${shown#claude }" >> "$EOUT/comandi.log"
  echo "== $label: ablation $abl, caso $case_name, tetto $cap USD"
  # lo shim della sonda va in testa al PATH di chi lancia l'eval: l'agente eredita il PATH del chiamante
  ( cd "$root" && PATH="$shim_dir:$PATH" TMPDIR="$evtmp" timeout "${P5_EVAL_TIMEOUT:-1800}" "${cmd[@]}" >"$dir/stdout.txt" 2>"$dir/stderr.txt" </dev/null )
  rc=$?
  echo "$rc" > "$dir/claude.rc"
  src="$dir/result.json"
  [ -s "$src" ] || src="$dir/aggregate-result.json"
  cost="$(jq -r '.costUsd | select(type == "number")' "$src" 2>/dev/null)"
  dur="$(jq -r '.durationSeconds | select(type == "number")' "$src" 2>/dev/null)"
  if [ -z "$cost" ] || [ -z "$dur" ]; then
    printf '%s %s: nessun costUsd/durationSeconds leggibile (uscita %s)\n' "$(date -u +%FT%TZ)" "$label" "$rc" >> "$EOUT/COSTO-IGNOTO.txt"
    # la riga c'è comunque: costUsd «?» fa rifiutare budget_cap (fail-closed) finché non la si corregge a mano
    printf '%s\t%s\t?\t?\t%s\n' "$(date -u +%FT%TZ)" "$label ($abl)" "$case_name" >> "$BUDGET"
    die "costo ignoto: controlla a mano prima di continuare ($dir)"
  fi
  casi="$(jq -r '[.cases[]?.name] | join(",")' "$src" 2>/dev/null)"
  [ -n "$casi" ] || casi="$case_name"
  printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$label ($abl)" "$cost" "$dur" "$casi" >> "$BUDGET"
  echo "   uscita $rc, costo $cost USD, durata ${dur}s"
  copy_run_files "$dir"
  return 0
}

EVAL_LABELS="sonda-nl-bash sonda-nl-worktree sonda-ws-worktree sonda-skill sonda-radice-tmp sonda-ve1-dependencies"
modo_eval_sonda() {
  local plugin="$here/probe-plugin" dep="$WORK/sonda-dep" tmp_target="${P5_TMP_TARGET:-/tmp/tollgate-eval-target-sonda}"
  command -v claude >/dev/null 2>&1 || die "claude non trovato nel PATH"
  local want
  for want in $(tr ',' ' ' <<<"${P5_ONLY:-}"); do
    case " $EVAL_LABELS " in *" $want "*) ;; *) die "P5_ONLY: etichetta sconosciuta $want (valide: $EVAL_LABELS)" ;; esac
  done
  command -v jq >/dev/null 2>&1 || die "jq non trovato nel PATH"
  mkdir -p "$EOUT" "$WORK"
  ensure_budget
  # VE5, VE7 (ablazione con/senza plugin su un solo caso), VE10 con cd nel worktree
  eval_run sonda-nl-bash with-without "$plugin" nl-bash
  # VE6 e VE10: EnterWorktree in allowed_tools
  eval_run sonda-nl-worktree none "$plugin" nl-worktree
  # VE12: il workspace è un worktree git con il gitdir fuori dal workspace; cwd di SessionStart
  eval_run sonda-ws-worktree none "$plugin" ws-worktree
  # VE2, VE3, VE4, VE6 (/sonda:prova, Agent), VE9 (subagente)
  eval_run sonda-skill none "$plugin" skill
  # D10: la stessa sonda in una copia fuori da /home (con lo shim copiato lì e messo in testa al PATH): quale radice si legge?
  rot "$tmp_target"
  mkdir -p "$tmp_target"
  cp -a "$plugin/." "$tmp_target/"
  mkdir -p "$tmp_target/probe-bin" && cp -a "$here/probe-bin/." "$tmp_target/probe-bin/"
  eval_run sonda-radice-tmp none "$tmp_target" skill "$tmp_target/probe-bin"
  # VE1 in una corsa separata: copia del plugin con `dependencies` come in .claude-plugin/plugin.json di tollgate
  rot "$dep"
  mkdir -p "$dep"
  cp -a "$plugin/." "$dep/"
  jq --argjson d "$(jq '.dependencies' "$root/.claude-plugin/plugin.json")" '. + {dependencies: $d}' \
    "$plugin/.claude-plugin/plugin.json" > "$dep/.claude-plugin/plugin.json" || die "copia con dependencies non scritta"
  eval_run sonda-ve1-dependencies none "$dep" skill
  echo "eval-sonda: fatto. Costi in $BUDGET"
}

# ---------------------------------------------------------------- clone di detect, PR

detect_clone() {
  local d="$WORK/detect"
  mkdir -p "$WORK"
  rot "$d"
  git_net detect-clone "$d" clone -q "$DET_URL" "$d"
  [ "$RC" = 0 ] || die "clone di $DET fallito (vedi detect-clone.err)"
  git -C "$d" config user.name "tollgate-p5-probe"
  git -C "$d" config user.email "probe@example.invalid"
  git -C "$d" switch -q main || die "main di detect non trovato"
}

# open_pr_detect <etichetta> <ramo> <file>: ramo da main con un file nuovo, push, PR verso main su detect, registrata
# nella guardia. Imposta BR, PR_NUM e PR_SHA.
open_pr_detect() {
  local label="$1" name="$2" file="$3" d="$WORK/detect" url
  fresh_branch "$DET" "$name"
  git -C "$d" switch -q main && git -C "$d" switch -q -c "$BR" || die "ramo $BR non creato"
  mkdir -p "$(dirname "$d/$file")"
  printf 'sonda %s %s\n' "$label" "$BR" > "$d/$file"
  git -C "$d" add "$file" && git -C "$d" commit -qm "sonda $label" || die "commit della sonda fallito"
  PR_SHA="$(git -C "$d" rev-parse HEAD)"
  git_net "$label-push" "$d" push "$DET_URL" "$BR"
  [ "$RC" = 0 ] || die "push di $BR fallito (vedi $label-push.err)"
  gh_call "$label-pr-create" pr create --repo "$DET" --base main --head "$BR" --title "sonda tollgate P5 ($label)" \
    --body "sonda tollgate P5 ($label), da chiudere"
  [ "$RC" = 0 ] || die "creazione della PR fallita (vedi $label-pr-create.err)"
  url="$(tail -n 1 "$OUT/$label-pr-create.out")"
  PR_NUM="${url##*/}"
  case "$PR_NUM" in ''|*[!0-9]*) die "numero della PR non leggibile da: $url" ;; esac
  CACHE_PR="$PR_NUM"      # subito: se un passo dopo fallisce, il trap di chi chiama chiude la PR
  python3 -B -I "$GH4/ghguard.py" register-pr "$PR_NUM" || die "la guardia non registra la PR $PR_NUM"
  save_text "$OUT/$label-pr.env" "PR=$PR_NUM" "SHA=$PR_SHA" "BRANCH=$BR"
}

# ---------------------------------------------------------------- modi

modo_cerca_token() {
  mkdir -p "$OUT"
  cerca_token "$SOURCE"
}

# VC1: durata della suite sui runner (3.11 e 3.13, con e senza PYTHONWARNINGS), checkout in "tollgate src"
modo_ci_sonda() {
  local d="$WORK/ci" br sha
  mkdir -p "$OUT" "$WORK"
  gh_call ci-auth auth status
  [ "$RC" = 0 ] || die "gh non autenticato (vedi ci-auth.err)"
  cerca_token "$SOURCE" || die "forme di token nella storia: mi fermo prima di creare il repo (vedi token-scan.txt)"
  gh_read ci-repo-esiste api "repos/$TOL"
  if [ "$RC" != 0 ]; then
    grep -q 404 "$OUT/ci-repo-esiste.err" || die "stato di $TOL non determinato (vedi ci-repo-esiste.err)"
    gh_call ci-repo-crea repo create "$TOL" --private
    [ "$RC" = 0 ] || die "creazione di $TOL fallita (vedi ci-repo-crea.err)"
    sleep "$POLL"
    gh_read ci-repo-esiste-dopo api "repos/$TOL"
    [ "$RC" = 0 ] || die "$TOL non risponde dopo la creazione"
    jq -e '.private == true' "$OUT/ci-repo-esiste-dopo.out" >/dev/null 2>&1 || die "$TOL non risulta privato: mi fermo"
  else
    jq -e '.private == true' "$OUT/ci-repo-esiste.out" >/dev/null 2>&1 || die "$TOL esiste ma non risulta privato: mi fermo"
  fi
  # clone temporaneo fuori dal worktree: main com'è, poi un ramo p5-probe-ci con il workflow della sonda
  case "$SOURCE" in /*) ;; *) die "P5_SOURCE_DIR deve essere un percorso assoluto di una cartella locale" ;; esac
  [ -d "$SOURCE" ] || die "P5_SOURCE_DIR non è una cartella: $SOURCE"
  rot "$d"
  git clone -q --no-hardlinks --branch main "$SOURCE" "$d" || die "clone locale di main fallito"
  git -C "$d" config user.name "tollgate-p5-probe"
  git -C "$d" config user.email "probe@example.invalid"
  git_net ci-push-main "$d" push "$TOL_URL" main
  [ "$RC" = 0 ] || die "push di main fallito (vedi ci-push-main.err)"
  fresh_branch "$TOL" p5-probe-ci
  br="$BR"
  git -C "$d" switch -q -c "$br" main || die "ramo $br non creato"
  mkdir -p "$d/.github/workflows"
  cp "$here/ci-probe.yml" "$d/.github/workflows/ci-probe.yml"
  git -C "$d" add .github && git -C "$d" commit -qm "sonda tollgate P5: ci-probe" || die "commit del workflow fallito"
  sha="$(git -C "$d" rev-parse HEAD)"
  git_net ci-push-sonda "$d" push "$TOL_URL" "$br"
  [ "$RC" = 0 ] || die "push di $br fallito (vedi ci-push-sonda.err)"
  save_text "$OUT/ci-sonda.env" "BRANCH=$br" "SHA=$sha"
  if wait_run ci "$TOL" ci-probe.yml "$sha" "$br" 0; then
    add_run ci "$TOL" "$RUN_ID" "$RUN_CONC"
    gh_read ci-log run view "$RUN_ID" --repo "$TOL" --log
    rot "$OUT/ci-riepilogo.txt"
    { grep -a 'sonda:' "$OUT/ci-log.out" || echo "non determinato: nessuna riga «sonda:» nel log"; } > "$OUT/ci-riepilogo.txt"
  else
    save_text "$OUT/ci-riepilogo.txt" "non determinato: il run di ci-probe non è comparso entro ${WAIT_MAX}s"
  fi
}

# VC2: SHA dei tag (dereferenziati) e motore di ogni versione (`runs.using` di action.yml)
modo_pins() {
  local a tag using f
  mkdir -p "$OUT" "$PINS"
  rot "$OUT/pins.tsv" "$OUT/pins-motore.tsv" "$OUT/pins-scelta.tsv"
  for a in checkout cache upload-artifact download-artifact setup-python; do
    git_net "pins-lsremote-$a" - ls-remote --tags "https://github.com/actions/$a"
    [ "$RC" = 0 ] || die "ls-remote di actions/$a fallito (vedi pins-lsremote-$a.err)"
  done
  python3 -B -I - "$OUT" <<'PY'
import os, re, sys
out = sys.argv[1]
rows, choice = [], []
for action in ("checkout", "cache", "upload-artifact", "download-artifact", "setup-python"):
    direct, peeled = {}, {}
    for line in open(os.path.join(out, "pins-lsremote-%s.out" % action)):
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith("refs/tags/"):
            continue
        name = parts[1][len("refs/tags/"):]
        if name.endswith("^{}"):
            peeled[name[:-3]] = parts[0]
        else:
            direct[name] = parts[0]
    best = {}
    for name, sha in direct.items():
        m = re.fullmatch(r"v([0-9]+)\.([0-9]+)\.([0-9]+)", name)      # solo versioni complete: v4 e v4.2 sono tag mobili
        if not m:
            continue
        key = tuple(int(x) for x in m.groups())
        if key[0] not in best or key > best[key[0]][0]:
            best[key[0]] = (key, name, peeled.get(name, sha), "dereferenziato" if name in peeled else "diretto")
    for major in sorted(best):
        _, name, sha, kind = best[major]
        rows.append((action, major, name, sha, kind))
    for major in sorted({4} & set(best) | ({max(best)} if best else set())):
        choice.append((action, best[major][1]))
with open(os.path.join(out, "pins.tsv"), "w") as fh:
    fh.write("azione\tmaggiore\ttag\tsha\ttipo\n")
    for row in rows:
        fh.write("\t".join(str(x) for x in row) + "\n")
with open(os.path.join(out, "pins-scelta.tsv"), "w") as fh:
    for row in choice:
        fh.write("%s\t%s\n" % row)
PY
  [ -s "$OUT/pins.tsv" ] || die "pins.tsv vuoto"
  printf 'azione\ttag\tusing\n' > "$OUT/pins-motore.tsv"
  while IFS=$'\t' read -r a tag; do
    [ -n "$a" ] || continue
    mkdir -p "$PINS/$a"
    [ -d "$PINS/$a/.git" ] || git -C "$PINS/$a" init -q || die "git init in $PINS/$a fallito"
    git_net "pins-fetch-$a-$tag" "$PINS/$a" fetch --depth 1 "https://github.com/actions/$a" tag "$tag"
    using="non determinato: fetch fallito"
    if [ "$RC" = 0 ]; then
      using="non determinato: action.yml assente"
      for f in action.yml action.yaml; do
        if git -C "$PINS/$a" cat-file -e "refs/tags/$tag:$f" 2>/dev/null; then
          using="$(git -C "$PINS/$a" show "refs/tags/$tag:$f" | sed -n 's/^[[:space:]]*using:[[:space:]]*//p' | head -n 1 | tr -d "'\"")"
          [ -n "$using" ] || using="non determinato: nessun runs.using in $f"
          break
        fi
      done
    fi
    printf '%s\t%s\t%s\n' "$a" "$tag" "$using" >> "$OUT/pins-motore.tsv"
  done < "$OUT/pins-scelta.tsv"
}

# VG1: cache in sola lettura dei job workflow_run sul privato (log del job verdict: «Cache mode:»)
CACHE_PR=""      # la PR aperta da open_pr_detect, assegnata là dentro appena il numero è noto
close_cache_pr() {
  [ -n "$CACHE_PR" ] || return 0
  gh_call cache-pr-close pr close "$CACHE_PR" --repo "$DET"
  CACHE_PR=""
}
modo_detect_cache() {
  local ts
  mkdir -p "$OUT" "$WORK"
  rot "$OUT/prs-aperte.txt"
  detect_clone
  ts="$(date +%Y%m%d-%H%M%S)"
  trap close_cache_pr EXIT
  open_pr_detect cache p5-probe-cache "sonde/p5-cache-$ts.txt"
  if wait_run cache-run "$DET" tollgate-run.yml "$PR_SHA" "$BR" 0; then add_run cache-run "$DET" "$RUN_ID" "$RUN_CONC"; fi
  rot "$OUT/cache-mode.txt"
  if wait_run cache-verdict "$DET" tollgate-verdict.yml "$PR_SHA" "$BR" 1; then
    add_run cache-verdict "$DET" "$RUN_ID" "$RUN_CONC"
    gh_read cache-verdict-log run view "$RUN_ID" --repo "$DET" --log
    { grep -a 'Cache mode:' "$OUT/cache-verdict-log.out" || echo "non determinato: nessuna riga «Cache mode:» nel log del job verdict"; } > "$OUT/cache-mode.txt"
  else
    echo "non determinato: il run di tollgate-verdict non è comparso entro ${WAIT_MAX}s" > "$OUT/cache-mode.txt"
  fi
  close_cache_pr
}

# VG2: sha_pinning_required su detect (privato Free): lo si accende, si prova un workflow a @v4 (e, se pins ha già gli SHA,
# uno fissato), si rimette SEMPRE il valore iniziale (trap), anche se un passo fallisce
PIN_INIT_ENABLED=""; PIN_INIT_ACTIONS=""; PIN_INIT_PIN=""; PIN_TOUCHED=0
pin_put() { # <etichetta> <true|false>
  local -a f=(-F enabled=true -F "sha_pinning_required=$2")
  [ -n "$PIN_INIT_ACTIONS" ] && f+=(-F "allowed_actions=$PIN_INIT_ACTIONS")
  gh_write_idem "$1" api --method PUT "repos/$DET/actions/permissions" "${f[@]}"
}
restore_pin() {
  local rc=0 try
  [ "$PIN_TOUCHED" = 1 ] || return 0
  for try in 1 2 3; do
    pin_put pin-ripristino "$PIN_INIT_PIN"
    [ "$RC" = 0 ] && break
    sleep "$RETRY_SLEEP"
  done
  gh_read pin-dopo api "repos/$DET/actions/permissions"
  if [ "$RC" = 0 ] && [ "$(jq -r '.sha_pinning_required // false' "$OUT/pin-dopo.out" 2>/dev/null)" = "$PIN_INIT_PIN" ]; then
    echo "sha_pinning_required rimesso a $PIN_INIT_PIN (verificato)"
    PIN_TOUCHED=0
  else
    echo "RIPRISTINO NON VERIFICATO: rimetti a mano sha_pinning_required=$PIN_INIT_PIN su $DET (vedi pin-ripristino.* e pin-dopo.*)" >&2
    rc=3
  fi
  [ "$rc" = 0 ] || exit "$rc"
}
modo_detect_pin() {
  local ts d="$WORK/detect" sha_ref pin_br
  mkdir -p "$OUT" "$WORK"
  gh_read pin-iniziale api "repos/$DET/actions/permissions"
  [ "$RC" = 0 ] || die "permessi iniziali di $DET non leggibili (vedi pin-iniziale.err)"
  [ "$(jq -r '.enabled' "$OUT/pin-iniziale.out" 2>/dev/null)" = true ] || die "Actions non risulta abilitato su $DET: mi fermo"
  PIN_INIT_ENABLED=true
  PIN_INIT_PIN="$(jq -r '.sha_pinning_required // false' "$OUT/pin-iniziale.out")"
  PIN_INIT_ACTIONS="$(jq -r '.allowed_actions // empty' "$OUT/pin-iniziale.out")"
  case "$PIN_INIT_PIN" in true|false) ;; *) die "sha_pinning_required iniziale non leggibile" ;; esac
  trap restore_pin EXIT
  trap 'exit 130' INT TERM
  detect_clone
  ts="$(date +%Y%m%d-%H%M%S)"
  fresh_branch "$DET" p5-probe-pin
  pin_br="$BR"
  git -C "$d" switch -q -c "$pin_br" main || die "ramo $pin_br non creato"
  mkdir -p "$d/.github/workflows"
  cat > "$d/.github/workflows/p5-probe-pin.yml" <<'YML'
name: p5-probe-pin
# Sonda VG2 di tollgate P5: azione a tag mobile (@v4); con sha_pinning_required il run deve essere rifiutato.
on:
  push:
    branches: ["p5-probe-pin*"]
permissions:
  contents: read
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo sonda-pin-ok
YML
  sha_ref="$(awk -F'\t' '$1 == "checkout" && $3 ~ /^v4\./ { sha = $4 } END { print sha }' "$OUT/pins.tsv" 2>/dev/null)"
  if [ -n "$sha_ref" ]; then
    cat > "$d/.github/workflows/p5-probe-pin-sha.yml" <<YML
name: p5-probe-pin-sha
# Sonda VG2 di tollgate P5 (controprova): la stessa azione fissata per SHA; con sha_pinning_required deve girare.
on:
  push:
    branches: ["p5-probe-pin*"]
permissions:
  contents: read
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@$sha_ref # v4
      - run: echo sonda-pin-sha-ok
YML
  else
    echo "controprova a SHA non scritta: pins.tsv assente o senza un tag v4 di checkout (lancia prima il modo pins)" > "$OUT/pin-controprova.txt"
  fi
  git -C "$d" add .github && git -C "$d" commit -qm "sonda tollgate P5: p5-probe-pin" || die "commit dei workflow fallito"
  PR_SHA="$(git -C "$d" rev-parse HEAD)"
  # si accende il fissaggio PRIMA del push (il push fa partire i run): da qui il ripristino è dovuto
  PIN_TOUCHED=1
  pin_put pin-on true
  [ "$RC" = 0 ] || die "PUT con sha_pinning_required=true fallito (vedi pin-on.err): il valore sarà rimesso com'era"
  gh_read pin-on-verifica api "repos/$DET/actions/permissions"
  git_net pin-push "$d" push "$DET_URL" "$pin_br"
  [ "$RC" = 0 ] || die "push di $pin_br fallito (vedi pin-push.err)"
  save_text "$OUT/pin-ramo.env" "BRANCH=$pin_br" "SHA=$PR_SHA"
  if wait_run pin-v4 "$DET" p5-probe-pin.yml "$PR_SHA" "$pin_br" 0; then
    add_run pin-v4 "$DET" "$RUN_ID" "$RUN_CONC"
    gh_read pin-v4-log-failed run view "$RUN_ID" --repo "$DET" --log-failed
  else
    save_text "$OUT/pin-v4-esito.txt" "non determinato: il run di p5-probe-pin non è comparso entro ${WAIT_MAX}s"
  fi
  if [ -n "$sha_ref" ]; then
    if wait_run pin-sha "$DET" p5-probe-pin-sha.yml "$PR_SHA" "$pin_br" 0; then
      add_run pin-sha "$DET" "$RUN_ID" "$RUN_CONC"
      gh_read pin-sha-log run view "$RUN_ID" --repo "$DET" --log
    fi
  fi
  gh_read pin-lista-run run list --repo "$DET" --limit 20 --json databaseId,workflowName,headBranch,event,status,conclusion,createdAt
  restore_pin
  trap - EXIT
}

# versioni e minuti di Actions dei run elencati in runs.tsv
modo_raccogli() {
  local label repo id conc total_ms=0 ms n=0
  mkdir -p "$OUT"
  rot "$OUT/raccogli-versioni.txt" "$OUT/raccogli-minuti.txt" "$OUT/raccogli-budget.txt"
  gh_call raccogli-gh-versione --version
  {
    echo "gh: $(head -n 1 "$OUT/raccogli-gh-versione.out")"
    echo "claude: $(timeout 30 claude --version 2>&1 | head -n 1)"
    echo "git: $(git --version 2>&1)"
    echo "python3: $(python3 --version 2>&1)"
    echo "bwrap: $(bwrap --version 2>&1 | head -n 1)"
    echo "socat: $(socat -V 2>&1 | sed -n 2p)"
    echo "jq: $(jq --version 2>&1)"
  } > "$OUT/raccogli-versioni.txt"
  : > "$OUT/raccogli-minuti.txt"
  if [ -s "$OUT/runs.tsv" ]; then
    while IFS=$'\t' read -r label repo id conc; do
      [ -n "$id" ] || continue
      gh_read "raccogli-timing-$label-$id" api "repos/$repo/actions/runs/$id/timing"
      ms="$(jq -r '.billable.UBUNTU.total_ms // 0' "$OUT/raccogli-timing-$label-$id.out" 2>/dev/null || echo 0)"
      case "$ms" in ''|*[!0-9]*) ms=0 ;; esac
      total_ms=$((total_ms + ms)); n=$((n + 1))
      printf '%s\t%s\trun %s\tconclusione %s\tdurata %s ms\tfatturabile UBUNTU %s ms\n' "$label" "$repo" "$id" "$conc" \
        "$(jq -r '.run_duration_ms // 0' "$OUT/raccogli-timing-$label-$id.out" 2>/dev/null)" "$ms" >> "$OUT/raccogli-minuti.txt"
    done < "$OUT/runs.tsv"
  fi
  printf 'totale: %d run, %d ms fatturabili (circa %d minuti)\n' "$n" "$total_ms" $(( (total_ms + 59999) / 60000 )) >> "$OUT/raccogli-minuti.txt"
  ensure_budget
  awk -F'\t' -v total="$BUDGET_TOTAL" 'NR > 1 { spent += $3; n++ } END { printf "invocazioni: %d, speso: %.4f USD, residuo: %.4f USD su %d\n", n, spent, total - spent, total }' "$BUDGET" \
    > "$OUT/raccogli-budget.txt"
  cat "$OUT/raccogli-versioni.txt" "$OUT/raccogli-minuti.txt" "$OUT/raccogli-budget.txt"
}

# ---------------------------------------------------------------- modo controlla (nessuna rete)

# Prova negativa: ogni comando vietato deve fermare guard_args e dare una violazione in `ghguard.py log`
check_negativi() { # <cartella>
  local T="$1" n=0 stopped=0 viol cmd
  local -a forbidden=(
    "api user" "api /user" "api graphql" "api repos/$OWNER/tollgate-p4-protected" "api repos/$OWNER/altro"
    "api --method=POST repos/$DET/issues" "api -XPOST repos/$DET/issues" "api -X POST repos/$DET/issues"
    "api --method PATCH repos/$TOL -F private=false" "api --method PATCH repos/$DET -f visibility=public"
    "api --method DELETE repos/$DET" "api --method DELETE repos/$TOL" "api repos/$DET/actions/secrets"
    "api --method PUT repos/$TOL/actions/secrets/X -f encrypted_value=x" "api --method PUT repos/$DET/actions/permissions -F enabled=false"
    "api --method PATCH repos/$DET/pulls/999 -F body=@/tmp/x"
    "repo create $TOL --public" "repo create $TOL" "repo create $DET --private" "repo create $OWNER/tollgate-p4-protected --private"
    "repo delete $TOL" "repo edit $TOL --visibility public" "repo clone $DET" "repo view $TOL"
    "auth login" "auth refresh" "auth status --show-token" "auth token" "secret set X" "ssh-key add"
    "pr create --repo $TOL --head x" "pr list --repo $TOL" "pr list --repo $OWNER/tollgate-p4-protected"
    "pr merge 1 --repo $DET" "pr edit 1 --repo $DET --body x" "issue create --repo $DET --title x" "issue delete 1 --repo $DET"
    "run delete 1 --repo $TOL" "run cancel 1 --repo $TOL" "run list" "run list --repo $OWNER/tollgate-p4-protected"
    "workflow run ci.yml --repo $TOL" "release create v1 --repo $TOL"
    "pr comment 1 --repo $DET --body vedi-$OWNER/tollgate-p4-protected"
  )
  local -a allowed=(
    "auth status" "--version" "repo create $TOL --private" "run list --repo $TOL --workflow ci-probe.yml --limit 30 --json databaseId"
    "run view 5 --repo $TOL --log" "run watch 5 --repo $DET --exit-status" "run rerun 5 --repo $DET --failed"
    "api repos/$TOL" "api repos/$DET/actions/permissions" "api repos/$TOL/actions/runs/5/timing"
    "api --method PUT repos/$DET/actions/permissions -F enabled=true -F sha_pinning_required=true"
    "pr close 3 --repo $DET" "pr view 3 --repo $DET --json state" "issue list --repo $DET --state open"
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
  viol="$(python3 -B -I "$GH4/ghguard.py" log "$T/negativi.log" | grep -c '^VIOLAZIONE')"
  echo "  guard_args: $stopped fermati su $n; ghguard log: $viol violazioni su $n"
  local ok=0
  for cmd in "${allowed[@]}"; do
    # shellcheck disable=SC2086
    if ( guard_args $cmd ) >/dev/null 2>&1; then ok=$((ok + 1)); else echo "  AMMESSO MA RIFIUTATO: $cmd"; fi
  done
  echo "  comandi legittimi ammessi: $ok su ${#allowed[@]}"
  [ "$stopped" = "$n" ] && [ "$viol" -ge "$n" ] && [ "$ok" = "${#allowed[@]}" ]
}

# Prova negativa dei comandi git con la rete
check_git_negativi() {
  local n=0 stopped=0 pins="${P5_PINS:-/tmp/tollgate-p5-pins}" w="$WORK" args
  local -a forbidden=(
    "push --force $TOL_URL main" "push -f $TOL_URL main" "push $TOL_URL +main" "push $TOL_URL main:main" "push --mirror $TOL_URL"
    "push $TOL_URL altro" "push --delete $TOL_URL main" "push --delete $DET_URL p5-probe-cache" "push https://github.com/$OWNER/tollgate-p4-protected.git main"
    "push origin main" "push --all $TOL_URL" "pull $TOL_URL" "ls-remote --tags $TOL_URL" "ls-remote --tags https://github.com/actions/runner"
    "fetch --depth 1 https://github.com/actions/checkout tag main" "fetch $TOL_URL main"
  )
  for args in "${forbidden[@]}"; do
    n=$((n + 1))
    # shellcheck disable=SC2086
    if python3 -B -I "$GH4/ghguard.py" gitcheck --dir "$w/x" -- $args >/dev/null 2>&1; then
      echo "  git NON FERMATO: $args"
    else
      stopped=$((stopped + 1))
    fi
  done
  echo "  git: $stopped fermati su $n"
  python3 -B -I "$GH4/ghguard.py" gitcheck --dir "$pins/checkout" -- fetch --depth 1 https://github.com/actions/checkout tag v4.2.2 \
    || { echo "  git legittimo rifiutato"; return 1; }
  [ "$stopped" = "$n" ]
}

# ogni `claude` registrato: solo --version e `plugin eval`; ogni `plugin eval` con --no-publish, --trust-plugin, --runs 1 e il modello
check_claude_log() { # <registro del claude finto>
  python3 -B -I - "$1" "$MODEL" <<'PY'
import sys
bad, evals = [], 0
for line in open(sys.argv[1]):
    args = line.rstrip("\n").split("\t")
    if args and args[-1] == "":
        args = args[:-1]
    if not args:
        continue
    if args == ["--version"]:
        continue
    if args[:2] != ["plugin", "eval"]:
        bad.append("comando claude non ammesso: " + " ".join(args)); continue
    evals += 1
    for need in ("--no-publish", "--trust-plugin", "--scaffold", "--keep-temp", "--json", "--output-dir", "--report", "--max-cost-usd"):
        if need not in args:
            bad.append("manca %s: %s" % (need, " ".join(args)))
    if "--runs" not in args or args[args.index("--runs") + 1] != "1":
        bad.append("manca --runs 1")
    if "--model" not in args or args[args.index("--model") + 1] != sys.argv[2]:
        bad.append("manca --model " + sys.argv[2])
    if "-p" in args or "--print" in args:
        bad.append("opzione -p (modalità non interattiva)")
    cap = args[args.index("--max-cost-usd") + 1] if "--max-cost-usd" in args else "x"
    try:
        if not 0 < float(cap) <= 3:
            bad.append("tetto fuori da (0, 3]: " + cap)
    except ValueError:
        bad.append("tetto illeggibile: " + cap)
print("claude plugin eval registrati: %d" % evals)
for b in bad:
    print("VIOLAZIONE (%s)" % b)
sys.exit(1 if bad or evals == 0 else 0)
PY
}

# repo nudi locali del banco: detect con un commit su main (e un hook che rifiuta il ramo p5-probe-pin-rifiutato), actions/* con tag
make_remotes() { # <cartella dei nudi>
  local R="$1" tmp a v
  tmp="$R.costruzione"           # cartella di lavoro dei nudi, dentro la cartella del controllo (mai cancellata da qui)
  mkdir -p "$R/$OWNER" "$R/actions" "$tmp"
  git init -q --bare "$R/$OWNER/tollgate-p4-detect.git"
  git init -q "$tmp/d" && git -C "$tmp/d" -c user.name=t -c user.email=t@example.invalid commit -q --allow-empty -m "base di detect" \
    && git -C "$tmp/d" branch -M main && git -C "$tmp/d" push -q "$R/$OWNER/tollgate-p4-detect.git" main
  for a in checkout cache upload-artifact download-artifact setup-python; do
    git init -q --bare "$R/actions/$a.git"
    git init -q "$tmp/$a"
    for v in v4.1.0 v4.2.2 v5.0.0; do
      printf "name: %s %s\nruns:\n  using: 'node%s'\n  main: dist/index.js\n" "$a" "$v" "$([ "$v" = v5.0.0 ] && echo 24 || echo 20)" > "$tmp/$a/action.yml"
      git -C "$tmp/$a" add action.yml
      git -C "$tmp/$a" -c user.name=t -c user.email=t@example.invalid commit -q -m "$a $v" >/dev/null
      git -C "$tmp/$a" -c user.name=t -c user.email=t@example.invalid tag -a "$v" -m "$a $v"
    done
    git -C "$tmp/$a" -c user.name=t -c user.email=t@example.invalid tag -f -a v4 -m "$a v4 mobile" v4.2.2 >/dev/null 2>&1
    git -C "$tmp/$a" push -q "$R/actions/$a.git" --tags
  done
}

# sorgente di prova: un repo con main; opzionalmente un file con una forma di token costruita a runtime (mai nel testo di questo script)
make_source() { # <cartella> [sporco]
  local d="$1" fake
  mkdir -p "$d/tests"
  git init -q -b main "$d"
  printf '#!/usr/bin/env bash\necho tests\n' > "$d/tests/run"; chmod +x "$d/tests/run"
  printf 'contenuto innocuo\n' > "$d/README.md"
  if [ "${2:-}" = sporco ]; then
    fake="gh""p_$(printf 'a%.0s' {1..24})"
    printf 'valore finto: %s\n' "$fake" > "$d/fixture.txt"
  fi
  git -C "$d" add -A
  git -C "$d" -c user.name=t -c user.email=t@example.invalid commit -q -m "base"
}

modo_controlla() {
  local T mode f rc=0 missing=0 url n hit
  bash -n "$here/run-p5-checks.sh" || die "bash -n fallito"
  T="${P5_CHECK_DIR:-$(mktemp -d /tmp/tollgate-p5-controlla.XXXXXX)}"
  mkdir -p "$T/bin" "$T/remote" "$T/out" "$T/eval" "$T/work" "$T/pins" "$T/fake" "$T/runs"
  cp "$here/fake/gh" "$T/bin/gh"
  # il claude finto registra il primo elemento del PATH con cui è lanciato (lo shim della sonda) prima di passare a Python
  printf '#!/usr/bin/env bash\nprintf "%%s\\n" "${PATH%%%%:*}" >> "$P5_FAKE_CLAUDE_LOG.path"\nexec python3 -B %q "$@"\n' "$here/fake/claude.py" > "$T/bin/claude"
  chmod +x "$T/bin/gh" "$T/bin/claude"
  make_remotes "$T/remote"
  make_source "$T/src"; make_source "$T/src-sporco" sporco
  export PATH="$T/bin:$PATH"
  [ "$(command -v gh)" = "$T/bin/gh" ] && [ "$(command -v claude)" = "$T/bin/claude" ] || die "gh e claude finti non sono i primi nel PATH"
  # variabili del modo controlla: i modi girano come sottoprocessi con questo ambiente
  export P5_CHECK=1 P5_OUT="$T/out" P5_EVAL_OUT="$T/eval" P5_WORK="$T/work" P5_PINS="$T/pins" P5_GIT_BASE="$T/remote" \
         P5_SOURCE_DIR="$T/src" P5_FAKE_LOG="$T/gh.log" P5_FAKE_CLAUDE_LOG="$T/claude.log" P5_FAKE_STATE="$T/fake" \
         P5_FAKE_RUNS="$T/runs" P5_EVAL_TMPDIR="$T/evtmp" P5_TMP_TARGET="$T/tmp-target" P5_WAIT_MAX=5 P5_POLL=0 P5_RETRY_SLEEP=0 P5_EVAL_TIMEOUT=60 TMPDIR="$T/runs"
  : > "$P5_FAKE_LOG"; : > "$P5_FAKE_CLAUDE_LOG"
  OUT="$T/out"; EOUT="$T/eval"; WORK="$T/work"; PINS="$T/pins"; BUDGET="$EOUT/budget.tsv"
  export P4_OUT="$OUT" P4_WORK="$WORK" P5_PR_REGISTRY="$OUT/prs-aperte.txt"
  echo "cartella del controllo: $T"
  run_mode() { # <nome> <modo> [VAR=valore...]: esito atteso 0
    local name="$1" m="$2"; shift 2
    if env "$@" bash "$here/run-p5-checks.sh" "$m" >"$T/modo-$name.log" 2>&1; then echo "modo $name: ok"
    else echo "modo $name: FALLITO (vedi $T/modo-$name.log)"; tail -n 5 "$T/modo-$name.log"; rc=1; fi
  }
  run_fails() { # <nome> <modo> [VAR=valore...]: esito atteso diverso da 0
    local name="$1" m="$2"; shift 2
    if env "$@" bash "$here/run-p5-checks.sh" "$m" >"$T/modo-$name.log" 2>&1; then echo "modo $name: DOVEVA FALLIRE"; rc=1
    else echo "modo $name: fermato come previsto"; fi
  }

  echo "--- ricerca di token"
  run_mode cerca-token-pulito cerca-token
  run_fails cerca-token-sporco cerca-token P5_SOURCE_DIR="$T/src-sporco"
  grep -q 'TROVATO' "$T/modo-cerca-token-sporco.log" && echo "cerca-token: il sorgente sporco è segnalato"
  grep -q 'fixture.txt' "$T/modo-cerca-token-sporco.log" && echo "cerca-token: percorso stampato"
  if grep -aq "gh""p_aaaa" "$T/modo-cerca-token-sporco.log" "$T/out/token-scan.txt"; then echo "cerca-token: IL TESTO TROVATO È STATO STAMPATO"; rc=1; else echo "cerca-token: il testo trovato non è stampato"; fi
  run_mode cerca-token-ammesso cerca-token P5_SOURCE_DIR="$T/src-sporco" P5_TOKEN_ALLOW_PATHS=fixture.txt
  grep -q 'AMMESSO (P5_TOKEN_ALLOW_PATHS)' "$T/modo-cerca-token-ammesso.log" && echo "cerca-token: l'ammissione esplicita è stampata"
  echo "--- ci-sonda: sporco, poi pulito"
  : > "$P5_FAKE_LOG"
  run_fails ci-sonda-sporco ci-sonda P5_SOURCE_DIR="$T/src-sporco"
  if grep -q $'^repo\tcreate' "$P5_FAKE_LOG"; then echo "ci-sonda: HA CREATO IL REPO CON TOKEN NELLA STORIA"; rc=1; else echo "ci-sonda: nessun repo creato con token nella storia"; fi
  run_mode ci-sonda ci-sonda
  run_mode pins pins
  # M4: se dopo l'apertura della PR un passo fallisce (qui: la registrazione), il trap chiude la PR
  closes="$(grep -c $'^pr\tclose' "$P5_FAKE_LOG")"
  run_fails detect-cache-registro-bloccato detect-cache P5_FAKE_LOCK_REGISTRY=1
  if [ "$(grep -c $'^pr\tclose' "$P5_FAKE_LOG")" -gt "$closes" ]; then echo "detect-cache: PR chiusa dal trap dopo un errore"; else echo "PR ORFANA DOPO UN ERRORE"; rc=1; fi
  run_mode detect-cache detect-cache P5_FAKE_500_ONCE=1
  run_mode detect-pin detect-pin
  [ "$(jq -r '.sha_pinning_required' "$T/fake/perm.json")" = false ] && echo "detect-pin: valore iniziale rimesso (false)" || { echo "DETECT-PIN: VALORE NON RIMESSO"; rc=1; }
  rm -f "$T/fake/perm.json"
  mkdir -p "$T/remote/$OWNER/tollgate-p4-detect.git/hooks"
  printf '#!/bin/sh\nwhile read old new ref; do case "$ref" in *p5-probe-pin*) echo rifiutato >&2; exit 1;; esac; done\n' > "$T/remote/$OWNER/tollgate-p4-detect.git/hooks/pre-receive"
  chmod +x "$T/remote/$OWNER/tollgate-p4-detect.git/hooks/pre-receive"
  run_fails detect-pin-push-rifiutato detect-pin
  [ "$(jq -r '.sha_pinning_required' "$T/fake/perm.json")" = false ] && echo "detect-pin dopo un passo fallito: valore iniziale rimesso (false)" || { echo "DETECT-PIN: VALORE NON RIMESSO DOPO UN FALLIMENTO"; rc=1; }
  grep -q 'sha_pinning_required rimesso a false' "$T/modo-detect-pin-push-rifiutato.log" && echo "detect-pin: ripristino verificato anche dopo il fallimento"
  rm -f "$T/remote/$OWNER/tollgate-p4-detect.git/hooks/pre-receive"
  run_mode raccogli raccogli
  echo "--- eval-sonda"
  run_mode eval-sonda eval-sonda
  echo "--- tetto di spesa e costo ignoto"
  mkdir -p "$T/eval-b1" "$T/eval-b2" "$T/eval-b3" "$T/eval-b4"
  printf '%s\n%s\t%s\t%s\t%s\t%s\n' "$BUDGET_HEADER" "2026-10-23T00:00:00Z" "prima" "78.5" "100" "x" > "$T/eval-b1/budget.tsv"
  run_mode eval-tetto-residuo eval-sonda P5_EVAL_OUT="$T/eval-b1"
  printf '%s\n%s\t%s\t%s\t%s\t%s\n' "$BUDGET_HEADER" "2026-10-23T00:00:00Z" "prima" "80" "100" "x" > "$T/eval-b2/budget.tsv"
  : > "$T/claude.before"; cp "$P5_FAKE_CLAUDE_LOG" "$T/claude.before"
  run_fails eval-tetto-esaurito eval-sonda P5_EVAL_OUT="$T/eval-b2"
  cmp -s "$T/claude.before" "$P5_FAKE_CLAUDE_LOG" && echo "eval-sonda: con il tetto esaurito claude non è stato lanciato" || { echo "CLAUDE LANCIATO CON IL TETTO ESAURITO"; rc=1; }
  run_fails eval-costo-ignoto eval-sonda P5_EVAL_OUT="$T/eval-b3" P5_FAKE_CLAUDE_MODE=nojson
  grep -q 'costo ignoto: controlla a mano prima di continuare' "$T/modo-eval-costo-ignoto.log" && echo "eval-sonda: costo ignoto segnalato"
  n="$(grep -c 'plugin' "$P5_FAKE_CLAUDE_LOG")"
  run_fails eval-dopo-costo-ignoto eval-sonda P5_EVAL_OUT="$T/eval-b3"
  [ "$(grep -c 'plugin' "$P5_FAKE_CLAUDE_LOG")" = "$n" ] && echo "eval-sonda: dopo un costo ignoto non parte altro" || { echo "PARTITO ALTRO DOPO IL COSTO IGNOTO"; rc=1; }
  grep -qP '\t\?\t\?\t' "$T/eval-b3/budget.tsv" && echo "eval-sonda: riga con costUsd ? in budget.tsv" || { echo "RIGA DEL COSTO IGNOTO ASSENTE"; rc=1; }
  rm -f "$T/eval-b3/COSTO-IGNOTO.txt"
  n="$(grep -c 'plugin' "$P5_FAKE_CLAUDE_LOG")"
  run_fails eval-riga-con-punto-interrogativo eval-sonda P5_EVAL_OUT="$T/eval-b3"
  [ "$(grep -c 'plugin' "$P5_FAKE_CLAUDE_LOG")" = "$n" ] && echo "eval-sonda: con una riga costUsd ? budget_cap rifiuta (fail-closed)" || { echo "PARTITO CON UNA RIGA ILLEGGIBILE"; rc=1; }
  echo "--- P5_ONLY"
  run_fails eval-solo-etichetta-sbagliata eval-sonda P5_EVAL_OUT="$T/eval-b4" P5_ONLY=sonda-skill,sonda-sbagliata
  run_mode eval-solo eval-sonda P5_EVAL_OUT="$T/eval-b4" P5_ONLY=sonda-skill,sonda-ve1-dependencies
  echo "eval-sonda con P5_ONLY: $(($(wc -l < "$T/eval-b4/budget.tsv") - 1)) invocazioni registrate"
  echo "--- copia delle corse tenute (cartelle sigillate)"
  hit="$(ls -d "$T"/eval/*-sonda-skill | head -n 1)"
  kept="$(head -n 1 "$hit/cartelle-tenute.txt")"
  [ -f "$hit/corse/$(basename "$kept")/trace.jsonl" ] && echo "corsa tenuta: trace copiata" || { echo "TRACE NON COPIATA"; rc=1; }
  [ -f "$hit/corse/$(basename "$kept")/cwd/esiti.txt" ] && [ -f "$hit/corse/$(basename "$kept")/home/.local/state/sonda/hooks.jsonl" ] && echo "corsa tenuta: file della sonda copiati" || { echo "FILE DELLA SONDA NON COPIATI"; rc=1; }
  if [ -e "$hit/corse/$(basename "$kept")/cwd/altro.txt" ] || [ -e "$hit/corse/$(basename "$kept")/home/.bashrc" ]; then echo "COPIATO QUALCOSA DI TROPPO"; rc=1; else echo "corsa tenuta: nient'altro copiato"; fi
  mv "$hit/corse" "$hit/corse.prima"
  if bash "$here/run-p5-checks.sh" raccogli-corse "$kept" >"$T/modo-raccogli-corse.log" 2>&1; then echo "modo raccogli-corse: ok"
  else echo "modo raccogli-corse: FALLITO (vedi $T/modo-raccogli-corse.log)"; rc=1; fi
  [ -f "$hit/corse/$(basename "$kept")/trace.jsonl" ] && echo "raccogli-corse: corsa riassegnata alla sua evidenza dalla tracePath" || { echo "RACCOGLI-CORSE NON HA COPIATO"; rc=1; }
  mkdir -p "$T/eval-b5"
  run_mode eval-settings-con-credenziali eval-sonda P5_EVAL_OUT="$T/eval-b5" P5_ONLY=sonda-skill P5_FAKE_SETTINGS_TOKEN=1
  hit5="$(ls -d "$T"/eval-b5/*-sonda-skill | head -n 1)"
  if [ -f "$hit5/corse/$(basename "$(head -n 1 "$hit5/cartelle-tenute.txt")")/settings-non-copiato.txt" ] && [ -z "$(find "$hit5/corse" -name settings.json)" ]; then echo "settings.json con credenziali: non copiato e registrato"; else echo "SETTINGS CON CREDENZIALI COPIATO"; rc=1; fi
  echo "TMPDIR dell'eval: $(cat "$hit/tmpdir.txt")"
  [ -d "$T/evtmp" ] && echo "P5_EVAL_TMPDIR usato per le corse" || { echo "P5_EVAL_TMPDIR NON USATO"; rc=1; }
  echo "--- ambiente dei gh finti e di git"
  if awk -F'\t' 'BEGIN { bad = 0 } { for (i = 1; i < NF; i++) { split($i, kv, "="); if (kv[2] != "") bad++ } } END { exit bad > 0 }' "$P5_FAKE_LOG.env"; then
    echo "gh finti: GH_HOST, GH_REPO e i token enterprise non arrivano mai"
  else
    echo "VARIABILI DI GH ARRIVATE AI GH FINTI"; rc=1
  fi
  [ "$(cat "$T/fake/terminal-prompt" 2>/dev/null)" = 0 ] && echo "git di rete: GIT_TERMINAL_PROMPT=0" || { echo "GIT_TERMINAL_PROMPT NON IMPOSTATO"; rc=1; }
  echo "--- registro dei comandi gh (profilo p5)"
  python3 -B -I "$GH4/ghguard.py" log "$P5_FAKE_LOG" || rc=1
  echo "--- registro dei comandi claude"
  check_claude_log "$P5_FAKE_CLAUDE_LOG" || rc=1
  if [ "$(grep -c '/probe-bin$' "$P5_FAKE_CLAUDE_LOG.path")" = "$(grep -c $'^plugin\teval' "$P5_FAKE_CLAUDE_LOG")" ]; then
    echo "shim della sonda in testa al PATH di ogni eval: sì"
  else
    echo "SHIM NON IN TESTA AL PATH"; rc=1
  fi
  echo "--- prova negativa della guardia gh"
  check_negativi "$T" || { echo "PROVA NEGATIVA FALLITA"; rc=1; }
  echo "--- prova negativa dei comandi git"
  check_git_negativi || { echo "PROVA NEGATIVA GIT FALLITA"; rc=1; }
  echo "--- comandi.log delle uscite"
  python3 -B -I "$GH4/ghguard.py" comandi "$T/out/comandi.log" | grep -v '^ *[0-9]* *gh ' || true
  python3 -B -I "$GH4/ghguard.py" comandi "$T/out/comandi.log" >/dev/null || { echo "COMANDI REGISTRATI RIFIUTATI"; rc=1; }
  echo "righe RIFIUTATO nel registro: $(grep -c RIFIUTATO "$T/out/comandi.log")"
  echo "--- remoti e rami nei nudi"
  for f in "$OWNER/tollgate" "$OWNER/tollgate-p4-detect"; do
    echo "  $f: $(git --git-dir "$T/remote/$f.git" for-each-ref --format='%(refname:short)' refs/heads 2>/dev/null | sort | paste -sd, -)"
  done
  echo "  PINS: $(paste -sd' ' "$T/out/pins-scelta.tsv" 2>/dev/null | tr '\t' ':')"
  echo "--- uscite attese"
  for f in token-scan.txt ci-auth.out ci-repo-esiste.rc ci-push-main.rc ci-push-sonda.rc ci-sonda.env ci-riepilogo.txt ci-log.out runs.tsv \
           pins.tsv pins-motore.tsv pins-scelta.tsv cache-pr.env cache-mode.txt cache-pr-close.rc pin-iniziale.out pin-on.rc pin-ripristino.rc \
           pin-dopo.out pin-v4-log-failed.out pin-ramo.env raccogli-versioni.txt raccogli-minuti.txt raccogli-budget.txt ritentativi.log comandi.log prs-aperte.txt; do
    [ -e "$T/out/$f" ] || { echo "  manca $f"; missing=1; }
  done
  [ "$missing" = 0 ] && echo "  tutte presenti"
  [ "$missing" = 0 ] || rc=1
  echo "--- evidenze degli eval"
  hit="$(ls -d "$T"/eval/*-sonda-skill 2>/dev/null | head -n 1)"
  if [ -n "$hit" ]; then
    echo "  copiati: $(find "$hit/corse" -type f 2>/dev/null | wc -l) file delle corse; result.json: $([ -s "$hit/result.json" ] && echo sì || echo no); aggregate-result.json: $([ -s "$hit/aggregate-result.json" ] && echo sì || echo no)"
  else
    echo "  cartella di sonda-skill assente"; rc=1
  fi
  echo "  budget.tsv:"; sed 's/^/    /' "$T/eval/budget.tsv"
  echo "  budget del residuo (78.5 speso):"; grep -- '--max-cost-usd' "$T/eval-b1/comandi.log" | sed 's/.*--max-cost-usd \([0-9.]*\).*/    tetto \1/' | head -n 2
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

case "$MODE" in
  eval-sonda|ci-sonda|pins|detect-cache|detect-pin|raccogli|cerca-token)
    mkdir -p "$OUT" "$WORK"; "modo_${MODE//-/_}" ;;
  raccogli-corse) shift; modo_raccogli_corse "$@" ;;
  controlla) modo_controlla ;;
  *) echo "uso: $0 eval-sonda|ci-sonda|pins|detect-cache|detect-pin|raccogli|raccogli-corse|cerca-token|controlla" >&2; exit 2 ;;
esac
