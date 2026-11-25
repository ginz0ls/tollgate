# C2: prova reale L2 con il profilo security

Esito: riuscita

Data: 23 novembre 2026. Piano: C2 (profilo `security`), Task 9. Stesso schema della prova di B7: un lavoro di livello L2 portato fino alla revisione finale e alla PR (finta), eseguito con `claude -p` vero. Il profilo `security` è acceso da `init`, con le regole vere (`rules-security`, versione 1, approvata il 23/11) caricate dagli agenti dell'area e lo specialista finale `final-security`. Il lavoro è piccolo: la scadenza dei token firmati di un progetto di prova in sola libreria standard di Python, e la lettura di una nota riservata al suo proprietario. Due task, nessuna credenziale vera, nessun servizio, nessuna rete: il segreto è il valore finto `PROVA-123`, che i test mettono nella variabile `C2_PROVA_SECRET`.

L'esito non è composito: una sola esecuzione, un tentativo per passo, nessun modo `libero`, nessuna fermata, nessuna scelta dell'utente a metà, nessun difetto del prodotto. I due atti dell'utente (`approve spec 1`, `approve plan`) li ha dati il controller dopo il confronto con l'input, come in B7 (decisione 16).

- Versioni: Claude Code `2.1.330` (`registro-1/versione-claude.txt`). Sessione e implementatori su opus (`claude-opus-5-5`), avversari, revisori, specialista e verificatore su Fable (`claude-fable-5-2`), dai messaggi degli stream (vedi «Il lavoro in L2 e gli agenti lanciati»).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=security`, `B1_FLOW_RULES=vere` e `B1_FLOW_EVIDENCE=c2` (modi `controlla`, `prepara`, `passo1` ... `passo6`, `registra`). Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova in `/tmp/tollgate-b1/state`. Comandi esatti in `argv.txt` di ogni tentativo.
- Evidenze: `docs/verifiche/evidenze/c2/flusso/` (`validate/`, `passo1` ... `passo6/tentativo-1/`, `registro-1/`, `spec-diff.txt`, `piano-diff.txt`, `exit-codes.txt`). `controlla` e `prepara` non hanno una cartella: il loro esito sta nel registro del controller.
- Chi ha fatto cosa: la prova l'ha eseguita il controller (eccezione 2 delle istruzioni); questo rapporto la racconta partendo dalle evidenze e dal registro del controller. Dove i due non coincidono vale ciò che mostrano le evidenze (vedi «Differenze con il registro del controller»).
- Prima di partire, nell'ambiente erano assenti `ANTHROPIC_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN`, `JWT_SECRET`, `SESSION_SECRET`, `AUTH_SECRET`, `NEXTAUTH_SECRET`, `DATABASE_URL`, `CLAUDE_CODE_SUBAGENT_MODEL` e `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (controllata solo la presenza, mai il valore). Il modo `controlla` ha dato ok: `--model opus` in tutti i passi; `--disallowedTools` nega `node`, `npm`, `npx`, `pnpm`, `yarn`, `bun`, `bunx`, `deno`, `supabase`, `psql`, `docker`, `wrangler`, `vercel`, `openssl` e i caricatori di segreti (`dotenv`, `dotenvx`, `cross-env`, `env-cmd`, `doppler`, `infisical`, `op`) nelle quattro forme (da soli, con un percorso, dopo `command`, dopo `env`).
- `claude plugin validate --strict` sulla copia del plugin: «Validation passed», uscita 0 (`validate/validate-1.txt`); restano un avviso della directory dei plugin (manca l'icona) e un consiglio sul README, che non cambiano l'esito. La copia elenca `tollgate:rules-security`, `tollgate:implementer-security`, `tollgate:reviewer-security` e `tollgate:final-security`.

## Passi e tentativi

Tutti i passi sono riusciti al tentativo 1 (`exit-codes.txt`: uscita 0 per tutti e sei). Durate e turni dai messaggi `result` degli stream; gli orari di `esito.txt` sono locali, quelli degli eventi UTC.

| Passo | Tentativi | Esito | Durata | Turni | Costo equivalente |
|---|---|---|---|---|---|
| `controlla` e `prepara` | 1 | interruttore acceso, progetto e stato pronti; `init` propone `security`; blocco L2, `spec-check` e `plan-check` ok | n/d | n/d | nessuno |
| `passo1`: `/tollgate:start #1 L2` | 1 | lavoro #1 in L2 sul ramo `tg/1-scadenza-dei-token-e-lettura-delle-note`; spec scritta con `Write` e committata (`50b8f68`), 9 giri avversariali | 869 s | 33 | 7,30 USD |
| `passo2`: `/tollgate:approve spec 1` | 1 | spec approvata con 1 fetta, fase `plan`, taglia media | 19 s | 2 | 0,38 USD |
| `passo3`: piano | 1 | piano scritto e committato (`ed5433b`), 6 giri dell'avversario del piano, fase `approval` | 595 s | 36 | 5,35 USD |
| `passo4`: `/tollgate:approve plan` | 1 | piano approvato, 2 task in una sola area, 6 file nello scope, fase `execution` | 13 s | 3 | 0,37 USD |
| `passo5`: `/tollgate:execute` | 1 | due task fatti e rivisti, tutti e due `approved` al primo giro | 363 s | 15 | 3,67 USD |
| `passo6`: `/tollgate:finish` | 1 | `finish check` verde, revisione finale ciclo 1 (`ok`), PR finta #1 | 128 s | 9 | 2,47 USD |

Cosa è successo, in ordine:

1. **`passo1`.** La sessione ha avviato il lavoro in L2, è entrata nel worktree con `EnterWorktree`, ha scritto la spec con `Write` e l'ha committata identica all'input (`50b8f68`; il controller l'ha controllato con `diff` prima di dare l'atto). Poi nove giri di `tollgate:spec-adversary`, un agente per giro, l'ultimo senza rilievi. Ogni correzione ha il suo commit «correzioni dal giro avversariale N» (`0254fd3` ... `82fa951`, più `bd50bda` con il report del giro 9; `registro-1/git-log-worktree.txt`). 15 eventi `spec_audit_round` in `registro-1/events.jsonl`: 9 della spec e 6 del piano.
2. **`approve spec 1` dato dal controller.** Prima di darlo il controller ha confrontato la spec con l'input (`spikes/c2/input/spec-L2.md`): `spec-diff.txt` è il confronto con la spec finale. Ogni differenza viene da un rilievo dei giri avversariali (vedi «Gli avversari»). La spec è passata da 2 a 13 must-have, sempre in una sola fetta, quindi il passo 2 (che manda sempre `approve spec 1`) valeva. L'atto è `a-1` in `events.jsonl` (fonte `claude-code`).
3. **`passo3` e `passo4`.** Il piano è stato scritto con `Write`, committato identico all'input (`ed5433b`) e corretto in sei giri dell'avversario del piano, un commit per giro (`e48b2ba` ... `3b1aee4`, più `0fd5c92` con il report del giro 6). `approve plan` dato dal controller dopo il confronto con l'input (`piano-diff.txt`): le differenze vengono dai rilievi e riprendono la spec approvata. Restano due task; l'atto è `a-2`.
4. **`passo5`.** Il task 1 (scadenza, chiave di firma) e il task 2 (`can_read`, `read_note`) sono stati fatti da `tollgate:implementer-security` e rivisti da `tollgate:reviewer-security`. Task 1: commit `1aa13c7`, ricevuta `verify` green con 9 test, `approved` con 2 rilievi `minor`. Task 2: commit `fc2a3f5`, ricevuta green con 15 test, `approved` senza rilievi. Nessun giro di correzione. La sessione non ha lanciato `/tollgate:finish`.
5. **`passo6`.** `finish check` verde sullo SHA `fc2a3f5` (15 test); revisione finale al ciclo 1 con `tollgate:final-reviewer` e `tollgate:final-security`, quattro rilievi `minor` tutti scartati da `tollgate:finding-verifier`; PR finta #1 aperta con il `gh` finto (`registro-1/fakegh.log`, `pr create`). L'atto `finish` è `a-3`.

Nessun atto dell'utente è stato dato dal modello: i soli atti in `events.jsonl` sono `a-1` e `a-2` (dati dal controller) e `a-3` (`finish`, il comando del passo 6). Nessun `needs_you`, nessun veto, nessun blocco, nessuna deroga (`registro-1/stats.json`). Stato finale (`registro-1/status.json`, `snapshot.json`): L2, fase `pr_open`, 2 task `done`, PR 1, nessun blocco.

## Proposta di `init`

Il progetto di prova (`spikes/c2/flow/`) ha `app/notes.py` (`Note(id, owner, text)` e un archivio in memoria), `app/auth/__init__.py` e `app/auth/tokens.py` (`sign` e `verify` con firma HMAC della libreria standard, senza scadenza; la firma si confronta con `!=`), `tests/test_tokens.py`, un `verify` con `tools/unittest_junit.py` e `report = "junit:reports/junit.xml"`, come B7.

- `init` propone solo `security`, con `paths = ["app/auth/**"]`: lo accendono `app/auth/__init__.py` e `app/auth/tokens.py`. Gli altri cinque profili non sono proposti (nessun file corrisponde ai loro percorsi). Dopo la proposta: «blocco L2: ok», «spec-check: ok fette: 1», «plan-check: ok». Questo viene dall'uscita di `prepara` annotata dal controller.
- Il blocco copiato nel `tollgate.toml` del progetto (commit `b54a0ce`, «profilo security proposto da init») si legge nello stream di `passo1`, dove l'avversario del giro 1 lo apre: `min_level = "L2"`, `agent = "tollgate:implementer-security"`, `reviewer = "tollgate:reviewer-security"`, `final_specialist = "tollgate:final-security"`, `checklist = "chi arriva al codice cambiato e cosa può fare; accesso negato provato da un test; nessun segreto nel diff; valori predefiniti che rifiutano"`, le 17 regole `R-SECURITY-…` e le 13 che bloccano, `skills = []`, `commands = {}`, `dod = []`.
- `registro-1/tipi-task.txt`: tutti e due i task con `agent_type=tollgate:implementer-security` e `reviewer_type=tollgate:reviewer-security`. Il task 2 tocca anche `app/notes.py`, fuori da `app/auth/`: i file fuori da ogni profilo non contano e il task resta all'area `security`, come aveva previsto la sonda del revisore del Task 8.

## Il lavoro in L2 e gli agenti lanciati

Ventidue subagenti (`registro-1/events.jsonl`, eventi `subagent_start`; `comandi-modello.txt`: `Agent` 22). Il modello di ognuno viene dal campo `model` dei messaggi dei subagenti negli stream ed è confermato dagli eventi `cost` (`by_model`). Nessun lancio di `Agent` porta un parametro `model`: vale il frontmatter degli agenti.

| Passo | Agenti | Modello |
|---|---|---|
| `passo1` | 9 `tollgate:spec-adversary` (uno per giro) | Fable |
| `passo3` | 6 `tollgate:plan-adversary` (uno per giro) | Fable |
| `passo5` | task 1 e 2: `tollgate:implementer-security` (nomi `tg-1-t1`, `tg-1-t2`) | opus |
| `passo5` | task 1 e 2: `tollgate:reviewer-security` | Fable |
| `passo6` | `tollgate:final-reviewer`, `tollgate:final-security`, `tollgate:finding-verifier` | Fable |
| tutti | la sessione principale | opus |

Nei passi 1 e 5 i messaggi `result` contano anche un consumo piccolo di `claude-haiku-5-5` (0,019 e 0,005 USD equivalenti), senza nessun messaggio di un agente su quel modello. Sono i due soli passi con `WebFetch` (7 e 2 chiamate): con ogni probabilità è il modello che Claude Code usa da sé per leggere le pagine, non un agente di tollgate. Le evidenze non lo dicono in modo esplicito.

Note di ricerca: una per task, tutte e due valide al primo invio (`registro-1/eventi-ricerca.jsonl`, `research-1.md`, `research-2.md`). La nota del task 1 cita due pagine di docs.python.org (`hmac`, `str.isdigit`); quella del task 2 dice «Nessuna fonte esterna» (solo libreria standard). Lavoro finale: due commit di codice dopo l'approvazione del piano (`1aa13c7`, `fc2a3f5`). Test: 9 dopo il task 1 e 15 dopo il task 2 (ricevute `verify` in `events.jsonl`); il progetto di partenza ne aveva 2 (`spikes/c2/flow/tests/test_tokens.py` nel repo, non nelle evidenze).

## Gli avversari

Nove giri sulla spec e sei sul piano: il numero più alto delle prove L2 (B7: 5 e 4). Gli avversari non hanno `rules-security` (nelle trascrizioni dei sei avversari del piano non c'è nessun titolo di regole, e nessun loro report cita un id `R-SECURITY-…`). Lavorano con la voce sulla sicurezza fin dal progetto che il Task 2 ha messo in «Cosa cercare» (decisione 20). Hanno però letto il `tollgate.toml` del progetto, e la `checklist` del profilo la citano.

**Spec, giro 1** (3 `major`, 3 `moderate`, 1 `minor`). Quasi tutti i rilievi riguardano la sicurezza:
- *accesso negato non definito né provato* (`major`): l'unico must-have sulla lettura era il caso positivo, e una `read_note` che dà la nota a chiunque abbia un token valido sarebbe passata; l'avversario cita la `checklist` del profilo («accesso negato provato da un test», `tollgate.toml:26`). Da qui M6, M7 e M8;
- *chi legge `C2_PROVA_SECRET` e cosa succede se manca* (`major`): la lettura più comoda, con un valore vuoto di ripiego, avrebbe firmato con una chiave vuota, e chiunque avrebbe potuto forgiare un token; cita «valori predefiniti che rifiutano». Da qui `signing_key()`, che rifiuta la chiave assente, vuota o non codificabile (M5), e più avanti M11 e M13;
- *scadenza non numerica e confronto della firma non specificati* (`moderate`): chiede di dire se il confronto deve essere a tempo costante. Da qui la tana «Confronto della firma: a tempo costante con `hmac.compare_digest` sui byte UTF-8»;
- *interfaccia dell'issue sparita dalla spec* (`major`): `read_note` e `can_read(user: str, owner: str)`, con il proprietario come stringa per evitare un import circolare;
- *una sola fetta* (`moderate`, scelta motivata nella tana «Numero di fette»), *il confine `expires_at == now` non provato* (`moderate`, poi M3), *chi riceve un token nuovo* (`minor`).

**Spec, giri 2-9.** Giro 2: un `major` (un token con un surrogato isolato fa sollevare `verify`, poi M9) e un `moderate` (`int` oltre 4300 cifre, poi il limite di 20 cifre in M4), più tre `minor` (codifica della chiave, utente vuoto, poi M10). Giro 3: un `moderate` (chi fornisce `now`: il chiamante fidato, mai chi presenta il token) e cinque `minor`. Giri 4-8: solo `minor` (ordine dei passi di `read_note` a chiave assente, il ramo «non codificabile» di M5, la docstring, il test di `can_read` che diventa M12, la chiave vuota in `verify` che diventa M13, il contenuto del `RuntimeError`). Giro 9: nessun rilievo.

**Piano, giro 1** (5 `major`, 1 `moderate`): il piano copriva 2 must-have su 13; `can_read(user, note)` contraddiceva la spec e creava un import circolare (diventa `can_read(user, owner)`); mancava `signing_key()`; il passo su `verify` ometteva l'ordine dei controlli fissato dalla spec; `tests/test_access.py` era fuori dallo scope; il test di `NotesTest` non aveva isolamento né chiave. Giri 2-5: un `moderate` ciascuno nei giri 2 e 3, il resto `minor` (casi dei test di M4, M5, M7, M8, ordine TDD, sezione «Rischi»). Giro 6: nessun rilievo.

**Che cosa vuol dire per la prova.** La spec di prova diceva già in poche righe chi usa il codice, quali dati e segreti tocca e cosa succede con un input ostile (D2 del Task 8). Su quella base l'avversario ha chiesto, già sulla spec, il test del caso negato, il rifiuto senza segreto e la decisione sul confronto della firma. Ha usato la voce sulla sicurezza fin dal progetto e la `checklist` del profilo. È l'effetto previsto dalla ruling D2, più forte del previsto: la sicurezza fin dal progetto (decisione 20, Task 2) fa già sulla spec il lavoro che la prova voleva vedere fare alle regole nel codice. Il costo si vede in due punti. Il piano di prova non nominava i requisiti delle regole (decisione 16), ma quando è arrivato all'implementatore li conteneva già quasi tutti, quindi i segnali delle regole nel codice non provano il precaricamento di `rules-security`: la prova resta il titolo della skill nelle trascrizioni, con gli id citati da revisori e specialista come indizio forte (vedi «Segnali»). E i 15 giri degli avversari su Fable sono quasi metà del costo, nove dei quali senza rilievi sopra `minor` (vedi «Costi»).

## Lo specialista finale

- **I revisori del ciclo.** `passo6` lancia `tollgate:final-reviewer`, `tollgate:final-security` e, per i rilievi, `tollgate:finding-verifier`. Il controller ha letto da una copia temporanea dello stato di prova (lo stato non è nelle evidenze del repo) che `review_cycles.reviewers` è `["tollgate:final-reviewer", "tollgate:final-security"]`, `reported = {final-reviewer: ok, final-security: ok}`, `outcome` `ok`, `findings_confirmed` 0. Nelle evidenze il ciclo si vede in `events.jsonl` (evento `review_cycle`: `number` 1, `outcome` `ok`, `findings_confirmed` 0) e nei due verdetti dello stream (`outcome: ok`, stesso `sha` e `code`).
- **Il brief.** Il file di brief della revisione finale, letto da `final-reviewer` e da `final-security` nello stream di `passo6` (righe 63 e 72 di `passo6/tentativo-1/claude.jsonl`), ha la sezione «Lista di controllo dell'area» con la `checklist` del profilo: «chi arriva al codice cambiato e cosa può fare; accesso negato provato da un test; nessun segreto nel diff; valori predefiniti che rifiutano». Porta anche i must-have M1-M13, lo scope dei sei file, le gravità e il blocco JSON del verdetto con `sha` e `code`. Il revisore generale ha passato la lista voce per voce («Lista dell'area» nel suo report).
- **Il riporto dello specialista.** `outcome` `ok`, nessun `blocker` né `major`. Comincia dal rischio e dal raggio d'azione: il confine è il token che arriva a `read_note` da un chiamante non fidato; un anonimo o un token non valido si ferma in `verify`; un utente autenticato legge solo le sue note; a chiave assente il `RuntimeError` passa e nessuno entra. Poi le regole sul diff, ciascuna con il punto del codice.
- **Gli id che cita.** Rispettate: R-SECURITY-03, -04, -05, -07, -08, -10, -12. Non applicabili, perché il diff non ha password, cookie, login, reindirizzamenti né CORS: R-SECURITY-06, -09, -11, -13, -14. Nessuna delle regole sul report (01, 02, 15, 16, 17): lo specialista giudica solo quelle sul diff, come dice la sua sezione «Area `security`».
- **Voce `specialists` della DoD.** Nell'uscita di `finish check` la voce «Specialisti finali passati» è `[dopo la revisione]` (riga 23 dello stream), come «Nessun rilievo blocker o major confermato»; nell'uscita di `finish open-pr`, che apre la PR finta, è `[sì]` (riga 307). Nessuna voce `[no]`. Il corpo della PR (`.tollgate-run/1/pr-body.md`) non è nelle evidenze: `fakegh.log` ha solo gli argomenti di `pr create`.
- Token (`registro-1/stats.json`): `final-reviewer` 47.120, `final-security` 58.388, `finding-verifier` 38.857. In B7 lo specialista aveva usato meno del revisore generale (38.646 contro 54.762); qui di più.

## I rilievi minori

**Revisore del task 1** (`approved`, due `minor`, tutti e due con R-BASE-11, cioè il report contro i fatti):
- il report dice che una firma non ASCII dà `None` con una «prova fatta a mano», senza comando né esito, e nessun test copre quel ramo; è proprio il caso che giustifica `.encode("utf-8")` prima di `compare_digest`, perché con due `str` non ASCII la funzione solleverebbe `TypeError`;
- il report dice che `signing_key` legge `os.environ['C2_PROVA_SECRET']`, mentre il codice usa `os.environ.get(...)`: il comportamento è giusto, il report è inesatto.

Il revisore del task 2 ha approvato senza rilievi.

**Revisione finale** (quattro `minor`, tutti **scartati** dal verificatore; nessuno confermato):
- `f-1-1` (`final-reviewer`, confidenza 0,9): `from None` superfluo in `signing_key`, perché il `raise` non sta dentro un `except`. Scartato: il piano lo prescrive alla lettera;
- `f-1-2` (`final-reviewer`, 0,7): il test di M8 non affianca esplicitamente il `None` della nota inesistente a quello della nota altrui. Scartato: la nota altrui è già asserita `None` in un altro test, e `None` è un valore solo;
- `f-1-3` (`final-security`, 0,6, citando R-SECURITY-05): `can_read("", "")` dà `True`. Oggi non si raggiunge da `read_note`, perché `verify` rifiuta l'utente vuoto. Scartato: R-SECURITY-05 riguarda i segreti e le impostazioni mancanti, e l'uguaglianza è il contratto del piano;
- `f-1-4` (`final-security`, 0,7): tra le scadenze malformate di M4 manca la stringa vuota, che il codice rifiuta già. Scartato: M4 non la chiede.

`f-1-3` è un buon esempio del limite del verificatore: il fatto è vero e ha un peso di sicurezza (un permesso concesso a un'identità vuota se un domani qualcuno chiama `can_read` senza passare da `verify`), ma la regola citata non è quella giusta, quindi il rilievo cade. Lo specialista l'aveva dato come rilievo `minor`, tra le note che «non chiedono modifiche». Il `finding-verifier`, che ha precaricate solo le regole di base, per giudicarlo ha letto il testo di R-SECURITY-05 dal file della skill (`sed -n 39,44p …/skills/rules-security/SKILL.md`, riga 262 di `passo6/tentativo-1/claude.jsonl`, anche in `comandi-modello.txt`).

## Segnali delle regole e precaricamento

**(a) I tre segnali delle regole della decisione 16.**
- *Confronto a tempo costante* (R-SECURITY-08): l'implementatore del task 1 ha sostituito `!=` con `hmac.compare_digest` sui byte UTF-8, e revisore, revisore generale e specialista l'hanno riconosciuto. Ma il confronto a tempo costante è entrato nella spec dopo il rilievo 6 del giro 1 della spec (tana «Confronto della firma», data per chiusa dal giro 2) ed era nel piano tra i «vincoli senza must-have». **Non conta** come segnale di `rules-security`.
- *Modello delle minacce e raggio d'azione nel report* (R-SECURITY-01 e R-SECURITY-16): ci sono **tutti e due, in tutti e due i report** degli implementatori, nel campo `done`. Task 1: «Chi arriva al codice cambiato: nessuno da fuori» (funzioni chiamate solo dai test e, con il task 2, da `read_note`), e «Raggio d'azione: tocca verify, signing_key e la chiave C2_PROVA_SECRET», con cosa succederebbe se il codice fosse sbagliato. Task 2: chi arriva a `read_note` (nessuna rotta né endpoint; se domani un chiamante le passasse un token, lo fermerebbero `verify` e poi `can_read`) e «Raggio d'azione: read_note è chiamata solo dai test», con i dati letti e nessun permesso nuovo. I report non citano gli id 01 e 16 (il task 1 cita invece R-SECURITY-15, «non si applica»), ma il contenuto è quello che le due regole chiedono. Non lo chiede il piano di prova. Lo chiede però **per esteso il testo dell'agente dell'area**: `agents/implementer-security.md` (riga 51) dice di scrivere nel campo `done` chi può arrivare al codice cambiato, cosa può fare e quale controllo lo ferma, il raggio d'azione del cambio e la prova locale fatta con valori finti, e i due report lo ricalcano quasi parola per parola. Lo chiedono anche R-SECURITY-01 e R-SECURITY-16 nella skill e la `checklist` del profilo nel `tollgate.toml`, che tutti e due gli implementatori hanno letto (`lookups.txt`, letture 6 e 16). Quindi questo segnale prova che il profilo manda il task all'agente dell'area e che l'agente fa ciò che il suo testo chiede; **non prova il precaricamento** di `rules-security`.
- *Id `R-SECURITY-…` citati dai revisori e dallo specialista.* Revisore del task 1: 03, 05, 07, 08, 10, 12 sul diff; 01, 15, 16, 17 sul report. Revisore del task 2: 03, 04, 05, 08, 10, 12 sul diff; 01, 16, 17 sul report. Insieme: 01, 03, 04, 05, 07, 08, 10, 12, 15, 16, 17. Fra queste, 15 (revisore del task 1) e 08 (revisore del task 2) sono citate come «non si applica». Specialista: 03, 04, 05, 07, 08, 10, 12 rispettate; 06, 09, 11, 13, 14 non applicabili; 05 anche nel rilievo `f-1-3`. **Comparsi**, e ognuno con il contenuto giusto (07 la scadenza, 08 `hmac.compare_digest`, 10 nessun segreto oltre a `PROVA-123`, 12 il token validato al confine). La divisione tra regole sul diff e regole sul report è scritta, id per id, nella skill e anche nel testo degli agenti (`agents/reviewer-security.md`, `agents/final-security.md`). Quei testi però elencano solo i numeri, senza dire che cosa chiede ogni regola: l'abbinamento fra numero e contenuto viene dal testo della skill. È l'**indizio forte** del precaricamento; la prova resta il titolo nelle trascrizioni, al punto (c).

**(b) I due segnali della sicurezza fin dal progetto** (test del caso negato, rifiuto senza segreto): comparsi **già nella spec**, chiesti dall'avversario al giro 1 (M5, M6, M7, M8, M11, M13). Nel codice ci sono tutti e due (`signing_key()` senza ripiego e i test dei casi negati), ma provano la decisione 20 e la spec, non `rules-security`.

**(c) Il titolo di `rules-security` nelle trascrizioni dei subagenti.** `registro-1/trascrizioni.txt` (sessione 5 = `passo5`, sessione 6 = `passo6`): `# Regole security (versione 1)` e `# Regole di base (versione 1)` con `isMeta: sì` nelle trascrizioni dei due implementatori e dei due revisori del passo 5 (`a2bb65c…` e `ae98c72…` implementatori, `a2d7515…` e `af6aaab…` revisori, secondo gli eventi `subagent_start`) e dello specialista del passo 6 (`a015a11…`, `final-security`). `final-reviewer` (`a19a07b…`) e `finding-verifier` (`a75543…`) hanno solo `# Regole di base (versione 1)`. I sei avversari del piano (sessione 3): «nessun titolo». Per ogni titolo c'è anche una riga `isMeta: no`; la prova è quella delle righe `isMeta: sì`. Per la sessione 1 (`passo1`) `registra` non ha trovato trascrizioni di subagenti: i nove avversari della spec non sono nel file, e le evidenze non dicono perché (la sessione era entrata nel worktree con `EnterWorktree`). `registro-1/precarico.txt` dice «indizio» (8 righe con `R-BASE-` nelle uscite): le trascrizioni non stanno nello stream, e la prova del precaricamento resta il titolo in `trascrizioni.txt`.

**(d) La riga `Sicurezza:` nei report dei due implementatori** (campo `done` del blocco JSON, risultato dello strumento `Agent` nello stream di `passo5`):
- task 1: il token è input non fidato ed è validato al confine (codifica, forma, firma a tempo costante, utente, scadenza di sole cifre ASCII al più 20); il caso negato è provato da test (token scaduto, che scade nell'istante `now`, malformato, non codificabile, con utente vuoto, con chiave vuota); per la chiave mancante non c'è ripiego, un test prova i casi assente, vuota e non codificabile, e il messaggio d'errore non contiene il valore;
- task 2: il token è validato da `verify` al confine; a chiave mancante si chiude con `RuntimeError`, mai con un ripiego; l'accesso è negato per difetto con lo stesso `None` nei tre casi negativi, così non si capisce quali note esistono; i casi negati sono provati da test; nessun segreto nel codice, nei log o nei messaggi, e nei test solo `PROVA-123`.

Il revisore del task 2 scrive che la riga c'è e che il diff non la smentisce. Il controller ha visto le due righe anche nella tabella `subagents` della copia dello stato. `snapshot.json` non le contiene.

**(e) I due suggerimenti nel codice di partenza** che il revisore del Task 8 aveva segnalato (`spikes/c2/flow/tests/test_tokens.py`): `self.secret = os.environ["C2_PROVA_SECRET"].encode()` si ferma se la variabile manca, e `test_altered_token_is_rejected` mostra l'abitudine di provare il rifiuto. L'implementatore ha letto quel file (nota di ricerca, `lookups.txt`) e ha seguito lo schema del `setUp`. Il rifiuto senza segreto e il test del caso negato erano però già chiesti dalla spec, quindi i due suggerimenti non cambiano la lettura dei segnali.

## Costi

I costi vengono dai messaggi `result` degli stream (`total_cost_usd`, `modelUsage`): sono **equivalenti API**, non addebiti. Non c'era nessuna `ANTHROPIC_API_KEY`: la prova usa la quota dell'abbonamento e non si è speso denaro.

| Passo | Totale | opus | Fable | haiku |
|---|---|---|---|---|
| `passo1` | 7,30 | 1,72 | 5,57 | 0,02 |
| `passo2` | 0,38 | 0,38 | — | — |
| `passo3` | 5,35 | 1,39 | 3,96 | — |
| `passo4` | 0,37 | 0,37 | — | — |
| `passo5` | 3,67 | 2,57 | 1,10 | 0,01 |
| `passo6` | 2,47 | 0,55 | 1,93 | — |
| totale | **19,55 USD** | 6,98 | 12,55 | 0,02 |

(USD equivalenti, arrotondati al centesimo; haiku 0,019 + 0,005.)

**Contro la stima.** La decisione 16 stimava 10-18 USD equivalenti; la prova ne ha usati 19,55. Il motivo sono i giri degli avversari: 15 giri su Fable (9 sulla spec, 6 sul piano) costano 9,53 USD, quasi metà del totale. Il dato che spiega il numero dei giri sta in `registro-1/events.jsonl` (eventi `spec_audit_round`): i giri 4-9 della spec e 4-6 del piano hanno `outcome: empty`, cioè nessun rilievo sopra `minor` (i giri con un `moderate`, come il 3 della spec, hanno `findings`). `audit prepare` ha rifiutato per rilievi aperti solo dopo il giro 1 della spec e il giro 1 del piano, che avevano rilievi `major` (righe 209 di `passo1` e 218 di `passo3`). Ogni volta che la sessione corregge il documento, anche per una nota `minor`, il documento cambia e si apre un giro nuovo: i giri 5-9 della spec e 5-6 del piano si sono aperti solo perché la sessione aveva corretto le note `minor` del giro prima. Sono sette giri, 280.137 token (`cost` in `events.jsonl`: 194.229 della spec, 85.908 del piano). In B7 erano 9 giri e la sessione era su sonnet; qui la sessione e gli implementatori sono su opus e tutti i revisori su Fable (decisione 14). L'esecuzione dei due task e la revisione finale, insieme, costano 6,14 USD.

**Token dei subagenti** (`registro-1/stats.json`, totale 1.014.248): `spec-adversary` 349.871 (9 agenti), `plan-adversary` 256.170 (6), `implementer-security` 174.677 (100.376 e 74.301), `reviewer-security` 89.165 (50.696 e 38.469), `final-reviewer` 47.120, `final-security` 58.388, `finding-verifier` 38.857. Per modello: opus 174.677 (gli implementatori), Fable 839.571 (tutti gli altri). Per task (`snapshot.json`): task 1 151.072, task 2 112.770. Giri di correzione 0, veti 0, blocchi 0, deroghe 0. Ore di fase: 0,26 h in `spec_audit`, 0,17 h in `plan`, 0,01 h in `approval`, 0,12 h in `execution`, 0,03 h in `review`, 0,01 h in `pr_open`.

## Comandi del modello

`registro-1/comandi-modello.txt` elenca i comandi del modello (sessione principale e subagenti) e il totale degli strumenti. Letti a mano: comandi `tollgate` (`start`, `audit prepare`, `act apply`, `status --checkpoint`, `research submit`, `task start`, `task review-prepare`, `task done`, `verify` attraverso gli implementatori, `finish check`, `review prepare`, `finish open-pr`); `git` (elenco dei file, log, stato, `add`, `commit`, `diff`, `show`, `rev-parse`, `check-ignore`); `cat`, `ls`, `sed`, `grep`; script `python3` che correggono la spec con sostituzioni di testo; `python3 -m unittest` e `python3 tools/unittest_junit.py` per i test; quattro sonde `python3 -c` (della sessione, di un implementatore e dei revisori finali) sul comportamento di `os.environ` e di `verify`, con il valore finto.

- Nessun `node`, `npm`, `npx`, `pnpm`, `yarn`, `bun`, `bunx`, `deno`, `supabase`, `psql`, `docker`, `wrangler`, `vercel`, `openssl`, `dotenv`, `dotenvx`, `cross-env`, `env-cmd`, `doppler`, `infisical`, `op`, `gh`, `curl`, `wget` né `git push` (controllo a mano e con una ricerca a confine di parola sul file).
- `registro-1/comandi-rischiosi.txt` è **vuoto**. I falsi positivi di `op` che il revisore del Task 8 temeva non si sono presentati.

Strumenti del modello (totale, di cui da subagenti): `Agent` 22 (0), `Bash` 84 (39), `Edit` 41 (28), `EnterWorktree` 1 (0), `Glob` 26 (26), `Grep` 2 (2), `Read` 184 (182), `Skill` 4 (2), `ToolSearch` 1 (0), `WebFetch` 9 (9), `Write` 7 (3). I due `Skill` dei subagenti sono degli implementatori, che hanno chiamato `superpowers:test-driven-development`: lo chiede `agents/implementer-security.md` (passo 2 di «Il lavoro», il TDD), come a ogni implementatore di tollgate, e la chiamata riesce perché quel plugin è installato sulla macchina (vedi «Limiti»).

Letture registrate (`registro-1/lookups.txt`): 16 `read` e 2 `fetch` degli implementatori; i `Grep` degli implementatori non sono registrati (B1-V6; `grep-non-registrati.txt`).

## Risultati di WebFetch e pagine di terzi

- Nove `WebFetch`, tutte su docs.python.org. Sette in `passo1`, fatte dagli avversari della spec: `library/stdtypes.html` quattro volte, `library/hmac.html` due volte, `library/os.html` una volta. Servivano a verificare `str.isdigit` e `isascii`, il limite di cifre nella conversione di `int`, `hmac.compare_digest` con testo non ASCII e la codifica dei valori delle variabili d'ambiente. Due in `passo5`, fatte dall'implementatore del task 1: `library/hmac.html` e `library/stdtypes.html#str.isdigit`.
- Tutte e nove sono **sotto i 5000 caratteri** (da 519 a 2.624), quindi `flowreg.py togli-pagine` non le toglie. Il controller le ha lette una per una, poi le ha sostituite tutte con il segnaposto (`scrub.py strip-web`, ruling del Task 9): erano riassunti con frasi citate dalle pagine, e nelle evidenze non deve restare testo di terzi. **Nelle evidenze non resta nessun risultato di `WebFetch`**: restano gli indirizzi e le lunghezze nel segnaposto, e i riassunti con parole proprie degli agenti nei loro report e nelle note di ricerca. `test_committed_evidence_has_no_long_web_results` è verde.
- Le pagine erano documentazione di Python. Il testo delle pagine non è più nelle evidenze, quindi questo rapporto non può dire se contenesse richieste agli agenti; nei report e nelle note degli agenti non c'è traccia di richieste seguite.
- Per ogni flusso `togli-pagine` ha anche sostituito le tre uscite degli hook `SessionStart` di altri plugin (`registro-1/togli-pagine.txt`: «3 risultati sostituiti» per flusso); poi le righe stesse sono state tolte (vedi «Anonimizzazione»), e con loro i segnaposto che ne davano la lunghezza.

## Scostamenti dall'atteso

- **I giri degli avversari e il costo.** Nove giri sulla spec e sei sul piano, contro i 5 e 4 di B7; il costo è sopra la stima (19,55 contro 10-18 USD equivalenti). Sette di quei giri (5-9 della spec, 5-6 del piano) si sono aperti solo dopo correzioni di note `minor` (vedi «Costi»). Il passo 1 da solo è costato 7,30 USD; il controller ha deciso di proseguire (consumo di quota, senza addebito, e nessuna fermata delle istruzioni riguarda il consumo).
- **La spec e il piano sono cambiati molto.** La spec da 2 a 13 must-have, con interfacce, ordine dei controlli e una tana per ogni scelta; il piano allineato ai 13 must-have. Tutte le differenze vengono dai rilievi, un commit per giro, e sono state ammesse dal controller.
- **`can_read(user, owner)` invece di `can_read(user, note)`.** Il piano di prova (e la decisione 16) dicevano `can_read(user: str, note: Note)`; la spec, al giro 1, ha scelto il proprietario come stringa per non importare `app/notes.py` da `app/auth/access.py`, e l'avversario del piano ha allineato il piano (rilievo `major` R2 del giro 1).
- **I segnali delle regole sono più deboli del previsto** (vedi sopra): il confronto a tempo costante è passato dalla spec; il modello delle minacce e il raggio d'azione nei report li chiede il testo dell'agente dell'area. Per il precaricamento restano la prova del titolo con `isMeta: sì` nelle cinque trascrizioni e, come indizio forte, gli id citati da revisori e specialista con il contenuto giusto.

## Limiti

- **Un lavoro piccolo (L2).** Due task, una fetta, sola libreria standard. La prova mostra il percorso completo con il profilo (spec, piano, esecuzione, revisione finale con lo specialista, PR); non è un lavoro grande né un'applicazione vera.
- **Il test di testo non prova un servizio di login vero.** I test chiamano funzioni Python con un segreto finto: nessun endpoint, nessuna sessione, nessun cookie, nessuna libreria di token o password. Le regole su password, cookie, login, reindirizzamenti e CORS (06, 09, 11, 13, 14) sono rimaste non applicabili.
- **La sessione usa la configurazione di Claude Code della macchina, con altri plugin attivi.** Lo script non cambia `HOME`: nella sessione erano attivi altri plugin, i loro hook `SessionStart` e `PreToolUse` sono partiti a ogni passo (le loro uscite sono state tolte), e la skill di TDD che `implementer-security` chiama (`superpowers:test-driven-development`) è di un plugin installato sulla macchina: il testo di quella skill di terzi è entrato nel contesto dei due implementatori e non è nelle evidenze. Claude Code ha usato anche haiku per le pagine lette con `WebFetch`, fuori dagli agenti di tollgate.
- **Le difese che `--disallowedTools` non chiude** (`registro-1/limiti.txt`): i divieti sono a prefisso e non chiudono `env VAR=… <programma>`, `sudo`, `xargs`, `bash -c '…'`; per `git`/`gh` restano aperti `git -C x push …`, `git push --force-with-lease`, `git remote set-url` seguito da un push, `env gh`. `Write` ed `Edit` nudi valgono per qualsiasi percorso. La difesa vera è l'hook `effects` di tollgate più un progetto di prova senza credenziali.
- **I limiti della grep di `registra`:** un `(openssl)` nudo, un comando dopo un backtick e i falsi positivi su `echo` non sono coperti. `--allowedTools` concede gli strumenti senza domande: in una sessione interattiva `WebFetch` chiede un permesso per dominio.
- **Il precaricamento si prova con le trascrizioni**, lette da `registra` solo nelle cartelle della prova; quelle degli avversari della spec non sono state trovate.
- **Le fermate e le prove dal vivo dell'utente sono di C6.** Qui non c'è stata nessuna fermata, quindi la prova non mostra come `security` si comporta quando una regola si scontra con la spec (in B7 era successo con `database`).
- Gli orari degli eventi sono UTC; quelli di `esito.txt` sono locali.

## Differenze con il registro del controller

Le evidenze confermano il registro del controller su passi, tentativi, durate, turni, costi totali, giri degli avversari, atti, esiti dei task e della revisione finale, trascrizioni e pulizia. Non coincidono in sei punti. Il rapporto segue le evidenze:

1. **Id citati dai revisori del task.** Il registro elenca R-SECURITY-01, -03, -04, -05, -08, -10, -12, -15; i verdetti nello stream citano anche **-07** (revisore del task 1, sul diff) e **-16** e **-17** (tutti e due i revisori, sul report).
2. **Id citati dallo specialista.** Il registro elenca 03, 04, 05, **06**, 07, 08, 10, 12; nel verdetto 06 non è tra le regole giudicate rispettate ma tra quelle «non applicabili», insieme a **09, 11, 13, 14**, che il registro non nomina.
3. **La DoD a `finish check`.** Il registro dice «tutte le voci della DoD `[sì]`»; a `finish check` due voci erano `[dopo la revisione]` (i rilievi confermati e gli specialisti) e sono diventate `[sì]` solo a `finish open-pr`. È il comportamento previsto, come in B7.
4. **Haiku nei costi.** Il registro divide i costi dei passi 1 e 5 tra opus e Fable; i messaggi `result` hanno anche `claude-haiku-5-5` (0,019 e 0,005 USD). Il totale di 19,55 lo comprende già.
5. **Le trascrizioni degli avversari della spec.** Il registro non lo dice: `registra` non le ha trovate (sessione 1, «nessuna trascrizione di subagente»).
6. **Modello delle minacce e raggio d'azione.** Il registro («Prova: segnali») li conta tra i segnali delle regole della decisione 16. Li chiede per esteso il testo di `agents/implementer-security.md`, quindi provano l'instradamento all'agente dell'area, non il precaricamento della skill (vedi «Segnali»).

## Anonimizzazione delle evidenze

Già fatti dal controller: `togli-pagine` (3 risultati per flusso, tutti uscite di hook `SessionStart` di altri plugin, poi 0 nuovi al secondo passaggio), `evals/scrub.py anonymize` (nome utente, host, `/home/<utente>`; 12 file) e la sostituzione dei nove risultati brevi di `WebFetch` con il segnaposto. Poi, prima del commit, su tutti i file di `evidenze/c2/flusso/`:

- **Sessioni.** I sei id di sessione sono diventati `SESSIONE-1` ... `SESSIONE-6`, uno per flusso, con la stessa numerazione di `registro-1/trascrizioni.txt` (`passo1` ... `passo6` = 1-6): 4.433 occorrenze, negli stream, in `events.jsonl` e in `eventi-c1.jsonl` (anche nei percorsi dei file salvati da Claude Code). Nessun nome di cartella conteneva un id. Gli `agent_id` restano: non sono segreti.
- **Percorsi.** Il percorso del checkout del repo è diventato relativo al repo (12 occorrenze, in `comandi-modello.txt` e `togli-pagine.txt`).
- **Righe `init` degli stream** (1 per flusso, 6 in tutto): tenute, ma ridotte a ciò che è di tollgate. Dei plugin resta solo `tollgate` (prima 18); i server MCP sono vuoti (prima 7). Di skill, agenti e comandi restano solo quelli `tollgate:…` (23 skill e 23 comandi su 212 e 291, 21 agenti su 43). Dagli strumenti sono tolti gli 8 strumenti MCP. Il percorso della memoria e quello del socket sono sostituiti con «[tolto dalle evidenze]». Ogni riga ridotta ha un campo `nota` che lo dice («riga ridotta: tolti plugin, skill, server MCP, agenti e comandi non di tollgate»). Restano la versione di Claude Code, il modello, il modo dei permessi e gli strumenti di Claude Code.
- **Righe tolte dagli stream.** Le righe `hook_started` e `hook_response` dei `SessionStart` degli altri plugin: 62 righe in tutto (10 in ciascun flusso, 12 in `passo1`, dove tollgate non aveva ancora un lavoro attivo e quindi non resta nessuna riga `SessionStart`). Resta in ogni altro flusso la coppia dell'hook di tollgate («lavoro #1 (L2), fase …»). Poi i dati dell'account, che non servono alla prova: le 15 righe `rate_limit_event` (uso della quota e suo azzeramento) e i 6 campi `credential_expires_at` dei messaggi `result`. Dopo le modifiche `togli-pagine` è stato ripassato sui sei stream (0 risultati) e ogni riga di ogni stream è JSON valido. Le righe tolte spostano i numeri di riga: quelli citati in questo rapporto sono quelli degli stream committati.
- **Restano**, perché non identificano l'utente né la sua macchina: gli id degli hook, dei messaggi e dei blocchi, gli id degli agenti, le righe vuote o `{}` degli hook `PreToolUse`, `PostToolUse`, `Stop` e `UserPromptSubmit` (anche di altri plugin, senza nomi), le firme dei blocchi di ragionamento, gli SHA dei commit della prova, il numero di utente di sistema nel percorso `/tmp/claude-1000/…`, il percorso `/home/USER/.claude/projects/-tmp-tollgate-b1-flow…/` dei risultati salvati dagli strumenti, l'indirizzo finto `prova@example.com` dell'autore dei commit della prova (in un `git show` dello stream di `passo5`). Restano anche i nomi che sono testo di tollgate: `superpowers:writing-plans` nella skill `spec-audit`, `context7:` nel formato della nota di ricerca, `agent-skills` tra le fonti di `rules-security` lette da un revisore, e `docs/superpowers/…` nei percorsi. Resta infine `superpowers:test-driven-development`, la skill che gli implementatori hanno chiamato su richiesta del loro testo (solo il nome e «Launching skill», senza il testo della skill).

Controllo (con `/usr/bin/grep -ra` e con script Python sulla cartella `evidenze/c2/flusso/` e su questo rapporto; valori cercati non riportati):

| Cercato | Dove | Occorrenze |
|---|---|---|
| nome utente (ricavato a runtime) | `docs/verifiche/evidenze/c2/` e questo rapporto | 0 |
| nome dell'host (ricavato a runtime) | `docs/verifiche/evidenze/c2/` e questo rapporto | 0 |
| `/home/` seguito da qualcosa di diverso da `USER` | `docs/verifiche/evidenze/c2/` | 0 |
| i nomi delle cartelle dell'utente (della sua cartella personale e delle cartelle che contengono il repo), ricavati a runtime e mai scritti | `docs/verifiche/evidenze/c2/` e questo rapporto | 0, tolti due falsi positivi (il nome di un programma e `README.md`) |
| i prefissi di token di API e di GitHub (`sk-ant`, `ghp_`, `github_pat_`, `gho_`, `ghs_`) e le forme di JWT | `docs/verifiche/evidenze/c2/` e questo rapporto | 0 |
| cartelle dei plugin dell'utente (`.claude/plugins`) e percorso del socket (`/run/user`) | `docs/verifiche/evidenze/c2/` | 0 |
| nomi di plugin, server MCP, skill e agenti di terzi presi dalla riga `init` originale | `docs/verifiche/evidenze/c2/` | solo quelli elencati sopra tra i «Restano» |
| indirizzi e-mail | `docs/verifiche/evidenze/c2/` | solo `noreply@anthropic.com` e `prova@example.com` |
| gli id di sessione reali (ogni `session_id` degli stream e ogni `session` degli eventi è `SESSIONE-n` o assente) | `docs/verifiche/evidenze/c2/` e questo rapporto | 0 |
| stringhe lunghe da 60 caratteri in su | `docs/verifiche/evidenze/c2/` | solo percorsi della prova, firme dei blocchi di ragionamento e righe di separazione |
