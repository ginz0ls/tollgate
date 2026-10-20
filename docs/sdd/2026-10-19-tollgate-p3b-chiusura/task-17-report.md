# Report Task 17: prova reale del flusso finish -> open-pr

Status: DONE_WITH_CONCERNS (esito atteso ottenuto con ciclo `ok`; verificatore e needs_fix non esercitati).

File: `spikes/run-p3b-flow.sh`, `docs/verifiche/2026-10-19-p3b-prova-flusso.md` (rapporto completo con esiti per passo, eventi, token, difetti, non esercitato). Nessun codice di P3b modificato, nessun test aggiunto (nessun difetto di P3b trovato).

Esiti: passi 1, 3 riusciti; passo 2 non eseguito come scritto (piano già presente, come in P3a); passo 4a (cwd radice, `--continue`) non riuscito: atto non registrato perché la sessione di `claude -p` non è legata al lavoro (limite dell'impianto, come D3 di P3a); passo 4b (cwd = worktree, sessione nuova) riuscito fino a `finish open-pr`: PR #1 nel finto gh con `Closes #1` e blocco leggibile con `prblock.parse`, fase `pr_open`, ramo a `1fb3fe8` nel repo nudo = HEAD. Passo 5 non servito. Passo 6 eseguito.
Correzione solo dello script: dal passo 4 `claude -p` parte dal worktree del lavoro (la causa è dell'ambiente `-p`, non di P3b, quindi nessun commit-codice+test).
Veti 0, blocchi 0, needs_you 0, token 87076, costi totali circa 1,76 USD. Controllo del push verso il repo nudo mai scattato. `~/.local/state/tollgate` mai creato.
Non esercitati: finding-verifier, needs_fix e task di correzione, tetti, `--update`, sync, adopt, cleanup, abandon, L2.
Test: `tests/run` verde (python3.11 e python3, 1390 test), nessun `__pycache__`.

## Fix round 1

Cambiato: (I1) `bin/tollgate_checks/acts.py`: il rifiuto di `/tollgate:finish` in sessione non legata ora dice «riprendi il lavoro con /tollgate:start #<N> (lega questa sessione) oppure apri Claude Code nel worktree del lavoro, poi digita di nuovo /tollgate:finish» (verificato: `start.py:200` lega la sessione anche alla ripresa); `skills/finish/SKILL.md` dice lo stesso. Rapporto: D1 riscritto come «non esercitato in sessione interattiva» e vuoto di guida (ora chiuso). M1 sessioni reali (f809819d legata; 7e8ea5af mai legata nei passi 2-4a; 36433509 legata in 4b; catena `--continue` spezzata dopo il passo 1). M2 4b composito e catena in una sola sessione legata tra i non esercitati. M3 modo `passo4-radice` nello script (non in `tutto`, non eseguito). M4 lettura del sorgente nel passo 1. M5 «nessuna rete» poggia su skill, hook e log. Nessun `claude -p` rilanciato.
RED: `python3 -B -m unittest tests.test_check_acts` -> FAIL `test_unbound_finish_refusal_says_how_to_recover`: `'/tollgate:start #<N>' not found in …atto non registrato: /tollgate:finish vale solo in una sessione legata a un lavoro…`.
GREEN: stesso comando -> `Ran 22 tests … OK`. Completo: `tests/run` -> 1391 test OK (python3.11 e python3), nessun `__pycache__`.
