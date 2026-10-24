#!/usr/bin/env bash
# Esegue gli eval veri di tollgate con `claude plugin eval` (decisioni 8, 9 e 23). Solo il controller, in locale.
#
#   evals/run.sh [--a-secco] <spec|extra|nome-del-caso> [--runs N]
#
# --a-secco: fa tutto fino alla stampa del comando (rifiuti, preambolo, residuo, bersaglio) ed esce 0 senza lock,
# senza prenotare e senza lanciare claude (1 se il tetto è esaurito, come la corsa vera).
#
# Controlla il residuo del tetto (80 USD in budget.tsv), costruisce il bersaglio fuori dal repo, mette
# tests/evalbin (shim di gh e python3) in testa al PATH di chi lancia l'eval, lancia claude con --no-publish
# e una cartella d'uscita fissa, scrive il costo in budget.tsv qualunque sia l'uscita, copia le corse tenute
# in <uscita>/runs/ e controlla che il plugin tollgate sia caricato nel braccio con plugin.
#
# Uscite: 0, 1, 2 sono quelle di claude (1 = sotto soglia, 2 = tetto raggiunto) tranne il rifiuto per
# residuo esaurito (1, claude non parte); 3 = costo ignoto; 4 = plugin non caricato; 64 = uso errato.
#
# Variabili. BUDGET, EVIDENCE e TARGET valgono SOLO con TOLLGATE_EVAL_TEST_MODE=1 (i test le puntano a cartelle
# temporanee); senza, se una è impostata, l'uscita è 64 prima di tutto:
#   TOLLGATE_EVAL_BUDGET    registro dei costi (predefinito docs/verifiche/evidenze/eval-p5/budget.tsv)
#   TOLLGATE_EVAL_EVIDENCE  radice delle cartelle d'uscita (predefinita docs/verifiche/evidenze/eval-p5)
#   TOLLGATE_EVAL_TARGET    bersaglio (predefinito /tmp/tollgate-eval-target, decisione 9 (c))
# Valgono sempre:
#   TOLLGATE_EVAL_TMPDIR    TMPDIR dell'eval (predefinito $HOME/.cache/tollgate-eval-tmp), mai sotto /tmp, /var/tmp, /dev/shm
#   TOLLGATE_EVAL_TIMEOUT   secondi per invocazione, intero positivo (predefinito 3600; dopo 30 s di grazia, SIGKILL)
#   TOLLGATE_EVAL_TEST_MODE=1  solo per i test: abilita le tre variabili sopra e salta il rifiuto di /tmp per la cartella
#                           temporanea (i test stanno in /tmp); il preambolo lo stampa
#
# Una sola invocazione alla volta (flock su <registro>.lock). Prima del lancio di claude la riga dell'invocazione
# entra in budget.tsv con costUsd «?»: se lo script muore (anche SIGKILL) il residuo resta 0 finché non la correggi a mano.
set -u
die() { echo "$1" >&2; exit "${2:-64}"; }
if [ "${TOLLGATE_EVAL_TEST_MODE:-}" != 1 ]; then
  for v in TOLLGATE_EVAL_BUDGET TOLLGATE_EVAL_EVIDENCE TOLLGATE_EVAL_TARGET; do
    [ -z "${!v:-}" ] || die "$v è impostata ma vale solo con TOLLGATE_EVAL_TEST_MODE=1: la tolgo dall'ambiente e rilancio"
  done
fi
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
EVIDENCE="${TOLLGATE_EVAL_EVIDENCE:-$root/docs/verifiche/evidenze/eval-p5}"
# Il registro: fuori dai test non si esporta niente e cost.py usa il suo predefinito (lo stesso percorso).
if [ "${TOLLGATE_EVAL_TEST_MODE:-}" = 1 ] && [ -n "${TOLLGATE_EVAL_BUDGET:-}" ]; then
  budget_file="$TOLLGATE_EVAL_BUDGET"; export TOLLGATE_EVAL_BUDGET
else
  budget_file="$root/docs/verifiche/evidenze/eval-p5/budget.tsv"; unset TOLLGATE_EVAL_BUDGET
fi
TARGET="${TOLLGATE_EVAL_TARGET:-/tmp/tollgate-eval-target}"
MODEL=claude-sonnet-5-5
THRESHOLD=0.66
DEFAULT_RUNS=3         # decisione 8: tre corse per caso
TOKEN_PATTERN='gh[pos]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|sk-ant-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}'

cost() { python3 -B "$here/cost.py" "$@"; }

# ---------------------------------------------------------------- argomenti

selector="" runs="$DEFAULT_RUNS" dry=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-dir|--output-dir=*|--json|--json=*|--report|--report=*|--publish|--publish=*|--publish-report|--publish-report=*)
      die "argomento rifiutato ($1): cartella d'uscita, JSON e rapporto sono fissi e il rapporto non si pubblica mai" ;;
    --a-secco) dry=1; shift ;;
    --runs)
      [ "$#" -ge 2 ] || die "--runs vuole un numero"
      runs="$2"; shift 2 ;;
    --runs=*) runs="${1#--runs=}"; shift ;;
    -*) die "argomento sconosciuto: $1 (uso: run.sh [--a-secco] <spec|extra|caso> [--runs N])" ;;
    *)
      [ -z "$selector" ] || die "un solo selettore: spec, extra o il nome di un caso"
      selector="$1"; shift ;;
  esac
done
[ -n "$selector" ] || die "uso: run.sh <spec|extra|caso> [--runs N]"
eval_timeout="${TOLLGATE_EVAL_TIMEOUT:-3600}"
case "$eval_timeout" in ''|*[!0-9]*|0|0[0-9]*) die "TOLLGATE_EVAL_TIMEOUT vuole un intero positivo di secondi: $eval_timeout" ;; esac
[ "${#eval_timeout}" -le 6 ] || die "TOLLGATE_EVAL_TIMEOUT troppo grande: $eval_timeout"
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

if [ "$dry" = 0 ]; then
  mkdir -p "$(dirname "$budget_file")" || die "cartella del registro non creabile" 1
  exec 9>"$budget_file.lock" || die "file di lock non apribile: $budget_file.lock" 1
  flock -n 9 || die "un'altra invocazione di run.sh è in corso (lock $budget_file.lock): una alla volta"
fi

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
echo "registro dei costi: $budget_file"
echo "cartella delle evidenze: $EVIDENCE"
echo "bersaglio: $TARGET"
echo "TMPDIR dell'eval: $evtmp"
echo "residuo del tetto: $cap USD"
[ "${TOLLGATE_EVAL_TEST_MODE:-}" != 1 ] || echo "!! TEST_MODE attivo: percorsi di prova, non è una corsa vera"

# ---------------------------------------------------------------- bersaglio e cartella d'uscita

python3 -B "$here/_kit/target.py" "$root" "$TARGET" >/dev/null || die "bersaglio non costruito in $TARGET" 1
shim_dir="$TARGET/tests/evalbin"
[ -x "$shim_dir/gh" ] && [ -x "$shim_dir/python3" ] || die "shim assenti in $shim_dir" 1

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dir="$EVIDENCE/$stamp-$selector"
if [ "$dry" = 0 ]; then
  mkdir -p "$dir" || die "cartella d'uscita non creabile: $dir" 1
  dir="$(realpath -e -- "$dir")"
fi

label="$selector ($ablation, --runs $runs)"
cmd=(claude plugin eval "$TARGET" "${select_args[@]}" --runs "$runs" --scaffold --trust-plugin --no-publish
     --model "$MODEL" --allow-tools Bash Write Edit --threshold "$THRESHOLD" --ablation "$ablation"
     --max-cost-usd "$cap" --keep-temp --output-dir "$dir" --json "$dir/result.json" --report "$dir/report.html")

echo "== $label"
echo "comando: PATH=$shim_dir:\$PATH TMPDIR=$evtmp timeout -k 30 $eval_timeout ${cmd[*]}"
echo "uscita: $dir"
if [ "$dry" = 1 ]; then
  echo "a secco: niente lock, niente prenotazione, claude non lanciato"
  exit 0
fi
printf '%s\n' "TMPDIR dell eval: $evtmp" > "$dir/tmpdir.txt"
printf '%s claude %s\n' "$(date -u +%FT%TZ)" "${cmd[*]:1}" >> "$dir/comando.txt"

reserved="$(cost reserve --label "$label")" || die "prenotazione del costo in budget.tsv fallita: non lancio niente" 1
( cd "$TARGET" && PATH="$shim_dir:$PATH" TMPDIR="$evtmp" timeout -k 30 "$eval_timeout" "${cmd[@]}" \
    >"$dir/stdout.txt" 2>"$dir/stderr.txt" </dev/null 9>&- )
rc=$?
echo "$rc" > "$dir/claude.rc"

# ---------------------------------------------------------------- costo: qualunque sia l'uscita

if [ ! -s "$dir/result.json" ]; then
  echo "uscita di claude: $rc" >&2
  die "costo ignoto: controlla a mano prima di continuare ($dir): la riga «?» resta in budget.tsv" 3
fi
if ! cost add "$dir/result.json" --label "$label" --reserved "$reserved"; then
  die "costo ignoto: controlla a mano prima di continuare ($dir): la riga «?» resta in budget.tsv" 3
fi
after="$(cost remaining)"
run_cost="$(grep -F "$reserved" "$budget_file" | tail -n 1 | cut -f3)"
echo "uscita di claude: $rc; costo dell'invocazione $run_cost USD; residuo $after USD"

# ---------------------------------------------------------------- copia delle corse tenute (modello: spikes/p5/run-p5-checks.sh)

# run_dir_ok <cartella>: stampa il percorso risolto se è claude-eval-* ed è figlia diretta della cartella temporanea dell'eval
run_dir_ok() {
  local r parent base allowed
  [ ! -L "$1" ] || return 1                                 # una corsa che è un collegamento simbolico non si segue
  r="$(realpath -e -- "$1" 2>/dev/null)" || return 1
  base="$(basename "$r")"; parent="$(dirname "$r")"
  case "$base" in claude-eval-?*) ;; *) return 1 ;; esac
  allowed="$(realpath -m -- "$evtmp" 2>/dev/null)" || return 1
  [ "$parent" = "$allowed" ] || return 1
  printf '%s\n' "$r"
}

# real_dir / real_file: cartella o file veri, mai collegamenti simbolici (né il percorso finale né la cartella madre indicata)
real_dir() { [ -d "$1" ] && [ ! -L "$1" ]; }
real_file() { [ -f "$1" ] && [ ! -L "$1" ]; }

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
  [ -d "$run" ] && chmod 700 "$run" 2>/dev/null
  real_dir "$run/sealed" && chmod 700 "$run/sealed" 2>/dev/null
  mkdir -p "$dest"
  if real_dir "$run/out" && real_file "$run/out/trace.jsonl"; then cp_checked "$run/out/trace.jsonl" "$dest/trace.jsonl" "$dest" && n=$((n + 1)); fi
  if real_dir "$run/config" && real_file "$run/config/settings.json"; then
    if grep -qiE "$TOKEN_PATTERN|\"[A-Za-z_]*(token|api_?key|secret|password)[A-Za-z_]*\"[[:space:]]*:[[:space:]]*\"[^\"]+\"" "$run/config/settings.json"; then
      echo "settings.json contiene forme di credenziali: non copiato" > "$dest/settings-non-copiato.txt"
    else
      cp -n -- "$run/config/settings.json" "$dest/settings.json" && n=$((n + 1))
    fi
  fi
  if real_dir "$run/sealed/home" && real_dir "$run/sealed/home/cwd"; then
    while IFS= read -r f; do
      mkdir -p "$dest/cwd/$(dirname "${f#"$run/sealed/home/cwd/"}")"
      cp_checked "$f" "$dest/cwd/${f#"$run/sealed/home/cwd/"}" "$dest" && n=$((n + 1))
    done < <(find "$run/sealed/home/cwd" -maxdepth 6 \( -name .git -o -name .origin.git -o -name node_modules \) -prune -o \
               -type f -size -300k -print 2>/dev/null)
  fi
  for d in .local/state/tollgate .tollgate-eval; do
    real_dir "$run/sealed/home" && real_dir "$run/sealed/home/$d" || continue
    while IFS= read -r f; do
      mkdir -p "$dest/home/$(dirname "${f#"$run/sealed/home/"}")"
      cp_checked "$f" "$dest/home/${f#"$run/sealed/home/"}" "$dest" && n=$((n + 1))
    done < <(find "$run/sealed/home/$d" -maxdepth 6 -type f -size -300k 2>/dev/null)
  done
  f=.claude/plugins/installed_plugins.json
  if real_dir "$run/sealed/home/.claude/plugins" && real_file "$run/sealed/home/$f"; then
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

status=0
cost table "$dir/result.json" > "$dir/tabella.md" || true
if ! problems="$(cost plugin-check "$dir/result.json")"; then
  printf '%s\n' "$problems" >&2
  echo "plugin tollgate non caricato: controlla prima di continuare ($dir)" >&2
  status=4
fi
# forme di token nei file d'uscita che finiscono nelle evidenze (mai stampate, solo i nomi)
leaks="$(cd "$dir" && grep -alE "$TOKEN_PATTERN" stdout.txt stderr.txt result.json report.html 2>/dev/null)"
if [ -n "$leaks" ]; then
  printf '%s\n' "$leaks" > "$dir/file-con-token.txt"
  echo "forma di token nelle evidenze: non committare ($(printf '%s' "$leaks" | tr '\n' ' ')in $dir)" >&2
  status=4
fi
[ "$status" = 0 ] || exit "$status"
exit "$rc"
