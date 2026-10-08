# Stato dell'audit: specifica del nucleo di tollgate

Documento auditato: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`.
Metodo: skill `prd-audit` (lenti L1-L10, otto punti di vista, due cicli vuoti per ciascuno, tetto di 30 cicli). In parallelo: revisione avversariale a contesto pulito, senza le motivazioni dell'autore (`2026-10-08-revisione-avversariale-spec-nucleo.md`).
Giudice esterno (`/goal`): **non usato**, per scelta dell'utente l'08/10/2026. La chiusura la decide chi conduce l'audit.
Stato: **SOSPESO al ciclo 30** (tetto raggiunto, non chiuso). Vedi «Esito» in fondo.

## Perimetro

- **Dentro**: la specifica e i documenti con cui deve essere coerente, cioè `docs/COSA-TENERE.md` (decisioni: voci 1-42, H, R1-R16, sezione 9) e `docs/RICERCA-PAPER.md`. Più i fatti esterni: documentazione di Claude Code e Superpowers 6.4.1 installato.
- **Fuori**: report di confronto (`REPORT-CONFRONTO-WORKFLOW.md`), consultato solo se un requisito vi rimanda. Sotto-progetti B, C e D, verificati solo per gli agganci che il nucleo deve lasciare.

## Criterio di gravità tarato su tollgate

| Gravità | Significato in questo progetto |
|---|---|
| **Bloccante** | Un obbligo aggirabile dall'agente senza lasciare traccia. Un effetto esterno (push, PR, deploy, db push) ripetuto o eseguito senza conferma. Stato corrotto. L'utente bloccato senza via d'uscita. Una scelta che impedisce B, C o D |
| **Grave** | Un meccanismo che non può funzionare come scritto su Claude Code o con Superpowers. Una contraddizione che l'implementatore risolverebbe a caso. Un criterio di accettazione che lascia scoperto un obbligo |
| **Rilevante** | Attrito, costo in token, falsi positivi frequenti, ambiguità che produrrà debito |
| **Minore** | Redazionale, numerazione, riferimenti |

Un rilievo rilevante o superiore azzera il contatore.

## Inventario (sezioni × esito)

La specifica è alla **revisione 10**. Le sezioni 6.1, 6.3, 8 e 9 sono state riscritte: vanno riauditate da tutti i punti di vista.

| Sezione | Lenti applicate | Esito |
|---|---|---|
| 1 Scopo / 1.1 | L1-L10 (cicli 1-3) | A-01, A-03 → corretto, **da riauditare** |
| 2 Decisioni | L1-L10 | A-19 → corretto, da riauditare |
| 3 Struttura | L1-L10 | A-04, A-22 → corretto, da riauditare |
| 4 Ruoli | L1-L10 | A-05 → corretto, da riauditare |
| 5 Livelli | L1-L10 | A-10, A-12 → corretto, da riauditare |
| 6 Ciclo di vita | L1-L10 | A-01, A-07, A-09, A-11 → corretto, da riauditare |
| 7 Hook | L1-L10 | A-02, A-03, A-06, A-09, A-10, A-13, A-25 → corretto, da riauditare |
| 8 Ricevute, test-guard, deroghe | L1-L10 | A-06, A-14, A-15 → corretto, da riauditare |
| 9 Revisione finale | L1-L10 | A-08, A-16 → corretto, da riauditare |
| 10 Stato | L1-L10 | A-12, A-18 → corretto, da riauditare |
| 11 tollgate.toml | L1-L10 | A-19, A-20 → corretto, da riauditare |
| 12 Errori | L1-L10 | integrato, da riauditare |
| 13 Test | L5, L6 | integrato, da riauditare |
| 14 Criteri | L4, L5, L6 | A-21 → corretto, da riauditare |
| 15 Da verificare | L8, L10 | ampliato, da riauditare |
| 16 Revisioni (nuova) | — | da auditare |

## Matrice dei punti di vista (sulla revisione 5: tutti i contatori ripartono)

| Punto di vista | Cicli precedenti | Ultimo esito | Contatore vuoti sulla rev. 5 |
|---|---|---|---|
| Chi esegue | 1, 10, 12 | 12: 1 bloccante, 2 gravi → **da ripetere** | 0 |
| Chi attacca | 2, 4, 10, 11 | rilievi (seconda avversariale: 10 bloccanti) | 0 |
| Chi usa | 3, 13 | 13: vuoto (controlli: numero di atti, `finish` digitato o invocato dal modello, sessioni senza tollgate nello stesso repo) | 1 |
| Chi paga | 5, 15 | 15: 1 minore | 1 |
| Chi arriva dopo | 6, 18 | 18: 1 minore | 1 |
| Lo scettico | 7, 17 | 17: vuoto | 1 |
| Il caso limite | 8, 14 | 14: 1 grave → **da ripetere** | 0 |
| Chi integra | 9, 16 | 16: vuoto | 1 |

## Rilievi (cicli 1-3, corretti nella revisione 2 della specifica)

| ID | Gravità | Stato | Sezione | Rilievo | Correzione |
|---|---|---|---|---|---|
| A-01 | Bloccante | [VERIFICATO] | 1, 6 | subagent-driven-development finisce con `finishing-a-development-branch`, che offre merge locale, PR, «tieni» o scarto con `git branch -D` e `git worktree remove` (`superpowers/6.4.1/skills/finishing-a-development-branch/SKILL.md:55-64, 86-110, 156, 173`; `subagent-driven-development/SKILL.md:120, 487`). La specifica non ne parlava: si potevano saltare PR e merge umano, e lo scarto corrompeva lo stato | Il passo è sostituito da `/tollgate:finish` (6.3); gli hook negano merge verso la base, push, cancellazione dei rami `tg/*` e rimozione del worktree |
| A-02 | Bloccante | [RAGIONATO] | 7, 11 | File protetti e scope controllati solo su Edit e Write: via Bash (`sed -i`, `>`, `tee`, `cp`) l'agente poteva modificare `tollgate.toml` e spegnere i componenti, o uscire dallo scope | Configurazione letta dal commit di partenza; `finish check` blocca se `tollgate.toml` è cambiato; scope e test-guard autorevoli sul diff (8.4); regole Bash «best effort» |
| A-03 | Bloccante | [RAGIONATO] | 1, 7 | Gli hook non vedono i processi figli né impediscono `claude plugin disable` o la modifica delle impostazioni: i controlli si aggiravano senza traccia | Prova di presenza: ogni commit deve avere il suo evento dall'hook, altrimenti «commit fuori controllo» e PR ferma fino a `/tollgate:approve` (8.4); il limite è dichiarato nella sezione 1 |
| A-04 | Grave | [RAGIONATO] | 3, 6 | «`git push` e `gh pr create` negati fuori da `finish`»: l'hook non può sapere se un comando Bash arriva da `finish` | I passi deterministici li esegue `bin/tollgate finish open-pr`, un processo figlio invisibile agli hook; push e PR diretti sono sempre negati; sottocomandi divisi per chiamante |
| A-05 | Bloccante | [RAGIONATO] | 4, 9 | Il verdetto passava dal coordinatore, che poteva alterarlo o inventarlo | I verdetti li registra `SubagentStop` dall'ultimo messaggio dei subagenti di tollgate |
| A-06 | Grave | [VERIFICATO] | 7, 8 | La regola «commit senza ricevuta verde = non chiude» bloccava gli implementatori che dichiarano legittimamente `BLOCKED` o `NEEDS_CONTEXT` (`subagent-driven-development/SKILL.md:290-296`) | Regola per stato dichiarato (8.1) |
| A-07 | Grave | [VERIFICATO] | 6, 7 | R4 (2 giri di correzione) senza meccanismo, in conflitto con il tetto di Superpowers a 5 (`SKILL.md:406`) | Hook `PreToolUse` su Agent che legge il registro di Superpowers; formato del registro tra le cose da verificare |
| A-08 | Rilevante | [VERIFICATO] | 9 | Doppia revisione finale: Superpowers ne fa già una dell'intero ramo (`SKILL.md:446-469`) | La skill `start` indica di saltarla; il costo residuo si misura in D |
| A-09 | Grave | [RAGIONATO] | 6, 7 | Nella fase `piano` lo scope era vuoto: lo scope-check avrebbe negato anche la scrittura del piano | Nelle fasi `piano` e `approvazione` si scrive solo sotto `docs/superpowers/` |
| A-10 | Grave | [RAGIONATO] | 5, 7 | La sezione 5 diceva «dopo ogni modifica si ricalcola il livello», ma nessun hook lo faceva | `PostToolUse` su Edit e Write, più `git commit` e `finish` |
| A-11 | Grave | [RAGIONATO] | 6 | Non era detto in quale directory lavora la sessione né come un hook capisce quale task è attivo | Sezione 6.4: il task si ricava dal ramo `tg/<N>-*` |
| A-12 | Grave | [RAGIONATO] | 5, 10 | Nessun posto per le fette del piano principale: `start #N` non poteva sapere quale fetta viene dopo | Tabella `slices`; `plan-check` riconosce il piano principale |
| A-13 | Grave | [RAGIONATO] | 7, 8 | Nessun modo per te di approvare deroghe, risolvere blocchi, approvare il piano in L2 | Skill `approve` e `resolve` riservate all'utente, registrate dall'hook `UserPromptSubmit` |
| A-14 | Rilevante | [RAGIONATO] | 6, 8 | `finish` rieseguiva solo `test_all`, non `verify` (lint e typecheck) | `finish check` riesegue `verify` e `test_all` |
| A-15 | Rilevante | [RAGIONATO] | 8 | I file prodotti dai test rendevano «sporco» il worktree e invalidavano la ricevuta | Pulizia controllata prima dell'esecuzione |
| A-16 | Rilevante | [VERIFICATO] | 9 | `/security-review` è una skill: eseguita nel coordinatore ne sporca il contesto | `tollgate:specialist-runner` la esegue in un subagente; da verificare che un subagente possa usare Skill |
| A-17 | Rilevante | [RAGIONATO] | 1.1 | Il limite di ~30K token per i subagenti (R7) non ha nessun meccanismo | Dichiarato fuori dal nucleo, si misura in D |
| A-18 | Rilevante | [RAGIONATO] | 10 | Log, eventi e file di contesto crescono senza limite | Pulizia a `start` con giorni di conservazione configurabili |
| A-19 | Rilevante | [RAGIONATO] | 2, 11 | `gh pr merge` era tra gli effetti esterni «con conferma»: contraddice «il merge lo fa sempre una persona» | Merge negato all'agente |
| A-20 | Minore | [VERIFICATO] | 11 | Gravità `rilevante` e `minore` mancanti; sezione profili assente nonostante la 1.1 la citasse | Aggiunte |
| A-21 | Rilevante | [RAGIONATO] | 14 | Criteri mancanti per: comportamento quando uno script si rompe, prova di presenza, configurazione dalla base, atti dell'utente, sostituzione della chiusura di Superpowers | Criteri 10-13 e collegamento di ogni criterio a un test |
| A-22 | Rilevante | [RAGIONATO] | 10, 15 | `CLAUDE_PLUGIN_DATA` potrebbe non arrivare alla statusline | Tra le cose da verificare, con alternativa |
| A-25 | Grave | [VERIFICATO] | 7 | «Un solo scrittore» era solo una regola nel prompt di Superpowers (`subagent-driven-development/SKILL.md:282`) | Hook su Agent: un solo `general-purpose` attivo per worktree |

(A-23 e A-24 sono stati scartati, vedi sotto.)


## Rilievi del ciclo 4 (revisione avversariale, corretti nella revisione 3)

Il report completo è in `2026-10-08-revisione-avversariale-spec-nucleo.md`, con 36 voci: 7 bloccanti, 17 gravi, 11 rilevanti e 1 minore. Era stato condotto sulla revisione 1: le voci già coperte dalla revisione 2 sono indicate.

| V | Gravità | Esito nella revisione 3 |
|---|---|---|
| 1 CLI nel PATH, sottocomandi non separati | Bloccante | Già nella rev. 2 (sottocomandi per chiamante). Il resto (import del modulo Python) è dichiarato nella sezione 16 e coperto dal controllo autorevole |
| 2 Gli hook non bloccano se si rompono | Bloccante | **Corretto**: wrapper `hooks/run` (7.1). [VERIFICATO] hooks.md: «exit code 2 is the only exit code that blocks through the code alone»; il timeout non blocca |
| 3 Scope e file protetti aggirabili via Bash | Bloccante | Già nella rev. 2 (A-02) |
| 4 Ricevute falsificabili cambiando `package.json` o la configurazione dei test | Bloccante | **Corretto**: comando risolto nella ricevuta, `command_files` sotto test-guard, deroga `comando` sempre approvata da te, controllo 8.4.5 |
| 5 test-guard cieco con `git add -A && git commit` | Bloccante | **Corretto**: working tree più indice rispetto alla base (7.4) |
| 6 Effetti esterni solo come lista nera di stringhe | Bloccante | **Corretto in parte**: MCP con `ask`, curl, gh api e shell annidate; il limite residuo è nella sezione 16 |
| 7 Stallo tra deroga e divieto sul DB | Bloccante | Già nella rev. 2 (A-23) |
| 8 Approvazioni non autenticate | Grave | **Corretto**: `UserPromptExpansion` [VERIFICATO] |
| 9 `finish` come skill e divieto di push | Grave | Già nella rev. 2 (A-04) |
| 10 Eval 1 in contraddizione con «Stop: nessun blocco» | Grave | **Corretto**: eval 1 riscritto |
| 11 `/tollgate:off` passa dai componenti rotti | Grave | **Corretto**: file `OFF` scritto dal wrapper senza Python |
| 12 Il plugin non può impostare la statusline | Grave | **Corretto**: `/tollgate:setup`; `null` non blocca. [VERIFICATO] components.md: «Only two keys take effect from a plugin, agent and subagentStatusLine» |
| 13 Dipendenze tra marketplace e versioni | Grave | **Corretto**: `marketplace.json` con `allowCrossMarketplaceDependenciesOn`; specialisti opzionali |
| 14 `PostToolUse` non annulla; matcher solo su Write | Grave | **Corretto**: il piano resta scritto ma non registrato; matcher anche su Edit [VERIFICATO] |
| 15 Le sezioni del piano non le produce writing-plans; intervalli di righe | Grave | Già nella rev. 2 (start dà le sezioni); **corretto** il parser |
| 16 Lo scope nega i file di servizio di Superpowers e i lockfile | Grave | **Corretto**: `.superpowers/**` sempre permessi, `[scope] always` |
| 17 La sola lettura non è imponibile | Grave | **Corretto**: controllo di sola lettura (7.3) |
| 18 Tetti dei giri incoerenti con Superpowers | Grave | **Corretto**: chiarito che R4 prevale su 5 e che i 4 giri sono di tollgate |
| 19 L0→L1 senza hook; nega anche il piano | Grave | Rev. 2 per l'hook; **corretto**: la fase torna `piano` |
| 20 `SubagentStop`: contatore e worktree sporco | Grave | **Corretto**: contatore nel DB; BLOCKED con worktree sporco ammesso |
| 21 Worktree e `session_id` dopo `/clear` | Grave | Rev. 2 per il ramo; **corretto**: due sessioni rilevate dagli eventi, `git worktree add` doppio negato |
| 22 Asserzioni indebolite non rilevate | Grave | **Corretto in parte**: conteggio delle asserzioni; il resto è dichiarato nella sezione 16 e affidato a R3 |
| 23 Una deroga può coprire una cartella | Grave | **Corretto**: un file per deroga |
| 24 Testo dell'issue e slug non ripuliti | Grave | **Corretto**: slug ripulito, issue come dato non fidato |
| 25 Falsi positivi di test-guard | Rilevante | **Corretto**: parole intere, solo file di test, conteggio per nome, fixture escluse |
| 26 Ricevuta verde con zero test | Rilevante | **Corretto**: ricevuta «vuota» |
| 27 Effetti esterni ripetuti dopo una ripresa | Rilevante | **Corretto**: intenti idempotenti con conferma (8.5) |
| 28 Livello solo in salita anche con falsi positivi | Rilevante | **Corretto**: abbassamento solo da te |
| 29 Nessun bootstrap di `tollgate.toml` | Rilevante | **Corretto**: `/tollgate:init`, rifiuto senza file |
| 30 Termini con due significati | Rilevante | **Corretto**: glossario, tabella `work_items` |
| 31 Il coordinatore può scrivere codice | Rilevante | **Corretto**: niente codice senza `agent_id` in L1 e L2 (da verificare) |
| 32 Chiave del repo e unicità indefinite | Rilevante | **Corretto**: glossario e vincoli |
| 33 Criteri incompleti | Rilevante | **Corretto**: 17 criteri, ognuno con azione, osservazione e test |
| 34 Attriti per B, C e D | Rilevante | **Corretto**: override, mappa aperta, presa in carico solo locale |
| 35 `/security-review` non è un agente | Rilevante | **Corretto**: `specialist-runner` o `context: fork`, da verificare |
| 36 Redazionali | Minore | **Corretto** |


## Rilievi dei cicli 5-10 (sulla revisione 3, da correggere nella revisione 4)

| ID | Ciclo | Gravità | Stato | Sezione | Rilievo | Correzione prevista |
|---|---|---|---|---|---|---|
| B-01 | 5 chi paga | Rilevante | [RAGIONATO] | 8.4 | `finish check` riesegue `verify` **e** `test_all`; se `verify` comprende già i test (come la verifica tipica di un progetto) i test girano due volte | Comandi del gate configurabili: `[commands] gate = ["verify"]` (predefinito), e il conteggio dei test si legge dal reporter di quel comando |
| B-02 | 5 chi paga | Rilevante | [RAGIONATO] | 9 | Un verificatore **per ogni rilievo** vuol dire N subagenti per giro di revisione: il costo cresce con i rilievi | Un solo subagente verificatore per giro, che controlla ogni rilievo separatamente con le sue prove; tetto `max_findings` per giro (predefinito 15, in ordine di gravità) |
| B-03 | 5 chi paga | Rilevante | [RAGIONATO] | 8.3, 8.4 | Molti tipi di approvazione (piano, deroghe oltre il tetto, `comando`, presenza, non verificato, livello): rischio di approvazioni date senza leggere | `/tollgate:status` mostra gli atti in sospeso con il motivo e il costo dichiarato. Nessuna approvazione cumulativa |
| B-04 | 6 chi arriva dopo | Rilevante | [RAGIONATO] | 2, 15 | «Intervallo di versioni di Superpowers» senza valori | `>=6.4.1 <7.0.0`; un cambio di versione maggiore va verificato a mano sul formato del registro |
| B-05 | 7 lo scettico | Minore | [RAGIONATO] | 10.2 | Le colonne `lease_*` non servono al nucleo: le due sessioni si rilevano dagli eventi | Tenute come aggancio deciso per C (`COSA-TENERE.md`), segnate «non usate nel nucleo» |
| B-06 | 8 caso limite | Rilevante | [RAGIONATO] | 6.1, 12 | Repo senza remote GitHub, `gh` non autenticato, repo senza commit, ramo base assente, issue chiusa: comportamento non definito | `start` si rifiuta con un messaggio chiaro; per un'issue chiusa avvisa e chiede conferma. La v1 richiede un remote GitHub |
| B-07 | 8 caso limite | Rilevante | [RAGIONATO] | 8.2 | Un file di test **rinominato** risulta «cancellato» | Diff con rilevamento delle rinomine (`-M`): una rinomina non è una cancellazione e il conteggio per nome segue il test |
| B-08 | 8 caso limite | Rilevante | [RAGIONATO] | 6.3, 7.2 | La guardia del contesto scatta durante `finish` e nega i subagenti di revisione: `finish` resta a metà | `finish` riprende dal punto registrato nel DB dopo `/clear` (check fatto, giro di revisione N) |
| B-09 | 8 caso limite | Minore | [RAGIONATO] | 2 | Sistemi supportati non dichiarati (il wrapper è uno script shell) | Linux e macOS; Windows fuori dalla v1 |
| B-10 | 9 chi integra | Rilevante | [RAGIONATO] | 1.1, 11 | B deve aggiungere comandi di gate, checklist e specialisti per profilo, ma il nucleo non definisce il punto di estensione: B dovrebbe toccare `finish` | Contratto minimo di un profilo: `[profiles.<nome>]` con `paths`, `gate` (comandi), `checklist` (file per il revisore), `specialists`. Nel nucleo esiste solo `base`, ma `finish` già itera sui profili attivi |
| B-11 | 9 chi integra | Rilevante | [RAGIONATO] | 9, 15 | «Codex come parere, se installato»: come si invoca non è scritto | Tramite `specialist-runner`, con il comando documentato di codex-plugin-cc; il meccanismo va verificato (sezione 15) |
| B-12 | 9 chi integra | Minore | [RAGIONATO] | 6.3 | La descrizione della PR è solo testo: C e la dashboard non la possono leggere | Un blocco JSON in un commento HTML nella descrizione della PR |
| B-13 | 10 chi esegue (sulla rev. 3) | **Grave** | [RAGIONATO] | 6.4, 7.4 | Il plugin è abilitato per tutti i progetti: le «regole valide ovunque» (merge e push negati) bloccherebbero `git push` anche nei repo che non usano tollgate o fuori dai rami `tg/*`. Inoltre fuori da un lavoro non c'è `work_base_sha` da cui leggere `tollgate.toml` | Senza `tollgate.toml` nel ramo base tollgate è **inerte**. In un repo con tollgate ma fuori dai rami `tg/*` valgono solo i comandi distruttivi e la protezione dei file di tollgate; la configurazione si legge dalla punta del ramo base. Push, merge e PR sono regolati solo per i rami `tg/*` e per i merge verso la base da un ramo `tg/*` |
| B-14 | 10 chi esegue | Minore | [RAGIONATO] | 8.1 | `test_related {files}`: quali file non è detto | I file del diff rispetto alla base del lavoro |
| B-15 | 10 chi attacca (sulla rev. 3) | Rilevante | [RAGIONATO] | 7.2, 8.4 | `docs/superpowers/**` sempre scrivibile in ogni fase: ci si può nascondere codice eseguibile importato da altri file | Sempre permessi solo i `.md` sotto `docs/superpowers/`; gli altri file lì valgono come codice |
| B-16 | 10 chi attacca | Rilevante | [RAGIONATO] | 7.2, 8.4 | `.superpowers/**` sempre scrivibile: se finisce in un commit nasconde codice | Scrivibile, ma un file sotto `.superpowers/` nel diff a `finish` è fuori scope |
| B-17 | 10 chi attacca | Rilevante | [RAGIONATO] | 11 | I lockfile sempre ammessi permettono di aggiungere una dipendenza senza toccare il manifest | Un lockfile è ammesso solo se il suo manifest è nello scope; altrimenti serve una deroga |


## Ciclo 11: seconda revisione avversariale (sulla revisione 3)

Il report è in `2026-10-08-revisione-avversariale-2-spec-nucleo.md` (W-1 … W-40: 10 bloccanti, 10 gravi, 16 rilevanti, 4 minori).

**Esito strutturale.** I bloccanti W-1, W-2, W-3, W-5, W-12, W-19 e W-20 hanno la stessa radice: un agente con Bash sulla stessa macchina può alterare tutto ciò che è locale. Correggerli uno per uno non converge. Ho portato la decisione all'utente, che ha scelto il **gate su GitHub** (`COSA-TENERE.md`, sezione 10). La revisione 5 della specifica:
- fa ricalcolare al gate i fatti in un ambiente pulito;
- dichiara i guardrail locali «best effort»;
- elenca i limiti residui nelle sezioni 1.2 e 17.

**Rilievi corretti nella revisione 5**, senza dipendere dalla decisione sul gate:
- W-4: scope senza glob e immutabile;
- W-6: marcatori e percorsi di test estesi; asserzioni contate escludendo i commenti; identificativi dei test della base controllati sulla testa;
- W-7: atti `finding` e `rounds`;
- W-8: atti `rebase` e `abandon`;
- W-9: esenzione solo per i `.md` sotto `docs/superpowers/`; `.superpowers/` ignorato da git;
- W-10: effetti esterni con un elenco predefinito ampio e gli script non tracciati, dichiarati come livello unico;
- W-11: `open-pr` solo dopo il tuo `/tollgate:finish` o un `approve pr`;
- W-13: deroghe `test` per identificativo e sempre in attesa;
- W-14: brief con codice di controllo e verifica delle letture;
- W-15: R4 ridimensionata;
- W-16: tabella completa dei sottocomandi e livello alzabile solo con un atto;
- W-17: `EnterWorktree`, ramo dal `file_path` e da `git -C`, `isolation: worktree` negato;
- W-18: configurazione fuori dai `tg/*` letta dal ramo predefinito di `origin`;
- W-21 … W-40: wrapper con on/off prima di `OFF`; guardia del contesto solo su `Agent`; report dell'avversario salvato dall'hook; cartelle di output; `SubagentStop` che esce con 0 in caso di errore; L0 misurato anche in byte; issue di un autore esterno portata in L2; Python ≥ 3.11; fase `bloccato`; scritture via Bash della sessione principale; criteri binari; dipendenze; effetti esterni con diniego più atto; tabella `acts`; glossario; formulazioni.

**Verificato in questo ciclo**:
- `pull_request_target` gira nel contesto del ramo predefinito (docs.github.com);
- in `dontAsk` le richieste di conferma vengono negate (code.claude.com/docs/en/permission-modes).


## Rilievi dei cicli 12-18 (sulla revisione 5, da correggere nella revisione 6)

| ID | Ciclo | Gravità | Stato | Sezione | Rilievo | Correzione prevista |
|---|---|---|---|---|---|---|
| C-01 | 12 chi esegue | Grave | [RAGIONATO] | 8.3, 9.2 | Le deroghe stanno nel ramo, ma lo stato «in attesa» o «approvata» vive negli atti locali: il gate non può distinguerle. 9.2 dice «bloccante per le modifiche senza deroga», quindi qualunque deroga scritta nel file sblocca il gate | Il gate tratta **ogni** deroga come dichiarata: non blocca, la elenca nella sezione «attenzione» con lo stato dichiarato. Bloccano solo le violazioni senza nessuna deroga |
| C-02 | 12 chi esegue | Rilevante | [RAGIONATO] | 7.2, 7.4, 8.3 | `.tollgate/waivers.toml` non è tra i file sempre permessi né tra quelli protetti: lo scope lo bloccherebbe, oppure l'agente lo modifica a mano saltando la CLI | È sempre ammesso nello scope, scrivibile solo da `tollgate waiver add` (negato a Edit e Write) |
| C-03 | 12 chi esegue | **Bloccante** | [RAGIONATO] | 9.2, 9.4 | Gli identificativi dei test della base, se messi in cache, si possono avvelenare da una PR (la cache creata da una PR si legge nelle sue esecuzioni successive). Se invece si calcolano nello stesso job **dopo** aver eseguito il codice della PR, quel codice li può alterare | Niente cache. Nel job del gate: (1) checkout della base, esecuzione e calcolo degli identificativi **prima** di qualunque codice della PR, con l'impronta salvata nell'output del passo; (2) checkout della testa ed esecuzione; (3) valutazione con il CLI ripreso dalla base in una cartella nuova, che confronta l'impronta. Il risultato dei test della testa resta prodotto da codice non fidato: limite dichiarato in 1.2 («codice che, eseguito dai test, ne falsifica l'esito»), visibile nel diff |
| C-04 | 12 chi esegue | Rilevante | [RAGIONATO] | 9.2 | «Scope: bloccante, salvo L0» non dice cosa succede se non ci sono piani e il diff supera le soglie di L0 | Senza piano e oltre le soglie di L0 → bloccante |
| C-05 | 12 chi esegue | **Grave** | [RAGIONATO] | 9.2, 9.3 | Con i controlli obbligatori su tutte le PR, una PR fatta a mano da un ramo che non è `tg/*` non ha piani: scope e livello la bloccano. L'utente non potrebbe più fare PR normali | Per i rami che non sono `tg/*` il gate esegue solo i comandi del gate e i controlli di `guard`, come una CI normale |
| C-06 | 12 chi esegue | Rilevante | [RAGIONATO] | 6.3 | La copia locale del gate richiede l'esecuzione dei test della base: lenta | In locale `base_test_ids` è spento per impostazione predefinita; lo fa il gate |
| C-07 | 14 caso limite | **Grave** | [RAGIONATO] | 9.2, 11.2 | Ogni PR che cambia `tollgate.toml`, i workflow o la copia del CLI fa fallire `guard`: dopo l'installazione l'utente non può più aggiornare la configurazione né la versione del CLI, perché la protezione del ramo vieta il push diretto | Un percorso dedicato: rami `tollgate-config/*` con PR che contengono **solo** file di tollgate. `guard` li accetta e il riepilogo lo dice in evidenza; il merge resta tuo |
| C-08 | 14 caso limite | Rilevante | [RAGIONATO] | 9, 13 | Progetti i cui test richiedono servizi (DB locale, Supabase): senza servizi configurati nel workflow il gate è sempre rosso e nessuna PR si può unire | `/tollgate:init` chiede quali servizi servono e li mette nella proposta del workflow. Se il gate non può girare in CI, `start` lo segnala; la scelta di togliere l'obbligo resta tua |
| C-09 | 15 chi paga | Minore | [RAGIONATO] | 9.4 | Senza cache, ogni PR prepara l'ambiente ed esegue la suite due volte | Dichiarato; `base_test_ids` si può spegnere |
| C-10 | 18 chi arriva dopo | Minore | [RAGIONATO] | 8.4 | Il titolo «Il livello degli atti nel gate» non dice cosa contiene | «Gli atti nel gate» |

Cicli 16 (chi integra) e 17 (lo scettico): **vuoti**.
- **Chi integra, controlli fatti:**
  - C legge il JSON nella PR e il *job summary*;
  - D ha il repo di prova del gate e `TOLLGATE_STATE`;
  - B ha `[profiles.*].gate` eseguito dal gate.
  - Scartati: «il gate non conosce i profili» (falso, 9.2 usa i `gate` dei profili attivi); «la dashboard non ha dati» (ha `events`); «Codex senza contratto» (passa da `specialist-runner` e dal verificatore).
- **Lo scettico, controlli fatti:**
  - `finish check` locale duplicato: serve come riscontro rapido, scartato;
  - `reviewer_reads_check` complesso: si può spegnere, scartato;
  - tabella `acts` contro `approvals`: sostituita, scartato;
  - `slices` necessaria a `start`, scartato.


## Ciclo 19: terza revisione avversariale (sulla revisione 5)

Il report è in `2026-10-08-revisione-avversariale-3-spec-nucleo.md` (X-1 … X-27: 4 bloccanti, 8 gravi, 13 rilevanti, 2 minori). Tutti i rilievi, insieme a C-01 … C-10, sono corretti nella **revisione 6**.

- **X-1**: controllo omonimo creato da un workflow nuovo. Corretto con `guard` su tutti i workflow e la sorgente dei controlli fissata su GitHub Actions.
- **X-2 e X-3**: deroghe e scope scritti dall'agente. Il gate li tratta come dichiarati e li verifica solo per coerenza; il controllo `attenzione` diventa rosso; il limite è dichiarato in 1.2.
- **X-4**: codice della PR nello stesso job della valutazione. Il gate è ora diviso in tre workflow: `run` senza permessi, `verdict` fidato che legge gli artefatti come dati, identificativi della base calcolati da codice e dipendenze della base. Il limite residuo (report JUnit falsificato dal codice della PR) è dichiarato.
- **X-5 … X-11**:
  - 1.1 corretta;
  - commento pubblicato dal job fidato;
  - PR da rami che non sono `tg/*`;
  - percorso `tollgate-config/*`;
  - esenzioni dallo scope al commit e nel gate;
  - transizione `pr_aperta → esecuzione` con `open-pr --update`;
  - gate completo quando non ci sono test collegati, più `allow_no_tests`.
- **X-12 … X-27**:
  - cache dal ramo predefinito (`tollgate-base`);
  - `guard` senza checkout della PR;
  - confronto per contenuto con la punta attuale;
  - protezione del ramo completa;
  - `gh api` con scrittura negato ovunque nei repo attivi;
  - L2 controllato tramite gli artefatti committati;
  - marcatori per linguaggio;
  - giri contati dai commit;
  - `resolve` che concede un giro;
  - `WorktreeCreate`;
  - criteri 19-23;
  - `/tollgate:finish` legato allo SHA;
  - riapertura nel worktree come strada predefinita;
  - numerazione.

**Verificato in questo ciclo**: `workflow_run` usa la definizione del ramo predefinito, ha token con permessi di scrittura e può scaricare gli artefatti dell'esecuzione che l'ha avviato (docs.github.com, events-that-trigger-workflows).

**Matrice.** La revisione 6 cambia di nuovo le sezioni 6.3, 8 e 9: i punti di vista che avevano già un ciclo vuoto (chi usa, chi integra, lo scettico) lo avevano sulla revisione 5, e per le sezioni riscritte va ripetuto.


## Ciclo 20: quarta revisione avversariale (sulla revisione 6)

Il report è in `2026-10-08-revisione-avversariale-4-spec-nucleo.md` (Y-1 … Y-22: 4 bloccanti, 6 gravi, 10 rilevanti, 2 minori).

- **Decisione dell'utente su Y-1** (stati falsificati da workflow aggiunti nella PR): la garanzia della v1 copre scorciatoie e manomissioni locali. Il sabotaggio deliberato della CI è un limite dichiarato (1.2); la modalità rinforzata con GitHub App viene dopo la v1.
- Tutti gli altri rilievi sono corretti nella **revisione 7**:
  - Y-2: diff calcolato da `verdict`;
  - Y-3: `tollgate-config/*` esente da test-guard e scope;
  - Y-4: `verdict` solo per le PR verso il ramo predefinito;
  - Y-5: convalida di esecuzione, SHA e ramo;
  - Y-6: più di 2 deroghe `scope` in `attenzione`;
  - Y-8: chiavi che allentano il gate e impronta del CLI;
  - Y-9: procedura d'emergenza;
  - Y-10: limite dichiarato;
  - Y-11 … Y-22.
- **Revisione 8**: aggiunto l'audit della spec al flusso L2 (decisione dell'utente).

**Andamento dei bloccanti nelle revisioni avversariali**: 7 → 10 → 4 → 4. Gli ultimi otto sono tutti nel gate su GitHub, la parte nuova.


## Ciclo 21: quinta revisione avversariale (sulla revisione 8)

Il report è in `2026-10-08-revisione-avversariale-5-spec-nucleo.md` (Z-1 … Z-30: **1 bloccante**, 9 gravi, 15 rilevanti, 5 minori). È una revisione di convergenza sull'intero documento. Tutti i rilievi sono corretti nella **revisione 9**:
- Z-1: transizione `revisione → esecuzione`;
- Z-2 e Z-3: fasi per livello;
- Z-4: condizione «Fette previste»;
- Z-5: meccanica dell'audit della spec;
- Z-6: l'agente non prepara le PR di configurazione;
- Z-7: sorgente fissata «se possibile»;
- Z-8: tolto `WorktreeCreate`;
- Z-9: wrapper inerte nei repo non attivi;
- Z-10: report committati con spec e piano;
- Z-11 … Z-30: atti, job della base senza permessi, stato in attesa, `verification_globs` come `attenzione`, `gh api`, `abandon`, freschezza della configurazione, criteri 24-29, redazionali.

**Andamento dei bloccanti**: 7 → 10 → 4 → 4 → **1**. L'ultimo bloccante è un buco di flusso, non una garanzia aggirabile. Le revisioni avversariali convergono.

## Fatti verificati

| Fatto | Fonte | Data |
|---|---|---|
| I piani di Superpowers si salvano in `docs/superpowers/plans/YYYY-MM-DD-<nome>.md` | `superpowers/6.4.1/skills/writing-plans/SKILL.md:18` | 08/10/2026 |
| Gli stati dell'implementatore sono DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | `subagent-driven-development/SKILL.md:290-296` | 08/10/2026 |
| Tetto dei giri di correzione di Superpowers: 5 (`fix round <R>/5`) | `subagent-driven-development/SKILL.md:406` | 08/10/2026 |
| «Never dispatch multiple implementation subagents in parallel» è solo nel prompt | `subagent-driven-development/SKILL.md:282` | 08/10/2026 |
| subagent-driven-development verifica o crea il worktree con using-git-worktrees | `subagent-driven-development/SKILL.md:125-128` | 08/10/2026 |
| La chiusura del ramo offre merge locale, PR, «tieni» o scarto | `finishing-a-development-branch/SKILL.md:55-64` | 08/10/2026 |
| `pr-review-toolkit`: licenza Apache 2.0, agenti `pr-test-analyzer` e `silent-failure-hunter` | `pr-review-toolkit/fbe07fb6ce7d/LICENSE`, `agents/` | 08/10/2026 |
| `SubagentStop` riceve `agent_type`, `last_assistant_message` e `stop_hook_active`; `block` tiene in vita il subagente | code.claude.com/docs/en/hooks.md (verifica del 08/10, `COSA-TENERE.md`) | 08/10/2026 |
| Gli agenti dei plugin ignorano `hooks` nel frontmatter | code.claude.com/docs/en/sub-agents.md | 08/10/2026 |
| Solo l'uscita 2 blocca; con 1, crash o timeout l'azione prosegue; timeout predefinito 600 s | code.claude.com/docs/en/hooks.md (WebFetch, caratteri 0-100.000) | 08/10/2026 |
| Il comando `/skill` digitato dall'utente fa scattare `UserPromptExpansion` con `prompt` e `command_name` | hooks.md (caratteri 100.000-200.000) | 08/10/2026 |
| `PostToolUse` con `block` aggiunge il motivo, non annulla | hooks.md | 08/10/2026 |
| Strumento dei subagenti: `Agent`; `agent_type` dei plugin: `plugin:nome` | hooks.md | 08/10/2026 |
| Il `settings.json` di un plugin applica solo `agent` e `subagentStatusLine` | code.claude.com/docs/en/plugins/components.md:590, 901 | 08/10/2026 |

## Scartati

| ID | Sospetto | Perché non regge |
|---|---|---|
| A-23 | La deroga di scope si registra con un comando Bash che tocca il DB, e il divieto «comandi che toccano il DB» la impedirebbe | Il divieto riguarda l'accesso diretto (sqlite3, scrittura sul file); `tollgate waiver add` è nella lista dei sottocomandi permessi all'agente |
| A-24 | Il DB per macchina impedirebbe a C la presa in carico da più macchine | In C la fonte condivisa è GitHub; il lease locale serve solo alle sessioni della stessa macchina |
| S-1 | Le ricevute si possono falsificare scrivendo nel DB | Al gate `finish check` riesegue tutto e usa solo la sua ricevuta; durante il lavoro una falsificazione è possibile solo aggirando l'hook Bash e la prova di presenza la renderebbe visibile come commit fuori controllo |
| S-2 | SQLite in modalità WAL dentro MEGA si degrada | Il DB sta in `CLAUDE_PLUGIN_DATA` sotto `~/.claude`, e MEGA non è sincronizzato (utente, 08/10) |
| S-3 | Il limite di 10.000 caratteri di `SessionStart` è troppo stretto | Le righe di stato sono 5-10; il limite è verificato sulla documentazione |

## Registro dei cicli

| Ciclo | Punto di vista | Lenti | Esito |
|---|---|---|---|
| 1 | Chi esegue | L1-L10 | A-01, A-06, A-07, A-08, A-09, A-10, A-11, A-12, A-14, A-15, A-16, A-17, A-22 |
| 2 | Chi attacca | L1-L10 | A-02, A-03, A-04, A-05, A-19, A-25 |
| 3 | Chi usa | L1-L10 (in particolare L9: errori, concorrenza, annullamento) | A-13, A-18, A-20, A-21 |

| 4 | Chi attacca (revisione avversariale a contesto pulito) | L1-L10 | V-1 … V-36 (vedi sopra) |

| 5 | Chi paga | L1-L10 | B-01, B-02, B-03 |
| 6 | Chi arriva dopo | L1-L10 | B-04 |
| 7 | Lo scettico | L1-L10 | B-05 (minore). Scartati: `slices` decorativa (no: serve a `start`), `report` superfluo (no: senza conteggio non si vede la ricevuta vuota), eval a 3 esecuzioni troppo costosi (no: 6 casi × 3) |
| 8 | Il caso limite | L9 in particolare | B-06, B-07, B-08, B-09 |
| 9 | Chi integra | L2, L7 | B-10, B-11, B-12 |
| 10 | Chi esegue e chi attacca, sulla rev. 3 | L1-L10 | B-13 … B-17 |

Revisione 3 della specifica scritta. **Prossimo passo** (dopo la seconda revisione avversariale, in corso sulla rev. 3): revisione 4, poi cicli 5 e successivi con i punti di vista mai applicati (chi paga, chi arriva dopo, lo scettico, il caso limite, chi integra), poi chi esegue, chi attacca e chi usa sulla revisione 3, fino a due cicli vuoti per ciascuno.


## Cicli 22-29: otto auditor indipendenti per punto di vista (sulla revisione 9)

Ognuno a contesto pulito, con le lenti L1-L10 da un solo punto di vista.

| Ciclo | Punto di vista | Bloccanti | Gravi | Rilevanti | Rilievi principali |
|---|---|---|---|---|---|
| 22 | Chi esegue | 0 | 2 | 8 | Il gate non sa che la PR è L2; fette non implementabili; formati non definiti (intestazioni, JSON, dialetto dei glob) |
| 23 | Chi usa | 0 | 2 | 6 | Subagente «running» dopo un crash che blocca per sempre; nessuna corsia per l'hotfix; troppi passi dopo `strict` |
| 24 | Chi attacca | **1** | 2 | 3 | **Regole legate al nome del ramo, che sceglie l'agente**; implementatore riconosciuto solo come `general-purpose`; verificatore alimentato dal coordinatore |
| 25 | Chi paga | 0 | 0 | 7 | Nessun modello di costo; L2 con 2 fette = 50-70 subagenti; L1 obbligato a subagent-driven-development |
| 26 | Chi arriva dopo | 0 | 1 | 8 | Condizione dell'audit a lenti scritta in tre modi; glossario incompleto; codici R e H; identificatori in italiano |
| 27 | Lo scettico | 0 | 0 | 8 | Proposte di rinvio: audit a lenti, fette, verbi Bash, ID della base, letture, guardia del contesto, specialisti |
| 28 | Il caso limite | 0 | 3 | 5 | DB perso senza ricostruzione; glob non ancorati; dieci fette |
| 29 | Chi integra | 0 | 4 | 5 | Profili senza comandi propri e senza regola di attivazione; rami delle fette; atti legati a Claude Code |

**Decisioni dell'utente sul perimetro**, dopo i cicli 25 e 27:
- fette e piano principale rinviati a C (un'issue è un lavoro ed è una PR);
- audit a lenti come già deciso;
- rinviati a dopo la v1: specialisti L2, Codex e controllo delle letture.

Restano guardia del contesto e identificativi della base.

## Ciclo 30: revisione 10 e chiusura

La revisione 10 è una **riscrittura** che integra tutti i rilievi dei cicli 22-29 e le decisioni sul perimetro. La sezione 20 della specifica ne elenca il contenuto.

## Esito

**Audit SOSPESO, non chiuso.** È stato raggiunto il tetto di 30 cicli.

**Matrice finale.** Tutti i punti di vista hanno ancora il contatore dei cicli vuoti a 0 sulla revisione 10. Ognuno ha prodotto rilievi nel ciclo 22-29, e la revisione 10 li corregge ma non è ancora stata riauditata.

| Punto di vista | Ultimo ciclo | Ultimo esito | Contatore vuoti |
|---|---|---|---|
| Chi esegue | 22 | 10 rilievi | 0 |
| Chi usa | 23 | 8 rilievi | 0 |
| Chi attacca | 24 | 6 rilievi (1 bloccante) | 0 |
| Chi paga | 25 | 7 rilievi | 0 |
| Chi arriva dopo | 26 | 9 rilievi | 0 |
| Lo scettico | 27 | 8 rilievi | 0 |
| Il caso limite | 28 | 8 rilievi | 0 |
| Chi integra | 29 | 9 rilievi | 0 |

**Andamento.**
- Bloccanti nelle revisioni avversariali: 7 → 10 → 4 → 4 → 1.
- Nei cicli per punto di vista: 1 bloccante, 14 gravi.
- Le garanzie dichiarate reggono sempre di più, e i rilievi residui riguardano soprattutto completezza e formati.

**Punto di ripresa.** Se si decide di proseguire oltre il tetto:
1. rilanciare gli otto auditor sulla revisione 10 con `docs/audit/prompt-ciclo-punto-di-vista.txt`;
2. correggere;
3. ripetere solo i punti di vista che trovano qualcosa, fino a due cicli vuoti per ciascuno.

**Decisione che spetta all'utente**: proseguire l'audit oltre il tetto, oppure passare al piano accettando la spec come «sospesa».

## Prosecuzione oltre il tetto (decisione dell'utente, 08/10/2026)

L'utente ha scelto di proseguire con un giro di verifica sulla revisione 10. **Cicli 31-38 conclusi**: un auditor per punto di vista, in parallelo, con `docs/audit/prompt-ciclo-punto-di-vista.txt`.
- 31 Chi esegue, 32 Chi usa, 33 Chi attacca, 34 Chi paga, 35 Chi arriva dopo, 36 Lo scettico, 37 Il caso limite, 38 Chi integra.
- Se si interrompono senza risultati, vanno rilanciati tutti e otto.

### Esito dei cicli 31-38 (revisione 10)

| Ciclo | Punto di vista | Bloccanti | Gravi | Rilevanti |
|---|---|---|---|---|
| 31 | Chi esegue | 0 | 3 | 2 |
| 32 | Chi usa | 0 | 1 | 3 |
| 33 | Chi attacca | 0 | 4 | 2 |
| 34 | Chi paga | 0 | 1 | 4 |
| 35 | Chi arriva dopo | 0 | 3 | 3 |
| 36 | Lo scettico | 0 | 1 | 3 |
| 37 | Il caso limite | 0 | 4 | 2 |
| 38 | Chi integra | 0 | 4 | 3 |
| | **Totale** | **0** | **21** | **22** |

Rispetto ai cicli 22-29 (65 rilievi, 1 bloccante, 14 gravi): i bloccanti scendono a zero e il totale cala, ma i gravi non convergono. Nessun punto di vista ha prodotto un ciclo vuoto.

**Temi gravi dopo la deduplicazione** (tra parentesi i cicli che li hanno trovati):
- G1 La sessione che lavora nel worktree non è legata al lavoro: con un `cd` fuori le regole cadono (31, 33).
- G2 Regole di scrittura assenti nelle fasi `review` e `pr_open` (31, 33, 35).
- G3 Gli script di Superpowers (`sdd-workspace`, `task-brief`, `review-package`) diventano effetti esterni e bloccano SDD (31, 38) [VERIFICATO].
- G4 L'audit a lenti non è una condizione di `approve spec`; «sospeso» ambiguo (35, 36).
- G5 Repo privati con GitHub Free: la protezione del ramo non c'è, quindi il gate autorevole cade (34, 37) [VERIFICATO]. **Decisione dell'utente.**
- G6 `sync`: conflitto di rebase non gestito, ed è eseguito dall'hook con scadenza di 20 s e senza rete (32, 37).
- G7 `SessionStart` segna `interrupted` i subagenti di sessioni ancora vive (37).
- G8 `allow_no_tests`: nessuna ricevuta `green`, veti ripetuti; `unverified` non classificato nel gate (37).
- G9 `|| true` nel comando di check: il JUnit con fallimenti viene ignorato dal gate (33).
- G10 Le deroghe passano al ramo predefinito e valgono per le PR successive; gli identificativi collidono (33).
- G11 6.6 e 7.4 danno regole diverse per «repo attivo senza lavoro» (35).
- G12 Il task del subagente e `fix_rounds` non hanno fonte; `SubagentStart` non riceve il prompt (36, 38) [VERIFICATO].
- G13 In auto mode il report del subagente arriva con `SubagentHandback`, non nell'ultimo messaggio (38) [da riverificare].
- G14 Il contratto delle fette contraddice il rinvio a C (38).

Rilevanti: ripristino del DB guasto; ripresa senza rete bloccata dai passi 0-1; uscita d'emergenza documentata solo via `/tollgate:off`; da `plan` ad `approval` in L2; quale file è il piano; atti in sospeso senza colonna; R13 con due significati; base di conteggio dei cicli; `attention` rosso come norma; `flaky` indefinito; costo in minuti di Actions; doppia revisione finale con SDD; modello degli agenti e costo minimo dell'audit; `guard` senza `issues: write`; repo senza `origin/HEAD`; crash tra riga e worktree; DONE senza commit; cambio di ramo riconosciuto per nome del comando; campi mancanti nel JSON della PR; schema degli eventi; collocazione di GitHub Projects.

Le note complete dei cicli sono state riassunte qui; l'output integrale degli auditor non è conservato nel repo.

**Scartato dopo verifica:** il rilievo del ciclo 38 sulla collocazione di GitHub Projects. `docs/COSA-TENERE.md:27` assegna kanban e ponte GitHub a C, come già scritto in 1.3.

**Verifiche alla fonte** (sezione 16 della spec): protezione del ramo solo con Pro o Team sui privati; nessun token con scoping per ramo; `SubagentHandback` solo in auto mode; `SubagentStart` senza prompt; revisione finale di SDD riconoscibile dal riferimento a `code-reviewer.md`.

**Decisioni dell'utente:** repo privati senza Pro in **modalità `detect`** (rilevazione con `tollgate-sentinel`, non impedimento); dopo la revisione 11, **altro giro completo** degli otto auditor.

**Revisione 11** (commit 30969b5): 110 correzioni puntuali, nessuna riscrittura. Contenuto nella sezione 20 della spec.

### Cicli 39-46 (revisione 11): in corso

39 Chi esegue, 40 Chi usa, 41 Chi attacca, 42 Chi paga, 43 Chi arriva dopo, 44 Lo scettico, 45 Il caso limite, 46 Chi integra. Se si interrompono senza risultati, vanno rilanciati tutti e otto.

## Nota storica: interruzione per limite di utilizzo (08/10/2026)

**Stato: audit IN CORSO, non chiuso.**
- 21 cicli fatti su un tetto di 30.
- Specifica alla revisione 9.
- I cicli 22-29 (un auditor per punto di vista sulla revisione 9) erano partiti e sono stati **fermati senza risultati** per il limite di utilizzo.

**Per riprendere:**
1. Rilanciare gli 8 auditor, uno per punto di vista, con il prompt in `docs/audit/prompt-ciclo-punto-di-vista.txt`. Al posto di {VP} va il punto di vista; le formulazioni sono nella skill prd-audit, sezione «Cambiare punto di vista».
2. Correggere la spec con quello che trovano.
3. Ciclo 30: chiusura. Con il tetto a 30, i due cicli vuoti per ogni punto di vista non sono raggiungibili, quindi l'esito atteso è «SOSPESO» con la matrice, a meno che tu non decida di continuare oltre il tetto.
