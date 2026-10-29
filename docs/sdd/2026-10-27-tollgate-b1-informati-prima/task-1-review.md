# Revisione Task 1, Step 1 (script, sonda e test di B1) — commit 67aad17

Revisione sul pacchetto `review-181a4a6..67aad17.diff`. Un controllo mirato fuori dal diff: `hooks/run` e `bin/tollgate_hooks/adapter.py:27-75`, per capire se il `PostToolUse` di Bash passa dal DB e se `cwd` viene dal payload (sì: `adapter.py:60`, `hooks/run:56-63`). Non ho lanciato test né `claude`.

### Aderenza (✅ / ❌; ⚠️ non verificabile)
- ✅ `sonda` (`run-b1-checks.sh:678-679`): `--plugin-dir`, `--model sonnet`, `--permission-mode acceptEdits`, `--allowedTools` con l'elenco esatto dello Step 1, più `--disallowedTools` (curl, wget, gh, git push), `--output-format json`, `timeout` (:762). `--allowedTools` è variadico, ma la sequenza `--disallowedTools … --output-format json <prompt>` mette un'opzione non variadica prima del prompt: il prompt non viene inghiottito.
- ✅ Rifiuti: cartella fuori da `/tmp/tollgate-b1/` (anche `..` e la radice stessa, :653-655, :748), `--plugin-dir` vuoto o inesistente (:676-681), `--redirect-url` mancante o non https (:746-747). I rifiuti avvengono prima di qualunque scrittura (il test lo asserisce, `test_b1_scripts.py:979-980`).
- ✅ Tentativi numerati (:752-754), repo di prova ricreato a ogni giro con `rot` (:755), niente cancellato; solo `rot` (rinomina) in tutto lo script.
- ✅ Plugin sonda: hook `PreToolUse`/`PostToolUse`/`PostToolUseFailure` con `.*`, `SubagentStart`/`SubagentStop` (`hooks.json`); `record.py` scrive solo lo stdin, mai l'ambiente, mai sotto la HOME, esce sempre 0. Agente con `tools` come da brief. Skill che lancia `probe:lettore` e porta il passo finale.
- ✅ Prompt (:659-670): ogni passo nominato per strumento, compreso `Read` di un file assente (aggiunta utile per B1-V1); la skill dice di dare i passi alla lettera al subagente e di fargli eseguire l'heredoc: le letture sono del subagente, non della sessione principale. ⚠️ Che il modello obbedisca lo dirà il primo giro (`riepilogo.txt` conta gli eventi con e senza `agent_id`).
- ✅ Heredoc B1-V5: delimitatore `<<'NOTA_DI_RICERCA_FINE'`, backtick, riga `EOF`, riga con `$HOME` e `$(echo no)`, `${CLAUDE_PLUGIN_ROOT}/bin/eco` tra virgolette (il percorso del worktree ha spazi); `eco` scrive byte per byte; `raccogli` confronta (integro / diverso / assente) e prende l'atteso dalla skill (fonte unica). Un test esegue il comando della skill con bash.
- ✅ `latenza`: sentinella in `state`, HOME temporanea, `python3 -B`, repo attivo con lavoro L1 e implementatore registrato da `hooks/run SubagentStart`, 50 + 50 misure (più una di riscaldamento non conteggiata, dichiarata), mediana e p95, B1-V3 a secco con `mcp__plugin_context7_context7__query-docs` e `agent_id`; uscita e risposta salvate. `cwd` viene dal payload, quindi il repo di prova viene davvero visto da `hooks/run`.
- ✅ `valida`: copia sotto `$TMP/valida`, skill `approved: prova`, solo `claude plugin validate --strict .`.
- ✅ `raccogli`: campioni con le chiavi dello Step 3, chiave senza campione assente, `env` scartato, `session_id`/`transcript_path` segnaposto, HOME sostituita; test `test_checks_raccogli_anonymizes` (e due altri) su un log finto.
- ✅ I cinque test nominati dal brief esistono; più `requires_redirect_url`, raccolta, plugin, latenza reale con `--runs 2`.
- Scostamenti dichiarati (`latenza.py`, `raccogli.py` in più; `B1_CHECK`/`B1_TMP` solo con `B1_CHECK=1`): ragionevoli, il secondo non riapre la porta (la variabile è ignorata senza `B1_CHECK=1`).

### Punti di forza
- Tutte le scritture del controller sono rinomine, mai cancellazioni; l'ordine dei controlli precede ogni effetto.
- Test che esercitano comportamento reale: `claude` finto che registra gli argomenti, heredoc eseguito da bash, anonimizzazione con HOME e `session_id` finti, `record.py` con un segreto nell'ambiente che non compare, `eco` che rifiuta la HOME, `latenza.py` eseguito davvero.
- La sonda non può cambiare l'esito degli eventi (sempre uscita 0, nessun output).

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. `run-b1-checks.sh:762` — la sessione `claude -p` eredita la configurazione vera dell'utente (altri plugin, hook, CLAUDE.md, e tollgate stesso se abilitato). Un `hooks/run` di tollgate nella sessione della sonda userebbe `~/.local/state/tollgate` (fuori dalla cautela «mai toccare»). Correzione a costo zero: nell'ambiente di `claude` esportare `TOLLGATE_STATE="$TMP/state-sonda"` con una sentinella `.tollgate-test` dentro, così l'hook vero, se c'è, lavora su uno stato temporaneo. ⚠️ Non verificabile se tollgate sia abilitato (non leggo `~/.claude/plugins`): il controller può controllarlo prima del lancio.
2. `raccogli.py:405-411` — con `--home ""` (HOME non impostata) `scrub_text` non sostituisce nulla e il comando va avanti. Meglio che `raccogli` rifiuti una HOME vuota, perché le evidenze si committano. Il test (`test_b1_scripts.py:1131-1133`) controlla la HOME e `PATH`; il controllo `"PATH"` è debole come prova dell'assenza dell'ambiente (lo garantisce davvero `record.py`, provato a parte).
3. `run-b1-checks.sh:653-655` — `sotto_tmp` confronta stringhe e non risolve i collegamenti simbolici: `/tmp/tollgate-b1/probe` come symlink verso la HOME passerebbe. Basta `realpath -m` prima del confronto. Rischio basso (la radice la crea lo script).
4. `raccogli.py:469` — `bash_cat` esclude `eco` con `"eco" not in command`: sottostringa fragile (per esempio `cat decode.py`). Meglio confrontare il percorso `bin/eco`.
5. `latenza.py:98` — il lavoro è creato con `phases.create_work` (libreria), non con il programma (`start`); la decisione del controller dice «col programma vero e gli hook». L'implementatore è registrato dall'hook vero, quindi la misura è valida; ma se `start` scrive campi che `create_work` non scrive, il repo di prova può divergere. Il Task 4 rimisurerà con `post_lookup` vero, quindi il rischio è contenuto.
6. `latenza.py:180-188` — non c'è prova che la serie Bash da subagente arrivi davvero in Python (il dry run riportato, 600 contro 485 ms, lo suggerisce). Un controllo a costo basso: dopo la serie, verificare nel DB di stato un effetto (per esempio il `touch` del lavoro) oppure che le due medie differiscano.
7. `agents/lettore.md:5` — `maxTurns: 30` per 10 passi + heredoc + eventuali tentativi è sufficiente; se uno strumento (WebFetch con redirect) consuma giri, il giro finale può saltare l'heredoc. Il primo tentativo lo mostrerà.
8. `raccogli.py:475-476` — `webfetch_redirect` vuole `url == redirect` esatto; se il modello normalizza l'URL (slash finale) il campione sparisce e `riepilogo.txt` lo segnala («senza campione»), senza falsi positivi. Accettabile.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni del controller rispettati sul diff, cautele e rifiuti verificati dai test; i rilievi sono rifiniture (il più utile: isolare `TOLLGATE_STATE` nell'ambiente della sonda e rifiutare una HOME vuota in `raccogli`). Restano ⚠️ che solo il primo giro vero può chiarire: obbedienza del modello al passaggio dei passi al subagente, e arrivo delle variabili `B1_PROBE_LOG`/`B1_ECO_OUT` agli hook (il ripiego sui percorsi di default c'è, :766-769).
