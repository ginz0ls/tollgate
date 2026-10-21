# Revisione finale del ramo `p3c-percorso-l2` (8ea0f39..d71f48d)

Revisore: opus, sola lettura. Metodo: `requesting-code-review/code-reviewer.md`, con la spec rev 24 come autorità. Revisione fatta in più passate: codice nuovo di `bin/` letto per intero (`audit.py`, `l2acts.py`, `l2tree.py`, `audits.py`, `audit_round.py`, `apply.py`, `approvals.py`, `specdoc.py`, `auditrules.py`), diff di `violations`, `scope`, `phases`, `subagents`, `start`, `adopt`, `finishcheck`, `openpr`, `actapply`, `checkpoint`, `sync`, `taskcmd`, `finalreview`, `post_edit`, `writes`, `commit`; skill `spec-audit`, `reopen`, `approve`, `start`; spec 6.2, 8.4, 12.3, 12.4. I test sono stati letti per campione (Review Focus 1-6, `test_criteria_p3c.py`). Esito della suite: in fondo.

## Punti di forza

- La decisione di `prepare` è una funzione pura (`_decide_spec`/`_decide_plan`) usata da `prepare`, `peek` e `decline`: lo stato mostrato da `status` e quello eseguito non possono divergere.
- I giri hanno un'identità solida: un solo giro aperto, `code` nel brief, `started >= opened` in `_common.awaiting_audit`, `superseded` fuori dai conteggi e dalla matrice (`audits.rounds`, `last_closed`). Il report tardivo di un giro superato non tocca il giro nuovo (`apply._audit_report` riverifica `stage = 'open'`).
- Le sospensioni si decidono dal DB, non dal testo del blocco (`l2acts.suspend_on_resolve`, D6), e lo `0` del rifiuto del costo si legge con `in` (D17).
- La lettura «a HEAD» con `committed_blob` (HEAD uguale al worktree) chiude la classe di guasti di P3b sul documento non committato.
- Testo non fidato: titoli delle fette, messaggi degli agenti e titoli dei task sempre in un recinto con `DATA_NOTE`; i problemi del JSON nominano i campi, mai i valori; intestazioni scritte con `render_*` che rifiutano a capo e virgolette.
- `subagents.in_use` condivisa da `sync` e `reopen` (D5), config caricata solo se serve.
- Strati rispettati (`tests/test_layers.py` verde), nessun letterale `tollgate audit …` nudo nei messaggi di `bin/`.

## 1. Rilievi

### Critical

Nessuno.

### Important

**I-1. `audit prepare` (fase `plan`) legge l'approvazione della spec con `spec_blob=None`: con due approvazioni della stessa spec rifiuta a torto una fetta successiva.**

- Dove: `bin/tollgate_flow/audit.py:325-337` (`_spec_approval_current`, riga 329: `locate_spec_approval(..., spec_blob=None)`). Lo stesso passo vale per `peek` (`audit.py:547-575`), quindi anche `status` e il checkpoint danno il passo sbagliato.
- Sequenza (due modi reali):
  1. Spec a tre fette approvata dall'issue 3 (`reviews/3/spec-approval.md`, `sha` = X) e unita. Fetta 2, issue 9: `start 9 --spec S`, poi `/tollgate:reopen spec`, la spec corretta diventa Y, giri, `approve spec` (`reviews/9/spec-approval.md`, `sha` = Y), PR unita. Fetta 3, issue 12: `start 12 --spec S` trova l'approvazione di 9 (`_slice` cerca prima con il blob) e parte in `plan`. Il coordinatore scrive il piano e lancia `audit prepare`: `locate_spec_approval(files, spec_blob=None)` restituisce la prima candidata per numero d'issue, cioè `reviews/3/` con `sha` = X; `is_current(X, Y)` è falso e il comando rifiuta con «spec cambiata dopo approve spec: /tollgate:reopen spec».
  2. Fetta 2 già in `execution`; nel frattempo sul predefinito un'altra fetta ha riaperto e corretto la spec; `/tollgate:sync` porta la spec a Y; `finish check` segnala `plan-approval.md` su una spec diversa; `reopen plan` → fase `plan` → `audit prepare` rifiuta come sopra, anche se l'approvazione corrente (della fetta che ha corretto la spec) esiste nell'albero.
- Riprodotto: repo git con `reviews/3/spec-approval.md` (sha vecchio) e `reviews/9/spec-approval.md` (sha attuale), lavoro dell'issue 12. `audit._spec_approval_current` rifiuta con «spec cambiata dopo approve spec: /tollgate:reopen spec»; `l2acts._spec_approved` sugli stessi file accetta. Script di prova in `/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/7559b7f5-d4d4-4aa4-9695-4b6c2897bf5d/scratchpad/probe1/`.
- Perché è un difetto: spec 6.2 (paragrafo «Dove sta l'approvazione di una spec», riga 309) dice che per una fetta successiva vale l'approvazione con `sha == spec_blob`, e che con `spec_blob = None` basta il `path` solo dove serve sapere se esiste (il blocco di `locked_docs`). `approve plan` lo fa già (ruling del giro di correzione del Task 7, decisione 13); `audit prepare`, `peek`, `approve plan`, `finish check`, `open-pr` e `adopt` devono dare la stessa risposta sullo stesso albero, e qui due di loro divergono. Il lavoro non resta bloccato per sempre, ma l'unica uscita indicata (`reopen spec`) costa un nuovo audit completo della spec, che è già approvata.
- Correzione: in `_spec_approval_current` cercare prima con `spec_blob=spec_blob` e solo se manca con `None` (per scegliere tra «committa…», «spec cambiata…» e «nessuna approvazione»), come fa `l2acts._spec_approved`. Meglio ancora un unico helper in `l2tree` (per esempio `l2tree.spec_approval_state(wt, "HEAD", work, spec_blob)`) usato da entrambi, così la regola sta in un punto solo.
- Test: in `tests/test_audit_prepare.py` (o `test_criteria_p3c.py::LaterSliceTest`) un banco con due `spec-approval.md` della stessa spec in `reviews/3/` (sha vecchio) e `reviews/9/` (sha attuale) sul predefinito, `start 12 --spec`, piano committato: `audit prepare` apre il giro `plan-adversarial` invece di rifiutare, e `peek` non dice «reopen spec». Più un test unitario dell'helper condiviso con le tre combinazioni (propria superata più altra corrente, sola altra superata, nessuna).

### Minor

**m-1. In `approval` `audit prepare` e `approve plan` si rimandano a vicenda.** `audit.py:418-424` e `489-490`: in `approval` `prepare` stampa sempre «chiedi all'utente /tollgate:approve plan» senza guardare piano e spec; `l2acts.py:207-209` rifiuta con «il piano o la spec sono cambiati dopo l'ultimo giro dell'avversario: lancia audit prepare». Sequenza: fase `approval`, il piano o la spec cambiano in HEAD per una via che i guardrail non coprono (Bash, `git checkout -- <file>`, oppure `sync` su un piano toccato altrove). Nessuno dei due messaggi indica l'uscita vera, `/tollgate:reopen plan`. Correzione: in `approval` `prepare` (e `peek`) verificano blob del piano e della spec contro l'ultimo giro e, se diversi, rifiutano con «riapri con /tollgate:reopen plan»; il rifiuto di `approve plan` in `approval` dice lo stesso. Test: `test_audit_prepare.py`, fase `approval` con il piano cambiato in HEAD → rifiuto che nomina `reopen plan`.

**m-2. Dopo un DB perso la numerazione dei giri riparte da 1 e l'hook sovrascrive report già committati.** `audits.py:42-43` numera dal DB; `apply.py` `_audit_report` scrive `reviews/<N>/<kind>-<n>.md` con `os.replace`. Sequenza: L2 in `plan` con `plan-adversarial-1.md` e `-2.md` committati, DB perso, `adopt` (fase `plan` perché manca `plan-approval.md`), `audit prepare` apre il giro 1, l'hook rimpiazza il report 1 della vita precedente. Il file è protetto e lo scrivono solo gli hook, ma la traccia dell'audit nel ramo cambia senza avviso (la storia di git resta). Correzione: `open_round` parte da `max(numero nel DB, numero più alto dei report di quel tipo in reviews/<N>/ a HEAD) + 1`, oppure `adopt` lo semina. Test: dopo `adopt`, il primo giro ha numero maggiore dei report presenti.

**m-3. `adopt` dopo `reopen` con il documento ancora identico ripristina la fase precedente alla riapertura.** `adopt.py:225-242`: un `plan-approval.md` (o `spec-approval.md`) con lo `sha` uguale al documento vale come prova anche se il lavoro era stato riaperto (spec 8.4: «le approvazioni restano come storico e non valgono più»). Effetto limitato: il documento è proprio quello approvato, e l'utente può riaprire di nuovo. Da annotare in 12.4 come limite, o da registrare la riapertura nel ramo (per esempio un `reopen` nell'intestazione). Rinviabile.

**m-4. `spec_path` e `plan_path` si registrano una volta sola e nessun comando li cambia.** `audit.py:246-256` registra il primo file nuovo in ordine alfabetico sotto `specs/` (lo stesso per il piano con `find_plan`, e `post_edit` per `plan_path`); `reset_plan` e `reopen` li lasciano (conforme a 6.2 e 8.4). Se il modello ha scritto due spec nel ramo (la prova reale mostra che scrive spec sue), o rinomina il piano, l'unica via è rimettere il contenuto sotto il nome registrato; i rifiuti («la spec X non è nel ramo») non lo dicono. Correzione minima: il rifiuto di un documento registrato ma assente nomina il percorso registrato e dice che il nome non si cambia. Rinviabile.

**m-5. Testi con «audit prepare» senza il programma.** `audit.py:49-50` (`STEPS["resolve"]`: «oppure correggi e rilancia audit prepare dopo il resolve»), `l2acts.py:113-115` e `211-213` («correggi … e rilancia audit prepare»): il vincolo globale vuole `program_command` in ogni comando scritto in un messaggio. Il passo `resolve` è citato alla lettera dalla skill e dal test del contratto, quindi va cambiato insieme. Test: `test_skill_contract` e un test che ogni «audit prepare» nei messaggi di `l2acts` sia preceduto da `program_command`.

**m-6. Il passo `resolve` presenta due strade che passano entrambe per la sospensione.** `audit.py:49-50`, `skills/spec-audit/SKILL.md` («I tetti»), spec 6.2 punto 6: «correggi e rilancia dopo il resolve» scrive comunque la sospensione; per le lenti è definitiva. Conforme alla spec, ma l'utente può credere di non sospendere scegliendo la seconda strada. Basta una frase nella skill («in entrambi i casi il resolve sospende; per le lenti è definitivo»).

## 2. Triage delle 41 righe `minor (deferred)`

| # | Esito | Motivo |
|---|---|---|
| 1 | chiusa | Corretta nel giro 1 del Task 1: `docs/verifiche/2026-10-20-p3c-verifiche.md:12` cita `handbackReport`. |
| 2 | rinviabile a P4 | Solo messaggi in più quando il piano è già superato; il gate rilegge `check_l2`. |
| 3 | rinviabile a P4 | `plan_path` è registrato una volta e `is_current` confronta il blob; serve al gate, che legge i file senza DB. |
| 4 | rinviabile a P4 | Conforme a D15; da ricordare nel gate. |
| 5 | chiusa/nessuna azione | I file li scrive solo `render_approval` con un intero. |
| 6 | chiusa/nessuna azione | Intestazioni scritte solo dalla CLI. |
| 7 | rinviabile a P4 | Test più stretti quando il gate userà `check_l2`. |
| 8 | chiusa/nessuna azione | `1.0` uguale a `1` non apre nessuna via: il giro resta quello. |
| 9 | chiusa/nessuna azione | L'unico chiamante passa sempre i valori del giro. |
| 10 | chiusa/nessuna azione | Esiti scritti solo da `auditrules.outcome`. |
| 11 | rinviabile a P4 | La spec 6.2 punto 3 elenca `v` nella riga: da richiedere quando servirà una versione 2. |
| 12 | rinviabile a P4/P5 | Pulizia; `close_round` ha un solo chiamante che passa valori calcolati. |
| 13 | rinviabile a P5 | Solo posizione del test. |
| 14 | chiusa/nessuna azione | I chiamanti passano `HEAD` o uno SHA. |
| 15 | rinviabile a P5 | Copertura di un caso già verificato a mano. |
| 16 | rinviabile a P4 | Il brief è un file letto dall'agente, non un comando; percorsi già filtrati da `_check_path`. |
| 17 | chiusa | `skills/spec-audit/references/dimensioni.md` esiste e un test ne controlla il percorso (giro 1 del Task 13). |
| 18 | da correggere prima del merge | Costo minimo (catturare anche `ValueError`, o `errors="surrogateescape"`): oggi resta un `.tmp` in `reviews/<N>/`, protetto e quindi non rimovibile dal coordinatore, che finirebbe nel commit con `git add` della cartella. |
| 19 | rinviabile a P4 | Il blob del giro è in HEAD e si legge; il gate ricontrollerà il pitch. Meglio fail-closed (un `major` «spec non leggibile») quando si tocca il modulo. |
| 20 | rinviabile a P4 | Il giro resta aperto e `prepare` lo ristampa: nessun lavoro fermo. |
| 21 | chiusa | Il Task 15 applica gli atti con `act apply` dal programma vero (`test_criteria_p3c.py`). |
| 22 | rinviabile a P4 | Coperti a pezzi (`test_plan_round_cap_after_two`, `test_plan_cap_uses_configured_threshold`, Review Focus 6 sulla spec); la catena intera del piano manca ancora. |
| 23 | chiusa/nessuna azione | Solo ambiente di test. |
| 24 | rinviabile a P5 | Refactoring preesistente. |
| 25 | rinviabile a P5 | Duplicazione di testo. |
| 26 | rinviabile a P5 | Il codice regge (`reset_plan` idempotente). |
| 27 | rinviabile a P5 | Scorciatoie del banco dichiarate. |
| 28 | rinviabile a P5 | Stile. |
| 29 | rinviabile a P4 | `peek` con `NEEDS_CONFIRM` dice solo «lancia audit prepare», che poi chiede la conferma: nessun errore, solo un passo meno chiaro. |
| 30 | chiusa/nessuna azione | Docstring lunga. |
| 31 | chiusa/nessuna azione | Solo test. |
| 32 | chiusa/nessuna azione | Preesistente, `tests/run` funziona. |
| 33 | chiusa/nessuna azione | Conforme alla riga 71 e al ruling sull'instradamento. |
| 34 | rinviabile a P4 | Il rifiuto è chiaro; manca solo il test. |
| 35 | chiusa/nessuna azione | `--force` vi compare come divieto. |
| 36 | rinviabile a P5 | Testo della skill, già rivisto a mano. |
| 37 | chiusa/nessuna azione | Dichiarato nel rapporto; nessun file nel repo. |
| 38 | da correggere prima del merge | Rapporto committato: backtick rotti alla riga 5 (verificato) e percorsi della prova sbagliati; costo minimo e il documento è la prova del criterio. |
| 39 | rinviabile a P4 | Da verificare alla prossima prova reale (ruling sul Task 14). |
| 40 | da correggere prima del merge | La riga 269 del piano principale dice che le parti «Resta a P3c» sono «annotate nelle loro righe», ma la riga 225 (tabella P3a) ha ancora «(P3c)» senza annotazione. Una parola. |
| 41 | rinviabile (dopo il merge) | Da portare in `docs/sdd/` come previsto. |

Sintesi: 3 da correggere prima del merge (18, 38, 40, tutte a costo minimo); 22 rinviabili (P4: 2, 3, 4, 7, 11, 12, 16, 19, 20, 22, 29, 34, 39; P5: 13, 15, 24-28, 36; dopo il merge: 41); 16 chiuse o senza azione (1, 5, 6, 8, 9, 10, 14, 17, 21, 23, 30-33, 35, 37).

## 3. Valutazione delle `Ruling:`

Nessuna ruling mi pare sbagliata. Note:

- **D3** (da dove si legge l'approvazione) è giusta; l'applicazione non è uniforme: `audit prepare` in `plan` passa `spec_blob=None` dove `approve plan` (dopo il giro 1 del Task 7) passa il blob. È l'origine di I-1. Costo della ruling come scritta: nessuno; costo dell'applicazione: I-1.
- **D14** (agente tardivo di un giro superato trattato come sola lettura comune) regge solo con il primo piano imposto dalla skill. Con un agente in background e una correzione nel frattempo si apre un `needs_you` spurio: costo basso e dichiarato; da tenere presente se P4/P5 introdurranno lanci in parallelo.
- **Ruling sul Task 14, giro di correzione senza nuova prova reale**: accettabile per il costo, ma lascia non provati con il modello lo shim di `gh` e l'esito propagato (riga 39). Va ripresa alla prossima prova reale (P4), come già annotato.
- **D2** (variante B) è coerente con 6.2 punto 4: la conferma sul blob finale resta condizione di `approve spec`. Nessun costo nascosto trovato.
- **D6** e **D17**: verificate sul codice (`suspend_on_resolve`, letture con `in`). Corrette.

## 4. Considerati e messi da parte

- `bash_rules` non applica `locked_docs` né `_NO_PLANS` alle scritture da Bash (si può cambiare la spec bloccata con `sed -i`): preesistente e fuori dalla garanzia dei guardrail locali (spec 1.2); il gate di P4 ricontrolla `sha` e approvazioni.
- File di approvazione falsificabili con comandi git che non sono redirezioni: preesistente, è materia del gate (P4), che legge i file senza il DB.
- Livello di un lavoro adottato ricalcolato dal diff (una fetta successiva senza percorsi sensibili tornerebbe sotto L2 prima della PR): preesistente (12.4), e 12.4 rev 24 dichiara già il caso della fetta successiva adottata senza piano approvato.
- Un ciclo a lenti con soli `moderate` costringe a cambiare la spec per proseguire: è la definizione di ciclo vuoto in 6.2, non un difetto del codice.
- Lettura della config di `peek` con `load_config_at` invece di `load_config`: differenza solo con `TOLLGATE_TEST_CONFIG` (riga 23).

## 5. Suite

`python3 -B -m unittest discover -s tests -t .` (Python 3.13.5) su d71f48d: 1736 test, OK, in 557 s; `git status` pulito dopo l'esecuzione. Con `python3.11` non l'ho rilanciata: il ledger la dà verde al Task 15.

## 6. Verdetto

**Pronto per il merge: sì, con correzioni.** Nessun Critical. Un Important (I-1) da correggere prima del merge: è piccolo (una ricerca in due passi o un helper condiviso in `l2tree`, più un test), ma tocca proprio la lezione di P3b, cioè due comandi che leggono lo stesso albero e rispondono diversamente. Insieme a I-1 conviene chiudere le tre righe rinviate a costo minimo (18, 38, 40); i Minor m-1..m-6 possono andare a P4.
