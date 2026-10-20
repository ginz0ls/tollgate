# Task 18 - Report dell'implementatore

Commit: `78705e2` tollgate P3b: prove dei criteri, spec rev 23, piano principale. Status: DONE.

## Cosa è stato fatto

1. `tests/test_criteria_p3b.py` (nuovo, 4 test, dal programma vero: `hooks/run` per gli eventi `UserPromptExpansion`, `PreToolUse Bash`, `SubagentStart`, `SubagentStop`; `bin/tollgate` per la CLI; `FlowLab` con `gh` finto e push verso il repo nudo locale):
   - `FinishToPrEndToEndTest.test_finish_to_pr_end_to_end` (criteri 9, 12, 40, 41): atto `finish` da `/tollgate:finish`, `finish check` (fase `review`, `finish_sha`), `review prepare` (lancio del revisore), verdetto con un rilievo valido e uno senza `rule` (scartato `rejected` prima del verificatore), `review prepare` (lancio del verificatore), esiti, ciclo `ok`, `review prepare` che indica `finish open-pr`, `open-pr` con il segnale scritto dal `PreToolUse Bash` vero (segnale consumato: `CliSessionError` alla seconda lettura con `argv`), PR nel finto `gh`, ramo sul repo nudo uguale a HEAD, fase `pr_open`, atto `consumed`, blocco 18.1 con `verdict.outcome == "ok"`, `issue`, `head_sha`, evento `pr_opened`.
   - `NeedsFixTest.test_needs_fix_then_from_findings_consumes_cycle` (26, 37): ciclo `needs_fix` con rilievo `major`, `counted = 1`, fase `execution`, `open-pr` rifiutato, `task start --from-findings 1` crea il task 2 `fix` (`source = cycle:1`), secondo lancio rifiutato (uscita 1), `counted` e `count` restano 1.
   - `SyncTest.test_sync_after_default_advanced` (16): predefinito avanzato su origin, atto `/tollgate:sync`, `sync`: base riallineata alla punta, HEAD riscritto e spinto, PR aggiornata (`head_sha` del blocco = nuovo HEAD), atto consumato, nessun ciclo in più (stesso patch-id), eventi `base_realigned` e `pr_updated`.
   - `AdoptTest.test_adopt_after_db_lost` (17): dopo la PR il DB viene spostato e ricreato vuoto; atto `/tollgate:adopt #7`, `adopt 7`: riga ricostruita (L1, `pr_open`, ramo, `pr_number` 1, worktree riusato), atto consumato, `prossimo passo: EnterWorktree`.
2. Buco trovato dalla matrice e chiuso nel modulo che possiede il codice: criterio 18, componente `final_review` a livello di hook. Test nuovo `tests/test_check_final_review.py::ComponentOffTest.test_final_review_component_off_ignores_verdict`.
3. Spec rev 23 (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`): intestazione, 3.1 (sottocomandi, segnale con `argv` consumato fail-closed, comandi negati ai subagenti, `abandon` senza lavoro), 6.4 (`finish check`, `review prepare`, `open-pr`, regola di scope in L2), 6.5 (`sync`, merge e chiusura), 8.4 (atti applicabili, `approve rounds` sui giri di correzione, `unverified-review`, `rebase`, `abandon`, `finish` in sessione non legata), 8.6 (`rules`/`blocking_rules`, scarto prima del verificatore, C8, riporti del verificatore, `needs_you` al secondo omesso), 8.7 (DoD: ultimo ciclo, `related`, `finish_report`, `review_unverified`), 10 (stadi, tetti, `superseded`), 11.4 (chiavi `rules`/`blocking_rules`, nomi dei profili, `[review] models`, tetto di `json_candidates`), 12.2 (colonne e migrazione 4), 12.4 (`adopt`, `cleanup`), 15 (criteri 40 e 41), 16 (G1-G5 e prova reale), 18.1 (contratto `prblock`, marcatore `<!-- tollgate-verdict` con SHA per P4), 18.4 (eventi), 18.5 (`"v": 1`), 20 (riga 23). Le righe delle revisioni precedenti non sono toccate.
4. Piano principale: spec rev 23; «Stato» (P3b chiuso sul ramo `p3b-chiusura`, merge in attesa dell'OK dell'utente, 1396 test); riga P3c con la seconda frase del 41; sezione 3 con moduli, interfacce, stato/DB, blocco JSON e `GATE_MARKER`, `finishcheck.check` come interfaccia che P4 sostituisce, vincoli per P3c e P4; tabella «Prove dei criteri di P3b» (criteri 1, 9, 12, 16, 17, 18, 26, 28, 31, 37, 38, 40, 41, 42, con «Resta a» per P3c e P4); riga del criterio 40 della tabella di P3a aggiornata con i test riscritti (C8). Ogni `file::Classe.metodo` citato nel piano esiste (verificato con uno script su tutte le tabelle).

## TDD / evidenza

- I 4 test di criteri e `ComponentOffTest` sono passati al primo lancio: la copertura dei Task 3-17 era già completa per questi criteri. Non c'è un RED da mostrare; i test asseriscono sullo stato reale (DB, finto `gh`, repo nudo, git), non su stringhe di uscita sole.
- Nel primo lancio di `-W error::ResourceWarning` il test `AdoptTest` lasciava una connessione non chiusa («unclosed database»): corretto assegnando la nuova connessione anche a `Lab.conn` (la chiude `Lab.close`). Poi 0 occorrenze.
- `python3 -B -m unittest tests.test_criteria_p3b`: 4 test OK (circa 17 s).
- `tests/run`: Python 3.11 e 3.13.5, 1396 test OK ciascuno. `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 1396 test OK, exit 0, nessun «unclosed database». Nessun `__pycache__`, `git status` pulito dopo il commit.

## Scostamenti dal piano

- Test 1: l'`open-pr` e gli altri comandi passano da un helper `cli()` che prima manda `PreToolUse Bash` a `hooks/run` (scrive il segnale) e poi lancia `bin/tollgate`, come fa il modello; il brief citava il segnale solo per `open-pr`.
- Il verdetto del test 1 ha un rilievo `minor` con `rule` (che il verificatore conferma) e uno senza `rule`, così il ciclo si chiude `ok` e il verificatore viene davvero lanciato.
- «Stato»: il registro dell'esecuzione è indicato come cartella `.superpowers/sdd/...` del worktree (fuori dal repo), perché `docs/sdd/2026-10-19-...` non esiste ancora: il controller può aggiornare il riferimento quando lo copia.
- La revisione finale del ramo non è citata nello «Stato» (non ancora fatta); le righe `minor (deferred)` non sono nel piano (carry).

## Dubbi

- Alcune frasi della rev 23 derivano dal ledger (decisioni e ruling) e non da una rilettura riga per riga del codice; ho verificato contro il codice le costanti, i codici d'uscita, le firme, gli eventi e i campi della migrazione 4. Da controllare in revisione: «finish check rifiuta in fase diversa da `execution` e `review`» (dedotto da `test_wrong_phase_refused`) e l'elenco dei campi di `*-approval.md` (preso dagli helper di `test_adopt.py`).
- I nomi dei campi JSON di `gh` (G4) restano non verificati: scritto in spec 16, nel piano (vincoli P4) e nel rapporto delle verifiche.

## Fix round 1

Cambiati solo testi (nessun codice):
1. Piano principale, «Stato»: registro indicato come `docs/sdd/2026-10-19-tollgate-p3b-chiusura/`; aggiunto «(revisione finale del ramo in corso)» dopo «P3b chiuso ... sul ramo `p3b-chiusura`» (punto 5).
2. Spec 6.5, «Dettagli di `sync`», riletti su `sync.py`: fasi `execution` e `pr_open`, e `review` se la PR esiste già (`sync.py` controllo di fase); un commit remoto che sia un nostro push poi riscritto (eventi `commit`, `_remote_conflict`) o già antenato di HEAD non è divergenza.
3. Spec 11.4: giri di correzione dal quarto in poi (fino a 8 con `approve rounds`) restano `inherit`.
4. Spec 12.4: aggiunta la fase `plan` per L2 con spec approvata e senza piano valido (`adopt._phase`).
Esito: `tests/run` Python 3.11.16 e 3.13.5, 1396 test OK ciascuno; `-W error::ResourceWarning` 1396 OK, nessun «unclosed database»; nessun `__pycache__`.
