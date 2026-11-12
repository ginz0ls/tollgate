# Ri-revisione 1 del giro di correzione della revisione finale B6

Diff `ab847d6..0e82c40` (commit `0e82c40`), letto sulle righe cambiate (`git diff -U0`). Sola lettura; nessun test rilanciato (suite del giro verde su 3.11 e 3.13, `exit 0`, controllata dal controller).

## Verdetti sui rilievi

**M1. Il divieto di `node`/`npm` non dice come si lanciano i test.** INDIRIZZATO. `agents/implementer-frontend.md:53` ora dice che i test si lanciano con `<programma> verify` (con `--related`, se configurato), anche quando sono comandi `npm`, e che li esegue tollgate. Motivazione corretta («il `dod` di `frontend` è vuoto, quindi il canale è `verify`») nella spec 6.3 (riga 492, «Costo del divieto di `node` e `npm`») e nel piano principale (sezione 9, voce del divieto, riga 248). Il test sui nomi vietati resta valido (cerca solo i nomi).

**M2. Il rimedio di `routes/` non vale con `backend` già dichiarato (P39).** INDIRIZZATO.
- Test: `tests/test_init.py` `test_real_precedence_p39` (diff @@ 1456): `DEFAULT_TOML` più `[profiles.backend] paths = ["src/routes/**"]`; asserisce `frontend == ["**/*.tsx"]`, `backend` invariato, nessuna riga «togli» per `src/routes/**`, e a runtime tutti e due i file a `backend`. Asserzioni con messaggio fisso, nessuna stampa dell'ambiente. Il test passa subito, come dichiarato: descrive un comportamento già vero.
- Spec 6.3: riga P39 nella tabella, dopo P38, con la voce «costo» e «vince backend» (corrisponde al messaggio di `bin/tollgate_flow/init.py:429`, `vince {…}`).
- «Prove di B6» (spec 16 / piano sezione 15): riga nuova (`piano:527`) e `p39` nell'elenco della riga «Progetto 13» (`piano:500`).
- «P1-P38» diventa «P1-P39» in spec 6.3 (riga 495), catalogo (`profili-verticali.md:173`), piano (`:8`, `:518`) e spec 33 (riga 2067).

**M3. «Ordine alfabetico» vale solo dentro una corsa.** INDIRIZZATO. Spec 6.3 riga 483 («Un file, un profilo verticale»): corsa unica alfabetica, `--update` in coda, vince l'ordine di aggiunta. Riga P37 (spec :535) e docstring di `test_real_precedence_p37` (`tests/test_init.py:1443-1444`) allineate. Punto 18 della pagina (vedi (b)).

**M4. «Le caricheranno».** INDIRIZZATO. `docs/uso/comandi.md:167` «Le caricano gli agenti dell'area `frontend`», come le righe 155, 159, 163.

**(a) Frase del rimedio di `routes/` in `docs/profili/frontend.md:67`.** INDIRIZZATA. Aggiunte: «Questo vale per una proposta nuova. Se il `tollgate.toml` ha già un blocco `backend` con la cartella `routes/` … `init --update` propone `frontend` ma non toglie la riga da `backend`: lo segnala con «vince backend», e la cartella si toglie a mano, come per il file senza import.» Coincide con la richiesta dell'utente, con il codice (`init.py:429`, `_drift` propone solo aggiunte) e con P39 e il suo test. Nessuna scelta o regola cambiata; la frase «Lo hai già deciso così … (costo accettato)» resta.

**(b) Punto 18 in `docs/profili/frontend.md:161`.** INDIRIZZATO. «A parità di percorso vince il primo blocco del `tollgate.toml`. In una prima proposta `init` scrive i blocchi in ordine alfabetico, quindi va a `backend`; con `--update` un profilo nuovo va in coda, quindi l'esito dipende dall'ordine in cui i blocchi sono stati aggiunti.» Coincide con la richiesta, con la spec 6.3 e con N13 della revisione. Il resto del punto (dentro `routes/`…) è invariato. La data dell'approvazione e `approved` non sono toccate; `skills/rules-frontend/SKILL.md` e `templates/` non compaiono nel diff (`git diff --stat -- skills templates` vuoto).

**Triage 12.** INDIRIZZATO: docstring di `tests/test_rules_frontend.py:409-411` ora dice che il ciclo vale quando il rapporto avrà righe `no` e che oggi contano i quattro `assertNotIn`; il codice del test non è cambiato.

**Triage 20.** INDIRIZZATO: virgola in `agents/final-reviewer.md:37` e `agents/finding-verifier.md:13` («`rules-infra`, le `R-BACKEND-…` che `rules-backend` e le `R-FRONTEND-…`»). Suite verde, quindi gli `assertIn` di `test_manifest.py` non fissavano la frase.

**Triage 24.** INDIRIZZATO: piano sezione 9 (`:207`, «Chiuso da B4 per `infra` e da B6 per `**/*.{tsx,jsx}` …») e riga B4 della tabella di contratto (`:53`): `**/*.<estensione>` ammessa da B6, le altre forme con `*` iniziale rifiutate, `database` a B7.

**Triage 25.** INDIRIZZATO: catalogo `profili-verticali.md:31`, parentesi «per le forme a cartella e a nome; la forma `ext` è l'eccezione: il percorso proposto è il pattern stesso».

**Triage 26.** INDIRIZZATO: spec 16 (riga 1877, «`tollgate plan-check` … non è un sottocomando (uscita 2, nessun effetto …)» e «il task 1 non prova il precaricamento») e piano `:529`; «Stato (11 novembre 2026)» a `piano:8`.

**Triage 27.** INDIRIZZATO: «Chiuso da B6 per `frontend`, resta B7 per `database`» (`piano:237`), «Chiuso da B6 nella copia … resta B7» (`:240`), «Chiuso da B6 (Task 2, decisione 16)» (`:241`), in testa alla voce.

**Triage 28.** INDIRIZZATO: `docs/verifiche/2026-11-10-b6-prova-flusso.md:68` «stream del passo 2, `passo2/tentativo-1/claude.jsonl`, riga 147».

## Danni nuovi nel diff della correzione

Nessun Critical/Important. Due Minor di coerenza, residui di numeri e frasi vecchi che il giro non ha toccato:
- Minor: `docs/profili/verifiche/frontend-fonti.md:91` dice ancora «casi P1-P38»; ora i casi sono P1-P39 (rapporto delle fonti, non nella lista dei file vietati; la riga è un riferimento, non un fatto sulle fonti).
- Minor: spec 6.3, riga 2067 (storico rev 33, voce D3): «`init` li scrive in ordine alfabetico» senza il limite della corsa unica. È la registrazione storica del ruling D3; le regole vere (riga 483, P37) sono corrette.

Nessun test indebolito (il test aggiunto è nuovo; i cambi a test esistenti sono solo docstring). Nessuna frase nuova contraddice il codice: «vince backend» è il testo vero di `init.py:429`. File approvati delle altre aree, `skills/rules-frontend/SKILL.md` e i frammenti: non toccati (l'elenco dei file del diff è di 11 file, nessuno vietato).

## Osservazioni fuori ambito

Nessuna.

## Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. M1, M2, M3, M4, le frasi (a) e (b) della pagina e le righe 12, 20, 24, 25, 26, 27, 28 del triage sono INDIRIZZATI. Due Minor facoltativi: «P1-P38» in `frontend-fonti.md:91` e la frase storica a spec riga 2067.
