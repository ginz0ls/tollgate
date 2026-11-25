# Ri-revisione del Task 10 (C2), giro di correzione 1

Ri-revisore: Fable, sola lettura. Commit rivisto: `4cf2b97` (diff `86b3dff..4cf2b97`, letto una volta da `review-task-10-fix.diff`). File letti con `git show 4cf2b97:<percorso>`. Nessun test lanciato, nessuna cartella temporanea creata, suite non rilanciata (il report riporta 4516 test verdi sui due interpreti e i tre test mirati verdi).

Riferimenti brevi: «spec» = `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`; «catalogo» = `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`; «piano principale» = `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`; «rapporto» = `docs/verifiche/2026-11-22-c2-prova-flusso.md`. Righe al commit `4cf2b97`.

### Verdetti sui rilievi

**I1. La sezione 16 presenta come segnale delle regole un dato che non lo è** — INDIRIZZATO. `spec:2152`: il modello delle minacce e il raggio d'azione «li chiede per esteso il testo di `agents/implementer-security.md` (sezione «Area `security`», 6.3): provano che il task è andato all'agente dell'area …, **non il precaricamento**»; gli id citati con il contenuto giusto (07, 08, 10, 12) sono un «indizio forte» perché gli agenti elencano solo i numeri; «La prova del precaricamento resta il titolo `isMeta` nelle cinque trascrizioni». Coincide con il rapporto (righe 107-120: punto (a) secondo e terzo trattino, punto (c): due implementatori, due revisori, lo specialista = cinque). Controllato sugli agenti: `agents/implementer-security.md:51` chiede nel campo `done` chi può arrivare al codice e il raggio d'azione; `agents/reviewer-security.md:55` elenca solo i numeri delle regole. Nessuna contraddizione con `spec:508`. Il dato dei giri (4-9 e 4-6 con `outcome: empty`, sette giri, 280.137 token) coincide con il rapporto, «Costi» (riga 142), e con `registro-1/events.jsonl` (vedi m3).

**I2. Il catalogo non dice che sotto `auth/` il lavoro è L2 già senza il profilo** — INDIRIZZATO. `catalogo:40`: «sotto `auth/` il lavoro è L2 già senza il profilo (`levels.sensitive_paths`, spec 11.4): il livello è nuovo per `security/`, `rls/`, `middleware.*`, `proxy.ts`, `proxy.js` e i file trovati per contenuto». Vero contro `bin/tollgate_core/config.py:40` (`"sensitive_paths": ["**/migrations/**", "**/auth/**"]`), contro i sei pattern di `templates/profiles/security.toml:20-35` e uguale a `spec:508` e a `docs/profili/security.md:86`.

**m1. `blocking_rules` indicata come fonte dell'accettazione** — INDIRIZZATO. `spec:509`: «(`rules` dei profili attivi, `profiles.known_rules`; `blocking_rules` decide solo se un rilievo può bloccare, `verdicts.is_blocking`)». Vero: `bin/tollgate_analysis/profiles.py:99-101` (`known_rules` legge `rules`), `bin/tollgate_analysis/verdicts.py:91-101` (blocca un passo del piano, una regola in `blocking_rules`, o una `R-…` fuori da `known_rules`).

**m2. «solo nelle sessioni interattive» e «Se l'account non può usare»** — INDIRIZZATO. `spec:226`: «Se `availableModels` esclude il modello chiesto … (dove il fornitore lo consente) … con un avviso nelle sessioni interattive»; `spec:2147`: «con un avviso nelle sessioni interattive». `docs/uso/comandi.md` non è nel commit.

**m3. «oggi nessun tetto sotto quello dell'audit»** — INDIRIZZATO. `piano:148`: la frase vecchia è tolta; la nuova dice che i tetti aprono un blocco solo per un giro sporco, che i giri puliti non hanno tetto e che ogni correzione chiede un giro nuovo. Vera nella sostanza contro il codice (dettaglio sotto, con un'imprecisione minore nel danno nuovo N1).

Ciò che ho verificato sul codice:
- `bin/tollgate_core/config.py:72`: `spec_rounds = 4`, `plan_rounds = 2`.
- `bin/tollgate_hooks/apply.py:178-192` (`_cap_block`): `done = len(audits.rounds(...))`; il blocco `needs_you` si apre solo se `done >= tetto` **e** `not auditrules.is_clean(counts)`.
- `bin/tollgate_analysis/auditrules.py:33-35`: pulito = `blocker + major == 0` (i `moderate` non sporcano); `:28-30`: `outcome` è `empty` solo se anche `moderate == 0`.
- `bin/tollgate_core/audits.py:92-96`: `rounds` conta i giri chiusi, mai i `superseded`.
- `bin/tollgate_flow/audit.py:180-188` (`adversarial_ok`): l'ultimo giro chiuso deve stare sul blob attuale del documento ed essere pulito o sospeso, quindi un documento cambiato vuole un giro nuovo.
- `bin/tollgate_flow/l2acts.py:347-350`: la sospensione si scrive solo se `len(rows) >= cap` e l'ultimo giro non è pulito.

**Atto dell'utente (`approve rounds`) nella prova: NON era dovuto.** Verificato sui dati, non sul report dell'implementatore:
- `registro-1/events.jsonl`, 15 eventi `spec_audit_round`: spec 1-3 `findings`, 4-9 `empty`; piano 1-3 `findings`, 4-6 `empty`.
- Poiché `findings` comprende anche i soli `moderate`, ho letto i conteggi delle righe JSON dei giri negli stream (`passo1/tentativo-1/claude.jsonl`, `passo3/tentativo-1/claude.jsonl`): spec giro 1 `major` 3, giro 2 `major` 1, giro 3 `major` 0 (`moderate` 1), giri 4-8 solo `minor`, giro 9 zero; piano giro 1 `major` 5, giro 2 `major` 0 (`moderate` 1), giro 3 `major` 0 (`moderate` 1), giri 4-5 solo `minor`, giro 6 zero. Nessun `blocker`.
- I punti in cui il tetto poteva scattare sono il giro 4 della spec (`done = 4`) e il giro 2 del piano (`done = 2`) e tutti i successivi: tutti con `blocker + major == 0`, quindi puliti. Il caso più vicino è il giro 2 del piano, `findings` per un `moderate`, ma pulito per il tetto.
- Conferme: nessun evento `veto` né blocco in `events.jsonl`; i tre eventi `act` sono `approve spec`, `approve plan`, `finish`; `registro-1/status.json` ha `blocks: []`.
Conclusione: il codice si è comportato come dice `spec:420`; nessun difetto del prodotto. Resta vero, come fatto di progetto e non come difetto, che i giri puliti non hanno tetto: il loro numero dipende da quante volte la sessione corregge il documento (è la voce 9 di «Dopo C», da tarare in D).

**m4. Voce di `database` al presente su `AREAS` e `FINAL_AREAS`** — INDIRIZZATO. `spec:507`: «`AREAS` … era, fino alla rev 36, (…) (dalla rev 37 anche `security`, voce sotto)»; «`FINAL_AREAS`, che era `("database",)` fino alla rev 36».

**m5. La riga originale del catalogo non più riportata** — INDIRIZZATO. `catalogo:40`: «La riga dell'8/10/2026, citata come «riga 40 del catalogo» dal rapporto approvato delle fonti, era: `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**`, L2, specialista sì». Uguale alla riga 40 del catalogo su `main` (pattern, ordine, L2, sì).

**m6. La voce pronta della sezione 8 riceve solo i minori della revisione finale** — INDIRIZZATO. `piano:165`: «I minori che la revisione finale di C2 lascerà rinviati e i minori differiti dei task che il triage tiene si aggiungono qui».

**m7. La riga «C2 → C3» non nomina le skill del revisore di `ci`** — INDIRIZZATO. `piano:49`: «C3 decide anche le skill del revisore di `ci`: il catalogo (riga `ci` di 2.1) mette `rules-security` tra le sue `reviewer_skills`, ma da B3 le regole le precaricano gli agenti (`skills:` del frontmatter), non il brief». Vero contro `catalogo:68` (colonna «Revisore del task: skill»: `rules-ci`, `rules-security`).

**m8. Tre dati distinti fusi in una parentesi** — INDIRIZZATO. `spec:2151`: «quasi tutti sessioni di chat in due copie di terzi, 100 documenti, 449 test».

### Danni nuovi nel diff della correzione

- **N1 (Minor), `piano:148`.** «aprono un blocco solo quando un giro **oltre il tetto** è sporco»: il blocco si apre già al giro che **raggiunge** il tetto (`done >= tetto`, `apply.py:185,187`; `spec:420`: «se il quarto giro trova ancora `blocker` o `major`»). Chi legge «oltre» capisce dal quinto giro della spec e dal terzo del piano. Basta «dal giro che raggiunge il tetto in poi». Non cambia la lettura della prova.

Nessun danno Critical o Important. Controlli sul resto: nessuna riga aggiunta con «unita su `main`» (0 occorrenze nelle righe `+`); la riga 37 della sezione 20 (`spec:2346`) non è nel diff e resta coerente (decisione 13 «sotto `auth/` L2 già con `sensitive_paths`», costo 19,55, 15 giri); la riga `**Tipi:**` e i titoli di 1.2 non sono nel diff; il commit tocca tre file, tutti fra i quattro documenti del task (il progetto di C non aveva rilievi); nessun dato privato nelle righe aggiunte (0 occorrenze di nome utente e percorsi di casa).

### Osservazioni fuori ambito

- Rapporto, «Gli avversari» (riga 80 circa, «Che cosa vuol dire per la prova»): «i 15 giri … nove dei quali aperti dopo giri senza rilievi sopra `minor`». I giri senza rilievi sopra `minor` sono nove (4-9 e 4-6), ma quelli **aperti dopo** un giro così sono sette (5-9 e 5-6), come dicono «Costi» e «Scostamenti» dello stesso rapporto. È del Task 9, non di questo giro.
- `spec:2152` e il rapporto chiamano `spec_audit_round` anche gli eventi dei giri del piano: è il nome vero del tipo di evento (i giri del piano hanno `kind: plan-adversarial`), nessuna correzione.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
