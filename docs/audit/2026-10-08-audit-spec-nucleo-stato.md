# Stato dell'audit: specifica del nucleo di tollgate

Documento auditato: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`.
Metodo: skill `prd-audit` (lenti L1-L10, otto punti di vista, due cicli vuoti per ciascuno, tetto di 30 cicli). In parallelo: revisione avversariale a contesto pulito, senza le motivazioni dell'autore (`2026-10-08-revisione-avversariale-spec-nucleo.md`).
Giudice esterno (`/goal`): **non usato**, per scelta dell'utente l'08/10/2026. La chiusura la decide chi conduce l'audit.
Stato: **in corso**.

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

Le sezioni sono quelle della revisione 2: le correzioni dei cicli 1-3 vanno riauditate.

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

## Matrice dei punti di vista

| Punto di vista | Cicli | Ultimo esito | Contatore vuoti |
|---|---|---|---|
| Chi esegue | 1 | 13 rilievi → **da ripetere** | 0 |
| Chi attacca | 2 | 6 rilievi → **da ripetere** | 0 |
| Chi usa | 3 | 4 rilievi → **da ripetere** | 0 |
| Chi paga | — | mai applicato | 0 |
| Chi arriva dopo | — | mai applicato | 0 |
| Lo scettico | — | mai applicato | 0 |
| Il caso limite | — | mai applicato | 0 |
| Chi integra | — | mai applicato | 0 |

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

Correzioni applicate nella revisione 2 della specifica. **Prossimo passo**: integrare la revisione avversariale, poi i cicli con i punti di vista mai applicati e la ripetizione di chi esegue, chi attacca e chi usa sulle correzioni.
