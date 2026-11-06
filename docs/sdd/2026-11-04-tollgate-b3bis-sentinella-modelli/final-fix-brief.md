# Giro di correzione finale del ramo B3-bis

Rilievi da `final-review.md` (leggilo: sezioni 2 e 3 hanno file, righe, scenari e correzioni proposte). Per ogni punto di **codice**: prima un test che fallisce (RED, comando e output), poi la correzione (GREEN). Per i punti di testo: la frase corretta, coerente con il codice.

## Codice
1. **(Important, rilievo 1)** `bin/tollgate_analysis/models.py` `gemini_family`: la modalità che segue un suffisso (`preview`, `exp`, `experimental`, `latest`) resta nella variante: `gemini-2.5-flash-preview-tts` → famiglia `flash-tts`, versione `(2, 5)`; si scartano solo i suffissi, i numeri di tre cifre e le date numeriche. Aggiorna l'attesa sbagliata di `tests/test_models.py:226` e aggiungi un test con il modello in uso `…-preview-tts` che non riceve «più nuovo» verso un `flash` normale. Controlla i casi esistenti (`gemini-2.5-flash-preview-09-2025` → `flash`, `gemini-3.7-flash-preview-tts` non stabile, `gemini-2.0-flash-001` → `flash`).
2. **(rilievo 2)** `bin/tollgate_flow/models_check.py:125`: a scadenza finita, un fornitore con una cache valida non si salta: la scadenza si controlla prima della `fetch`, non prima di `cached_pages`; con il tempo finito e una cache (fresca o scaduta) si usa la cache, con la riga di cache esistente (fresca: «elenco dalla cache del …», nascosta in `start`; scaduta: «rete non riuscita (tempo scaduto), elenco dalla cache del …»); senza cache resta «saltato, tempo del controllo finito». Il piano chiede che `test_deadline_skips_remaining_providers` resti valido senza cache.
3. **(rilievo 3)** `bin/tollgate_flow/modelsfetch.py:348`: se la rete risponde ma `validate` solleva `ModelsFormatError`, e c'è una cache che passa `validate`, si usa la cache con la riga «rete non riuscita (forma inattesa), elenco dalla cache del …»; la cache non si sovrascrive; senza cache resta «elenco non letto: forma inattesa».
4. **(rilievo 4)** `models_check`/`cli.py`: con almeno una chiave e nessun letterale dei file che corrisponde a un elenco letto, una riga generale `modelli: nessun nome di modello riconosciuto nei file dichiarati` (in `start` e in `models check`), così `models check` non stampa «nessun avviso» in quel caso. Rispetta l'ordine delle righe (generali in fondo) e il tetto.
5. **(rilievo 6)** `spikes/b1/flowreg.py:304` (`_hook_text`): un'uscita di hook il cui `additionalContext` comincia con `(tollgate:` è di tollgate (i messaggi d'errore del runner, `bin/tollgate_hooks/runner.py:309`, `:323`); test. Le evidenze ripulite non devono cambiare (il test esteso resta verde).
6. **(rilievo 8, triage 3)** `models.py:100`: `line` stringa vuota → nessuna famiglia (`… or None`); test.
7. **(triage 6)** `tests/test_models.py:343`: `assertRaises(dataclasses.FrozenInstanceError)`.
8. **(triage 10)** `tests/helpers.py` `no_network()`: blocca anche `socket.getaddrinfo` (finto che solleva `AssertionError("rete in un test")`), con un'asserzione in `test_no_network_helper`. Controlla che nessun test sotto `no_network()` risolva nomi per motivi legittimi (per esempio `git` in un processo figlio non è toccato dalla patch).

## Testi
9. **(rilievo 5, triage 12)** `docs/uso/comandi.md` e spec 11.4: il tetto di tempo è «20 s, più al più una risoluzione DNS e una lettura di 5 s».
10. **(rilievo 7)** `docs/uso/comandi.md`: «… e la riga lo dice, se nei file c'è un nome con la forma dei suoi modelli».
11. **(triage 22)** `docs/uso/comandi.md`: la copia del gate in `.github/tollgate/` ha il codice (si copia tutto `bin/`) ma non `templates/models.toml`: lanciato da lì il comando dà «controllo non riuscito (ProvidersError)»; si lancia dal plugin.
12. **(triage 23)** spec 11.4: con `--refresh` la cache non si usa se la rete risponde, ma resta il ripiego quando la rete fallisce (anche cache scaduta, con la sua data); non si chiedono i modelli `retired` (un `claude-…` assente dall'elenco ricade in «non è nell'elenco»); gli alias `~` di OpenRouter si leggono ma non hanno un controllo proprio. In più, nella spec, le righe nuove dei punti 2, 3 e 4 (forme della decisione 13 aggiornate) e la regola del punto 1.

Non toccare `skills/rules-base/SKILL.md`, `skills/rules-ai/SKILL.md`, `docs/profili/`. `tests/test_docs.py` deve restare verde (`test_limits_match_spec_1_2`).

## Verifica e commit
Test mirati mentre lavori; alla fine **una** corsa di `PYTHONWARNINGS=error::ResourceWarning tests/run` in background (uscita su `W/final-fix-suite.out`), controllata da te con un ciclo `until` limitato, restando attivo. Un commit per gruppo logico va bene (mai amend), ognuno con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Report in `W/final-fix-report.md`: per ogni punto cosa hai cambiato, test, RED e GREEN (comando e output), poi la suite.
