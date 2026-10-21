# Revisione Task 1 (835aa1c)

### Aderenza
- ✅ File creato (`docs/verifiche/2026-10-20-p3c-verifiche.md`), una riga per ognuna delle 8 voci della decisione 22, con versioni (claude 2.1.304, gh 2.46.0) e riga «verifiche nuove: nessuna; la prova reale del Task 14 è il controllo» (riga 7). Modello di forma P3b rispettato. Commit con il messaggio richiesto.
- ✅ Citazioni «Dove è provato» verificate con grep sui file del worktree: P0 E1 (`last_assistant_message: "due"` presente anche in `evidenze/hook/e1.jsonl`), E2 (riga 14, auto mode senza campo, `manual` con campo), E4, E5, E6 (`agent_type` `hookprobe:probe-agent` x2 in e5.jsonl, `hookprobe:probe-turns` x5 in e6.jsonl), I2, I3, «Fatto in più» (`agent_type: ""`, riga 39); P3a V1 (riga 11 e conseguenze riga 27); P3b prova-flusso «Passi ed esiti», riga 27 (`tollgate:final-reviewer`); P3b-verifiche G2-G5 e annotazione di versione (riga 15). Le sezioni «Hook (claude -p)» e «Interattivi» esistono (righe 7, 29). Nessuna citazione inventata. Versioni P0 2.1.294 corretta (p0-esiti riga 3).
- ✅ Onesto sui limiti: G4 «in parte», G5 formato non provato, versioni diverse tra le prove.
- ⚠️ Cautele rispettate (solo `--version`): non verificabile dal diff, il report lo dichiara.

### Punti di forza
Citazioni precise per file/sezione/id, limiti dichiarati (auto mode, G4), annotazione sulle versioni diverse, nessun fatto inventato.

### Rilievi
**Important**
- `docs/verifiche/2026-10-20-p3c-verifiche.md:16` (riga EnterWorktree): «Task 13 e Task 14: le skill del percorso L2 entrano nel worktree del lavoro». Il piano non lo dice: `EnterWorktree` non compare nel piano; Task 13 (righe 461-500) crea skill spec-audit/reopen e aggiorna approve/start/resolve ma non tocca il passo `EnterWorktree` (esiste già in `skills/start/SKILL.md:30`, `skills/adopt/SKILL.md:22`, `bin/tollgate_flow/adopt.py:360`); Task 14 (piano righe 514-523) parte con `cd` nel worktree, non con `EnterWorktree` (`claude -p`). L'unico punto in cui il fatto incide è `adopt` di L2 (Task 9, riga 378) se emette ancora quel passo. Correggere la colonna (Task 9/`adopt`, e dire che Task 14 non lo esercita) o scrivere «già usato, nessuna nuova dipendenza».
- Righe 12-13 (`UserPromptExpansion`/`command_args`): «Task 7 e Task 8: l'atto dell'utente si legge da `command_name` e `command_args`». Il piano non nomina `UserPromptExpansion`, `command_name` né `command_args`; Task 7 e 8 passano da `actapply` (`act apply`, già di P3b; decisione 20 riga 19 «già segnalato»). Il fatto incide in realtà sul meccanismo esistente e sulle skill `disable-model-invocation` (`skills/reopen/SKILL.md`, piano riga 485, Task 13). Riformulare: «meccanismo di P3b su cui poggiano `approve spec|plan` e `reopen` (Task 7, 8, 13)».
- Riga 11 (`agent_type`): «Task 6 e Task 13: l'hook riconosce gli agenti auditor da `agent_type` e ignora quelli con tipo vuoto». Task 6 (piano righe 280-290) riconosce l'agente da `row["type"] == audits.AGENTS[giro.kind]` (tabella `subagents`), non da `agent_type` del payload, e non menziona il tipo vuoto. Va scritto come lo usa il piano o attenuato («il tipo registrato da `SubagentStart` si confronta con `audits.AGENTS`; i `SubagentStop` interni con tipo vuoto non hanno riga e restano fuori»), altrimenti il rapporto attribuisce al piano una logica che non ha.

**Minor**
- Riga 10 (`SubagentHandback`): in primo piano il report è anche in `handbackReport` di `PostToolUse Agent` (correzione di P0 riga 14 e 108); il rapporto dice solo «fonte in auto mode», coerente ma incompleto rispetto alla correzione.
- Riga 7: la frase sui giri in sequenza ripete la decisione 22; accettabile, solo duplicazione.
- Il report dell'implementatore ammette di aver dedotto la colonna dai titoli dei task: confermato dal controllo, vedi sopra (3 voci su 8 non reggono; Task 5 e Task 6 per `SubagentStop`/`Handback`/`agente:` reggono: piano righe 43, 259).

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** le citazioni di prova sono tutte vere, ma la colonna «Dove incide in P3c» attribuisce al piano usi che non ha per `EnterWorktree`, `UserPromptExpansion` e `agent_type`; è una correzione di testo di tre celle.
