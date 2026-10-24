#!/usr/bin/env bash
# Esegue gli eval veri di tollgate con `claude plugin eval` (decisioni 8, 9 e 23). Solo il controller, in locale.
#
#   evals/run.sh <spec|extra|nome-del-caso> [--runs N]
#
# Controlla il residuo del tetto (80 USD in budget.tsv), costruisce il bersaglio fuori dal repo, mette
# tests/evalbin (shim di gh e python3) in testa al PATH di chi lancia l'eval, lancia claude con --no-publish
# e una cartella d'uscita fissa, scrive il costo in budget.tsv qualunque sia l'uscita, copia le corse tenute
# in <uscita>/runs/ e controlla che il plugin tollgate sia caricato nel braccio con plugin.
#
# Uscite: 0, 1, 2 sono quelle di claude (1 = sotto soglia, 2 = tetto raggiunto) tranne il rifiuto per
# residuo esaurito (1, claude non parte); 3 = costo ignoto; 4 = plugin non caricato; 64 = uso errato.
#
# Variabili (i test le puntano a cartelle temporanee, mai ai percorsi veri):
#   TOLLGATE_EVAL_BUDGET    registro dei costi (predefinito docs/verifiche/evidenze/eval-p5/budget.tsv)
#   TOLLGATE_EVAL_EVIDENCE  radice delle cartelle d'uscita (predefinita docs/verifiche/evidenze/eval-p5)
#   TOLLGATE_EVAL_TARGET    bersaglio (predefinito /tmp/tollgate-eval-target, decisione 9 (c))
#   TOLLGATE_EVAL_TMPDIR    TMPDIR dell'eval (predefinito $HOME/.cache/tollgate-eval-tmp), mai sotto /tmp, /var/tmp, /dev/shm
#   TOLLGATE_EVAL_TIMEOUT   secondi per invocazione (predefinito 3600)
#   TOLLGATE_EVAL_TEST_MODE=1  solo per i test: la cartella temporanea dei test sta in /tmp, quindi salta quel rifiuto
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
EVIDENCE="${TOLLGATE_EVAL_EVIDENCE:-$root/docs/verifiche/evidenze/eval-p5}"
export TOLLGATE_EVAL_BUDGET="${TOLLGATE_EVAL_BUDGET:-$root/docs/verifiche/evidenze/eval-p5/budget.tsv}"
TARGET="${TOLLGATE_EVAL_TARGET:-/tmp/tollgate-eval-target}"
MODEL=claude-sonnet-5-5
THRESHOLD=0.66
DEFAULT_RUNS=3         # decisione 8: tre corse per caso
TOKEN_PATTERN='gh[pos]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|sk-ant-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}'

die() { echo "$1" >&2; exit "${2:-64}"; }
cost() { python3 -B "$here/cost.py" "$@"; }

# ---------------------------------------------------------------- argomenti

selector="" runs="$DEFAULT_RUNS"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-dir|--output-dir=*|--json|--json=*|--report|--report=*|--publish|--publish=*|--publish-report|--publish-report=*)
      die "argomento rifiutato ($1): cartella d'uscita, JSON e rapporto sono fissi e il rapporto non si pubblica mai" ;;
    --runs)
      [ "$#" -ge 2 ] || die "--runs vuole un numero"
      runs="$2"; shift 2 ;;
    --runs=*) runs="${1#--runs=}"; shift ;;
    -*) die "argomento sconosciuto: $1 (uso: run.sh <spec|extra|caso> [--runs N])" ;;
    *)
      [ -z "$selector" ] || die "un solo selettore: spec, extra o il nome di un caso"
      selector="$1"; shift ;;
  esac
done
[ -n "$selector" ] || die "uso: run.sh <spec|extra|caso> [--runs N]"
case "$runs" in ''|*[!0-9]*|0|0[0-9]*) die "--runs vuole un intero positivo: $runs" ;; esac
[ "${#runs}" -le 3 ] || die "--runs troppo grande: $runs"

# case_tags <caso>: i tag di evals/<caso>/case.yaml (riga `tags: [a, b]`)
case_tags() { sed -n 's/^tags:[[:space:]]*\[\(.*\)\][[:space:]]*$/\1/p' "$root/evals/$1/case.yaml" | head -n 1 | tr -d ' '; }

declare -a select_args
case "$selector" in
  spec)  select_args=(--tag spec);  ablation=with-without ;;
  extra) select_args=(--tag extra); ablation=none ;;
  *)
    case "$selector" in */*|.*|*..*) die "caso non valido: $selector" ;; esac
    [ -f "$root/evals/$selector/case.yaml" ] || die "caso inesistente in evals/: $selector"
    tags=",$(case_tags "$selector"),"
    case "$tags" in
      *,spec,*)  ablation=with-without ;;
      *,extra,*) ablation=none ;;
      *) die "il caso $selector non ha il tag spec né extra: non so che ablazione usare" ;;
    esac
    select_args=(--case "$selector") ;;
esac

# ---------------------------------------------------------------- tetto

cap="$(cost remaining)" || die "budget.tsv illeggibile: non lancio niente" 1
if ! awk -v c="$cap" 'BEGIN { exit !(c >= 0.01) }'; then
  die "tetto di 80 USD esaurito (residuo $cap): non lancio niente. Chiedi all'utente." 1
fi

# ---------------------------------------------------------------- cartella temporanea dell'eval

# eval_tmpdir: fuori da /tmp, /var/tmp e /dev/shm (la sandbox li ha in denyWrite e quel divieto prevale sulle cartelle della corsa);
# il rifiuto vale anche dopo la risoluzione di `..` e dei collegamenti simbolici
eval_tmpdir() {
  local d="${TOLLGATE_EVAL_TMPDIR:-$HOME/.cache/tollgate-eval-tmp}" r
  case "$d" in /*) ;; *) die "TOLLGATE_EVAL_TMPDIR deve essere un percorso assoluto: $d" ;; esac
  r="$(realpath -m -- "$d")" || die "TOLLGATE_EVAL_TMPDIR non risolvibile: $d"
  if [ "${TOLLGATE_EVAL_TEST_MODE:-}" != 1 ]; then
    case "$r" in /tmp|/tmp/*|/var/tmp|/var/tmp/*|/dev/shm|/dev/shm/*) die "TOLLGATE_EVAL_TMPDIR non può stare sotto /tmp, /var/tmp o /dev/shm: $d -> $r" ;; esac
  fi
  mkdir -p "$r" && chmod 700 "$r" || die "cartella temporanea $r non creabile"
  r="$(realpath -e -- "$r")"
  if [ "${TOLLGATE_EVAL_TEST_MODE:-}" != 1 ]; then
    case "$r" in /tmp|/tmp/*|/var/tmp|/var/tmp/*|/dev/shm|/dev/shm/*) die "TOLLGATE_EVAL_TMPDIR risolve sotto /tmp, /var/tmp o /dev/shm: $d -> $r" ;; esac
  fi
  printf '%s\n' "$r"
}
evtmp="$(eval_tmpdir)" || exit $?

# ---------------------------------------------------------------- bersaglio e cartella d'uscita

python3 -B "$here/_kit/target.py" "$root" "$TARGET" >/dev/null || die "bersaglio non costruito in $TARGET" 1
shim_dir="$TARGET/tests/evalbin"
[ -x "$shim_dir/gh" ] && [ -x "$shim_dir/python3" ] || die "shim assenti in $shim_dir" 1

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dir="$EVIDENCE/$stamp-$selector"
mkdir -p "$dir" || die "cartella d'uscita non creabile: $dir" 1
dir="$(realpath -e -- "$dir")"

label="$selector ($ablation, --runs $runs)"
cmd=(claude plugin eval "$TARGET" "${select_args[@]}" --runs "$runs" --scaffold --trust-plugin --no-publish
     --model "$MODEL" --allow-tools Bash Write Edit --threshold "$THRESHOLD" --ablation "$ablation"
     --max-cost-usd "$cap" --keep-temp --output-dir "$dir" --json "$dir/result.json" --report "$dir/report.html")

echo "== $label"
echo "residuo del tetto: $cap USD"
echo "comando: PATH=$shim_dir:\$PATH TMPDIR=$evtmp timeout ${TOLLGATE_EVAL_TIMEOUT:-3600} ${cmd[*]}"
echo "uscita: $dir"
printf '%s\n' "TMPDIR dell eval: $evtmp" > "$dir/tmpdir.txt"
printf '%s claude %s\n' "$(date -u +%FT%TZ)" "${cmd[*]:1}" >> "$dir/comando.txt"

( cd "$TARGET" && PATH="$shim_dir:$PATH" TMPDIR="$evtmp" timeout "${TOLLGATE_EVAL_TIMEOUT:-3600}" "${cmd[@]}" \
    >"$dir/stdout.txt" 2>"$dir/stderr.txt" </dev/null )
rc=$?
echo "$rc" > "$dir/claude.rc"

# ---------------------------------------------------------------- costo: qualunque sia l'uscita

if [ ! -s "$dir/result.json" ]; then
  cost add "$dir/result.json" --label "$label" >/dev/null 2>&1      # riga con «?»: il residuo diventa 0
  echo "uscita di claude: $rc" >&2
  die "costo ignoto: controlla a mano prima di continuare ($dir)" 3
fi
if ! cost add "$dir/result.json" --label "$label"; then
  die "costo ignoto: controlla a mano prima di continuare ($dir)" 3
fi
after="$(cost remaining)"
run_cost="$(python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["costUsd"])' "$dir/result.json")"
echo "uscita di claude: $rc; costo dell'invocazione $run_cost USD; residuo $after USD"

# ---------------------------------------------------------------- copia delle corse tenute (modello: spikes/p5/run-p5-checks.sh)

# run_dir_ok <cartella>: stampa il percorso risolto se è claude-eval-* ed è figlia diretta della cartella temporanea dell'eval
run_dir_ok() {
  local r parent base allowed
  r="$(realpath -e -- "$1" 2>/dev/null)" || return 1
  base="$(basename "$r")"; parent="$(dirname "$r")"
  case "$base" in claude-eval-?*) ;; *) return 1 ;; esac
  allowed="$(realpath -m -- "$evtmp" 2>/dev/null)" || return 1
  [ "$parent" = "$allowed" ] || return 1
  printf '%s\n' "$r"
}

# cp_checked <origine> <destinazione> <cartella della corsa copiata>: non copia un file che contiene forme di token e lo registra
cp_checked() {
  local src="$1" dst="$2" note="$3"
  if grep -aqE "$TOKEN_PATTERN" "$src"; then
    printf '%s: forme di credenziali, non copiato\n' "${dst#"$note/"}" >> "$note/file-non-copiati.txt"
    return 1
  fi
  cp -n -- "$src" "$dst"
}

# copy_one_run <cartella della corsa tenuta> <cartella d'uscita>: le corse tenute da --keep-temp sono in
# <TMPDIR>/claude-eval-<sigla>/ con out/trace.jsonl e config/settings.json leggibili e home/ e tmp/ sigillati in sealed/ (modo 000):
# si rendono leggibili (chmod 700 della corsa e di sealed) e si copiano SOLO la trace, settings.json (se non contiene credenziali),
# i file del workspace (sealed/home/cwd, senza .git), lo stato di tollgate e il registro dei plugin scritto dallo scaffold.
copy_one_run() {
  local run f d n=0 name dest="$2/runs"
  run="$(run_dir_ok "$1")" || { echo "cartella rifiutata (non è claude-eval-* figlia diretta della cartella temporanea dell'eval): $1"; return 1; }
  name="$(basename "$run")"
  dest="$dest/$name"
  chmod 700 "$run" 2>/dev/null; [ -d "$run/sealed" ] && chmod 700 "$run/sealed" 2>/dev/null
  mkdir -p "$dest"
  if [ -f "$run/out/trace.jsonl" ]; then cp_checked "$run/out/trace.jsonl" "$dest/trace.jsonl" "$dest" && n=$((n + 1)); fi
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
      cp_checked "$f" "$dest/cwd/${f#"$run/sealed/home/cwd/"}" "$dest" && n=$((n + 1))
    done < <(find "$run/sealed/home/cwd" -maxdepth 6 \( -name .git -o -name .origin.git -o -name node_modules \) -prune -o \
               -type f -size -300k -print 2>/dev/null)
  fi
  for d in .local/state/tollgate .tollgate-eval; do
    [ -d "$run/sealed/home/$d" ] || continue
    while IFS= read -r f; do
      mkdir -p "$dest/home/$(dirname "${f#"$run/sealed/home/"}")"
      cp_checked "$f" "$dest/home/${f#"$run/sealed/home/"}" "$dest" && n=$((n + 1))
    done < <(find "$run/sealed/home/$d" -maxdepth 6 -type f -size -300k 2>/dev/null)
  done
  f=.claude/plugins/installed_plugins.json
  if [ -f "$run/sealed/home/$f" ]; then
    mkdir -p "$dest/home/$(dirname "$f")"
    cp_checked "$run/sealed/home/$f" "$dest/home/$f" "$dest" && n=$((n + 1))
  fi
  echo "corsa $name: $n file copiati in runs/$name"
}

# le corse tenute sono quelle che claude stampa in stderr («kept <cartella>:»)
grep -ahoE "kept (/[^[:space:]:]+)" "$dir/stdout.txt" "$dir/stderr.txt" 2>/dev/null | sed 's/^kept //' | sort -u > "$dir/cartelle-tenute.txt"
while IFS= read -r run; do
  copy_one_run "$run" "$dir" || echo "cartella tenuta ignorata: $run"
done < "$dir/cartelle-tenute.txt"

# ---------------------------------------------------------------- il plugin è caricato?

if ! problems="$(cost plugin-check "$dir/result.json")"; then
  printf '%s\n' "$problems" >&2
  die "plugin tollgate non caricato: controlla prima di continuare ($dir)" 4
fi
cost table "$dir/result.json" > "$dir/tabella.md" || true
exit "$rc"
