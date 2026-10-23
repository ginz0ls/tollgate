## Copertura: criteri, vincoli e rinviati → task

| Voce | Task |
|---|---|
| Criterio 10 Gate su GitHub (tutte le righe; stato del token personale in `protected`) | 4, 5, 7, 8, 9, 10, 16, 17 |
| Criterio 11 Protezione e modalità | 12, 16 |
| Criterio 18 Componenti: `definition_of_done` nel gate, `base_test_ids`, `sentinel` | 4, 5, 9, 10, 17 |
| Criterio 21 Deroga per pattern in `attenzione` | 4 |
| Criterio 22 Livello sotto il minimo nel gate (`verdict` rosso, con tetto `attenzione`) | 5, 13 |
| Criterio 27 Neutralizzazione | 6 |
| Criterio 29 `gate` del profilo eseguito nel gate | 4, 7, 16 |
| Criterio 30 `allow_no_tests` con zero test: verde con `attenzione` rosso | 4, 16 |
| Criterio 32 `skipped` nel JUnit della testa | 4 |
| Criterio 33 Issue e deroghe nel gate | 5, 16 |
| Criterio 34 `init` senza amministrazione; primo push con `tollgate-sentinel` | 10, 12, 16 |
| Criterio 35 Componenti spenti nel gate | 5, 17 |
| Criterio 36 Piano registrato nel gate | 4, 16 |
| Criterio 39 `attenzione` per `size_reason` | 5, 13 |
| Criterio 41 DoD nel gate | 5, 13 |
| Criterio 42 Must-have ricalcolati dal JUnit nel gate | 4 |
| Criterio 44 `attenzione` a due gruppi | 4, 6, 17 |
| Gate installato: `prereq.GATE_FILES`, `VERSION`, `gh.REQUIRED_CONTEXTS` (P3a) | 11, 12 |
| P3a riga 56: `sentinel_issues` con `--limit 100` | 10 |
| Blocco 18.1 letto con `prblock.parse` (ultimo blocco); marcatore `<!-- tollgate-verdict` con lo SHA (P3b) | 5, 6, 13 |
| `finishcheck.check` sostituita dietro la stessa interfaccia; rischio 2; «P4 → P3: `gate run` locale» | 13 |
| Vincoli per P4 di P3b (1) scope L2, (2) SHA nel marcatore, (3) DoD dei rilievi sull'ultimo ciclo, (4) voci ricalcolate e dichiarate, bloccante con `review_unverified`, (5) campi di `gh`, (6) `rules`/`blocking_rules` | (1) 2, 4; (2) 6, 13; (3) 5; (4) 5; (5) 1; (6) 5, 13 (campo `blocking`) |
| Contratti verso il gate di P3c (1) `check_l2`, (2) `locate_spec_approval`, (3) intestazioni, (4) `spec_reviews_dir`, `plan_reviews_dir`, `spec_audit`, (5) `suspended`/`off` in `attenzione`, (6) `reviews/<N>/` esenti | 3, 5 |
| Vincoli per P4 di P3c (1) report non legati allo `spec_sha`, (2) `check_l2` e piano superato, `path`, `slices`, (3) `lens: suspended` ambiguo, (4) `PATH` del tool Bash, (5) parti non esercitate dalla prova di P3c, (6) rinviati dei task | (1) 3; (2) 3; (3) dichiarato (decisione 10); (4) 16; (5) `/tollgate:finish` e la PR con il modello nel 16 (in L1); audit a lenti, `reopen`, `--spec`, tetti, più fette con il modello → **P5** (eval), perché i test dal programma vero li coprono e una prova con il modello costa più di 500k token; (6) righe sotto |
| Caso (a) propria superata contro altra corrente | 3, 14 |
| Caso (b) `approval` con `plan_adversary` spento e spec cambiata | 14 |
| Caso (c) m-2, m-3, m-4 | 14 (m-2, m-4); m-3 dichiarato in 12.4 (17) |
| Caso (d) report della spec legati allo `spec_sha` | 3 |
| P3b righe 4, 47, 68, 69 | 1, 6, 13, 13 |
| P3c righe 2, 3, 4, 7 | 3 |
| P3c righe 16, 19, 22, 29, 34, 39 | 14 (16, 19, 22, 29, 34); 16 (39) |
| P3c riga 11 (`v` nella riga dei giri) | **P5**: serve solo quando esisterà una versione 2 della riga |
| P3c riga 12 (`close_round` non valida `outcome` e `counts`) | **P5**: un solo chiamante, che passa valori calcolati |
| P3c riga 20 (dopo «report non scritto» solo il veto) | **P5**: il giro resta aperto e `audit prepare` lo ristampa, nessun lavoro fermo |
| P3c righe 13, 15, 24-28, 36; duplicazione «base o predefinito più `load_config`» | **P5**: posizione di test, refactoring e testo senza guasti |
| Vincolo P3c (6): `ls_files_at` con riferimento `-…`; backtick nei percorsi del brief | 2; 14 |
| Fatti di GitHub nuovi (V1-V9) | 1 |
| Spec 9.1-9.6, 11.2, 13 (righe del gate), 14 (riga «Gate»), 18.1 | 4-12, 16 (9.6: avviso di Actions spente in `start`, 12) |
| Revisione finale di P3c, «Considerati e messi da parte»: approvazioni falsificabili con comandi git, `bash_rules` senza `locked_docs` | Il gate li ricontrolla (decisioni 9 e 10, Task 5); per i guardrail locali restano un limite dichiarato di 1.2 (rev 25, Task 17) |
| Revisione del piano P4 (C-1, C-2, I-1…I-12, M-1…M-15) | decisioni 1, 5, 7, 9, 10, 12-19, 21, 25, 26; Task 1, 2, 3, 7-13, 16 |
| Review Focus 1-9 | 13, 5 e 13, 13, 10, 9, 11, 9, 3 e 14, 9 |
| Regole degli strati in `test_layers.py` | 2 |
