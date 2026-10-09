# tollgate P2: guardrail

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire i guardrail locali di tollgate: wrapper `hooks/run`, adattatore per Claude Code, registro dei controlli con i moduli di ogni riga di 7.2 e 7.4, le analisi pure riusate dal gate (`tollgate_analysis`) e i sottocomandi `hook`, `verify`, `waiver add`, `block open`, più `plugin.json` e `hooks.json`.

**Architecture:** Tre pacchetti nuovi sotto `bin/`. `tollgate_analysis` contiene funzioni pure (testo in ingresso, dati in uscita, niente DB né rete) e non importa mai `tollgate_core`, così P4 le usa nel gate. `tollgate_hooks` è il motore: legge l'input JSON di Claude Code, lo traduce in un evento d'ingresso (3.2), costruisce un contesto in sola lettura, fa girare i moduli di `tollgate_checks` in ordine, combina le decisioni e applica le registrazioni con le funzioni di `tollgate_core`. `hooks/run` è uno script bash che gestisce `OFF`, il repo non attivo, Python mancante e le uscite prima di chiamare `bin/tollgate hook <evento>`. `tollgate_core` riceve la migrazione 2 e i moduli che servono agli hook (sessioni, subagenti, scope, ricevute, effetti, git in sola lettura, `verify`).

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`sqlite3`, `tomllib`, `ast`, `tokenize`, `shlex`, `xml.etree`, `unittest`), bash e git. Test con `unittest` su Python 3.11 e sul `python3` di sistema tramite `tests/run`.

**Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 20, revisione 21 scritta nei Task 1 e 20): sezioni 3, 3.1, 3.2, 5, 6.3 (hook dei task), 6.6, 7, 8.1-8.5, 11.1, 12.4 (adozione negli hook), 13, 16, 18.2, 18.4, 18.5 (report dell'implementatore). Piano principale: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (riga P2, contratti e vincoli di P1 nella sezione 3). Esiti di P0: `docs/verifiche/2026-10-08-p0-esiti.md`. Rilievi rinviati a P2 (memoria del progetto, `p1-rilievi-rinviati.md`): li copre la sezione «Rilievi di P1 ripresi qui».

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Nessuna dipendenza esterna.
- Python ≥ 3.11 (spec 2). Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- `tollgate_analysis` non importa `tollgate_core`, `tollgate_hooks` né `tollgate_checks` (piano principale, sezione 3). Un test lo controlla (Task 4).
- Un modulo di `tollgate_checks` non scrive mai nel DB: restituisce decisioni `record` (spec 3.2). Il contesto che riceve espone il DB solo in lettura.
- Chi scrive nel DB lo fa con le funzioni di `tollgate_core`; `set_phase`, `open_block` e `close_block` si chiamano fuori da una transazione; ogni commit visto dagli hook diventa un evento `commit` e fa scattare `acts.invalidate_finish`; gli hook gestiscono `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni (vincoli 1-5 del piano principale).
- Gli hook non usano mai la rete (spec 3.2). La configurazione si legge dalla base del lavoro, o dalla punta del ramo predefinito di `origin`, mai dal working tree.
- I pattern usano ovunque il dialetto di `.gitignore` (spec 3.2), implementato una volta in `tollgate_analysis/globs.py`.
- Solo l'uscita 2 blocca (spec 7.1). Il veto si dà con uscita 2 e il motivo su stderr; ogni messaggio d'errore riporta il percorso assoluto di `bin/tollgate` e il comando `touch <cartella di stato>/OFF`.
- Variabili di test (`TOLLGATE_STATE`, `TOLLGATE_GH`, `TOLLGATE_TEST_CONFIG`) valide solo con la sentinella `.tollgate-test` (spec 3.1). **Nessun test tocca `~/.local/state/tollgate`**: ogni test usa `tests.helpers.TempState`.
- I test non lanciano `claude` e non usano la rete. Solo il Task 1 lancia `claude -p`, in `/tmp/tollgate-p2`, mai nel repo.
- Identificatori in inglese, messaggi all'utente in italiano (spec 0).
- Nessun `__pycache__` nel repo (`sys.dont_write_bytecode`, `-B`).
- Commit dopo ogni task (e dopo ogni passo di commit indicato).

## Decisioni di questo piano

Scelte che la spec lascia aperte o che i fatti impongono. Il costo se sbagliate è indicato. Le decisioni 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15 e 22 entrano nella revisione 21 della spec (Task 1 e Task 20).

1. **Hook di controllo e hook informativi.** Di controllo sono gli hook `PreToolUse` (eventi d'ingresso `pre_edit`, `pre_bash`, `pre_agent`, `pre_send_message`, `pre_mcp`): un errore diventa 2. Informativi tutti gli altri (`SessionStart`, `UserPromptExpansion`, `PostToolUse`, `SubagentStart`, `SubagentStop`): un errore diventa 0 con avviso (spec 7.1 punti 6-7). Anche «Python mancante» (7.1 punto 4) segue questa regola: un `SubagentStop` che esce con 2 per sempre terrebbe vivo il subagente. Costo: un controllo informativo in errore passa in silenzio, come la spec già accetta per `SubagentStop`.
2. **Eventi d'ingresso in più: `post_agent` e `post_skill`.** La tabella 7.2 (revisione 20) ha le righe `PostToolUse Agent` e `PostToolUse Skill`, ma l'elenco chiuso di 3.2 non ha gli eventi corrispondenti. Si aggiungono. Costo: nessuno, è un allineamento.
3. **Veto e iniezione.** `deny` = uscita 2 con il motivo su stderr, per ogni evento. `inject` = uscita 0 con `{"hookSpecificOutput": {"hookEventName": <evento>, "additionalContext": <testo>}}` su stdout. Il Task 1 verifica sulla documentazione ufficiale e con una prova quali eventi accettano `additionalContext`; la tabella `INJECT_MODE` dell'adattatore (Task 12) è l'unico punto da cambiare se un evento non lo accetta (ripiego: `systemMessage`). Mai `permissionDecision: "allow"`: scavalcherebbe le richieste di permesso dell'utente.
4. **Scadenza.** Python imposta `signal.alarm([hooks] timeout_s)` appena letta la configurazione (20 s prima). Il wrapper legge lo stesso valore da `tollgate.toml` sul riferimento remoto con `awk` e tiene un cane da guardia a `timeout_s + 2` secondi, con i descrittori chiusi (altrimenti un `sleep` orfano terrebbe aperta la pipe di Claude Code). `hooks.json` dichiara `timeout: 90`. Costo: nessuno rispetto alla spec.
5. **`OFF` senza Python.** Il wrapper gestisce `/tollgate:off [ore]` e `/tollgate:on` direttamente su `UserPromptExpansion` (`command_name` letto con `sed`): crea o cancella `OFF` (con `until=<epoch>` se ci sono ore), e scrive `<ora> off <epoch>` / `<ora> on` in `off.log` nella cartella di stato. I salti degli hook vanno in `skipped.log`. Al primo hook successivo con Python acceso, `tollgate_core.offlog.import_log` trasforma `off.log` in eventi `off`/`on` con l'ora originale, che `stats` già conta. Costo: gli eventi `off`/`on` arrivano in ritardo, con l'ora giusta.
6. **`record` porta un'operazione, non solo un tipo di log.** Spec 3.2 dice `record <tipo di log> <data>`, ma gli hook devono anche aprire blocchi, registrare atti, subagenti, scope. `record(op, **data)` nomina un'operazione di un elenco chiuso (`tollgate_hooks/apply.py`), e ogni operazione scrive il suo evento di 18.4 tramite `tollgate_core`. Costo: nessuno; la revisione 21 lo scrive.
7. **Migrazione 2 dello schema.** Servono dati che lo schema 1 non ha:
   - `session_seen(session, last_seen)` per «sessione viva» (0);
   - `subagents.last_seen` per «subagente fermo da più di `stale_minutes`»;
   - `subagents.vetoes` per i 2 veti di 8.1;
   - `subagents.report` per il report arrivato con `SubagentHandback` prima di `SubagentStop`;
   - `tasks.pending` (`launch` | `resume`) per «`task start` in sospeso» (6.3), scritto da `tasks.assign` (che P3 chiamerà da `task start`);
   - `work_items.level_cap_paths` per «il tetto resta finché il diff non tocca un percorso sensibile **nuovo**» (5).

   Costo: una migrazione; le successive restano solo in avanti.
8. **Revisori, avversari e auditor a `SubagentStop` restano a P3.** P2 fa a `SubagentStop`: implementatori (token, report, ricevuta, veti), controllo di sola lettura (7.3), subagenti interni ignorati. Verdetti del revisore del task, rilievi del revisore finale e report degli avversari sono moduli nuovi del registro in P3 (18.3, 18.5, 8.6 sono di P3 nella matrice). Costo: nessuno, il registro è fatto per questo.
9. **Le deroghe dichiarate sciolgono la violazione in locale, anche se in attesa.** Un commit con una deroga `test` non ancora approvata passa; è `open-pr` (P3) a rifiutare finché c'è qualcosa «in attesa» (0). Così «dopo la deroga passa» (criterio 3) e «un `test` resta in attesa» (criterio 21) valgono insieme. Costo: un commit in più prima del rifiuto di `open-pr`.
10. **Un `approve waiver <id>` resta valido** in qualunque stato del suo atto (`pending`, `consumed`, `expired`): l'approvazione di una deroga non si «usa», quindi la scadenza di 8.4 non la tocca. Costo: nessuno; P3 segue la stessa regola.
11. **Ricevute e report.** Report configurato e assente → ricevuta `red` (8.1: «resta rosso»). `uncounted` solo senza report configurato. `dod._receipt` accetta `uncounted` con `allow_no_tests` e uscita 0 (rilievo rinviato di P1). Costo: nessuno.
12. **`verify` non lancia `setup`.** Il setup è del gate (P4); in locale l'ambiente è già pronto. `verify` esegue i comandi del gate (`[commands] gate` più i `gate` dei profili attivi sul diff); `verify --related` esegue `test_related` sui file cambiati dalla base, e ripiega sul gate completo se non ce ne sono (8.1). Costo: un progetto che richiede il setup a ogni verifica lo mette nel comando.
13. **File del contesto.** La guardia del contesto legge `<cartella di stato>/ctx/<session_id>.json` con la forma `{"used_pct": <numero o null>}`. Lo scrive la statusline di P3 (11.3). File assente, illeggibile o `null` → nessun blocco (criterio 8). Costo: P3 deve scrivere quella forma.
14. **Identificativo di un effetto esterno:** `e-` più i primi 8 caratteri esadecimali di `sha256(comando normalizzato, lavoro, SHA)`. È deterministico, quindi il veto lo può citare prima che la registrazione scriva l'intento. L'intento (`intents`, `action = "effect"`) ha chiave `effect:<sha256>`. Costo: collisione su 32 bit tra effetti dello stesso repo, trascurabile.
15. **Oggetto e target degli atti** (letti da `command_name` e `command_args`, 8.4): `approve <oggetto> [<target>] [...]` con target = secondo argomento per `waiver`, `effect`, `finding`, `level`, `rounds`, `spec` (numero di fette); per `pr` il target è lo SHA di HEAD; per `plan`, `rebase`, `unverified-*` nessun target. `reopen spec|plan <motivo>`: oggetto `spec` o `plan`. `resolve <id> <nota>`: target `<id>` (anche `writer`). `adopt #N`, `abandon #N`: target `N`. `finish`: lavoro della sessione e SHA di HEAD. Tutti gli argomenti restano in `args`. Costo: P3 legge gli atti con queste chiavi (lo scrive il piano principale).
16. **Ramo `tg/*` senza riga nel DB** (12.4, criterio 17): Edit e Write negati tranne i `.md` sotto `docs/superpowers/`; in Bash negati i comandi che scrivono (commit, push, redirect, `rm`, `mv`…). I comandi di lettura passano, così l'agente può ancora guardare lo stato. Costo: un comando di scrittura non riconosciuto passa, come per ogni regola di 7.4.
17. **`git commit` si controlla su working tree più indice** (7.4), rispetto a HEAD, anche file non tracciati e non ignorati. `PostToolUse Bash` controlla poi ogni commit nuovo, rispetto al suo genitore. Costo: un commit dell'indice soltanto, con altre modifiche non messe in stage, può ricevere un veto che non gli spetta; l'agente lo vede dal motivo.
18. **«4.000 byte» del livello L0** = lunghezza del diff unificato dalla base più la dimensione dei file nuovi non tracciati. Costo: soglia tarabile in `[levels]`.
19. **Forma degli identificativi.** JS e TS: forma vitest (` > `), oppure forma jest (spazio) se un comando del gate contiene `jest`. Python: forma pytest (7.5). Go: `<cartella>::<TestNome>`, forma non verificata in P0 (nessun gate Go nel nucleo). Costo: per Go, falsi «mancanti» nel gate; in locale il confronto è tra due analisi statiche della stessa forma, quindi coerente.
20. **Token del budget:** somma, sui messaggi dell'assistente del transcript (unici per `message.id`), di `input_tokens + cache_creation_input_tokens + output_tokens`. `cache_read_input_tokens` resta fuori: riconta l'intero contesto a ogni turno, e 60 turni da 30K supererebbero da soli il tetto L1. Costo: tetto più largo del previsto; si tara con D.
21. **Sessione viva:** ogni hook aggiorna `session_seen` (e `subagents.last_seen` se c'è `agent_id`). È una scrittura per hook. Costo: qualche millisecondo per chiamata.
22. **Sessioni legate fuori dal repo:** quando una sessione si lega a un lavoro, l'hook crea `<cartella di stato>/bound/<session_id>`. Il wrapper considera attivo anche un `cwd` fuori dai repo attivi se quel file esiste, così le regole del lavoro valgono «in qualunque directory» (6.6) senza aprire Python per ogni repo. Costo: un file per sessione legata; P3 li pulisce con `start`.
23. **`marketplace.json` resta a P3** (matrice, riga 3). P2 crea `.claude-plugin/plugin.json` con `dependencies` nella forma `{"name", "version", "marketplace"}` (verificata in `docs/audit/2026-10-08-revisione-avversariale-2-spec-nucleo.md`, riga 80); l'intervallo dipende dall'esito del Task 1.
24. **Ricevute dei test correlati:** `verify --related` registra il comando con il nome `related`. Vale per il controllo di `SubagentStop` (una ricevuta `green` sull'ultimo commit), non per la Definition of Done, che chiede i comandi del gate. Costo: nessuno.

## Rilievi di P1 ripresi qui

| Rilievo (memoria `p1-rilievi-rinviati.md`) | Dove |
|---|---|
| `profiles.active` con profili non dichiarati | Task 4: avviso in `config.load_config_text` |
| Corruzione dopo l'apertura e `sqlite3.Error` durante le operazioni | Task 12: il runner gestisce `sqlite3.DatabaseError` (corrotto → suggerimento di `db restore`) e `sqlite3.Error` |
| Con `OFF` gli hook non aprono il DB | Task 13 (wrapper) e Task 12 (il runner controlla `OFF` prima di aprire il DB) |
| `uncounted` sempre rosso in `dod._receipt` | Task 3 (decisione 11) |

## Review Focus

1. **Comandi Bash che `shlex` non sa leggere** (virgolette non chiuse, heredoc, `$(...)` annidati, righe continuate con `\`): il controllo non deve andare in crash né lasciar passare in silenzio. Con un comando illeggibile in un lavoro attivo si cercano comunque per testo le parole pericolose (`push`, `--force`, `reset --hard`, `--no-verify`, `TOLLGATE_`). Test in Task 7 (`test_unparsable_falls_back_to_text`) e in Task 16.
2. **Input degli hook malformato o con campi mancanti** (JSON troncato, `tool_input` senza `file_path`, `cwd` inesistente): un hook di controllo esce con 2 e un messaggio chiaro; uno informativo esce con 0. Test in Task 12 (`test_malformed_input_*`).
3. **Percorsi con spazi, collegamenti simbolici e file che non esistono ancora** (il repo stesso è in `.../Plugin IT workflow/`; un Write crea `src/nuova/cartella/x.py`): il repo di appartenenza si trova risalendo alla prima cartella esistente; il confronto con il worktree usa percorsi risolti. Test in Task 9 (`test_toplevel_of_missing_path`) e Task 15 (`test_write_new_dir_out_of_scope`).
4. **File binari e testo non UTF-8 nel diff** (un'immagine nei test, un file Latin-1): test-guard e livello non vanno in crash; un binario porta il lavoro almeno a L1. Test in Task 5 (`test_binary_is_not_l0`) e Task 6 (`test_binary_and_latin1_do_not_crash`).
5. **Due hook nello stesso istante** (due subagenti in sola lettura e il coordinatore): `session_seen` e `subagents.last_seen` si aggiornano senza `database is locked`. Lo copre il `busy_timeout` di P1; qui un test con due processi che fanno girare il runner insieme. Test in Task 12 (`test_concurrent_hooks`).

## Mappa dei file

| File | Responsabilità |
|---|---|
| `spikes/run-p2-experiments.sh`, `spikes/hookprobe/agents/probe-turns3.md` | Verifiche del Task 1 |
| `docs/verifiche/2026-10-09-p2-verifiche.md` | Esiti del Task 1 |
| `spikes/fixtures/hook-inputs/samples.json` | Campioni reali degli input (si aggiungono Edit, Write, Skill) |
| `bin/tollgate_core/db.py` | Migrazione 2 |
| `bin/tollgate_core/sessions.py` | Sessioni viste, sessione viva, lavoro legato, lavoro di un percorso, segnalino `bound/` |
| `bin/tollgate_core/subagents.py` | Righe di `subagents`: partenza, ripresa, nome, report, veti, chiusura, interruzione |
| `bin/tollgate_core/tasks.py` | `assign`, `take_pending`, `add_commit` |
| `bin/tollgate_core/scope.py` | Scope e registrazione del piano |
| `bin/tollgate_core/receipts.py` | Ricevute (8.1) |
| `bin/tollgate_core/effects.py` | Effetti esterni come intenti (8.5) |
| `bin/tollgate_core/offlog.py` | Import di `off.log` negli eventi |
| `bin/tollgate_core/git.py` | Git in sola lettura |
| `bin/tollgate_core/verify.py` | Sottocomando `verify` (8.1) |
| `bin/tollgate_core/waiver_cli.py` | `waiver add`, `block open` |
| `bin/tollgate_core/cli.py` | Sottocomandi `hook`, `verify`, `waiver`, `block` |
| `bin/tollgate_analysis/globs.py` | Dialetto `.gitignore` |
| `bin/tollgate_analysis/protected.py` | File di tollgate e file protetti |
| `bin/tollgate_analysis/profiles.py` | Profilo verticale di un file, profili attivi, skill di un task |
| `bin/tollgate_analysis/plan.py` | `plan-check` (7.5) |
| `bin/tollgate_analysis/level.py` | Livello (5) |
| `bin/tollgate_analysis/junit.py` | Lettura sicura del JUnit |
| `bin/tollgate_analysis/scan.py` | Token JS, codice Python senza commenti e stringhe |
| `bin/tollgate_analysis/testids.py` | Identificativi dei test per analisi statica |
| `bin/tollgate_analysis/testguard.py` | test-guard (8.2) |
| `bin/tollgate_analysis/bash.py` | Lettura dei comandi Bash e classificazione (7.4, 8.5) |
| `bin/tollgate_analysis/waivers.py` | File delle deroghe (18.2), stato, copertura delle violazioni |
| `bin/tollgate_analysis/report.py` | Report dell'implementatore (18.5), taglio di `maxTurns`, token dal transcript |
| `bin/tollgate_hooks/model.py` | `Event`, `Decision`, elenco degli eventi d'ingresso |
| `bin/tollgate_hooks/adapter.py` | Input di Claude Code → `Event`; esito → uscita, stdout, stderr |
| `bin/tollgate_hooks/context.py` | `Ctx` in sola lettura |
| `bin/tollgate_hooks/registry.py` | Caricamento dei moduli, `api`, componenti |
| `bin/tollgate_hooks/apply.py` | Operazioni `record` |
| `bin/tollgate_hooks/runner.py` | `run_hook`: tutto il percorso di un hook |
| `bin/tollgate_checks/*.py` | Un modulo per controllo |
| `hooks/run`, `hooks/hooks.json` | Wrapper e dichiarazione degli hook |
| `.claude-plugin/plugin.json` | Manifest del plugin |
| `skills/off/SKILL.md`, `skills/on/SKILL.md` | Interruttore (solo l'utente) |
| `tests/hookkit.py` | Campioni degli input e banco di prova con repo, origin, worktree e lavoro |
| `tests/test_*.py` | Un file per modulo |

---

### Task 1: Verifiche residue, formato d'uscita, campioni reali

Voci aperte della sezione 16 e fatti che il codice di P2 dà per buoni. Nessun codice di prodotto: un esperimento, un rapporto, la revisione 21 della spec.

**Files:**
- Create: `spikes/hookprobe/agents/probe-turns3.md`
- Create: `spikes/run-p2-experiments.sh`
- Create: `docs/verifiche/2026-10-09-p2-verifiche.md`
- Modify: `spikes/fixtures/hook-inputs/samples.json`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21)

**Interfaces:**
- Produces: in `samples.json` le chiavi `PreToolUse-Write`, `PostToolUse-Write`, `PreToolUse-Edit`, `PostToolUse-Edit`, `PostToolUse-Skill` (sessione principale) e `PreToolUse-Write-subagent` (con `agent_id`). Le usano i Task 14-19 tramite `tests/hookkit.sample`.
- Produces: l'esito di D2 (quali eventi accettano `additionalContext`), che decide la tabella `INJECT_MODE` del Task 12.
- Produces: l'esito di D1, che decide il campo `version` di `dependencies` nel Task 13.

**Regole di cautela (vanno nel brief del subagente):** si lavora solo in `/tmp/tollgate-p2`. Non si installa, non si abilita e non si disinstalla nessun plugin nella configurazione dell'utente (niente `claude plugin install`, niente `claude plugin marketplace add`). Non si toccano `~/.claude/settings.json` né `~/.local/state/tollgate`. Non si crea nessun repo su GitHub. `claude -p` si lancia solo con `--plugin-dir spikes/hookprobe`.

- [ ] **Step 1: Agente sonda per il taglio durante la ripresa**

`spikes/hookprobe/agents/probe-turns3.md`:

```markdown
---
name: probe-turns3
description: Sonda P2 per maxTurns durante una ripresa. Da usare solo quando richiesto esplicitamente.
tools: Read
model: haiku
maxTurns: 3
---
Esegui alla lettera il compito che ricevi. Leggi i file solo con lo strumento Read, un file per turno. Alla fine di ogni compito scrivi FATTO.
```

- [ ] **Step 2: Script degli esperimenti**

`spikes/run-p2-experiments.sh` (eseguibile):

```bash
#!/usr/bin/env bash
# spikes/run-p2-experiments.sh — E7 (taglio in background), E8 (taglio alla ripresa), E9 (campioni)
set -uo pipefail
P2=/tmp/tollgate-p2; mkdir -p "$P2" || exit 1
PLUGIN="$(cd "$(dirname "$0")/hookprobe" && pwd)" || exit 1
export PROBE_LOG="$P2/probe.jsonl"
W="$P2/turns"; rm -rf "$W"; mkdir -p "$W" || exit 1
for i in 1 2 3 4 5 6 7 8; do echo "contenuto $i" > "$W/$i.txt"; done
run() { # id, modo, prompt
  rm -f "$PROBE_LOG"
  ( cd "$W" && claude -p --plugin-dir "$PLUGIN" --permission-mode "$2" "$3" < /dev/null ) > "$P2/$1.out" 2>&1
  cp "$PROBE_LOG" "$P2/$1.jsonl" 2>/dev/null || : > "$P2/$1.jsonl"
}
run e7 manual "Lancia con lo strumento Agent il subagente hookprobe:probe-turns IN BACKGROUND (run_in_background: true) con il compito descritto nelle sue istruzioni. Aspetta la notifica di fine e riporta alla lettera ogni testo che ricevi, compresi gli avvisi di interruzione."
run e8 manual "Lancia con lo strumento Agent, in primo piano, il subagente hookprobe:probe-turns3 con name 'sonda3' e il compito: leggi 1.txt e scrivi FATTO. Poi riprendilo con SendMessage verso 'sonda3' chiedendo: leggi 2.txt, 3.txt, 4.txt, 5.txt, 6.txt uno per turno e scrivi FATTO. Riporta alla lettera ogni risposta e ogni avviso di interruzione."
run e9 manual "Esegui in ordine: 1) con lo strumento Write crea il file nota.txt con il testo 'uno'; 2) con lo strumento Edit sostituisci 'uno' con 'due' in nota.txt; 3) lancia con lo strumento Agent un subagente general-purpose in primo piano con il compito: con lo strumento Write crea sub.txt con il testo 'tre' e rispondi FATTO; 4) invoca con lo strumento Skill la skill hookprobe:probe-preload. Riporta l'esito di ogni passo."
echo "fatto: $(ls "$P2")"
```

- [ ] **Step 3: Eseguire e leggere i log**

Run: `bash spikes/run-p2-experiments.sh`
Expected: `fatto:` seguito da `e7.jsonl e7.out e8.jsonl e8.out e9.jsonl e9.out probe.jsonl turns`.

Poi, per ogni log: `python3 -c "import json,sys; [print(json.loads(l)['event'], json.loads(l)['input'].get('tool_name'), json.loads(l)['input'].get('agent_id')) for l in open(sys.argv[1]) if l.strip()]" /tmp/tollgate-p2/e7.jsonl` (stesso per `e8`, `e9`).

Da registrare:
- **E7**: compare `SubagentStop` per il subagente in background tagliato? Il testo del taglio arriva al coordinatore? Da quale evento si può leggere (nessuno, `PostToolUse` di qualche strumento, solo la notifica)? Il `PostToolUse Agent` è `async_launched`.
- **E8**: la ripresa con 5 letture e `maxTurns: 3` viene tagliata? (`maxTurns` riparte da zero alla ripresa se la ripresa arriva a 3 letture.) Quali eventi produce il taglio alla ripresa (`SubagentStop`? `PostToolUse SendMessage` con quale `tool_response`?)
- **E9**: input di `PreToolUse`/`PostToolUse` di `Write`, `Edit`, `Skill` della sessione principale e di `Write` del subagente.

Se un esperimento non dà un risultato leggibile (per esempio il processo `-p` chiude prima della notifica del background), ripeterlo una volta con una formulazione più esplicita e registrare «non determinato» se non basta. Non inventare un esito.

- [ ] **Step 4: Campioni in `samples.json`**

Aggiungere a `spikes/fixtures/hook-inputs/samples.json` le chiavi elencate in **Interfaces**, copiando l'input reale da `e9.jsonl` e sostituendo la cartella personale con `/home/USER` (stessa anonimizzazione dei campioni esistenti):

```bash
python3 - <<'PY'
import json, os, re
from pathlib import Path
p = Path("spikes/fixtures/hook-inputs/samples.json")
samples = json.loads(p.read_text())
home = os.path.expanduser("~")
rows = [json.loads(l) for l in open("/tmp/tollgate-p2/e9.jsonl") if l.strip()]
def pick(event, tool, sub):
    for r in rows:
        i = r["input"]
        if r["event"] == event and i.get("tool_name") == tool and bool(i.get("agent_id")) == sub:
            return json.loads(json.dumps(i).replace(home, "/home/USER"))
    return None
for key, (ev, tool, sub) in {
    "PreToolUse-Write": ("PreToolUse", "Write", False), "PostToolUse-Write": ("PostToolUse", "Write", False),
    "PreToolUse-Edit": ("PreToolUse", "Edit", False), "PostToolUse-Edit": ("PostToolUse", "Edit", False),
    "PostToolUse-Skill": ("PostToolUse", "Skill", False),
    "PreToolUse-Write-subagent": ("PreToolUse", "Write", True)}.items():
    s = pick(ev, tool, sub)
    if s is None:
        print("MANCA", key)
    else:
        samples[key] = s
p.write_text(json.dumps(samples, ensure_ascii=False, indent=2) + "\n")
PY
```

Expected: nessuna riga `MANCA`. Se una manca, ripetere E9; se manca ancora, registrarlo nel rapporto e nel ledger: `tests/hookkit.sample` costruisce quell'input dalla busta di `PreToolUse-Bash` con `tool_name` e `tool_input` della documentazione (Task 12).

- [ ] **Step 5: Fatti dalla documentazione ufficiale**

Con un subagente `claude-code-guide` (modello sonnet), leggere le pagine ufficiali `hooks`, `plugins/dependencies` e `plugins-reference` e rispondere, citando la frase e la pagina:

- **D1**: le `dependencies` con `version` (intervallo semver) si risolvono sui tag del repo della dipendenza; quale forma di tag (`v6.4.1`, `superpowers--v6.4.1`, altro)? Una dipendenza da un plugin di un altro marketplace richiede `allowCrossMarketplaceDependenciesOn`? Esiste un comando che valida `plugin.json` senza installare (`claude plugin validate`)?
- **D2**: per quali eventi `hookSpecificOutput.additionalContext` viene aggiunto al contesto del modello: `PreToolUse`, `PostToolUse`, `SessionStart`, `SubagentStart`, `UserPromptExpansion`? Per `SubagentStop`, l'uscita 2 impedisce la chiusura e passa stderr al subagente? Per `PostToolUse`, l'uscita 2 mostra stderr al modello?
- **D3**: nomi e campi degli strumenti `MultiEdit` e `NotebookEdit` nella versione attuale (esistono ancora? `tool_input.file_path` o `notebook_path`?).

Se la documentazione non risponde a D2 per `PreToolUse`, provarlo: aggiungere temporaneamente a `spikes/hookprobe/probe.sh` un ramo che, per `PreToolUse` di `Read` con `PROBE_CTX` nel percorso, stampi `{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"MARCATORE-CTX-77"}}`, lanciare `claude -p` chiedendo di leggere `/tmp/tollgate-p2/turns/PROBE_CTX.txt` e di riportare ogni marcatore ricevuto, poi togliere il ramo.

- [ ] **Step 6: Rapporto**

`docs/verifiche/2026-10-09-p2-verifiche.md` con la stessa forma del rapporto di P0: versioni (`claude --version`), una tabella con `Id | Voce | Esito (sì/no/non determinato) | Evidenza | Conseguenza` per E7, E8, E9, D1, D2, D3, e la sezione «Conseguenze per il piano P2» che dice:
- quale valore va in `INJECT_MODE` (Task 12) per ogni evento;
- quale `version` va in `dependencies` (Task 13): l'intervallo `>=6.4.1 <7.0.0` se D1 conferma tag compatibili, altrimenti nessun `version` e il ripiego di 11.1 (controllo in `start`, P3);
- se il taglio in background o alla ripresa si riconosce da un evento: se sì, quale riga va aggiunta al modulo `post_agent` del Task 18 (o a un modulo nuovo); se no, la rete resta `stale_minutes` (spec 6.3), e il rapporto lo dice.

- [ ] **Step 7: Revisione 21 della spec**

In `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`:
- intestazione: `Revisione: **21**: esiti delle verifiche P2 (docs/verifiche/2026-10-09-p2-verifiche.md); eventi d'ingresso post_agent e post_skill; record come operazione. Revisione 20: …` (il resto invariato);
- 3.2, «Eventi d'ingresso»: aggiungere `post_agent` e `post_skill` all'elenco;
- 3.2, «Decisioni»: `record <operazione> <data>`: un'operazione di un elenco chiuso del motore, che scrive anche il suo evento di 18.4;
- 16: spostare le due voci di «Ancora da verificare» nella tabella degli esiti, con l'esito di E7/E8 e di D1 (o «non determinato» con la rete di sicurezza);
- 20: una riga per la revisione 21.

- [ ] **Step 8: Commit**

```bash
git add spikes/hookprobe/agents/probe-turns3.md spikes/run-p2-experiments.sh spikes/fixtures/hook-inputs/samples.json docs/verifiche/2026-10-09-p2-verifiche.md docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md
git commit -m "tollgate P2: verifiche residue (maxTurns, dependencies, uscite degli hook), campioni reali, spec rev 21"
```

---

### Task 2: Migrazione 2, sessioni, subagenti, assegnazione dei task

**Files:**
- Modify: `bin/tollgate_core/db.py` (dopo `SCHEMA_V1`, e `MIGRATIONS`)
- Create: `bin/tollgate_core/sessions.py`
- Create: `bin/tollgate_core/subagents.py`
- Modify: `bin/tollgate_core/tasks.py`
- Modify: `tests/test_db.py:39,56` (versione attesa da `"1"` a `str(db.latest_version())`)
- Test: `tests/test_sessions.py`, `tests/test_subagents.py`, `tests/test_tasks.py`, `tests/test_db.py`

**Interfaces:**
- Consumes: `db.open_db`, `db.tx`, `db.backup`, `events.record_event`, `phases.create_work`, `phases.bind_session`, `phases.get_work`, `tasks.task_event`, `clock`.
- Produces:
  - `db.latest_version() == 2`.
  - `sessions.touch(conn, session: str, *, now) -> None`; `sessions.alive(conn, session, *, now, stale_minutes: int) -> bool`; `sessions.bound_work(conn, session) -> Row | None`; `sessions.work_for_path(conn, path) -> Row | None`; `sessions.mark_bound(state, session) -> None`; `sessions.BOUND_DIR = "bound"`.
  - `subagents.start(conn, *, agent_id, type_, session, work, task, base_sha, fingerprint, now) -> bool` (vero se ripresa); `subagents.touch(conn, agent_id, *, now)`; `subagents.set_name(conn, agent_id, name, *, session, work, now)`; `subagents.set_report(conn, agent_id, text)`; `subagents.add_veto(conn, agent_id) -> int`; `subagents.finish(conn, agent_id, *, state, now, declared_status=None, tokens=None, session=None)`; `subagents.get(conn, agent_id) -> Row | None`; `subagents.by_name(conn, name, *, work) -> Row | None`; `subagents.running(conn, *, work=None) -> list[Row]`; `subagents.interrupt(conn, agent_id, *, now, session=None)`; `subagents.STATES`.
  - `tasks.assign(conn, work, number, *, implementer, agent_type, pending, reviewer_type=None, now, session=None)`; `tasks.take_pending(conn, work, *, agent_type, resume: bool) -> int | None`; `tasks.add_commit(conn, work, number, sha)`; `tasks.PENDING = ("launch", "resume")`.

- [ ] **Step 1: Test della migrazione**

In `tests/test_db.py` sostituire `"1"` con `str(db.latest_version())` nelle due asserzioni sulla versione (righe 39 e 56) e aggiungere:

```python
class MigrationV2Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_from_v1_adds_columns_and_backup(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:1]
            db.open_db(self.ts.state).close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "2")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(subagents)")}
            self.assertTrue({"last_seen", "vetoes", "report"} <= cols)
            self.assertIn("pending", {r[1] for r in conn.execute("PRAGMA table_info(tasks)")})
            self.assertIn("level_cap_paths",
                          {r[1] for r in conn.execute("PRAGMA table_info(work_items)")})
            conn.execute("SELECT session, last_seen FROM session_seen").fetchall()
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-2.db")))
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_db -v`
Expected: FAIL in `test_from_v1_adds_columns_and_backup` (versione `"1"`).

- [ ] **Step 3: Migrazione**

In `bin/tollgate_core/db.py`, dopo `SCHEMA_V1`:

```python
# Migrazione 2 (piano P2, decisione 7): dati che servono agli hook.
SCHEMA_V2 = [
    "CREATE TABLE session_seen (session TEXT PRIMARY KEY, last_seen TEXT NOT NULL)",
    "ALTER TABLE subagents ADD COLUMN last_seen TEXT",
    "ALTER TABLE subagents ADD COLUMN vetoes INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE subagents ADD COLUMN report TEXT",
    "ALTER TABLE tasks ADD COLUMN pending TEXT "
    "CHECK (pending IS NULL OR pending IN ('launch','resume'))",
    "ALTER TABLE work_items ADD COLUMN level_cap_paths TEXT NOT NULL DEFAULT '[]'",
    "CREATE INDEX subagents_work ON subagents(work, state)",
]

MIGRATIONS: list[tuple[int, list[str]]] = [(1, SCHEMA_V1), (2, SCHEMA_V2)]
```

(sostituisce la riga `MIGRATIONS` esistente).

- [ ] **Step 4: Verificare che passi**

Run: `python3 -B -m unittest tests.test_db -v`
Expected: PASS.

- [ ] **Step 5: Test di sessioni e subagenti**

`tests/test_sessions.py`:

```python
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.helpers import TempState
from tollgate_core import db, phases, sessions

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class SessionsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_alive_by_last_seen(self):
        sessions.touch(self.conn, "s1", now=T0)
        self.assertTrue(sessions.alive(self.conn, "s1", now=T0 + timedelta(minutes=29),
                                       stale_minutes=30))
        self.assertFalse(sessions.alive(self.conn, "s1", now=T0 + timedelta(minutes=31),
                                        stale_minutes=30))
        self.assertFalse(sessions.alive(self.conn, "mai-vista", now=T0, stale_minutes=30))

    def test_bound_work_and_path(self):
        wt = self.ts.dir / "wt 7"
        (wt / "src").mkdir(parents=True)
        w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                               session="s1", worktree=str(wt))
        self.assertEqual(sessions.bound_work(self.conn, "s1")["id"], w)
        self.assertIsNone(sessions.bound_work(self.conn, "s2"))
        self.assertEqual(sessions.work_for_path(self.conn, wt / "src" / "nuovo.py")["id"], w)
        self.assertIsNone(sessions.work_for_path(self.conn, self.ts.dir / "altro"))

    def test_closed_work_is_not_bound(self):
        w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                               session="s1")
        phases.set_phase(self.conn, self.ts.state, w, "closed", "abandoned", now=T0)
        self.assertIsNone(sessions.bound_work(self.conn, "s1"))

    def test_mark_bound_creates_marker(self):
        sessions.mark_bound(self.ts.state, "s1")
        self.assertTrue((self.ts.dir / sessions.BOUND_DIR / "s1").is_file())
        sessions.mark_bound(self.ts.state, "../fuori")
        self.assertFalse((self.ts.dir / "fuori").exists())


if __name__ == "__main__":
    unittest.main()
```

`tests/test_subagents.py`:

```python
import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, subagents, tasks

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class SubagentsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                                    session="s1")
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _start(self, now=T0):
        return subagents.start(self.conn, agent_id="a1", type_="tollgate:implementer",
                               session="s1", work=self.w, task=1, base_sha="b0",
                               fingerprint="f0", now=now)

    def test_start_then_resume_keeps_base(self):
        self.assertFalse(self._start())
        subagents.finish(self.conn, "a1", state="done", declared_status="NEEDS_CONTEXT", now=T0)
        resumed = subagents.start(self.conn, agent_id="a1", type_="tollgate:implementer",
                                  session="s1", work=self.w, task=1, base_sha="b9",
                                  fingerprint="f9", now=T0 + timedelta(minutes=1))
        self.assertTrue(resumed)
        row = subagents.get(self.conn, "a1")
        self.assertEqual((row["agent_base_sha"], row["resumes"], row["state"]), ("b0", 1, "running"))
        self.assertIsNone(row["ended"])

    def test_name_before_start_is_merged(self):
        subagents.set_name(self.conn, "a1", "tg-7-t1", session="s1", work=self.w, now=T0)
        self._start()
        self.assertEqual(subagents.by_name(self.conn, "tg-7-t1", work=self.w)["id"], "a1")

    def test_vetoes_and_report(self):
        self._start()
        self.assertEqual(subagents.add_veto(self.conn, "a1"), 1)
        self.assertEqual(subagents.add_veto(self.conn, "a1"), 2)
        subagents.set_report(self.conn, "a1", "testo")
        self.assertEqual(subagents.get(self.conn, "a1")["report"], "testo")

    def test_interrupt_returns_running_task_to_pending(self):
        tasks.task_event(self.conn, self.w, 1, "start", now=T0)
        self._start()
        subagents.interrupt(self.conn, "a1", now=T0 + timedelta(hours=1))
        self.assertEqual(subagents.get(self.conn, "a1")["state"], "interrupted")
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["state"], "pending")
        self.assertEqual(subagents.running(self.conn, work=self.w), [])

    def test_finish_records_event(self):
        self._start()
        subagents.finish(self.conn, "a1", state="done", declared_status="DONE", tokens=123, now=T0)
        ev = self.conn.execute("SELECT data FROM events WHERE type='subagent_stop'").fetchone()
        self.assertIn('"tokens": 123', ev["data"])

    def test_unknown_state_rejected(self):
        self._start()
        with self.assertRaises(ValueError):
            subagents.finish(self.conn, "a1", state="boh", now=T0)


if __name__ == "__main__":
    unittest.main()
```

In `tests/test_tasks.py` aggiungere:

```python
class AssignTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_assign_and_take_launch(self):
        tasks.assign(self.conn, self.w, 1, implementer="tg-7-t1", agent_type="tollgate:implementer",
                     pending="launch", now=T0)
        self.assertIsNone(tasks.take_pending(self.conn, self.w, agent_type="general-purpose",
                                             resume=False))
        self.assertIsNone(tasks.take_pending(self.conn, self.w, agent_type="tollgate:implementer",
                                             resume=True))
        self.assertEqual(tasks.take_pending(self.conn, self.w, agent_type="tollgate:implementer",
                                            resume=False), 1)
        self.assertIsNone(tasks.get_task(self.conn, self.w, 1)["pending"])

    def test_assign_rejects_unknown_pending(self):
        with self.assertRaises(ValueError):
            tasks.assign(self.conn, self.w, 1, implementer="x", agent_type="y", pending="boh",
                         now=T0)

    def test_add_commit_dedup(self):
        tasks.add_commit(self.conn, self.w, 1, "abc")
        tasks.add_commit(self.conn, self.w, 1, "abc")
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["commits"], '["abc"]')
```

(Se `tests/test_tasks.py` non definisce già `T0`, `TempState`, `db`, `phases`, aggiungere gli import come in `tests/test_subagents.py`.)

- [ ] **Step 6: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_sessions tests.test_subagents tests.test_tasks -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_core.sessions'` e `AttributeError: module 'tollgate_core.tasks' has no attribute 'assign'`.

- [ ] **Step 7: `sessions.py`**

```python
"""Sessioni viste dagli hook, sessione viva e lavoro legato (spec 0, 6.6, 12.4)."""
from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

from . import clock, db
from .paths import State, ensure_dirs

BOUND_DIR = "bound"
_SAFE = re.compile(r"^[A-Za-z0-9_-]+$")


def touch(conn, session: str, *, now) -> None:
    with db.tx(conn):
        conn.execute("INSERT INTO session_seen (session, last_seen) VALUES (?, ?) "
                     "ON CONFLICT(session) DO UPDATE SET last_seen = excluded.last_seen",
                     (session, clock.fmt(now)))


def alive(conn, session: str, *, now, stale_minutes: int) -> bool:
    row = conn.execute("SELECT last_seen FROM session_seen WHERE session = ?",
                       (session,)).fetchone()
    return row is not None and row[0] > clock.fmt(now - timedelta(minutes=stale_minutes))


def bound_work(conn, session: str):
    """Il lavoro attivo a cui la sessione è legata (il più recente, se più d'uno)."""
    for row in conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' "
                            "ORDER BY updated DESC, id DESC"):
        if session in json.loads(row["sessions"]):
            return row
    return None


def work_for_path(conn, path) -> object | None:
    """Il lavoro attivo il cui worktree contiene il percorso (risolto, anche se non esiste)."""
    p = Path(path).resolve()
    for row in conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' "
                            "AND worktree IS NOT NULL ORDER BY id"):
        wt = Path(row["worktree"]).resolve()
        if p == wt or wt in p.parents:
            return row
    return None


def mark_bound(state: State, session: str) -> None:
    """Segnalino per il wrapper (decisione 22): la sessione è legata a un lavoro."""
    if not _SAFE.match(session):
        return
    ensure_dirs(state)
    d = state.root / BOUND_DIR
    d.mkdir(mode=0o700, exist_ok=True)
    (d / session).touch()
```

- [ ] **Step 8: `subagents.py`**

```python
"""Righe di `subagents` (spec 6.3, 7.2, 12.2): partenza, ripresa, nome, chiusura."""
from __future__ import annotations

from datetime import timedelta

from . import clock, db, tasks
from .events import record_event

STATES = ("running", "done", "cut", "budget", "interrupted", "tampered")


def get(conn, agent_id: str):
    return conn.execute("SELECT * FROM subagents WHERE id = ?", (agent_id,)).fetchone()


def start(conn, *, agent_id: str, type_: str, session: str, work: int | None,
          task: int | None, base_sha: str | None, fingerprint: str | None, now) -> bool:
    """Registra la partenza; alla ripresa (stessa riga) non tocca agent_base_sha né l'impronta."""
    ts = clock.fmt(now)
    with db.tx(conn):
        row = get(conn, agent_id)
        resumed = row is not None and row["started"] is not None
        if row is None:
            conn.execute("INSERT INTO subagents (id, type, work, task, session, agent_base_sha, "
                         "fingerprint, started, last_seen, state) "
                         "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running')",
                         (agent_id, type_, work, task, session, base_sha, fingerprint, ts, ts))
        elif not resumed:
            conn.execute("UPDATE subagents SET type = ?, work = coalesce(work, ?), task = ?, "
                         "session = ?, agent_base_sha = ?, fingerprint = ?, started = ?, "
                         "last_seen = ?, state = 'running' WHERE id = ?",
                         (type_, work, task, session, base_sha, fingerprint, ts, ts, agent_id))
        else:
            conn.execute("UPDATE subagents SET resumes = resumes + 1, state = 'running', "
                         "ended = NULL, last_seen = ?, task = coalesce(task, ?) WHERE id = ?",
                         (ts, task, agent_id))
        record_event(conn, "subagent_start", {"id": agent_id, "type": type_, "task": task,
                                              "resumed": resumed},
                     now=now, session=session, work=work)
    return resumed


def touch(conn, agent_id: str, *, now) -> None:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET last_seen = ? WHERE id = ?",
                     (clock.fmt(now), agent_id))


def set_name(conn, agent_id: str, name: str, *, session: str, work: int | None, now) -> None:
    """Il nome arriva da PostToolUse Agent, che in background può precedere SubagentStart."""
    with db.tx(conn):
        if get(conn, agent_id) is None:
            conn.execute("INSERT INTO subagents (id, name, work, session, last_seen) "
                         "VALUES (?, ?, ?, ?, ?)",
                         (agent_id, name, work, session, clock.fmt(now)))
        else:
            conn.execute("UPDATE subagents SET name = ? WHERE id = ?", (name, agent_id))


def set_report(conn, agent_id: str, text: str) -> None:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET report = ? WHERE id = ?", (text, agent_id))


def add_veto(conn, agent_id: str) -> int:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET vetoes = vetoes + 1 WHERE id = ?", (agent_id,))
        row = get(conn, agent_id)
        return row["vetoes"] if row else 0


def finish(conn, agent_id: str, *, state: str, now, declared_status: str | None = None,
           tokens: int | None = None, session: str | None = None) -> None:
    if state not in STATES or state == "running":
        raise ValueError(f"stato di chiusura non ammesso: {state}")
    with db.tx(conn):
        row = get(conn, agent_id)
        if row is None:
            raise ValueError(f"subagente {agent_id} sconosciuto")
        started = clock.parse(row["started"]) if row["started"] else now
        conn.execute("UPDATE subagents SET ended = ?, state = ?, declared_status = ?, "
                     "tokens = coalesce(?, tokens), duration = ? WHERE id = ?",
                     (clock.fmt(now), state, declared_status, tokens,
                      (now - started).total_seconds(), agent_id))
        record_event(conn, "subagent_stop",
                     {"id": agent_id, "type": row["type"], "task": row["task"],
                      "declared_status": declared_status, "tokens": tokens, "state": state},
                     now=now, session=session or row["session"], work=row["work"])


def by_name(conn, name: str, *, work: int | None):
    return conn.execute("SELECT * FROM subagents WHERE name = ? AND work IS ? "
                        "ORDER BY coalesce(started, last_seen) DESC LIMIT 1",
                        (name, work)).fetchone()


def running(conn, *, work: int | None = None) -> list:
    sql, params = "SELECT * FROM subagents WHERE state = 'running'", []
    if work is not None:
        sql += " AND work = ?"
        params.append(work)
    return conn.execute(sql + " ORDER BY started", params).fetchall()


def is_stale(row, *, now, stale_minutes: int) -> bool:
    seen = row["last_seen"] or row["started"]
    return seen is not None and seen <= clock.fmt(now - timedelta(minutes=stale_minutes))


def interrupt(conn, agent_id: str, *, now, session: str | None = None) -> None:
    """Un implementatore interrotto riporta il suo task a pending senza consumare un giro."""
    with db.tx(conn):
        row = get(conn, agent_id)
        if row is None or row["state"] != "running":
            return
        conn.execute("UPDATE subagents SET state = 'interrupted', ended = ? WHERE id = ?",
                     (clock.fmt(now), agent_id))
        if row["work"] is not None and row["task"] is not None:
            t = conn.execute("SELECT state FROM tasks WHERE work = ? AND number = ?",
                             (row["work"], row["task"])).fetchone()
            if t is not None and t["state"] == "running":
                tasks.task_event(conn, row["work"], row["task"], "interrupted", now=now,
                                 session=session)
        record_event(conn, "subagent_stop", {"id": agent_id, "type": row["type"],
                                             "task": row["task"], "declared_status": None,
                                             "tokens": None, "state": "interrupted"},
                     now=now, session=session or row["session"], work=row["work"])
```

- [ ] **Step 9: `tasks.py`**

Aggiungere in fondo a `bin/tollgate_core/tasks.py`:

```python
PENDING = ("launch", "resume")


def assign(conn, work: int, number: int, *, implementer: str, agent_type: str, pending: str,
           reviewer_type: str | None = None, now, session=None) -> None:
    """Scritto da `task start` (P3): chi può partire o riprendere su questo task (6.3)."""
    if pending not in PENDING:
        raise ValueError(f"pending sconosciuto: {pending}")
    with db.tx(conn):
        row = get_task(conn, work, number)
        conn.execute("UPDATE tasks SET implementer = ?, agent_type = ?, reviewer_type = ?, "
                     "pending = ? WHERE work = ? AND number = ?",
                     (implementer, agent_type, reviewer_type, pending, work, number))
        _log(conn, row, now=now, session=session)


def take_pending(conn, work: int, *, agent_type: str, resume: bool) -> int | None:
    """Associa un subagente che parte (o riprende) al task in sospeso del suo tipo."""
    want = "resume" if resume else "launch"
    with db.tx(conn):
        row = conn.execute("SELECT number FROM tasks WHERE work = ? AND pending = ? "
                           "AND agent_type = ? ORDER BY number LIMIT 1",
                           (work, want, agent_type)).fetchone()
        if row is None:
            return None
        conn.execute("UPDATE tasks SET pending = NULL WHERE work = ? AND number = ?",
                     (work, row["number"]))
        return row["number"]


def add_commit(conn, work: int, number: int, sha: str) -> None:
    with db.tx(conn):
        commits = json.loads(get_task(conn, work, number)["commits"])
        if sha not in commits:
            commits.append(sha)
            conn.execute("UPDATE tasks SET commits = ? WHERE work = ? AND number = ?",
                         (json.dumps(commits), work, number))
```

- [ ] **Step 10: Verificare che passino e suite completa**

Run: `tests/run`
Expected: tutti i test OK su entrambe le versioni.

- [ ] **Step 11: Commit**

```bash
git add bin/tollgate_core/db.py bin/tollgate_core/sessions.py bin/tollgate_core/subagents.py bin/tollgate_core/tasks.py tests/test_db.py tests/test_sessions.py tests/test_subagents.py tests/test_tasks.py
git commit -m "tollgate P2: migrazione 2, sessioni, subagenti, assegnazione dei task"
```

---
### Task 3: Scope, ricevute, effetti, registro di `OFF`, ricevuta `uncounted` nella DoD

**Files:**
- Create: `bin/tollgate_core/scope.py`
- Create: `bin/tollgate_core/receipts.py`
- Create: `bin/tollgate_core/effects.py`
- Create: `bin/tollgate_core/offlog.py`
- Modify: `bin/tollgate_core/dod.py` (`_receipt`)
- Test: `tests/test_scope.py`, `tests/test_receipts.py`, `tests/test_effects.py`, `tests/test_offlog.py`, `tests/test_dod.py`

**Interfaces:**
- Consumes: `db.tx`, `events.record_event`, `phases.get_work`, `phases.set_phase`, `tasks.add_task`, `clock`.
- Produces:
  - `scope.paths(conn, work) -> set[str]`; `scope.register_plan(conn, state, work, *, plan_path, plan_sha, scope_paths: list[str], plan_tasks: list[tuple[int, list[str]]], advance: bool, now, session=None) -> None` (errore `ValueError` se il piano è già registrato); `scope.set_plan_path(conn, work, plan_path, *, now) -> None`.
  - `receipts.STATES`; `receipts.add(conn, *, work, sha, command, resolved_command, exit_code, tests_run, tests_skipped, duration, log, produced_by, state, now, session=None) -> int`; `receipts.latest(conn, work, sha) -> list[Row]` (l'ultima per comando); `receipts.any_since(conn, work, since: str) -> bool`.
  - `effects.effect_key(command: str, work: int | None, sha: str | None) -> str`; `effects.effect_id(key) -> str` (`e-` + 8 esadecimali); `effects.get(conn, key) -> Row | None`; `effects.request(conn, *, key, command, work, sha, now, session=None) -> None`; `effects.mark_executed(conn, *, key, act_id, now, session=None) -> None`; `effects.executed_at(row) -> str | None`.
  - `offlog.LOG_NAME = "off.log"`; `offlog.import_log(conn, state) -> int` (eventi scritti).
  - `dod._receipt` accetta `uncounted` con `allow_no_tests` e uscita 0.

- [ ] **Step 1: Test**

`tests/test_scope.py`:

```python
import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, scope, tasks

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_register_plan_l1_advances(self):
        scope.register_plan(self.conn, self.ts.state, self.w,
                            plan_path="docs/superpowers/plans/p.md", plan_sha="s1",
                            scope_paths=["src/a.py", "tests/test_a.py"],
                            plan_tasks=[(1, ["tdd"]), (2, [])], advance=True, now=T0)
        self.assertEqual(scope.paths(self.conn, self.w), {"src/a.py", "tests/test_a.py"})
        w = phases.get_work(self.conn, self.w)
        self.assertEqual((w["phase"], w["plan_path"], w["plan_sha"]),
                         ("execution", "docs/superpowers/plans/p.md", "s1"))
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["skills_required"], '["tdd"]')
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM events WHERE type='scope_registered'").fetchone()[0], 1)

    def test_register_twice_rejected_and_scope_unchanged(self):
        scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md", plan_sha="s1",
                            scope_paths=["a"], plan_tasks=[(1, [])], advance=False, now=T0)
        with self.assertRaises(ValueError):
            scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md",
                                plan_sha="s2", scope_paths=["a", "b"], plan_tasks=[(1, [])],
                                advance=False, now=T0)
        self.assertEqual(scope.paths(self.conn, self.w), {"a"})

    def test_set_plan_path_only_once(self):
        scope.set_plan_path(self.conn, self.w, "p.md", now=T0)
        scope.set_plan_path(self.conn, self.w, "altro.md", now=T0)
        self.assertEqual(phases.get_work(self.conn, self.w)["plan_path"], "p.md")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_receipts.py`:

```python
import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import clock, db, phases, receipts

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


def add(conn, work, command, state, at, sha="h1", exit_code=0):
    return receipts.add(conn, work=work, sha=sha, command=command, resolved_command=command,
                        exit_code=exit_code, tests_run=3, tests_skipped=0, duration=1.0,
                        log="/tmp/x.log", produced_by="verify", state=state, now=at)


class ReceiptsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_latest_per_command(self):
        add(self.conn, self.w, "verify", "red", T0)
        add(self.conn, self.w, "verify", "green", T0 + timedelta(seconds=1))
        add(self.conn, self.w, "lint", "green", T0)
        got = {r["command"]: r["state"] for r in receipts.latest(self.conn, self.w, "h1")}
        self.assertEqual(got, {"verify": "green", "lint": "green"})
        ev = self.conn.execute("SELECT count(*) FROM events WHERE type='receipt'").fetchone()[0]
        self.assertEqual(ev, 3)

    def test_any_since(self):
        add(self.conn, self.w, "verify", "red", T0)
        self.assertTrue(receipts.any_since(self.conn, self.w, clock.fmt(T0 - timedelta(1))))
        self.assertFalse(receipts.any_since(self.conn, self.w, clock.fmt(T0 + timedelta(1))))

    def test_unknown_state(self):
        with self.assertRaises(ValueError):
            add(self.conn, self.w, "verify", "boh", T0)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_effects.py`:

```python
import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, effects

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_id_is_deterministic(self):
        k1 = effects.effect_key("npm publish", None, "abc")
        self.assertEqual(k1, effects.effect_key("npm publish", None, "abc"))
        self.assertNotEqual(k1, effects.effect_key("npm publish", None, "def"))
        self.assertRegex(effects.effect_id(k1), r"^e-[0-9a-f]{8}$")

    def test_request_execute_request_again(self):
        k = effects.effect_key("npm publish", None, "abc")
        effects.request(self.conn, key=k, command="npm publish", work=None, sha="abc",
                        now=T0, session="s1")
        self.assertEqual(effects.get(self.conn, k)["state"], "requested")
        self.assertIsNone(effects.executed_at(effects.get(self.conn, k)))
        effects.mark_executed(self.conn, key=k, act_id="a-3", now=T0, session="s1")
        self.assertEqual(effects.get(self.conn, k)["state"], "executed")
        effects.request(self.conn, key=k, command="npm publish", work=None, sha="abc",
                        now=T0, session="s1")
        row = effects.get(self.conn, k)
        self.assertEqual(row["state"], "requested")
        self.assertEqual(effects.executed_at(row), "2026-10-09T10:00:00.000000Z")
        types = [r[0] for r in self.conn.execute("SELECT type FROM events ORDER BY seq")]
        self.assertEqual(types, ["effect_requested", "effect_executed", "effect_requested"])


if __name__ == "__main__":
    unittest.main()
```

`tests/test_offlog.py`:

```python
import unittest

from tests.helpers import TempState
from tollgate_core import db, offlog


class OffLogTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_import_keeps_original_times_and_empties_log(self):
        (self.ts.dir / offlog.LOG_NAME).write_text(
            "2026-10-09T08:00:00.000000Z off 1791540000\n"
            "riga rovinata\n"
            "2026-10-09T09:00:00.000000Z on\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 2)
        rows = self.conn.execute("SELECT type, at, data FROM events ORDER BY seq").fetchall()
        self.assertEqual([(r[0], r[1]) for r in rows],
                         [("off", "2026-10-09T08:00:00.000000Z"),
                          ("on", "2026-10-09T09:00:00.000000Z")])
        self.assertIn('"until": 1791540000', rows[0][2])
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)

    def test_no_log(self):
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)


if __name__ == "__main__":
    unittest.main()
```

In `tests/test_dod.py` aggiungere (con gli import di `receipts` e dell'ora `T0` del file):

```python
class UncountedTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=1, level="L0", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _receipt(self, exit_code):
        receipts.add(self.conn, work=self.w, sha="h", command="verify", resolved_command="x",
                     exit_code=exit_code, tests_run=None, tests_skipped=None, duration=0.1,
                     log=None, produced_by="verify", state="uncounted", now=T0)

    def test_uncounted_ok_only_with_allow_no_tests_and_exit_zero(self):
        self._receipt(0)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=True,
                               required_commands=["verify"])[0]
        self.assertTrue(item.ok)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=False,
                               required_commands=["verify"])[0]
        self.assertFalse(item.ok)

    def test_uncounted_with_failure_is_red(self):
        self._receipt(1)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=True,
                               required_commands=["verify"])[0]
        self.assertFalse(item.ok)
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_scope tests.test_receipts tests.test_effects tests.test_offlog tests.test_dod -v`
Expected: FAIL con `ModuleNotFoundError` per `scope`, `receipts`, `effects`, `offlog`.

- [ ] **Step 3: `scope.py`**

```python
"""Scope del piano e registrazione del piano (spec 7.5, 6.2)."""
from __future__ import annotations

from . import clock, db, phases, tasks
from .events import record_event


def paths(conn, work: int) -> set[str]:
    return {r[0] for r in conn.execute("SELECT path FROM scope WHERE work = ?", (work,))}


def set_plan_path(conn, work: int, plan_path: str, *, now) -> None:
    """In L2 il piano si registra come percorso; scope e plan_sha arrivano con approve plan."""
    with db.tx(conn):
        conn.execute("UPDATE work_items SET plan_path = ?, updated = ? "
                     "WHERE id = ? AND plan_path IS NULL", (plan_path, clock.fmt(now), work))


def register_plan(conn, state, work: int, *, plan_path: str, plan_sha: str,
                  scope_paths: list[str], plan_tasks: list[tuple[int, list[str]]],
                  advance: bool, now, session=None) -> None:
    """Scope e task dal piano; una volta registrato lo scope non cresce (7.5)."""
    with db.tx(conn):
        row = phases.get_work(conn, work)
        if row["plan_sha"] is not None:
            raise ValueError("piano già registrato: per cambiarlo serve /tollgate:reopen plan")
        ts = clock.fmt(now)
        conn.execute("UPDATE work_items SET plan_path = ?, plan_sha = ?, updated = ? "
                     "WHERE id = ?", (plan_path, plan_sha, ts, work))
        for p in dict.fromkeys(scope_paths):
            conn.execute("INSERT INTO scope (work, path, origin, registered_at) "
                         "VALUES (?, ?, 'plan', ?)", (work, p, ts))
        for number, skills in plan_tasks:
            tasks.add_task(conn, work, number, source="plan", skills_required=skills, now=now,
                           session=session)
        record_event(conn, "scope_registered",
                     {"count": len(set(scope_paths)), "plan": plan_path, "plan_sha": plan_sha},
                     now=now, session=session, work=work)
    if advance:
        phases.set_phase(conn, state, work, "execution", "advance", now=now, session=session)
```

- [ ] **Step 4: `receipts.py`**

```python
"""Ricevute locali (spec 8.1): le producono solo verify e finish check."""
from __future__ import annotations

from . import clock, db
from .events import record_event

STATES = ("green", "red", "empty", "uncounted", "unverified")


def add(conn, *, work: int | None, sha: str, command: str, resolved_command: str | None,
        exit_code: int | None, tests_run: int | None, tests_skipped: int | None,
        duration: float | None, log: str | None, produced_by: str, state: str, now,
        session=None) -> int:
    if state not in STATES:
        raise ValueError(f"stato di ricevuta sconosciuto: {state}")
    with db.tx(conn):
        cur = conn.execute(
            "INSERT INTO receipts (work, sha, command, resolved_command, exit, tests_run, "
            "tests_skipped, duration, log, produced_by, state, at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (work, sha, command, resolved_command, exit_code, tests_run, tests_skipped,
             duration, log, produced_by, state, clock.fmt(now)))
        record_event(conn, "receipt", {"sha": sha, "command": command, "state": state,
                                       "tests_run": tests_run},
                     now=now, session=session, work=work)
        return cur.lastrowid


def latest(conn, work: int | None, sha: str) -> list:
    return conn.execute(
        "SELECT r.* FROM receipts r WHERE r.work IS ? AND r.sha = ? AND r.id = "
        "(SELECT max(id) FROM receipts x WHERE x.work IS r.work AND x.sha = r.sha "
        "AND x.command = r.command) ORDER BY r.command", (work, sha)).fetchall()


def any_since(conn, work: int, since: str) -> bool:
    return conn.execute("SELECT 1 FROM receipts WHERE work = ? AND at >= ? LIMIT 1",
                        (work, since)).fetchone() is not None
```

- [ ] **Step 5: `effects.py`**

```python
"""Effetti esterni come intenti (spec 8.5): veto, atto, una esecuzione, avviso se ripetuto."""
from __future__ import annotations

import hashlib
import json

from . import clock, db
from .events import record_event


def effect_key(command: str, work: int | None, sha: str | None) -> str:
    raw = f"{command}\0{'' if work is None else work}\0{sha or ''}"
    return hashlib.sha256(raw.encode("utf-8", "surrogateescape")).hexdigest()


def effect_id(key: str) -> str:
    return f"e-{key[:8]}"


def get(conn, key: str):
    return conn.execute("SELECT * FROM intents WHERE idempotency_key = ?",
                        (f"effect:{key}",)).fetchone()


def executed_at(row) -> str | None:
    return json.loads(row["data"] or "{}").get("executed_at") if row else None


def request(conn, *, key: str, command: str, work: int | None, sha: str | None, now,
            session=None) -> None:
    eid = effect_id(key)
    with db.tx(conn):
        row = get(conn, key)
        if row is None:
            data = {"id": eid, "command": command, "sha": sha}
            conn.execute("INSERT INTO intents (work, action, idempotency_key, data, state, at) "
                         "VALUES (?, 'effect', ?, ?, 'requested', ?)",
                         (work, f"effect:{key}", json.dumps(data), clock.fmt(now)))
        else:
            conn.execute("UPDATE intents SET state = 'requested' WHERE id = ?", (row["id"],))
        record_event(conn, "effect_requested", {"command_hash": key, "id": eid},
                     now=now, session=session, work=work)


def mark_executed(conn, *, key: str, act_id: str, now, session=None) -> None:
    with db.tx(conn):
        row = get(conn, key)
        if row is None:
            raise ValueError(f"effetto {effect_id(key)} mai richiesto")
        data = json.loads(row["data"] or "{}")
        data["executed_at"] = clock.fmt(now)
        data["act_id"] = act_id
        conn.execute("UPDATE intents SET state = 'executed', outcome = ?, data = ? WHERE id = ?",
                     (clock.fmt(now), json.dumps(data), row["id"]))
        record_event(conn, "effect_executed", {"command_hash": key, "id": effect_id(key),
                                               "act_id": act_id},
                     now=now, session=session, work=row["work"])
```

- [ ] **Step 6: `offlog.py`**

```python
"""Import in `events` delle accensioni e degli spegnimenti scritti dal wrapper (decisione 5)."""
from __future__ import annotations

import os
import re

from . import clock
from .events import record_event
from .paths import State

LOG_NAME = "off.log"
_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z) (off|on)(?: (\d+))?\s*$")


def import_log(conn, state: State) -> int:
    log = state.root / LOG_NAME
    work_file = state.root / f".{LOG_NAME}.{os.getpid()}"
    try:
        log.rename(work_file)   # atomico: due hook insieme non importano due volte
    except FileNotFoundError:
        return 0
    n = 0
    try:
        for line in work_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _LINE.match(line)
            if not m:
                continue
            data = {"until": int(m.group(3))} if m.group(3) else {}
            record_event(conn, m.group(2), data, now=clock.parse(m.group(1)))
            n += 1
    finally:
        work_file.unlink(missing_ok=True)
    return n
```

- [ ] **Step 7: `dod._receipt`**

In `bin/tollgate_core/dod.py`, `_receipt` legge anche l'uscita e accetta `uncounted` con `allow_no_tests` e uscita 0 (decisione 11):

```python
def _receipt(conn, work: int, head_sha: str, allow_no_tests: bool,
             required_commands: list[str]) -> tuple[bool, str]:
    if not required_commands:
        return False, "nessun comando richiesto"
    rows = conn.execute(
        "SELECT r.command, r.state, r.exit FROM receipts r WHERE r.work = ? AND r.sha = ? "
        "AND r.id = (SELECT max(id) FROM receipts x WHERE x.work = r.work AND x.sha = r.sha "
        "AND x.command = r.command) ORDER BY r.command", (work, head_sha)).fetchall()
    if not rows:
        return False, f"nessuna ricevuta su {head_sha}"

    def ok(r) -> bool:
        if r["state"] == "green":
            return True
        if allow_no_tests and r["state"] == "empty":
            return True
        return allow_no_tests and r["state"] == "uncounted" and r["exit"] == 0

    bad = [f"{r['command']}={r['state']}" for r in rows if not ok(r)]
    have = {r["command"] for r in rows}
    missing = [c for c in required_commands if c not in have]
    if missing:
        bad.append("mancano: " + ", ".join(missing))
    return (not bad), ", ".join(bad)
```

- [ ] **Step 8: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 9: Commit**

```bash
git add bin/tollgate_core/scope.py bin/tollgate_core/receipts.py bin/tollgate_core/effects.py bin/tollgate_core/offlog.py bin/tollgate_core/dod.py tests/test_scope.py tests/test_receipts.py tests/test_effects.py tests/test_offlog.py tests/test_dod.py
git commit -m "tollgate P2: scope, ricevute, effetti, registro di OFF; uncounted nella DoD"
```

---

### Task 4: Analisi: pattern, file protetti, profili, `plan-check`

**Files:**
- Create: `bin/tollgate_analysis/__init__.py`
- Create: `bin/tollgate_analysis/globs.py`
- Create: `bin/tollgate_analysis/protected.py`
- Create: `bin/tollgate_analysis/profiles.py`
- Create: `bin/tollgate_analysis/plan.py`
- Modify: `bin/tollgate_core/config.py` (avviso su `profiles.active`)
- Test: `tests/test_globs.py`, `tests/test_protected.py`, `tests/test_profiles.py`, `tests/test_plan.py`, `tests/test_analysis_isolation.py`, `tests/test_config.py`

**Interfaces:**
- Produces:
  - `globs.compile(pattern) -> re.Pattern`; `globs.match(pattern, path) -> bool`; `globs.match_any(patterns, path) -> bool`; `globs.is_pattern(s) -> bool`; `globs.literal_segments(pattern) -> int`.
  - `protected.TOLLGATE_FILES`, `protected.REPO_PROTECTED`; `protected.is_tollgate_file(rel) -> bool`; `protected.is_protected(rel: str | None, abs_path: Path, *, abs_roots: list[Path]) -> bool`.
  - `profiles.vertical_for(path, profiles: dict[str, dict]) -> str | None`; `profiles.active_profiles(files, profiles, always) -> list[str]`; `profiles.task_skills(files, profiles) -> list[str]`; `profiles.min_level(names, profiles) -> str`.
  - `plan.PlanTask(number, title, files, must_haves)`, `plan.MustHave(id, text, tests)`, `plan.PlanCheck(problems, warnings, scope, tasks, must_haves)` con `.ok`; `plan.check_plan(text, *, required_sections, max_scope_files, must_have_tests, level, profiles, active_always) -> PlanCheck`; `plan.TEST_SEP = "— test:"`.

- [ ] **Step 1: Test**

`tests/test_globs.py`:

```python
import unittest

from tollgate_analysis import globs


class GlobsTest(unittest.TestCase):
    def test_gitignore_dialect(self):
        cases = [
            ("**/__tests__/**", "src/__tests__/a.test.js", True),
            ("**/test_*.py", "test_x.py", True),
            ("**/test_*.py", "a/b/test_x.py", True),
            ("web/**", "web/a/b.ts", True),
            ("web/**", "x/web/a.ts", False),
            ("*.md", "docs/a.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/x.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/plans/x.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/plans/x.py", False),
            ("/tollgate.toml", "tollgate.toml", True),
            ("/tollgate.toml", "sub/tollgate.toml", False),
            (".github/workflows/tollgate-*.yml", ".github/workflows/tollgate-verdict.yml", True),
            (".github/workflows/tollgate-*.yml", ".github/workflows/ci.yml", False),
            ("reports/", "reports/junit.xml", True),
            ("**", "qualunque/cosa.txt", True),
            ("**/*.test.*", "src/a.test.ts", True),
            ("scripts/check*", "scripts/check-all.sh", True),
            ("src/[ab].py", "src/a.py", True),
            ("src/[!ab].py", "src/a.py", False),
        ]
        for pattern, path, expected in cases:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(globs.match(pattern, path), expected)

    def test_helpers(self):
        self.assertTrue(globs.is_pattern("src/*.py"))
        self.assertFalse(globs.is_pattern("src/a.py"))
        self.assertEqual(globs.literal_segments("web/admin/**"), 2)
        self.assertEqual(globs.literal_segments("**/*.ts"), 0)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_protected.py`:

```python
import unittest
from pathlib import Path

from tollgate_analysis import protected


class ProtectedTest(unittest.TestCase):
    def test_repo_files(self):
        roots = [Path("/stato"), Path("/home/u/.claude/plugins")]
        for rel in ["tollgate.toml", ".github/workflows/tollgate-gate.yml",
                    ".github/tollgate/cli/x.py", ".tollgate/waivers/7.toml",
                    "docs/superpowers/reviews/7/r.md", ".claude/settings.json",
                    ".claude/settings.local.json"]:
            with self.subTest(rel=rel):
                self.assertTrue(protected.is_protected(rel, Path("/r") / rel, abs_roots=roots))
        self.assertFalse(protected.is_protected("src/a.py", Path("/r/src/a.py"), abs_roots=roots))
        self.assertFalse(protected.is_protected("docs/superpowers/plans/p.md",
                                                Path("/r/docs/superpowers/plans/p.md"),
                                                abs_roots=roots))

    def test_absolute_roots(self):
        roots = [Path("/stato"), Path("/r/.git/hooks")]
        self.assertTrue(protected.is_protected(None, Path("/stato/tollgate.db"), abs_roots=roots))
        self.assertTrue(protected.is_protected(None, Path("/r/.git/hooks/pre-commit"),
                                               abs_roots=roots))
        self.assertFalse(protected.is_protected(None, Path("/altro/x"), abs_roots=roots))

    def test_tollgate_file(self):
        self.assertTrue(protected.is_tollgate_file("tollgate.toml"))
        self.assertFalse(protected.is_tollgate_file(".tollgate/waivers/7.toml"))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_profiles.py`:

```python
import unittest

from tollgate_analysis import profiles

PROFILES = {
    "web": {"kind": "vertical", "paths": ["web/**"], "skills": ["ui-ux-pro-max"],
            "min_level": "L0", "plan_sections": []},
    "admin": {"kind": "vertical", "paths": ["web/admin/**"], "skills": ["a", "b"],
              "min_level": "L1", "plan_sections": []},
    "api": {"kind": "vertical", "paths": ["api/**"], "skills": ["c", "d"],
            "min_level": "L2", "plan_sections": ["Contratti"]},
    "a11y": {"kind": "cross", "paths": ["web/**"], "skills": ["x"], "min_level": "L0",
             "plan_sections": []},
}


class ProfilesTest(unittest.TestCase):
    def test_most_specific_wins(self):
        self.assertEqual(profiles.vertical_for("web/admin/x.ts", PROFILES), "admin")
        self.assertEqual(profiles.vertical_for("web/x.ts", PROFILES), "web")
        self.assertIsNone(profiles.vertical_for("lib/x.ts", PROFILES))

    def test_tie_first_declared(self):
        p = {"uno": {"kind": "vertical", "paths": ["src/**"]},
             "due": {"kind": "vertical", "paths": ["src/**"]}}
        self.assertEqual(profiles.vertical_for("src/a", p), "uno")

    def test_active_and_skills(self):
        self.assertEqual(profiles.active_profiles(["web/a.ts"], PROFILES, ["api"]),
                         ["web", "api", "a11y"])
        self.assertEqual(profiles.task_skills(["web/admin/a.ts", "api/b.py"], PROFILES),
                         ["a", "b", "c", "d"])
        self.assertEqual(profiles.min_level(["web", "admin"], PROFILES), "L1")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_plan.py`:

```python
import unittest

from tollgate_analysis import plan

SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope",
            "Punti di arresto", "Rischi"]


def make(must_have="M1. Somma corretta — test: tests.test_a::test_sum", files=None,
         extra="", drop=None):
    files = files or ["- Create: `src/a.py`", "- Test: `tests/test_a.py:10-20`"]
    out = ["# Piano", ""]
    for s in SECTIONS:
        if s == drop:
            continue
        out.append(f"## {s}")
        if s == "Must-have":
            out.append(must_have)
        out.append("")
    out += ["### Task 1: Somma", "", "**Files:**", *files, "Must-have: M1", "",
            "```markdown", "## Finta sezione in un blocco di codice", "- Create: `x/finto.py`",
            "```", extra]
    return "\n".join(out)


def check(text, level="L1", profiles=None, max_scope=30):
    return plan.check_plan(text, required_sections=SECTIONS, max_scope_files=max_scope,
                           must_have_tests=True, level=level, profiles=profiles or {},
                           active_always=[])


class PlanCheckTest(unittest.TestCase):
    def test_complete_plan(self):
        r = check(make())
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.scope, ["src/a.py", "tests/test_a.py"])
        self.assertEqual(r.must_haves[0].tests, ["tests.test_a::test_sum"])
        self.assertEqual([t.number for t in r.tasks], [1])

    def test_missing_section(self):
        r = check(make(drop="Rischi"))
        self.assertFalse(r.ok)
        self.assertIn("## Rischi", " ".join(r.problems))

    def test_pattern_or_dir_rejected(self):
        for bad in ["- Modify: `src/*.py`", "- Create: `src/nuova/`"]:
            with self.subTest(bad=bad):
                self.assertFalse(check(make(files=[bad])).ok)

    def test_must_have_without_test(self):
        self.assertFalse(check(make(must_have="M1. Somma corretta")).ok)
        self.assertTrue(check(make(must_have="M1. Somma corretta"), level="L0").ok)

    def test_manual_test_allowed(self):
        self.assertTrue(check(make(must_have="M1. Colore giusto — test: manuale")).ok)

    def test_too_many_files(self):
        files = [f"- Create: `src/f{i}.py`" for i in range(4)]
        self.assertFalse(check(make(files=files), max_scope=3).ok)

    def test_unknown_must_have_reference(self):
        text = make().replace("Must-have: M1", "Must-have: M1, M9")
        self.assertFalse(check(text).ok)

    def test_more_than_three_skills_is_warning(self):
        prof = {"api": {"kind": "vertical", "paths": ["src/**"], "skills": ["a", "b", "c", "d"],
                        "plan_sections": []}}
        r = check(make(), profiles=prof)
        self.assertTrue(r.ok)
        self.assertTrue(any("4 skill" in w for w in r.warnings))

    def test_profile_sections_required(self):
        prof = {"api": {"kind": "vertical", "paths": ["src/**"], "skills": [],
                        "plan_sections": ["Contratti"]}}
        self.assertFalse(check(make(), profiles=prof).ok)

    def test_no_tasks(self):
        self.assertFalse(check("\n".join(f"## {s}" for s in SECTIONS)).ok)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_analysis_isolation.py`:

```python
import ast
import unittest

from tests.helpers import BIN

FORBIDDEN = ("tollgate_core", "tollgate_hooks", "tollgate_checks")


class IsolationTest(unittest.TestCase):
    def test_analysis_imports_only_stdlib_and_itself(self):
        for path in sorted((BIN / "tollgate_analysis").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for n in names:
                    with self.subTest(file=path.name, module=n):
                        self.assertFalse(n.split(".")[0] in FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
```

In `tests/test_config.py` aggiungere un test (usare il testo minimo che il file già usa negli altri test, con `[gate] mode = "protected"`):

```python
    def test_active_profile_not_declared_warns(self):
        cfg = config.load_config_text(
            'schema_version = 1\n[gate]\nmode = "protected"\n'
            '[profiles]\nactive = ["web"]\n')
        self.assertIn("profilo attivo non dichiarato: web", cfg.warnings)
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_globs tests.test_protected tests.test_profiles tests.test_plan tests.test_analysis_isolation tests.test_config -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_analysis'` e il test di config che non trova l'avviso.

- [ ] **Step 3: `__init__.py` e `globs.py`**

`bin/tollgate_analysis/__init__.py`:

```python
"""Analisi pure di tollgate: niente DB, niente rete, niente tollgate_core (usate anche dal gate)."""
```

`bin/tollgate_analysis/globs.py`:

```python
"""Pattern nel dialetto di .gitignore (spec 3.2), su percorsi relativi alla radice del repo."""
from __future__ import annotations

import re
from functools import lru_cache

_GLOB_CHARS = set("*?[")


def is_pattern(s: str) -> bool:
    return any(c in _GLOB_CHARS for c in s)


def literal_segments(pattern: str) -> int:
    return sum(1 for seg in pattern.strip("/").split("/") if seg and not is_pattern(seg))


@lru_cache(maxsize=1024)
def compile(pattern: str) -> re.Pattern:  # noqa: A001 - nome voluto, come re.compile
    p = pattern
    dir_only = p.endswith("/")
    p = p.rstrip("/")
    anchored = p.startswith("/") or "/" in p
    p = p.lstrip("/")
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif p.startswith("/**", i) and i + 3 == len(p):
            out.append("/.*")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "[":
            j = p.find("]", i + 1)
            if j == -1:
                out.append(re.escape("["))
                i += 1
            else:
                body = p[i + 1:j]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append("[" + body.replace("\\", "\\\\") + "]")
                i = j + 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    prefix = "" if anchored else "(?:.*/)?"
    suffix = "/.*" if dir_only else "(?:/.*)?"
    return re.compile("^" + prefix + "".join(out) + suffix + "$")


def match(pattern: str, path: str) -> bool:
    return compile(pattern).match(path[2:] if path.startswith("./") else path) is not None


def match_any(patterns, path: str) -> bool:
    return any(match(p, path) for p in patterns)
```

- [ ] **Step 4: `protected.py`**

```python
"""File di tollgate e file protetti (spec 0, 7.4)."""
from __future__ import annotations

from pathlib import Path

from . import globs

TOLLGATE_FILES = ["/tollgate.toml", ".github/workflows/tollgate-*.yml",
                  ".github/actions/tollgate-*/**", ".github/tollgate/**"]
REPO_PROTECTED = TOLLGATE_FILES + [
    ".tollgate/waivers/**", "docs/superpowers/reviews/**",
    ".claude/settings.json", ".claude/settings.local.json",
    ".git/hooks/**", ".git/config",
]


def is_tollgate_file(rel: str) -> bool:
    return globs.match_any(TOLLGATE_FILES, rel)


def is_protected(rel: str | None, abs_path: Path, *, abs_roots: list[Path]) -> bool:
    """`rel` è il percorso nel repo (None fuori da un repo); `abs_roots` sono cartelle o file
    protetti per percorso assoluto: cartella di stato, plugin installati, impostazioni utente,
    `.git/hooks` e `.git/config` della cartella comune di git."""
    if rel is not None and globs.match_any(REPO_PROTECTED, rel):
        return True
    p = Path(abs_path)
    return any(p == r or r in p.parents for r in abs_roots)
```

- [ ] **Step 5: `profiles.py`**

```python
"""Profili: verticale di un file, profili attivi, skill di un task (spec 6.3, 9.2, 11.4)."""
from __future__ import annotations

from . import globs

_LEVELS = ("L0", "L1", "L2")


def _score(path: str, patterns) -> int | None:
    scores = [globs.literal_segments(p) for p in patterns if globs.match(p, path)]
    return max(scores) if scores else None


def vertical_for(path: str, profiles: dict[str, dict]) -> str | None:
    """Vince il pattern con più segmenti letterali; a parità il primo dichiarato."""
    best, best_score = None, -1
    for name, prof in profiles.items():
        if prof.get("kind", "vertical") != "vertical":
            continue
        s = _score(path, prof.get("paths", []))
        if s is not None and s > best_score:
            best, best_score = name, s
    return best


def active_profiles(files, profiles: dict[str, dict], always) -> list[str]:
    files = list(files)
    return [name for name, prof in profiles.items()
            if name in always or any(globs.match_any(prof.get("paths", []), f) for f in files)]


def task_skills(files, profiles: dict[str, dict]) -> list[str]:
    skills: list[str] = []
    for f in files:
        name = vertical_for(f, profiles)
        if name:
            for s in profiles[name].get("skills", []):
                if s not in skills:
                    skills.append(s)
    return skills


def min_level(names, profiles: dict[str, dict]) -> str:
    level = "L0"
    for n in names:
        lv = profiles.get(n, {}).get("min_level", "L0")
        if lv in _LEVELS and _LEVELS.index(lv) > _LEVELS.index(level):
            level = lv
    return level
```

- [ ] **Step 6: `plan.py`**

```python
"""plan-check (spec 7.5): intestazioni, scope dai task, must-have legati ai test."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import globs, profiles as prof

TEST_SEP = "— test:"
SKILL_CAP = 3
_SECTION = re.compile(r"^## (.+?)\s*$")
_TASK = re.compile(r"^### Task (\d+)\b[:.]?\s*(.*)$")
_FILE = re.compile(r"^\s*[-*]\s*(Create|Modify|Test):\s*(.+?)\s*$")
_TASK_MH = re.compile(r"^\s*\**Must-have\**:\**\s*(.+?)\s*$")
_MH = re.compile(r"^\s*(?:[-*]\s*)?(M\d+)\.\s*(.+?)\s*$")
_RANGE = re.compile(r":\d+(?:-\d+)?$")
_TICK = re.compile(r"`([^`]+)`")


@dataclass
class PlanTask:
    number: int
    title: str
    files: list[str] = field(default_factory=list)
    must_haves: list[str] | None = None


@dataclass
class MustHave:
    id: str
    text: str
    tests: list[str]


@dataclass
class PlanCheck:
    problems: list[str]
    warnings: list[str]
    scope: list[str]
    tasks: list[PlanTask]
    must_haves: list[MustHave]

    @property
    def ok(self) -> bool:
        return not self.problems


def _file_value(raw: str) -> str:
    m = _TICK.search(raw)
    value = (m.group(1) if m else raw.split()[0]).strip()
    value = _RANGE.sub("", value)
    return value[2:] if value.startswith("./") else value


def _parse(text: str):
    sections: list[str] = []
    tasks: list[PlanTask] = []
    mh_lines: list[str] = []
    current_section, task = None, None
    fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = _SECTION.match(line)
        if m:
            current_section, task = m.group(1), None
            sections.append(current_section)
            continue
        m = _TASK.match(line)
        if m:
            task = PlanTask(int(m.group(1)), m.group(2).strip())
            tasks.append(task)
            continue
        if line.startswith("### "):
            task = None
            continue
        if task is not None:
            fm = _FILE.match(line)
            if fm:
                task.files.append(_file_value(fm.group(2)))
                continue
            mm = _TASK_MH.match(line)
            if mm:
                task.must_haves = [x.strip() for x in mm.group(1).split(",") if x.strip()]
                continue
        if current_section == "Must-have" and task is None:
            mh_lines.append(line)
    return sections, tasks, mh_lines


def _must_haves(lines: list[str]) -> list[MustHave]:
    out = []
    for line in lines:
        m = _MH.match(line)
        if not m:
            continue
        body = m.group(2)
        if TEST_SEP in body:
            text, tests = body.split(TEST_SEP, 1)
            ids = [t.strip().strip("`") for t in tests.split(",") if t.strip()]
        else:
            text, ids = body, []
        out.append(MustHave(m.group(1), text.strip(), ids))
    return out


def check_plan(text: str, *, required_sections, max_scope_files: int, must_have_tests: bool,
               level: str, profiles: dict[str, dict], active_always) -> PlanCheck:
    problems: list[str] = []
    warnings: list[str] = []
    sections, tasks, mh_lines = _parse(text)
    scope = list(dict.fromkeys(f for t in tasks for f in t.files))
    active = prof.active_profiles(scope, profiles, active_always)
    needed = list(required_sections) + [s for n in active
                                         for s in profiles[n].get("plan_sections", [])]
    for s in dict.fromkeys(needed):
        if s not in sections:
            problems.append(f"manca la sezione «## {s}»")
    if not tasks:
        problems.append("nessun task (intestazioni «### Task N»)")
    for f in scope:
        if globs.is_pattern(f) or f.endswith("/"):
            problems.append(f"pattern o cartella non ammessi nello scope: {f}")
    if len(scope) > max_scope_files:
        problems.append(f"scope di {len(scope)} file, oltre il massimo di {max_scope_files}")
    must_haves = _must_haves(mh_lines)
    if must_have_tests and level in ("L1", "L2"):
        if not must_haves:
            problems.append("nessun must-have nella sezione «## Must-have»")
        for mh in must_haves:
            if not mh.tests:
                problems.append(f"{mh.id} senza test: scrivi «{TEST_SEP} <classname::name>» "
                                f"oppure «{TEST_SEP} manuale»")
    known = {mh.id for mh in must_haves}
    for t in tasks:
        for ref in t.must_haves or []:
            if ref not in known:
                problems.append(f"task {t.number}: must-have {ref} inesistente")
        skills = prof.task_skills(t.files, profiles)
        if len(skills) > SKILL_CAP:
            warnings.append(f"task {t.number}: {len(skills)} skill dai profili (massimo "
                            f"{SKILL_CAP}): {', '.join(skills)}; il task va diviso")
    return PlanCheck(problems, warnings, scope, tasks, must_haves)
```

- [ ] **Step 7: Avviso su `profiles.active`**

In `bin/tollgate_core/config.py`, in `load_config_text`, subito prima di `if not data["gate"]["mode"]:`:

```python
    declared = {k for k in data["profiles"] if k != "active"}
    for name in data["profiles"]["active"]:
        if name not in declared:
            warnings.append(f"profilo attivo non dichiarato: {name}")
```

- [ ] **Step 8: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 9: Commit**

```bash
git add bin/tollgate_analysis tests/test_globs.py tests/test_protected.py tests/test_profiles.py tests/test_plan.py tests/test_analysis_isolation.py bin/tollgate_core/config.py tests/test_config.py
git commit -m "tollgate P2: analisi di pattern, file protetti, profili e plan-check"
```

---
### Task 5: Analisi: livello e JUnit

**Files:**
- Create: `bin/tollgate_analysis/level.py`
- Create: `bin/tollgate_analysis/junit.py`
- Test: `tests/test_level.py`, `tests/test_junit.py`

**Interfaces:**
- Consumes: `globs.match_any`.
- Produces:
  - `level.LEVELS`; `level.FileChange(path, added, removed, binary=False, status="M", old_path=None)` (le funzioni accettano qualunque oggetto con gli attributi `path`, `added`, `removed`, `binary`, come `git.Change` del Task 9); `level.max_level(*levels) -> str`; `level.sensitive_in(paths, sensitive_paths) -> list[str]`; `level.diff_level(changes, *, diff_bytes, sensitive_paths, l0_max_files, l0_max_lines, l0_max_bytes) -> str`; `level.labels_level(labels, sensitive_labels) -> str`; `level.next_level(*, current, computed, cap, cap_paths, sensitive_now) -> str`.
  - `junit.JunitError`; `junit.Junit(total, skipped, failed, ids_run, ids_skipped, ids_failed)`; `junit.parse_junit(data: bytes) -> Junit`.

- [ ] **Step 1: Test**

`tests/test_level.py`:

```python
import unittest

from tollgate_analysis.level import FileChange, diff_level, labels_level, max_level, next_level

KW = dict(sensitive_paths=["**/migrations/**", "**/auth/**"], l0_max_files=2,
          l0_max_lines=50, l0_max_bytes=4000)


class LevelTest(unittest.TestCase):
    def test_small_diff_is_l0(self):
        ch = [FileChange("src/a.py", 10, 2)]
        self.assertEqual(diff_level(ch, diff_bytes=500, **KW), "L0")
        self.assertEqual(diff_level([], diff_bytes=0, **KW), "L0")

    def test_thresholds(self):
        self.assertEqual(diff_level([FileChange(f"f{i}", 1, 0) for i in range(3)],
                                    diff_bytes=10, **KW), "L1")
        self.assertEqual(diff_level([FileChange("a", 40, 11)], diff_bytes=10, **KW), "L1")
        self.assertEqual(diff_level([FileChange("a", 1, 0)], diff_bytes=4001, **KW), "L1")

    def test_binary_is_not_l0(self):
        self.assertEqual(diff_level([FileChange("img.png", 0, 0, binary=True)],
                                    diff_bytes=10, **KW), "L1")

    def test_sensitive_is_l2(self):
        self.assertEqual(diff_level([FileChange("db/migrations/1.sql", 1, 0)],
                                    diff_bytes=10, **KW), "L2")

    def test_labels_and_max(self):
        self.assertEqual(labels_level(["bug", "security"], ["security"]), "L2")
        self.assertEqual(labels_level(["bug"], ["security"]), "L0")
        self.assertEqual(max_level("L0", "L2", "L1"), "L2")

    def test_cap_holds_until_new_sensitive_path(self):
        self.assertEqual(next_level(current="L1", computed="L2", cap="L1",
                                    cap_paths=["src/auth/a.py"], sensitive_now=["src/auth/a.py"]),
                         "L1")
        self.assertEqual(next_level(current="L1", computed="L2", cap="L1",
                                    cap_paths=["src/auth/a.py"],
                                    sensitive_now=["src/auth/a.py", "src/auth/b.py"]), "L2")
        self.assertEqual(next_level(current="L2", computed="L0", cap=None, cap_paths=[],
                                    sensitive_now=[]), "L2")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_junit.py`:

```python
import unittest

from tollgate_analysis.junit import JunitError, parse_junit

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites><testsuite name="s">
  <testcase classname="src/a.test.ts" name="g &gt; passes"/>
  <testcase classname="src/a.test.ts" name="g &gt; skipped"><skipped/></testcase>
  <testcase classname="tests.test_x" name="test_fail"><failure message="x"/></testcase>
  <testcase classname="tests.test_x" name="test_err"><error message="y"/></testcase>
</testsuite></testsuites>"""


class JunitTest(unittest.TestCase):
    def test_counts_and_ids(self):
        j = parse_junit(XML)
        self.assertEqual((j.total, j.skipped, j.failed), (4, 1, 2))
        self.assertEqual(j.ids_run, ["src/a.test.ts::g > passes", "tests.test_x::test_fail",
                                     "tests.test_x::test_err"])
        self.assertEqual(j.ids_skipped, ["src/a.test.ts::g > skipped"])
        self.assertEqual(j.ids_failed, ["tests.test_x::test_fail", "tests.test_x::test_err"])

    def test_entities_rejected(self):
        bad = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><testsuite/>'
        with self.assertRaises(JunitError):
            parse_junit(bad)

    def test_malformed(self):
        with self.assertRaises(JunitError):
            parse_junit(b"<testsuite><testcase")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_level tests.test_junit -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `level.py`**

```python
"""Livello del lavoro (spec 5): il massimo tra diff, etichette e scelta dell'utente."""
from __future__ import annotations

from dataclasses import dataclass

from . import globs

LEVELS = ("L0", "L1", "L2")


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    removed: int
    binary: bool = False
    status: str = "M"
    old_path: str | None = None


def max_level(*levels: str) -> str:
    return max(levels, key=LEVELS.index) if levels else "L0"


def sensitive_in(paths, sensitive_paths) -> list[str]:
    return sorted({p for p in paths if globs.match_any(sensitive_paths, p)})


def diff_level(changes, *, diff_bytes: int, sensitive_paths, l0_max_files: int,
               l0_max_lines: int, l0_max_bytes: int) -> str:
    changes = list(changes)
    paths = [c.path for c in changes] + [c.old_path for c in changes if c.old_path]
    if sensitive_in(paths, sensitive_paths):
        return "L2"
    lines = sum(c.added + c.removed for c in changes)
    if (len(changes) > l0_max_files or lines > l0_max_lines or diff_bytes > l0_max_bytes
            or any(c.binary for c in changes)):
        return "L1"
    return "L0"


def labels_level(labels, sensitive_labels) -> str:
    return "L2" if set(labels) & set(sensitive_labels) else "L0"


def next_level(*, current: str, computed: str, cap: str | None, cap_paths,
               sensitive_now) -> str:
    """Lo script alza soltanto; il tetto vale finché non compare un percorso sensibile nuovo."""
    if cap and set(sensitive_now) <= set(cap_paths):
        computed = min(computed, cap, key=LEVELS.index)
    return max_level(current, computed)
```

- [ ] **Step 4: `junit.py`**

```python
"""Lettura del report JUnit (spec 7.5, 8.1): identificativi classname::name, niente entità."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_DANGER = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


class JunitError(ValueError):
    pass


@dataclass
class Junit:
    total: int = 0
    skipped: int = 0
    failed: int = 0
    ids_run: list[str] = field(default_factory=list)
    ids_skipped: list[str] = field(default_factory=list)
    ids_failed: list[str] = field(default_factory=list)


def parse_junit(data: bytes) -> Junit:
    if _DANGER.search(data):
        raise JunitError("XML con DOCTYPE o entità: report rifiutato")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise JunitError(f"XML non valido: {e}") from e
    j = Junit()
    for case in root.iter("testcase"):
        tid = f"{case.get('classname', '')}::{case.get('name', '')}"
        j.total += 1
        if case.find("skipped") is not None:
            j.skipped += 1
            j.ids_skipped.append(tid)
            continue
        j.ids_run.append(tid)
        if case.find("failure") is not None or case.find("error") is not None:
            j.failed += 1
            j.ids_failed.append(tid)
    return j
```

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_analysis/level.py bin/tollgate_analysis/junit.py tests/test_level.py tests/test_junit.py
git commit -m "tollgate P2: analisi del livello e lettura sicura del JUnit"
```

---

### Task 6: Analisi: test-guard

**Files:**
- Create: `bin/tollgate_analysis/scan.py`
- Create: `bin/tollgate_analysis/testids.py`
- Create: `bin/tollgate_analysis/testguard.py`
- Test: `tests/test_testids.py`, `tests/test_testguard.py`

**Interfaces:**
- Consumes: `globs.match_any`.
- Produces:
  - `scan.js_tokens(text)` (generatore di `(tipo, valore)` con tipo `str`, `id`, `p`); `scan.js_code(text) -> str` (codice senza commenti, stringhe come `S`); `scan.py_code(text) -> str | None`.
  - `testids.language(path) -> str | None` (`js`, `py`, `go`, `java`, `rust`); `testids.test_ids(text, rel, *, js_form) -> tuple[dict[str, str], set[str]] | None` (locali attivi → identificativo completo; locali saltati; `None` se il file non si legge).
  - `testguard.DEFAULT_TEST_GLOBS`; `testguard.Violation(kind, path, detail, waiver_type, ids=())`; `testguard.Change(status, path, old_path, base_text, head_text, binary=False)`; `testguard.GuardConfig(test_globs, fixture_globs, ci_globs, verification_globs, verification_watch, skip_markers=(), assert_markers=(), js_form="vitest")`; `testguard.check(changes, cfg) -> GuardResult(violations, watched)`.
  - Tipi di violazione (`kind` → `waiver_type`): `test_deleted` → `test`; `test_id_missing` → `test`; `asserts_decreased` → `test`; `skip_added` → `test`; `unparsable` → `test`; `fixture_changed` → `test`; `ci_changed` → `ci`; `threshold_lowered` → `threshold`; `verification_changed` → `command`. Il Task 15 aggiunge `out_of_scope` → `scope` con la stessa classe.

- [ ] **Step 1: Test**

`tests/test_testids.py`:

```python
import unittest

from tollgate_analysis import scan, testids

JS = """
import { describe, it, expect } from 'vitest'
// it('commentato', () => {})
describe('format', () => {
  it('handles UTC', () => { expect(1).toBe(1) })
  describe("nested", () => {
    test(`deep`, () => {})
  })
  it.skip('saltato', () => {})
})
it('top', () => {})
"""

PY = '''
import pytest, unittest

def test_a():
    assert 1

@pytest.mark.skip
def test_skipped():
    pass

class TestGroup:
    def test_b(self):
        assert "assert dentro una stringa"

class Other(unittest.TestCase):
    def test_c(self):
        self.assertEqual(1, 1)
'''


class TestIdsTest(unittest.TestCase):
    def test_js_vitest_and_jest_forms(self):
        active, skipped = testids.test_ids(JS, "src/date.test.ts", js_form="vitest")
        self.assertEqual(set(active.values()), {
            "src/date.test.ts::format > handles UTC", "src/date.test.ts::format > nested > deep",
            "src/date.test.ts::top"})
        self.assertEqual(skipped, {"format > saltato"})
        active, _ = testids.test_ids(JS, "src/date.test.ts", js_form="jest")
        self.assertIn("src/date.test.ts::format handles UTC", active.values())

    def test_python_pytest_form(self):
        active, skipped = testids.test_ids(PY, "tests/test_x.py", js_form="vitest")
        self.assertEqual(set(active.values()), {"tests.test_x::test_a",
                                                "tests.test_x.TestGroup::test_b",
                                                "tests.test_x.Other::test_c"})
        self.assertEqual(skipped, {"test_skipped"})
        self.assertIn("TestGroup::test_b", active)

    def test_python_syntax_error(self):
        self.assertIsNone(testids.test_ids("def test_a(:\n", "tests/test_x.py", js_form="vitest"))

    def test_go(self):
        active, _ = testids.test_ids("func TestSum(t *testing.T) {}\n", "pkg/sum_test.go",
                                     js_form="vitest")
        self.assertEqual(set(active.values()), {"pkg::TestSum"})

    def test_code_without_comments_and_strings(self):
        self.assertNotIn("commentato", scan.js_code("// it('commentato')\nx = 'testo'"))
        self.assertNotIn("dentro", scan.py_code("x = 'assert dentro'  # assert commento\n"))
        self.assertIsNone(scan.py_code("x = '\n"))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_testguard.py`:

```python
import unittest

from tollgate_analysis.testguard import (DEFAULT_TEST_GLOBS, Change, GuardConfig, check)

CFG = GuardConfig(test_globs=DEFAULT_TEST_GLOBS, fixture_globs=["**/fixtures/**/*.json"],
                  ci_globs=[".github/workflows/**"],
                  verification_globs=["**/vitest.config.*", "**/conftest.py"],
                  verification_watch=["**/package.json", "**/pyproject.toml"])

JS_BASE = "describe('a', () => {\n  it('x', () => { expect(1).toBe(1) })\n  it('y', () => {})\n})\n"
PY_BASE = "def test_a():\n    assert 1\n\ndef test_b():\n    assert 2\n"


def kinds(changes):
    return sorted(v.kind for v in check(changes, CFG).violations)


class TestGuardTest(unittest.TestCase):
    def test_deleted_test_file(self):
        self.assertEqual(kinds([Change("D", "src/__tests__/a.test.js", None, JS_BASE, None)]),
                         ["test_deleted"])

    def test_xdescribe_added(self):
        head = JS_BASE.replace("describe(", "xdescribe(")
        self.assertIn("skip_added", kinds([Change("M", "src/a.test.ts", None, JS_BASE, head)]))

    def test_pytest_skip_added(self):
        head = PY_BASE.replace("    assert 2", "    pytest.skip('no')\n    assert 2")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["skip_added"])

    def test_pytest_mark_skip_added(self):
        head = "import pytest\n" + PY_BASE.replace("def test_b", "@pytest.mark.skip\ndef test_b")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["skip_added", "test_id_missing"])

    def test_assertion_replaced_by_comment(self):
        head = PY_BASE.replace("    assert 2", "    # assert 2\n    pass")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["asserts_decreased"])

    def test_missing_id(self):
        head = "def test_a():\n    assert 1\n    assert 2\n"
        v = check([Change("M", "tests/test_x.py", None, PY_BASE, head)], CFG).violations
        self.assertEqual([(x.kind, x.ids) for x in v],
                         [("test_id_missing", ("tests.test_x::test_b",))])

    def test_process_exit_is_fine(self):
        head = JS_BASE.replace("expect(1).toBe(1)", "expect(1).toBe(1); process.exit(0)")
        self.assertEqual(kinds([Change("M", "src/a.test.ts", None, JS_BASE, head)]), [])

    def test_rename_with_same_tests(self):
        self.assertEqual(kinds([Change("R", "tests/test_y.py", "tests/test_x.py",
                                       PY_BASE, PY_BASE)]), [])

    def test_ci_fixture_verification_threshold(self):
        changes = [
            Change("M", ".github/workflows/ci.yml", None, "a", "b"),
            Change("M", "tests/fixtures/data/x.json", None, "{}", "{\"a\": 1}"),
            Change("M", "vitest.config.ts", None, "lines: 90", "lines: 80"),
        ]
        self.assertEqual(kinds(changes), ["ci_changed", "fixture_changed", "threshold_lowered",
                                          "verification_changed"])

    def test_watch_is_info_only(self):
        r = check([Change("M", "package.json", None, "{}", "{\"x\": 1}")], CFG)
        self.assertEqual((r.violations, r.watched), ([], ["package.json"]))

    def test_new_file_with_skip(self):
        head = "def test_a():\n    pytest.skip('x')\n"
        self.assertEqual(kinds([Change("A", "tests/test_new.py", None, None, head)]),
                         ["skip_added"])

    def test_unparsable_head(self):
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, "def (:\n")]),
                         ["unparsable"])

    def test_binary_and_latin1_do_not_crash(self):
        r = check([Change("M", "tests/data.bin", None, None, None, binary=True),
                   Change("M", "tests/test_l.py", None, "x = 'caff\xe8'\n", "x = 'caff\xe8'\n")],
                  CFG)
        self.assertEqual(r.violations, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_testids tests.test_testguard -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `scan.py`**

```python
"""Lettura di codice senza commenti e stringhe (JS/TS e simili, Python)."""
from __future__ import annotations

import io
import tokenize


def js_tokens(text: str):
    """Token di linguaggi con la sintassi del C: ('str', valore), ('id', nome), ('p', carattere)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "'\"`":
            j, buf = i + 1, []
            while j < n and text[j] != c:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                buf.append(text[j])
                j += 1
            yield ("str", "".join(buf))
            i = j + 1
            continue
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (text[j].isalnum() or text[j] in "_$"):
                j += 1
            yield ("id", text[i:j])
            i = j
            continue
        if not c.isspace():
            yield ("p", c)
        i += 1


def js_code(text: str) -> str:
    return " ".join("S" if k == "str" else v for k, v in js_tokens(text))


def py_code(text: str) -> str | None:
    """Codice Python senza commenti né stringhe; None se il file non si legge."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            name = tokenize.tok_name[tok.type]
            if name == "ERRORTOKEN" and not tok.string.isspace():
                return None   # Python 3.11 non solleva su una stringa non chiusa
            if "STRING" in name or name in ("COMMENT", "NL", "NEWLINE", "INDENT", "DEDENT",
                                            "ENDMARKER"):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return " ".join(out)
```

- [ ] **Step 4: `testids.py`**

```python
"""Identificativi dei test per analisi statica, nella forma del JUnit di ogni strumento (7.5)."""
from __future__ import annotations

import ast
import posixpath
import re

from .scan import js_tokens

JS_EXT = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts")
_GROUPS = {"describe", "suite", "context", "xdescribe"}
_CASES = {"it", "test", "xit", "xtest"}
_SKIP_MODS = {"skip", "todo", "fixme"}
_GO_TEST = re.compile(r"^func\s+(Test\w+)\s*\(", re.MULTILINE)


def language(path: str) -> str | None:
    if path.endswith(JS_EXT):
        return "js"
    if path.endswith(".py"):
        return "py"
    if path.endswith(".go"):
        return "go"
    if path.endswith((".java", ".kt")):
        return "java"
    if path.endswith(".rs"):
        return "rust"
    return None


def _js(text: str, rel: str, joiner: str):
    toks = list(js_tokens(text))
    active: dict[str, str] = {}
    skipped: set[str] = set()
    frames: list[tuple[str, int, bool]] = []
    depth, i = 0, 0
    while i < len(toks):
        kind, val = toks[i]
        if kind == "p":
            if val == "{":
                depth += 1
            elif val == "}":
                depth -= 1
                while frames and frames[-1][1] >= depth:
                    frames.pop()
            i += 1
            continue
        if kind == "id" and (val in _GROUPS or val in _CASES):
            j, mods = i + 1, []
            while j + 1 < len(toks) and toks[j] == ("p", ".") and toks[j + 1][0] == "id":
                mods.append(toks[j + 1][1])
                j += 2
            if j + 1 < len(toks) and toks[j] == ("p", "(") and toks[j + 1][0] == "str":
                title = toks[j + 1][1]
                skip = (val.startswith("x") or any(m in _SKIP_MODS for m in mods)
                        or any(f[2] for f in frames))
                if val in _GROUPS:
                    frames.append((title, depth, skip))
                else:
                    local = joiner.join([f[0] for f in frames] + [title])
                    if skip:
                        skipped.add(local)
                    else:
                        active[local] = f"{rel}::{local}"
                i = j + 2
                continue
        i += 1
    return active, skipped


def _is_skip(decorators) -> bool:
    return any(re.search(r"skip|xfail", ast.unparse(d)) for d in decorators)


def _py(text: str, rel: str):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    module = rel[:-3].replace("/", ".")
    active: dict[str, str] = {}
    skipped: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            if _is_skip(node.decorator_list):
                skipped.add(node.name)
            else:
                active[node.name] = f"{module}::{node.name}"
        elif isinstance(node, ast.ClassDef):
            bases = {ast.unparse(b) for b in node.bases}
            if not (node.name.startswith("Test") or any(b.endswith("TestCase") for b in bases)):
                continue
            cls_skip = _is_skip(node.decorator_list)
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith("test"):
                    local = f"{node.name}::{m.name}"
                    if cls_skip or _is_skip(m.decorator_list):
                        skipped.add(local)
                    else:
                        active[local] = f"{module}.{node.name}::{m.name}"
    return active, skipped


def _go(text: str, rel: str):
    pkg = posixpath.dirname(rel) or "."
    return {name: f"{pkg}::{name}" for name in _GO_TEST.findall(text)}, set()


def test_ids(text: str, rel: str, *, js_form: str):
    lang = language(rel)
    if lang == "js":
        return _js(text, rel, " > " if js_form == "vitest" else " ")
    if lang == "py":
        return _py(text, rel)
    if lang == "go":
        return _go(text, rel)
    return {}, set()
```

- [ ] **Step 5: `testguard.py`**

```python
"""test-guard (spec 8.2): test tolti, identificativi mancanti, asserzioni, salti, CI e soglie."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import globs
from .scan import js_code, py_code
from .testids import language, test_ids

DEFAULT_TEST_GLOBS = ("**/__tests__/**", "**/test/**", "**/tests/**", "**/e2e/**",
                      "**/*_test.py", "**/test_*.py", "**/*.test.*", "**/*.spec.*",
                      "**/*_test.go", "**/src/test/**")
_ASSERTS = {
    "js": [r"\bexpect\s*\(", r"\bassert\w*\b", r"\.\s*should\b"],
    "py": [r"\bassert\w*", r"\bpytest\s*\.\s*raises\b"],
    "go": [r"\bt\s*\.\s*(?:Error|Errorf|Fatal|Fatalf)\b", r"\b(?:assert|require)\s*\.\s*\w+"],
    "java": [r"\bassert\w*"], "rust": [r"\bassert\w*"],
}
_SKIPS = {
    "js": [r"\bxit\b", r"\bxdescribe\b", r"\bxtest\b", r"\.\s*skip\b", r"\.\s*only\b",
           r"\.\s*todo\b", r"\.\s*fixme\b", r"\.\s*skipIf\b", r"\.\s*runIf\s*\(\s*false\s*\)",
           r"\.\s*fails\b"],
    "py": [r"\bpytest\s*\.\s*skip\s*\(", r"\bpytest\s*\.\s*mark\s*\.\s*skip\w*", r"\bxfail\b",
           r"\bunittest\s*\.\s*skip\w*", r"\bskipIf\b", r"\bskipUnless\b"],
    "go": [r"\bt\s*\.\s*Skip\w*"],
    "java": [r"@\s*Disabled\b", r"@\s*Ignore\b"],
    "rust": [r"#\s*\[\s*ignore\s*\]"],
}
_THRESH = re.compile(r"(?i)\b(branches|functions|lines|statements|fail[_-]under|"
                     r"cov-fail-under|minimum_coverage|threshold)\b[\"']?\s*[:=]?\s*[\"']?"
                     r"(\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class Violation:
    kind: str
    path: str
    detail: str
    waiver_type: str
    ids: tuple = ()


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None
    base_text: str | None
    head_text: str | None
    binary: bool = False


@dataclass(frozen=True)
class GuardConfig:
    test_globs: tuple | list
    fixture_globs: tuple | list
    ci_globs: tuple | list
    verification_globs: tuple | list
    verification_watch: tuple | list
    skip_markers: tuple | list = ()
    assert_markers: tuple | list = ()
    js_form: str = "vitest"


@dataclass
class GuardResult:
    violations: list[Violation] = field(default_factory=list)
    watched: list[str] = field(default_factory=list)


def _code(text: str | None, lang: str) -> str | None:
    if text is None:
        return ""
    return py_code(text) if lang == "py" else js_code(text)


def _literal(marker: str) -> str:
    rx = re.escape(marker)
    if marker[:1].isalnum() or marker[:1] == "_":
        rx = r"\b" + rx
    if marker[-1:].isalnum() or marker[-1:] == "_":
        rx += r"\b"
    return rx


def _count(code: str, patterns) -> int:
    return sum(len(re.findall(p, code)) for p in patterns)


def _thresholds(text: str | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, val in _THRESH.findall(text or ""):
        k = key.lower().replace("-", "_")
        out[k] = min(out.get(k, float("inf")), float(val))
    return out


def _test_file(c: Change, cfg: GuardConfig, out: list[Violation]) -> None:
    lang = language(c.path if c.status != "D" else (c.old_path or c.path))
    if lang is None:
        return
    old = c.old_path or c.path
    if c.status == "D":
        base = test_ids(c.base_text or "", old, js_form=cfg.js_form)
        ids = tuple(sorted(base[0].values())) if base else ()
        out.append(Violation("test_deleted", old, "file di test cancellato", "test", ids))
        return
    head = test_ids(c.head_text or "", c.path, js_form=cfg.js_form)
    if head is None:
        out.append(Violation("unparsable", c.path, "file di test non leggibile", "test"))
        return
    if c.base_text is not None and c.status != "A":
        base = test_ids(c.base_text, old, js_form=cfg.js_form)
        if base is not None:
            missing = tuple(sorted(full for local, full in base[0].items()
                                   if local not in head[0]))
            if missing:
                out.append(Violation("test_id_missing", c.path,
                                     "test della base assenti o saltati: " + ", ".join(missing),
                                     "test", missing))
    base_code, head_code = _code(c.base_text, lang), _code(c.head_text, lang)
    if base_code is None or head_code is None:
        return
    asserts = _ASSERTS[lang] + [_literal(m) for m in cfg.assert_markers]
    if c.status != "A" and _count(head_code, asserts) < _count(base_code, asserts):
        out.append(Violation("asserts_decreased", c.path, "asserzioni diminuite", "test"))
    skips = _SKIPS[lang] + [_literal(m) for m in cfg.skip_markers]
    if _count(head_code, skips) > _count(base_code, skips):
        out.append(Violation("skip_added", c.path, "marcatori di salto aggiunti", "test"))


def check(changes, cfg: GuardConfig) -> GuardResult:
    r = GuardResult()
    for c in changes:
        paths = [p for p in (c.path, c.old_path) if p]
        if c.binary:
            if c.status == "D" and globs.match_any(cfg.test_globs, paths[-1]) \
                    and language(paths[-1]):
                r.violations.append(Violation("test_deleted", paths[-1],
                                              "file di test cancellato", "test"))
        elif any(globs.match_any(cfg.test_globs, p) for p in paths):
            _test_file(c, cfg, r.violations)
        if any(globs.match_any(cfg.ci_globs, p) for p in paths):
            r.violations.append(Violation("ci_changed", c.path, "CI modificata", "ci"))
        if any(globs.match_any(cfg.fixture_globs, p) for p in paths):
            r.violations.append(Violation("fixture_changed", c.path,
                                          "snapshot o fixture aggiornati", "test"))
        verification = any(globs.match_any(cfg.verification_globs, p) for p in paths)
        watched = any(globs.match_any(cfg.verification_watch, p) for p in paths)
        if verification:
            r.violations.append(Violation("verification_changed", c.path,
                                          "configurazione di test o copertura modificata",
                                          "command"))
        if watched:
            r.watched.append(c.path)
        if (verification or watched) and not c.binary and c.base_text and c.head_text:
            base_t, head_t = _thresholds(c.base_text), _thresholds(c.head_text)
            lowered = [k for k in base_t if k in head_t and head_t[k] < base_t[k]]
            if lowered:
                r.violations.append(Violation("threshold_lowered", c.path,
                                              "soglie abbassate: " + ", ".join(sorted(lowered)),
                                              "threshold"))
    return r
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK. Se `test_pytest_mark_skip_added` fallisce perché l'ordine dei `kind` differisce, il test usa `sorted`: correggere il codice, non il test.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_analysis/scan.py bin/tollgate_analysis/testids.py bin/tollgate_analysis/testguard.py tests/test_testids.py tests/test_testguard.py
git commit -m "tollgate P2: test-guard con identificativi statici per linguaggio"
```

---

### Task 7: Analisi: comandi Bash

**Files:**
- Create: `bin/tollgate_analysis/bash.py`
- Test: `tests/test_bash.py`

**Interfaces:**
- Produces:
  - `bash.BashParseError`; `bash.Cmd(argv, cwd, env, redirects, nested=False)`; `bash.parse(command: str, cwd: str) -> list[Cmd]` (solleva `BashParseError`).
  - `bash.git_call(cmd) -> tuple[str | None, list[str], str | None]` (sottocomando, argomenti, `-C`); `bash.effective_dir(cmd) -> str`.
  - `bash.is_push(cmd)`, `bash.push_is_force(cmd)`, `bash.push_targets(cmd) -> list[str]`, `bash.is_commit(cmd)`, `bash.commit_all(cmd)`, `bash.is_gh_pr_create(cmd)`, `bash.branch_change(cmd) -> str | None`, `bash.checkout_args(cmd) -> list[str]`, `bash.destructive(cmd) -> str | None`, `bash.rm_rf_targets(cmd) -> list[str]`, `bash.write_targets(cmd) -> list[str]`, `bash.writes(cmd) -> bool`, `bash.is_claude(cmd)`, `bash.is_tollgate_hook(cmd)`, `bash.uses_tollgate_bin(cmd, plugin_bin: str) -> bool`, `bash.merge_args(cmd) -> list[str]`, `bash.worktree_op(cmd)`, `bash.branch_deletes(cmd) -> list[str]`.
  - `bash.EffectsCfg(commands=(), project_scripts=(), allow=())`; `bash.normalized(cmd) -> str`; `bash.effect_reason(cmd, cfg) -> str | None`; `bash.script_path(cmd) -> str | None` (percorso assoluto normalizzato dello script eseguito); `bash.text_danger(raw) -> str | None`.

- [ ] **Step 1: Test**

`tests/test_bash.py`:

```python
import unittest

from tollgate_analysis import bash

CWD = "/r/wt"


def cmds(text, cwd=CWD):
    return bash.parse(text, cwd)


def one(text):
    out = cmds(text)
    return out[-1]


class ParseTest(unittest.TestCase):
    def test_chain_and_cd(self):
        out = cmds("cd /r/main && git status; ls")
        self.assertEqual([c.argv[0] for c in out], ["cd", "git", "ls"])
        self.assertEqual(out[1].cwd, "/r/main")

    def test_git_c(self):
        c = one("git -C ../main commit -am x")
        self.assertEqual(bash.git_call(c)[0], "commit")
        self.assertEqual(bash.effective_dir(c), "/r/main")
        self.assertTrue(bash.commit_all(c))

    def test_redirects_and_env(self):
        c = one("FOO=1 echo x > src/a.py 2>&1")
        self.assertEqual(c.env, {"FOO": "1"})
        self.assertEqual(c.redirects, ["src/a.py"])
        self.assertEqual(bash.write_targets(c), ["src/a.py"])

    def test_heredoc_body_ignored(self):
        out = cmds("cat > notes.txt <<'EOF'\ngit push --force\nEOF\necho ok")
        self.assertEqual([c.argv[0] for c in out], ["cat", "echo"])
        self.assertEqual(out[0].redirects, ["notes.txt"])

    def test_nested_shell_and_substitution(self):
        out = cmds("bash -c 'git push origin main'")
        self.assertTrue(any(bash.is_push(c) and c.nested for c in out))
        out = cmds("echo $(gh pr create --fill)")
        self.assertTrue(any(bash.is_gh_pr_create(c) for c in out))

    def test_wrappers_stripped(self):
        self.assertEqual(one("env A=1 sudo git push").argv[:2], ["git", "push"])

    def test_unparsable_falls_back_to_text(self):
        with self.assertRaises(bash.BashParseError):
            cmds("echo 'non chiuso")
        self.assertIsNotNone(bash.text_danger("echo 'x; git push --force"))
        self.assertIsNone(bash.text_danger("echo 'ciao"))


class ClassifyTest(unittest.TestCase):
    def test_push(self):
        self.assertTrue(bash.push_is_force(one("git push -f origin tg/1-x")))
        self.assertTrue(bash.push_is_force(one("git push origin +tg/1-x")))
        self.assertEqual(bash.push_targets(one("git push origin HEAD:refs/heads/main")), ["main"])
        self.assertEqual(bash.push_targets(one("git push")), [])

    def test_branch_change(self):
        for text in ["git switch -c altro", "git checkout -B altro", "git branch -m nuovo",
                     "git switch main"]:
            with self.subTest(text=text):
                self.assertIsNotNone(bash.branch_change(one(text)))
        self.assertIsNone(bash.branch_change(one("git checkout -- src/a.py")))
        self.assertEqual(bash.checkout_args(one("git checkout altro")), ["altro"])

    def test_destructive(self):
        self.assertIsNotNone(bash.destructive(one("git reset --hard HEAD~1")))
        self.assertIsNotNone(bash.destructive(one("git commit --no-verify -m x")))
        self.assertEqual(bash.rm_rf_targets(one("rm -rf /tmp/x build")), ["/tmp/x", "/r/wt/build"])
        self.assertEqual(bash.rm_rf_targets(one("rm -r x")), [])

    def test_writes(self):
        self.assertEqual(bash.write_targets(one("sed -i 's/a/b/' src/a.py")), ["src/a.py"])
        self.assertEqual(bash.write_targets(one("cp a.txt dest/b.txt")), ["dest/b.txt"])
        self.assertEqual(bash.write_targets(one("echo x | tee -a out.txt")), ["out.txt"])
        self.assertTrue(bash.writes(one("git add -A")))
        self.assertFalse(bash.writes(one("git status")))

    def test_claude_and_tollgate(self):
        self.assertTrue(bash.is_claude(one("claude -p ciao")))
        self.assertTrue(bash.is_claude(one("npx @anthropic-ai/claude-code -p x")))
        self.assertTrue(bash.is_tollgate_hook(one("/p/bin/tollgate hook PreToolUse")))
        self.assertFalse(bash.is_tollgate_hook(one("/p/bin/tollgate verify")))

    def test_worktree_merge_branch_delete(self):
        self.assertEqual(bash.worktree_op(one("git worktree add ../x -b tg/2-y")),
                         ("add", "/r/x", "tg/2-y"))
        self.assertEqual(bash.worktree_op(one("git worktree remove ../x")), ("remove", "/r/x", None))
        self.assertEqual(bash.merge_args(one("git merge --no-ff tg/1-x")), ["tg/1-x"])
        self.assertEqual(bash.branch_deletes(one("git branch -D tg/1-x")), ["tg/1-x"])


class EffectsTest(unittest.TestCase):
    CFG = bash.EffectsCfg(commands=["make prod*"], project_scripts=["deploy"],
                          allow=["kubectl get *"])

    def eff(self, text):
        return bash.effect_reason(one(text), self.CFG)

    def test_effects(self):
        for text in ["ssh host ls", "docker push img", "terraform apply", "npm publish",
                     "curl -X POST https://x", "curl -d a=1 https://x", "wget --post-data=a https://x",
                     "gh pr edit 3 --title x", "gh api -X PATCH repos/o/r", "gh api repos/o/r -f a=b",
                     "gh api graphql -f query='mutation { x }'", "gh issue create -t x",
                     "npm run deploy", "make production", "supabase db push",
                     "wrangler deploy", "gh release create v1"]:
            with self.subTest(text=text):
                self.assertIsNotNone(self.eff(text))

    def test_not_effects(self):
        for text in ["curl https://x", "gh pr view 3", "gh api repos/o/r",
                     "gh api graphql -f query='query { x }'", "kubectl get pods", "npm test",
                     "git push", "supabase status"]:
            with self.subTest(text=text):
                self.assertIsNone(self.eff(text))

    def test_script_path(self):
        self.assertEqual(bash.script_path(one("./scripts/x.sh a")), "/r/wt/scripts/x.sh")
        self.assertEqual(bash.script_path(one("python3 tools/y.py")), "/r/wt/tools/y.py")
        self.assertIsNone(bash.script_path(one("python3 -m pytest")))
        self.assertIsNone(bash.script_path(one("ls -la")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_bash -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `bash.py`**

```python
"""Lettura dei comandi Bash e classificazione per le regole di 7.4 e gli effetti di 8.5.
Best effort: ciò che sfugge lo prende PostToolUse Bash (spec 7.2)."""
from __future__ import annotations

import fnmatch
import os
import re
import shlex
from dataclasses import dataclass, field


class BashParseError(ValueError):
    pass


@dataclass
class Cmd:
    argv: list[str]
    cwd: str
    env: dict[str, str] = field(default_factory=dict)
    redirects: list[str] = field(default_factory=list)
    nested: bool = False


_OPS = {";", "&&", "||", "|", "&", "|&", ";;", "(", ")"}
_REDIR_OUT = {">", ">>", ">|", "&>", "&>>"}
_REDIR_SKIP = {"<", "<<<", "<&", ">&", "<>"}
_WRAPPERS = {"sudo", "nohup", "time", "command", "exec", "nice", "env", "xargs", "timeout",
             "stdbuf", "builtin"}
_SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_SUBST = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")


def _strip_heredocs(text: str) -> str:
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in _HEREDOC.finditer(line):
            delim = m.group(2)
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1
    return "\n".join(out)


def _norm(cwd: str, path: str) -> str:
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))


def _unwrap(argv: list[str], env: dict) -> list[str]:
    while argv and os.path.basename(argv[0]) in _WRAPPERS:
        argv = argv[1:]
        while argv and (argv[0].startswith("-") or _ASSIGN.match(argv[0])
                        or argv[0].replace(".", "", 1).isdigit()):
            if _ASSIGN.match(argv[0]):
                k, _, v = argv[0].partition("=")
                env[k] = v
            argv = argv[1:]
    return argv


def parse(command: str, cwd: str) -> list[Cmd]:
    text = _strip_heredocs(command.replace("\\\n", " "))
    extra: list[Cmd] = []
    for m in _SUBST.finditer(text):
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        for c in parse(inner, cwd):
            c.nested = True
            extra.append(c)
    lex = shlex.shlex(text.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        tokens = list(lex)
    except ValueError as e:
        raise BashParseError(str(e)) from e
    out: list[Cmd] = []
    seg: list[str] = []

    def flush():
        nonlocal cwd, seg
        if not seg:
            return
        env: dict[str, str] = {}
        redirects: list[str] = []
        argv: list[str] = []
        i = 0
        while i < len(seg):
            t = seg[i]
            if t in _REDIR_OUT or (t[:-1].isdigit() and t[-1:] == ">"):
                if i + 1 < len(seg):
                    redirects.append(seg[i + 1])
                i += 2
                continue
            if t in _REDIR_SKIP or t == "<<":
                i += 2
                continue
            if not argv and _ASSIGN.match(t):
                k, _, v = t.partition("=")
                env[k] = v
            else:
                argv.append(t)
            i += 1
        argv = _unwrap(argv, env)
        seg = []
        if not argv and not redirects:
            return
        cmd = Cmd(argv, cwd, env, redirects)
        out.append(cmd)
        if argv and argv[0] in ("cd", "pushd"):
            cwd = _norm(cwd, argv[1] if len(argv) > 1 else "~")
        elif argv and os.path.basename(argv[0]) in _SHELLS and "-c" in argv:
            k = argv.index("-c")
            if k + 1 < len(argv):
                for c in parse(argv[k + 1], cmd.cwd):
                    c.nested = True
                    out.append(c)
        elif argv and argv[0] == "eval" and len(argv) > 1:
            for c in parse(" ".join(argv[1:]), cmd.cwd):
                c.nested = True
                out.append(c)

    for t in tokens:
        if t in _OPS:
            flush()
        else:
            seg.append(t)
    flush()
    return out + extra


# --- git -------------------------------------------------------------------------------------

_GIT_OPT_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
_GIT_MUTATING = {"add", "commit", "checkout", "switch", "reset", "restore", "rm", "mv", "merge",
                 "rebase", "cherry-pick", "revert", "am", "stash", "apply", "pull", "clean",
                 "tag", "branch", "worktree", "push"}


def git_call(cmd: Cmd):
    a = cmd.argv
    if not a or os.path.basename(a[0]) != "git":
        return None, [], None
    i, c_dir = 1, None
    while i < len(a) and a[i].startswith("-"):
        if a[i] == "-C" and i + 1 < len(a):
            c_dir = a[i + 1]
            i += 2
        elif a[i] in _GIT_OPT_ARG:
            i += 2
        else:
            i += 1
    return (a[i] if i < len(a) else None), a[i + 1:], c_dir


def effective_dir(cmd: Cmd) -> str:
    _, _, c_dir = git_call(cmd)
    return _norm(cmd.cwd, c_dir) if c_dir else cmd.cwd


def _positional(args: list[str]) -> list[str]:
    return [x for x in args if not x.startswith("-")]


def is_push(cmd: Cmd) -> bool:
    return git_call(cmd)[0] == "push"


def push_is_force(cmd: Cmd) -> bool:
    sub, args, _ = git_call(cmd)
    if sub != "push":
        return False
    if any(x in ("-f", "--mirror") or x.startswith("--force") for x in args):
        return True
    return any(x.startswith("+") for x in _positional(args)[1:])


def push_targets(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    if sub != "push":
        return []
    out = []
    for spec in _positional(args)[1:]:
        dst = spec.split(":")[-1].lstrip("+")
        out.append(dst.removeprefix("refs/heads/"))
    return out


def is_commit(cmd: Cmd) -> bool:
    return git_call(cmd)[0] == "commit"


def commit_all(cmd: Cmd) -> bool:
    sub, args, _ = git_call(cmd)
    if sub != "commit":
        return False
    return any(x in ("-a", "--all") or (x.startswith("-") and not x.startswith("--")
                                         and "a" in x[1:]) for x in args)


def is_gh_pr_create(cmd: Cmd) -> bool:
    return cmd.argv[:3] == ["gh", "pr", "create"]


def checkout_args(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    if sub != "checkout" or "--" in args:
        return []
    return _positional(args)


def branch_change(cmd: Cmd) -> str | None:
    sub, args, _ = git_call(cmd)
    if sub == "switch":
        return "git switch"
    if sub == "checkout" and any(x in ("-b", "-B", "--orphan") for x in args):
        return "git checkout -b/-B"
    if sub == "branch" and any(x in ("-m", "-M", "--move") for x in args):
        return "git branch -m/-M"
    return None


def rm_rf_targets(cmd: Cmd) -> list[str]:
    a = cmd.argv
    if not a or os.path.basename(a[0]) != "rm":
        return []
    flags = "".join(x[1:] for x in a[1:] if x.startswith("-") and not x.startswith("--"))
    long = {x for x in a[1:] if x.startswith("--")}
    recursive = "r" in flags or "R" in flags or "--recursive" in long
    force = "f" in flags or "--force" in long
    if not (recursive and force):
        return []
    return [_norm(cmd.cwd, x) for x in _positional(a[1:])]


def destructive(cmd: Cmd) -> str | None:
    sub, args, _ = git_call(cmd)
    if sub == "reset" and "--hard" in args:
        return "git reset --hard"
    if sub is not None and "--no-verify" in args:
        return "--no-verify"
    return None


def write_targets(cmd: Cmd) -> list[str]:
    a = cmd.argv
    out = list(cmd.redirects)
    if not a:
        return out
    base = os.path.basename(a[0])
    pos = _positional(a[1:])
    if base == "tee":
        out += pos
    elif base in ("sed", "perl") and any(x == "-i" or x.startswith("-i") or x == "--in-place"
                                          for x in a[1:]):
        has_e = any(x in ("-e", "--expression") for x in a[1:])
        out += pos if has_e else pos[1:]
    elif base in ("cp", "mv", "install", "ln") and len(pos) >= 2:
        out.append(pos[-1])
    elif base in ("rm", "touch", "mkdir", "rmdir", "truncate", "chmod", "chown"):
        out += pos[1:] if base in ("chmod", "chown") else pos
    elif base == "dd":
        out += [x[3:] for x in a[1:] if x.startswith("of=")]
    return out


def writes(cmd: Cmd) -> bool:
    return bool(write_targets(cmd)) or git_call(cmd)[0] in _GIT_MUTATING


def is_claude(cmd: Cmd) -> bool:
    a = cmd.argv
    if not a:
        return False
    base = os.path.basename(a[0])
    if base in ("claude", "claude-code"):
        return True
    return base in ("npx", "bunx", "pnpx", "pnpm", "yarn", "npm") and any(
        "@anthropic-ai/claude-code" in x for x in a[1:])


def is_tollgate_hook(cmd: Cmd) -> bool:
    a = cmd.argv
    for i, x in enumerate(a[:2]):
        if os.path.basename(x) == "tollgate":
            return len(a) > i + 1 and a[i + 1] == "hook"
    return False


def uses_tollgate_bin(cmd: Cmd, plugin_bin: str) -> bool:
    a = cmd.argv
    target = os.path.realpath(plugin_bin)
    cands = a[:1] + (a[1:2] if a and os.path.basename(a[0]).startswith("python") else [])
    return any(os.path.realpath(_norm(cmd.cwd, x)) == target for x in cands)


def merge_args(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    return _positional(args) if sub == "merge" else []


def worktree_op(cmd: Cmd):
    sub, args, _ = git_call(cmd)
    if sub != "worktree" or not args:
        return None
    op, rest = args[0], args[1:]
    branch = None
    if "-b" in rest or "-B" in rest:
        k = rest.index("-b") if "-b" in rest else rest.index("-B")
        branch = rest[k + 1] if k + 1 < len(rest) else None
        rest = rest[:k] + rest[k + 2:]
    pos = _positional(rest)
    if op == "add" and pos:
        return ("add", _norm(cmd.cwd, pos[0]), branch or (pos[1] if len(pos) > 1 else None))
    if op == "remove" and pos:
        return ("remove", _norm(cmd.cwd, pos[0]), None)
    return None


def branch_deletes(cmd: Cmd) -> list[str]:
    sub, args, _ = git_call(cmd)
    if sub != "branch" or not any(x in ("-d", "-D", "--delete") for x in args):
        return []
    return _positional(args)


# --- effetti esterni (8.5) --------------------------------------------------------------------

@dataclass(frozen=True)
class EffectsCfg:
    commands: tuple | list = ()
    project_scripts: tuple | list = ()
    allow: tuple | list = ()


_DEFAULT_EFFECTS = [("ssh",), ("scp",), ("rsync",), ("psql",), ("docker", "push"),
                    ("kubectl",), ("terraform", "apply"), ("aws",), ("gcloud",), ("az",),
                    ("vercel",), ("netlify",), ("firebase", "deploy"), ("wrangler", "deploy"),
                    ("wrangler", "publish"), ("npm", "publish"), ("pnpm", "publish"),
                    ("yarn", "publish")]
_SUPABASE_WRITE = {"db", "functions", "secrets", "link", "migration", "storage", "projects",
                   "orgs", "branches"}
_SUPABASE_READ = {"list", "diff", "dump", "ls", "download", "--help", "-h"}
_GH_WRITE = {("pr", "create"), ("pr", "edit"), ("pr", "review"), ("pr", "close"),
             ("pr", "merge"), ("workflow", "run"), ("issue", "edit"), ("issue", "close"),
             ("issue", "create")}
_GH_WRITE_ANY = {"release", "secret", "project"}
_INTERPRETERS = {"bash", "sh", "zsh", "python", "python3", "node", "ruby", "perl", "deno",
                 "bun", "tsx", "ts-node", "php"}


def normalized(cmd: Cmd) -> str:
    return " ".join(cmd.argv)


def _matches(patterns, text: str) -> bool:
    return any(text == p or text.startswith(p + " ") or fnmatch.fnmatchcase(text, p)
               for p in patterns)


def _curl_write(a: list[str]) -> bool:
    for i, x in enumerate(a):
        if x in ("-X", "--request") and i + 1 < len(a) and a[i + 1].upper() != "GET":
            return True
        if x.startswith("-X") and len(x) > 2 and x[2:].upper() != "GET":
            return True
        if x in ("-d", "-F", "-T", "--json", "--form", "--upload-file") or \
                x.startswith(("--data", "--form", "-d")):
            return True
    return False


def _wget_write(a: list[str]) -> bool:
    for x in a:
        if x.startswith(("--post-data", "--post-file", "--body-data", "--body-file")):
            return True
        if x.startswith("--method") and x.split("=", 1)[-1].upper() != "GET":
            return True
    return False


def _gh_write(a: list[str]) -> bool:
    if len(a) < 2:
        return False
    if a[1] in _GH_WRITE_ANY:
        return True
    if len(a) >= 3 and (a[1], a[2]) in _GH_WRITE:
        return True
    if a[1] == "api":
        rest = a[2:]
        for i, x in enumerate(rest):
            if x in ("-X", "--method") and i + 1 < len(rest) and rest[i + 1].upper() != "GET":
                return True
            if x.startswith("--method=") and x.split("=", 1)[1].upper() != "GET":
                return True
        graphql = "graphql" in rest
        fields = [rest[i + 1] for i, x in enumerate(rest[:-1])
                  if x in ("-f", "-F", "--field", "--raw-field")]
        if graphql:
            return any(re.search(r"\bmutation\b", f) for f in fields) or "--input" in rest
        return bool(fields) or "--input" in rest
    return False


def effect_reason(cmd: Cmd, cfg: EffectsCfg) -> str | None:
    a = cmd.argv
    if not a:
        return None
    text = normalized(cmd)
    if _matches(cfg.allow, text):
        return None
    if _matches(cfg.commands, text):
        return "comando dichiarato in [external_effects] commands"
    base = os.path.basename(a[0])
    for prefix in _DEFAULT_EFFECTS:
        if [base] + a[1:len(prefix)] == list(prefix):
            return f"effetto esterno: {' '.join(prefix)}"
    if base == "supabase" and len(a) > 1 and a[1] in _SUPABASE_WRITE \
            and not (len(a) > 2 and a[2] in _SUPABASE_READ):
        return "effetto esterno: supabase in scrittura"
    if base in ("npm", "pnpm", "yarn", "bun") and len(a) > 1:
        script = a[2] if a[1] == "run" and len(a) > 2 else a[1]
        if script in cfg.project_scripts:
            return f"script del progetto: {script}"
    if base in ("make", "just") and any(x in cfg.project_scripts for x in a[1:]):
        return "script del progetto"
    if base == "curl" and _curl_write(a[1:]):
        return "curl con metodo diverso da GET o con dati"
    if base == "wget" and _wget_write(a[1:]):
        return "wget con metodo diverso da GET o con dati"
    if base == "gh" and _gh_write(a):
        return "gh in scrittura"
    return None


def script_path(cmd: Cmd) -> str | None:
    a = cmd.argv
    if not a:
        return None
    if "/" in a[0] and os.path.basename(a[0]) not in _INTERPRETERS:
        return _norm(cmd.cwd, a[0])
    if os.path.basename(a[0]) in _INTERPRETERS:
        rest = a[1:]
        if any(x in ("-c", "-m", "-e") for x in rest[:1]):
            return None
        pos = [x for x in rest if not x.startswith("-")]
        if pos and ("/" in pos[0] or re.search(r"\.(sh|py|js|mjs|ts|rb|pl|php)$", pos[0])):
            return _norm(cmd.cwd, pos[0])
    return None


_TEXT_DANGER = [
    (re.compile(r"\bgit\b[^;&|]*\bpush\b"), "git push"),
    (re.compile(r"--force\b"), "--force"),
    (re.compile(r"\breset\s+--hard\b"), "reset --hard"),
    (re.compile(r"--no-verify\b"), "--no-verify"),
    (re.compile(r"TOLLGATE_"), "TOLLGATE_"),
    (re.compile(r"(^|[\s;&|(])claude(\s|$)"), "claude"),
]


def text_danger(raw: str) -> str | None:
    """Ripiego per i comandi che shlex non legge: si cerca per testo."""
    for rx, label in _TEXT_DANGER:
        if rx.search(raw):
            return label
    return None
```

- [ ] **Step 4: Verificare che passi**

Run: `python3 -B -m unittest tests.test_bash -v`
Expected: PASS. Se un caso fallisce, correggere `bash.py` (non il test) e registrare nel ledger un caso che si è deciso di non coprire solo con una `Ruling:`.

- [ ] **Step 5: Suite e commit**

Run: `tests/run`
Expected: OK.

```bash
git add bin/tollgate_analysis/bash.py tests/test_bash.py
git commit -m "tollgate P2: lettura e classificazione dei comandi Bash"
```

---

### Task 8: Analisi: deroghe e report dell'implementatore

**Files:**
- Create: `bin/tollgate_analysis/waivers.py`
- Create: `bin/tollgate_analysis/report.py`
- Test: `tests/test_waivers.py`, `tests/test_report.py`

**Interfaces:**
- Consumes: `globs.match`, `testguard.Violation`.
- Produces:
  - `waivers.TYPES`; `waivers.Waiver(id, type, file, pattern, tests, choice, why, cost, declared_by)`; `waivers.WaiverFile(issue, branch, waivers, schema_version=1)`; `waivers.parse(text) -> WaiverFile` (`ValueError` se non valido); `waivers.dumps(wf) -> str`; `waivers.next_id(wf) -> str`; `waivers.status(wf, *, approved_ids, sensitive) -> dict[str, str]` (`valid` | `pending`); `waivers.covers(w, v) -> bool`; `waivers.unresolved(violations, wf) -> list[Violation]`; `waivers.path_for(issue) -> str` (`.tollgate/waivers/<N>.toml`).
  - `report.STATUSES`, `report.REQUIRED`; `report.ImplReport(status, data, missing, unknown_status)` con `.valid`; `report.parse_report(text) -> ImplReport`; `report.is_turn_cut(tool_response) -> bool`; `report.transcript_tokens(path) -> int`.

- [ ] **Step 1: Test**

`tests/test_waivers.py`:

```python
import unittest

from tollgate_analysis import waivers
from tollgate_analysis.testguard import Violation


def wf(*items):
    return waivers.WaiverFile(issue=7, branch="tg/7-x", waivers=list(items))


def w(n, type_, file=None, pattern=None, tests=()):
    return waivers.Waiver(f"w-7-{n}", type_, file, pattern, list(tests), "scelta", "perché",
                          "costo", "agent")


class WaiversTest(unittest.TestCase):
    def test_roundtrip_with_tricky_text(self):
        f = wf(waivers.Waiver("w-7-1", "scope", "src/a.py", None, [], 'virgolette " e \\',
                              "```\n@utente", "c", "agent"))
        back = waivers.parse(waivers.dumps(f))
        self.assertEqual(back, f)

    def test_parse_rejects_bad(self):
        with self.assertRaises(ValueError):
            waivers.parse('schema_version = 1\nissue = 7\nbranch = "b"\n[[waiver]]\nid = "x"\n'
                          'type = "boh"\nfile = "a"\nchoice = ""\nwhy = ""\ncost = ""\n')

    def test_next_id(self):
        self.assertEqual(waivers.next_id(wf()), "w-7-1")
        self.assertEqual(waivers.next_id(wf(w(1, "scope", "a"), w(4, "scope", "b"))), "w-7-5")

    def test_status_rules(self):
        f = wf(w(1, "scope", "a"), w(2, "scope", "b"), w(3, "scope", "c"),
               w(4, "test", "t", tests=["x"]), w(5, "command", "cfg"),
               w(6, "scope", pattern="src/**"), w(7, "scope", "auth/x"))
        st = waivers.status(f, approved_ids={"w-7-4"}, sensitive=lambda p: p.startswith("auth/"))
        self.assertEqual(st, {"w-7-1": "valid", "w-7-2": "valid", "w-7-3": "pending",
                              "w-7-4": "valid", "w-7-5": "valid", "w-7-6": "pending",
                              "w-7-7": "pending"})

    def test_covers(self):
        v_scope = Violation("out_of_scope", "src/x.py", "", "scope")
        v_ids = Violation("test_id_missing", "t.py", "", "test", ("t::a", "t::b"))
        self.assertTrue(waivers.covers(w(1, "scope", "src/x.py"), v_scope))
        self.assertTrue(waivers.covers(w(1, "scope", pattern="src/**"), v_scope))
        self.assertFalse(waivers.covers(w(1, "test", "src/x.py"), v_scope))
        self.assertFalse(waivers.covers(w(1, "test", "t.py", tests=["t::a"]), v_ids))
        self.assertTrue(waivers.covers(w(1, "test", "t.py", tests=["t::a", "t::b"]), v_ids))
        self.assertEqual(waivers.unresolved([v_scope, v_ids], wf(w(1, "scope", "src/x.py"))),
                         [v_ids])
        self.assertEqual(waivers.unresolved([v_scope], None), [v_scope])


if __name__ == "__main__":
    unittest.main()
```

`tests/test_report.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import report

GOOD = {"v": 1, "task": 2, "status": "DONE", "done": "fatto", "tests": "verify green",
        "files": ["src/a.py"], "must_have": ["M1"], "concerns": "", "left": "",
        "size_reason": None}
SAMPLES = json.loads((ROOT / "spikes/fixtures/hook-inputs/samples.json").read_text())


class ReportTest(unittest.TestCase):
    def test_last_json_block(self):
        text = "Ecco il lavoro.\n```json\n" + json.dumps(GOOD) + "\n```\n"
        r = report.parse_report(text)
        self.assertTrue(r.valid)
        self.assertEqual(r.status, "DONE")
        r = report.parse_report("prima {\"a\": 1} poi " + json.dumps(GOOD))
        self.assertTrue(r.valid)

    def test_missing_fields(self):
        bad = dict(GOOD)
        del bad["left"], bad["concerns"]
        r = report.parse_report(json.dumps(bad))
        self.assertFalse(r.valid)
        self.assertEqual(r.missing, ["concerns", "left"])
        self.assertFalse(report.parse_report("nessun json").valid)
        self.assertFalse(report.parse_report(None).valid)

    def test_unknown_status_counts_as_done(self):
        r = report.parse_report(json.dumps(dict(GOOD, status="FINITO")))
        self.assertEqual((r.status, r.unknown_status, r.valid), ("DONE", True, True))

    def test_turn_cut_from_real_sample(self):
        cut = SAMPLES["PostToolUse-Agent-maxturns-cut"]["tool_response"]
        normal = SAMPLES["PostToolUse-Agent-foreground-manual"]["tool_response"]
        self.assertTrue(report.is_turn_cut(cut))
        self.assertFalse(report.is_turn_cut(normal))
        fake = dict(normal, content=[{"type": "text",
                                      "text": "NOTE: this agent stopped at its 2-turn limit"}])
        self.assertFalse(report.is_turn_cut(fake))

    def test_transcript_tokens(self):
        lines = [
            {"type": "assistant", "message": {"id": "m1", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 1000, "output_tokens": 3}}},
            {"type": "assistant", "message": {"id": "m1", "usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 1000, "output_tokens": 3}}},
            {"type": "user", "message": {"content": "x"}},
            "riga non json",
            {"type": "assistant", "message": {"id": "m2", "usage": {"input_tokens": 1,
                                                                     "output_tokens": 1}}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for l in lines:
                f.write((l if isinstance(l, str) else json.dumps(l)) + "\n")
        try:
            self.assertEqual(report.transcript_tokens(f.name), 20)
        finally:
            Path(f.name).unlink()
        self.assertEqual(report.transcript_tokens("/non/esiste.jsonl"), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_waivers tests.test_report -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `waivers.py`**

```python
"""Deroghe in .tollgate/waivers/<N>.toml (spec 8.3, 18.2)."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from typing import Callable

from . import globs

TYPES = ("scope", "test", "ci", "threshold", "command")
_ID = re.compile(r"^w-(\d+)-(\d+)$")
IMMEDIATE_SCOPE = 2


@dataclass
class Waiver:
    id: str
    type: str
    file: str | None
    pattern: str | None
    tests: list[str]
    choice: str
    why: str
    cost: str
    declared_by: str = "agent"


@dataclass
class WaiverFile:
    issue: int
    branch: str
    waivers: list[Waiver] = field(default_factory=list)
    schema_version: int = 1


def path_for(issue: int) -> str:
    return f".tollgate/waivers/{issue}.toml"


def _str(d: dict, k: str, required=True) -> str | None:
    v = d.get(k)
    if v is None and not required:
        return None
    if not isinstance(v, str):
        raise ValueError(f"campo {k} mancante o non stringa")
    return v


def parse(text: str) -> WaiverFile:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"TOML non valido: {e}") from e
    if raw.get("schema_version") != 1:
        raise ValueError("schema_version mancante o non supportata")
    issue, branch = raw.get("issue"), raw.get("branch")
    if not isinstance(issue, int) or isinstance(issue, bool) or not isinstance(branch, str):
        raise ValueError("issue o branch non validi")
    out = []
    for item in raw.get("waiver", []):
        if not isinstance(item, dict):
            raise ValueError("[[waiver]] non è una tabella")
        wid, type_ = _str(item, "id"), _str(item, "type")
        if not _ID.match(wid) or type_ not in TYPES:
            raise ValueError(f"deroga non valida: {wid} {type_}")
        file, pattern = _str(item, "file", False), _str(item, "pattern", False)
        if (file is None) == (pattern is None):
            raise ValueError(f"{wid}: serve file oppure pattern")
        tests = item.get("tests", [])
        if not isinstance(tests, list) or not all(isinstance(t, str) for t in tests):
            raise ValueError(f"{wid}: tests deve essere una lista di stringhe")
        out.append(Waiver(wid, type_, file, pattern, tests, _str(item, "choice"),
                          _str(item, "why"), _str(item, "cost"),
                          _str(item, "declared_by", False) or "agent"))
    return WaiverFile(issue, branch, out, 1)


def _q(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def dumps(wf: WaiverFile) -> str:
    lines = [f"schema_version = {wf.schema_version}", f"issue = {wf.issue}",
             f"branch = {_q(wf.branch)}"]
    for w in wf.waivers:
        lines += ["", "[[waiver]]", f"id = {_q(w.id)}", f"type = {_q(w.type)}"]
        lines.append(f"file = {_q(w.file)}" if w.file is not None
                     else f"pattern = {_q(w.pattern)}")
        lines.append("tests = [" + ", ".join(_q(t) for t in w.tests) + "]")
        for k in ("choice", "why", "cost", "declared_by"):
            lines.append(f"{k} = {_q(getattr(w, k))}")
    return "\n".join(lines) + "\n"


def next_id(wf: WaiverFile) -> str:
    nums = [int(m.group(2)) for w in wf.waivers if (m := _ID.match(w.id))]
    return f"w-{wf.issue}-{max(nums, default=0) + 1}"


def status(wf: WaiverFile, *, approved_ids, sensitive: Callable[[str], bool]) -> dict[str, str]:
    """Le prime 2 deroghe scope su file non sensibili valgono subito; command vale subito;
    il resto (test, ci, threshold, pattern, scope oltre la seconda) aspetta approve waiver."""
    out: dict[str, str] = {}
    scope_seen = 0
    for w in wf.waivers:
        immediate = False
        if w.type == "scope" and w.pattern is None and not sensitive(w.file):
            scope_seen += 1
            immediate = scope_seen <= IMMEDIATE_SCOPE
        elif w.type == "command" and w.pattern is None:
            immediate = True
        out[w.id] = "valid" if (immediate or w.id in approved_ids) else "pending"
    return out


def covers(w: Waiver, v) -> bool:
    if w.type != v.waiver_type:
        return False
    ok = globs.match(w.pattern, v.path) if w.pattern is not None else w.file == v.path
    if not ok:
        return False
    if v.kind == "test_id_missing":
        return set(v.ids) <= set(w.tests)
    return True


def unresolved(violations, wf: WaiverFile | None) -> list:
    if wf is None:
        return list(violations)
    return [v for v in violations if not any(covers(w, v) for w in wf.waivers)]
```

- [ ] **Step 4: `report.py`**

```python
"""Report dell'implementatore (spec 18.5), taglio di maxTurns (6.3), token dal transcript."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

STATUSES = ("DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT")
REQUIRED = ("v", "task", "status", "done", "tests", "files", "concerns", "left")
CUT_PREFIX = "NOTE: this agent stopped at its"


@dataclass
class ImplReport:
    status: str
    data: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    unknown_status: bool = False

    @property
    def valid(self) -> bool:
        return not self.missing


def _last_json(text: str) -> dict | None:
    dec = json.JSONDecoder()
    pos = text.rfind("{")
    while pos >= 0:
        try:
            obj, _ = dec.raw_decode(text, pos)
            if isinstance(obj, dict) and "status" in obj:
                return obj
        except json.JSONDecodeError:
            pass
        pos = text.rfind("{", 0, pos)
    return None


def parse_report(text: str | None) -> ImplReport:
    data = _last_json(text or "")
    if data is None:
        return ImplReport("DONE", {}, list(REQUIRED))
    missing = [k for k in REQUIRED if k not in data]
    status = data.get("status")
    unknown = status not in STATUSES
    return ImplReport("DONE" if unknown else status, data, missing, unknown)


def is_turn_cut(tool_response: dict | None) -> bool:
    """Il blocco lo scrive Claude Code, separato dall'output del subagente (P0, E6)."""
    if not isinstance(tool_response, dict):
        return False
    if not isinstance(tool_response.get("harnessNoteCount"), int) \
            or tool_response["harnessNoteCount"] < 1:
        return False
    content = tool_response.get("content")
    if not isinstance(content, list) or not content or not isinstance(content[0], dict):
        return False
    return str(content[0].get("text", "")).startswith(CUT_PREFIX)


def transcript_tokens(path) -> int:
    """Token nuovi del subagente: input + cache_creation + output, una volta per messaggio
    (decisione 20). cache_read resta fuori perché riconta il contesto a ogni turno."""
    seen: dict[str, int] = {}
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return 0
    with fh:
        for n, line in enumerate(fh):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = row.get("message") if isinstance(row, dict) else None
            usage = msg.get("usage") if isinstance(msg, dict) else None
            if not isinstance(usage, dict):
                continue
            total = sum(int(usage.get(k) or 0) for k in
                        ("input_tokens", "cache_creation_input_tokens", "output_tokens"))
            seen[str(msg.get("id") or f"riga-{n}")] = total
    return sum(seen.values())
```

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK. Nota: se `PostToolUse-Agent-maxturns-cut` in `samples.json` non ha `content[0].text` che comincia con `NOTE: this agent stopped at its`, fermarsi e leggere il campione: il test usa l'input reale e prevale sul codice.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_analysis/waivers.py bin/tollgate_analysis/report.py tests/test_waivers.py tests/test_report.py
git commit -m "tollgate P2: deroghe e report dell'implementatore"
```

---
### Task 9: Git in sola lettura

**Files:**
- Create: `bin/tollgate_core/git.py`
- Test: `tests/test_git.py`

**Interfaces:**
- Produces:
  - `git.GitError`; `git.Change(status, path, old_path, added, removed, binary)` (stessi attributi di `level.FileChange`).
  - `git.run(repo, *args, check=True) -> str`; `git.ok(repo, *args) -> bool`.
  - `git.toplevel(path) -> Path | None` (risale alla prima cartella esistente); `git.head(repo) -> str | None`; `git.branch(repo) -> str | None`; `git.common_dir(repo) -> Path`; `git.worktrees(repo) -> list[tuple[Path, str | None]]`; `git.main_worktree(repo) -> Path`; `git.local_branches(repo) -> set[str]`.
  - `git.resolve_ref(repo, ref) -> str | None`; `git.default_ref(repo) -> str | None`; `git.default_branch(repo) -> str | None`; `git.origin_url(repo) -> str | None`.
  - `git.changes(repo, base, *, head=None) -> list[Change]` (con `head=None`: dalla base al working tree, non tracciati compresi); `git.commit_changes(repo, sha) -> list[Change]`; `git.diff_size(repo, base, *, head=None) -> int`.
  - `git.show(repo, ref, path) -> bytes | None`; `git.text_at(repo, ref, path) -> str | None`; `git.worktree_text(repo, path) -> str | None`; `git.exists_at(repo, ref, path) -> bool`; `git.blob_sha(repo, path) -> str`.
  - `git.rev_list(repo, base, head) -> list[str]` (dal più vecchio); `git.fingerprint(repo, exclude) -> str`; `git.is_clean(repo, exclude) -> bool`.

- [ ] **Step 1: Test**

`tests/test_git.py`:

```python
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.helpers import git as g, make_repo
from tollgate_core import git


class GitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate git "))
        self.repo = make_repo(self.tmp / "repo con spazi")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.py").write_text("uno\ndue\n")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n")
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-qm", "base")
        self.base = g(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_toplevel_of_missing_path(self):
        self.assertEqual(git.toplevel(self.repo / "src" / "nuova" / "x.py"), self.repo.resolve())
        self.assertIsNone(git.toplevel(self.tmp / "fuori"))

    def test_changes_worktree_and_untracked(self):
        (self.repo / "src" / "a.py").write_text("uno\ndue\ntre\n")
        (self.repo / "src" / "b.py").write_text("x\ny\n")
        (self.repo / "img.bin").write_bytes(b"\x00\x01\x02")
        g(self.repo, "mv", "tests/test_a.py", "tests/test_b.py")
        got = {c.path: c for c in git.changes(self.repo, self.base)}
        self.assertEqual((got["src/a.py"].status, got["src/a.py"].added), ("M", 1))
        self.assertEqual((got["src/b.py"].status, got["src/b.py"].added), ("A", 2))
        self.assertTrue(got["img.bin"].binary)
        self.assertEqual((got["tests/test_b.py"].status, got["tests/test_b.py"].old_path),
                         ("R", "tests/test_a.py"))
        self.assertGreater(git.diff_size(self.repo, self.base), 0)

    def test_commits_and_text(self):
        (self.repo / "src" / "a.py").unlink()
        g(self.repo, "commit", "-qam", "via a")
        head = git.head(self.repo)
        self.assertEqual(git.rev_list(self.repo, self.base, head), [head])
        self.assertEqual([(c.status, c.path) for c in git.commit_changes(self.repo, head)],
                         [("D", "src/a.py")])
        self.assertEqual(git.text_at(self.repo, self.base, "src/a.py"), "uno\ndue\n")
        self.assertIsNone(git.text_at(self.repo, head, "src/a.py"))
        self.assertTrue(git.exists_at(self.repo, self.base, "src/a.py"))
        self.assertFalse(git.exists_at(self.repo, head, "src/a.py"))
        root = git.commit_changes(self.repo, self.base)
        self.assertEqual({c.path for c in root}, {"src/a.py", "tests/test_a.py"})

    def test_default_ref_order(self):
        origin = self.tmp / "origin.git"
        g(self.tmp, "init", "-q", "--bare", "-b", "main", str(origin))
        g(self.repo, "remote", "add", "origin", str(origin))
        g(self.repo, "push", "-q", "origin", "main")
        self.assertEqual(git.default_ref(self.repo), "origin/main")
        g(self.repo, "config", "tollgate.defaultBranch", "main")
        self.assertEqual(git.default_ref(self.repo), "origin/main")
        self.assertEqual(git.default_branch(self.repo), "main")
        self.assertEqual(git.origin_url(self.repo), str(origin))

    def test_worktrees_and_branches(self):
        wt = self.tmp / "wt 1"
        g(self.repo, "worktree", "add", "-q", "-b", "tg/1-x", str(wt))
        self.assertEqual(git.main_worktree(wt), self.repo.resolve())
        self.assertIn((wt.resolve(), "tg/1-x"), git.worktrees(self.repo))
        self.assertEqual(git.branch(wt), "tg/1-x")
        self.assertIn("tg/1-x", git.local_branches(self.repo))
        self.assertEqual(git.common_dir(wt), (self.repo / ".git").resolve())

    def test_fingerprint_and_clean(self):
        f0 = git.fingerprint(self.repo, ["reports/"])
        (self.repo / "reports").mkdir()
        (self.repo / "reports" / "j.xml").write_text("x")
        self.assertEqual(git.fingerprint(self.repo, ["reports/"]), f0)
        self.assertTrue(git.is_clean(self.repo, ["reports/"]))
        (self.repo / "nuovo.txt").write_text("x")
        self.assertNotEqual(git.fingerprint(self.repo, ["reports/"]), f0)
        self.assertFalse(git.is_clean(self.repo, ["reports/"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_git -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_core.git'`.

- [ ] **Step 3: `git.py`**

```python
"""Git in sola lettura per hook e CLI (spec 3.2): diff dalla base, file, impronte."""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class GitError(Exception):
    pass


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None
    added: int
    removed: int
    binary: bool


def _proc(repo, args, input_=None):
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              input=input_)
    except FileNotFoundError as e:
        raise GitError("git non disponibile") from e


def run(repo, *args, check=True) -> str:
    r = _proc(repo, args)
    if check and r.returncode != 0:
        raise GitError(f"git {' '.join(args)}: "
                       f"{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "surrogateescape")


def ok(repo, *args) -> bool:
    try:
        return _proc(repo, args).returncode == 0
    except GitError:
        return False


def toplevel(path) -> Path | None:
    p = Path(path)
    while not p.exists():
        if p.parent == p:
            return None
        p = p.parent
    if not p.is_dir():
        p = p.parent
    try:
        out = run(p, "rev-parse", "--show-toplevel").strip()
    except GitError:
        return None
    return Path(out).resolve() if out else None


def head(repo) -> str | None:
    out = run(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).strip()
    return out or None


def branch(repo) -> str | None:
    out = run(repo, "symbolic-ref", "--short", "-q", "HEAD", check=False).strip()
    return out or None


def common_dir(repo) -> Path:
    out = run(repo, "rev-parse", "--git-common-dir").strip()
    p = Path(out)
    return (p if p.is_absolute() else Path(repo) / p).resolve()


def worktrees(repo) -> list[tuple[Path, str | None]]:
    out, path, br = [], None, None
    for line in run(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if line.startswith("worktree "):
            path, br = Path(line[9:]).resolve(), None
        elif line.startswith("branch "):
            br = line[7:].removeprefix("refs/heads/")
        elif not line and path is not None:
            out.append((path, br))
            path = None
    return out


def main_worktree(repo) -> Path:
    return worktrees(repo)[0][0]


def local_branches(repo) -> set[str]:
    return {b for b in run(repo, "for-each-ref", "--format=%(refname:short)",
                           "refs/heads").splitlines() if b}


def resolve_ref(repo, ref: str) -> str | None:
    out = run(repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}", check=False).strip()
    return out or None


def default_branch(repo) -> str | None:
    b = run(repo, "config", "--get", "tollgate.defaultBranch", check=False).strip()
    if b:
        return b
    sym = run(repo, "symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False).strip()
    if sym:
        return sym.removeprefix("refs/remotes/origin/")
    for b in ("main", "master"):
        if resolve_ref(repo, f"origin/{b}"):
            return b
    return None


def default_ref(repo) -> str | None:
    """Ordine di 7.1: tollgate.defaultBranch, origin/HEAD, origin/main, origin/master."""
    b = run(repo, "config", "--get", "tollgate.defaultBranch", check=False).strip()
    for ref in ([f"origin/{b}"] if b else []) + ["origin/HEAD", "origin/main", "origin/master"]:
        if resolve_ref(repo, ref):
            return ref
    return None


def origin_url(repo) -> str | None:
    out = run(repo, "remote", "get-url", "origin", check=False).strip()
    return out or None


def _parse_z(numstat: str, status: str) -> list[Change]:
    st_tokens = status.split("\0")
    statuses: dict[str, tuple[str, str | None]] = {}
    i = 0
    while i < len(st_tokens) and st_tokens[i]:
        code = st_tokens[i]
        if code[0] in "RC":
            statuses[st_tokens[i + 2]] = ("R", st_tokens[i + 1])
            i += 3
        else:
            statuses[st_tokens[i + 1]] = (code[0], None)
            i += 2
    out = []
    ns = numstat.split("\0")
    i = 0
    while i < len(ns) and ns[i]:
        added, removed, path = ns[i].split("\t", 2)
        if path == "":
            path = ns[i + 2]
            i += 3
        else:
            i += 1
        binary = added == "-"
        st, old = statuses.get(path, ("M", None))
        out.append(Change("M" if st == "T" else st, path, old,
                          0 if binary else int(added), 0 if binary else int(removed), binary))
    return out


def _untracked(repo) -> list[Change]:
    out = []
    for rel in run(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not rel:
            continue
        try:
            data = (Path(repo) / rel).read_bytes()
        except OSError:
            continue
        binary = b"\0" in data[:8000]
        lines = 0 if binary else data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
        out.append(Change("A", rel, None, lines, 0, binary))
    return out


def changes(repo, base: str, *, head: str | None = None) -> list[Change]:
    refs = [base] if head is None else [base, head]
    numstat = run(repo, "diff", "-M", "--numstat", "-z", *refs, "--")
    status = run(repo, "diff", "-M", "--name-status", "-z", *refs, "--")
    out = _parse_z(numstat, status)
    if head is None:
        out += _untracked(repo)
    return out


def commit_changes(repo, sha: str) -> list[Change]:
    parent = resolve_ref(repo, f"{sha}^") or EMPTY_TREE
    return changes(repo, parent, head=sha)


def diff_size(repo, base: str, *, head: str | None = None) -> int:
    refs = [base] if head is None else [base, head]
    size = len(run(repo, "diff", "--no-color", *refs, "--").encode("utf-8", "surrogateescape"))
    if head is None:
        for rel in run(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
            if rel:
                try:
                    size += (Path(repo) / rel).stat().st_size
                except OSError:
                    pass
    return size


def show(repo, ref: str, path: str) -> bytes | None:
    r = _proc(repo, ["show", f"{ref}:{path}"])
    return r.stdout if r.returncode == 0 else None


def _text(data: bytes | None) -> str | None:
    if data is None or b"\0" in data[:8000]:
        return None
    return data.decode("utf-8", "replace")


def text_at(repo, ref: str, path: str) -> str | None:
    return _text(show(repo, ref, path))


def worktree_text(repo, path: str) -> str | None:
    try:
        return _text((Path(repo) / path).read_bytes())
    except OSError:
        return None


def exists_at(repo, ref: str, path: str) -> bool:
    return ok(repo, "cat-file", "-e", f"{ref}:{path}")


def blob_sha(repo, path: str) -> str:
    return run(repo, "hash-object", "--", path).strip()


def rev_list(repo, base: str, head: str) -> list[str]:
    return [s for s in run(repo, "rev-list", "--reverse", f"{base}..{head}").split() if s]


def _excluded(rel: str, exclude) -> bool:
    return any(rel == e.rstrip("/") or rel.startswith(e.rstrip("/") + "/") for e in exclude)


def fingerprint(repo, exclude) -> str:
    """Impronta dei file tracciati e non tracciati non ignorati (7.3), esclusi output_dirs."""
    h = hashlib.sha256()
    files = run(repo, "ls-files", "-co", "--exclude-standard", "-z").split("\0")
    for rel in sorted({f for f in files if f}):
        if _excluded(rel, exclude):
            continue
        try:
            digest = hashlib.sha1((Path(repo) / rel).read_bytes()).hexdigest()
        except FileNotFoundError:
            digest = "cancellato"
        except IsADirectoryError:
            digest = "cartella"
        h.update(f"{rel}\0{digest}\n".encode("utf-8", "surrogateescape"))
    return h.hexdigest()


def is_clean(repo, exclude) -> bool:
    out = run(repo, "status", "--porcelain", "-z", "--untracked-files=all")
    entries = [e for e in out.split("\0") if e]
    paths, skip = [], False
    for e in entries:
        if skip:
            skip = False
            continue
        code, rel = e[:2], e[3:]
        paths.append(rel)
        if code[0] in "RC":
            skip = True
    return all(_excluded(p, exclude) for p in paths)
```

- [ ] **Step 4: Verificare che passi**

Run: `python3 -B -m unittest tests.test_git -v`
Expected: PASS. Nota: `git worktree list --porcelain` e `--show-toplevel` restituiscono percorsi risolti; i test confrontano con `.resolve()` perché `/tmp` può essere un collegamento simbolico.

- [ ] **Step 5: Suite e commit**

Run: `tests/run`
Expected: OK.

```bash
git add bin/tollgate_core/git.py tests/test_git.py
git commit -m "tollgate P2: accesso a git in sola lettura"
```

---

### Task 10: Sottocomando `verify` (8.1)

**Files:**
- Create: `bin/tollgate_core/verify.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `verify`)
- Modify: `tests/helpers.py` (funzione `make_origin_repo`)
- Test: `tests/test_verify.py`

**Interfaces:**
- Consumes: `config.load_config`, `git.*`, `sessions.work_for_path`, `receipts.add`, `profiles.active_profiles`, `junit.parse_junit`, `paths.resolve_state`, `db.open_db`.
- Produces:
  - `verify.CommandSpec(name, command, report)`; `verify.gate_commands(cfg, files) -> list[CommandSpec]` (comandi del gate più i `gate` dei profili attivi; un nome di profilo diventa `profile:<profilo>:<comando>`); `verify.receipt_state(*, exit_code, report_configured, junit, allow_no_tests) -> str`; `verify.clean_env(env_allow, environ) -> dict`; `verify.run_verify(state, cwd, *, related=False, now=None, environ=None) -> tuple[int, list[str]]` (uscita e righe da stampare).
  - CLI: `tollgate verify [--related]`, uscita 0 se ogni ricevuta vale verde (anche `empty` o `uncounted` con `allow_no_tests` e uscita 0), 1 altrimenti.
  - `tests.helpers.make_origin_repo(root: Path, files: dict[str, str], toml: str) -> tuple[Path, Path, str]` (checkout principale, origin nudo, SHA della base), usato anche dal banco degli hook.

- [ ] **Step 1: Banco di prova con origin**

In `tests/helpers.py` aggiungere:

```python
def make_origin_repo(root, files: dict, toml: str):
    """Origin nudo e checkout principale con tollgate.toml sul predefinito (repo attivo, 7.1)."""
    root = Path(root)
    origin = root / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True,
                   capture_output=True)
    main = make_repo(root / "main")
    (main / "tollgate.toml").write_text(toml)
    for rel, text in files.items():
        p = main / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    git(main, "add", "-A")
    git(main, "commit", "-qm", "base")
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "-u", "origin", "main")
    git(main, "remote", "set-head", "origin", "main")
    git(main, "config", "tollgate.defaultBranch", "main")
    return main, origin, git(main, "rev-parse", "HEAD")
```

- [ ] **Step 2: Test**

`tests/test_verify.py`:

```python
import shutil
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.helpers import TempState, git, make_origin_repo
from tollgate_core import config, db, phases, verify
from tollgate_core.paths import repo_key
from tollgate_analysis.junit import Junit

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
TOML = textwrap.dedent('''
    schema_version = 1
    [gate]
    mode = "protected"
    [commands]
    verify = "sh check.sh"
    test_related = "sh related.sh {files}"
    gate = ["verify"]
    report = "junit:reports/junit.xml"
    report_related = "junit:reports/junit-related.xml"
    env_allow = ["PATH", "HOME"]
    [profiles.web]
    paths = ["web/**"]
    commands = { lint = "sh lint.sh" }
    gate = ["lint"]
''')
CHECK = textwrap.dedent('''
    mkdir -p reports
    test -n "$SEGRETO" && echo "segreto visibile" && exit 3
    cat > reports/junit.xml <<EOF
    <testsuite><testcase classname="t" name="a"/><testcase classname="t" name="b"><skipped/></testcase></testsuite>
    EOF
''')


class VerifyUnitTest(unittest.TestCase):
    def test_receipt_state(self):
        j = Junit(total=2, skipped=0, failed=0)
        st = verify.receipt_state
        self.assertEqual(st(exit_code=0, report_configured=True, junit=j, allow_no_tests=False),
                         "green")
        self.assertEqual(st(exit_code=1, report_configured=True, junit=j, allow_no_tests=False),
                         "red")
        self.assertEqual(st(exit_code=0, report_configured=True,
                            junit=Junit(total=1, failed=1), allow_no_tests=False), "red")
        self.assertEqual(st(exit_code=0, report_configured=True, junit=Junit(),
                            allow_no_tests=False), "empty")
        self.assertEqual(st(exit_code=0, report_configured=True, junit=None,
                            allow_no_tests=True), "red")
        self.assertEqual(st(exit_code=0, report_configured=False, junit=None,
                            allow_no_tests=True), "uncounted")

    def test_clean_env(self):
        self.assertEqual(verify.clean_env(["PATH"], {"PATH": "/bin", "TOKEN": "x"}),
                         {"PATH": "/bin"})

    def test_gate_commands_with_profiles(self):
        cfg = config.load_config_text(TOML)
        names = [c.name for c in verify.gate_commands(cfg, ["src/a.py"])]
        self.assertEqual(names, ["verify"])
        names = [c.name for c in verify.gate_commands(cfg, ["web/a.ts"])]
        self.assertEqual(names, ["verify", "profile:web:lint"])


class VerifyRunTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-verify-"))
        self.main, _, self.base = make_origin_repo(
            self.tmp, {"check.sh": CHECK, "related.sh": "exit 0\n",
                       ".gitignore": "reports/\n"}, TOML)
        self.wt = self.tmp / "wt"
        git(self.main, "worktree", "add", "-q", "-b", "tg/7-x", str(self.wt))
        conn = db.open_db(self.ts.state)
        self.work = phases.create_work(conn, repo_key=repo_key(str(self.tmp / "origin.git")),
                                       issue=7, level="L1", now=T0, worktree=str(self.wt),
                                       branch="tg/7-x", work_base_sha=self.base)
        conn.close()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _receipts(self):
        conn = db.open_db(self.ts.state)
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM receipts ORDER BY id")]
        finally:
            conn.close()

    def test_green_receipt_and_clean_env(self):
        (self.wt / "reports").mkdir()
        (self.wt / "reports" / "junit.xml").write_text("<vecchio/>")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin", "SEGRETO": "x"})
        self.assertEqual(code, 0, lines)
        r = self._receipts()[0]
        self.assertEqual((r["state"], r["tests_run"], r["tests_skipped"], r["work"], r["sha"]),
                         ("green", 1, 1, self.work, self.base))

    def test_dirty_worktree_refused(self):
        (self.wt / "sporco.txt").write_text("x")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 1)
        self.assertIn("worktree non pulito", " ".join(lines))
        self.assertEqual(self._receipts(), [])

    def test_config_read_from_work_base(self):
        (self.wt / "tollgate.toml").write_text(TOML.replace('verify = "sh check.sh"', ""))
        git(self.wt, "commit", "-qam", "senza verify")
        code, _ = verify.run_verify(self.ts.state, self.wt, now=T0,
                                    environ={"PATH": "/usr/bin:/bin"})
        # la configurazione si legge dalla base del lavoro, non dal working tree (3.2)
        self.assertEqual(self._receipts()[0]["state"], "green")
        self.assertEqual(code, 0)

    def test_missing_command_is_unverified(self):
        cfg = self.tmp / "cfg.toml"
        cfg.write_text(TOML.replace('verify = "sh check.sh"\n', ""))
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin",
                                                 "TOLLGATE_TEST_CONFIG": str(cfg)})
        self.assertEqual(code, 1)
        self.assertEqual(self._receipts()[0]["state"], "unverified")
        self.assertIn("approve unverified-tests", " ".join(lines))

    def test_related_without_files_runs_gate(self):
        code, lines = verify.run_verify(self.ts.state, self.wt, related=True, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual([r["command"] for r in self._receipts()], ["verify"])
        self.assertEqual(code, 0, lines)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_verify -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_core.verify'`.

- [ ] **Step 4: `verify.py`**

```python
"""tollgate verify (spec 8.1): comandi del gate su HEAD, ambiente ripulito, ricevute."""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from tollgate_analysis import profiles as prof
from tollgate_analysis.junit import Junit, JunitError, parse_junit

from . import clock, db, git, receipts, sessions
from .config import Config, ConfigError, load_config
from .paths import State, ensure_dirs


@dataclass(frozen=True)
class CommandSpec:
    name: str
    command: str
    report: str


def _report_for(report, name: str) -> str:
    if isinstance(report, dict):
        return report.get(name, "")
    return report or ""


def _report_path(spec: str) -> str | None:
    return spec.split(":", 1)[1] if spec.startswith("junit:") else (spec or None)


def gate_commands(cfg: Config, files) -> list[CommandSpec]:
    cmds = cfg.get("commands")
    out = [CommandSpec(n, cmds.get(n, ""), _report_for(cmds["report"], n))
           for n in cmds["gate"]]
    profs = cfg.profiles
    for name in prof.active_profiles(files, profs, cfg.get("profiles.active")):
        p = profs[name]
        for n in p["gate"]:
            out.append(CommandSpec(f"profile:{name}:{n}", p["commands"].get(n, ""),
                                   _report_for(p["report"], n)))
    return out


def receipt_state(*, exit_code: int, report_configured: bool, junit: Junit | None,
                  allow_no_tests: bool) -> str:
    if report_configured and junit is None:
        return "red"     # report configurato e assente: resta rosso (8.1, decisione 11)
    if junit is None:
        return "red" if exit_code != 0 else "uncounted"
    if exit_code != 0 or junit.failed:
        return "red"
    if junit.total - junit.skipped == 0:
        return "empty"
    return "green"


def clean_env(env_allow, environ) -> dict:
    return {k: environ[k] for k in env_allow if k in environ}


def counts_green(state: str, exit_code: int, allow_no_tests: bool) -> bool:
    return state == "green" or (allow_no_tests and (
        state == "empty" or (state == "uncounted" and exit_code == 0)))


def _run_one(spec: CommandSpec, *, root: Path, files: list[str], env: dict, timeout_s: int,
             allow_no_tests: bool, log_dir: Path, tag: str):
    resolved = spec.command.replace("{files}", " ".join(shlex.quote(f) for f in files))
    report_rel = _report_path(spec.report)
    report = root / report_rel if report_rel else None
    if report is not None:
        report.unlink(missing_ok=True)
    log = log_dir / f"{tag}-{spec.name.replace(':', '_')}.log"
    t0 = time.monotonic()
    try:
        with open(log, "wb") as fh:
            exit_code = subprocess.run(["/bin/sh", "-c", resolved], cwd=root, env=env,
                                       stdout=fh, stderr=subprocess.STDOUT,
                                       timeout=timeout_s).returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    duration = time.monotonic() - t0
    junit = None
    if report is not None and report.is_file():
        try:
            junit = parse_junit(report.read_bytes())
        except JunitError as e:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"\n[tollgate] report non valido: {e}\n")
    state = receipt_state(exit_code=exit_code, report_configured=report is not None,
                          junit=junit, allow_no_tests=allow_no_tests)
    return resolved, exit_code, junit, duration, state, log


def run_verify(state: State, cwd, *, related: bool = False, now=None,
               environ=None) -> tuple[int, list[str]]:
    environ = os.environ if environ is None else environ
    root = git.toplevel(cwd)
    if root is None:
        return 1, ["tollgate verify: non sei in un repo git"]
    conn = db.open_db(state)
    try:
        work = sessions.work_for_path(conn, root)
        ref = work["work_base_sha"] if work is not None and work["work_base_sha"] \
            else git.default_ref(root)
        if ref is None:
            return 1, ["tollgate verify: nessun riferimento remoto da cui leggere tollgate.toml"]
        try:
            cfg = load_config(state, root, ref, env=environ)
        except ConfigError as e:
            return 1, [f"tollgate verify: {e}"]
        exclude = cfg.get("review.output_dirs") + [".tollgate-run/"]
        if not git.is_clean(root, exclude):
            return 1, ["tollgate verify: worktree non pulito: committa prima di verificare"]
        sha = git.head(root)
        base = ref if work is None else work["work_base_sha"]
        changed = [c for c in git.changes(root, base, head=sha) if c.status != "D"]
        files = [c.path for c in changed]
        allow = cfg.get("project.allow_no_tests")
        cmds = cfg.get("commands")
        specs = gate_commands(cfg, files)
        related_files = files
        if related and cmds["test_related"] and related_files:
            specs = [CommandSpec("related", cmds["test_related"], cmds["report_related"])]
        env = clean_env(cfg.get("commands.env_allow"), environ)
        log_dir = state.root / "logs"
        ensure_dirs(state)
        log_dir.mkdir(mode=0o700, exist_ok=True)
        now = now or clock.now()
        tag = f"{work['issue'] if work is not None else 'repo'}-{sha[:7]}-" \
              f"{now.strftime('%Y%m%dT%H%M%S')}"
        lines, all_ok = [], True
        for spec in specs:
            if not spec.command:
                receipts.add(conn, work=work["id"] if work is not None else None, sha=sha,
                             command=spec.name, resolved_command=None, exit_code=None,
                             tests_run=None, tests_skipped=None, duration=None, log=None,
                             produced_by="verify", state="unverified", now=now)
                lines.append(f"{spec.name}: unverified (comando non configurato: serve "
                             f"/tollgate:approve unverified-tests)")
                all_ok = False
                continue
            resolved, exit_code, junit, duration, st, log = _run_one(
                spec, root=root, files=related_files if spec.name == "related" else files,
                env=env, timeout_s=cfg.get("commands.timeout_s"), allow_no_tests=allow,
                log_dir=log_dir, tag=tag)
            receipts.add(conn, work=work["id"] if work is not None else None, sha=sha,
                         command=spec.name, resolved_command=resolved, exit_code=exit_code,
                         tests_run=(junit.total - junit.skipped) if junit else None,
                         tests_skipped=junit.skipped if junit else None, duration=duration,
                         log=str(log), produced_by="verify", state=st, now=now)
            good = counts_green(st, exit_code, allow)
            all_ok = all_ok and good
            run = f", {junit.total - junit.skipped} test" if junit else ""
            lines.append(f"{spec.name}: {st} (uscita {exit_code}{run}; log {log})")
        return (0 if all_ok else 1), lines
    finally:
        conn.close()
```

- [ ] **Step 5: CLI**

In `bin/tollgate_core/cli.py`: in `build_parser`, dopo il sottocomando `events`:

```python
    vp = sub.add_parser("verify", help="esegue i comandi del gate e registra le ricevute (8.1)")
    vp.add_argument("--related", action="store_true", help="solo i test correlati ai file cambiati")
```

In `main`, prima di `conn = db.open_db(state)` (dentro il `try`):

```python
        if args.cmd == "verify":
            from . import verify
            code, lines = verify.run_verify(state, Path.cwd(), related=args.related)
            print("\n".join(lines))
            return code
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK. `test_missing_command_is_unverified` dimostra che la configurazione si legge dalla base: il `tollgate.toml` modificato nel ramo non conta. Se fallisce perché `verify` ha letto il working tree, è un difetto del codice.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_core/verify.py bin/tollgate_core/cli.py tests/helpers.py tests/test_verify.py
git commit -m "tollgate P2: sottocomando verify con ricevute e ambiente ripulito"
```

---

### Task 11: Sottocomandi `waiver add` e `block open`

**Files:**
- Create: `bin/tollgate_core/waiver_cli.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomandi `waiver add`, `block open`)
- Test: `tests/test_waiver_cli.py`

**Interfaces:**
- Consumes: `waivers.*`, `sessions.work_for_path`, `phases.open_block`, `events.record_event`, `git.toplevel`.
- Produces:
  - `waiver_cli.add_waiver(state, cwd, *, type_, file=None, pattern=None, tests=(), choice, why, cost, now=None) -> str` (id della deroga; `UsageError` su errori d'uso).
  - `waiver_cli.open_block_cmd(state, cwd, *, type_, reason, now=None) -> int`.
  - CLI: `tollgate waiver add <tipo> [<file>] [--pattern G] [--test ID]... --choice T --why T --cost T`; `tollgate block open <tipo> --reason T`.

- [ ] **Step 1: Test**

`tests/test_waiver_cli.py`:

```python
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.helpers import TempState, git, make_repo
from tollgate_analysis import waivers
from tollgate_core import db, phases, waiver_cli
from tollgate_core.cli import UsageError

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class WaiverCliTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-waiver-"))
        self.wt = make_repo(self.tmp / "wt")
        (self.wt / "a").write_text("x")
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-qm", "x")
        conn = db.open_db(self.ts.state)
        self.work = phases.create_work(conn, repo_key="r", issue=7, level="L1", now=T0,
                                       worktree=str(self.wt), branch="tg/7-x")
        conn.close()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_two_waivers(self):
        w1 = waiver_cli.add_waiver(self.ts.state, self.wt / "src", type_="scope", file="src/x.py",
                                   choice="c", why="w", cost="k", now=T0)
        w2 = waiver_cli.add_waiver(self.ts.state, self.wt, type_="test", file="tests/t.py",
                                   tests=["t::a"], choice="c", why="w", cost="k", now=T0)
        self.assertEqual((w1, w2), ("w-7-1", "w-7-2"))
        wf = waivers.parse((self.wt / ".tollgate/waivers/7.toml").read_text())
        self.assertEqual((wf.issue, wf.branch, [w.id for w in wf.waivers]),
                         (7, "tg/7-x", ["w-7-1", "w-7-2"]))
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute("SELECT count(*) FROM events WHERE type="
                                          "'waiver_added'").fetchone()[0], 2)
        finally:
            conn.close()

    def test_errors(self):
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="boh", file="a", choice="c",
                                  why="w", cost="k", now=T0)
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="scope", choice="c", why="w",
                                  cost="k", now=T0)
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.tmp, type_="scope", file="a", choice="c",
                                  why="w", cost="k", now=T0)

    def test_block_open(self):
        bid = waiver_cli.open_block_cmd(self.ts.state, self.wt, type_="test_spec_conflict",
                                        reason="il test contraddice la spec", now=T0)
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(phases.get_work(conn, self.work)["phase"], "blocked")
            self.assertEqual(conn.execute("SELECT type FROM blocks WHERE id = ?",
                                          (bid,)).fetchone()[0], "test_spec_conflict")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_waiver_cli -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `waiver_cli.py`**

```python
"""tollgate waiver add, tollgate block open (spec 8.3): li usa l'agente, dal worktree."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import waivers

from . import clock, db, git, phases, sessions
from .events import record_event
from .paths import State


def _work(conn, cwd):
    from .cli import UsageError
    root = git.toplevel(cwd)
    work = sessions.work_for_path(conn, root or cwd)
    if work is None:
        raise UsageError("nessun lavoro attivo in questa cartella: lancialo dal worktree "
                         "del lavoro")
    return work


def add_waiver(state: State, cwd, *, type_: str, file: str | None = None,
               pattern: str | None = None, tests=(), choice: str, why: str, cost: str,
               now=None) -> str:
    from .cli import UsageError
    if type_ not in waivers.TYPES:
        raise UsageError(f"tipo di deroga sconosciuto: {type_} (ammessi: "
                         f"{', '.join(waivers.TYPES)})")
    if (file is None) == (pattern is None):
        raise UsageError("indica un file oppure --pattern, non entrambi")
    now = now or clock.now()
    conn = db.open_db(state)
    try:
        work = _work(conn, cwd)
        path = Path(work["worktree"]) / waivers.path_for(work["issue"])
        if path.exists():
            try:
                wf = waivers.parse(path.read_text(encoding="utf-8"))
            except ValueError as e:
                raise UsageError(f"{path}: {e}") from e
        else:
            wf = waivers.WaiverFile(work["issue"], work["branch"] or "", [])
        wid = waivers.next_id(wf)
        wf.waivers.append(waivers.Waiver(wid, type_, file, pattern, list(tests), choice, why,
                                         cost, "agent"))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(waivers.dumps(wf), encoding="utf-8")
        tmp.replace(path)
        record_event(conn, "waiver_added", {"id": wid, "type": type_}, now=now,
                     work=work["id"])
        return wid
    finally:
        conn.close()


def open_block_cmd(state: State, cwd, *, type_: str, reason: str, now=None) -> int:
    from .cli import UsageError
    if type_ not in phases.BLOCK_TYPES:
        raise UsageError(f"tipo di blocco sconosciuto: {type_}")
    conn = db.open_db(state)
    try:
        work = _work(conn, cwd)
        return phases.open_block(conn, state, work["id"], type_, reason, now=now or clock.now())
    finally:
        conn.close()
```

- [ ] **Step 4: CLI**

In `build_parser`:

```python
    wp = sub.add_parser("waiver", help="deroghe (8.3)")
    wsub = wp.add_subparsers(dest="waiver_cmd", required=True)
    wa = wsub.add_parser("add", help="dichiara una deroga in .tollgate/waivers/<N>.toml")
    wa.add_argument("type", metavar="tipo")
    wa.add_argument("file", nargs="?", metavar="file")
    wa.add_argument("--pattern", metavar="GLOB")
    wa.add_argument("--test", action="append", default=[], metavar="ID")
    wa.add_argument("--choice", required=True)
    wa.add_argument("--why", required=True)
    wa.add_argument("--cost", required=True)
    bp = sub.add_parser("block", help="blocchi del lavoro (8.3)")
    bsub = bp.add_subparsers(dest="block_cmd", required=True)
    bo = bsub.add_parser("open", help="apre un blocco; lo chiude l'utente")
    bo.add_argument("type", metavar="tipo")
    bo.add_argument("--reason", required=True)
```

In `main`, accanto a `verify`:

```python
        if args.cmd == "waiver":
            from . import waiver_cli
            print(waiver_cli.add_waiver(state, Path.cwd(), type_=args.type, file=args.file,
                                        pattern=args.pattern, tests=args.test,
                                        choice=args.choice, why=args.why, cost=args.cost))
            return 0
        if args.cmd == "block":
            from . import waiver_cli
            print(waiver_cli.open_block_cmd(state, Path.cwd(), type_=args.type,
                                            reason=args.reason))
            return 0
```

e aggiungere `phases.TransitionError` all'`except` finale di `main` (`except (db.DbError, UsageError, phases.TransitionError) as e:`).

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_core/waiver_cli.py bin/tollgate_core/cli.py tests/test_waiver_cli.py
git commit -m "tollgate P2: sottocomandi waiver add e block open"
```

---
### Task 12: Motore degli hook: modello, adattatore, contesto, registro, runner, `tollgate hook`

**Files:**
- Create: `bin/tollgate_hooks/__init__.py`
- Create: `bin/tollgate_hooks/model.py`
- Create: `bin/tollgate_hooks/adapter.py`
- Create: `bin/tollgate_hooks/context.py`
- Create: `bin/tollgate_hooks/registry.py`
- Create: `bin/tollgate_hooks/apply.py`
- Create: `bin/tollgate_hooks/runner.py`
- Create: `bin/tollgate_checks/__init__.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `hook`)
- Create: `tests/hookkit.py`
- Test: `tests/test_hook_engine.py`

**Interfaces:**
- Consumes: tutto `tollgate_core` dei Task 2-3 e 9; `tollgate_analysis.testguard.GuardConfig`, `waivers`, `profiles`.
- Produces (i Task 14-19 li usano così):
  - `model.INPUT_EVENTS`, `model.CONTROL_EVENTS`; `model.Event(kind, hook_event, session, cwd, agent_id, agent_type, tool_name, tool_input, tool_response, raw)`; `model.Decision`; costruttori `model.allow()`, `model.deny(reason, rule="")`, `model.inject(text)`, `model.record(op, **data)`.
  - `adapter.to_event(hook_event: str, raw: dict) -> Event | None`; `adapter.edit_path(event) -> str | None`; `adapter.INJECT_MODE`; `adapter.render(hook_event, deny_text, inject_text) -> tuple[int, str, str]`.
  - `context.ReadDb(conn)` (solo `SELECT`); `context.Ctx` con: `event`, `state`, `db`, `config`, `repo`, `work`, `bound`, `now`, `plugin_root`; metodi `cfg(dotted)`, `component(name)`, `readonly(agent_type)`, `stale_minutes`, `work_for_path(path)`, `rel(path, root)`, `waiver_file(work)`, `approved_waivers(work)`, `scope(work)`, `guard_config(work, files)`, `protected_roots(repo)`, `plugin_bin`.
  - `registry.API = 1`; `registry.Loaded(name, module, check)`; `registry.Broken(name, events, reason)`; `registry.load(package="tollgate_checks") -> tuple[list[Loaded], list[Broken]]`.
  - `apply.OPS` (insieme dei nomi); `apply.apply(conn, state, ctx, decision) -> None`. Operazioni e campi di `data`:
    - `bind {work}`; `act {type, object, target, args, typed_text, work, head_sha}`; `expire_acts {}`;
    - `block {work, type, reason}`; `level {work, level}`; `phase {work, to, cause}`;
    - `plan {work, plan_path, plan_sha, scope, tasks, advance}`; `plan_path {work, plan_path}`;
    - `subagent_start {agent_id, type, work, task, base_sha, fingerprint, take_pending, resume}`;
    - `subagent_name {agent_id, name, work}`; `subagent_report {agent_id, text}`; `subagent_veto {agent_id}`;
    - `subagent_finish {agent_id, state, declared_status, tokens}`; `subagent_interrupt {agent_id}`;
    - `task {work, number, event}`; `task_commit {work, number, sha}`; `skill_used {work, number, skill}`;
    - `commit {work, sha, head}`; `effect_request {key, command, work, sha}`; `effect_execute {key, act_id, work}`;
    - `event {type, data, work}`.
  - `runner.HookResult(exit, stdout, stderr)`; `runner.run_hook(hook_event, stdin_text, *, env=None, now=None, plugin_root=None, checks=None, alarm=False) -> HookResult`; `runner.BUDGET` (limiti di iniezione per evento).
  - Contratto di un modulo di `tollgate_checks`: `CHECK = {"api": 1, "events": [...], "component": str | None, "order": int}` e `decide(event, ctx) -> list[Decision]`.
  - `tests.hookkit`: `SAMPLES`, `sample(name, **campi)`, `DROP`, `SESSION`, `T0`, `DEFAULT_TOML`, `Lab(level=, phase=, toml=, files=, bind=, work=)` con `lab.hook(payload)`, `lab.pre_edit(path, agent_id=None, tool="Write", content="x")`, `lab.post_edit(...)`, `lab.bash(command, post=False, agent_id=None, cwd=None, response=None)`, `lab.events(type_)`, `lab.close()`, e i campi `ts`, `main`, `wt`, `base`, `conn`, `work`.

- [ ] **Step 1: Banco degli hook**

`tests/hookkit.py`:

```python
"""Banco di prova degli hook: input reali di Claude Code (P0) e un repo attivo con un lavoro."""
import copy
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.helpers import ROOT, TempState, git, make_origin_repo
from tollgate_core import db, phases
from tollgate_core.paths import repo_key
from tollgate_hooks import runner

SAMPLES = json.loads((ROOT / "spikes/fixtures/hook-inputs/samples.json").read_text())
SESSION = "sess-lab"
T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
DROP = object()
DEFAULT_TOML = """schema_version = 1
[gate]
mode = "protected"
[commands]
verify = "true"
gate = ["verify"]
"""
DEFAULT_FILES = {
    "src/app.py": "def somma(a, b):\n    return a + b\n",
    "tests/test_app.py": "from src.app import somma\n\n\ndef test_somma():\n"
                         "    assert somma(1, 2) == 3\n\n\ndef test_zero():\n"
                         "    assert somma(0, 0) == 0\n",
    "docs/superpowers/README.md": "doc\n",
    ".gitignore": "reports/\n",
}


def sample(name, **changes):
    """Un input reale con i campi cambiati; i nomi di Task 1 mancanti si costruiscono dalla
    busta di PreToolUse-Bash con tool_name e tool_input della documentazione."""
    if name in SAMPLES:
        s = copy.deepcopy(SAMPLES[name])
    else:
        event, _, tool = name.partition("-")
        s = copy.deepcopy(SAMPLES[f"{event}-Bash"] if event in ("PreToolUse", "PostToolUse")
                          else SAMPLES["SessionStart-none"])
        s["hook_event_name"] = event
        if tool:
            s["tool_name"] = tool.split("-")[0]
    for k, v in changes.items():
        if v is DROP:
            s.pop(k, None)
        else:
            s[k] = v
    return s


class Lab:
    def __init__(self, *, level="L1", phase="execution", toml=DEFAULT_TOML, files=None,
                 bind=True, work=True):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate lab "))
        self.main, self.origin, self.base = make_origin_repo(self.tmp, files or DEFAULT_FILES,
                                                             toml)
        self.wt = self.tmp / "wt 7"
        git(self.main, "worktree", "add", "-q", "-b", "tg/7-demo", str(self.wt))
        self.conn = db.open_db(self.ts.state)
        self.work = None
        self.now = T0 + timedelta(minutes=1)
        if work:
            self.work = phases.create_work(
                self.conn, repo_key=repo_key(str(self.origin)), issue=7, level=level, now=T0,
                session=SESSION if bind else None, branch="tg/7-demo", worktree=str(self.wt),
                work_base_sha=self.base, gate_mode="protected")
            self.goto(phase)

    def goto(self, phase):
        row = phases.get_work(self.conn, self.work)
        seq = phases.SEQUENCES[row["level"]]
        cur = row["phase"]
        while cur != phase:
            nxt = seq[seq.index(cur) + 1]
            cause = phases._FORWARD_CONDITION.get((cur, nxt), "advance")
            phases.set_phase(self.conn, self.ts.state, self.work, nxt, cause, now=T0)
            cur = nxt

    def hook(self, payload, now=None):
        self.now = now or (self.now + timedelta(seconds=1))
        return runner.run_hook(payload["hook_event_name"], json.dumps(payload),
                               env=self.ts.env(), now=self.now, plugin_root=ROOT)

    def _base(self, name, agent_id, cwd, **kw):
        extra = {"session_id": SESSION, "cwd": str(cwd or self.wt)}
        if agent_id:
            extra.update(agent_id=agent_id, agent_type=kw.pop("agent_type",
                                                              "tollgate:implementer"))
        else:
            extra.update(agent_id=DROP, agent_type=DROP)
        extra.update(kw)
        return sample(name, **extra)

    def pre_edit(self, path, *, agent_id=None, tool="Write", content="x", cwd=None, **kw):
        ti = {"file_path": str(path), "content": content} if tool == "Write" else \
            {"file_path": str(path), "old_string": "a", "new_string": "b"}
        return self.hook(self._base(f"PreToolUse-{tool}", agent_id, cwd, tool_name=tool,
                                    tool_input=ti, **kw))

    def post_edit(self, path, *, agent_id=None, tool="Write", cwd=None, **kw):
        ti = {"file_path": str(path), "content": Path(path).read_text()
              if Path(path).exists() else ""}
        return self.hook(self._base(f"PostToolUse-{tool}", agent_id, cwd, tool_name=tool,
                                    tool_input=ti, tool_response={"filePath": str(path)}, **kw))

    def bash(self, command, *, post=False, agent_id=None, cwd=None, response=None, **kw):
        name = "PostToolUse-Bash" if post else "PreToolUse-Bash"
        extra = {"tool_input": {"command": command, "description": "x"}}
        if post:
            extra["tool_response"] = response or {"stdout": "", "stderr": "",
                                                  "interrupted": False}
        return self.hook(self._base(name, agent_id, cwd, **extra, **kw))

    def events(self, type_):
        return [json.loads(r["data"]) for r in self.conn.execute(
            "SELECT data FROM events WHERE type = ? ORDER BY seq", (type_,))]

    def close(self):
        self.conn.close()
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)
```

- [ ] **Step 2: Test del motore**

`tests/test_hook_engine.py`:

```python
import json
import multiprocessing
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.helpers import ROOT, TempState
from tollgate_hooks import adapter, registry, runner
from tollgate_hooks.model import Event, deny, inject, record

FAKE = {
    "uno.py": '''
CHECK = {"api": 1, "events": ["pre_bash", "session_start"], "component": None, "order": 10}
def decide(event, ctx):
    from tollgate_hooks.model import deny, inject, record
    cmd = (event.tool_input or {}).get("command", "")
    if "vietato" in cmd:
        return [deny("comando vietato", rule="uno"), record("event", type="off", data={})]
    if event.kind == "session_start":
        return [inject("riga\\n" * 30)]
    return []
''',
    "due.py": '''
CHECK = {"api": 2, "events": ["pre_edit"], "component": None, "order": 20}
def decide(event, ctx):
    return []
''',
    "tre.py": '''
CHECK = {"api": 1, "events": ["pre_bash"], "component": "scope_check", "order": 5}
def decide(event, ctx):
    from tollgate_hooks.model import deny
    if "tre" in (event.tool_input or {}).get("command", ""):
        return [deny("controllo tre", rule="tre")]
    return []
''',
    "lento.py": '''
CHECK = {"api": 1, "events": ["pre_mcp"], "component": None, "order": 1}
def decide(event, ctx):
    import time
    time.sleep(5)
    return []
''',
}


def fake_checks(tmp: Path):
    pkg = tmp / "finti_checks"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    for name, body in FAKE.items():
        (pkg / name).write_text(textwrap.dedent(body))
    sys.path.insert(0, str(tmp))
    try:
        return registry.load("finti_checks")
    finally:
        sys.path.remove(str(tmp))


class AdapterTest(unittest.TestCase):
    def test_mapping(self):
        cases = [("SessionStart-none", "session_start"), ("PreToolUse-Bash", "pre_bash"),
                 ("PostToolUse-Bash", "post_bash"), ("PreToolUse-Agent", "pre_agent"),
                 ("PostToolUse-Agent", "post_agent"), ("PreToolUse-SendMessage",
                                                       "pre_send_message"),
                 ("SubagentStart-none", "subagent_start"), ("SubagentStop-none", "subagent_stop"),
                 ("PostToolUse-SubagentHandback", "subagent_handback"),
                 ("UserPromptExpansion-none", "prompt_expansion"),
                 ("PreToolUse-Read", None), ("PreToolUse-ToolSearch", None)]
        for name, kind in cases:
            s = sample(name)
            ev = adapter.to_event(s["hook_event_name"], s)
            with self.subTest(name=name):
                self.assertEqual(ev.kind if ev else None, kind)
        mcp = sample("PreToolUse-Bash", tool_name="mcp__srv__scrivi", tool_input={"a": 1})
        self.assertEqual(adapter.to_event("PreToolUse", mcp).kind, "pre_mcp")
        w = sample("PreToolUse-Write", tool_name="Write", tool_input={"file_path": "/x/a.py"})
        self.assertEqual(adapter.edit_path(adapter.to_event("PreToolUse", w)), "/x/a.py")
        nb = sample("PreToolUse-Bash", tool_name="NotebookEdit",
                    tool_input={"notebook_path": "/x/n.ipynb"})
        self.assertEqual(adapter.edit_path(adapter.to_event("PreToolUse", nb)), "/x/n.ipynb")

    def test_render(self):
        self.assertEqual(adapter.render("PreToolUse", "no", None)[:1], (2,))
        code, out, _ = adapter.render("SessionStart", None, "ciao")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["hookSpecificOutput"],
                         {"hookEventName": "SessionStart", "additionalContext": "ciao"})
        self.assertEqual(adapter.render("PostToolUse", None, None), (0, "", ""))


class RunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="tollgate-finti-"))
        cls.checks = fake_checks(cls.tmp)

    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def run_with(self, payload, **kw):
        return runner.run_hook(payload["hook_event_name"], json.dumps(payload),
                               env=self.lab.ts.env(), now=self.lab.now, plugin_root=ROOT,
                               checks=self.checks, **kw)

    def test_deny_records_veto_and_records_after_deny(self):
        r = self.run_with(self.lab._base("PreToolUse-Bash", None, None,
                                         tool_input={"command": "echo vietato"}))
        self.assertEqual(r.exit, 2)
        self.assertIn("comando vietato", r.stderr)
        self.assertEqual(self.lab.events("veto"), [{"event": "pre_bash", "rule": "uno",
                                                    "reason": "comando vietato"}])
        self.assertEqual(len(self.lab.events("off")), 1)

    def test_api_mismatch_denies_its_events(self):
        r = self.run_with(self.lab._base("PreToolUse-Write", None, None, tool_name="Write",
                                         tool_input={"file_path": str(self.lab.wt / "x")}))
        self.assertEqual(r.exit, 2)
        self.assertIn("due", r.stderr)

    def test_component_off_skips_module(self):
        toml = DEFAULT_TOML + "[components]\nscope_check = false\n"
        lab = Lab(toml=toml)
        try:
            p = lab._base("PreToolUse-Bash", None, None, tool_input={"command": "echo tre"})
            r = runner.run_hook("PreToolUse", json.dumps(p), env=lab.ts.env(), now=lab.now,
                                plugin_root=ROOT, checks=self.checks)
            self.assertEqual(r.exit, 0)
        finally:
            lab.close()
        p = self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "echo tre"})
        self.assertEqual(self.run_with(p).exit, 2)

    def test_inject_budget_session_start(self):
        r = self.run_with(self.lab._base("SessionStart-none", None, None))
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(ctx.splitlines()), 10)
        self.assertLessEqual(len(ctx), 1500)

    def test_malformed_input_control_and_info(self):
        r = runner.run_hook("PreToolUse", "{rotto", env=self.lab.ts.env(), plugin_root=ROOT)
        self.assertEqual(r.exit, 2)
        self.assertIn("touch", r.stderr)
        r = runner.run_hook("PostToolUse", "{rotto", env=self.lab.ts.env(), plugin_root=ROOT)
        self.assertEqual(r.exit, 0)

    def test_malformed_input_missing_fields(self):
        p = self.lab._base("PreToolUse-Write", None, None, tool_name="Write", tool_input={})
        self.assertIn(self.run_with(p).exit, (0, 2))
        p = self.lab._base("PreToolUse-Bash", None, "/non/esiste",
                           tool_input={"command": "ls"})
        self.assertEqual(self.run_with(p).exit, 0)

    def test_inactive_repo_and_off(self):
        ts = TempState()
        try:
            p = sample("PreToolUse-Bash", cwd=str(ts.dir), tool_input={"command": "vietato"})
            self.assertEqual(runner.run_hook("PreToolUse", json.dumps(p), env=ts.env(),
                                             plugin_root=ROOT, checks=self.checks).exit, 0)
        finally:
            ts.cleanup()
        (self.lab.ts.dir / "OFF").write_text("")
        before = self.lab.events("veto")
        r = self.run_with(self.lab._base("PreToolUse-Bash", None, None,
                                         tool_input={"command": "echo vietato"}))
        self.assertEqual((r.exit, self.lab.events("veto")), (0, before))

    def test_off_does_not_open_db(self):
        ts = TempState()
        try:
            (ts.dir / "OFF").write_text("")
            p = sample("PreToolUse-Bash", cwd=str(self.lab.wt), tool_input={"command": "x"})
            runner.run_hook("PreToolUse", json.dumps(p), env=ts.env(), plugin_root=ROOT)
            self.assertFalse((ts.dir / "tollgate.db").exists())
        finally:
            ts.cleanup()

    def test_corrupt_db(self):
        self.lab.conn.close()
        db_path = self.lab.ts.dir / "tollgate.db"
        for suffix in ("-wal", "-shm"):
            Path(str(db_path) + suffix).unlink(missing_ok=True)
        db_path.write_bytes(b"non sono un db" * 100)
        p = self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "ls"})
        r = self.run_with(p)
        self.assertEqual(r.exit, 2)
        self.assertIn("db restore", r.stderr)
        p = self.lab._base("PostToolUse-Bash", None, None, tool_input={"command": "ls"},
                           tool_response={})
        self.assertEqual(self.run_with(p).exit, 0)
        import sqlite3
        self.lab.conn = sqlite3.connect(":memory:")  # il DB guasto non si riapre in tearDown

    def test_internal_timeout(self):
        lab = Lab(toml=DEFAULT_TOML + "[hooks]\ntimeout_s = 1\n")
        try:
            p = lab._base("PreToolUse-Bash", None, None, tool_name="mcp__x__y", tool_input={})
            t0 = time.monotonic()
            r = runner.run_hook("PreToolUse", json.dumps(p), env=lab.ts.env(), now=lab.now,
                                plugin_root=ROOT, checks=self.checks, alarm=True)
            self.assertEqual(r.exit, 2)
            self.assertLess(time.monotonic() - t0, 4)
        finally:
            lab.close()

    def test_session_seen_and_offlog_import(self):
        (self.lab.ts.dir / "off.log").write_text("2026-10-09T08:00:00.000000Z off\n")
        self.run_with(self.lab._base("PreToolUse-Bash", None, None, tool_input={"command": "ls"}))
        seen = self.lab.conn.execute("SELECT session FROM session_seen").fetchall()
        self.assertEqual([r[0] for r in seen], [SESSION])
        self.assertEqual(len(self.lab.events("off")), 1)


def _worker(env, payload, q):
    r = runner.run_hook("PreToolUse", payload, env=env, plugin_root=ROOT)
    q.put(r.exit)


class ConcurrencyTest(unittest.TestCase):
    def test_concurrent_hooks(self):
        lab = Lab()
        try:
            payload = json.dumps(lab._base("PreToolUse-Bash", None, None,
                                           tool_input={"command": "ls"}))
            q = multiprocessing.get_context("spawn").Queue()
            procs = [multiprocessing.get_context("spawn").Process(
                target=_worker, args=(lab.ts.env(), payload, q)) for _ in range(4)]
            for p in procs:
                p.start()
            for p in procs:
                p.join(30)
            self.assertEqual(sorted(q.get(timeout=5) for _ in procs), [0, 0, 0, 0])
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_hook_engine -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_hooks'`.

- [ ] **Step 4: `model.py` e `adapter.py`**

`bin/tollgate_hooks/__init__.py`:

```python
"""Motore degli hook di tollgate: adattatore per Claude Code, contesto, registro, runner."""
```

`bin/tollgate_checks/__init__.py`:

```python
"""Registro dei controlli (spec 3.2): un modulo per controllo, con CHECK e decide(event, ctx)."""
```

`bin/tollgate_hooks/model.py`:

```python
"""Eventi d'ingresso e decisioni (spec 3.2, revisione 21)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

INPUT_EVENTS = ("session_start", "prompt_expansion", "pre_edit", "post_edit", "pre_bash",
                "post_bash", "pre_agent", "post_agent", "pre_send_message", "pre_mcp",
                "subagent_start", "subagent_stop", "subagent_handback", "post_skill")
CONTROL_EVENTS = frozenset({"pre_edit", "pre_bash", "pre_agent", "pre_send_message", "pre_mcp"})


@dataclass(frozen=True)
class Event:
    kind: str
    hook_event: str
    session: str
    cwd: Path
    agent_id: str | None
    agent_type: str | None
    tool_name: str | None
    tool_input: dict
    tool_response: dict | None
    raw: dict


@dataclass(frozen=True)
class Decision:
    kind: str                      # allow | deny | inject | record
    text: str = ""
    rule: str = ""
    op: str = ""
    data: dict = field(default_factory=dict)


def allow() -> Decision:
    return Decision("allow")


def deny(reason: str, rule: str = "") -> Decision:
    return Decision("deny", text=reason, rule=rule)


def inject(text: str) -> Decision:
    return Decision("inject", text=text)


def record(op: str, **data) -> Decision:
    return Decision("record", op=op, data=data)
```

`bin/tollgate_hooks/adapter.py`:

```python
"""Adattatore per Claude Code (spec 3.2): input degli hook → Event; esito → risposta."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Event

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_PRE = {"Bash": "pre_bash", "Agent": "pre_agent", "SendMessage": "pre_send_message"}
_POST = {"Bash": "post_bash", "Agent": "post_agent", "Skill": "post_skill",
         "SubagentHandback": "subagent_handback"}
_PLAIN = {"SessionStart": "session_start", "UserPromptExpansion": "prompt_expansion",
          "SubagentStart": "subagent_start", "SubagentStop": "subagent_stop"}
# Come arriva un'iniezione al modello, per evento (decisione 3; esito di D2 nel Task 1).
# "context": hookSpecificOutput.additionalContext; "system": systemMessage; "stderr": solo stderr.
INJECT_MODE = {"SessionStart": "context", "UserPromptExpansion": "context",
               "PreToolUse": "context", "PostToolUse": "context", "SubagentStart": "context",
               "SubagentStop": "stderr"}


def _kind(hook_event: str, tool: str | None) -> str | None:
    if hook_event in _PLAIN:
        return _PLAIN[hook_event]
    if hook_event == "PreToolUse":
        if tool in EDIT_TOOLS:
            return "pre_edit"
        if tool and tool.startswith("mcp__"):
            return "pre_mcp"
        return _PRE.get(tool)
    if hook_event == "PostToolUse":
        if tool in EDIT_TOOLS:
            return "post_edit"
        return _POST.get(tool)
    return None


def to_event(hook_event: str, raw: dict) -> Event | None:
    if not isinstance(raw, dict):
        raise ValueError("input dell'hook non è un oggetto JSON")
    tool = raw.get("tool_name") if isinstance(raw.get("tool_name"), str) else None
    kind = _kind(hook_event, tool)
    if kind is None:
        return None
    ti = raw.get("tool_input")
    tr = raw.get("tool_response")
    return Event(kind=kind, hook_event=hook_event, session=str(raw.get("session_id") or ""),
                 cwd=Path(str(raw.get("cwd") or ".")), agent_id=raw.get("agent_id") or None,
                 agent_type=raw.get("agent_type") if raw.get("agent_type") is not None else None,
                 tool_name=tool, tool_input=ti if isinstance(ti, dict) else {},
                 tool_response=tr if isinstance(tr, dict) else None, raw=raw)


def edit_path(event: Event) -> str | None:
    p = event.tool_input.get("file_path") or event.tool_input.get("notebook_path")
    return p if isinstance(p, str) and p else None


def render(hook_event: str, deny_text: str | None, inject_text: str | None):
    """Solo l'uscita 2 blocca (7.1). Mai permissionDecision allow (decisione 3)."""
    if deny_text:
        return 2, "", f"tollgate: {deny_text}\n"
    if inject_text:
        mode = INJECT_MODE.get(hook_event, "context")
        if mode == "context":
            out = {"hookSpecificOutput": {"hookEventName": hook_event,
                                          "additionalContext": inject_text}}
            return 0, json.dumps(out, ensure_ascii=False), ""
        if mode == "system":
            return 0, json.dumps({"systemMessage": inject_text}, ensure_ascii=False), ""
        return 0, "", inject_text + "\n"
    return 0, "", ""
```

- [ ] **Step 5: `context.py`**

```python
"""Contesto in sola lettura dei controlli (spec 3.2)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from tollgate_analysis import profiles as prof, waivers
from tollgate_analysis.testguard import DEFAULT_TEST_GLOBS, GuardConfig

from tollgate_core import git, scope, sessions
from tollgate_core.config import Config
from tollgate_core.paths import State

from .model import Event

_AREA_READONLY = re.compile(r"^[^:]+:(reviewer|final)-")


class ReadDb:
    """Il DB visto dai controlli: solo SELECT (un modulo non scrive mai, spec 3.2)."""
    in_transaction = False

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=()):
        if not sql.lstrip().upper().startswith("SELECT"):
            raise PermissionError("il contesto dei controlli è in sola lettura")
        return self._conn.execute(sql, params)


@dataclass
class Ctx:
    event: Event
    state: State
    db: ReadDb
    config: Config
    repo: Path | None
    work: object | None
    bound: bool
    now: object
    plugin_root: Path

    def cfg(self, dotted: str):
        return self.config.get(dotted)

    def component(self, name: str) -> bool:
        return bool(self.config.data["components"].get(name, True))

    def readonly(self, agent_type: str | None) -> bool:
        if not agent_type:
            return False
        return agent_type in self.cfg("review.readonly_agents") or bool(
            _AREA_READONLY.match(agent_type))

    @property
    def stale_minutes(self) -> int:
        return self.cfg("review.stale_minutes")

    @property
    def plugin_bin(self) -> Path:
        return self.plugin_root / "bin" / "tollgate"

    def work_for_path(self, path):
        return sessions.work_for_path(self.db, path)

    @staticmethod
    def rel(path, root) -> str | None:
        try:
            return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return None

    def waiver_file(self, work):
        if work is None or not work["worktree"]:
            return None
        p = Path(work["worktree"]) / waivers.path_for(work["issue"])
        try:
            return waivers.parse(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def approved_waivers(self, work) -> set[str]:
        """Decisione 10: un approve waiver vale in ogni stato dell'atto."""
        if work is None:
            return set()
        return {r[0] for r in self.db.execute(
            "SELECT target FROM acts WHERE type = 'approve' AND object = 'waiver' "
            "AND work = ? AND target IS NOT NULL", (work["id"],))}

    def scope(self, work) -> set[str]:
        return scope.paths(self.db, work["id"]) if work is not None else set()

    def guard_config(self, work, files) -> GuardConfig:
        tg = self.cfg("test_guard")
        profs = self.config.profiles
        active = prof.active_profiles(files, profs, self.cfg("profiles.active"))
        extra = lambda k: [x for n in active for x in profs[n].get(k, [])]  # noqa: E731
        commands = " ".join(str(v) for v in self.cfg("commands").values())
        return GuardConfig(
            test_globs=list(DEFAULT_TEST_GLOBS) + tg["test_globs"] + extra("test_globs"),
            fixture_globs=tg["fixture_globs"], ci_globs=tg["ci_globs"],
            verification_globs=tg["verification_globs"],
            verification_watch=tg["verification_watch"],
            skip_markers=tg["skip_markers"] + extra("skip_markers"),
            assert_markers=tg["assert_markers"] + extra("assert_markers"),
            js_form="jest" if "jest" in commands else "vitest")

    def protected_roots(self, repo) -> list[Path]:
        home = Path(os.path.expanduser("~"))
        roots = [self.state.root.resolve(), (home / ".claude" / "plugins").resolve(),
                 home / ".claude" / "settings.json", home / ".claude" / "settings.local.json"]
        if repo is not None:
            try:
                common = git.common_dir(repo)
                roots += [common / "hooks", common / "config"]
            except git.GitError:
                pass
        return roots
```

- [ ] **Step 6: `registry.py`**

```python
"""Caricamento dei moduli del registro (spec 3.2): ordine, api, componenti."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass

from .model import INPUT_EVENTS

API = 1


@dataclass(frozen=True)
class Loaded:
    name: str
    module: object
    check: dict


@dataclass(frozen=True)
class Broken:
    name: str
    events: tuple | None      # None: eventi ignoti, vale per ogni evento di controllo
    reason: str


def _validate(check) -> str | None:
    if not isinstance(check, dict):
        return "CHECK mancante o non è un dizionario"
    if check.get("api") != API:
        return f"api {check.get('api')!r}, questa versione di tollgate carica api {API}"
    events = check.get("events")
    if not isinstance(events, list) or not events or not set(events) <= set(INPUT_EVENTS):
        return f"eventi non validi: {events!r}"
    if not isinstance(check.get("order"), int):
        return "order mancante"
    comp = check.get("component")
    if comp is not None and not isinstance(comp, str):
        return "component non valido"
    return None


def load(package: str = "tollgate_checks"):
    pkg = importlib.import_module(package)
    loaded, broken = [], []
    for info in pkgutil.iter_modules(pkg.__path__):
        if info.name.startswith("_"):
            continue
        name = f"{package}.{info.name}"
        try:
            mod = importlib.import_module(name)
        except Exception as e:  # un controllo che manca non deve passare in silenzio
            broken.append(Broken(info.name, None, f"import fallito: {e}"))
            continue
        check = getattr(mod, "CHECK", None)
        reason = _validate(check)
        if reason is None and not callable(getattr(mod, "decide", None)):
            reason = "decide mancante"
        if reason is not None:
            events = tuple(check["events"]) if isinstance(check, dict) and isinstance(
                check.get("events"), list) else None
            broken.append(Broken(info.name, events, reason))
            continue
        loaded.append(Loaded(info.name, mod, check))
    loaded.sort(key=lambda m: (m.check["order"], m.name))
    return loaded, broken
```

- [ ] **Step 7: `apply.py`**

```python
"""Operazioni `record` dei controlli (decisione 6): ognuna scrive con tollgate_core."""
from __future__ import annotations

import getpass

from tollgate_core import (acts, effects, events, phases, scope, sessions, subagents, tasks)


def _actor() -> str | None:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return None


def _bind(conn, state, ctx, d):
    phases.bind_session(conn, d["work"], ctx.event.session, now=ctx.now)
    sessions.mark_bound(state, ctx.event.session)


def _act(conn, state, ctx, d):
    acts.record_act(conn, type_=d["type"], object_=d.get("object"), target=d.get("target"),
                    args=d.get("args"), typed_text=d.get("typed_text", ""), actor=_actor(),
                    session=ctx.event.session, work=d.get("work"), head_sha=d.get("head_sha"),
                    now=ctx.now, ttl_minutes=ctx.cfg("acts.ttl_minutes"))


def _subagent_start(conn, state, ctx, d):
    task = d.get("task")
    if d.get("take_pending") and d.get("work") is not None:
        task = tasks.take_pending(conn, d["work"], agent_type=d["type"],
                                  resume=bool(d.get("resume"))) or task
    subagents.start(conn, agent_id=d["agent_id"], type_=d["type"], session=ctx.event.session,
                    work=d.get("work"), task=task, base_sha=d.get("base_sha"),
                    fingerprint=d.get("fingerprint"), now=ctx.now)


def _commit(conn, state, ctx, d):
    events.record_event(conn, "commit", {"sha": d["sha"]}, now=ctx.now,
                        session=ctx.event.session, work=d["work"])
    acts.invalidate_finish(conn, d["work"], d.get("head") or d["sha"], now=ctx.now,
                           session=ctx.event.session)


def _effect_execute(conn, state, ctx, d):
    act = acts.find_usable(conn, type_="approve", object_="effect",
                           target=effects.effect_id(d["key"]), work=d.get("work"),
                           session=ctx.event.session, now=ctx.now)
    if act is None:
        raise acts.ActError("atto approve effect non più valido")
    acts.consume(conn, act["act_id"], type_="approve", object_="effect",
                 target=effects.effect_id(d["key"]), now=ctx.now, work=d.get("work"),
                 session=ctx.event.session)
    effects.mark_executed(conn, key=d["key"], act_id=act["act_id"], now=ctx.now,
                          session=ctx.event.session)


_OPS = {
    "event": lambda c, s, x, d: events.record_event(c, d["type"], d.get("data"), now=x.now,
                                                    session=x.event.session, work=d.get("work")),
    "bind": _bind,
    "act": _act,
    "expire_acts": lambda c, s, x, d: acts.expire_stale(c, now=x.now, session=x.event.session),
    "block": lambda c, s, x, d: phases.open_block(c, s, d["work"], d["type"], d["reason"],
                                                  now=x.now, session=x.event.session),
    "level": lambda c, s, x, d: phases.set_level(c, d["work"], d["level"], now=x.now,
                                                 session=x.event.session),
    "phase": lambda c, s, x, d: phases.set_phase(c, s, d["work"], d["to"], d["cause"],
                                                 now=x.now, session=x.event.session),
    "plan": lambda c, s, x, d: scope.register_plan(
        c, s, d["work"], plan_path=d["plan_path"], plan_sha=d["plan_sha"],
        scope_paths=d["scope"], plan_tasks=[tuple(t) for t in d["tasks"]],
        advance=d["advance"], now=x.now, session=x.event.session),
    "plan_path": lambda c, s, x, d: scope.set_plan_path(c, d["work"], d["plan_path"], now=x.now),
    "subagent_start": _subagent_start,
    "subagent_name": lambda c, s, x, d: subagents.set_name(c, d["agent_id"], d["name"],
                                                           session=x.event.session,
                                                           work=d.get("work"), now=x.now),
    "subagent_report": lambda c, s, x, d: subagents.set_report(c, d["agent_id"], d["text"]),
    "subagent_veto": lambda c, s, x, d: subagents.add_veto(c, d["agent_id"]),
    "subagent_finish": lambda c, s, x, d: subagents.finish(
        c, d["agent_id"], state=d["state"], declared_status=d.get("declared_status"),
        tokens=d.get("tokens"), now=x.now, session=x.event.session),
    "subagent_interrupt": lambda c, s, x, d: subagents.interrupt(c, d["agent_id"], now=x.now,
                                                                 session=x.event.session),
    "task": lambda c, s, x, d: tasks.task_event(c, d["work"], d["number"], d["event"],
                                                now=x.now, session=x.event.session),
    "task_commit": lambda c, s, x, d: tasks.add_commit(c, d["work"], d["number"], d["sha"]),
    "skill_used": lambda c, s, x, d: tasks.add_skill_used(c, d["work"], d["number"], d["skill"]),
    "commit": _commit,
    "effect_request": lambda c, s, x, d: effects.request(
        c, key=d["key"], command=d["command"], work=d.get("work"), sha=d.get("sha"), now=x.now,
        session=x.event.session),
    "effect_execute": _effect_execute,
}
OPS = frozenset(_OPS)


def apply(conn, state, ctx, decision) -> None:
    fn = _OPS.get(decision.op)
    if fn is None:
        raise ValueError(f"operazione record sconosciuta: {decision.op}")
    fn(conn, state, ctx, decision.data)
```

- [ ] **Step 8: `runner.py`**

```python
"""Il percorso di un hook (spec 7.1 dal punto 5, 3.2, 12.1)."""
from __future__ import annotations

import json
import os
import signal
import sqlite3
import traceback
from dataclasses import dataclass
from pathlib import Path

from tollgate_core import clock, db, git, offlog, sessions, subagents
from tollgate_core.acts import ActError
from tollgate_core.config import ConfigError, ConfigNotFound, load_config
from tollgate_core.phases import TransitionError
from tollgate_core.tasks import TaskTransitionError
from tollgate_core.events import record_event
from tollgate_core.paths import resolve_state

from . import adapter, apply as applier, registry
from .context import Ctx, ReadDb
from .model import CONTROL_EVENTS

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
BUDGET = {"session_start": (10, 1500), "subagent_start": (None, 2000)}
DEFAULT_BUDGET = (None, 1500)
_CONTROL_HOOKS = {"PreToolUse"}


@dataclass(frozen=True)
class HookResult:
    exit: int
    stdout: str = ""
    stderr: str = ""


class _Timeout(Exception):
    pass


def _footer(state_root: Path) -> str:
    return (f"Programma: {db.BIN_PATH}. Per spegnere tollgate: /tollgate:off, "
            f"oppure dal terminale: touch {state_root / 'OFF'}")


def _fail(control: bool, msg: str, state_root: Path) -> HookResult:
    text = f"tollgate: {msg}\n{_footer(state_root)}\n"
    if control:
        return HookResult(2, "", text + "Azione negata perché il controllo non è riuscito.\n")
    return HookResult(0, "", text + "Avviso: controllo informativo saltato.\n")


def _off_active(state_root: Path, now) -> bool:
    off = state_root / "OFF"
    if not off.exists():
        return False
    try:
        for line in off.read_text().splitlines():
            if line.startswith("until="):
                return now.timestamp() < int(line[6:])
    except (OSError, ValueError):
        pass
    return True


def _budget(kind: str, text: str) -> str:
    max_lines, max_chars = BUDGET.get(kind, DEFAULT_BUDGET)
    lines = text.splitlines()
    if max_lines is not None and len(lines) > max_lines:
        text = "\n".join(lines[:max_lines - 1] + ["…"])
    if len(text) > max_chars:
        text = text[:max_chars - 1] + "…"
    return text


def _set_alarm(seconds: int) -> None:
    def handler(signum, frame):
        raise _Timeout()
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(max(1, int(seconds)))


def _corrupt(e: BaseException) -> bool:
    code = getattr(e, "sqlite_errorcode", None)
    return code is not None and (code & 0xFF) in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB)


def run_hook(hook_event: str, stdin_text: str, *, env=None, now=None, plugin_root=None,
             checks=None, alarm: bool = False) -> HookResult:
    env = os.environ if env is None else env
    state = resolve_state(env)
    control = hook_event in _CONTROL_HOOKS
    now = now or clock.now()
    if alarm:
        _set_alarm(20)
    conn = None
    try:
        try:
            raw = json.loads(stdin_text)
            event = adapter.to_event(hook_event, raw)
        except (ValueError, TypeError) as e:
            return _fail(control, f"input dell'hook non valido ({e})", state.root)
        if event is None or _off_active(state.root, now):
            return HookResult(0)
        control = event.kind in CONTROL_EVENTS
        cwd_ok = event.cwd.is_dir()
        root = git.toplevel(event.cwd) if cwd_ok else None
        marker = state.root / sessions.BOUND_DIR / event.session
        if root is None and not marker.exists():
            return HookResult(0)
        conn = db.open_db(state)
        offlog.import_log(conn, state)
        if event.session:
            sessions.touch(conn, event.session, now=now)
        if event.agent_id and subagents.get(conn, event.agent_id) is not None:
            subagents.touch(conn, event.agent_id, now=now)
        bound = sessions.bound_work(conn, event.session) if event.session else None
        work = bound or (sessions.work_for_path(conn, event.cwd) if cwd_ok else None)
        if work is not None and work["work_base_sha"] and work["worktree"] \
                and Path(work["worktree"]).is_dir():
            cfg_repo, ref = Path(work["worktree"]), work["work_base_sha"]
        elif root is not None:
            cfg_repo, ref = root, git.default_ref(root)
        else:
            return HookResult(0)
        if ref is None:
            return HookResult(0, "", "tollgate: nessun riferimento remoto (origin/HEAD, main, "
                                     "master): repo trattato come non attivo\n")
        try:
            config = load_config(state, cfg_repo, ref, env=env)
        except ConfigNotFound:
            return HookResult(0)
        except ConfigError as e:
            return _fail(control, f"tollgate.toml non valido: {e}", state.root)
        if alarm:
            _set_alarm(config.get("hooks.timeout_s"))
        ctx = Ctx(event, state, ReadDb(conn), config, root, work,
                  bound is not None and work is not None and bound["id"] == work["id"], now,
                  Path(plugin_root) if plugin_root else PLUGIN_ROOT)
        loaded, broken = checks if checks is not None else registry.load()
        denial, rule, injects, records = None, "", [], []
        for b in broken:
            if (b.events is None and control) or (b.events and event.kind in b.events):
                if denial is None:
                    denial, rule = f"controllo «{b.name}» non caricato: {b.reason}", b.name
        for m in loaded:
            if event.kind not in m.check["events"]:
                continue
            comp = m.check.get("component")
            if comp and not ctx.component(comp):
                continue
            try:
                decisions = m.module.decide(event, ctx) or []
            except _Timeout:
                raise
            except Exception as e:
                if control and denial is None:
                    denial, rule = f"controllo «{m.name}» in errore: {e}", m.name
                elif not control:
                    injects.append(f"(tollgate: controllo «{m.name}» in errore: {e})")
                continue
            for d in decisions:
                if d.kind == "deny" and denial is None:
                    denial, rule = d.text, d.rule or m.name
                elif d.kind == "inject" and d.text:
                    injects.append(d.text)
                elif d.kind == "record":
                    records.append(d)
        for d in records:
            try:
                applier.apply(conn, state, ctx, d)
            except (TransitionError, TaskTransitionError, ActError, ValueError) as e:
                # una registrazione non più possibile (fase cambiata, atto scaduto) non
                # annulla le altre né il veto: si riporta e si va avanti
                injects.append(f"(tollgate: registrazione «{d.op}» non applicata: {e})")
        if denial:
            record_event(conn, "veto", {"event": event.kind, "rule": rule, "reason": denial},
                         now=now, session=event.session or None,
                         work=work["id"] if work is not None else None)
        inject_text = _budget(event.kind, "\n".join(injects)) if injects else None
        code, out, err = adapter.render(hook_event, denial, inject_text)
        return HookResult(code, out, err)
    except _Timeout:
        return _fail(control, "controllo oltre la scadenza ([hooks] timeout_s)", state.root)
    except db.DbCorrupt as e:
        return _fail(control, str(e), state.root)
    except db.DbError as e:
        return _fail(control, str(e), state.root)
    except sqlite3.DatabaseError as e:
        if _corrupt(e):
            return _fail(control, f"DB di tollgate guasto: {e}. Ripristino dal terminale: "
                                  f"{db.restore_hint()}", state.root)
        return _fail(control, f"errore del DB: {e}", state.root)
    except Exception as e:
        tb = traceback.format_exc(limit=3)
        return _fail(control, f"errore interno: {e}\n{tb}", state.root)
    finally:
        if alarm:
            signal.alarm(0)
        if conn is not None:
            conn.close()
```

- [ ] **Step 9: Sottocomando `hook`**

In `build_parser` di `bin/tollgate_core/cli.py`:

```python
    hp = sub.add_parser("hook", help="solo per hooks/run: adattatore per Claude Code")
    hp.add_argument("event", metavar="evento")
```

In `main`, subito dopo `if args.cmd is None:` e prima di `state = resolve_state()`:

```python
    if args.cmd == "hook":
        from tollgate_hooks.runner import run_hook
        r = run_hook(args.event, sys.stdin.read(), alarm=True)
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        return r.exit
```

- [ ] **Step 10: Verificare che passino**

Run: `tests/run`
Expected: OK. Se `test_concurrent_hooks` dà `database is locked`, la causa è nel runner (transazioni lunghe), non nel test: le scritture devono restare brevi, una per operazione.

- [ ] **Step 11: Commit**

```bash
git add bin/tollgate_hooks bin/tollgate_checks/__init__.py bin/tollgate_core/cli.py tests/hookkit.py tests/test_hook_engine.py
git commit -m "tollgate P2: motore degli hook (adattatore, contesto, registro, runner) e tollgate hook"
```

---
### Task 13: Wrapper `hooks/run`, `hooks.json`, `plugin.json`, skill `off` e `on`

**Files:**
- Create: `hooks/run` (eseguibile)
- Create: `hooks/hooks.json`
- Create: `.claude-plugin/plugin.json`
- Create: `skills/off/SKILL.md`, `skills/on/SKILL.md`
- Test: `tests/test_wrapper.py`, `tests/test_manifest.py`

**Interfaces:**
- Consumes: `bin/tollgate hook <evento>` (Task 12); esito D1 del Task 1 per `dependencies`.
- Produces: il wrapper con le uscite di 7.1 (criterio 14); `OFF` con `until=<epoch>`; `off.log` e `skipped.log` nella cartella di stato (decisione 5); il segnalino `bound/<sessione>` letto dal wrapper (decisione 22).

- [ ] **Step 1: Test del wrapper**

`tests/test_wrapper.py`:

```python
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.helpers import ROOT, TempState, make_origin_repo

FAKE_BIN = textwrap.dedent('''\
    #!/usr/bin/env python3
    import os, sys, time
    sys.stdin.read()
    m = os.environ.get("FAKE_MODE", "0")
    if m == "sleep":
        time.sleep(30)
    if m == "raise":
        raise RuntimeError("guasto")
    print("OUT")
    sys.stderr.write("ERR\\n")
    sys.exit(int(m))
''')
TOML = 'schema_version = 1\n[gate]\nmode = "protected"\n[hooks]\ntimeout_s = 1\n'
TOOLS = ["bash", "git", "sed", "tr", "head", "cat", "date", "mkdir", "rm", "mktemp", "sleep",
         "awk", "dirname", "kill", "env"]


class WrapperTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate wrapper "))
        self.plugin = self.tmp / "plugin"
        (self.plugin / "hooks").mkdir(parents=True)
        (self.plugin / "bin").mkdir()
        shutil.copy(ROOT / "hooks" / "run", self.plugin / "hooks" / "run")
        (self.plugin / "bin" / "tollgate").write_text(FAKE_BIN)
        (self.plugin / "bin" / "tollgate").chmod(0o755)
        self.repo, _, _ = make_origin_repo(self.tmp / "r", {"a.txt": "a\n"}, TOML)
        self.plain = self.tmp / "plain"
        self.plain.mkdir()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_wrapper(self, event, payload=None, *, cwd=None, mode="0", path=None):
        payload = payload or {"hook_event_name": event, "session_id": "s1",
                              "cwd": str(cwd or self.repo), "tool_name": "Bash",
                              "tool_input": {"command": "ls"}}
        env = self.ts.env()
        env["FAKE_MODE"] = mode
        if path is not None:
            env["PATH"] = path
        t0 = time.monotonic()
        r = subprocess.run([str(self.plugin / "hooks" / "run"), event],
                           input=json.dumps(payload), capture_output=True, text=True, env=env,
                           cwd=str(cwd or self.repo), timeout=30)
        return r, time.monotonic() - t0

    def test_control_errors_become_2(self):
        for mode in ("1", "127", "raise"):
            with self.subTest(mode=mode):
                r, _ = self.run_wrapper("PreToolUse", mode=mode)
                self.assertEqual(r.returncode, 2)
                self.assertIn(f"touch {self.ts.dir}/OFF", r.stderr)
                self.assertIn(str(self.plugin / "bin" / "tollgate"), r.stderr)

    def test_timeout_becomes_2(self):
        r, elapsed = self.run_wrapper("PreToolUse", mode="sleep")
        self.assertEqual(r.returncode, 2)
        self.assertLess(elapsed, 10)

    def test_informative_errors_become_0(self):
        for event in ("PostToolUse", "SubagentStop", "SessionStart", "UserPromptExpansion"):
            with self.subTest(event=event):
                self.assertEqual(self.run_wrapper(event, mode="1")[0].returncode, 0)

    def test_zero_and_two_pass_through(self):
        r, _ = self.run_wrapper("PreToolUse", mode="2")
        self.assertEqual((r.returncode, r.stdout.strip()), (2, "OUT"))
        self.assertEqual(self.run_wrapper("SubagentStop", mode="2")[0].returncode, 2)
        self.assertEqual(self.run_wrapper("PreToolUse", mode="0")[0].returncode, 0)

    def test_inactive_repo_exits_0_without_running(self):
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, mode="2")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_bound_marker_makes_any_dir_active(self):
        (self.ts.dir / "bound").mkdir()
        (self.ts.dir / "bound" / "s1").touch()
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, mode="2")
        self.assertEqual(r.returncode, 2)

    def _path_without_python(self):
        d = self.tmp / "nopy"
        d.mkdir(exist_ok=True)
        for t in TOOLS:
            src = shutil.which(t)
            if src and not (d / t).exists():
                os.symlink(src, d / t)
        return str(d)

    def test_without_python(self):
        path = self._path_without_python()
        self.assertEqual(self.run_wrapper("PreToolUse", path=path)[0].returncode, 2)
        self.assertEqual(self.run_wrapper("PostToolUse", path=path)[0].returncode, 0)
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, path=path)
        self.assertEqual(r.returncode, 0)

    def test_off_on_and_expiry(self):
        off = {"hook_event_name": "UserPromptExpansion", "session_id": "s1",
               "cwd": str(self.repo), "command_name": "tollgate:off", "command_args": "2",
               "expansion_type": "slash_command"}
        r, _ = self.run_wrapper("UserPromptExpansion", off, mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("until=", (self.ts.dir / "OFF").read_text())
        r, _ = self.run_wrapper("PreToolUse", mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("spento", r.stderr)
        self.assertIn("PreToolUse", (self.ts.dir / "skipped.log").read_text())
        on = dict(off, command_name="tollgate:on", command_args="")
        self.run_wrapper("UserPromptExpansion", on)
        self.assertFalse((self.ts.dir / "OFF").exists())
        log = (self.ts.dir / "off.log").read_text().splitlines()
        self.assertRegex(log[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.000000Z off \d+$")
        self.assertRegex(log[1], r"Z on$")
        (self.ts.dir / "OFF").write_text(f"until={int(time.time()) - 60}\n")
        self.assertEqual(self.run_wrapper("PreToolUse", mode="2")[0].returncode, 2)
        self.assertFalse((self.ts.dir / "OFF").exists())

    def test_off_without_hours(self):
        off = {"hook_event_name": "UserPromptExpansion", "session_id": "s1",
               "cwd": str(self.plain), "command_name": "tollgate:off", "command_args": ""}
        self.run_wrapper("UserPromptExpansion", off)
        self.assertEqual((self.ts.dir / "OFF").read_text(), "")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_manifest.py`:

```python
import json
import re
import unittest

from tests.helpers import ROOT


class ManifestTest(unittest.TestCase):
    def test_hooks_json(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptExpansion", "PreToolUse",
                                      "PostToolUse", "SubagentStart", "SubagentStop"})
        pre = hooks["PreToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "Agent", "SendMessage"):
            self.assertRegex(tool, f"^(?:{pre})$")
        self.assertRegex("mcp__srv__x", f"^(?:{pre})$")
        self.assertNotRegex("Read", f"^(?:{pre})$")
        post = hooks["PostToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "Bash", "Agent", "Skill", "SubagentHandback"):
            self.assertRegex(tool, f"^(?:{post})$")
        for event, groups in hooks.items():
            for h in groups[0]["hooks"]:
                self.assertEqual(h["command"], f'"${{CLAUDE_PLUGIN_ROOT}}/hooks/run" {event}')
                self.assertEqual(h["timeout"], 90)

    def test_plugin_json(self):
        p = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(p["name"], "tollgate")
        from tollgate_core import VERSION
        self.assertEqual(p["version"], VERSION)
        dep = p["dependencies"][0]
        self.assertEqual((dep["name"], dep["marketplace"]),
                         ("superpowers", "claude-plugins-official"))

    def test_off_on_skills_user_only(self):
        for name in ("off", "on"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
            self.assertRegex(text, rf"(?m)^name: {name}$")

    def test_wrapper_executable(self):
        import os
        self.assertTrue(os.access(ROOT / "hooks" / "run", os.X_OK))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_wrapper tests.test_manifest -v`
Expected: FAIL (file mancanti).

- [ ] **Step 3: `hooks/run`**

```bash
#!/usr/bin/env bash
# Wrapper degli hook di tollgate (spec 7.1). Uso: hooks/run <EventoDiClaudeCode>
# Solo l'uscita 2 blocca: qui ogni errore di un hook di controllo diventa 2,
# ogni errore di un hook informativo diventa 0 con un avviso.
set -u
EVENT="${1:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/bin/tollgate"
STATE="${HOME}/.local/state/tollgate"
if [ -n "${TOLLGATE_STATE:-}" ] && [ -f "${TOLLGATE_STATE}/.tollgate-test" ]; then
  STATE="$TOLLGATE_STATE"
fi
OFF="$STATE/OFF"
HINT="Per spegnere tollgate: /tollgate:off, oppure dal terminale: touch $STATE/OFF"
case "$EVENT" in PreToolUse) CONTROL=yes ;; *) CONTROL=no ;; esac
INPUT="$(cat)"

now_iso() { date -u +%Y-%m-%dT%H:%M:%S.000000Z; }
iso_of() { date -u -d "@$1" +%Y-%m-%dT%H:%M:%S.000000Z 2>/dev/null \
  || date -u -r "$1" +%Y-%m-%dT%H:%M:%S.000000Z; }
# Valore stringa di una chiave dell'input, senza jq (best effort: basta per cwd, sessione, comando).
json_str() {
  printf '%s' "$INPUT" | tr '\n' ' ' \
    | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -n 1
}

# 1. Interruttore senza Python né DB.
if [ "$EVENT" = "UserPromptExpansion" ]; then
  CMD="$(json_str command_name)"
  if [ "$CMD" = "tollgate:off" ]; then
    mkdir -p "$STATE"
    HOURS="$(json_str command_args | tr -cd '0-9')"
    UNTIL=""
    if [ -n "$HOURS" ]; then
      UNTIL=$(( $(date +%s) + HOURS * 3600 ))
      printf 'until=%s\n' "$UNTIL" > "$OFF"
    else
      : > "$OFF"
    fi
    printf '%s off %s\n' "$(now_iso)" "$UNTIL" | sed 's/ $//' >> "$STATE/off.log"
    echo "tollgate spento${HOURS:+ per $HOURS ore}. Per riaccenderlo: /tollgate:on" >&2
    exit 0
  fi
  if [ "$CMD" = "tollgate:on" ] && [ -e "$OFF" ]; then
    rm -f "$OFF"
    printf '%s on\n' "$(now_iso)" >> "$STATE/off.log"
    echo "tollgate acceso" >&2
  fi
fi

# 2. OFF attivo, salvo scadenza passata.
if [ -e "$OFF" ]; then
  UNTIL="$(sed -n 's/^until=\([0-9][0-9]*\)$/\1/p' "$OFF" 2>/dev/null | head -n 1)"
  if [ -n "$UNTIL" ] && [ "$(date +%s)" -ge "$UNTIL" ]; then
    rm -f "$OFF"
    printf '%s on\n' "$(iso_of "$UNTIL")" >> "$STATE/off.log"
  else
    printf '%s skip %s\n' "$(now_iso)" "$EVENT" >> "$STATE/skipped.log" 2>/dev/null
    echo "tollgate spento ($OFF): nessun controllo. Per riaccenderlo: /tollgate:on" >&2
    exit 0
  fi
fi

# 3. Repo attivo? tollgate.toml sul ramo predefinito di origin, senza rete.
CWD="$(json_str cwd)"
[ -n "$CWD" ] && [ -d "$CWD" ] || CWD="$PWD"
ACTIVE=no; FOUND=no; REF=""
B="$(git -C "$CWD" config --get tollgate.defaultBranch 2>/dev/null)"
for ref in ${B:+"origin/$B"} origin/HEAD origin/main origin/master; do
  if git -C "$CWD" rev-parse --verify -q "$ref^{commit}" >/dev/null 2>&1; then
    FOUND=yes; REF="$ref"
    git -C "$CWD" cat-file -e "$ref:tollgate.toml" 2>/dev/null && ACTIVE=yes
    break
  fi
done
SESSION="$(json_str session_id | tr -cd 'A-Za-z0-9_-')"
if [ "$ACTIVE" = no ] && [ -n "$SESSION" ] && [ -e "$STATE/bound/$SESSION" ]; then
  ACTIVE=yes   # sessione legata a un lavoro: le regole valgono in ogni cartella (6.6)
fi
if [ "$ACTIVE" = no ]; then
  if [ "$FOUND" = no ] && git -C "$CWD" rev-parse --git-dir >/dev/null 2>&1; then
    echo "tollgate: nessun riferimento remoto (origin/HEAD, main, master): repo trattato come non attivo" >&2
  fi
  exit 0
fi

# 4. Python >= 3.11.
PY=""
for c in python3 python3.13 python3.12 python3.11; do
  if command -v "$c" >/dev/null 2>&1 \
     && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "tollgate: serve Python >= 3.11 per i controlli. Programma: $BIN. $HINT" >&2
  [ "$CONTROL" = yes ] && exit 2
  exit 0
fi

# 5. Il controllo, con un cane da guardia oltre la scadenza interna di Python (decisione 4).
TIMEOUT=20
if [ -n "$REF" ]; then
  T="$(git -C "$CWD" show "$REF:tollgate.toml" 2>/dev/null | awk '
    /^\[hooks\]/ { s = 1; next } /^\[/ { s = 0 }
    s && /^[[:space:]]*timeout_s[[:space:]]*=/ { gsub(/[^0-9]/, "", $0); print; exit }')"
  [ -n "$T" ] && TIMEOUT="$T"
fi
TMPO="$(mktemp)"; TMPE="$(mktemp)"
trap 'rm -f "$TMPO" "$TMPE"' EXIT
printf '%s' "$INPUT" | "$PY" "$BIN" hook "$EVENT" >"$TMPO" 2>"$TMPE" &
PID=$!
( sleep $(( TIMEOUT + 2 )) && kill -TERM "$PID" ) >/dev/null 2>&1 </dev/null &
WD=$!
wait "$PID"; RC=$?
kill "$WD" >/dev/null 2>&1

# 6-7. Uscite.
if [ "$RC" -eq 0 ] || [ "$RC" -eq 2 ]; then
  cat "$TMPO"; cat "$TMPE" >&2
  exit "$RC"
fi
mkdir -p "$STATE"
{ printf '%s %s rc=%s\n' "$(now_iso)" "$EVENT" "$RC"; cat "$TMPE"; } >> "$STATE/hook-errors.log" 2>/dev/null
if [ "$CONTROL" = yes ]; then
  cat "$TMPE" >&2
  echo "tollgate: controllo non riuscito (uscita $RC): azione negata. Log: $STATE/hook-errors.log. Programma: $BIN. $HINT" >&2
  exit 2
fi
echo "tollgate: avviso, hook $EVENT non riuscito (uscita $RC) e ignorato. $HINT" >&2
exit 0
```

Poi `chmod +x hooks/run`.

- [ ] **Step 4: `hooks.json`, `plugin.json`, skill**

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" SessionStart", "timeout": 90}]}],
    "UserPromptExpansion": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" UserPromptExpansion", "timeout": 90}]}],
    "PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash|Agent|SendMessage|mcp__.*", "hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" PreToolUse", "timeout": 90}]}],
    "PostToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash|Agent|Skill|SubagentHandback", "hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" PostToolUse", "timeout": 90}]}],
    "SubagentStart": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" SubagentStart", "timeout": 90}]}],
    "SubagentStop": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" SubagentStop", "timeout": 90}]}]
  }
}
```

`.claude-plugin/plugin.json` (il campo `version` della dipendenza secondo l'esito D1 del Task 1: con D1 «sì» `">=6.4.1 <7.0.0"`; con D1 «no» o «non determinato» la chiave `version` si toglie e il ledger registra la `Ruling:`; il controllo della versione passa a `start` in P3):

```json
{
  "name": "tollgate",
  "version": "0.1.0",
  "description": "Dall'issue GitHub alla PR verificata: guardrail locali per Claude Code e gate su GitHub.",
  "author": {"name": "ginz0ls"},
  "license": "MIT",
  "dependencies": [
    {"name": "superpowers", "version": ">=6.4.1 <7.0.0", "marketplace": "claude-plugins-official"}
  ]
}
```

`skills/off/SKILL.md`:

```markdown
---
name: off
description: Spegne tollgate su questa macchina, per sempre o per un numero di ore. Solo l'utente.
disable-model-invocation: true
argument-hint: "[ore]"
---

Il wrapper degli hook ha già spento tollgate quando hai digitato il comando, senza Python né DB.
Riferisci all'utente il messaggio dell'hook («tollgate spento…»). Ricordagli che con tollgate
spento non gira nessun guardrail locale, che il gate su GitHub resta attivo, e che si riaccende
con /tollgate:on. Non eseguire comandi.
```

`skills/on/SKILL.md`:

```markdown
---
name: on
description: Riaccende tollgate su questa macchina. Solo l'utente.
disable-model-invocation: true
---

Il wrapper degli hook ha già tolto l'interruttore quando hai digitato il comando.
Riferisci all'utente che tollgate è acceso. Non eseguire comandi.
```

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK. Se `claude` è installato, eseguire anche `claude plugin validate .` (se il comando esiste, esito D1) e riportare l'esito nel ledger; non installare il plugin.

- [ ] **Step 6: Commit**

```bash
git add hooks/run hooks/hooks.json .claude-plugin/plugin.json skills/off/SKILL.md skills/on/SKILL.md tests/test_wrapper.py tests/test_manifest.py
git commit -m "tollgate P2: wrapper hooks/run, hooks.json, plugin.json, interruttore off/on"
```

---
### Task 14: Controlli `SessionStart` e `UserPromptExpansion` (atti)

**Files:**
- Create: `bin/tollgate_checks/_common.py`
- Create: `bin/tollgate_checks/session.py`
- Create: `bin/tollgate_checks/acts.py`
- Test: `tests/test_check_session.py`, `tests/test_check_acts.py`

**Interfaces:**
- Consumes: `Ctx`, `model.*`, `sessions`, `subagents`, `git`, `paths.repo_key`, `acts.ACT_TYPES`, `acts.APPROVE_OBJECTS`.
- Produces in `_common.py` (aiuti condivisi dai moduli; il nome con `_` non viene caricato dal registro):
  - `repo_key_of(repo) -> str | None`; `orphan_tg(ctx, repo) -> int | None` (numero dell'issue di un ramo `tg/<N>-*` senza lavoro attivo); `governing_work(ctx, path) -> object | None` (il lavoro le cui regole valgono per quel percorso: quello della sessione legata, o quello del cui worktree il percorso fa parte); `is_docs_md(rel) -> bool`; `locked_docs(work) -> set[str]`; `waiver_hint(v, issue) -> str`; `explain(violations, issue) -> str`; `status_lines(ctx, work) -> list[str]`.
- Modulo `session` (evento `session_start`, ordine 10): lega la sessione se il `cwd` è nel worktree di un lavoro attivo; segna `interrupted` i subagenti `running` di sessioni non vive; fa scadere gli atti; inietta stato e checkpoint (≤ 10 righe, ≤ 1.500 caratteri dal runner); indica `adopt` per un ramo `tg/*` senza lavoro.
- Modulo `acts` (evento `prompt_expansion`, ordine 10): registra l'atto con oggetto e target della decisione 15.

- [ ] **Step 1: Test**

`tests/test_check_session.py`:

```python
import json
import unittest
from datetime import timedelta

from tests.hookkit import SESSION, T0, Lab, sample
from tollgate_core import phases, sessions, subagents


def start_payload(lab, session, cwd=None, source="startup"):
    return sample("SessionStart-none", session_id=session, cwd=str(cwd or lab.wt), source=source)


def context_of(r):
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout else ""


class SessionStartTest(unittest.TestCase):
    def test_binds_new_session_in_worktree(self):
        lab = Lab()
        try:
            r = lab.hook(start_payload(lab, "s-nuova"))
            self.assertEqual(r.exit, 0)
            self.assertIn("s-nuova", json.loads(phases.get_work(lab.conn, lab.work)["sessions"]))
            self.assertTrue((lab.ts.dir / "bound" / "s-nuova").is_file())
            ctx = context_of(r)
            self.assertIn("#7", ctx)
            self.assertIn("execution", ctx)
            self.assertLessEqual(len(ctx.splitlines()), 10)
            self.assertLessEqual(len(ctx), 1500)
        finally:
            lab.close()

    def test_main_checkout_does_not_bind(self):
        lab = Lab(bind=False)
        try:
            lab.hook(start_payload(lab, "s-fuori", cwd=lab.main))
            self.assertNotIn("s-fuori", json.loads(phases.get_work(lab.conn,
                                                                   lab.work)["sessions"]))
        finally:
            lab.close()

    def test_interrupts_only_dead_sessions(self):
        lab = Lab()
        try:
            sessions.touch(lab.conn, "morta", now=T0 - timedelta(hours=2))
            sessions.touch(lab.conn, "viva", now=lab.now)
            for aid, sess in (("a-morto", "morta"), ("a-vivo", "viva")):
                subagents.start(lab.conn, agent_id=aid, type_="tollgate:implementer",
                                session=sess, work=lab.work, task=None, base_sha=lab.base,
                                fingerprint="f", now=T0)
            lab.hook(start_payload(lab, SESSION, source="resume"))
            self.assertEqual(subagents.get(lab.conn, "a-morto")["state"], "interrupted")
            self.assertEqual(subagents.get(lab.conn, "a-vivo")["state"], "running")
        finally:
            lab.close()

    def test_checkpoint_is_injected(self):
        lab = Lab()
        try:
            cp = lab.wt / "docs/superpowers/reviews/7/checkpoint.md"
            cp.parent.mkdir(parents=True)
            cp.write_text("Prossimo passo: task 3\n")
            r = lab.hook(start_payload(lab, SESSION, source="clear"))
            self.assertIn("Prossimo passo: task 3", context_of(r))
        finally:
            lab.close()

    def test_orphan_tg_branch_points_to_adopt(self):
        lab = Lab(work=False)
        try:
            r = lab.hook(start_payload(lab, "s1"))
            self.assertIn("/tollgate:adopt #7", context_of(r))
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

`tests/test_check_acts.py`:

```python
import unittest

from tests.hookkit import SESSION, Lab, sample
from tollgate_core import git


def expand(lab, name, args, session=SESSION, cwd=None):
    return lab.hook(sample("UserPromptExpansion-none", session_id=session,
                           cwd=str(cwd or lab.wt), command_name=name, command_args=args,
                           prompt=f"/{name} {args}".strip()))


class ActsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def acts(self):
        return [dict(r) for r in self.lab.conn.execute("SELECT * FROM acts ORDER BY n")]

    def test_approve_waiver(self):
        r = expand(self.lab, "tollgate:approve", "waiver w-7-1")
        self.assertEqual(r.exit, 0)
        a = self.acts()[0]
        self.assertEqual((a["type"], a["object"], a["target"], a["work"], a["session"]),
                         ("approve", "waiver", "w-7-1", self.lab.work, SESSION))
        self.assertEqual(a["typed_text"], "/tollgate:approve waiver w-7-1")

    def test_finish_bound_to_head(self):
        expand(self.lab, "tollgate:finish", "")
        a = self.acts()[0]
        self.assertEqual((a["type"], a["head_sha"]), ("finish", git.head(self.lab.wt)))

    def test_approve_pr_targets_head(self):
        expand(self.lab, "tollgate:approve", "pr")
        self.assertEqual(self.acts()[0]["target"], git.head(self.lab.wt))

    def test_invalid_object_not_recorded(self):
        r = expand(self.lab, "tollgate:approve", "boh 3")
        self.assertEqual(self.acts(), [])
        self.assertIn("non registrato", r.stdout)

    def test_adopt_from_unbound_session(self):
        expand(self.lab, "tollgate:adopt", "#9", session="altra", cwd=self.lab.main)
        a = self.acts()[0]
        self.assertEqual((a["type"], a["target"], a["work"]), ("adopt", "9", None))

    def test_non_tollgate_and_status_are_not_acts(self):
        expand(self.lab, "superpowers:brainstorming", "")
        expand(self.lab, "tollgate:status", "")
        self.assertEqual(self.acts(), [])

    def test_skill_tool_does_not_create_acts(self):
        p = sample("PostToolUse-Skill", session_id=SESSION, cwd=str(self.lab.wt),
                   tool_name="Skill", tool_input={"skill": "tollgate:approve",
                                                  "args": "waiver w-7-1"},
                   tool_response={"success": True})
        self.lab.hook(p)
        self.assertEqual(self.acts(), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_session tests.test_check_acts -v`
Expected: FAIL (nessun legame, nessun atto: i moduli non esistono).

- [ ] **Step 3: `_common.py`**

```python
"""Aiuti condivisi dai controlli (non è un controllo: il registro salta i nomi con _)."""
from __future__ import annotations

import re
from pathlib import Path

from tollgate_core import git
from tollgate_core.paths import repo_key

_TG = re.compile(r"^tg/(\d+)-")


def repo_key_of(repo) -> str | None:
    url = git.origin_url(repo) if repo else None
    return repo_key(url) if url else None


def orphan_tg(ctx, repo) -> int | None:
    """Ramo tg/<N>-* senza lavoro attivo per (repo, N): DB perso, serve adopt (12.4)."""
    if repo is None:
        return None
    m = _TG.match(git.branch(repo) or "")
    if not m:
        return None
    key = repo_key_of(repo)
    row = ctx.db.execute("SELECT 1 FROM work_items WHERE repo_key = ? AND issue = ? "
                         "AND phase <> 'closed'", (key, int(m.group(1)))).fetchone()
    return None if row else int(m.group(1))


def governing_work(ctx, path):
    """Le regole complete valgono nella sessione legata e per ogni percorso nel worktree (6.6)."""
    if ctx.bound and ctx.work is not None:
        return ctx.work
    return ctx.work_for_path(path) if path is not None else None


def is_docs_md(rel: str | None) -> bool:
    return bool(rel) and rel.startswith("docs/superpowers/") and rel.endswith(".md")


def locked_docs(work) -> set[str]:
    """Spec bloccata dopo approve spec, piano bloccato dopo la registrazione dello scope (6.2)."""
    out = set()
    if work["plan_sha"] and work["plan_path"]:
        out.add(work["plan_path"])
    if work["spec_path"] and work["worktree"]:
        approval = Path(work["worktree"]) / f"docs/superpowers/reviews/{work['issue']}" \
                                           "/spec-approval.md"
        if approval.exists():
            out.add(work["spec_path"])
    return out


def waiver_hint(v, issue) -> str:
    target = f"--test {' --test '.join(v.ids)} " if v.ids else ""
    return (f"tollgate waiver add {v.waiver_type} {v.path} {target}"
            f"--choice … --why … --cost …")


def explain(violations, issue) -> str:
    lines = [f"- {v.path}: {v.detail} (deroga: {waiver_hint(v, issue)})" for v in violations]
    return "\n".join(lines)


def status_lines(ctx, work) -> list[str]:
    lines = [f"tollgate: lavoro #{work['issue']} ({work['level']}), fase {work['phase']}"
             + (f" (prima: {work['phase_before_block']})" if work["phase"] == "blocked" else "")]
    for b in ctx.db.execute("SELECT id, type, reason FROM blocks WHERE work = ? AND closed "
                            "IS NULL ORDER BY id LIMIT 3", (work["id"],)):
        lines.append(f"blocco {b['id']} ({b['type']}): {b['reason'][:120]}")
    counts = {r[0]: r[1] for r in ctx.db.execute(
        "SELECT state, count(*) FROM tasks WHERE work = ? GROUP BY state", (work["id"],))}
    if counts:
        lines.append("task: " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    return lines
```

- [ ] **Step 4: `session.py`**

```python
"""SessionStart (spec 7.2): legame, subagenti di sessioni morte, stato e checkpoint."""
from __future__ import annotations

from pathlib import Path

from tollgate_core import sessions, subagents
from tollgate_hooks.model import inject, record

from ._common import orphan_tg, status_lines

CHECK = {"api": 1, "events": ["session_start"], "component": None, "order": 10}


def decide(event, ctx):
    out = [record("expire_acts")]
    for row in subagents.running(ctx.db):
        if row["session"] and row["session"] != event.session and not sessions.alive(
                ctx.db, row["session"], now=ctx.now, stale_minutes=ctx.stale_minutes):
            out.append(record("subagent_interrupt", agent_id=row["id"]))
    work = ctx.work
    if work is not None and not ctx.bound:
        path_work = ctx.work_for_path(event.cwd)
        if path_work is not None and path_work["id"] == work["id"]:
            out.append(record("bind", work=work["id"]))
    if work is None:
        n = orphan_tg(ctx, ctx.repo)
        if n is not None:
            out.append(inject(f"tollgate: ramo tg/{n}-* senza lavoro nel DB (DB perso?). Le "
                              f"scritture sono negate finché l'utente non lancia "
                              f"/tollgate:adopt #{n}."))
        return out
    lines = status_lines(ctx, work)
    if work["worktree"]:
        cp = Path(work["worktree"]) / f"docs/superpowers/reviews/{work['issue']}/checkpoint.md"
        try:
            lines += ["checkpoint:"] + cp.read_text(encoding="utf-8").strip().splitlines()
        except OSError:
            pass
    out.append(inject("\n".join(lines)))
    return out
```

- [ ] **Step 5: `acts.py`**

```python
"""UserPromptExpansion (spec 8.4): l'atto da command_name (forma lunga) e command_args."""
from __future__ import annotations

import shlex
from pathlib import Path

from tollgate_core import acts, git
from tollgate_hooks.model import inject, record

CHECK = {"api": 1, "events": ["prompt_expansion"], "component": None, "order": 10}
_TARGET_ARG = {"waiver", "effect", "finding", "level", "rounds", "spec"}


def _refuse(why: str):
    return [inject(f"tollgate: atto non registrato: {why}")]


def decide(event, ctx):
    name = str(event.raw.get("command_name") or "")
    if not name.startswith("tollgate:"):
        return []
    type_ = name.split(":", 1)[1]
    if type_ in ("off", "on") or type_ not in acts.ACT_TYPES:
        return []
    raw_args = str(event.raw.get("command_args") or "")
    try:
        args = shlex.split(raw_args)
    except ValueError:
        args = raw_args.split()
    work = ctx.work if ctx.bound else None
    work_id = work["id"] if work is not None else None
    head = git.head(Path(work["worktree"])) if work is not None and work["worktree"] else None
    obj = target = None
    if type_ == "finish":
        if work is None or not head:
            return _refuse("/tollgate:finish vale solo in una sessione legata a un lavoro")
    elif type_ == "approve":
        if not args or args[0] not in acts.APPROVE_OBJECTS:
            return _refuse(f"oggetto di approve sconosciuto: {args[0] if args else '(vuoto)'}")
        obj = args[0]
        if obj in _TARGET_ARG:
            if len(args) < 2:
                return _refuse(f"approve {obj} richiede un argomento")
            target = args[1]
        elif obj == "pr":
            if not head:
                return _refuse("approve pr vale solo in una sessione legata a un lavoro")
            target = head
    elif type_ == "reopen":
        if not args or args[0] not in ("spec", "plan"):
            return _refuse("reopen vuole spec o plan e un motivo")
        obj = args[0]
    elif type_ == "resolve":
        if not args:
            return _refuse("resolve vuole l'identificativo del blocco")
        target = args[0]
    elif type_ in ("adopt", "abandon"):
        if not args or not args[0].lstrip("#").isdigit():
            return _refuse(f"{type_} vuole il numero dell'issue (#N)")
        target = args[0].lstrip("#")
    if type_ in ("adopt", "cleanup"):
        work_id = None
    typed = str(event.raw.get("prompt") or f"/{name} {raw_args}".strip())
    label = " ".join(x for x in (type_, obj, target) if x)
    return [record("expire_acts"),
            record("act", type=type_, object=obj, target=target, args=args, typed_text=typed,
                   work=work_id, head_sha=head if type_ == "finish" else None),
            inject(f"tollgate: atto registrato ({label})")]
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_checks/_common.py bin/tollgate_checks/session.py bin/tollgate_checks/acts.py tests/test_check_session.py tests/test_check_acts.py
git commit -m "tollgate P2: controlli di SessionStart e degli atti dell'utente"
```

---
### Task 15: Controlli su Edit e Write: fasi, scope, coordinatore, file protetti, livello, `plan-check`

**Files:**
- Modify: `bin/tollgate_checks/_common.py` (aggiunge `level_records`, `scope_exempt`)
- Create: `bin/tollgate_checks/writes.py`
- Create: `bin/tollgate_checks/post_edit.py`
- Test: `tests/test_check_writes.py`, `tests/test_check_post_edit.py`

**Interfaces:**
- Consumes: `adapter.edit_path`, `protected.is_protected`, `plan.check_plan`, `level.*`, `profiles.*`, `waivers.unresolved`, `testguard.Violation`, `git.*`, `_common.*`.
- Produces in `_common.py`: `level_records(ctx, work) -> list[Decision]` (ricalcolo del livello sul diff dalla base, decisione 18; L0 che cresce → `phase` con `l0_grew`); `scope_exempt(ctx, work, rel, scope) -> bool` (esenzioni di 7.4: `.md` sotto `docs/superpowers/` non protetti né bloccati, `.superpowers/`, `[scope] always`, lockfile con il manifest nello scope).
- Modulo `writes` (evento `pre_edit`, ordine 20): righe `PreToolUse Edit/Write` di 7.2, 6.6 e 12.4. Lo scope gira solo con il componente `scope_check`.
- Modulo `post_edit` (evento `post_edit`, ordine 20): ricalcolo del livello; `plan-check` sul piano nuovo in fase `plan` con il componente `plan_check`.

- [ ] **Step 1: Test di `pre_edit`**

`tests/test_check_writes.py`:

```python
import unittest

from tests.hookkit import DEFAULT_TOML, Lab
from tollgate_analysis import waivers
from tollgate_core import scope

IMPL = "a-impl"


def with_scope(lab, paths=("src/app.py",)):
    scope.register_plan(lab.conn, lab.ts.state, lab.work, plan_path="docs/superpowers/plans/p.md",
                        plan_sha="s", scope_paths=list(paths), plan_tasks=[(1, [])],
                        advance=False, now=lab.now)


def write_waiver(lab, *items):
    wf = waivers.WaiverFile(7, "tg/7-demo", [
        waivers.Waiver(f"w-7-{i}", t, f, None, [], "c", "w", "k") for i, (t, f) in
        enumerate(items, 1)])
    p = lab.wt / ".tollgate/waivers/7.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(waivers.dumps(wf))


class ExecutionL1Test(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def test_scope(self):
        self.assertEqual(self.lab.pre_edit(self.lab.wt / "src/app.py", agent_id=IMPL).exit, 0)
        r = self.lab.pre_edit(self.lab.wt / "src/altro.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("tollgate waiver add scope src/altro.py", r.stderr)
        write_waiver(self.lab, ("scope", "src/altro.py"))
        self.assertEqual(self.lab.pre_edit(self.lab.wt / "src/altro.py", agent_id=IMPL).exit, 0)

    def test_write_new_dir_out_of_scope(self):
        r = self.lab.pre_edit(self.lab.wt / "src/nuova/cartella/x.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)

    def test_coordinator_cannot_write_code(self):
        r = self.lab.pre_edit(self.lab.wt / "src/app.py")
        self.assertEqual(r.exit, 2)
        self.assertIn("tollgate:execute", r.stderr)
        self.assertEqual(self.lab.pre_edit(self.lab.wt / "docs/superpowers/note.md").exit, 0)

    def test_protected_files(self):
        for rel in ("tollgate.toml", "docs/superpowers/reviews/7/r.md",
                    ".tollgate/waivers/7.toml", ".github/workflows/tollgate-verdict.yml"):
            with self.subTest(rel=rel):
                self.assertEqual(self.lab.pre_edit(self.lab.wt / rel, agent_id=IMPL).exit, 2)
        self.assertEqual(self.lab.pre_edit(self.lab.ts.dir / "tollgate.db").exit, 2)

    def test_main_checkout_is_denied(self):
        r = self.lab.pre_edit(self.lab.main / "src/app.py", agent_id=IMPL)
        self.assertEqual(r.exit, 2)
        self.assertIn("checkout principale", r.stderr)

    def test_locked_plan(self):
        p = self.lab.wt / "docs/superpowers/plans/p.md"
        self.assertEqual(self.lab.pre_edit(p).exit, 2)

    def test_scope_component_off(self):
        lab = Lab(toml=DEFAULT_TOML + "[components]\nscope_check = false\n")
        try:
            with_scope(lab)
            self.assertEqual(lab.pre_edit(lab.wt / "src/altro.py", agent_id=IMPL).exit, 0)
        finally:
            lab.close()


class PhasesTest(unittest.TestCase):
    def check(self, level, phase, rel, expected, agent_id=None):
        lab = Lab(level=level, phase=phase)
        try:
            r = lab.pre_edit(lab.wt / rel, agent_id=agent_id)
            self.assertEqual(r.exit, expected, (level, phase, rel, r.stderr))
        finally:
            lab.close()

    def test_plan_phase(self):
        self.check("L1", "plan", "docs/superpowers/plans/p.md", 0)
        self.check("L1", "plan", "src/app.py", 2)
        self.check("L1", "plan", ".superpowers/sdd/x.txt", 0)

    def test_spec_audit_no_plans(self):
        self.check("L2", "spec_audit", "docs/superpowers/specs/s.md", 0)
        self.check("L2", "spec_audit", "docs/superpowers/plans/p.md", 2)

    def test_review_and_pr_open(self):
        self.check("L1", "review", "src/app.py", 2, agent_id=IMPL)
        self.check("L1", "pr_open", "src/app.py", 2, agent_id=IMPL)

    def test_l0_main_session_writes(self):
        self.check("L0", "execution", "src/app.py", 0)


class OrphanTest(unittest.TestCase):
    def test_tg_branch_without_work(self):
        lab = Lab(work=False)
        try:
            r = lab.pre_edit(lab.wt / "src/app.py")
            self.assertEqual(r.exit, 2)
            self.assertIn("/tollgate:adopt #7", r.stderr)
            self.assertEqual(lab.pre_edit(lab.wt / "docs/superpowers/n.md").exit, 0)
        finally:
            lab.close()

    def test_unbound_session_outside_worktree_only_protected(self):
        lab = Lab(bind=False)
        try:
            self.assertEqual(lab.pre_edit(lab.main / "src/app.py", cwd=lab.main,
                                          session_id="altra").exit, 0)
            self.assertEqual(lab.pre_edit(lab.main / "tollgate.toml", cwd=lab.main,
                                          session_id="altra").exit, 2)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Test di `post_edit`**

`tests/test_check_post_edit.py`:

```python
import json
import unittest

from tests.hookkit import Lab
from tollgate_core import phases, scope, tasks

SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope",
            "Punti di arresto", "Rischi"]


def plan_text(must_have="M1. Somma — test: tests.test_app::test_somma",
              files=("- Modify: `src/app.py`", "- Test: `tests/test_app.py`")):
    out = []
    for s in SECTIONS:
        out += [f"## {s}", must_have if s == "Must-have" else "x", ""]
    out += ["### Task 1: Somma", *files, "", "### Task 2: Doc", "- Create: `docs/uso.md`"]
    return "\n".join(out) + "\n"


class LevelTest(unittest.TestCase):
    def test_l0_grows_to_l1_and_plan(self):
        lab = Lab(level="L0", phase="execution")
        try:
            for i in range(3):
                (lab.wt / f"src/f{i}.py").write_text("x = 1\n")
            r = lab.post_edit(lab.wt / "src/f2.py")
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["phase"]), ("L1", "plan"))
            self.assertIn("L1", r.stdout)
        finally:
            lab.close()

    def test_sensitive_path_goes_l2(self):
        lab = Lab()
        try:
            (lab.wt / "src/auth").mkdir()
            (lab.wt / "src/auth/x.py").write_text("x = 1\n")
            lab.post_edit(lab.wt / "src/auth/x.py", agent_id="a1")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L2")
        finally:
            lab.close()


class PlanCheckHookTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(phase="plan")
        self.plan = self.lab.wt / "docs/superpowers/plans/2026-10-09-somma.md"
        self.plan.parent.mkdir(parents=True)

    def tearDown(self):
        self.lab.close()

    def test_complete_plan_registers_scope(self):
        self.plan.write_text(plan_text())
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        w = phases.get_work(self.lab.conn, self.lab.work)
        self.assertEqual((w["phase"], w["plan_path"]),
                         ("execution", "docs/superpowers/plans/2026-10-09-somma.md"))
        self.assertEqual(scope.paths(self.lab.conn, self.lab.work),
                         {"src/app.py", "tests/test_app.py", "docs/uso.md"})
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 2)["state"], "pending")

    def test_incomplete_plan_vetoed_and_not_registered(self):
        self.plan.write_text(plan_text().replace("## Rischi", "## Altro"))
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 2)
        self.assertIn("## Rischi", r.stderr)
        self.assertEqual(scope.paths(self.lab.conn, self.lab.work), set())
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "plan")

    def test_pattern_and_must_have_without_test(self):
        for text in (plan_text(files=("- Modify: `src/*.py`",)),
                     plan_text(must_have="M1. Somma senza test")):
            with self.subTest(text=text[-60:]):
                self.plan.write_text(text)
                self.assertEqual(self.lab.post_edit(self.plan).exit, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_writes tests.test_check_post_edit -v`
Expected: FAIL (le scritture passano tutte, livello e scope non cambiano).

- [ ] **Step 4: Aiuti in `_common.py`**

In fondo a `bin/tollgate_checks/_common.py`:

```python
import json
import posixpath

from tollgate_analysis import globs, level as lv, profiles as prof
from tollgate_hooks.model import inject, record


def scope_exempt(ctx, work, rel: str, scope: set[str]) -> bool:
    if rel.startswith(".superpowers/") or rel == f".tollgate/waivers/{work['issue']}.toml":
        return True
    if is_docs_md(rel) and not rel.startswith("docs/superpowers/reviews/") \
            and rel not in locked_docs(work):
        return True
    if globs.match_any(ctx.cfg("scope.always"), rel):
        return True
    manifest = ctx.cfg("scope.lockfiles").get(posixpath.basename(rel))
    if manifest and posixpath.join(posixpath.dirname(rel), manifest) in scope:
        return True
    return False


def level_records(ctx, work) -> list:
    wt = Path(work["worktree"])
    base = work["work_base_sha"]
    if not base or not wt.is_dir():
        return []
    changes = git.changes(wt, base)
    cfg = ctx.cfg("levels")
    paths = [c.path for c in changes] + [c.old_path for c in changes if c.old_path]
    computed = lv.diff_level(changes, diff_bytes=git.diff_size(wt, base),
                             sensitive_paths=cfg["sensitive_paths"],
                             l0_max_files=cfg["l0_max_files"], l0_max_lines=cfg["l0_max_lines"],
                             l0_max_bytes=cfg["l0_max_bytes"])
    profs = ctx.config.profiles
    computed = lv.max_level(computed, prof.min_level(
        prof.active_profiles(paths, profs, ctx.cfg("profiles.active")), profs))
    new = lv.next_level(current=work["level"], computed=computed, cap=work["level_cap"],
                        cap_paths=json.loads(work["level_cap_paths"] or "[]"),
                        sensitive_now=lv.sensitive_in(paths, cfg["sensitive_paths"]))
    if new == work["level"]:
        return []
    out = []
    if work["level"] == "L0" and work["phase"] == "execution":
        out.append(record("phase", work=work["id"], to="plan", cause="l0_grew"))
        if new == "L2":
            out.append(record("level", work=work["id"], level="L2"))
        out.append(inject(f"tollgate: il diff supera le soglie di L0: il lavoro sale a {new} e "
                          f"torna in fase plan. Serve un piano (writing-plans)."))
    else:
        out.append(record("level", work=work["id"], level=new))
        out.append(inject(f"tollgate: il lavoro sale a {new} (percorsi sensibili o soglie)."))
    return out
```

- [ ] **Step 5: `writes.py`**

```python
"""PreToolUse Edit/Write/NotebookEdit/MultiEdit (spec 7.2, 6.6, 12.4)."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis.protected import is_protected
from tollgate_analysis.testguard import Violation
from tollgate_analysis.waivers import unresolved
from tollgate_core import git
from tollgate_hooks.adapter import edit_path
from tollgate_hooks.model import deny

from ._common import (explain, governing_work, is_docs_md, locked_docs, orphan_tg,
                      scope_exempt)

CHECK = {"api": 1, "events": ["pre_edit"], "component": None, "order": 20}
_DOCS_ONLY = ("spec_audit", "plan", "approval", "blocked", "review", "pr_open")


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def decide(event, ctx):
    raw = edit_path(event)
    if not raw:
        return []
    p = Path(raw)
    if not p.is_absolute():
        p = event.cwd / p
    p = p.resolve()
    repo = git.toplevel(p)
    rel = ctx.rel(p, repo) if repo else None
    if is_protected(rel, p, abs_roots=ctx.protected_roots(repo)):
        return [deny(f"{p} è un file protetto: lo scrivono solo la CLI e gli hook di tollgate "
                     f"(7.4)", rule="protected")]
    work = governing_work(ctx, p)
    if work is None:
        n = orphan_tg(ctx, repo)
        if n is not None and not is_docs_md(rel):
            return [deny(f"ramo tg/{n}-* senza lavoro nel DB: scritture negate tranne i .md "
                         f"sotto docs/superpowers/. L'utente deve lanciare /tollgate:adopt #{n} "
                         f"(12.4)", rule="adopt")]
        return []
    wt = Path(work["worktree"]).resolve() if work["worktree"] else None
    rel_w = ctx.rel(p, wt) if wt else None
    if rel_w is None:
        if wt is not None and repo is not None and _inside(p, git.main_worktree(wt)) \
                and not _inside(p, wt):
            return [deny(f"scrittura nel checkout principale negata durante il lavoro "
                         f"#{work['issue']}: si lavora nel worktree {wt} (6.6)",
                         rule="main_checkout")]
        return []
    if rel_w in locked_docs(work):
        return [deny(f"{rel_w} è approvato e bloccato: per cambiarlo serve "
                     f"/tollgate:reopen spec|plan <motivo> (6.2)", rule="locked")]
    md_ok = is_docs_md(rel_w) or rel_w.startswith(".superpowers/")
    phase = work["phase"]
    if phase in _DOCS_ONLY:
        if phase in ("spec_audit", "approval") and rel_w.startswith("docs/superpowers/plans/"):
            return [deny(f"in fase {phase} non si scrivono piani: prima l'audit e "
                         f"/tollgate:approve spec (6.2)", rule="phase")]
        if md_ok:
            return []
        hint = (" Per correggere il codice dopo finish: /tollgate:start." if phase in
                ("review", "pr_open") else "")
        return [deny(f"in fase {phase} si scrivono solo i .md sotto docs/superpowers/."
                     + hint, rule="phase")]
    if md_ok or work["level"] == "L0":
        return []
    if event.agent_id is None:
        return [deny(f"in {work['level']} il codice lo scrivono gli implementatori: usa "
                     f"/tollgate:execute (6.3)", rule="coordinator")]
    if ctx.component("scope_check"):
        scope = ctx.scope(work)
        if rel_w not in scope and not scope_exempt(ctx, work, rel_w, scope):
            v = Violation("out_of_scope", rel_w, "file fuori dallo scope del piano", "scope")
            left = unresolved([v], ctx.waiver_file(work))
            if left:
                return [deny("file fuori scope:\n" + explain(left, work["issue"]), rule="scope")]
    return []
```

- [ ] **Step 6: `post_edit.py`**

```python
"""PostToolUse Edit/Write (spec 7.2): livello e plan-check (7.5)."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import plan as planmod, profiles as prof
from tollgate_core import git
from tollgate_hooks.adapter import edit_path
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work, level_records

CHECK = {"api": 1, "events": ["post_edit"], "component": None, "order": 20}


def _plan(ctx, work, wt: Path, rel: str):
    if not (rel.startswith("docs/superpowers/plans/") and rel.endswith(".md")):
        return []
    if work["phase"] != "plan" or not ctx.component("plan_check") or work["plan_sha"]:
        return []
    if work["plan_path"] not in (None, rel) or git.exists_at(wt, work["work_base_sha"], rel):
        return []
    try:
        text = (wt / rel).read_text(encoding="utf-8")
    except OSError:
        return []
    r = planmod.check_plan(text, required_sections=ctx.cfg("plan.required_sections"),
                           max_scope_files=ctx.cfg("plan.max_scope_files"),
                           must_have_tests=ctx.component("must_have_tests"),
                           level=work["level"], profiles=ctx.config.profiles,
                           active_always=ctx.cfg("profiles.active"))
    if not r.ok:
        return [deny("piano incompleto, non registrato:\n- " + "\n- ".join(r.problems),
                     rule="plan_check")]
    out = [inject("tollgate: " + w) for w in r.warnings]
    if work["level"] == "L1":
        plan_tasks = [(t.number, prof.task_skills(t.files, ctx.config.profiles)[:3])
                      for t in r.tasks]
        out += [record("plan", work=work["id"], plan_path=rel, plan_sha=git.blob_sha(wt, rel),
                       scope=r.scope, tasks=plan_tasks, advance=True),
                inject(f"tollgate: piano registrato, scope di {len(r.scope)} file; fase "
                       f"execution. Prossimo passo: /tollgate:execute.")]
    else:
        out += [record("plan_path", work=work["id"], plan_path=rel),
                inject("tollgate: piano valido. Prossimi passi in L2: plan-adversary, poi "
                       "/tollgate:approve plan.")]
    return out


def decide(event, ctx):
    raw = edit_path(event)
    if not raw:
        return []
    p = Path(raw) if Path(raw).is_absolute() else event.cwd / raw
    work = governing_work(ctx, p)
    if work is None or not work["worktree"]:
        return []
    wt = Path(work["worktree"]).resolve()
    rel = ctx.rel(p, wt)
    if rel is None:
        return []
    return level_records(ctx, work) + _plan(ctx, work, wt, rel)
```

- [ ] **Step 7: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 8: Commit**

```bash
git add bin/tollgate_checks/_common.py bin/tollgate_checks/writes.py bin/tollgate_checks/post_edit.py tests/test_check_writes.py tests/test_check_post_edit.py
git commit -m "tollgate P2: controlli su Edit e Write (fasi, scope, coordinatore, protetti, livello, plan-check)"
```

---
### Task 16: Regole su Bash (7.4) ed effetti esterni (8.5)

**Files:**
- Create: `bin/tollgate_checks/bash_rules.py`
- Create: `bin/tollgate_checks/effects.py`
- Test: `tests/test_check_bash.py`, `tests/test_check_effects.py`

**Interfaces:**
- Consumes: `bash.*`, `protected.is_protected`, `effects.*`, `acts.find_usable`, `git.*`, `_common.*`.
- Produces:
  - Modulo `bash_rules` (evento `pre_bash`, ordine 20): tutte le righe di 7.4 tranne `git commit` (Task 17) e gli effetti; comandi illeggibili cercati per testo (Review Focus 1).
  - Modulo `effects` (eventi `pre_bash` e `pre_mcp`, ordine 30): veto con l'identificativo della decisione 14, una esecuzione per atto `approve effect <id>`, avviso «già eseguito alle…» sullo stesso SHA (criterio 23). `bin/tollgate` del plugin non è mai un effetto.

- [ ] **Step 1: Test delle regole**

`tests/test_check_bash.py`:

```python
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.hookkit import Lab
from tests.helpers import ROOT, git, make_repo


class BoundSessionTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def code(self, command, **kw):
        return self.lab.bash(command, **kw).exit

    def test_push_and_pr_denied(self):
        self.assertEqual(self.code("git push origin tg/7-demo"), 2)
        self.assertEqual(self.code("gh pr create --fill"), 2)
        self.assertEqual(self.code("bash -c 'git push'"), 2)

    def test_branch_changes_in_worktree(self):
        for cmd in ("git switch -c altro", "git checkout -B altro", "git branch -m nuovo",
                    "git checkout main"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd), 2)
        self.assertEqual(self.code("git checkout -- src/app.py"), 0)
        self.assertEqual(self.code("git status"), 0)

    def test_main_checkout(self):
        self.assertEqual(self.code(f"cd '{self.lab.main}' && touch x.txt"), 2)
        self.assertEqual(self.code(f"cd '{self.lab.main}' && gh pr create"), 2)
        self.assertEqual(self.code(f"echo x > '{self.lab.main}/src/app.py'"), 2)
        self.assertEqual(self.code(f"git -C '{self.lab.main}' status"), 0)

    def test_coordinator_code_writes(self):
        self.assertEqual(self.code("echo x > src/app.py"), 2)
        self.assertEqual(self.code("sed -i 's/a/b/' src/app.py"), 2)
        self.assertEqual(self.code("echo x > src/app.py", agent_id="a1"), 0)
        self.assertEqual(self.code("echo x > docs/superpowers/n.md"), 0)

    def test_destructive_and_forbidden(self):
        for cmd in ("git push -f origin tg/7-demo", "git reset --hard HEAD~1",
                    "git commit --no-verify -m x", "rm -rf /tmp/qualcosa", "claude -p ciao",
                    "TOLLGATE_STATE=/tmp ls", f"'{ROOT}/bin/tollgate' hook PreToolUse",
                    "echo x > tollgate.toml", "echo x >> .tollgate/waivers/7.toml"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd, agent_id="a1"), 2)
        self.assertEqual(self.code("rm -rf build", agent_id="a1"), 0)

    def test_unparsable_dangerous_text(self):
        self.assertEqual(self.code("echo 'x; git push --force"), 2)
        self.assertEqual(self.code("echo 'ciao"), 0)

    def test_l0_coordinator_writes(self):
        lab = Lab(level="L0")
        try:
            self.assertEqual(lab.bash("echo x > src/app.py").exit, 0)
        finally:
            lab.close()


class RepoLevelTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(bind=False)

    def tearDown(self):
        self.lab.close()

    def code(self, command):
        return self.lab.bash(command, cwd=self.lab.main, session_id="altra").exit

    def test_push_to_default_branch(self):
        self.assertEqual(self.code("git push origin main"), 2)
        self.assertEqual(self.code("git push"), 2)

    def test_work_branch_and_worktree_protection(self):
        self.assertEqual(self.code("git merge tg/7-demo"), 2)
        self.assertEqual(self.code("git branch -D tg/7-demo"), 2)
        self.assertEqual(self.code(f"git worktree remove '{self.lab.wt}'"), 2)
        self.assertEqual(self.code("git worktree add ../doppio tg/7-demo"), 2)
        self.assertEqual(self.code("git log --oneline"), 0)

    def test_inactive_repo_push_passes(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-inattivo-"))
        try:
            repo = make_repo(tmp / "r")
            r = self.lab.bash("git push origin main", cwd=repo, session_id="altra")
            self.assertEqual(r.exit, 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class OrphanBashTest(unittest.TestCase):
    def test_writes_denied_reads_allowed(self):
        lab = Lab(work=False)
        try:
            r = lab.bash("git commit -am x")
            self.assertEqual(r.exit, 2)
            self.assertIn("/tollgate:adopt #7", r.stderr)
            self.assertEqual(lab.bash("git status").exit, 0)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Test degli effetti**

`tests/test_check_effects.py`:

```python
import re
import unittest

from tests.hookkit import DEFAULT_TOML, DEFAULT_FILES, SESSION, Lab, sample
from tests.helpers import ROOT

EID = re.compile(r"approve effect (e-[0-9a-f]{8})")


def approve(lab, eid):
    lab.hook(sample("UserPromptExpansion-none", session_id=SESSION, cwd=str(lab.wt),
                    command_name="tollgate:approve", command_args=f"effect {eid}",
                    prompt=f"/tollgate:approve effect {eid}"))


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(toml=DEFAULT_TOML + '[external_effects]\nallow = ["npm publish --dry-run"]\n'
                       'mcp_allow = ["mcp__lettura__*"]\n',
                       files=dict(DEFAULT_FILES, **{"scripts/ok.sh": "echo ok\n"}))

    def tearDown(self):
        self.lab.close()

    def test_veto_act_once_then_warning(self):
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        eid = EID.search(r.stderr).group(1)
        approve(self.lab, eid)
        self.assertEqual(self.lab.bash("npm publish").exit, 0)
        self.assertEqual(len(self.lab.events("effect_executed")), 1)
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        self.assertIn("già eseguito alle", r.stderr)
        self.assertEqual(EID.search(r.stderr).group(1), eid)

    def test_other_effects(self):
        for cmd in ("gh pr edit 3 --title x", "gh api graphql -f query='mutation { x }'",
                    "curl -X POST https://example.invalid", "bash scripts/nuovo.sh"):
            with self.subTest(cmd=cmd):
                if cmd.endswith("nuovo.sh"):
                    (self.lab.wt / "scripts/nuovo.sh").write_text("echo x\n")
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 2)

    def test_allowed(self):
        for cmd in ("npm publish --dry-run", "bash scripts/ok.sh", "gh pr view 3",
                    f"'{ROOT}/bin/tollgate' verify"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 0)

    def test_mcp(self):
        p = self.lab._base("PreToolUse-Bash", None, None, tool_name="mcp__srv__scrivi",
                           tool_input={"testo": "x"})
        self.assertEqual(self.lab.hook(p).exit, 2)
        p = self.lab._base("PreToolUse-Bash", None, None, tool_name="mcp__lettura__cerca",
                           tool_input={"q": "x"})
        self.assertEqual(self.lab.hook(p).exit, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_bash tests.test_check_effects -v`
Expected: FAIL (tutto passa con uscita 0).

- [ ] **Step 4: `bash_rules.py`**

```python
"""PreToolUse Bash (spec 7.4, ambito 6.6). Best effort: il resto lo prende PostToolUse Bash."""
from __future__ import annotations

import os
from pathlib import Path

from tollgate_analysis import bash
from tollgate_analysis.protected import is_protected
from tollgate_core import git
from tollgate_hooks.model import deny

from ._common import governing_work, is_docs_md, orphan_tg, repo_key_of

CHECK = {"api": 1, "events": ["pre_bash"], "component": None, "order": 20}


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def _abs(c: bash.Cmd, target: str) -> Path:
    return Path(os.path.normpath(os.path.join(c.cwd, os.path.expanduser(target))))


def _active_branches(ctx, repo) -> dict[str, object]:
    key = repo_key_of(repo)
    return {r["branch"]: r for r in ctx.db.execute(
        "SELECT * FROM work_items WHERE repo_key = ? AND phase <> 'closed' "
        "AND branch IS NOT NULL", (key,))}


def _repo_rules(ctx, c, edir: Path, repo: Path | None):
    argv_text = " ".join(c.argv) + " " + " ".join(c.env)
    if bash.is_claude(c):
        return "claude e i suoi alias sono negati: una sessione nuova sfuggirebbe ai guardrail"
    if "TOLLGATE_" in argv_text:
        return "le variabili TOLLGATE_ sono negate nei comandi (3.1)"
    if bash.is_tollgate_hook(c):
        return "tollgate hook lo lancia solo hooks/run"
    for t in bash.write_targets(c):
        p = _abs(c, t)
        r = git.toplevel(p)
        if is_protected(ctx.rel(p, r) if r else None, p.resolve(),
                        abs_roots=ctx.protected_roots(r)):
            return f"scrittura su un file protetto: {t}"
    d = bash.destructive(c)
    if d:
        return f"{d} è negato (7.4)"
    for t in bash.rm_rf_targets(c):
        roots = [x for x in (repo, ctx.work and ctx.work["worktree"] and
                             Path(ctx.work["worktree"]).resolve()) if x]
        if not any(_inside(Path(t).resolve(), r) for r in roots):
            return f"rm -rf fuori dal repo e dal worktree: {t}"
    if repo is None:
        return None
    default = git.default_branch(repo)
    if bash.is_push(c):
        if bash.push_is_force(c):
            return "push forzato negato: lo fanno solo open-pr e sync (6.5)"
        targets = bash.push_targets(c) or [git.branch(edir) or ""]
        if default and default in targets:
            return f"push verso {default} negato: l'hotfix passa da un ramo e da una PR (9.4)"
    works = _active_branches(ctx, repo)
    if git.branch(edir) == default and any(a in works for a in bash.merge_args(c)):
        return "merge di un ramo tg/* di un lavoro attivo verso il predefinito negato"
    if any(b in works for b in bash.branch_deletes(c)):
        return "cancellazione del ramo di un lavoro attivo negata"
    op = bash.worktree_op(c)
    if op:
        existing = git.worktrees(repo)
        if op[0] == "remove" and any(Path(op[1]).resolve() == Path(w["worktree"]).resolve()
                                     for w in works.values() if w["worktree"]):
            return "rimozione del worktree di un lavoro attivo negata"
        if op[0] == "add" and (any(Path(op[1]).resolve() == p for p, _ in existing)
                               or (op[2] and any(op[2] == b for _, b in existing))):
            return "git worktree add doppio negato"
    return None


def _work_rules(ctx, event, c, edir: Path, work):
    wt = Path(work["worktree"]).resolve() if work["worktree"] else None
    if bash.is_push(c):
        return "il push del ramo lo fa /tollgate:finish (open-pr), non Bash (6.6)"
    if bash.is_gh_pr_create(c):
        return "la PR la apre /tollgate:finish (open-pr), non gh pr create (6.6)"
    if wt is None:
        return None
    main = git.main_worktree(wt)
    in_wt = _inside(edir, wt)
    if in_wt:
        bc = bash.branch_change(c)
        if bc:
            return f"{bc} nel worktree negato: il ramo del lavoro non cambia (6.6)"
        branches = git.local_branches(wt)
        if any(a in branches or a == "-" for a in bash.checkout_args(c)):
            return "git checkout di un altro ramo nel worktree negato (6.6)"
    if _inside(edir, main) and not in_wt and bash.writes(c):
        return f"scritture nel checkout principale negate durante il lavoro #{work['issue']} (6.6)"
    for t in bash.write_targets(c):
        p = _abs(c, t).resolve()
        if _inside(p, main) and not _inside(p, wt):
            return f"scrittura nel checkout principale negata: {t}"
        if (event.agent_id is None and work["level"] in ("L1", "L2") and _inside(p, wt)
                and not is_docs_md(ctx.rel(p, wt)) and not ctx.rel(p, wt).startswith(
                    ".superpowers/")):
            return (f"in {work['level']} il codice lo scrivono gli implementatori, anche con "
                    f"redirect o sed -i: {t}")
    return None


def decide(event, ctx):
    command = str(event.tool_input.get("command") or "")
    try:
        cmds = bash.parse(command, str(event.cwd))
    except bash.BashParseError:
        label = bash.text_danger(command)
        return [deny(f"comando non leggibile che contiene «{label}»: riscrivilo in forma "
                     f"semplice", rule="bash")] if label else []
    for c in cmds:
        if not c.argv and not c.redirects:
            continue
        edir = Path(bash.effective_dir(c))
        repo = git.toplevel(edir) if edir.exists() else None
        reason = _repo_rules(ctx, c, edir, repo)
        if reason is None:
            work = governing_work(ctx, edir)
            if work is not None:
                reason = _work_rules(ctx, event, c, edir, work)
            elif bash.writes(c):
                n = orphan_tg(ctx, repo)
                if n is not None:
                    reason = (f"ramo tg/{n}-* senza lavoro nel DB: comandi che scrivono negati. "
                              f"L'utente deve lanciare /tollgate:adopt #{n} (12.4)")
        if reason:
            return [deny(reason, rule="bash")]
    return []
```

- [ ] **Step 5: `effects.py`**

```python
"""Effetti esterni (spec 8.5): veto con identificativo, una esecuzione per atto."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from tollgate_analysis import bash
from tollgate_core import acts, effects, git
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["pre_bash", "pre_mcp"], "component": None, "order": 30}


def _effect(ctx, event, command: str, reason: str, repo: Path | None, where: Path):
    work = governing_work(ctx, where)
    work_id = work["id"] if work is not None else None
    sha = git.head(repo) if repo else None
    key = effects.effect_key(command, work_id, sha)
    eid = effects.effect_id(key)
    act = acts.find_usable(ctx.db, type_="approve", object_="effect", target=eid, work=work_id,
                           session=event.session, now=ctx.now)
    row = effects.get(ctx.db, key)
    if act is not None:
        out = [] if row is not None else [record("effect_request", key=key, command=command,
                                                 work=work_id, sha=sha)]
        return out + [record("effect_execute", key=key, act_id=act["act_id"], work=work_id),
                      inject(f"tollgate: effetto {eid} permesso una volta dall'atto "
                             f"{act['act_id']}")]
    prev = effects.executed_at(row)
    msg = (f"effetto esterno ({reason}): {command[:200]}. Per eseguirlo una volta l'utente "
           f"digita /tollgate:approve effect {eid}")
    if prev:
        msg += f". Attenzione: già eseguito alle {prev} su questo SHA"
    return [deny(msg, rule="effects"),
            record("effect_request", key=key, command=command, work=work_id, sha=sha)]


def _script_reason(ctx, c, edir: Path) -> str | None:
    sp = bash.script_path(c)
    if not sp:
        return None
    p = Path(sp)
    repo = git.toplevel(p)
    if repo is None:
        return None
    work = governing_work(ctx, p)
    ref = work["work_base_sha"] if work is not None and work["work_base_sha"] \
        else git.default_ref(repo)
    rel = ctx.rel(p, repo)
    if ref and rel and not git.exists_at(repo, ref, rel):
        return "script nel repo non tracciato nella base"
    return None


def decide(event, ctx):
    if event.kind == "pre_mcp":
        name = event.tool_name or ""
        if any(fnmatch.fnmatchcase(name, pat) for pat in ctx.cfg("external_effects.mcp_allow")):
            return []
        command = f"{name} {json.dumps(event.tool_input, sort_keys=True, ensure_ascii=False)}"
        return _effect(ctx, event, command, "strumento MCP non in mcp_allow", ctx.repo,
                       event.cwd)
    try:
        cmds = bash.parse(str(event.tool_input.get("command") or ""), str(event.cwd))
    except bash.BashParseError:
        return []
    ee = ctx.cfg("external_effects")
    cfg = bash.EffectsCfg(ee["commands"], ee["project_scripts"], ee["allow"])
    for c in cmds:
        if bash.uses_tollgate_bin(c, str(ctx.plugin_bin)):
            continue
        edir = Path(bash.effective_dir(c))
        reason = bash.effect_reason(c, cfg) or _script_reason(ctx, c, edir)
        if reason:
            repo = git.toplevel(edir) if edir.exists() else None
            return _effect(ctx, event, bash.normalized(c), reason, repo, edir)
    return []
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_checks/bash_rules.py bin/tollgate_checks/effects.py tests/test_check_bash.py tests/test_check_effects.py
git commit -m "tollgate P2: regole su Bash ed effetti esterni con atto una tantum"
```

---

### Task 17: `git commit` (test-guard, scope, livello) e `PostToolUse Bash`

**Files:**
- Modify: `bin/tollgate_checks/_common.py` (aggiunge `commit_violations`)
- Create: `bin/tollgate_checks/commit.py`
- Create: `bin/tollgate_checks/post_bash.py`
- Test: `tests/test_check_commit.py`, `tests/test_check_post_bash.py`

**Interfaces:**
- Consumes: `testguard.check`, `testguard.Change`, `waivers.unresolved`, `git.*`, `_common.level_records`, `_common.scope_exempt`.
- Produces:
  - `_common.commit_violations(ctx, work, wt, base_ref, head_ref, changes) -> list[Violation]` (`head_ref=None`: working tree; violazioni non derogate, decisione 9).
  - Modulo `commit` (evento `pre_bash`, ordine 25): `git commit` in un lavoro attivo → test-guard (componente `test_guard`), scope (componente `scope_check`, solo dopo la registrazione dello scope e non in L0), livello; `deny` se mancano deroghe o se il lavoro è uscito da L0.
  - Modulo `post_bash` (evento `post_bash`, ordine 20): commit nuovi registrati come eventi `commit` (con `invalidate_finish`), aggiunti a `tasks.commits` del task dell'implementatore, controllati con test-guard e scope rispetto al genitore; violazioni → blocco `needs_you`; ramo del worktree cambiato → `needs_you`; livello ricalcolato.

- [ ] **Step 1: Test di `commit`**

`tests/test_check_commit.py`:

```python
import unittest

from tests.hookkit import DEFAULT_FILES, Lab
from tests.test_check_writes import with_scope, write_waiver

FILES = dict(DEFAULT_FILES, **{
    "src/__tests__/a.test.js": "describe('a', () => {\n  it('x', () => {\n"
                               "    expect(1).toBe(1)\n  })\n})\n"})
SCOPE = ("src/app.py", "tests/test_app.py", "src/__tests__/a.test.js")
COMMIT = "git add -A && git commit -m lavoro"


class CommitTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(files=FILES)
        with_scope(self.lab, SCOPE)
        self.t = self.lab.wt / "tests/test_app.py"

    def tearDown(self):
        self.lab.close()

    def commit(self):
        return self.lab.bash(COMMIT, agent_id="a1")

    def test_deleted_test(self):
        self.t.unlink()
        self.assertEqual(self.commit().exit, 2)

    def test_deleted_js_test_in_dunder_tests(self):
        (self.lab.wt / "src/__tests__/a.test.js").unlink()
        self.assertEqual(self.commit().exit, 2)

    def test_pytest_skip_added(self):
        self.t.write_text(self.t.read_text().replace(
            "    assert somma(0, 0) == 0", "    pytest.skip('no')\n    assert somma(0, 0) == 0"))
        self.assertEqual(self.commit().exit, 2)

    def test_mark_skip_added(self):
        self.t.write_text(self.t.read_text().replace("def test_zero", "@pytest.mark.skip\n"
                                                                      "def test_zero"))
        self.assertEqual(self.commit().exit, 2)

    def test_assertion_replaced_by_comment(self):
        self.t.write_text(self.t.read_text().replace("    assert somma(0, 0) == 0",
                                                     "    # assert somma(0, 0) == 0\n    pass"))
        r = self.commit()
        self.assertEqual(r.exit, 2)
        self.assertIn("asserzioni diminuite", r.stderr)

    def test_process_exit_is_fine(self):
        js = self.lab.wt / "src/__tests__/a.test.js"
        js.write_text(js.read_text().replace("expect(1).toBe(1)",
                                             "expect(1).toBe(1); process.exit(0)"))
        self.assertEqual(self.commit().exit, 0)

    def test_out_of_scope_then_waiver(self):
        (self.lab.wt / "src/extra.py").write_text("x = 1\n")
        r = self.commit()
        self.assertEqual(r.exit, 2)
        self.assertIn("src/extra.py", r.stderr)
        write_waiver(self.lab, ("scope", "src/extra.py"))
        self.assertEqual(self.commit().exit, 0)

    def test_pending_test_waiver_lets_commit_pass(self):
        self.t.unlink()
        write_waiver(self.lab, ("test", "tests/test_app.py"))
        self.assertEqual(self.commit().exit, 0)

    def test_test_guard_component_off(self):
        lab = Lab(files=FILES, toml="schema_version = 1\n[gate]\nmode = \"protected\"\n"
                                    "[components]\ntest_guard = false\n")
        try:
            with_scope(lab, SCOPE)
            (lab.wt / "tests/test_app.py").unlink()
            self.assertEqual(lab.bash(COMMIT, agent_id="a1").exit, 0)
        finally:
            lab.close()

    def test_l0_growing_blocks_commit(self):
        lab = Lab(level="L0")
        try:
            for i in range(3):
                (lab.wt / f"src/f{i}.py").write_text("x = 1\n")
            r = lab.bash(COMMIT)
            self.assertEqual(r.exit, 2)
            self.assertIn("plan", r.stderr)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Test di `post_bash`**

`tests/test_check_post_bash.py`:

```python
import unittest

from tests.hookkit import SESSION, Lab
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import acts, phases, subagents, tasks


class PostBashTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab, ("src/app.py", "tests/test_app.py"))

    def tearDown(self):
        self.lab.close()

    def test_new_commit_recorded_and_finish_invalidated(self):
        head0 = git(self.lab.wt, "rev-parse", "HEAD")
        acts.record_act(self.lab.conn, type_="finish", typed_text="/tollgate:finish",
                        session=SESSION, work=self.lab.work, head_sha=head0, now=self.lab.now,
                        ttl_minutes=10)
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        subagents.start(self.lab.conn, agent_id="a1", type_="tollgate:implementer",
                        session=SESSION, work=self.lab.work, task=1, base_sha=head0,
                        fingerprint="f", now=self.lab.now)
        (self.lab.wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
        git(self.lab.wt, "commit", "-qam", "ok")
        head1 = git(self.lab.wt, "rev-parse", "HEAD")
        r = self.lab.bash("git commit -qam ok", post=True, agent_id="a1")
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.lab.events("commit"), [{"sha": head1}])
        self.assertEqual(self.lab.conn.execute("SELECT state FROM acts WHERE type='finish'")
                         .fetchone()[0], "expired")
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["commits"],
                         f'["{head1}"]')
        self.lab.bash("git status", post=True, agent_id="a1")
        self.assertEqual(len(self.lab.events("commit")), 1)

    def test_merge_bringing_deleted_test_opens_needs_you(self):
        git(self.lab.main, "checkout", "-q", "-b", "altro")
        (self.lab.main / "tests/test_app.py").unlink()
        git(self.lab.main, "commit", "-qam", "via il test")
        git(self.lab.main, "checkout", "-q", "main")
        git(self.lab.wt, "merge", "-q", "--no-edit", "altro")
        r = self.lab.bash("git merge altro", post=True)
        self.assertEqual(r.exit, 2)
        w = phases.get_work(self.lab.conn, self.lab.work)
        self.assertEqual(w["phase"], "blocked")
        self.assertEqual(self.lab.conn.execute("SELECT type FROM blocks").fetchone()[0],
                         "needs_you")

    def test_branch_changed_opens_needs_you(self):
        git(self.lab.wt, "checkout", "-q", "-b", "fuga")
        self.lab.bash("git checkout -b fuga", post=True)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")


if __name__ == "__main__":
    unittest.main()
```

Nota: `tests/test_check_post_bash.py` registra il task 1 con `with_scope` (che crea il task 1 tramite `register_plan`).

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_commit tests.test_check_post_bash -v`
Expected: FAIL.

- [ ] **Step 4: `commit_violations` in `_common.py`**

```python
from tollgate_analysis import testguard
from tollgate_analysis.testguard import Violation
from tollgate_analysis.waivers import unresolved


def commit_violations(ctx, work, wt: Path, base_ref: str, head_ref: str | None,
                      changes) -> list:
    out = []
    paths = [c.path for c in changes]
    if ctx.component("test_guard"):
        tg = []
        for c in changes:
            base_text = None if c.status == "A" else git.text_at(wt, base_ref,
                                                                 c.old_path or c.path)
            if c.status == "D":
                head_text = None
            elif head_ref is None:
                head_text = git.worktree_text(wt, c.path)
            else:
                head_text = git.text_at(wt, head_ref, c.path)
            tg.append(testguard.Change(c.status, c.path, c.old_path, base_text, head_text,
                                       c.binary))
        out += testguard.check(tg, ctx.guard_config(work, paths)).violations
    if ctx.component("scope_check") and work["level"] != "L0" and work["plan_sha"]:
        scope = ctx.scope(work)
        for c in changes:
            if c.path not in scope and not scope_exempt(ctx, work, c.path, scope):
                out.append(Violation("out_of_scope", c.path, "file fuori dallo scope del piano",
                                     "scope"))
    return unresolved(out, ctx.waiver_file(work))
```

- [ ] **Step 5: `commit.py`**

```python
"""git commit in un lavoro attivo (spec 7.4): test-guard, scope e livello su working tree e indice."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import bash
from tollgate_core import git
from tollgate_hooks.model import deny

from ._common import commit_violations, explain, governing_work, level_records

CHECK = {"api": 1, "events": ["pre_bash"], "component": None, "order": 25}


def decide(event, ctx):
    try:
        cmds = bash.parse(str(event.tool_input.get("command") or ""), str(event.cwd))
    except bash.BashParseError:
        return []
    for c in cmds:
        if not bash.is_commit(c):
            continue
        edir = Path(bash.effective_dir(c)).resolve()
        work = governing_work(ctx, edir)
        if work is None or not work["worktree"]:
            continue
        wt = Path(work["worktree"]).resolve()
        if not (edir == wt or wt in edir.parents):
            continue
        head = git.head(wt)
        if head is None:
            continue
        out = level_records(ctx, work)
        if any(d.kind == "record" and d.op == "phase" for d in out):
            return out + [deny("il diff ha superato le soglie di L0: il lavoro torna in fase "
                               "plan e serve un piano prima del commit", rule="level")]
        left = commit_violations(ctx, work, wt, head, None, git.changes(wt, head))
        if left:
            return out + [deny("commit negato, violazioni senza deroga:\n"
                               + explain(left, work["issue"]), rule="commit")]
        return out
    return []
```

- [ ] **Step 6: `post_bash.py`**

```python
"""PostToolUse Bash (spec 7.2): commit nuovi, ramo cambiato; il controllo a valle di 7.4."""
from __future__ import annotations

import json
from pathlib import Path

from tollgate_core import git, subagents
from tollgate_core.git import EMPTY_TREE
from tollgate_hooks.model import deny, record

from ._common import commit_violations, explain, governing_work, level_records

CHECK = {"api": 1, "events": ["post_bash"], "component": None, "order": 20}


def decide(event, ctx):
    work = governing_work(ctx, event.cwd)
    if work is None or not work["worktree"] or not Path(work["worktree"]).is_dir():
        return []
    wt = Path(work["worktree"]).resolve()
    out = []
    br = git.branch(wt)
    if work["branch"] and br != work["branch"]:
        out.append(record("block", work=work["id"], type="needs_you",
                          reason=f"il ramo del worktree è {br or '(staccato)'}, atteso "
                                 f"{work['branch']}: rimettilo o decidi come procedere"))
    head, base = git.head(wt), work["work_base_sha"]
    if not head or not base:
        return out
    known = {json.loads(r[0]).get("sha") for r in ctx.db.execute(
        "SELECT data FROM events WHERE type = 'commit' AND work = ?", (work["id"],))}
    new = [s for s in git.rev_list(wt, base, head) if s not in known]
    if not new:
        return out
    task = None
    if event.agent_id:
        row = subagents.get(ctx.db, event.agent_id)
        task = row["task"] if row is not None else None
    problems = []
    for sha in new:
        out.append(record("commit", work=work["id"], sha=sha, head=head))
        if task is not None:
            out.append(record("task_commit", work=work["id"], number=task, sha=sha))
        parent = git.resolve_ref(wt, f"{sha}^") or EMPTY_TREE
        left = commit_violations(ctx, work, wt, parent, sha, git.commit_changes(wt, sha))
        if left:
            problems.append(f"commit {sha[:10]}:\n" + explain(left, work["issue"]))
    out = level_records(ctx, work) + out
    if problems:
        text = "\n".join(problems)
        out += [record("block", work=work["id"], type="needs_you",
                       reason=("commit con violazioni senza deroga: " + text)[:1000]),
                deny("commit registrati con violazioni senza deroga; aperto un blocco "
                     "needs_you:\n" + text, rule="post_bash")]
    return out
```

- [ ] **Step 7: Verificare che passino**

Run: `tests/run`
Expected: OK. Nota: in `test_merge_bringing_deleted_test_opens_needs_you` il commit di merge si confronta con il primo genitore, che ha ancora il test: la cancellazione deve risultare.

- [ ] **Step 8: Commit**

```bash
git add bin/tollgate_checks/_common.py bin/tollgate_checks/commit.py bin/tollgate_checks/post_bash.py tests/test_check_commit.py tests/test_check_post_bash.py
git commit -m "tollgate P2: controllo di git commit e PostToolUse Bash"
```

---
### Task 18: Subagenti: `PreToolUse Agent` e `SendMessage`, `SubagentStart`, `PostToolUse Agent`, `Skill`, `SubagentHandback`

**Files:**
- Create: `bin/tollgate_checks/agents.py`
- Create: `bin/tollgate_checks/send_message.py`
- Create: `bin/tollgate_checks/subagent_start.py`
- Create: `bin/tollgate_checks/post_agent.py`
- Create: `bin/tollgate_checks/skills.py`
- Create: `bin/tollgate_checks/handback.py`
- Test: `tests/test_check_agents.py`

**Interfaces:**
- Consumes: `subagents.*`, `tasks.assign` (nei test), `report.is_turn_cut`, `git.head`, `git.fingerprint`, `_common.governing_work`.
- Produces:
  - Modulo `agents` (`pre_agent`, ordine 20): guardia del contesto (componente `context_guard`, file della decisione 13), subagenti fermi oltre `stale_minutes` → `interrupted`, scrittore unico (componente `single_writer`), in `execution` L1/L2 solo il tipo, il `name` e il primo piano voluti da `task start`.
  - Modulo `send_message` (`pre_send_message`, ordine 20): risolve `to` per nome o `agent_id`; riprese ammesse con `pending = 'resume'` o per rispondere a `NEEDS_CONTEXT`.
  - Modulo `subagent_start` (`subagent_start`, ordine 20): riga in `subagents` con base e impronta (non sovrascritte alla ripresa), associazione al task in sospeso, promemoria dell'implementatore (≤ 2.000 caratteri dal runner).
  - Modulo `post_agent` (`post_agent`, ordine 20): nome → `agent_id`; report da `handbackReport`; taglio di `maxTurns` (componente `task_budget`) → riga chiusa `cut`, task `blocked`, blocco `needs_you`.
  - Modulo `skills` (`post_skill`, ordine 20): skill usata dal task dell'implementatore.
  - Modulo `handback` (`subagent_handback`, ordine 10): report del subagente in auto mode.
  - Promemoria iniettato all'implementatore: contiene il percorso assoluto di `bin/tollgate` e la riga «prima di DONE: commit, poi `<bin> verify`».

- [ ] **Step 1: Test**

`tests/test_check_agents.py`:

```python
import json
import unittest
from datetime import timedelta

from tests.hookkit import SESSION, T0, Lab, sample
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import phases, subagents, tasks

IMPL = "tollgate:implementer"


def agent_payload(lab, atype, name=None, bg=False):
    ti = {"description": "d", "prompt": "p", "subagent_type": atype, "run_in_background": bg}
    if name:
        ti["name"] = name
    return sample("PreToolUse-Agent", session_id=SESSION, cwd=str(lab.wt), tool_input=ti)


def send(lab, to, agent_id=None):
    extra = {"agent_id": agent_id, "agent_type": IMPL} if agent_id else {}
    return lab.hook(sample("PreToolUse-SendMessage", session_id=SESSION, cwd=str(lab.wt),
                           tool_input={"to": to, "message": "continua", "summary": "s"},
                           **extra))


def start(lab, agent_id, atype=IMPL):
    return lab.hook(sample("SubagentStart-none", session_id=SESSION, cwd=str(lab.wt),
                           agent_id=agent_id, agent_type=atype))


class PreAgentTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def assign(self, pending="launch"):
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending=pending, now=self.lab.now)

    def test_general_purpose_denied_with_execute_hint(self):
        r = self.lab.hook(agent_payload(self.lab, "general-purpose"))
        self.assertEqual(r.exit, 2)
        self.assertIn("/tollgate:execute", r.stderr)

    def test_implementer_rules(self):
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 2)
        self.assign()
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL)).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1", bg=True)).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 0)

    def test_readonly_always_allowed(self):
        for t in ("tollgate:task-reviewer", "Explore", "probe:reviewer-frontend"):
            self.assertEqual(self.lab.hook(agent_payload(self.lab, t)).exit, 0)

    def test_single_writer_and_stale(self):
        subagents.start(self.lab.conn, agent_id="a-vecchio", type_=IMPL, session=SESSION,
                        work=self.lab.work, task=None, base_sha=self.lab.base, fingerprint="f",
                        now=self.lab.now)
        self.assign()
        r = self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1"))
        self.assertEqual(r.exit, 2)
        self.assertIn("/tollgate:resolve writer", r.stderr)
        r = self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1"),
                          now=self.lab.now + timedelta(minutes=31))
        self.assertEqual(r.exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a-vecchio")["state"], "interrupted")

    def test_context_guard(self):
        d = self.lab.ts.dir / "ctx"
        d.mkdir()
        for pct, code in ((60, 2), (50, 0), (None, 0)):
            (d / f"{SESSION}.json").write_text(json.dumps({"used_pct": pct}))
            with self.subTest(pct=pct):
                r = self.lab.hook(agent_payload(self.lab, "Explore"))
                self.assertEqual(r.exit, code)
                if pct == 50:
                    self.assertIn("contesto", r.stdout)


class StartAndResumeTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)

    def tearDown(self):
        self.lab.close()

    def test_start_associates_task_and_keeps_base_on_resume(self):
        r = start(self.lab, "a1")
        self.assertIn("verify", r.stdout)
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["task"], row["agent_base_sha"]), (1, self.lab.base))
        self.assertIsNone(tasks.get_task(self.lab.conn, self.lab.work, 1)["pending"])
        (self.lab.wt / "src/app.py").write_text("x = 2\n")
        git(self.lab.wt, "commit", "-qam", "lavoro")
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        start(self.lab, "a1")
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["agent_base_sha"], row["resumes"]), (self.lab.base, 1))

    def test_name_registry_and_send_message(self):
        start(self.lab, "a1")
        post = sample("PostToolUse-Agent-foreground-manual", session_id=SESSION,
                      cwd=str(self.lab.wt))
        post["tool_input"]["name"] = "tg-7-t1"
        post["tool_response"]["agentId"] = "a1"
        self.lab.hook(post)
        self.assertEqual(subagents.by_name(self.lab.conn, "tg-7-t1", work=self.lab.work)["id"],
                         "a1")
        subagents.finish(self.lab.conn, "a1", state="done", declared_status="DONE",
                         now=self.lab.now)
        self.assertEqual(send(self.lab, "mai-visto").exit, 2)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 2)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 0)
        self.assertEqual(send(self.lab, "a1").exit, 0)

    def test_needs_context_resume_allowed(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        start(self.lab, "a1")
        subagents.set_name(self.lab.conn, "a1", "tg-7-t1", session=SESSION, work=self.lab.work,
                           now=self.lab.now)
        subagents.finish(self.lab.conn, "a1", state="done", declared_status="NEEDS_CONTEXT",
                         now=self.lab.now)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 0)

    def test_turn_cut_closes_row_and_blocks_task(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        cut = sample("PostToolUse-Agent-maxturns-cut", session_id=SESSION, cwd=str(self.lab.wt))
        aid = cut["tool_response"]["agentId"]
        start(self.lab, aid)
        self.lab.hook(cut)
        self.assertEqual(subagents.get(self.lab.conn, aid)["state"], "cut")
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["state"], "blocked")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")
        self.assertEqual(subagents.running(self.lab.conn, work=self.lab.work), [])

    def test_skill_and_handback(self):
        start(self.lab, "a1")
        self.lab.hook(sample("PostToolUse-Skill", session_id=SESSION, cwd=str(self.lab.wt),
                             agent_id="a1", agent_type=IMPL, tool_name="Skill",
                             tool_input={"skill": "superpowers:test-driven-development"},
                             tool_response={"success": True}))
        self.assertIn("test-driven-development",
                      tasks.get_task(self.lab.conn, self.lab.work, 1)["skills_used"])
        hb = sample("PostToolUse-SubagentHandback", session_id=SESSION, cwd=str(self.lab.wt),
                    agent_id="a1", agent_type=IMPL, tool_input={"message": "{\"status\":\"DONE\"}"})
        self.lab.hook(hb)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["report"], '{"status":"DONE"}')


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_check_agents -v`
Expected: FAIL.

- [ ] **Step 3: `agents.py`**

```python
"""PreToolUse Agent (spec 7.2, 6.3): contesto, subagenti fermi, scrittore unico, implementatore."""
from __future__ import annotations

import json

from tollgate_core import subagents
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["pre_agent"], "component": None, "order": 20}


def context_pct(ctx, session: str):
    try:
        data = json.loads((ctx.state.root / "ctx" / f"{session}.json").read_text())
        v = data.get("used_pct")
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
    except (OSError, ValueError, AttributeError):
        return None


def live_writers(ctx, work_id, exclude=()):
    rows = subagents.running(ctx.db, work=work_id)
    stale = [r for r in rows if subagents.is_stale(r, now=ctx.now,
                                                    stale_minutes=ctx.stale_minutes)]
    live = [r for r in rows if r not in stale and r["id"] not in exclude
            and not ctx.readonly(r["type"])]
    return live, [record("subagent_interrupt", agent_id=r["id"]) for r in stale]


def decide(event, ctx):
    work = governing_work(ctx, event.cwd)
    if work is None:
        return []
    out = []
    if ctx.component("context_guard"):
        pct = context_pct(ctx, event.session)
        if pct is not None and pct >= ctx.cfg("context.stop_pct"):
            return [deny(f"contesto al {pct:.0f}%: nessun nuovo subagente. Scrivi il checkpoint "
                         f"(tollgate status --checkpoint) e fai /clear (6.3)", rule="context")]
        if pct is not None and pct >= ctx.cfg("context.warn_pct"):
            out.append(inject(f"tollgate: contesto al {pct:.0f}%; a "
                              f"{ctx.cfg('context.stop_pct')}% servirà checkpoint e /clear."))
    ti = event.tool_input
    atype = str(ti.get("subagent_type") or "general-purpose")
    if ctx.readonly(atype):
        return out
    live, interrupts = live_writers(ctx, work["id"])
    out += interrupts
    if ctx.component("single_writer") and live:
        w = live[0]
        return out + [deny(f"scrittore unico: {w['type']} ({w['id']}) è ancora in corso nel "
                           f"lavoro #{work['issue']}. Se la sua sessione è caduta: "
                           f"/tollgate:resolve writer", rule="single_writer")]
    if work["phase"] != "execution" or work["level"] not in ("L1", "L2"):
        return out
    pending = ctx.db.execute("SELECT * FROM tasks WHERE work = ? AND pending = 'launch' "
                             "ORDER BY number", (work["id"],)).fetchall()
    cand = [t for t in pending if t["agent_type"] == atype]
    if not cand:
        hint = (f"; il task {pending[0]['number']} aspetta {pending[0]['agent_type']}"
                if pending else "")
        return out + [deny(f"in execution l'unico subagente che scrive è l'implementatore scelto "
                           f"da tollgate task start: {atype} non ha un task start in sospeso"
                           f"{hint}. Usa /tollgate:execute (6.3)", rule="writer")]
    t = cand[0]
    if ti.get("name") != t["implementer"]:
        return out + [deny(f"l'implementatore va lanciato con name «{t['implementer']}» "
                           f"(scritto nel brief): serve per riprenderlo con SendMessage",
                           rule="writer")]
    if ti.get("run_in_background"):
        return out + [deny("l'implementatore si lancia in primo piano: i task sono in sequenza",
                           rule="writer")]
    return out
```

- [ ] **Step 4: `send_message.py`**

```python
"""PreToolUse SendMessage (spec 7.2, 6.3): le riprese seguono le regole dello scrittore."""
from __future__ import annotations

from tollgate_core import subagents
from tollgate_hooks.model import deny

from ._common import governing_work
from .agents import live_writers

CHECK = {"api": 1, "events": ["pre_send_message"], "component": None, "order": 20}


def decide(event, ctx):
    work = governing_work(ctx, event.cwd)
    if work is None:
        return []
    to = str(event.tool_input.get("to") or event.tool_input.get("recipient") or "")
    target = subagents.by_name(ctx.db, to, work=work["id"]) or (
        subagents.get(ctx.db, to) if to else None)
    from_main = event.agent_id is None
    in_exec = work["phase"] == "execution" and work["level"] in ("L1", "L2")
    if target is None:
        if from_main and in_exec:
            return [deny(f"destinatario «{to}» mai registrato: in execution vale come un "
                         f"implementatore senza task start (6.3)", rule="writer")]
        return []
    if ctx.readonly(target["type"]) or not target["type"]:
        return []
    if not from_main:
        return [deny("un subagente non riprende un subagente che scrive", rule="writer")]
    if not in_exec:
        return []
    task = None
    if target["task"] is not None:
        task = ctx.db.execute("SELECT * FROM tasks WHERE work = ? AND number = ?",
                              (work["id"], target["task"])).fetchone()
    ok = task is not None and (
        (task["pending"] == "resume" and task["agent_type"] == target["type"])
        or (task["state"] == "running" and target["declared_status"] == "NEEDS_CONTEXT"))
    if not ok:
        return [deny(f"ripresa di {to} negata: serve tollgate task start {target['task']} --fix, "
                     f"oppure una risposta a NEEDS_CONTEXT (6.3)", rule="writer")]
    if ctx.component("single_writer"):
        live, _ = live_writers(ctx, work["id"], exclude=(target["id"],))
        if live:
            return [deny(f"scrittore unico: {live[0]['id']} è ancora in corso",
                         rule="single_writer")]
    return []
```

- [ ] **Step 5: `subagent_start.py`, `post_agent.py`, `skills.py`, `handback.py`**

`subagent_start.py`:

```python
"""SubagentStart (spec 7.2): base, impronta e tipo; associazione al task; promemoria."""
from __future__ import annotations

from pathlib import Path

from tollgate_core import git, subagents
from tollgate_hooks.model import inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["subagent_start"], "component": None, "order": 20}


def decide(event, ctx):
    if not event.agent_type or not event.agent_id:
        return []
    work = governing_work(ctx, event.cwd)
    row = subagents.get(ctx.db, event.agent_id)
    resume = row is not None and row["started"] is not None
    wt = Path(work["worktree"]) if work is not None and work["worktree"] else None
    base = git.head(wt) if wt is not None and wt.is_dir() else None
    fp = git.fingerprint(wt, ctx.cfg("review.output_dirs")) if base else None
    implementer = not ctx.readonly(event.agent_type)
    out = [record("subagent_start", agent_id=event.agent_id, type=event.agent_type,
                  work=work["id"] if work is not None else None,
                  task=row["task"] if row is not None else None, base_sha=base, fingerprint=fp,
                  take_pending=implementer and work is not None, resume=resume)]
    if implementer and work is not None:
        out.append(inject(
            f"tollgate: sei un subagente che scrive nel lavoro #{work['issue']}. Lavora solo sui "
            f"file dello scope del task, con TDD. Prima di DONE: committa, poi lancia "
            f"'{ctx.plugin_bin}' verify e controlla che la ricevuta sia green. Chiudi con il "
            f"report JSON di 18.5 (v, task, status, done, tests, files, must_have, concerns, "
            f"left, size_reason). Se un test contraddice la specifica: "
            f"'{ctx.plugin_bin}' block open test_spec_conflict --reason \"…\" e BLOCKED."))
    return out
```

`post_agent.py`:

```python
"""PostToolUse Agent (spec 7.2): nome → agent_id, report in primo piano, taglio di maxTurns."""
from __future__ import annotations

from tollgate_analysis import report
from tollgate_core import subagents
from tollgate_hooks.model import inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["post_agent"], "component": None, "order": 20}


def decide(event, ctx):
    tr = event.tool_response or {}
    aid = tr.get("agentId")
    if not aid:
        return []
    work = governing_work(ctx, event.cwd)
    wid = work["id"] if work is not None else None
    out = []
    if event.tool_input.get("name"):
        out.append(record("subagent_name", agent_id=aid, name=str(event.tool_input["name"]),
                          work=wid))
    hb = tr.get("handbackReport")
    if isinstance(hb, dict) and isinstance(hb.get("text"), str):
        out.append(record("subagent_report", agent_id=aid, text=hb["text"]))
    if ctx.component("task_budget") and report.is_turn_cut(tr):
        row = subagents.get(ctx.db, aid)
        if row is not None and row["state"] == "running":
            out.append(record("subagent_finish", agent_id=aid, state="cut"))
        task = row["task"] if row is not None else None
        if wid is not None and task is not None:
            t = ctx.db.execute("SELECT state FROM tasks WHERE work = ? AND number = ?",
                               (wid, task)).fetchone()
            if t is not None and t["state"] == "running":
                out += [record("task", work=wid, number=task, event="budget_exceeded"),
                        record("block", work=wid, type="needs_you",
                               reason=f"budget superato: maxTurns esaurito sul task {task}. "
                                      f"Proposta: dividere il task")]
        out.append(inject("tollgate: il subagente ha esaurito maxTurns. Il task è bloccato con "
                          "needs_you: non riprenderlo con SendMessage."))
    return out
```

`skills.py`:

```python
"""PostToolUse Skill (spec 7.2, 6.3): la skill usata dall'implementatore va al suo task."""
from __future__ import annotations

from tollgate_core import subagents
from tollgate_hooks.model import record

CHECK = {"api": 1, "events": ["post_skill"], "component": None, "order": 20}


def decide(event, ctx):
    if not event.agent_id:
        return []
    row = subagents.get(ctx.db, event.agent_id)
    skill = event.tool_input.get("skill") or event.tool_input.get("command")
    if row is None or row["task"] is None or row["work"] is None or not skill:
        return []
    return [record("skill_used", work=row["work"], number=row["task"], skill=str(skill))]
```

`handback.py`:

```python
"""PostToolUse SubagentHandback (spec 7.2): in auto mode è l'unica fonte del report."""
from __future__ import annotations

from tollgate_hooks.model import record

CHECK = {"api": 1, "events": ["subagent_handback"], "component": None, "order": 10}


def decide(event, ctx):
    msg = event.tool_input.get("message")
    if not event.agent_id or not isinstance(msg, str):
        return []
    return [record("subagent_report", agent_id=event.agent_id, text=msg)]
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK. Se il campione `PostToolUse-Agent-maxturns-cut` non porta il taglio nella forma attesa, vale il Task 1 e il Task 8: il test usa l'input reale.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_checks/agents.py bin/tollgate_checks/send_message.py bin/tollgate_checks/subagent_start.py bin/tollgate_checks/post_agent.py bin/tollgate_checks/skills.py bin/tollgate_checks/handback.py tests/test_check_agents.py
git commit -m "tollgate P2: controlli dei subagenti (scrittore unico, riprese, nomi, maxTurns, skill)"
```

---

### Task 19: `SubagentStop`: implementatori (8.1, 6.3) e sola lettura (7.3)

**Files:**
- Create: `bin/tollgate_checks/subagent_stop.py`
- Test: `tests/test_check_subagent_stop.py`

**Interfaces:**
- Consumes: `report.parse_report`, `report.transcript_tokens`, `receipts.latest`, `receipts.any_since`, `verify.counts_green`, `git.*`, `subagents.get`.
- Produces: modulo `subagent_stop` (evento `subagent_stop`, ordine 20). Ordine dei controlli per un implementatore: tetto di token (componente `task_budget`, prima di tutto, 6.3) → report a campi fissi (`report_fields`) → dimensione del task (`task_size`) → ricevuta (`subagent_receipt_gate`) → skill dei profili → transizione del task. Ogni veto conta in `subagents.vetoes`; dopo 2 veti si apre `needs_you` e il subagente chiude (8.1). Sola lettura con impronta cambiata (`readonly_check`) → riga `tampered` e `needs_you`. `agent_type` vuoto o `agent_id` mai visto → ignorato.

- [ ] **Step 1: Test**

`tests/test_check_subagent_stop.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import git as tg_git, phases, receipts, subagents, tasks

IMPL = "tollgate:implementer"


def report(status="DONE", **extra):
    data = {"v": 1, "task": 1, "status": status, "done": "fatto", "tests": "verify green",
            "files": ["src/app.py"], "must_have": [], "concerns": "", "left": "",
            "size_reason": None}
    data.update(extra)
    return "Fine.\n```json\n" + json.dumps(data) + "\n```"


class Base(unittest.TestCase):
    toml = DEFAULT_TOML

    def setUp(self):
        self.lab = Lab(toml=self.toml)
        with_scope(self.lab, ("src/app.py", "tests/test_app.py", "src/big.py"))
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        self.start("a1", IMPL, task=1)

    def tearDown(self):
        self.lab.close()

    def start(self, aid, atype, task=None):
        subagents.start(self.lab.conn, agent_id=aid, type_=atype, session=SESSION,
                        work=self.lab.work, task=task, base_sha=tg_git.head(self.lab.wt),
                        fingerprint=tg_git.fingerprint(self.lab.wt, ["reports/", "coverage/"]),
                        now=self.lab.now)

    def stop(self, aid="a1", atype=IMPL, text=None, transcript=None):
        p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.lab.wt),
                   agent_id=aid, agent_type=atype, last_assistant_message=text,
                   agent_transcript_path=transcript or "/non/esiste.jsonl")
        if text is None:
            p.pop("last_assistant_message")
        return self.lab.hook(p)

    def commit(self, content="def somma(a, b):\n    return b + a\n", path="src/app.py"):
        (self.lab.wt / path).write_text(content)
        git(self.lab.wt, "add", "-A")
        git(self.lab.wt, "commit", "-qm", "lavoro")
        return git(self.lab.wt, "rev-parse", "HEAD")

    def green(self, sha, state="green"):
        receipts.add(self.lab.conn, work=self.lab.work, sha=sha, command="verify",
                     resolved_command="true", exit_code=0, tests_run=0 if state == "empty" else 2,
                     tests_skipped=0, duration=0.1, log=None, produced_by="verify", state=state,
                     now=self.lab.now)

    def task_state(self):
        return tasks.get_task(self.lab.conn, self.lab.work, 1)["state"]


class ReceiptGateTest(Base):
    def test_done_without_receipt_two_vetoes_then_needs_you(self):
        self.commit()
        self.assertEqual(self.stop(text=report()).exit, 2)
        self.assertEqual(self.stop(text=report()).exit, 2)
        r = self.stop(text=report())
        self.assertEqual(r.exit, 0)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")
        self.assertEqual(self.task_state(), "blocked")

    def test_done_with_green_receipt(self):
        self.green(self.commit())
        self.assertEqual(self.stop(text=report()).exit, 0)
        self.assertEqual(self.task_state(), "review")
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "done")

    def test_done_with_changes_but_no_commit(self):
        (self.lab.wt / "src/app.py").write_text("x = 3\n")
        r = self.stop(text=report())
        self.assertEqual(r.exit, 2)
        self.assertIn("committa", r.stderr)

    def test_done_without_changes_passes(self):
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_blocked_with_red_receipt_closes(self):
        self.green(self.commit(), state="red")
        self.assertEqual(self.stop(text=report("BLOCKED", concerns="manca un dato")).exit, 0)
        self.assertEqual(self.task_state(), "blocked")

    def test_needs_context_without_receipt_or_block(self):
        self.assertEqual(self.stop(text=report("NEEDS_CONTEXT")).exit, 2)

    def test_invalid_report(self):
        r = self.stop(text='{"status": "DONE"}')
        self.assertEqual(r.exit, 2)
        self.assertIn("non valido", r.stderr)

    def test_report_from_handback(self):
        self.green(self.commit())
        subagents.set_report(self.lab.conn, "a1", report())
        self.assertEqual(self.stop(text=None).exit, 0)

    def test_internal_and_unknown_ignored(self):
        self.assertEqual(self.stop(aid="mai-visto").exit, 0)
        self.assertEqual(self.stop(atype="").exit, 0)


class BudgetAndSizeTest(Base):
    def test_tokens_over_cap_block_even_with_green(self):
        self.green(self.commit())
        tr = Path(tempfile.mkdtemp()) / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {
            "id": "m", "usage": {"input_tokens": 500000, "output_tokens": 1}}}) + "\n")
        self.assertEqual(self.stop(text=report(), transcript=str(tr)).exit, 0)
        self.assertEqual(self.task_state(), "blocked")
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "budget")

    def test_size_reason_required_over_max(self):
        sha = self.commit("".join(f"x{i} = {i}\n" for i in range(600)), path="src/big.py")
        self.green(sha)
        self.assertEqual(self.stop(text=report()).exit, 2)
        self.assertEqual(self.stop(text=report(size_reason="generato da uno schema")).exit, 0)


class AllowNoTestsTest(Base):
    toml = DEFAULT_TOML + "[project]\nallow_no_tests = true\n"

    def test_empty_receipt_counts(self):
        self.green(self.commit(), state="empty")
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReceiptGateOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nsubagent_receipt_gate = false\n"

    def test_done_without_receipt_passes(self):
        self.commit()
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReadonlyTest(Base):
    def test_tampering_reviewer(self):
        self.start("r1", "tollgate:task-reviewer")
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(aid="r1", atype="tollgate:task-reviewer", text="ok").exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "r1")["state"], "tampered")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")

    def test_clean_reviewer(self):
        self.start("r2", "tollgate:task-reviewer")
        self.stop(aid="r2", atype="tollgate:task-reviewer", text="ok")
        self.assertEqual(subagents.get(self.lab.conn, "r2")["state"], "done")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_check_subagent_stop -v`
Expected: FAIL.

- [ ] **Step 3: `subagent_stop.py`**

```python
"""SubagentStop (spec 7.2, 8.1, 6.3, 7.3): implementatori e sola lettura. Revisori e avversari: P3."""
from __future__ import annotations

import json
import posixpath
from pathlib import Path

from tollgate_analysis import globs, report
from tollgate_core import git, receipts, subagents
from tollgate_core.verify import counts_green
from tollgate_hooks.model import deny, record

CHECK = {"api": 1, "events": ["subagent_stop"], "component": None, "order": 20}
MAX_VETOES = 2
_GENERATED = ["**/*.min.js", "**/*.generated.*", "**/__snapshots__/**", "**/dist/**"]


def _readonly(ctx, row, work):
    out = []
    if ctx.component("readonly_check") and work is not None and work["worktree"] \
            and row["fingerprint"]:
        wt = Path(work["worktree"])
        if git.fingerprint(wt, ctx.cfg("review.output_dirs")) != row["fingerprint"]:
            return [record("subagent_finish", agent_id=row["id"], state="tampered"),
                    record("block", work=work["id"], type="needs_you",
                           reason=f"il subagente di sola lettura {row['type']} ha cambiato "
                                  f"file: il suo verdetto non vale (7.3)")]
    return out + [record("subagent_finish", agent_id=row["id"], state="done")]


def _task_lines(ctx, wt: Path, base: str, head: str) -> int:
    lockfiles = set(ctx.cfg("scope.lockfiles"))
    return sum(c.added + c.removed for c in git.changes(wt, base, head=head)
               if posixpath.basename(c.path) not in lockfiles
               and not globs.match_any(_GENERATED, c.path))


def _skill_missing(task) -> list[str]:
    used = json.loads(task["skills_used"])
    tail = {u.split(":")[-1] for u in used}
    return [s for s in json.loads(task["skills_required"])
            if s not in used and s.split(":")[-1] not in tail]


def decide(event, ctx):
    if not event.agent_type or not event.agent_id:
        return []
    row = subagents.get(ctx.db, event.agent_id)
    if row is None or row["started"] is None:
        return []      # subagente interno di Claude Code, mai visto a SubagentStart (P0)
    work = ctx.db.execute("SELECT * FROM work_items WHERE id = ?",
                          (row["work"],)).fetchone() if row["work"] is not None else None
    if ctx.readonly(event.agent_type):
        return _readonly(ctx, row, work)
    if work is None or not work["worktree"]:
        return [record("subagent_finish", agent_id=row["id"], state="done")]
    wid, aid = work["id"], row["id"]
    task = None
    if row["task"] is not None:
        task = ctx.db.execute("SELECT * FROM tasks WHERE work = ? AND number = ?",
                              (wid, row["task"])).fetchone()
    running = task is not None and task["state"] == "running"
    tokens = report.transcript_tokens(event.raw.get("agent_transcript_path") or "")
    cap = ctx.cfg("tasks.max_tokens").get(work["level"], 0)
    if ctx.component("task_budget") and cap and tokens > cap and running:
        return [record("subagent_finish", agent_id=aid, state="budget", tokens=tokens),
                record("task", work=wid, number=task["number"], event="budget_exceeded"),
                record("block", work=wid, type="needs_you",
                       reason=f"budget superato: {tokens} token oltre il tetto di {cap} sul task "
                              f"{task['number']}. Proposta: dividere il task")]
    rep = report.parse_report(event.raw.get("last_assistant_message") or row["report"])

    def veto(msg: str):
        if row["vetoes"] >= MAX_VETOES:
            out = [record("subagent_finish", agent_id=aid, state="done",
                          declared_status=rep.status, tokens=tokens)]
            if running:
                out.append(record("task", work=wid, number=task["number"],
                                  event="report_blocked"))
            return out + [record("block", work=wid, type="needs_you",
                                 reason=f"implementatore chiuso dopo {MAX_VETOES} veti: {msg}")]
        return [record("subagent_veto", agent_id=aid),
                deny(f"{msg} (veto {row['vetoes'] + 1} di {MAX_VETOES})",
                     rule="subagent_stop")]

    if ctx.component("report_fields") and not rep.valid:
        return veto("report finale non valido: mancano " + ", ".join(rep.missing)
                    + ". Chiudi con un blocco JSON con i campi di 18.5")
    wt = Path(work["worktree"])
    head, base = git.head(wt), row["agent_base_sha"]
    commits = git.rev_list(wt, base, head) if base and head and base != head else []
    if ctx.component("task_size") and commits and not rep.data.get("size_reason"):
        lines = _task_lines(ctx, wt, base, head)
        if lines > ctx.cfg("tasks.task_lines_max"):
            return veto(f"il task cambia {lines} righe, oltre task_lines_max "
                        f"({ctx.cfg('tasks.task_lines_max')}): aggiungi size_reason al report "
                        f"oppure dividi il task")
    done = rep.status in ("DONE", "DONE_WITH_CONCERNS")
    if ctx.component("subagent_receipt_gate"):
        allow = ctx.cfg("project.allow_no_tests")
        if done and commits:
            latest = receipts.latest(ctx.db, wid, head)
            if not latest or not all(counts_green(r["state"], r["exit"], allow) for r in latest):
                return veto(f"DONE senza ricevuta green su {head[:10]}: lancia "
                            f"'{ctx.plugin_bin}' verify")
        elif done:
            if row["fingerprint"] and git.fingerprint(
                    wt, ctx.cfg("review.output_dirs")) != row["fingerprint"]:
                return veto("file modificati senza commit: committa e verifica")
        else:
            has_block = ctx.db.execute("SELECT 1 FROM blocks WHERE work = ? AND closed IS NULL",
                                       (wid,)).fetchone() is not None
            if not has_block and not receipts.any_since(ctx.db, wid, row["started"]):
                return veto(f"con {rep.status} serve una ricevuta ('{ctx.plugin_bin}' verify) "
                            f"oppure un blocco ('{ctx.plugin_bin}' block open <tipo> "
                            f"--reason …)")
    if done and task is not None:
        missing = _skill_missing(task)
        if missing:
            return veto("skill dei profili non usate: " + ", ".join(missing))
    out = [record("subagent_finish", agent_id=aid, state="done", declared_status=rep.status,
                  tokens=tokens)]
    if running:
        if done:
            out.append(record("task", work=wid, number=task["number"], event="report_done"))
        elif rep.status == "BLOCKED":
            out.append(record("task", work=wid, number=task["number"], event="report_blocked"))
            if ctx.db.execute("SELECT 1 FROM blocks WHERE work = ? AND closed IS NULL",
                              (wid,)).fetchone() is None:
                out.append(record("block", work=wid, type="needs_you",
                                  reason=f"task {task['number']} BLOCKED: "
                                         f"{rep.data.get('concerns') or rep.data.get('left') or ''}"[:500]))
    return out
```

- [ ] **Step 4: Verificare che passi**

Run: `tests/run`
Expected: OK. Nota su `test_tokens_over_cap_block_even_with_green`: il tetto L1 predefinito è 400.000; 500.001 token lo superano.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_checks/subagent_stop.py tests/test_check_subagent_stop.py
git commit -m "tollgate P2: SubagentStop per implementatori e subagenti di sola lettura"
```

---

### Task 20: Prove dei criteri dal wrapper, revisione 21 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p2.py`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21: decisioni 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 15, 22 di questo piano)
- Modify: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (stato, sezione 3 con i nomi reali di P2, vincoli per P3)

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «criteri della colonna P2 → test» nel piano principale; i contratti reali di P2 per P3 e P4.

- [ ] **Step 1: Test dal wrapper vero**

`tests/test_criteria_p2.py` fa passare alcuni criteri da `hooks/run` e `bin/tollgate` veri, come li lancia Claude Code (input JSON su stdin):

```python
import json
import subprocess
import unittest

from tests.hookkit import SESSION, Lab, sample
from tests.helpers import ROOT

RUN = ROOT / "hooks" / "run"


def run(lab, event, payload):
    return subprocess.run([str(RUN), event], input=json.dumps(payload), capture_output=True,
                          text=True, env=lab.ts.env(), timeout=60)


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def test_push_denied_in_bound_session(self):              # criterio 7
        r = run(self.lab, "PreToolUse", sample(
            "PreToolUse-Bash", session_id=SESSION, cwd=str(self.lab.wt),
            tool_input={"command": "git push origin tg/7-demo"}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("open-pr", r.stderr)

    def test_session_start_injects_state(self):              # criterio 19
        r = run(self.lab, "SessionStart", sample("SessionStart-none", session_id=SESSION,
                                                 cwd=str(self.lab.wt)))
        self.assertEqual(r.returncode, 0)
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(ctx), 1500)

    def test_general_purpose_denied(self):                  # criterio 4, eval 9
        r = run(self.lab, "PreToolUse", sample(
            "PreToolUse-Agent", session_id=SESSION, cwd=str(self.lab.wt),
            tool_input={"description": "d", "prompt": "p", "subagent_type": "general-purpose"}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("/tollgate:execute", r.stderr)

    def test_read_tool_not_routed(self):
        r = run(self.lab, "PreToolUse", sample("PreToolUse-Read", session_id=SESSION,
                                               cwd=str(self.lab.wt)))
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
```

Run: `tests/run`
Expected: OK.

- [ ] **Step 2: Matrice dei criteri**

Per ogni criterio della colonna P2 del piano principale (2, 3, 4 hook, 5, 6, 7, 8, 13, 14, 15, 18 parte P2, 19, 20, 21 parte P2, 22 parte P2, 23, 29 parte P2, 30 parte P2, 31 parte hook, 32 parte hook, 34 push negato, 37 parte hook, 38 parte hook, 39 `SubagentStop`, 42 `plan-check`) scrivere nel ledger (o nel rapporto finale) il test che lo dimostra, con `file::classe.metodo`. Un criterio senza test è un buco: si aggiunge il test nel modulo che possiede il codice, prima di chiudere. Criteri che restano in parte a P3 o P4 (per esempio la parte «`task start` sceglie l'agente» del 38) si annotano come tali.

Controlli minimi attesi (se mancano, aggiungerli):
- 18: per ogni chiave di `[components]` usata da P2 (`scope_check`, `plan_check`, `test_guard`, `context_guard`, `subagent_receipt_gate`, `single_writer`, `readonly_check`, `task_size`, `task_budget`, `must_have_tests`, `report_fields`) un test che la mette a `false` e vede il controllo spento. Quelli non coperti dai Task 15-19 vanno in `tests/test_components_p2.py`, un test per chiave, con la stessa forma di `ReceiptGateOffTest`.
- 38: un profilo `web` con `skills = ["ui-ux-pro-max"]` e un task su `web/`: DONE senza aver invocato la skill → veto (con `tasks.add_task(..., skills_required=["ui-ux-pro-max"])`).
- 15: ricevuta `empty` con zero test, report vecchio cancellato, variabile non in `env_allow` non visibile: già in `tests/test_verify.py`.

- [ ] **Step 3: Revisione 21 della spec (completamento)**

Oltre a quanto scritto nel Task 1, la revisione 21 riporta:
- 7.1: classificazione degli hook di controllo (`PreToolUse`) e informativi (gli altri), anche per «Python mancante» (decisione 1); scadenza interna con `signal.alarm` e cane da guardia del wrapper (decisione 4); interruttore gestito dal wrapper con `off.log` importato negli eventi (decisione 5); segnalino `bound/` (decisione 22);
- 12.2: le colonne e la tabella della migrazione 2 (decisione 7);
- 11.3: forma del file del contesto `{"used_pct": …}` (decisione 13);
- 8.4: oggetto e target degli atti per ogni comando (decisione 15); un `approve waiver` vale in ogni stato dell'atto (decisione 10);
- 8.3: le deroghe dichiarate sciolgono la violazione in locale anche se in attesa; `open-pr` rifiuta finché ce ne sono in attesa (decisione 9);
- 8.1: report configurato e assente → `red`; `uncounted` solo senza report (decisione 11).

- [ ] **Step 4: Piano principale**

In `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`:
- intestazione «Stato»: P2 chiuso sul ramo (merge su `main` in attesa dell'OK dell'utente), con il numero di test;
- sezione 3, «Pacchetti»: aggiungere `tollgate_hooks` (motore: adattatore, contesto, registro, runner, operazioni `record`);
- sezione 3, «Contratti», righe P2 → P3/P4 con i nomi reali: `tollgate_analysis.plan.check_plan`, `level.*`, `testguard.check` e `GuardConfig`, `junit.parse_junit`, `waivers.*`, `bash.*`, `report.*`; `tollgate_core.verify.run_verify`, `receipts.*`, `scope.register_plan`, `tasks.assign` (che `task start` deve chiamare con `pending = "launch"`, o `"resume"` per i giri 1-3), `subagents.*`, `effects.*`, `sessions.*`; il contratto dei moduli di `tollgate_checks` e l'elenco `apply.OPS`;
- vincoli nuovi per P3: `task start` scrive il brief con `name` uguale a `tasks.implementer`; la statusline scrive `ctx/<session_id>.json` con `used_pct`; `start` pulisce i segnalini `bound/` delle sessioni chiuse; `open-pr` rifiuta con deroghe in attesa (`waivers.status`) e con effetti `requested`; `approve level` scrive `level_cap_paths`; i verdetti dei revisori e i report degli avversari sono moduli nuovi di `tollgate_checks` per `subagent_stop`, che devono controllare `subagents.state != 'tampered'`;
- sezione 4, nota alla riga 16: le due voci verificate nel Task 1 con il loro esito.

- [ ] **Step 5: Suite completa e commit**

Run: `tests/run`
Expected: OK su entrambe le versioni, nessun `ResourceWarning` con `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`.

```bash
git add tests/test_criteria_p2.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git add tests/test_components_p2.py 2>/dev/null || true
git commit -m "tollgate P2: prove dei criteri dal wrapper, spec rev 21, piano principale"
```
