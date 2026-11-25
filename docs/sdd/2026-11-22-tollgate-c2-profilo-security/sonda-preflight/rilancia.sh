#!/usr/bin/env bash
# Rilancia la sonda delle precedenze su una copia `git archive` del worktree, mai sul repo vivo.
# Uso: bash rilancia.sh [<ref>]     (ref predefinito: HEAD; dal Task 3 in poi HEAD ha keep_paths
#                                    vera, dal Task 4 anche il frammento vero: la sonda li usa)
# Variabili: SONDA_FRAMMENTO=<percorso di un security.toml> prova un frammento non ancora committato
# (Task 4, Step 3a: il file del worktree si legge soltanto). SONDA_TEST=1 lancia anche FrontendPrecedenceTest e DatabasePrecedenceTest interi sulla
# copia (con keep_paths simulata e il frammento candidato aggiunti se HEAD non li ha ancora).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
REF="${1:-HEAD}"
T="$(mktemp -d /tmp/tollgate-preflight-XXXXXX)"
trap 'chmod -R u+rwX "$T" 2>/dev/null || true; rm -rf "$T"' EXIT
mkdir "$T/copia" "$T/tmp" "$T/home" "$T/state"
git -C "$REPO" archive "$REF" | tar -x -C "$T/copia"
export TMPDIR="$T/tmp" HOME="$T/home" TOLLGATE_STATE="$T/state"
rc=0
python3 -B "$HERE/sonda.py" --codice "$T/copia" ${SONDA_FRAMMENTO:+--frammento "$SONDA_FRAMMENTO"} || rc=$?
if [ "${SONDA_TEST:-0}" = 1 ]; then
  python3 -B "$HERE/prepara_copia.py" "$T/copia"
  (cd "$T/copia" && python3 -B -m unittest tests.test_init.FrontendPrecedenceTest \
      tests.test_init.DatabasePrecedenceTest 2>&1 | tail -4) || rc=$?
fi
exit "$rc"
