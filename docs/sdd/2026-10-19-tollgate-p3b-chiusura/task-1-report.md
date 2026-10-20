# Report Task 1 (P3b): verifiche dell'interfaccia di gh

Status: DONE_WITH_CONCERNS.

Creati `spikes/run-p3b-experiments.sh` (scrive in `/tmp/tollgate-p3b/help/` version, api, pr create/edit/list/view) e `docs/verifiche/2026-10-19-p3b-verifiche.md`. gh 2.46.0, claude 2.1.304 (annotata).

Esiti: G1 sì (aiuto; insteadOf non provato). G2 sì (--head/--base/--title/--body-file). G3 sì. G4 in parte: --state all, --head, --json, --jq, --limit ok; i nomi dei campi (headRefOid, mergedAt, comments) NON compaiono nell'aiuto di 2.46.0 (manca la sezione JSON FIELDS), quindi non verificati. G5 --paginate e --jq sì, formato per riga non provato, --slurp assente.

Dubbi: G4 campi JSON non verificabili senza eseguire `gh pr list --json` senza valore o con rete; fuori dalle regole del task.
Nessun TDD (task di sola verifica). Test: vedi sotto.

Test: tests/run -> python3.11: 997 test OK; python3 (3.13.5): 997 test OK.
