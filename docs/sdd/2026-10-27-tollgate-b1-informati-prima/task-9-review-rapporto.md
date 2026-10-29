# Revisione del rapporto della prova reale, Task 9 di B1

Oggetto: `docs/verifiche/2026-10-27-b1-prova-flusso.md` contro `docs/verifiche/evidenze/b1/flusso/`. Sola lettura: nessuno script lanciato, nessun `claude`. Ho letto anche i grezzi in `/tmp/tollgate-b1/evidenze-grezze/` solo per contare le righe tolte dall'anonimizzazione.

### Aderenza

- ✅ Numeri e orari dei passi: passo1 07:27:11-07:28:16 = 65 s, passo2 07:29:19-07:30:40 = 81 s (`esito.txt`); uscite 0 (`exit-codes.txt`).
- ✅ Costi: `total_cost_usd` 0,40977 (passo1) e 0,49647 (passo2), somma 0,906 = 0,91. `modelUsage` ha `claude-sonnet-5-5` e `claude-haiku-5-5`.
- ✅ Token: `stats.json` 46.532 + 27.783 = 74.315.
- ✅ Versione `2.1.312` (`versione-claude.txt`).
- ✅ Sequenza passo1: `start`, `EnterWorktree`, `writing-plans`, `WebFetch`, heredoc Bash con `veto` `coordinator` (seq 2, testo identico), `Write`, commit `c568a8b`. Il piano ha un task, `src/config.py` con `app_name` e cinque test.
- ✅ Sequenza passo2: `Read` del brief, `cat` con glob, `WebFetch`, prima consegna (seq 10, `ok:false`, due problemi con il testo citato), tre `Read`, seconda consegna (seq 11, `ok:true`, 6 s dopo), poi i due `Write` (prima `tests/test_config.py`, poi `src/config.py`). Nessuna modifica di codice prima della nota valida.
- ✅ Letture (`lookups.txt`): 4 `read`, 1 `bash_read` (`config.toml`), 1 `fetch`, tutte con `agent_id` `a36b98ad8d214c293`. Il glob di `cat` non si espande: `bash.read_targets` ritorna `tests/*.py` e `observed_bash` (`bin/tollgate_core/lookups.py:94-103`) conta solo i file che esistono (`must_exist=True`).
- ✅ Nota: `research-1.md` coincide con la citazione del rapporto. Vale anche per il brief del revisore (recinto e avvertenza, righe 8-24 del `Read`).
- ✅ Revisore: `approved`, un solo `minor` su `src/config.py:8` (docstring lunga), nessun rilievo `nota di ricerca`. Suite: 6 test OK, `verify: uncounted (uscita 0)`.
- ✅ Esito non composito: un solo tentativo per passo, nessuna cartella `.prev` di tentativi nelle evidenze, `exit-codes.txt` lo conferma. `state.prev-…` in `/tmp` è del Task 1. Il cambio del prompt di `passo2` (`2765018`, 07:29:13) è precedente al lancio (07:29:19) e a nessun tentativo consumato, quindi la definizione del brief («più tentativi») non scatta.
- ✅ Anonimizzazione: nessun `/home/crucco`, nessuna email non `noreply`, nessun token o segreto. Gli unici `secret` e `token` trovati sono la voce `gh secret` di `--disallowedTools` e il testo del skill `execute`. Nessun messaggio `init` (nei grezzi ce n'era uno per passo). Righe tolte: 175→162 e 324→311 = 26, come dice il rapporto; nei grezzi 12 hook `SessionStart` e 2 `init`. Restano solo hook `UserPromptSubmit`/`Stop`/`PreToolUse`/ecc. con output vuoto o `{}`.
- ✅ Step 3, contenuto richiesto: passi, tentativi, letture, nota, avvisi e rifiuti, verdetto, token, consumo, difetti, limite della decisione 18 (testo conforme a `decisions.md:26`).
- ⚠️ Non verificabile: «plan-check del piano di prova ok» e il tetto 2400 s (rilievi 1 e 6).

### Punti di forza

- Il rapporto separa bene cosa è registrato (`lookups`) e cosa no (Grep, glob), e spiega il rifiuto della prima nota con il dato giusto e i 6 s del giro.
- Dichiara il piano scritto da `start` e non quello di prova, e il motivo della modifica del prompt di `passo2`.
- I limiti sono onesti (divieti a prefisso, modello cooperativo, un solo lavoro piccolo).
- Tabella dell'atteso del brief completa e corretta.

### Rilievi

#### Critical
Nessuno.

#### Important

1. **Riga `prepara` del rapporto senza evidenza.** La tabella dei passi dice «copia del plugin, progetto, `plan-check` del piano di prova ok», ma in `evidenze/b1/flusso/` non c'è nessuna uscita di `prepara` (nessun log, nessun esito del `plan-check`; ci sono solo `validate/`, `passo1/`, `passo2/`, `registro-1/`). Neppure il fatto che `skills/rules-base/SKILL.md` sia nella copia è documentato nelle evidenze (il rapporto lo afferma e basta). Il brief chiede «uscite in `docs/verifiche/evidenze/b1/flusso/` … con l'esito di ogni tentativo». Correzione: salvare l'uscita di `prepara` (anonimizzata) e il `ls` della copia, oppure togliere l'affermazione.

2. **Il passo 2 non ha provato quello per cui era stato scritto, e il rapporto non lo dice in modo esplicito.** Il Task 9 Step 1 giustifica il `Write` del piano in `passo2` con «un piano già committato non passerebbe da `plan-check`». Nella prova `/tollgate:start` in L1 ha scritto e registrato da sé il piano (passo1, eventi seq 3-5), quindi in `passo2` il modello non ha usato `Write` per il piano e ha ignorato il testo del prompt (`src/conf.py`, `leggi_nome`, `tests.test_conf`). Il messaggio finale del passo 2 (`claude.jsonl` passo2, riga 310) lo dice e chiede: «Se volevi il tuo piano, va rivisto». Il rapporto nota che il piano non è quello di `piano-L1.md`, ma non riporta: (a) che il ramo «scrivi il piano con Write» di `passo2` non è stato esercitato dal vivo; (b) che il modello ha segnalato la discrepanza; (c) che il testo `piano-L1.md` nel prompt è rimasto un riferimento morto. Per un rapporto di verifica serve dirlo tra i limiti o i difetti dello script, con il dato giusto: nel passo 2 nessun `Write` di piano.

#### Minor

1. **`validate`: il rapporto dice «un solo consiglio sul README» ma `validate-1.txt` ha anche un avviso** («Found 1 plugin directory warning», `ICON_MISSING` in `plugin.json`). L'esito resta «Validation passed», ma l'avviso va nominato.

2. **Fusi orari non dichiarati e un orario non presente in nessuna evidenza.** Il rapporto usa orari locali (07:30:00, 07:30:10) mentre `events.jsonl`/`lookups.txt` sono in UTC (06:30:00,93 per l'evento `research_note` valido, 06:30:11,08 per la ricevuta `verify`, 06:30:11,51 per l'evento `commit`). «07:30:10» per il commit `26aed41` non è in nessun file (git-log-worktree non ha orari); il dato più vicino è 06:30:11 UTC = 07:30:11 locale. Correzione: scrivere «UTC» o «ora locale (UTC+1)» e usare 07:30:11, ricordando che l'orario del commit è dedotto dall'evento `commit` (seq 13).

3. **«ha scritto e registrato da sé un piano» è impreciso.** La registrazione (`scope_registered`, seq 4, 06:28:06, poi `phase_change` a `execution`) l'ha fatta tollgate dopo il `Write` (il commit del modello è l'evento seq 6, 06:28:09, 3 s dopo). Il modello ha scritto e committato; il testo del passo 1 conferma «tollgate ha registrato il piano».

4. **Avvisi di `start` non riportati.** L'uscita finale del passo 1 (`claude.jsonl` passo1, riga 161) riporta due avvisi: impostazioni di GitHub Actions non leggibili e protezione del ramo non leggibile. `fakegh.log` mostra le chiamate (`actions/permissions`, `branches/main/protection`). Con il `gh` finto sono attesi, ma la sezione «avvisi e rifiuti» li omette.

5. **Anonimizzazione: restano due identificatori della macchina.** L'host `HOST` (campo `host` in `events.jsonl` e `eventi-ricerca.jsonl`) e, nelle intestazioni di `comandi-modello.txt` (righe 1 e 7), il percorso `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b1/…`, che rivela la struttura delle cartelle di lavoro. Non sono segreti e `USER` è già sostituito, quindi minor.

6. **Due affermazioni non riscontrabili nelle evidenze.** Il tetto di 2400 s (non c'è in `argv.txt` né in `esito.txt`) e «dentro l'abbonamento (nessuna spesa in più)»: `modelUsage` riporta `costBasis: "list"`, cioè prezzo di listino, e nulla prova come sia fatturata la sessione. Riformulare come «costo di listino stimato, 0,91 USD».

7. **Letture del coordinatore non menzionate.** Nel passo 1 la sessione principale ha fatto un `WebFetch` della stessa pagina `tomllib` (`claude.jsonl` passo1, riga 95) per scrivere il piano. Non entra in `lookups` (non è dell'implementatore), ma `comandi-modello.txt` conta `WebFetch: 2 (1)` e il rapporto non spiega la differenza. Una frase basta.

### Valutazione

**Qualità del task:** Approvato con riserve (due Important da sistemare nel testo del rapporto; nessuna correzione al prodotto).
**Motivo:** i numeri, le sequenze, i testi citati, i costi, i token e il verdetto del revisore tornano con le evidenze; l'esito «non composito» è corretto e l'anonimizzazione regge. Mancano l'evidenza di `prepara` e l'ammissione esplicita che il ramo `Write` del piano in `passo2` non è stato esercitato dal vivo.
