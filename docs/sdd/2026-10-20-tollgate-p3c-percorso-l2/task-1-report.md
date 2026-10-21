# Report Task 1

Creato `docs/verifiche/2026-10-20-p3c-verifiche.md` secondo il modello di `2026-10-19-p3b-verifiche.md`: versioni (claude 2.1.304, gh 2.46.0), tabella `Fatto | Dove è provato | Dove incide in P3c` per le 8 voci della decisione 22, riga «verifiche nuove: nessuna; la prova reale del Task 14 è il controllo».

Prove trovate per tutte le voci (P0 E1/E2/E4/E5/E6/I2/I3, P3a V1, P3b prova-flusso e G2-G5); nessun fatto «non trovato».
Comandi eseguiti: solo `claude --version`, `gh --version`. TDD non applicabile (solo documento).
Scostamenti: la colonna «Dove incide» indica i Task del piano secondo la mia lettura dei titoli (Task 5, 6, 7, 8, 13, 14), non verificata riga per riga sul testo dei task; da controllare in revisione. `tests/run`: 1417 test OK con python3.11 e con python3 (3.13.5).

## Fix round 1
Corrette le celle «Dove incide in P3c» di `docs/verifiche/2026-10-20-p3c-verifiche.md` leggendo il piano: `EnterWorktree` (nessuna nuova dipendenza; già in `skills/start/SKILL.md:30`, `skills/adopt/SKILL.md:22`, `bin/tollgate_flow/adopt.py:360`; Task 14 usa `cd`), `UserPromptExpansion`/`command_args` (meccanismo di P3b via `act apply`, Task 7 e 8; skill `reopen`, Task 13), `agent_type` (Task 6 usa `subagents.type` contro `audits.AGENTS`; i tipi vuoti non hanno riga), `SubagentHandback` (aggiunto `handbackReport`, correzione K3 di P0).
Test: `tests/run` -> 1444 test OK con python3.11 e python3 (3.13.5).
