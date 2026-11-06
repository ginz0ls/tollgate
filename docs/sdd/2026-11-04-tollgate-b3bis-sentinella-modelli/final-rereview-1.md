# Ri-revisione 1 del giro di correzione finale B3-bis (f202c8c..5102f0f)

### Verdetti sui rilievi
1. **Gemini, modalità dopo un suffisso** — INDIRIZZATO. `models.py:63-80`: restano le parole dopo il suffisso, si scartano suffissi e pezzi numerici seguenti. Sonda `python3 -B`: `2.5-flash-preview-tts`→`flash-tts`; `3.7-flash-preview-tts`→`flash-tts` (resta non stabile, `_gemini_stable`); `2.5-flash-preview-09-2025`→`flash`; `2.0-flash-001`→`flash`; `3.8-flash-tts`→`flash-tts`; `flash-latest`, `embedding-001`, `embedding-exp-03-07`→`None`. Test in `test_models.py` (attesa 226 corretta, test del modello in uso).
2. **Scadenza finita con cache** — INDIRIZZATO. `modelsfetch.py:~342-365`: la scadenza si controlla dopo la cache e prima della `fetch` (nessuna rete oltre la scadenza); cache fresca senza refresh resta il primo ramo; scaduta/refresh → «rete non riuscita (tempo scaduto), elenco dalla cache del …»; senza cache `DeadlineSkipped(FetchError)` → `models_check.py:80` «saltato, tempo del controllo finito» (catturata prima di `FetchError`). Tolto il salto in `_check`; test dichiarati.
3. **Forma inattesa con cache** — INDIRIZZATO. `modelsfetch.py`: `validate` sulle pagine di rete prima di ogni scrittura; con cache valida → riga «forma inattesa» e nessuna scrittura; senza cache `ModelsFormatError` esce come prima («elenco non letto: forma inattesa»).
4. **Riga «nessun nome riconosciuto»** — INDIRIZZATO. `models_check.py:140-143`: con almeno una chiave, `recognized` tutti falsi (o nessun letterale ma file letti) → `NO_NAMES` in `general`, quindi in fondo e dentro il tetto di 12; non compare con elenchi tutti falliti (`recognized` vuoto) né senza chiavi (resta la riga delle chiavi). `cli.py` non serve: «nessun avviso» solo a lista vuota.
5. **`_hook_text` e messaggi del runner** — INDIRIZZATO. `flowreg.py:304` riconosce `(tollgate:`; test esteso; nessun file di evidenza nel diff, quindi le evidenze ripulite sono invariate.
6. **`line` vuota → nessuna famiglia** — INDIRIZZATO. `models.py:103` `… or None`; test dedicato.
7. **`assertRaises(FrozenInstanceError)`** — INDIRIZZATO (diff `tests/test_models.py`, import `dataclasses`).
8. **`no_network()` blocca `getaddrinfo`** — INDIRIZZATO. `tests/helpers.py:44-51`; il finto solleva solo `AssertionError("rete in un test")`; i processi figli non sono toccati; il report dichiara suite verde (3572 OK, due interpreti).
9. **Tetto «20 s, più al più una risoluzione DNS e una lettura di 5 s»** — INDIRIZZATO in `comandi.md` e spec 11.4 (client stretto).
10. **Riga «lo dice se nei file c'è un nome con la forma dei suoi modelli»** — INDIRIZZATO in `comandi.md`, coerente con `_wanted` e `NO_NAMES`.
11. **Copia del gate senza `templates/models.toml`** — INDIRIZZATO in `comandi.md` (testo con «ProvidersError»).
12. **Spec 11.4: `--refresh`, retired, alias `~`, righe nuove, regola Gemini** — INDIRIZZATO. Presenti: ripiego con cache anche scaduta, `retired` non chiesti e `claude-…` assente → «non è nell'elenco», alias `~` senza controllo proprio, regola Gemini, righe dei punti 2-4 nelle forme. Nota: la frase su `--refresh` («la cache non si usa se la rete risponde») non l'ho riletta riga per riga nella spec oltre l'estratto del diff; il codice la rispetta (`cached is not None and not refresh`).

### Danni nuovi nel diff della correzione
Nessuno. Verificato: nessuna chiave né ambiente nelle righe, nella cache o nei messaggi dei test (il finto di rete e `DeadlineSkipped` portano testi fissi); nessun «più nuovo» verso modelli non stabili o di altra modalità (confronto su variante+`stable` invariato, ora la modalità è nella variante); la cache non si riscrive con forma sbagliata; nessuna rete oltre la scadenza; la nuova riga sta nell'ordine e nel tetto; `getaddrinfo` bloccato non ha rotto test (suite dichiarata verde).

### Osservazioni fuori ambito
Nessuna. (Non ho rilanciato la suite: mi fido dell'uscita dichiarata in `final-fix-suite.out`, non riletta.)

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
