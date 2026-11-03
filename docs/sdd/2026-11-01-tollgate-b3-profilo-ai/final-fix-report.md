# Report del giro di correzione finale (b3-profilo-ai)

Commit: `dd7dc82` (I-1, M-7) e `dd0132d` (M-2, M-3, M-5, M-6, minori del piano).

## I-1 (evidenze)
- `spikes/b1/flowreg.py`: nuovo comando `togli-pagine` (unico che scrive), costanti `WEB_TOOLS`, `MAX_WEB_RESULT = 5000`; sostituisce i risultati lunghi di WebFetch/WebSearch con `[pagina di terzi tolta dalle evidenze: <URL>, <N> caratteri]`, sia nel messaggio sia in `tool_use_result`. `spikes/run-b1-flow.sh registra` lo lancia sui flussi prima di `comandi`.
- Evidenze: 4 risultati sostituiti (1 nel passo 1, 3 nel passo 2); diff di 2 e 6 righe; nessun altro risultato lungo in `docs/verifiche/evidenze/` (scansione di tutti i `.jsonl`). `grep -rI` di nome utente, host e forme di token su `evidenze/b3/`: zero.
- RED: `test_committed_evidence_has_no_long_web_results` falliva su 4 punti (22.794 x3, 14.616); GREEN dopo `togli-pagine`. Test nuovi: `test_flowreg_togli_pagine_replaces_long_web_results`, `..._keeps_short_results_and_is_idempotent`, `test_flow_registra_strips_third_party_pages_from_the_streams`.
- Scostamento dal brief: tetto 5.000 e non 2.000 caratteri, perché evidenze vecchie di B1 e B2 hanno risultati di WebFetch da 2.400 e 2.200 caratteri (riassunti di documentazione Python, licenza permissiva) che altrimenti sarebbero da riscrivere.
- Rapporto della prova: riga nell'anonimizzazione (la riga sui "tre segnaposto" è riscritta: sono usciti con le pagine, ne resta uno in un messaggio di testo del passo 1).
- **Restano nella storia**: il commit `f8f5331` contiene ancora le pagine. Un commit nuovo non le toglie dalla storia. Riscrivere la storia è una scelta dell'utente (rebase/filter-branch vietati a me): da chiedere prima della prima spinta.

## M-7
Riga nel rapporto: `reviewer-ai` ha usato `WebFetch` dal vivo (verificato nello stream del passo 2: il WebFetch alla riga 250 ha come `parent_tool_use_id` il lancio `Revisione task 1`). Non ho toccato la riga della prova in spec 16 (il brief chiedeva solo il rapporto).

## M-5
- `docs/profili/ai.md`: «le altre si rinumerano» -> numero non riusato, le altre tengono il loro; sezione «Quando si accende»: `--propose` per un progetto nuovo, `--update` per uno che ha già tollgate; punto 4 di «Cosa hai deciso» riscritto (marcatore rimesso per decisione del 2026-11-02), tolta «coprono quasi tutti i casi».
- `templates/profiles/ai.toml`: rimesso `from "openai"`.
- `docs/profili/verifiche/ai-fonti.md`: riga del marcatore con esito `ok` per decisione dell'utente; voce «Regole tolte» e intestazione aggiornate.
- Nessun test da cambiare: `test_detect_markers_verified`, `test_real_markers_not_in_tollgate_bin` e gli altri sono verdi.

## M-6
`agents/implementer-ai.md`: «ciò che serve».

## M-2 / M-3
- `tests/test_manifest.py`: il test di deriva confronta l'insieme delle chiavi del frontmatter. RED: con `effort:` aggiunto temporaneamente al generico il test fallisce; GREEN senza (file ripristinato).
- `bin/tollgate_core/fragments.py`: i tipi del `[profile]` passano da `config._set_key`; un errore dà `FragmentError` con il nome del file. Test `test_load_rejects_wrong_value_types` (`paths = "x"`, `min_level = 1`, `skills = [1]`, `min_level = "L9"`, `agent = 3`). RED: 3 sottocasi su 5 non sollevavano (gli altri già rifiutati).

## Piano principale
- Conteggi ricontati sulle tabelle: 48 righe di regole (45 `ok`, una con riserva; 3 `no`), 20 righe di marcatori tutte `ok` (due con riserva, una per decisione dell'utente).
- `test_page_lists_every_rule` attribuito a `test_rules_ai.py`.
- Blocco «A B4-B7»: tre bullet nuovi (test esistenti sulla radice vera, M-1 cartelle `agents/` e `prompts/`, deriva e tipi dei frammenti).

## Verifiche
- Mirati con python3.11 e python3: `test_rules_ai test_fragments test_manifest test_b1_scripts test_init`: 273 test OK (2 saltati dichiarati) su entrambi.
- `claude plugin validate --strict .`: uscita 0.
- Suite completa con `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3392 test OK (4 saltati), python3.13 3392 test OK (2 saltati), uscita 0 (`final-fix-suite.out`).
- `approved` e testo/numeri delle regole non toccati.

## Fix round 2 (skill di terzi nelle evidenze)
- `flowreg.py togli-pagine` sostituisce ora anche i blocchi di testo `Base directory for this skill: <percorso>` oltre 5.000 caratteri quando il percorso non contiene `tollgate` (`external_skill`), con `[skill di terzi tolta dalle evidenze: <nome>, <N> caratteri]`. `registra` lo applica già (stesso comando).
- Evidenze b3: tolti `claude.jsonl:96` (claude-api, ~110 mila) e `:67` (skill `writing-plans` di superpowers, ~10 mila: è esterna anch'essa, quindi sostituita; la riga del rapporto che diceva che restava è riscritta). Le skill di tollgate (passo 2, riga 33) restano. B1, B2, gh-p4 non toccati.
- Nota: la riga `:139` indicata dalla ri-revisione non è una skill: è il risultato di una lettura di un file di test del progetto di prova (codice, non testo di terzi); resta.
- RED: il test delle evidenze fallito su `:67` e `:96` prima della pulizia; GREEN dopo. Test nuovi: `..._replaces_external_skills_but_keeps_tollgate_ones` (idempotente), `test_flow_registra_strips_external_skills_from_the_streams`. Il controllo sulle skill nel test delle evidenze vale solo per `evidenze/b3/`.
- `grep -rI` nome utente, host, token su `evidenze/b3/`: zero. `tests.test_b1_scripts`: 61 OK con python3.11 e python3.
