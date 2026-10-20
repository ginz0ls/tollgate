# Ri-revisione giro 1 del Task 17 (313cdac..173949e)

### Verdetti sui rilievi

- **I1, rifiuto di finish in sessione non legata senza via d'uscita / «il caso non si pone»**: INDIRIZZATO.
  - `bin/tollgate_checks/acts.py` (rifiuto di `finish`): il testo ora dice «riprendi il lavoro con /tollgate:start #<N> (lega questa sessione) oppure apri Claude Code nel worktree del lavoro, poi digita di nuovo /tollgate:finish».
  - Test `tests/test_check_acts.py::test_unbound_finish_refusal_says_how_to_recover`: sessione "altra", cwd radice; controlla la frase originale, `/tollgate:start #<N>` e «worktree del lavoro». RED/GREEN nel report.
  - `skills/finish/SKILL.md` (riga aggiunta dopo l'atto): stessa via d'uscita, con «Ridigitarlo nella stessa sessione non cambia nulla» e fermarsi.
  - Verificato in `bin/tollgate_flow/start.py`: la ripresa (`_resume`, righe 119-229) esegue `phases.bind_session` e `sessions.mark_bound` (righe 200-202) nel percorso normale. Il legame manca solo nei percorsi con ritorno anticipato (PR già unita, `NEEDS_CONFIRM` senza `--confirm`, ripristino del worktree rifiutato): dopo `--confirm` si lega. Non è un difetto della correzione.
  - Rapporto D1: non dice più «il caso non si pone»; dice «Non esercitato in sessione interattiva», cita `session.py:21-22` e `start.py:200`, e la voce è anche tra i non esercitati.
- **M1, sessioni reali / catena `--continue` spezzata**: INDIRIZZATO. Rapporto D1: `f809819d` (passo 1, legata da `start`), `7e8ea5af` (passi 2-3-4a, mai legata), `36433509` (4b, legata da SessionStart). Confermato nei log `/tmp/tollgate-p3b/flow/logs/`: passo1 = f809819d; passo2, passo3 e passo4-a-radice = 7e8ea5af (compaiono anche id minori, 8dae51c6 e a16972e2, nel solo passo3 e passo4-a: non riguardano la tesi); passo4 = 36433509.
- **M2, successo composito di 4b**: INDIRIZZATO. Cella 4b della tabella marcata «riuscito, ma composito» con la spiegazione; tra i non esercitati c'è la catena atto, check, revisore e `open-pr` in una sola sessione legata.
- **M3, riproducibilità del tentativo a**: INDIRIZZATO. `spikes/run-p3b-flow.sh`: modo `passo4-radice` (`--continue`, dir = radice) e funzione `passo4_radice`, fuori da `tutto`; il rapporto lo dice e avverte che `tutto` da zero lancerebbe il revisore nella sessione legata. Non eseguito (dichiarato).
- **M4, lettura del sorgente nel passo 1**: INDIRIZZATO. Sezione «Limiti dell'isolamento e del piano», con i tre comandi e la conseguenza sulla prova della sola skill `start`. I tre comandi coincidono con quelli indicati dalla revisione originale.
- **M5, garanzia «nessuna rete»**: INDIRIZZATO. Stessa sezione: poggia su skill, hook e log, non su isolamento (`--allowedTools Bash` libero, `gh` vero nel PATH).

### Danni nuovi nel diff della correzione

Nessuno Critical o Important. Minor:
- `spikes/run-p3b-flow.sh`, riga finale `*) echo "uso: ..."`: l'elenco d'uso non cita `passo4-radice` (l'intestazione sì). Cosmetico.
- Il messaggio di rifiuto consiglia `/tollgate:start #<N>`, che nei casi di ritorno anticipato può chiedere `--confirm`: l'utente lo vedrà dall'output di `start`. Accettabile.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
