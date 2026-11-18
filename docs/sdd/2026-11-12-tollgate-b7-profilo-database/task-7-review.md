# Revisione Task 7 (bf7892d)

### Aderenza
- ✅ Caso `database`: `OUT` b7/flusso, progetto `spikes/b7/flow`, spec e piano in `spikes/b7/input`, `PLAN_REL`, `PROJ_FILES` completo (run-b1-flow.sh, blocco `if [ "$CASE" = database ]`).
- ✅ Sei passi e `libero` (`modo_passo3`..`modo_libero`, cartelle `libero-N` senza riuso dei numeri); `controlla` li stampa; `prepara` sposta (`rot`) `passo1..6` e `libero-*` (non i `.prev-*`).
- ✅ `registra` legge `passo3..6` e `libero-*` (salta `libero-*.prev-*`): `togli-pagine`, `comandi-modello`, `comandi-rischiosi`, precarico, trascrizioni lavorano sull'unico elenco `files`.
- ✅ `DISALLOWED`: psql, postgres, pg_ctl, pg_dump, prisma, drizzle-kit più supabase/deno/node/docker/npx..., nelle quattro forme; la regex `risky` usa lo stesso `DEPLOY_CLIS`. Solo il caso `database` aggiunge i sei nuovi programmi.
- ✅ Nessun `finish` prima di `passo6`: gli unici `/tollgate:finish` dei passi 1-5 sono in «Non lanciare /tollgate:finish» (passo5). `approve spec 1` e `approve plan` sono passi separati (passo2, passo4).
- ✅ `prepara` controlla spec (`pitch_problems`, una fetta) e piano con `level=$START_LEVEL` (L2); il rifiuto di un piano senza must-have è provato.
- ✅ Progetto di prova: nessuna credenziale, `verify` passa (almeno un test), `.gitignore` con le sei voci, titolo della skill in `flowreg.AREA_TITLES`.
- ✅ Piano, spec e issue non nominano `auth.uid`, indici, chiave esterna, migrazione nuova, annullamento, policy (test con elenco di termini vietati); la spec ha una sola fetta e due must-have con test.
- ✅ D8: `src_repo` copia `skills/rules-database` e ha `database_approved`; `test_real_flow_case_backend_proposal_has_database_block` dice che il blocco `database` compare e che `backend` non prende `supabase/`; il progetto di B5 non cambia. Decisione 17: tolto il confronto con `spikes/b1/flow` dal test frontend.
- ✅ Nessun nome utente, host o token nel diff (solo `/home/USER/` finto già presente).
- ⚠️ Prompt di `passo1`: la skill `start` non ha `$ARGUMENTS` letterale; Claude Code accoda il testo e il modello lo legge insieme a «#N [L1|L2] [--spec]». Spec e piano non contengono `--spec`, `#N`, `L1`, `L2`, quindi l'analisi degli argomenti non è confusa dal testo. Il resto («Non avviare il brainstorming...») è in conflitto solo debole con la skill (che manda al brainstorming «solo senza spec»): il rischio è reale ma è quello della decisione 16 e il controller lo vede solo dal vivo (il report lo dichiara). Dimensione del rischio: nessun fallimento di forma, solo di obbedienza.
- ⚠️ `/tollgate:approve spec $ISSUE` (prompt di passo1, riga «finché audit prepare non chiede») e `passo2`: il numero dopo `spec` è il numero di fette, non l'issue. Oggi coincidono (issue 1, una fetta) e la decisione 16 scrive «approve spec 1», ma `$ISSUE` è la variabile sbagliata (vedi M1).

### Punti di forza
- Le variabili `PROPOSE` e `SERVICES` tolgono le catene di `||` e lasciano invariato il comportamento dei casi ai, infra, backend, frontend (verificato: `ai` ha PROPOSE senza SERVICES, come prima).
- `passo_worktree` unifica i passi dal worktree senza duplicare il controllo del ramo.
- I test di `registra` usano flussi finti, con il percorso reale del fallimento (comando vietato in `passo5`, pagina lunga in `libero-1`): fallirebbero senza il ciclo esteso.
- `test_real_flow_case_database_prepara_checks_l2_plan` lavora su una copia (spikes/b7 in tmp) e non tocca i file veri.
- Il progetto di prova ha violazioni plausibili (`auth.uid()` nudo, nessun indice su `user_id`) senza che il piano le nomini.

### RED mancante: i test fallirebbero senza il codice?
Valutazione per lettura: sì per quasi tutti. `requires_real_rules`, `out_dir`, `unknown_value_names_database`, `registra_reads_every_step`, `rot_moves_every_step`, `has_six_steps`, `reads_database_title`, `flags_db_tools`, `disallows_db_tools`, `proposes_profile`, la `Ruling` del caso backend (senza `skills/rules-database` copiata non c'è il blocco) falliscono con lo script o i file precedenti. Eccezioni in M2.

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**
- M1. `spikes/run-b1-flow.sh` (prompt_database_passo1 e `modo_passo2`): `approve spec $ISSUE` usa l'issue al posto del numero di fette; `has_six_steps` non lo distingue (issue 1, fette 1). Scrivere `1` letterale o una variabile `SPEC_SLICES=1`, e far leggere al test le fette dalla spec.
- M2. `test_real_flow_case_database_prepara_checks_l2_plan` non distingue L1 da L2: `check_plan` dà lo stesso esito sul piano senza must-have per entrambi i livelli (provato con un controllo mirato in Python puro). Il test prova il rifiuto, non il livello; per il livello servirebbe un piano che differisce tra L1 e L2 (oggi `plan.py:199` tratta i due allo stesso modo): dichiararlo nel docstring o accettarlo.
- M3. `STEPS` (run-b1-flow.sh:132-133) è assegnata e mai usata: variabile morta, da togliere.
- M4. Nessun test dice che `registra` salta `libero-*.prev-*` né che `libero` salta i numeri già spostati (il codice lo fa, `case */libero-*.prev-*/*) continue` e `compgen -G`). Un caso con una cartella `libero-1.prev-*` bloccherebbe una regressione.
- M5. `tests/test_b1_scripts.py`: due righe vuote prima di «# ----- il caso `database`» dentro la classe (una sola).
- M6. Il report non dichiara che `FRONTEND_PROJECT` potrebbe restare senza uso dopo la rimozione del confronto (controllare con grep; non verificato qui).

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** i requisiti del brief, la D8 e le decisioni 16 e 17 sono rispettati; i test provano il comportamento e fallirebbero senza il codice. Restano solo rifiniture (M1 la più utile) e il rischio del prompt di `passo1`, che si vede solo dal vivo.
