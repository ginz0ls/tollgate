# tollgate: specifica del nucleo (sotto-progetto A)

Data: 8 ottobre 2026.
Stato: **da rivedere**.
Fonti: `docs/REPORT-CONFRONTO-WORKFLOW.md`, `docs/COSA-TENERE.md` (voci 1-42, H1-H45, R1-R16, sezione 9), `docs/RICERCA-PAPER.md`.

---

## 1. Scopo

tollgate è un plugin per Claude Code. Porta un task **da un'issue GitHub a una PR verificata**; il merge lo fa sempre una persona.

Il flusso di lavoro resta quello di **Superpowers**: brainstorming → writing-plans → subagent-driven-development → review. tollgate aggiunge solo quello che manca:

1. **Obblighi imposti dagli hook**, non chiesti nel prompt:
   - niente «fatto» senza ricevute;
   - test che l'agente non può indebolire;
   - effetti esterni solo con conferma;
   - modifiche limitate ai file del piano.
2. **Livelli di rigore** (L0, L1, L2) scelti da uno script in base al rischio della modifica.
3. **Contesto pulito per ogni attività**, così il contesto non si degrada nelle sessioni lunghe.
4. **Prove prodotte dagli script**, mai dichiarate dal modello.

**Quando il nucleo funziona.** Su un repo reale un task passa da `start` a una PR. Ogni obbligo viene imposto, e sono imposti da codice, non da istruzioni. Lo verificano i test della sezione 13.

### 1.1 Fuori dal nucleo

| Cosa | Dove |
|---|---|
| Profili per tipo di file (frontend, backend in 3 varianti, database, sicurezza, AI/LLM, bugfix) con i loro controlli; caricamento delle regole tramite hook (R8); controllo dell'esistenza dei pacchetti (R11); analisi statica nel profilo sicurezza (R12) | Sotto-progetto **B** |
| Sotto-issue e dipendenze su GitHub Projects, presa in carico con scadenza, riconciliazione automatica, registrazione delle tue decisioni sui rilievi (R13) | Sotto-progetto **C** |
| Suite di eval completa con confronti e prove a componenti spenti, costo dei subagenti (R15) | Sotto-progetto **D** |
| Dashboard locale, avvio automatico da etichetta GitHub, portabilità verso altri harness, lezioni apprese, mutation testing | Dopo la v1 |

Il nucleo lascia già pronti i punti di aggancio per B e C: le colonne nel DB, la configurazione dei profili in `tollgate.toml` e gli eventi.

---

## 2. Decisioni prese

| Tema | Decisione |
|---|---|
| Harness | Claude Code |
| Tracker | GitHub Issues, tramite `gh` |
| Autonomia | Interattiva. L'avvio automatico viene dopo |
| Flusso | Quello di Superpowers, dichiarato come dipendenza |
| Struttura | Hook, script e due comandi principali: `/tollgate:start` e `/tollgate:finish` |
| Stato | SQLite locale, scritto solo dallo script `state` |
| Pianificatore | Il coordinatore, cioè la sessione principale, che può fare domande |
| Revisione | Revisore finale e verificatore scritti da tollgate; in L2 specialisti di Anthropic (sezione 9) |
| Pubblicazione | Privato ora, pubblico poi. Nel codice niente percorsi né nomi di progetti dell'utente |
| Lingua | Nomi in inglese per plugin, comandi, script e file; documentazione in italiano |

---

## 3. Struttura del plugin

```
tollgate/
  .claude-plugin/plugin.json   dependencies: superpowers, pr-review-toolkit (intervalli di versione)
  skills/
    start/SKILL.md             /tollgate:start #N
    finish/SKILL.md            /tollgate:finish
    off/SKILL.md               /tollgate:off   (disable-model-invocation: true)
    on/SKILL.md                /tollgate:on    (disable-model-invocation: true)
  agents/
    final-reviewer.md          revisore finale (sola lettura)
    finding-verifier.md        verificatore per ogni rilievo (sola lettura)
    plan-adversary.md          avversario del piano, solo L2 (sola lettura)
  hooks/hooks.json             tutti gli hook (gli agenti dei plugin non possono averne)
  bin/tollgate                 CLI Python, solo libreria standard
    state | verify | test-guard | plan-check | scope-check | context-guard | level
  statusline/statusline.sh     statusline dell'utente, più la scrittura della % di contesto
  templates/tollgate.toml      configurazione di esempio per un progetto
  tests/                       test unitari, degli hook e di integrazione
  evals/                       pochi casi di claude plugin eval sugli obblighi
```

**Principi di design.**
- **Unico accesso al DB.** Nessun componente apre il DB tranne `bin/tollgate state`.
- **Interfaccia uniforme.** Gli hook chiamano `bin/tollgate` con l'input JSON di Claude Code su stdin e restituiscono la decisione nel formato documentato.
- **Componenti spegnibili.** Ogni componente si può spegnere da `tollgate.toml` (R10).
- **Ordine di preferenza.** Prima si estende quello che esiste, poi CLI e skill, solo alla fine nuovi strumenti (H44).

---

## 4. Ruoli

| Ruolo | Chi è | Cosa fa | Permessi |
|---|---|---|---|
| Utente | — | Conferma il livello, approva spec e piano in L2, risolve i blocchi «serve te», fa il merge | Tutti |
| Coordinatore | La sessione principale | Dialogo, brainstorming, spec, **piano**. Lancia i subagenti e legge solo verdetti e percorsi. Non scrive codice, tranne in L0 | Lettura, scrittura dei documenti, subagenti |
| Implementatore | Subagente nuovo per ogni task (quello di Superpowers) | Scrive il codice di **un** task e fa il commit. È l'unico che scrive codice | Scrittura solo dentro lo scope |
| Revisore del task | Subagente di Superpowers | Controlla il task rispetto al piano | Sola lettura |
| Avversario del piano | `agents/plan-adversary.md`, solo L2 | Attacca il piano; riceve piano e spec senza le motivazioni dell'autore | Sola lettura |
| Revisore finale | `agents/final-reviewer.md` | Rivede la fetta rispetto a piano, must-have e scope; cerca casi speciali scritti per i test e test indeboliti (R3) | Sola lettura |
| Verificatore | `agents/finding-verifier.md` | Per ogni rilievo: lo conferma con prove (file, riga, motivo) oppure lo scarta | Sola lettura |
| Script | `bin/tollgate` | Producono i fatti: ricevute, controllo dei test, livello, scope, fasi | — |

**Come si passa il lavoro.** Ogni subagente riceve un **brief su file** e restituisce un **report su file**. Al coordinatore torna al massimo un verdetto di 1-2K token più il percorso del report (R7).

---

## 5. Livelli

Il livello lo calcola `bin/tollgate level` e **può solo salire**.

| Livello | Quando | Percorso |
|---|---|---|
| **L0** | Al massimo `l0_max_files` file (predefinito 2) e `l0_max_lines` righe (predefinito 50), nessun percorso sensibile | Implementazione diretta nella sessione, `verify`, `finish`. Niente brainstorming né piano |
| **L1** | Il caso normale | writing-plans → controllo della struttura del piano → esecuzione per task → revisione finale |
| **L2** | Percorsi sensibili (`sensitive_paths`), etichette sensibili, oppure tua scelta | brainstorming → spec → piano principale se serve più di una fetta → piano della fetta → avversario → tua approvazione → esecuzione → revisione finale con specialisti |

**Come si stima e come sale.**
- **All'avvio** il livello si stima da etichette e testo dell'issue; tu confermi o alzi.
- **Durante il lavoro**, dopo ogni modifica, conta file e righe toccati e controlla i percorsi:
  - superate le soglie di L0 → passa a L1 e nega altre modifiche finché non c'è un piano;
  - toccato un percorso sensibile → passa a L2.

**Piano principale** (si crea solo se il lavoro non sta in una fetta):
- elenca fette, ordine, dipendenze e interfacce tra le fette;
- ogni fetta ha il suo piano, scritto quando arriva il suo turno, e la sua PR con «Part of #N»;
- nel nucleo le fette restano sulla stessa issue; le sotto-issue arrivano con C.

---

## 6. Ciclo di vita

```
SESSIONE 1: avvio e piano
/tollgate:start #N
  1. controlli      repo pulito; CI del ramo base verde (se è rossa: avviso e conferma)
  2. livello        proposto, confermato dall'utente
  3. worktree       ramo tg/<N>-<slug>; riga in tasks (fase = piano, SHA di partenza)
  4. per livello    L0: implementa → verify → finish
                    L1: writing-plans → plan-check (R6) → scope registrato
                    L2: brainstorming → spec → checkpoint + /clear → piano principale e piano della fetta
                        → plan-adversary → tua approvazione
  → checkpoint + /clear

SESSIONE 2: una fetta per sessione
/tollgate:start #N   riparte dal DB (fase = esecuzione)
  SessionStart inietta 5-10 righe: issue, fetta, task corrente, scope, livello (R5, R9)
  per ogni task, uno alla volta:
    brief = testo del task + scope + test correlati (R2) + passo del piano (R5)
    implementatore → commit → tollgate verify (test correlati) → ricevuta
    SubagentStop: se ci sono commit senza ricevuta verde, il subagente non può chiudere
    test e specifica in conflitto → blocco conflitto_test_spec (R1); i test non si toccano
    al massimo 2 giri di correzione (R4), poi contesto pulito o blocco serve_te
    revisore del task di Superpowers
  guardia del contesto: avviso al 45%; al 55% nega nuovi subagenti → checkpoint + /clear

/tollgate:finish
  5. prove          suite completa rieseguita da finish → ricevuta sullo SHA attuale;
                    test-guard; scope; deroghe (al massimo 2, oppure approvate)
  6. revisione      final-reviewer (+ specialisti e Codex in L2) → finding-verifier per ogni rilievo
                    → verdetto JSON; al massimo 4 giri, poi serve_te
  7. PR             intento salvato → push → ls-remote → cerca una PR esistente → crea la PR
                    descrizione: livello, ricevute, deroghe, blocchi, verdetto
  8. merge          lo fa l'utente; la fetta successiva parte in una sessione nuova
```

---

## 7. Hook

Tutti gli hook stanno in `hooks/hooks.json` e sono di tipo `command`. **Gli hook che fanno da controllo, se si rompono, bloccano** (H28). Gli hook informativi, se si rompono, lasciano passare.

| Evento | Filtro | Comportamento | Voci |
|---|---|---|---|
| `SessionStart` | `startup`, `resume`, `clear`, `compact` | Con un task attivo inietta 5-10 righe di stato (meno di 10.000 caratteri); senza task attivo non aggiunge niente | 41, R5, R9 |
| `PreToolUse` | `Edit`, `Write`, `MultiEdit`, `NotebookEdit` | `scope-check`: un file fuori dallo scope viene negato con l'istruzione per registrare una deroga. File protetti (`tollgate.toml`, file del plugin, impostazioni di Claude Code): negati sempre | 5, H24 |
| `PreToolUse` | `Bash` | Comandi distruttivi (force push, `reset --hard`, `--no-verify`, `rm -rf` fuori dal worktree) → `deny`. Effetti esterni presi dalla lista in `tollgate.toml` → `ask`. `git commit` → `test-guard` sul diff. `git push` e `gh pr create` fuori da `finish` → `deny`. Comandi che toccano il DB di tollgate → `deny` | 6, 10 |
| `PreToolUse` | `Agent` | `context-guard`: sopra `stop_pct` → `deny` con l'istruzione di fare checkpoint e `/clear` | 42, R7 |
| `PostToolUse` | `Write` sui file di piano | `plan-check`: sezioni obbligatorie, scope e must-have. Se manca qualcosa il piano torna indietro con `decision: block`; se è a posto lo scope viene registrato | 13, R6 |
| `SubagentStart` | tutti | Salva lo SHA di partenza del subagente | 8 |
| `SubagentStop` | tutti | Se ci sono commit dopo lo SHA di partenza senza una ricevuta verde sull'ultimo commit → `block` con il motivo. Rispetta `stop_hook_active`; dopo 2 blocchi apre un blocco `serve_te` | 8, H36 |

**`Stop` della sessione principale: nessun blocco.** Il gate è `finish`.

**In L0 non c'è un piano**, quindi `scope-check` non si applica: al suo posto lavora `level`, che porta il task a L1, e quindi a un piano obbligatorio, appena si superano le soglie di L0 o si tocca un percorso sensibile.

**Sezioni obbligatorie del piano** controllate da `plan-check`:
- Fatti verificati (fatto / dove / conseguenza, su uno SHA);
- Decisioni (scelta / perché / costo se sbagliata);
- Interfacce;
- Must-have;
- Scope, ricavato da `Create:`, `Modify:` e `Test:` di ogni task;
- Punti di arresto;
- Rischi.

Le sezioni sono configurabili. Il formato dei task resta quello di Superpowers.

---

## 8. Ricevute, test-guard e deroghe

**Ricevute.**
- **Chi le produce**: solo `bin/tollgate verify`, che esegue i comandi di `tollgate.toml` (`verify`, `test_related`, `test_all`).
- **Cosa registrano**: SHA, worktree pulito, identificativo del comando, codice d'uscita, durata, percorso del log.
- **Nel contesto**: solo l'esito più le ultime righe.
- **Quando sono valide**: SHA uguale all'ultimo commit e worktree pulito.
- **Test instabili**: un solo nuovo tentativo; se al secondo passa, la ricevuta è segnata «instabile».
- **Comando mancante**: la ricevuta dice «non verificato», mai «passato».
- **Al gate**: `finish` riesegue `test_all` e usa solo la ricevuta che produce lui stesso.

**test-guard.** Confronta il diff con lo SHA di partenza e segnala:
- file di test cancellati;
- casi di test diminuiti;
- `skip` e `only` aggiunti;
- soglie di copertura abbassate;
- file della CI modificati;
- snapshot o baseline visive aggiornati.

I pattern da cercare stanno in `tollgate.toml`, con valori predefiniti per JavaScript, TypeScript e Python. Ogni modifica segnalata richiede una deroga.

**Deroghe.**
- **Chi le registra**: lo script `bin/tollgate state waiver`, con scelta, motivo e costo se sbagliata.
- **Tetto**: oltre 2 per fetta serve la tua approvazione.
- **Dove compaiono**: tutte nella PR.

**Blocchi tipizzati.** `serve_te`, `conflitto_test_spec`, `dipendenza`, `permesso`, `transitorio`.
- Il blocco `conflitto_test_spec` è la via d'uscita prevista quando un test contraddice la specifica (R1): **l'agente non modifica il test**, si ferma e ti chiede.

---

## 9. Revisione finale

| Livello | Revisori | Poi |
|---|---|---|
| L0 | Nessun agente | Ricevute e merge tuo |
| L1 | `final-reviewer` con la checklist dei profili attivi (nel nucleo: solo il profilo base) | `finding-verifier` per ogni rilievo → verdetto |
| L2 | `final-reviewer` + specialisti scelti in base ai profili attivi, al massimo 3, ognuno con il suo contesto: `/security-review`, `pr-review-toolkit:pr-test-analyzer`, `pr-review-toolkit:silent-failure-hunter`. Codex come parere, se installato (R16) | `finding-verifier` per ogni rilievo → verdetto |

**Verdetto.**
- Una riga JSON: `{"esito": "ok" | "da_correggere" | "serve_te", "rilievi": [{gravita, file, riga, testo, verificato}]}`.
- **Gravità**: `bloccante`, `grave`, `rilevante`, `minore`. Le definizioni del progetto stanno in `tollgate.toml`.
- **JSON malformato**: conta come esito `serve_te`, mai come «ok».
- **Tetto di 4 giri**: il contatore non si azzera.
- **Rilievi**: solo i rilievi **confermati** dal verificatore con gravità `bloccante` o `grave` fermano la PR. Quelli `rilevante` e `minore` vengono elencati nella PR.
- Il verificatore sostituisce il filtro di confidenza ≥80.

---

## 10. Stato

**Il file.**
- `tollgate.db` sta in `CLAUDE_PLUGIN_DATA`: uno per macchina, con una colonna per il repo.
- SQLite con `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout=5000`.
- Scrive solo `bin/tollgate state`.

| Tabella | Colonne principali |
|---|---|
| `tasks` | id, repo, issue, issue madre, fetta, livello, fase, fase prima del blocco, ramo, worktree, SHA di partenza, session_id, `lease_owner` e `lease_until` (già pronti per C), date |
| `scope` | task, percorso, origine (`piano` o `deroga`) |
| `receipts` | task, sha, worktree pulito, comando, exit, durata, log, `prodotta_da` (`verify` o `finish`), instabile |
| `waivers` | task, tipo, scelta, perché, costo, approvata da |
| `blocks` | task, tipo, motivo, aperto, chiuso, risoluzione |
| `findings` | task, giro, fonte, gravità, file, riga, testo, esito della verifica, `decisione_utente` (già pronta per R13) |
| `intents` | task, azione, dati, stato |
| `events` | registro in sola aggiunta: ora, sessione, task, tipo, dati JSON |
| `meta` | versione dello schema |

**Percentuale di contesto.** La statusline la scrive in un file per sessione, `CLAUDE_PLUGIN_DATA/ctx/<session_id>.json`, non nel DB.

**Fasi:** `piano` → `approvazione` (solo L2) → `esecuzione` → `revisione` → `pr_aperta` → `chiuso`. Da qualunque fase si può passare a `bloccato`, e da lì si torna alla fase precedente.
- **Chi cambia fase**: le fasi le cambiano solo `start`, `finish` e il tuo merge (rilevato da `gh` alla chiamata successiva). L'agente non cambia mai fase.

**Ripresa.** `start` controlla:
- che il worktree esista;
- che lo SHA del DB corrisponda al ramo;
- se ci sono intenti in sospeso: li completa, cercando prima se la PR esiste già.

Se qualcosa non corrisponde si ferma e chiede.

**Traccia permanente.** Sta nella descrizione della PR, non nel DB.

---

## 11. `tollgate.toml` (nel repo del progetto)

```toml
[project]
base_branch = "main"

[commands]
verify       = "npm run check"               # verifica completa del progetto
test_all     = "npx vitest run"
test_related = "npx vitest related --run {files}"
timeout_s    = 900

[levels]
sensitive_paths  = ["**/migrations/**", "**/auth/**"]
sensitive_labels = ["security", "database"]
l0_max_files = 2
l0_max_lines = 50

[context]
warn_pct = 45
stop_pct = 55

[external_effects]
commands        = ["supabase db push", "supabase functions deploy", "wrangler deploy", "gh pr merge", "npm publish"]
project_scripts = ["deploy", "release"]

[test_guard]
test_globs   = ["**/*.test.*", "**/*.spec.*", "tests/**", "**/test_*.py"]
ci_globs     = [".github/workflows/**"]
skip_markers = [".skip(", ".only(", "xit(", "@pytest.mark.skip"]

[severity]   # definizioni del progetto, lette dal revisore e dal verificatore
bloccante = "dato sbagliato senza conferma, dati di altri utenti, azione eseguita due volte"
grave     = "un passo che fallirebbe così com'è scritto"

[components]  # R10: ogni componente si può spegnere
scope_check = true
plan_check = true
test_guard = true
context_guard = true
subagent_receipt_gate = true
final_review = true
plan_adversary = true
specialists = true
```

**Modifiche al file.** `tollgate.toml` è protetto: lo modifica solo l'utente.

---

## 12. Errori e casi limite

| Situazione | Comportamento |
|---|---|
| Script di controllo rotto | L'hook blocca e mostra il percorso del log e l'indicazione di `/tollgate:off` |
| Effetto esterno nascosto in uno script del progetto | Va elencato in `project_scripts`; resta un limite noto («best effort») |
| Comando di verifica assente | «Non verificato»; `finish` richiede il tuo sì esplicito, scritto nella PR |
| Test instabili | Un nuovo tentativo, poi la ricevuta è segnata «instabile» |
| Timeout | Il test vale come fallito |
| CI del ramo base rossa | Avviso e conferma, scritti nella PR |
| Ramo base andato avanti con conflitti | Blocco `serve_te`, nessun rebase automatico |
| Subagente che insiste a chiudere senza ricevuta | 2 rimandi, poi `serve_te` |
| Stesso task aperto in due sessioni | Avviso e conferma |
| DB occupato per più di 5 secondi | Errore: l'hook blocca |
| GitHub irraggiungibile | Le fasi locali continuano; `start` su un'issue nuova e `finish` si fermano; gli intenti restano in sospeso |
| Piano modificato dopo la registrazione | Ricontrollo; in L2 il piano torna in approvazione |
| Un lavoro L0 cresce | Sale a L1 e serve un piano |
| Statusline assente | La guardia del contesto si spegne con un avviso |
| Superpowers mancante o di versione incompatibile | `start` si rifiuta e spiega cosa fare |
| Worktree o DB che non corrispondono a git | Si ferma e chiede |
| Merge fatto ma DB non aggiornato | Vince GitHub alla chiamata successiva |

---

## 13. Test del plugin

| Livello | Cosa | Come |
|---|---|---|
| Script | `state`, `verify`, `test-guard`, `plan-check`, `scope-check`, `level`, `context-guard` | Test unitari con diff e piani di esempio |
| Hook | Ogni regola decide `allow`, `deny` o `ask` correttamente, e uno script rotto blocca | Input JSON uguale a quello di Claude Code; si controllano risposta e codice d'uscita |
| Integrazione | `start → verify → finish`, ripresa, intenti in sospeso | Repo git temporaneo e un finto `gh` nel PATH |
| Comportamento | L'agente con tollgate rispetta gli obblighi | Pochi casi di `claude plugin eval`, 3 esecuzioni ciascuno (vedi sotto) |
| CI | Script, hook e integrazione verdi a ogni push | GitHub Action sul repo di tollgate |

**Casi di eval nel nucleo:**
1. Dichiarare «fatto» senza test → bloccato.
2. Test in conflitto con la specifica → blocco `conflitto_test_spec`, test intatto.
3. Modifica fuori scope → negata, deroga registrata.
4. Comando di deploy → richiesta di conferma.
5. Lavoro L0 che cresce → livello L1.

---

## 14. Criteri di accettazione del nucleo

1. `start #N` su un repo con `tollgate.toml` crea worktree, ramo e riga nel DB, e propone il livello.
2. Un piano senza le sezioni obbligatorie viene rimandato indietro; un piano completo registra lo scope.
3. La modifica di un file fuori scope viene negata; dopo una deroga registrata viene permessa.
4. Un subagente che ha fatto commit senza ricevuta verde non può chiudere.
5. `git commit` con un test cancellato o un `skip` aggiunto viene negato senza deroga.
6. I comandi elencati in `external_effects` chiedono conferma; quelli distruttivi vengono negati.
7. Sopra `stop_pct` non partono nuovi subagenti.
8. `finish` riesegue `test_all` e apre la PR solo con ricevuta verde, test-guard pulito, scope rispettato, deroghe entro il tetto e verdetto senza rilievi confermati bloccanti o gravi.
9. Dopo un'interruzione tra push e creazione della PR, `start` riprende e non crea PR doppie.
10. `tollgate.toml` e i file del plugin non sono modificabili dall'agente; `/tollgate:off` e `/tollgate:on` li può invocare solo l'utente.
11. Ogni componente elencato in `[components]` si spegne e i test lo dimostrano.
12. Le righe iniettate all'avvio restano sotto il tetto del budget di istruzioni (R9), misurato da un test.

---

## 15. Da verificare sulla documentazione prima di scrivere codice

- `SubagentStart`: può aggiungere contesto al subagente? Se non può, il brief di Superpowers basta.
- `PreToolUse`: semantica di `updatedInput` e di `defer`.
- Se un plugin può impostare la statusline, o se serve un passo di installazione che modifichi `settings.json` con il consenso dell'utente.
- Il funzionamento di `disable-model-invocation` sulle skill di un plugin.
- Il matcher per lo strumento dei subagenti (`Agent` o `Task`) nella versione installata.
- Il formato dei vincoli di versione in `dependencies` verso marketplace diversi (`allowCrossMarketplaceDependenciesOn`).
