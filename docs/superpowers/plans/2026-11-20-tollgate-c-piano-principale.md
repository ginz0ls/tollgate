# tollgate C: piano principale

Data: 20 novembre 2026.
Progetto: `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md` (approvato dall'utente il 20 novembre 2026), da qui «il progetto». Spec del nucleo: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 35. Progetto di B e catalogo dei profili: `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` e `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, per le fette dei profili.

Il progetto dice **cosa** fa C e perché; questo documento dice **in che ordine** si costruisce, **cosa consegna** ogni fetta e **quando C è finito**. Il codice e i passi stanno nei piani delle singole fette. È magro come il piano principale di B (`docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`), che resta il modello di forma.

Stato (20 novembre 2026): piano scritto; **C1 pronta da eseguire** (piano `2026-11-20-tollgate-c1-tracciamento-locale.md`, con `-esecuzione.md`, `-brief-sessione.md` e `-brief-goal.md`). Nessuna fetta eseguita. Suite su `main`: 4180 test verdi su Python 3.11 e 3.13.

---

## 1. Regole

1. **Un piano per fetta, scritto al suo turno.** Il piano di C(n+1) si scrive quando le fette da cui dipende sono unite su `main`, partendo dal codice reale e dalle interfacce che hanno prodotto davvero. La sezione 3 dà i nomi indicativi: valgono quelli del codice.
2. **Si costruisce con Superpowers** (subagent-driven-development), su un ramo e un worktree per fetta, con lo scan pre-flight, la revisione di ogni task, la revisione finale e il merge su `main` solo con l'OK dell'utente. È lo stesso metodo di B1-B8.
3. **Una correzione della spec del nucleo** scoperta in una fetta diventa una nuova revisione della spec, scritta dall'ultimo task della fetta. Due fette che girano insieme (sezione 2) prendono il numero di revisione al momento del merge: la seconda che si unisce riparte dalla revisione della prima. Una correzione del progetto di C si scrive nel progetto, con la data e il motivo, solo per le scelte marcate «mia scelta»; quelle marcate «utente» si cambiano solo con l'utente.
4. **Le regole dei profili le approva l'utente** (progetto 11, come B: progetto di B, sezione 5). Le fette C2 e C3 non sono finite finché la pagina del profilo non è approvata; il codice si può unire prima, con il profilo spento.
5. **Niente GitHub vero nei test** (progetto 13): il `gh` dei test è `tests/fakegh.py`. GitHub vero solo nelle sonde e nella prova delle fette C4-C6, sul repo di prova privato dell'utente, e solo dal controller.
6. **Questo documento si aggiorna alla chiusura di ogni fetta**: stato in testa, riga della fetta nella sezione 2, nomi reali nella sezione 3, rinvii nella sezione 8.

---

## 2. Sequenza

| Fetta | Obiettivo | Richiede | Consegna | Finita quando |
|---|---|---|---|---|
| **C1 Tracciamento locale** | Tutto ciò che il gestionale vorrà leggere, registrato nello stato locale, senza GitHub (progetto 2, obiettivi 1, 4, 7, 9.2, 9.3, 9.6) | `main` con questo piano e i quattro file del piano di C1 | Migrazione 7 dello stato (`work_items.size`, `size_by`, `slices`); tipi di evento nuovi `size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost`; la presa della taglia (regole semplici, punto unico) con la proposta all'avvio, alla registrazione del piano e ad `approve spec <n>`, e l'atto `approve size`; il comando `ruling add`; le fermate lette dagli hook di `AskUserQuestion`; il costo in token per subagente; ogni decisione sui rilievi come evento; la storia che non si cancella (archivio prima della potatura, «mai» per difetto); la fotografia `tollgate snapshot` con versione; la pagina `docs/uso/gestionale.md`; una prova reale corta; spec del nucleo alla revisione 36 | Tabella «Copertura» del piano di C1 come test; prova reale con gli eventi nuovi; revisione finale senza `critical` né `important` aperti |
| **C2 Profilo `security`** | Il profilo del catalogo, costruito come i profili di B, con **Fable** (`claude-fable-5-2`) dove serve giudizio (progetto 11) | `main` (indipendente dalle altre fette: può girare anche prima di C1 o insieme a C4, in un'altra sessione) | Fonti verificate e copiate con la licenza; `skills/rules-security/SKILL.md` con le regole e le fonti; pagina `docs/profili/security.md`; frammento `templates/profiles/security.toml` (percorsi del catalogo, L2); `implementer-security`, `reviewer-security`, `final-security`; tabella delle precedenze con gli altri sei profili, un test ciascuna; prova reale | Pagina approvata dall'utente; profilo acceso; revisione del piano e revisione finale con Fable |
| **C3 Profilo `ci`** | Il profilo dei workflow, con lo stesso specialista finale di `security` (progetto 11) | C2 (usa `final-security` e `rules-security`) | `skills/rules-ci/SKILL.md`, pagina `docs/profili/ci.md`, frammento `templates/profiles/ci.toml` (`.github/workflows/**` esclusi i `tollgate-*`, `.gitlab-ci.yml`, `scripts/ci/**`; L2); `implementer-ci`, `reviewer-ci`; l'eccezione per `ci` a `init.EXCLUDED_PREFIXES` (dalla rev 31 `.github/workflows/` non accende nessun profilo); precedenze; prova reale | Pagina approvata dall'utente; profilo acceso; revisione con Fable |
| **C4 Ponte con GitHub** | Le due bacheche, la coda che non blocca, più computer, l'allineamento, gli avvisi (progetto 4, 7, 8) | C1 | Il token separato delle bacheche e `/tollgate:setup` che lo configura; la coda delle scritture nello stato locale (tentativi, attesa crescente, idempotenza, evento `sync`); la macchina che possiede ogni lavoro; la bacheca principale (una scheda per repo, due percentuali, fase, cose che aspettano l'utente, ultima attività, CI) e la bacheca di progetto (lavori medi e grandi, colonne, eventi mostrabili); il controllo di ciò che va su GitHub (un test che fallisce su un campo della lista «non va mai» del progetto 7); gli avvisi con l'assegnazione; il comando di allineamento e il controllo all'avvio; il campo `queue` della fotografia; `[board]` in `tollgate.toml` per spegnere tutto | Test con `fakegh` esteso ai Projects; sonda sul repo di prova dell'utente per i fatti che solo GitHub vero dà (permessi del token, sezione 4); revisione finale chiusa |
| **C5 Piano a fette** | Il piano a fette lo crea tollgate (progetto 5) | C4 | Le dipendenze in `## Fette previste` (forma `3. Titolo (dopo 1, 2)`); dopo `approve spec <n>` con n > 1 le sotto-issue 1..n con le dipendenze, attraverso la coda di C4; l'issue madre aperta fino all'ultima fetta e chiusa da tollgate; `prbody` con `Closes #<sotto-issue>` per un lavoro grande (e il gate che legge il blocco JSON); `start --spec` che rifiuta una fetta con una dipendenza non unita e dice quale; il campo `depends_on` della fotografia (`slices` c'è da C1) | Test senza rete; revisione finale chiusa |
| **C6 Storia, prova vera e chiusura** | Recuperare i lavori già fatti (progetto 9) e provare C dal vivo (progetto 13) | C1-C5 (C2 e C3 unite o rinviate dall'utente) | Il comando di recupero della storia (da commit di unione, `docs/sdd/`, piani principali, `docs/verifiche/`, issue e PR chiuse; ripetibile, senza inventare); la prova vera sul repo di prova privato dell'utente (lavoro piccolo, medio, grande con tre fette, GitHub giù simulato, issue chiusa a mano, recupero della storia, una fermata con `AskUserQuestion` vista dagli hook) con il rapporto in `docs/verifiche/`; spec del nucleo, progetto di C e questo documento con lo stato finale | Sezione 5 di questo documento |

**Ordine consigliato:** C1, C2, C3, C4, C5, C6. C2 e C3 non dipendono dal tracciamento: possono andare prima di C1 o in parallelo a C4 e C5, **in un'altra sessione e su un altro ramo** (due implementatori sullo stesso ramo mai), con la regola 3 per il numero della revisione della spec. C4, C5 e C6 sono in fila: ognuna usa ciò che la precedente ha prodotto.

---

## 3. Interfacce tra le fette

I nomi li fissa la fetta che li produce; la successiva li copia dal codice, non da qui.

| Produce | Consuma | Contratto (indicativo) |
|---|---|---|
| C1 | C4, C5, C6 | **Eventi.** `events.EVENT_TYPES` con `size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost` (busta 1 invariata); `data` come nel piano di C1, decisioni 2-7. Le bacheche di C4 mostrano solo campi derivati da questi eventi, mai il loro testo (progetto 7) |
| C1 | C4, C5 | **Taglia.** `work_items.size` (`small`, `medium`, `large`) e `size_by` (`rules`, `user`); `tollgate_analysis.worksize.propose(signals) -> Proposal` è la presa unica (progetto 3.3); `tollgate_core.sizes.decide(...)` registra e non scende mai. **L'autorizzazione di C5 a creare le sotto-issue è `work_items.slices > 1` scritto da `approve spec <n>`** (il sì del progetto 3.2, sulla spec approvata da cui il progetto 5 legge le fette); `approve size grande` è solo la scelta dell'utente sulla taglia e non basta |
| C1 | C5 | **Fette.** `work_items.slices` scritto da `approve spec <n>` |
| C1 | C4, C6 | **Fotografia.** `tollgate snapshot` → JSON `{"v": 1, ...}`; C4 aggiunge `queue`, C5 aggiunge `depends_on` alle fette: un campo nuovo non cambia `v` (progetto 10). `tollgate_analysis.turn.waiting_on(facts) -> str` (`user`, `agent`, `decision`) è «a chi tocca» per le schede di C4 |
| C1 | C6 | **Storia.** Gli eventi non si cancellano per difetto; con `[retention] events_days > 0` gli eventi vecchi vanno prima nell'archivio JSONL della cartella di stato. Il recupero di C6 marca i propri eventi come recuperati (forma a C6) |
| C2 | C3 | **Specialista finale.** `agents/final-security.md` e `skills/rules-security/SKILL.md` approvata; `ci` li dichiara come `final_specialist` e `reviewer_skills` (catalogo, riga `ci`) |
| C4 | C5 | **Coda.** Un'API della coda (per esempio `ghqueue.enqueue(conn, kind, key, payload)`) con la chiave d'idempotenza stabile (`repo_key`, `issue`, tipo); la creazione di issue e sotto-issue passa da lì, con i titoli come dato in un file o in JSON, mai in una riga di comando (progetto 5, «Titoli non fidati») |
| C4 | C5, C6 | **Bacheche.** Le funzioni che creano e aggiornano la scheda di un lavoro e quella del repo, e il calcolo dei campi del repo da GitHub (progetto 8, «più computer») |
| C4, C5 | C6 | **Recupero.** C6 crea le schede dei lavori passati con le stesse funzioni, senza riscrivere lo stato locale (progetto 9) |

---

## 4. Copertura del progetto

| Punto del progetto | Fetta |
|---|---|
| 1 Perché (tollgate primo modulo del gestionale; tracciare subito) | C1 (tracciamento), C4-C6 (bacheche e storia) |
| 2 Obiettivo 1 (tracciare tutto, `tollgate events`) | C1 |
| 2 Obiettivo 2 (due bacheche) | C4 |
| 2 Obiettivo 3 (il piano a fette lo crea tollgate) | C5 |
| 2 Obiettivo 4 (proporzionalità) | C1 (taglia, locale e gratis); C4 (un lavoro piccolo aggiorna solo la scheda del repo) |
| 2 Obiettivo 5 (niente di delicato su GitHub) | C4 (test di ciò che va su GitHub); C5 e C6 lo rispettano |
| 2 Obiettivo 6 (pronto per i ruoli, a chi tocca) | C1 (`turn.waiting_on`); C4 (campo della scheda, permessi lasciati a GitHub) |
| 2 Obiettivo 7 (decisioni sui rilievi) | C1 |
| 2 Obiettivo 8 (allineamento) | C4 |
| 2 Obiettivo 9.1 (non bloccare mai) | C4 |
| 2 Obiettivo 9.2 (ruling) e 9.3 (costi) | C1 |
| 2 Obiettivo 9.4 (più computer) | C4 |
| 2 Obiettivo 9.5 (storia) | C1 (la storia non si cancella); C6 (recupero) |
| 2 Obiettivo 9.6 (contratto per il gestionale) | C1 (fotografia e pagina d'uso); C4 e C5 aggiungono campi |
| 2 Obiettivo 9.7 (avvisi) | C4 |
| 2 Non obiettivi (tabellone, comandi dal gestionale, modello di decisione, eval estesi) | nessuna fetta li costruisce; la presa vuota è di C1 |
| 2 Anti-obiettivi | C4 (GitHub lento non ferma; niente testo interno; aggiornamento dal codice); C1 (niente cerimonia per una cosa piccola); C4 (bacheca e stato allineati) |
| 3.1 Tre taglie | C1 (locale); C4 (cosa fa ciascuna sulle bacheche); C5 (grande) |
| 3.2 Come si sceglie (proposta, grande con `approve spec <n>`, segnali, crescita, atto dell'utente) | C1 |
| 3.3 La presa per un modello di decisione | C1 |
| 4.1 Bacheca principale; 4.2 bacheca di progetto; 4.3 a chi tocca, ruoli, avvisi; 4.4 chi aggiorna, quando, account personale, token | C4 (il calcolo di «a chi tocca» è di C1) |
| 5 Il piano a fette | C5 (con la taglia grande di C1 e la coda di C4) |
| 6 Eventi nuovi: `size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost`, decisioni sui rilievi | C1 |
| 6 Evento `sync` | C4 (lo registra la coda; decisione 2) |
| 6 Comando delle ruling; dove sta il costo; tutto locale; la storia non si cancella | C1 |
| 7 Cosa va su GitHub e cosa no | C4 (il test di controllo); C5, C6 |
| 8 Coda, idempotenza, più computer, allineamento, spento | C4 |
| 9 Recuperare la storia | C6 |
| 10 Contratto per il gestionale | C1 (fotografia e pagina); C4, C5 (campi nuovi) |
| 11 Profili `security` e `ci` con Fable | C2 (`security`), C3 (`ci`) |
| 11 Gli altri profili dopo C | sezione 8, «Dopo C», voce 6 |
| 12 Lasciato a chi costruisce | il piano di ogni fetta; questo documento per la divisione in fette |
| 13 Test senza rete, `fakegh` esteso | C4, C5 |
| 13 Prova vera sul repo di prova | C6 (con una sonda in C4 per i fatti del token) |
| 13 Controllo di ciò che va su GitHub | C4 |
| 14 Vincoli (stdlib, strati, suite, niente modelli nel codice, profili di B intatti, repo pubblico) | ogni fetta |

---

## 5. Quando C è finito

Dal progetto, sezioni 2 e 13, più le regole del nucleo:
- C1-C6 sono unite su `main`, ognuna con la revisione finale chiusa e la suite verde su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`;
- le pagine di `security` e `ci` sono approvate dall'utente e i profili sono accesi; un profilo che l'utente rinvia esce da C e lo dice il rapporto finale;
- la prova vera di C6 è riuscita sul repo di prova privato dell'utente, con il rapporto in `docs/verifiche/`: lavoro piccolo, medio e grande con tre fette, GitHub giù simulato senza che il lavoro si fermi, un'issue chiusa a mano segnalata dall'allineamento, il recupero della storia senza doppioni;
- `tollgate events` e `tollgate snapshot` sono documentati in `docs/uso/gestionale.md`;
- la spec del nucleo, il progetto di C e questo documento hanno lo stato finale; il blocco «Dopo C» (sezione 8) ha l'elenco unico di ciò che resta.

---

## 6. Rischi della sequenza

| Rischio | Effetto | Come si gestisce |
|---|---|---|
| I token a grana fine non danno i Projects di un account personale (pagina ufficiale dei permessi: la sezione «Projects» c'è solo tra i permessi dell'organizzazione) | Il token delle bacheche deve essere classico, con lo scope `project` | Decisione 3: C4 lo verifica con una sonda sul repo di prova e sceglie la forma; se serve uno scope largo (`repo`) è una domanda all'utente, non una scelta di chi costruisce |
| Le sotto-issue o le dipendenze non disponibili per l'account | C5 non può collegare le fette | Le pagine ufficiali non danno restrizioni di piano né di tipo di account (sezione 7): resta un fatto da vedere nella sonda di C4. Se GitHub le rifiuta, C4 si ferma e chiede (scelta «utente» del progetto 5) |
| La forma di `tool_response` di `AskUserQuestion` negli hook non è documentata | Le fermate di C1 senza la risposta | C1 legge le risposte in modo difensivo (decisione 4 del piano di C1) e la prova vera di C6 vede una fermata dal vivo |
| GitHub risponde 500 a corpo vuoto anche sui POST (memoria del progetto) | Doppioni sulle bacheche | La coda di C4 ripete senza controllo solo le scritture idempotenti; le altre si ricontrollano prima di riprovare (progetto 8) |
| C2 e C3 costano più delle altre (Fable dove serve giudizio) | Consumo dell'abbonamento | Fable solo nei punti del progetto 11 (fonti, regole, revisione del piano, revisione finale); gli implementatori meccanici restano sonnet |
| Due fette in parallelo (C2 o C3 insieme a C4 o C5) | Conflitti nella spec e in questo documento | Regola 3; la seconda fetta che si unisce fa il rebase dei soli documenti |

---

## 7. Decisioni di questo piano

Scelte di chi scrive, che l'utente può ribaltare.

1. **Sei fette invece di cinque: `security` e `ci` in due fette.** Il brief proponeva una fetta per i due profili. B ha fatto un profilo per fetta (B3-B7), ogni profilo ha la sua pagina da approvare e la sua tabella delle precedenze, e `ci` ha bisogno di `final-security`, che nasce con `security`. Due profili insieme farebbero una fetta di quindici o più task. Costo: una sessione in più.
2. **L'evento `sync` nasce in C4, non in C1.** È l'evento della coda verso GitHub, e solo la coda sa cosa scrive. C1 non registra eventi che nessun codice emette. Costo: nessuno, un tipo nuovo non cambia la busta.
3. **Il token delle bacheche.** Fatto delle pagine ufficiali (sezione 7): per i Projects di un account personale serve un token classico con lo scope `project`; le sotto-issue, le dipendenze e le assegnazioni chiedono il permesso «Issues» del repo, che il token dell'agente del nucleo ha già. Proposta per C4: un token classico con il solo `project` per le bacheche, e il `gh` già autenticato dell'agente per issue e sotto-issue. Le pagine non dicono se il solo `project` basta ad aggiungere a una bacheca un'issue di un repo privato: lo dice la sonda di C4. Se serve `repo` (accesso pieno a tutti i repo), C4 si ferma e lo chiede all'utente, con il costo spiegato.
4. **Fable** (`claude-fable-5-2`) in C2 e C3 per la verifica delle fonti, la scrittura delle regole, la revisione del piano e la revisione finale; il modello di `final-security` e del revisore di area si decide nel piano di C2 leggendo il catalogo (riga 78: `inherit` per `security`). Le altre fette restano come B: implementatori e revisori dei task sonnet, revisione finale opus.
5. **La prova vera è una sola, in C6** (progetto 13), ma C4 fa una **sonda** sul repo di prova per i fatti che solo GitHub vero mostra (scope del token, sotto-issue, dipendenze, campi dei Projects). Il repo di prova lo crea l'utente (è suo e privato); il piano di C4 dice come.
6. **C1 ha una prova reale corta** con `claude -p` e lo script `spikes/run-b1-flow.sh` (lavoro L1 senza GitHub), come le fette di B: vede `size_decided` e `cost` con le trascrizioni vere. Le fermate non si vedono con `-p` (le domande dirette chiedono una sessione interattiva): restano alla prova di C6.

---

## 8. Rinvii e «Dopo C»

**Dopo C** (elenco unico; riprende il blocco «Dopo B» della sezione 9 del piano principale di B). Ciò che C non chiude, con il motivo. Lo aggiorna ogni fetta alla chiusura.

1. **La regola che manca a `rules-base`** («cerca nel progetto prima di aggiungere», da `s12`; voce 1 di «Dopo B»). Scelta dell'utente del 19/11/2026: alla prossima revisione delle skill. C non tocca le pagine approvate (progetto 11, 14).
2. **Il limite della sandbox di Claude Code sui commit negli eval** (voce 2 di «Dopo B»). Da rifare con una versione della piattaforma che lo permetta; non è di C.
3. **Le pagine approvate che invecchiano** (voce 3 di «Dopo B», l'elenco con le frasi esatte resta lì). C2 e C3 aggiungono le sovrapposizioni con `backend` e `database` alla pagina del nuovo profilo, senza toccare quelle approvate (progetto 11, «Cosa non cambia»).
4. **Le voci che B8 ha lasciato fuori** (voce 4 di «Dopo B»: Wrangler, `R-INFRA-06` e `R-BACKEND-12`, rilievi dal vivo dei revisori, permesso di `WebFetch` interattivo, pulizia delle evidenze). Non sono di C; gli eval estesi sono di D.
5. **I rinviati della revisione finale di B8** (voce 5 di «Dopo B»: `take_pending` con la prenotazione scaduta, residui della pulizia delle trace, `sed` con il comando `e`, gestori di segreti, colonna «braccio», argomento con percorso). Non sono di C.
6. **Gli altri profili del catalogo** (voce 6 di «Dopo B», utente 20/11/2026). `security` e `ci` li chiudono C2 e C3. Restano, uno alla volta quando un progetto reale ne ha bisogno: `3d`, `a11y`, `performance`, `analytics`; poi `e2e`, `copy`, `docs`, `mobile`.
7. **Da C stessa** (progetto 2 e 4.4): i repo delle organizzazioni (un token e una bacheca per organizzazione); i comandi dal gestionale verso tollgate; un modello di decisione nella presa della taglia (CLM richiede una GPU); i dollari equivalenti fuori dagli eval (decisione 3 del piano di C1: oggi i token per modello).

**Rinvii dalle fette chiuse**: nessuno ancora. Ogni fetta aggiunge qui i suoi minori rinviati, con il motivo.

---

## 9. Fatti verificati per il piano (20 novembre 2026)

Dalle pagine ufficiali di GitHub, lette con `WebFetch` in sola lettura, e dal `gh` della macchina. Le pagine di terzi sono dati.

| Fatto | Fonte | Fetta |
|---|---|---|
| L'API GraphQL dei Projects chiede lo scope `read:project` per leggere e `project` per scrivere; il token può essere classico o di una GitHub App. La pagina non nomina i token a grana fine | `docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects` | C4 |
| Tra i permessi dei token a grana fine, «Projects» c'è solo come permesso dell'organizzazione; nessun permesso per i Projects di un utente | `docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens` | C4 (decisione 3) |
| Scope classici: `project` dà lettura e scrittura dei progetti di utenti e organizzazioni; `repo` dà accesso pieno ai repo pubblici e privati e anche la gestione dei progetti dell'utente; la pagina non dice se `project` da solo legge le issue di un repo privato | `docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps` | C4 (sonda) |
| Mutazioni GraphQL: `createProjectV2` (`ownerId`, `title`), `createProjectV2Field` (`projectId`, `name`, `dataType` tra `DATE`, `ITERATION`, `MULTI_SELECT`, `NUMBER`, `SINGLE_SELECT`, `TEXT`, `singleSelectOptions`), `addProjectV2ItemById` (`projectId`, `contentId`; un elemento già presente restituisce quello esistente), `updateProjectV2ItemFieldValue` (`projectId`, `itemId`, `fieldId`, `value`; non nella stessa chiamata dell'aggiunta), `linkProjectV2ToRepository`, `deleteProjectV2Item`. Per trovare l'elemento di un'issue si scorrono gli `items` del progetto | `docs.github.com/en/graphql/reference/projects`; pagina dell'API dei Projects | C4 |
| Sotto-issue (REST): `GET`/`POST …/issues/{n}/sub_issues` (corpo `sub_issue_id`, l'`id` dell'issue e non il numero; `replace_parent`), `DELETE …/issues/{n}/sub_issue`, `PATCH …/sub_issues/priority`, `GET …/issues/{n}/parent`; la sotto-issue deve avere lo stesso proprietario della madre; `sub_issues_summary` con `total`, `completed`, `percent_completed`; al più 100 sotto-issue per madre e otto livelli; nessuna restrizione di piano o di account scritta | `docs.github.com/en/rest/issues/sub-issues`; `docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues` | C5 |
| Dipendenze (REST): `GET`/`POST …/issues/{n}/dependencies/blocked_by` (corpo `issue_id`, l'`id`), `DELETE …/blocked_by/{issue_id}`, `GET …/dependencies/blocking`; `issue_dependencies_summary`; aggiunte e rimozioni rapide possono dare il limite secondario (422 sui POST ripetuti); sotto-issue e dipendenze chiedono il permesso «Issues» (scrittura per i POST) | `docs.github.com/en/rest/issues/issue-dependencies`; pagina dei permessi | C4 (coda), C5 |
| `gh` 2.46.0 ha `gh project` con `create`, `field-create`, `field-list`, `item-add`, `item-create` (scheda bozza), `item-edit` (`--project-id`, `--id`, `--field-id`, `--text`, `--number`, `--date`, `--single-select-option-id`, `--clear`; un campo per chiamata), `item-list`, `link`, `view`; chiede lo scope `project`. Non ha comandi per sotto-issue e dipendenze: si usa `gh api` | `gh project --help`, `gh project item-edit --help` sulla macchina; `cli.github.com/manual/gh_project` | C4, C5 |
| `PostToolUse` riceve `tool_input` e `tool_response` («la forma dipende dallo strumento»); `PreToolUse` può avere il matcher `AskUserQuestion`; `tool_input.questions` è l'elenco delle domande e `answers` mappa il testo della domanda all'etichetta scelta (più scelte unite da virgole). La pagina non descrive `tool_response` di `AskUserQuestion`; nelle trascrizioni di Claude Code di questa macchina il risultato ha le chiavi `questions`, `answers`, `annotations` | `code.claude.com/docs/en/hooks` (sezioni «PostToolUse» e «AskUserQuestion»); una trascrizione locale, letta solo per le chiavi | C1 (decisione 4 del piano di C1) |
