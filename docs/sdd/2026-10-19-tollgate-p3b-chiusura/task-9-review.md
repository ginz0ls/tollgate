# Revisione Task 9 — `finish open-pr`, blocco 18.1, merge e chiusura (e7aef10..7b203d0)

Ho letto brief, carry (due sezioni «Task 9»), Ruling G1-G5, decisioni 10, 11, 12, 15, review-focus 1 e 2, report e diff. Nessun test rilanciato; controlli mirati sul codice di `dod`, `acts`, `intents`, `effects`, `reviews` per i rischi nominati sotto.

## Aderenza

- ✅ Ordine della decisione 10 in `openpr.py:_open`/`_publish`: intento `requested` (openpr.py, prima di `_publish`) → push dello SHA esatto (solo se `remote != head`) → `ls-remote` uguale → PR aperta? `pr_edit` : `pr_create` + rilettura con `pr_for_branch` (G2) → `set_pr`, evento (`pr_opened` se `pr_number` era nullo, altrimenti `pr_updated`), `set_phase(pr_open)`, `intents.complete`, atti consumati per ultimi.
- ✅ Review Focus 1: push riuscito e `pr create` fallito → fase `review`, intento `requested`, atto `pending`; la ripetizione trova `remote == head`, nessuna PR, crea una sola PR (`test_interrupted_after_push_no_duplicate_pr`). PR creata e morte prima di `set_pr`: la ripetizione la trova `OPEN` e fa `pr edit` (`test_pr_created_but_process_died_edits_instead_of_creating`). Morte dopo `set_phase(pr_open)`: ramo `resume` (fase `pr_open`, `head == finish_sha`, intento ancora `requested`) senza ripetere la transizione (`test_died_after_phase_change_resumes_from_pr_open`). L'atto `finish` non scade per il tempo e decade solo con un evento `commit` successivo (`acts._FINISH_ALIVE`): `open-pr` non ne produce.
- ✅ Review Focus 2: `neutralize` (prbody.py:17-24) mette tutto in un recinto più lungo di ogni sequenza di backtick (`brief.fence`), `@` → `@`+U+200B, `<!--` e `-->` disinnescati nell'ordine giusto (verificato a mano anche il caso `<!---->`), troncamento a 2000. `prblock.render` sostituisce `<`, `>`, `&`: nessun `-->` né `<!--` può stare nel commento; `parse` prende l'ultimo blocco e il blocco è l'ultimo elemento del corpo, quindi un testo ostile (sempre prima) non può metterne uno successivo. `test_hostile_finding_text_neutralized_and_block_roundtrips` copre backtick, `@`, `-->`, `<!-- tollgate {…}`, 10.000 caratteri, recinti bilanciati e `parse(body) == BLOCK`.
- ✅ Titolo `#<N> <slug>` (`_title`), mai il titolo dell'issue; il test controlla che «export» non compaia negli argomenti di `gh pr`.
- ✅ Rifiuti raccolti e stampati insieme (`rifiuto: …`, codice 1); `test_refusals_collected` conta esattamente tre righe. Ritorni anticipati (nessun lavoro, PR unita/chiusa, nessun HEAD, nessuna base) sono ragionevoli.
- ✅ `CliSessionError` non rifiuta con un atto `finish` valido (`session_error` si accoda solo se `used` è vuoto); `find_usable(type_="finish", session=None)` rende l'atto indipendente dalla sessione (`test_finish_survives_clear`).
- ✅ Push forzato solo con `--force-with-lease=refs/heads/<ramo>:<sha letto prima>` e intento `force_push` autorizzato (`gitw.push_sha`, `_open` calcola `diverged` con `is_ancestor`, rifiuto senza push in caso contrario, `test_non_fast_forward_without_intent_refused`); `gitw.remote_sha` filtra `ref == refs/heads/<ramo>` (nessun falso positivo da suffissi).
- ✅ `FIELDS` nell'ordine di 18.1 (test di ordine), `build` con `KeyError`, `spec_audit` sempre oggetto come nell'esempio 18.1.
- ✅ C6 (guard_scope/must_have/approvals dal `finish_report`, `HEAD == finish_sha`), C19 (`is_ancestor`), C24 (`GhError`/`GitWriteError` → `rifiuto:`), eventi, `--update` senza PR aperta, CLOSED con `CLOSED_HINT`, MERGED chiude con `merge_detected`, aggancio a `finish check` con avviso offline.
- ✅ Strati rispettati: `prblock`/`prbody` importano solo `tollgate_analysis`; `openpr`/`prstate` solo core, analysis e flow; `cli.py` importa `openpr` in modo pigro. `gh` nei test solo `fakegh`, push solo verso il repo nudo del banco; `fakegh` rifiuta i campi `--json` sconosciuti (G4) anche senza PR.
- ⚠️ Non verificabile dal diff: se GitHub tratta le parole chiave di chiusura («Closes #99») dentro un recinto di codice come attive. Il recinto spegne menzioni e markdown, ma non ho modo di provare quel comportamento senza rete.
- ⚠️ Nomi dei campi `--json` col `gh` vero (`headRefOid`, `mergedAt`, `comments`): già tracciati nella Ruling G4.

### Scostamenti dichiarati dal report

1. `review_unverified` → `findings_cycle = 0`: vedi I-1. **Da correggere o da legittimare.**
2. Kwarg extra (`environ`, `now`, `dod`, `labels`, `cycle`) e campo `Detection.error`: accettabili, non cambiano i contratti.
3. `spec_audit` sempre oggetto: conforme a 18.1 (la decisione 11 diceva «altrimenti null», ma l'esempio della spec è l'autorità).
4. Evento `pr_opened`/`pr_updated` in base a `pr_number`: conforme al carry.
5. `tests/test_flowkit.py` con `--json number`: coerente con G4.

## Punti di forza

- La ripresa è guidata dallo stato reale (remoto e `gh pr list`), non da flag locali: ogni passo è idempotente e i tre punti di morte pertinenti sono coperti da test distinti.
- `profile_receipts` estratta da `finishcheck` e riusata (nessuna duplicazione della logica delle voci `dod` dei profili); `openpr` ricalcola la DoD invece di fidarsi del report, salvo le tre voci esterne come da C6.
- Rilettura della PR dopo `pr create` invece di leggere l'URL da stdout; se la rilettura fallisce, la ripetizione fa `edit`.
- `fakegh` stretto (campi sconosciuti, `fail` per comando) e test sul comportamento reale con repo nudo e SHA remoti.
- `test_prbody` verifica la struttura dei recinti riga per riga, non solo l'assenza di sottostringhe.

## Rilievi

### Critical
Nessuno.

### Important

**I-1. `review_unverified` azzera i rilievi e gli specialisti nella DoD (contro spec 8.7).** `openpr.py:_review` (righe del blocco `on_head = ... and not work["review_unverified"]`, `last["number"] if on_head else 0`, `specialists` vuoto). Con `findings_cycle = 0`, `dod._findings` chiama `blocking_open(..., cycle=0)` e non trova nulla (`cycle = 0` non è `NULL`), quindi la voce `findings` è `True` anche se l'ultimo ciclo ha rilievi `blocker`/`major` confermati senza `approve finding`. Il caso tipico è proprio quello di `approve unverified-review`: si arriva al tetto con un ciclo `needs_fix`. Effetti:
- 8.7 dice «nessun rilievo blocker o major confermato senza `approve finding`»; 8.4 dice solo «chiude la revisione come non verificata e lo scrive nella PR», non «scavalca i rilievi». Qui `approve unverified-review` diventa un modo per aprire la PR saltando i bloccanti, senza `approve finding`.
- Il blocco 18.1 dichiara `dod.items.findings: true` mentre `findings[]` elenca bloccanti confermati con `user_decision: null`. P4 legge le voci «come dichiarate» (8.7, ultima riga): il contratto con il gate è incoerente.
- `_notes` ritorna `[]` con `findings_cycle == 0`: nemmeno le note non bloccanti compaiono nel corpo.
- Con L2 la voce `specialists` diventa vacuamente vera (`expected` vuoto).
Correzione: con `review_unverified` usare comunque come `findings_cycle` l'ultimo ciclo chiuso su HEAD (o con lo stesso `patch-id`), così i bloccanti si superano con `approve finding` (la via d'uscita esiste); se il controller vuole davvero lo scavalco, va scritto nella decisione 10/15 e nella spec rev 23 e la voce `findings` del blocco deve riportare `null` («non calcolata»), non `true`. Aggiungere il test che manca (ciclo `needs_fix` con bloccante + `review_unverified`).

**I-2. L'autorizzazione al push forzato si consuma prima del push (`openpr.py:_publish`, `intents.take_force` prima di `gitw.push_sha`).** Se il push fallisce (rete, `--force-with-lease` respinto) l'intento `force_push` è già `used`; la ripetizione ricade su «serve un'autorizzazione» e, con `approve rebase`, il blocco del `sync` è già chiuso e non si può riautorizzare. Finché il Task 11 non dimostra che `sync` riautorizza a ripetizione, il lavoro resta bloccato: contraddice lo spirito di Review Focus 1 (la ripetizione deve poter proseguire). Correzione: eseguire il push, poi `take_force` (la presenza dell'autorizzazione è già verificata da `force_authorized` poche righe prima), oppure ripristinare l'autorizzazione (`authorize_force`) se il push solleva `GitWriteError`. Aggiungere un test: push forzato fallito (lease sbagliato o rete finta) → autorizzazione ancora presente, ripetizione che riesce. ⚠️ Non verificabile: il comportamento di `sync` (Task 11) non è ancora nel ramo.

**I-3. Il tetto di 2000 caratteri vale per sezione, non per voce (`prbody.py:_section`).** Tutte le righe di una sezione sono unite e poi troncate insieme: una nota lunga (il testo di un rilievo è già fino a 2000 caratteri nel DB) fa sparire tutte le successive, e lo stesso vale per le righe della DoD con `definition_of_done` spento (le uniche tracce dei `[no]`) e per le deroghe. Review Focus 2 chiede «testo di 10.000 caratteri» neutralizzato, non perdita delle altre voci. Il test ostile non lo vede perché mette un solo elemento per sezione. Correzione: troncare ogni voce a `MAX_TEXT` prima dell'unione (e dare alla sezione un tetto totale più alto, o nessuno), poi un solo recinto; aggiungere un test con tre note di cui la prima lunga e asserire che le altre due compaiono.

### Minor

- **M-1** `gh.py:prs_for_branch_prefix` — l'API REST restituisce `state` in minuscolo (`open`/`closed`) e `merged_at` a parte, e il `--jq` imposto da G5 non lo include; `fakegh` ripassa il `state` dei dati (`OPEN`) e nasconde la differenza. Oggi lo usa solo `start.py:281` (elenco), ma Task 12/13 vorranno distinguere aperta/unita/chiusa: usare `pr_for_branch`/`pr_view` o aggiungere `merged_at` e normalizzare in `prs_for_branch_prefix`; far emettere al fake il formato REST.
- **M-2** `gh.py:pr_for_branch` — `--head <ramo>` non filtra il proprietario del ramo: in un repo pubblico una PR da fork con lo stesso nome ramo e numero più alto verrebbe scelta come «la PR del lavoro» (e modificata con `pr edit`). Aggiungere `headRepositoryOwner`/`isCrossRepository` ai campi e scartare le PR da fork (aggiornare l'elenco dei campi di `fakegh`).
- **M-3** `prbody.py:11` — U+200B scritto letterale nel sorgente (invisibile in review): usare `"​"`.
- **M-4** `gh.py` — il messaggio d'errore `f"gh {' '.join(args[:2])}: {stderr or 'uscita N'}"` è ripetuto tre volte (`run_json`, `run_json_lines`, `_run_checked`): estrarre un helper.
- **M-5** `prbody.py:_note` — con `file`/`line` assenti stampa «None» (`None (R-1): …`); gestire il caso.
- **M-6** Morte tra `intents.complete` e `acts.consume`: fase `pr_open`, intento `executed`, atto `finish` ancora valido e mai consumato; la ripetizione rifiuta («la fase è pr_open»). Innocuo (l'atto decade al prossimo commit) ma lascia un atto vivo: valutare di consumare nel ramo di rifiuto quando l'intento è `executed` per lo stesso SHA, oppure documentarlo.
- **M-7** `openpr.py` — `json.loads(work["finish_report"])["items"]` e `json.loads(last["reviewers"])` non sono protetti: un valore corrotto dà un traceback invece di `rifiuto:`. Aggiungere `ValueError`/`KeyError` a `SIDE_EFFECT_ERRORS` o rifiutare esplicitamente.
- **M-8** `prstate.py:detect` — evento `merge_detected` e `set_phase(closed)` non sono atomici: se `set_phase` fallisce, il prossimo `detect` registra l'evento due volte. Invertire l'ordine o proteggere con la fase.
- **M-9** Dopo una morte tra `set_pr` e `record_event` la ripresa emette `pr_updated` e il `pr_opened` non esiste mai; non influisce sulla correttezza, ma `stats` conterà una PR aperta in meno.
- **M-10** Test mancanti, tutti riconducibili ai rilievi sopra: `review_unverified` con bloccante, push forzato fallito, note multiple con la prima lunga. Nessun test verifica da `open_pr` l'argv `--force-with-lease=…` (è coperto solo a livello di `gitw.push_sha`, con git vero, che basta per il comportamento).

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** La struttura è solida e il comportamento delle ripetizioni (Review Focus 1) e della neutralizzazione (Review Focus 2) è corretto e ben provato; ma `review_unverified` rende `approve unverified-review` un bypass dei rilievi bloccanti con un blocco 18.1 incoerente (I-1), l'autorizzazione al push forzato si perde se il push fallisce (I-2) e il tetto per sezione fa sparire note, deroghe e righe della DoD (I-3). Sono correzioni locali (poche righe ciascuna) più tre test.
