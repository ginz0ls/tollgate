# Ri-revisione del giro di correzione 2 dopo la revisione finale di C2 (Fable, sola lettura)

**Rilievi ancora aperti sull'intero ramo dopo il giro: `critical` 0, `important` 0.** D1 e D2 della ri-revisione precedente sono chiusi; il giro non ha introdotto danni. F4 non è di questo giro (controller, dopo il merge).

Oggetto: commit `1517fd3` (genitore `c8b7640`), 2 file, 4 righe cambiate. Metodo: lette le regole, `final-fix-2.md`, D1 e D2 in `final-rereview.md`, le due mani del giro 2 in fondo a `final-fix-report.md`, e il diff `review-final-fix-2.diff` (una volta, con il confronto parola per parola delle quattro righe lunghe). Codice letto con `git show 1517fd3:<percorso>`. Prove solo su una copia `git archive 1517fd3` in `/tmp/tollgate-rev-*`, resa repo privato, con `HOME`, `TMPDIR` e `TOLLGATE_STATE` temporanei, cancellata alla fine. Nessun subagente, nessuna rete, nessun `claude`, suite completa non rilanciata, niente lanciato nel worktree.

Lanciati sulla copia: `python3 -B -m unittest tests.test_manifest tests.test_rules_database tests.test_docs` → `Ran 129 tests`, `OK`; una sonda di poche righe su `verify.gate_commands` e `verify.dod_commands` con il blocco della pagina (sotto).

## Verdetti sui rilievi

**D1 (Important). `docs/profili/database.md:109`, l'esempio `gate = ["db_test"]` faceva girare il test delle policy prima del reset** — INDIRIZZATO.
- `docs/profili/database.md:109` ora dice: «se vuoi un comando anche durante il task, aggiungi anche a `gate` i comandi, nello stesso ordine (per esempio `gate = ["db_reset", "db_test"]`); i comandi di `gate` girano anche nel controllo prima della pull request». È la formula decisa dal controller in `final-fix-2.md`.
- La frase è vera contro il codice. `bin/tollgate_core/runner.py:47-57` (`gate_commands`: il gate del progetto, poi i nomi di `gate` del profilo nell'ordine in cui sono scritti); `runner.py:60-69` (`dod_commands` salta i nomi già nel `gate`, riga 66); `bin/tollgate_core/verify.py:88` (`gate = gate_commands(cfg, files) + extra`) e `verify.py:142-145` (esecuzione nell'ordine della lista); `verify.py:33` (`run_verify` passa `extra=()`); `bin/tollgate_flow/finishcheck.py:118-121` (`finish check` passa i `dod` come `extra`).
- Sonda sulla copia, blocco della pagina (`dod = ["db_reset", "db_test"]`) e un file del profilo:
  - senza `gate`: `verify` → `verify`; `finish check` → `verify, db_reset, db_test`;
  - `gate = ["db_test"]` (l'esempio vecchio): `verify` → `verify, db_test`; `finish check` → `verify, db_test, db_reset` (il difetto di D1);
  - `gate = ["db_reset", "db_test"]` (l'esempio nuovo): `verify` → `verify, db_reset, db_test`; `finish check` → `verify, db_reset, db_test`. L'ordine è giusto in tutti e due i momenti e nessun comando gira due volte.
- Nella pagina approvata cambia solo quella frase: il diff ha una riga tolta e una aggiunta, e dentro la riga cambiano solo «aggiungilo» → «aggiungi», l'aggiunta «i comandi, nello stesso ordine» e l'esempio. «Approvata dall'utente il 2026-11-17.» (`:5`) e la nota di storia del 2026-11-24 (`:7`) sono intatte. `test_real_verify_channel_is_the_gate` resta verde.

**D2 (Minor). La spec diceva che `open-pr` esegue i comandi di `dod`** — INDIRIZZATO.
- Codice: `bin/tollgate_flow/finishcheck.py:118-121` è l'unica esecuzione (`verify.run_gate(..., extra=extra)`); `bin/tollgate_flow/openpr.py:326-331` usa `dod_commands` solo per i nomi richiesti e per `finishcheck.profile_receipts` (`finishcheck.py:179`) su HEAD, senza eseguire niente.
- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:507` (6.3): «i comandi di `dod` li esegue solo `finish check` (`finishcheck.py`, come `extra` di `verify.run_gate`), e `open-pr` ne ricontrolla le ricevute sul commit (`openpr.py`, `finishcheck.profile_receipts`)».
- `:1147` (8.7): «I comandi di `dod` girano solo a fine lavoro, con `finish check` (`open-pr` non li riesegue: ne ricontrolla le ricevute sul commit)».
- `:2348` (riga 37 della sezione 20): «non i comandi di `dod`, che girano solo con `finish check` (`open-pr` ne ricontrolla le ricevute)».
- Ricerca della formula vecchia su `1517fd3` nella spec del nucleo, nel catalogo (`2026-10-08-tollgate-profili-verticali.md`), nel piano principale, negli altri piani, in `docs/uso/`, `docs/profili/`, `agents/`, `skills/`: nessun altro punto dice che `open-pr` esegue i comandi di `dod`. Le altre frasi con «`finish check` e `open-pr`» (spec `:765`, `:1153`; piano principale `:350`, `:466`; piano di P4 `:43`) parlano di altro (sync, voce `approvals`, test, ricalcolo) e sono giuste.

### Controlli chiesti dal controller

- **File del commit.** Solo `docs/profili/database.md` (1 riga) e la spec del nucleo (3 righe): quelli attesi. Niente in `bin/`, `tests/`, `skills/`, `templates/`, `agents/`, `docs/uso/`.
- **Commit.** Nuovo, genitore `c8b7640` (nessun amend), oggetto «tollgate C2: correzioni dopo la ri-revisione finale», due righe `Co-Authored-By` (Opus 5.5 e Fable 5.2).
- **«unita su `main`».** Nessuna occorrenza nelle righe aggiunte.
- **Dati privati e modelli.** Nome utente, host e `/home/` nelle righe aggiunte: 0. L'unico «sonnet» è nella parte invariata della riga 37 («mai sonnet»).
- **Report.** Le due mani nominano i test e ne riportano l'esito; `suite-final-fix-2.log` ha `Ran 4520 tests` `OK` due volte e `exit 0`. Ciò che il report afferma sul diff corrisponde.

## Danni nuovi nel diff della correzione

Nessuno.

## Osservazioni fuori ambito

- Già nota dal giro precedente e invariata: `verify --related`, quando trova test correlati, non esegue il gate (`verify.py:135-139`), quindi nemmeno i comandi del `gate` del profilo. Da tenere presente per C3.

## Verdetto

D1 e D2 sono chiusi; la frase nuova della pagina di `database` è vera contro il codice e provata; la spec dice in ogni punto che i comandi di `dod` girano solo con `finish check` e che `open-pr` ne ricontrolla le ricevute. Nessun minore nuovo: la tabella di triage di `final-review.md` non cambia.

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
