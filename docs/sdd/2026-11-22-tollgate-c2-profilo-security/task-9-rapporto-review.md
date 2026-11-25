# Task 9, Step 2-3: revisione del rapporto della prova (Fable)

Oggetto: commit `d9639cc`, `docs/verifiche/2026-11-22-c2-prova-flusso.md` (215 righe) e `docs/verifiche/evidenze/c2/flusso/` (68 file).
Metodo: sola lettura. Rapporto, agenti e skill letti con `git show d9639cc:<percorso>`; evidenze lette da una copia `git archive d9639cc` in `/tmp/tollgate-rev-XXXXXX` (cancellata alla fine) con script Python propri (`python3 -I -B`) e `/usr/bin/grep -ra`. Nessun `claude`, nessuna rete, nessun subagente, nessun test lanciato (il controllo sui risultati web l'ho rifatto con uno script mio).

## Aderenza al brief

- ✅ **Riga `Esito: riuscita` su una riga a sé** (`rapporto:3`) e «non composita» (`rapporto:7`). Controllo: `exit-codes.txt` (sei righe «tentativo 1, uscita 0»), `esito.txt` dei sei passi (`tentativo: 1`, `uscita: 0`), una sola cartella `tentativo-1` per passo, nessuna cartella `libero-*`, `is_error: false` nei sei `result`.
- ✅ **Passi, durate, turni, costi** (`rapporto:20-28`, `130-138`). Controllo sui sei `result`: turni 33/2/36/3/15/9; durate 868.598/18.750/595.419/13.460/363.134/128.318 ms; costi 7,3045/0,3767/5,3518/0,3730/3,6721/2,4745, totale 19,5526; per modello opus 6,9758, Fable 12,5525, haiku 0,0244 (0,0192 nel passo 1 e 0,0052 nel passo 5). Avversari 5,5701 + 3,9606 = 9,53; esecuzione e revisione finale 6,14. Tutto come nel rapporto.
- ✅ **Agenti e modelli** (`rapporto:50-59`). Controllo: 22 `tool_use` di `Agent` (9 `spec-adversary`, 6 `plan-adversary`, 2+2 nel passo 5, 3 nel passo 6), nessuno con il parametro `model`; il campo `model` dei messaggi dei subagenti è `claude-fable-5-2` per avversari, revisori, specialista e verificatore e `claude-opus-5-5` per i due implementatori e per la sessione; nessun messaggio su haiku. `events.jsonl`: 22 `subagent_start`, 22 `cost` con `by_model` coerente, 15 `spec_audit_round` (9 `spec-adversarial`, 6 `plan-adversarial`).
- ✅ **Due task a `implementer-security`/`reviewer-security`** (`tipi-task.txt`), tutti e due `approved` al primo giro (blocchi JSON dei verdetti, righe 698 e 1184 di `passo5`), ricevute `verify` green con 9 e 15 test (`events.jsonl`, seq 101 e 115), commit `1aa13c7` e `fc2a3f5` (`git-log-worktree.txt`).
- ✅ **Id `R-SECURITY-…`** (`rapporto:87`, `112`, `186-187`). Controllo sui testi dei verdetti: revisore del task 1 → 05, 07, 08, 10, 12, 03 sul diff e 01, 16, 17, 15 sul report; revisore del task 2 → 03, 04, 05, 08, 10, 12 sul diff e 01, 16, 17 sul report; specialista → 03, 04, 05, 07, 08, 10, 12 rispettate, 06, 09, 11, 13, 14 non applicabili, 05 nel rilievo `f-1-3`, nessuna regola sul report. Nelle prime due differenze con il ledger ha ragione il rapporto.
- ✅ **Specialista, verdetti, quattro minori, verificatore** (`rapporto:84-105`). Controllo: i due verdetti finali hanno `outcome: ok`, stesso `sha` e `code` (`da01ab95`); `f-1-1`…`f-1-4` con confidenza 0,9/0,7/0,6/0,7 e `verification: rejected` in `events.jsonl` (seq 141-144); `review_cycle` numero 1, `ok`, `findings_confirmed` 0. Il rapporto dice con chiarezza che `review_cycles.reviewers` e `reported` vengono dalla copia dello stato letta dal controller e non sono nelle evidenze (`rapporto:84`): giusto così.
- ✅ **Brief della revisione finale e voce `specialists`** (`rapporto:85`, `88`). Controllo: righe 65 e 74 di `passo6` contengono «Lista di controllo dell'area» con la `checklist`; riga 24 ha due `[dopo la revisione]` e sei `[sì]`, riga 309 otto `[sì]`, nessun `[no]`; `fakegh.log` ha `pr create` con `--body-file`, senza il corpo. Anche qui ha ragione il rapporto e non il ledger.
- ✅ **Riga `Sicurezza:`** (`rapporto:118-122`). Il testo dei due report (righe 639 e 1127 di `passo5`, campo `done`) è riassunto fedelmente, senza aggiunte.
- ✅ **Titolo nelle trascrizioni** (`rapporto:116`). `trascrizioni.txt`: «# Regole security (versione 1)» con `isMeta: sì` in cinque subagenti; l'attribuzione degli id agli agenti torna con gli eventi `subagent_start` (seq 99, 106, 113, 120, 131); `final-reviewer` e `finding-verifier` solo le regole di base; sessione 3 «nessun titolo»; sessione 1 «nessuna trascrizione di subagente».
- ✅ **Avversari** (`rapporto:67-80`). Campione: giro 1 della spec con 3 `major`, 3 `moderate`, 1 `minor` e la citazione «accesso negato provato da un test» (`tollgate.toml:26`); giro 1 del piano «2 dei 13 must-have»; nessun `R-SECURITY-` nei 15 report; i commit per giro in `git-log-worktree.txt`.
- ✅ **Strumenti, comandi, WebFetch** (`rapporto:148-162`). I totali degli strumenti ricalcolati dagli stream coincidono tutti (Agent 22, Bash 84 (39), Edit 41 (28), Glob 26, Grep 2, Read 184 (182), Skill 4 (2), WebFetch 9, Write 7 (3)); nessun programma vietato a confine di parola in `comandi-modello.txt`; `comandi-rischiosi.txt` vuoto; 9 `WebFetch` (stdtypes 4, hmac 2, os 1 nel passo 1; hmac e stdtypes nel passo 5), tutti e 9 i `tool_result` sono il segnaposto (97-115 caratteri), nessun `WebSearch`. Nessuna pagina citata nel rapporto.
- ✅ **Limiti e scostamenti**: costo sopra la stima e perché, haiku, trascrizioni degli avversari della spec non trovate, altri plugin attivi, limiti di `limiti.txt`: detti.
- ✅ **Commit**: solo il rapporto e la cartella delle evidenze (69 file), oggetto e `Co-Authored-By` come da brief.
- ❌ **Segnali «senza gonfiare»**: una frase attribuisce a `rules-security` precaricata ciò che chiede il testo dell'agente (rilievo I1).
- ⚠️ Non verificabili dalle evidenze: le variabili d'ambiente assenti e l'uscita di `prepara` (`rapporto:13`, `44`: vengono dal ledger, e il rapporto lo dice); «Test: 2 all'inizio» e le tre lunghezze degli hook (m3).

## Punti di forza

- Il rapporto segue le evidenze contro il ledger nei cinque punti in cui divergono, e in tutti e cinque le evidenze gli danno ragione.
- Dice da sé ciò che indebolisce la prova: il confronto a tempo costante non conta, i due segnali della decisione 20 stanno già nella spec, la `checklist` è nel `tollgate.toml` letto da avversari e implementatori (`lookups.txt`, letture 6 e 16: verificato), i suggerimenti del codice di partenza, `precarico.txt` che vale solo come indizio.
- `f-1-3` raccontato come limite del verificatore, non come successo.
- Ripulitura accurata: nessun dato che identifichi l'utente o la macchina (vedi sotto), JSON valido, `SESSIONE-N` coerenti tra stream ed eventi.

## Rilievi

### Critical
Nessuno.

### Important

**I1. `rapporto:111` (e di riflesso `:169`): il «segnale più pulito» è attribuito a `rules-security` precaricata con un fatto falso.**
Il rapporto scrive: «`agents/implementer-security.md` nomina solo gli id delle regole giudicate sul report, e che cosa dire lo dà il testo di `rules-security`, precaricato».
Evidenza contraria: `git show d9639cc:agents/implementer-security.md`, riga 51. Il corpo dell'agente, che è il suo prompt di sistema anche senza la skill, dice per esteso: «Scrivi nel report, nel campo `done`, ciò che serve: chi può arrivare al codice cambiato (un anonimo, un utente autenticato, un amministratore, un altro servizio), cosa può fare da lì e quale controllo lo ferma (o che da fuori non ci arriva nessuno), … il raggio d'azione del cambio (quali rotte e funzioni chiamano il codice cambiato, quali permessi e quali dati tocca, cosa succede se è sbagliato), e quale prova locale hai fatto con valori finti». I due report lo ricalcano quasi parola per parola («Chi arriva al codice cambiato: nessuno da fuori», «Raggio d'azione: …», «Se il codice fosse sbagliato…», «Prova locale: …»).
Perché conta: modello delle minacce e raggio d'azione nei report provano che il profilo manda il task all'agente dell'area e che l'agente fa ciò che il suo testo chiede; non provano il precaricamento della skill. La frase dà alle regole un effetto che le evidenze non dimostrano, proprio nel punto in cui il rapporto dichiara il segnale «più pulito».
Come correggere: in `:111` togliere la frase su `implementer-security.md` e dire che il contenuto lo chiede per esteso il testo dell'agente (riga 51), oltre a R-SECURITY-01 e R-SECURITY-16 nella skill e alla `checklist`; quindi il segnale è dell'agente dell'area, non del precaricamento. In `:169` (e dove serve in `:80`) la prova del precaricamento resta il titolo con `isMeta: sì` nelle cinque trascrizioni; come indizio forte restano gli id citati da revisori e specialista con il contenuto giusto (07 scadenza, 08 `compare_digest`, 10 segreti, 12 input): `reviewer-security.md:55` e `final-security.md:38` elencano solo i numeri, senza dire cosa chiede ogni regola (verificato), quindi l'abbinamento numero-contenuto viene dal testo della skill. Va segnalata la stessa cosa nella sezione «Differenze con il registro del controller» (il ledger, riga «Prova: segnali», lo conta tra i segnali delle regole).

### Minor

- **m1. `rapporto:112`**: «le dividono tra diff e report come dice la skill». La divisione è scritta, id per id, anche in `reviewer-security.md:55` e `final-security.md:38`: non prova la skill. Basta togliere «come dice la skill» o aggiungere «e il testo degli agenti». Nella stessa riga 08 (revisore del task 2) e 15 (revisore del task 1) sono citate come «non si applica»: dirlo.
- **m2. `rapporto:153`, `:175`, `:200`**: la skill di TDD è presentata come effetto della configurazione della macchina. La chiama `agents/implementer-security.md:57` («Invoca con lo strumento Skill `superpowers:test-driven-development`»): è un comportamento chiesto da tollgate, che riesce solo perché quel plugin è installato. Il limite vero da scrivere: il testo di una skill di terzi è entrato nel contesto dei due implementatori e non è nelle evidenze.
- **m3. Fatti senza fonte nelle evidenze**: «Test: 2 all'inizio» (`rapporto:63`: le ricevute in `events.jsonl` sono tre, con 9, 15 e 15 test) e le lunghezze «1.129, 3.604 e 10.170 caratteri» (`rapporto:162`: `togli-pagine.txt` ha solo «3 risultati sostituiti» per flusso, e le righe sono state tolte). Dire da dove vengono o toglierli.
- **m4. `rapporto:142` e `:166`**: il costo è spiegato con il numero dei giri, non con il perché. `events.jsonl` segna `outcome: empty` per i giri 4-9 della spec e 4-6 del piano; `audit prepare` rifiuta solo con blocker o major (riga 211 di `passo1`) e apre un giro nuovo a ogni spec cambiata. Sei giri della spec e tre del piano sono nati perché la sessione ha corretto note minori. È un dato utile per chi legge il costo.
- **m5. `rapporto:200` («Restano»)**: l'elenco non nomina due dati dell'account che restano negli stream: 15 righe `rate_limit_event` (percentuale d'uso della quota settimanale, orario di azzeramento, stato dei crediti extra) e 6 campi `credential_expires_at` nei `result`. Non identificano nessuno e B7 li ha già pubblicati (9 righe e 8 campi), ma vanno elencati; se il controller preferisce, si tolgono.
- **m6. `rapporto:105`**: «Lo specialista stesso lo dava come nota di rafforzamento». Lo specialista dà `f-1-3` come rilievo `minor` tra le «note, non chiedono modifiche»; «nota di rafforzamento» la usa per un altro punto (la lunghezza minima della chiave).
- **m7. Non detto**: il `finding-verifier`, che ha precaricate solo le regole di base, per giudicare `f-1-3` ha letto la regola dal file della skill (`sed -n 39,44p …/skills/rules-security/SKILL.md`, riga 264 di `passo6`, anche in `comandi-modello.txt`). Vale una riga accanto al limite del verificatore.
- **m8. Righe `init` ridotte**: la scelta di tenerle filtrate va bene (vedi sotto), ma la riga ora dice `plugins: [tollgate]` e `mcp_servers: []` senza segnalare da sé di essere stata ridotta; lo dice solo il rapporto (`:198`). Un campo in più nella riga (per esempio una nota «riga ridotta») la renderebbe leggibile anche da sola.

## Repo pubblico: cosa resta nelle evidenze e nel rapporto

Controllo con `/usr/bin/grep -ra` e script (nome utente e host da `id -un` e `hostname`):

| Tipo | Occorrenze |
|---|---|
| nome utente, host | 0 |
| `/home/` diverso da `/home/USER` | 0 (3 `/home/USER`) |
| nomi delle cartelle che contengono il repo, account git | 0 |
| forme di token (`sk-ant`, `ghp_`, `github_pat_`, `gho_`, `ghs_`, `xox`, `AKIA`, JWT) | 0 nelle evidenze; 1 riga nel rapporto, che elenca i prefissi cercati |
| id di sessione reali | 0: ogni `session_id` è `SESSIONE-1`…`SESSIONE-6`; i 7.146 UUID rimasti sono solo nei campi `uuid` (4.272) e `hook_id` (2.874) |
| e-mail | solo `noreply@anthropic.com` (63) e `prova@example.com` (3) |
| plugin, skill, server MCP, comandi o agenti di terzi nelle righe `init` | 0: plugin 1 (`tollgate`), server MCP 0, 23 skill, 23 comandi, 21 agenti, tutti `tollgate:` |
| blocchi di sistema iniettati con la configurazione dell'utente | 0 (gli 8 `system-reminder` sono l'avviso di Claude Code «file vuoto»); nessun `SessionStart` di terzi (restano 5 coppie, tutte di tollgate) |
| uscite di hook di terzi | solo `""`, `{}` o `allow`, senza nomi |
| nomi di terzi rimasti | `superpowers:test-driven-development` (6, tutte in `passo5`: nome, «Launching skill», `commandName`; nessun testo della skill), `context7:` (8, formato della nota di tollgate), `agent-skills` (2, fonti di `rules-security`), un nome d'autore dentro il testo della skill `spec-audit` di tollgate (2, già pubblico nel repo) |
| risultati di WebFetch/WebSearch diversi dal segnaposto | 0 su 9 |
| dati dell'account, non identificativi | 15 righe `rate_limit_event`, 6 `credential_expires_at` (m5) |

I due dubbi dell'implementatore:
1. **Righe `init` filtrate**: non mostrano più niente della configurazione privata. Restano versione, modello, modo dei permessi, strumenti e capacità di Claude Code, `apiKeySource: none`. Si possono tenere (m8 è una rifinitura).
2. **`superpowers:test-driven-development`**: non è un dato privato. È il nome di un plugin pubblico, scritto in `agents/implementer-security.md:57` che è già nel repo, e la chiamata è un comportamento chiesto da tollgate. Va tenuto; va corretta solo la frase del rapporto (m2).

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** numeri, fatti, verdetti e ripulitura reggono al controllo sulle evidenze, e il rapporto è onesto quasi ovunque; ma la frase di `rapporto:111` su `implementer-security.md` è smentita dal file e gonfia il segnale del precaricamento, che è il punto su cui la prova va letta con più cura. È una correzione di poche righe (I1), con cui conviene chiudere anche i minori m1-m7.
