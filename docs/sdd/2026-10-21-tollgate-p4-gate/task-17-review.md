# Revisione del Task 17 (commit 17e8cc7, 463cc84, f981c97)

## Aderenza

- ✅ Step 1: `tests/test_criteria_p4.py` contiene `test_criterion_10_matrix` (25 sottoprove `case_01`..`case_25`, righe 309-525), `test_criterion_44_groups_end_to_end` (528), `test_criterion_35_gate` (553) e `test_components_in_gate` (563, criterio 18: `definition_of_done`, `base_test_ids`, `sentinel`, ognuno acceso e spento). Il programma è lanciato come processo (`ProgramCase.program`, riga 233) su `GateLab` con `gh` finto.
- ✅ Isolamento: `TOLLGATE_STATE` con sentinella (`TempState`), `TOLLGATE_GH` = `fakegh.py`, `HOME` temporanea (`tests/test_criteria_p4.py:234`). Nessuna rete, nessun `gh` vero, nessun percorso reale di `~/.claude` o `~/.local/state/tollgate`.
- ✅ Esecuzione mirata offline: `python3 -B -W error::ResourceWarning -m unittest tests.test_criteria_p4` dà 7 test OK in 42,8 s, senza avvisi.
- ✅ Step 2: tabella «Prove dei criteri di P4» (piano, sezione 4) con i criteri 10, 11, 18, 21, 22, 27, 29, 30, 32, 33, 34, 35, 36, 39, 41, 42, 44. Ho verificato con un controllo AST che tutti i 334 riferimenti `file::Classe.metodo` del piano esistono in `tests/`. Le sottoprove citate (09 e 20 per il 22; 21 per il 30; 19 per il 36) corrispondono ai casi del test. Le note «(P4)» delle tabelle P2, P3a, P3b e P3c sono annotate «chiuso in P4».
- ✅ Step 3 e carry: ogni voce di `task-17-carry-extract.md` è nella spec rev 25. Verificate nel testo e, dove dubbie, nel codice:
  - PATCH REST al posto di `gh pr edit` (spec 527, 1327, 1551; docstring `openpr.py:5` e `:259` allineate).
  - Ritentativi: letture GET 3 tentativi con 2 s e 4 s (spec 858; `ghcli.py:25,38`); scritture solo con `retry=True` (`gate/github.py:139,182`); `TOLLGATE_GH_RETRY_DELAYS` (spec 237).
  - `UNSTABLE` e non `CLEAN` con `attention` rosso (spec 905).
  - In `protected` `tollgate-base` non pubblica `tollgate/base` (spec 853).
  - `tollgate-base` in due job con permessi distinti (confronto con `gate/workflows/tollgate-base.yml:15-54`), `verdict` che non salva mai in cache (`tollgate-verdict.yml` ha solo `cache/restore`), `ACTIONS_RUNTIME_TOKEN` nel limite 1.2 (riga 98), percorso `base_ids` senza i segmenti maiuscoli (721), `profile:<p>:<c>`, `init --propose|--update`, sottocomandi `gate`, `creator.login` (`gate/github.py:143`, `sentinel.py:79`), esiti del Task 1 e 16 in 16, riga 25 in 20.
- ✅ Step 4: «Stato», sezione 2, sezione 3 con moduli reali e contratti P4 → P5. La riga «Minori rinviati» (piano riga 98) riporta tutte le righe «minor (deferred)» del ledger. Fa eccezione solo `progress.md:197` («`tollgate-base` ricalcola anche sul cache hit»), superata dal ruling di `progress.md:200` (il job `ids` calcola solo su miss, `tollgate-base.yml:35,38`): l'omissione è corretta.
- ✅ Ruling già presi rispettati: l'attesa di 10 s e il riferimento al registro in `.superpowers/sdd` non sono contati come difetti.
- ⚠️ Non verificabile offline: i fatti «su GitHub» citati nella matrice (PR #75, `mergeStateStatus` `BLOCKED`, casi dei rapporti del Task 16, `app_id` 15368). Sono rimandati ai rapporti in `docs/verifiche/`.
- ⚠️ La suite completa (2457 test, due versioni di Python) non è stata rilanciata, come da regole. Mi baso sull'evidenza del report.

## Punti di forza

- Le asserzioni dei test sono sullo stato pubblicato (`tollgate/verdict`, `attention`, `guard`, `sentinel`), sul testo della voce nel commento e sull'issue di `sentinel`. Nessun test senza asserzioni: anche i casi `error` controllano la descrizione (`DESC_ARTIFACTS`, «SHA superato»).
- Controprove presenti: caso 11 contro 12 (deroga di un'altra issue contro la propria), componenti accesi contro spenti, `sentinel` spento con `calls() == []`.
- `test_criterion_44` controlla anche l'ordine delle voci: la deroga `test` prima di `<details>`, la deroga `scope` dopo.
- La spec descrive il codice e non solo le decisioni originali (per esempio `base-publish`, `--service NOME=IMMAGINE[,PORTA]`), e dichiara i conflitti risolti in 9.2 con il costo (Dependabot sempre con `attenzione` rosso).

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor
1. `tests/test_criteria_p4.py:309-312`: la matrice è un solo test con 25 sottoprove. Un guasto di `setUp` o di un caso condiviso blocca la diagnosi di tutta la riga del criterio 10. Non è un difetto di correttezza (`subTest` riporta ogni caso), ma i nomi `case_NN` non compaiono nel nome del test. Rifinitura facoltativa.
2. `tests/test_criteria_p4.py:435-450`: `case_16` chiama `self.fresh()` cinque volte nello stesso test (un `GateLab` per ogni workflow). Costa tempo e il `GateLab` iniziale di `VerdictBase.setUp` resta inutilizzato in tutti i casi del modulo (riga 28 di `test_gate_github.py`). Rifinitura facoltativa.
3. Nessuna prova di mutazione sui test nuovi (lo dichiara il report). Sono test di criteri su codice già scritto: il RED del TDD manca, come per i Task 3 e 4 già nel ledger.
4. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:98`: la riga dei minori rinviati è un solo paragrafo molto lungo (lo segnala anche l'implementatore). Leggibile ma poco scorrevole. Dividerla in punti è una rifinitura per la revisione finale.

## Valutazione

**Qualità del task:** Approvato.

**Motivo:** Test dal programma vero, isolati e con asserzioni reali (7 test OK offline). La spec rev 25 riporta ogni voce del carry e non contraddice il codice nei punti controllati. Il piano ha matrice (334 riferimenti esistenti) e minori rinviati completi. Restano solo rilievi Minor.
