#!/usr/bin/env bash
# spikes/b3bis/models-prova.sh — prova vera del controllo dei modelli (B3-bis, Task 7). La esegue solo il controller.
# Chiama gli elenchi dei fornitori per cui l'ambiente ha una chiave (una richiesta di elenco per fornitore, nessun token).
# Uso: models-prova.sh controlla | prepara | prova
#
#   controlla  nessuna rete, nessuna scrittura: verifica bash, git, l'interprete, il progetto di prova e il tollgate; stampa
#              di ogni variabile di chiave di templates/models.toml solo se è impostata (mai il valore)
#   prepara    copia spikes/b3bis/progetto/ in $B3BIS_DIR/repo, crea un origin nudo locale, committa e spinge; crea lo stato
#              con la sentinella in $B3BIS_DIR/state. Ciò che esiste già si rinomina in <nome>.prev-<tempo>
#   prova      dal repo di prova lancia due volte `tollgate models check` (la prima con --refresh) con l'ambiente dell'utente;
#              salva le uscite in $B3BIS_DIR/out/ (una per corsa) solo se nessuna contiene il valore di una variabile di chiave
#
# Variabili: B3BIS_DIR (predefinita /tmp/tollgate-b3bis; ammessa solo quella o una sotto /tmp/tollgate-b3bis-test-*),
# B3BIS_PY (predefinita python3.11), B3BIS_TOLLGATE (predefinita <plugin>/bin/tollgate; sotto /tmp/tollgate-b3bis-test-*
# è obbligatoria: nei test è un finto). Il valore di una chiave non viene mai stampato, copiato né passato come argomento.
set -uo pipefail
umask 077   # le uscite e lo stato stanno in /tmp, condiviso
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
MODE="${1:-}"

DEFAULT_DIR=/tmp/tollgate-b3bis
DIR="${B3BIS_DIR:-$DEFAULT_DIR}"
PY="${B3BIS_PY:-python3.11}"
TOLLGATE="${B3BIS_TOLLGATE:-$root/bin/tollgate}"
PROJ="$here/progetto"
PROVIDERS_FILE="$root/templates/models.toml"
REPO="$DIR/repo"
BARE="$DIR/origin.git"
STATE="$DIR/state"
OUT="$DIR/out"
FAKE_REQUIRED=0

die() { echo "ERRORE: $*" >&2; exit 1; }

# rot <percorso...>: se esiste lo rinomina in <percorso>.prev-<tempo> (mai cancellare)
rot() {
  local p
  for p in "$@"; do
    if [ -e "$p" ] || [ -L "$p" ]; then mv -- "$p" "$p.prev-$(date +%Y%m%d-%H%M%S)-$$"; fi
  done
}

# verifica_dir: B3BIS_DIR è /tmp/tollgate-b3bis, oppure /tmp/tollgate-b3bis-test-<nome> o una sola cartella sotto di essa;
# senza `..`, senza link simbolici (né B3BIS_DIR né la cartella <nome>) e, se esiste, con `pwd -P` uguale al percorso dato
verifica_dir() {
  local rest top
  case "$DIR" in
    *..*) die "B3BIS_DIR ($DIR) contiene '..'" ;;
    */) die "B3BIS_DIR ($DIR) finisce con '/'" ;;
    "$DEFAULT_DIR") top="$DIR" ;;
    "$DEFAULT_DIR"-test-?*)
      FAKE_REQUIRED=1
      rest="${DIR#"$DEFAULT_DIR"-test-}"
      case "$rest" in
        /*|*//*|*/*/*) die "B3BIS_DIR ($DIR): ammesso un solo livello sotto $DEFAULT_DIR-test-<nome>" ;;
      esac
      top="$DEFAULT_DIR-test-${rest%%/*}"
      ;;
    *) die "B3BIS_DIR ($DIR) non è $DEFAULT_DIR né sta sotto $DEFAULT_DIR-test-*" ;;
  esac
  local d
  for d in "$top" "$DIR"; do
    if [ -L "$d" ]; then die "B3BIS_DIR: $d è un link simbolico"; fi
    if [ -e "$d" ] && [ "$(cd "$d" 2>/dev/null && pwd -P)" != "$d" ]; then die "B3BIS_DIR: $d non è un percorso reale"; fi
  done
}

# nomi_chiavi: i nomi delle variabili di chiave di templates/models.toml, nell'ordine del file (mai i valori)
nomi_chiavi() {
  grep -E '^env = ' "$PROVIDERS_FILE" | grep -oE '"[A-Z][A-Z0-9_]*"' | tr -d '"'
}

# chiave_impostata <nome>: sì se la variabile è impostata e non vuota (le vuote si saltano, come in api_key)
chiave_impostata() {
  [ -n "${!1:-}" ]
}

verifica_tollgate() {
  if [ "$FAKE_REQUIRED" = 1 ] && [ -z "${B3BIS_TOLLGATE:-}" ]; then
    die "sotto $DEFAULT_DIR-test-* serve B3BIS_TOLLGATE (un tollgate finto)"
  fi
  [ -f "$TOLLGATE" ] || die "il tollgate $TOLLGATE non esiste"
}

# ---------------------------------------------------------------- controlla

modo_controlla() {
  local rc=0 f n
  echo "cartella di lavoro: $DIR"
  echo "interprete: $PY"
  echo "tollgate: $TOLLGATE"
  command -v bash >/dev/null 2>&1 && echo "  bash: ok" || { echo "  manca bash"; rc=1; }
  command -v git >/dev/null 2>&1 && echo "  git: ok" || { echo "  manca git"; rc=1; }
  command -v "$PY" >/dev/null 2>&1 && echo "  interprete: ok" || { echo "  manca l'interprete $PY"; rc=1; }
  [ -f "$TOLLGATE" ] && echo "  tollgate: ok" || { echo "  manca il tollgate $TOLLGATE"; rc=1; }
  [ "$FAKE_REQUIRED" = 1 ] && [ -z "${B3BIS_TOLLGATE:-}" ] && { echo "  sotto la cartella dei test serve B3BIS_TOLLGATE"; rc=1; }
  [ -f "$PROVIDERS_FILE" ] || { echo "  manca $PROVIDERS_FILE"; rc=1; }
  echo "--- il progetto di prova"
  for f in tollgate.toml ai/models.py README.md; do
    [ -f "$PROJ/$f" ] && echo "  $f: ok" || { echo "  manca spikes/b3bis/progetto/$f"; rc=1; }
  done
  bash -n "$here/models-prova.sh" || { echo "  bash -n fallito"; rc=1; }
  echo "--- le variabili di chiave (solo se impostate, mai il valore)"
  if [ -f "$PROVIDERS_FILE" ]; then
    local any=0
    while IFS= read -r n; do
      [ -n "$n" ] || continue
      if chiave_impostata "$n"; then echo "  chiave $n: impostata"; any=1; else echo "  chiave $n: non impostata"; fi
    done < <(nomi_chiavi)
    [ "$any" = 1 ] || echo "  nessuna chiave impostata: la prova non farebbe rete"
  fi
  echo "--- i passi"
  echo "  prepara   copia il progetto in $REPO, origin nudo in $BARE, stato in $STATE"
  echo "  prova     da $REPO: tollgate models check --refresh, poi tollgate models check; uscite in $OUT"
  [ "$rc" = 0 ] && echo "CONTROLLA: ok" || echo "CONTROLLA: FALLITO"
  return "$rc"
}

# ---------------------------------------------------------------- prepara

modo_prepara() {
  command -v git >/dev/null 2>&1 || die "manca git"
  [ -f "$PROJ/tollgate.toml" ] && [ -f "$PROJ/ai/models.py" ] || die "manca il progetto di prova ($PROJ)"
  mkdir -p "$DIR" || die "cartella $DIR non creata"
  rot "$REPO" "$BARE" "$STATE" "$OUT"
  mkdir -p "$REPO" "$STATE" || die "cartelle non create"
  : > "$STATE/.tollgate-test"
  cp -R "$PROJ/." "$REPO/" || die "progetto non copiato"
  git init -q --bare -b main "$BARE" || die "origin nudo non creato"
  git -C "$BARE" config user.name prova; git -C "$BARE" config user.email prova@example.com
  git -C "$BARE" config commit.gpgsign false
  git init -q -b main "$REPO" || die "git init fallito"
  (
    cd "$REPO" || exit 1
    git config user.name prova; git config user.email prova@example.com; git config commit.gpgsign false
    git add -A && git commit -qm "progetto di prova" || exit 1
    git remote add origin "$BARE"
    git push -q -u origin main || exit 1
    git remote set-head origin main
    git config tollgate.defaultBranch main
  ) || die "repo di prova non creato"
  echo "repo di prova: $REPO (origin $BARE), stato: $STATE"
}

# ---------------------------------------------------------------- prova

# corsa <nome> <argomenti...>: lancia tollgate dal repo e tiene l'uscita in $CORSA_OUT; mai stampata prima del controllo
corsa() {
  local nome="$1"; shift
  CORSA_OUT="$(cd "$REPO" && TOLLGATE_STATE="$STATE" "$PY" -B "$TOLLGATE" "$@" 2>&1)"
  CORSA_RC=$?
  echo "corsa $nome: uscita $CORSA_RC"
}

# uscita_pulita: sì (0) se $CORSA_OUT non contiene il valore di nessuna variabile di chiave non vuota. Il confronto è
# interno a bash; lo script dice solo sì o no e il nome della variabile, mai il valore.
uscita_pulita() {
  local n ok=0
  while IFS= read -r n; do
    [ -n "$n" ] || continue
    chiave_impostata "$n" || continue
    if [[ "$CORSA_OUT" == *"${!n}"* ]]; then
      echo "ERRORE: l'uscita contiene il valore di una variabile di chiave ($n): non salvata" >&2
      ok=1
    fi
  done < <(nomi_chiavi)
  return "$ok"
}

modo_prova() {
  verifica_tollgate
  [ -f "$STATE/.tollgate-test" ] || die "manca lo stato di prova con la sentinella ($STATE/.tollgate-test): lancia prepara"
  [ -d "$REPO/.git" ] || die "manca il repo di prova ($REPO): lancia prepara"
  [ -z "${TOLLGATE_TEST_CONFIG:-}" ] || die "TOLLGATE_TEST_CONFIG è impostata"
  local nomi=(refresh cache) args i
  [ -e "$OUT" ] && die "$OUT esiste già: lancia prepara per una prova nuova"
  mkdir -p "$OUT" || die "cartella $OUT non creata"
  for i in 0 1; do
    if [ "$i" = 0 ]; then args=(models check --refresh); else args=(models check); fi
    corsa "${nomi[$i]}" "${args[@]}"
    uscita_pulita || { rmdir "$OUT" 2>/dev/null; exit 1; }
    printf '%s\n' "$CORSA_OUT" > "$OUT/${nomi[$i]}.txt" || die "uscita non salvata"
    echo "salvata: $OUT/${nomi[$i]}.txt"
  done
  echo "prova finita: uscite in $OUT"
}

case "$MODE" in
  controlla|prepara|prova) verifica_dir ;;
esac
case "$MODE" in
  controlla) modo_controlla ;;
  prepara) modo_prepara ;;
  prova) modo_prova ;;
  *) echo "uso: $0 controlla | prepara | prova" >&2; exit 2 ;;
esac
