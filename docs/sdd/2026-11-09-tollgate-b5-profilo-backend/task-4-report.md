# Report Task 4 (impl-t4)

Fatto: rapporto `docs/profili/verifiche/backend-fonti.md` (4 tabelle + correzioni), pagina `docs/profili/backend.md` (9 punti in «Da decidere tu»), correzioni a `skills/rules-backend/SKILL.md` (R-01 e R-09 senza sezioni non reggenti, R-07 riscritta, R-08 con «Fail Securely», R-12 «scelta nostra»), `export function POST(` tolto dal frammento (23 marcatori), `RulesBackendPageTest` in `tests/test_rules_backend.py` (+ R-12 nel test «scelta nostra»).
TDD: RED = 16 errori (rapporto assente) prima dei file; GREEN = `python3 -B -m unittest tests.test_rules_backend` OK (39 test).
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3724 test OK (7 skip), python3 3724 OK (5 skip). Uscita in `task-4-suite.txt`.
Scostamenti: nessun `approved`; R-BACKEND-09 resta senza fonte «Verification».

## Fix round 1
Cambiato (solo testo e test): voce «Rinvio» (decisione 15: su main solo Task 1-2, regole/pagina/frammento sul ramo); fine di «Quando si accende» (percorso esatto, file gemelli al generico, file senza righe a mano); «Regole tolte» riscritta con l'elenco esatto delle differenze, senza id; riga sulle fonti corretta (server/, backend/, routes/, handlers/ sul catalogo e sul progetto di B); termini spiegati (edge function, namespace, bucket, lanciatore, orchestratore, tollgate.toml, gestore); intestazione del rapporto resa vera. Test nuovi: test_page_rinvio_says_what_stays_on_the_branch, test_page_explains_the_terms; `supabase/` tra i needle di «Da decidere tu».
Comandi: `python3 -B -m unittest tests.test_rules_backend tests.test_docs` OK (48); `PYTHONWARNINGS=error::ResourceWarning tests/run`: vedi task-4-suite-2.txt (3.11: 3726 OK, skip 7; 3.13: ultima riga sopra).
