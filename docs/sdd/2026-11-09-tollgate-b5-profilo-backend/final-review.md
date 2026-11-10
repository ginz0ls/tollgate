# Revisione finale del ramo B5 (`b5-profilo-backend`, `0854ad6..80e9f47`)

Revisore a contesto pulito, in sola lettura. Letti: brief, decisioni, review focus, copertura, vincoli, fatti, `carry.md`, `final-rulings.md`, `final-deferred.md`, i due diff finali (il codice per intero, i documenti per i punti nominati), i file del ramo per rischi precisi. Eseguiti solo test mirati (`tests.test_manifest`, `tests.test_rules_backend`, `tests.test_fragments`, `tests.test_profiles`, `tests.test_bash`: 230 test, OK, 3 saltati per approvazione come in `infra`) e due sonde in `$CLAUDE_JOB_DIR/tmp/final/` (`probe.py` su `bash.effect_reason`, `probe2.py` su `init.profile_blocks` con i frammenti veri). Nessuna rete, nessun programma di servizio.

## 1. Verdetto

**Non pronto** per il merge: Critical 0, Important 1, Minor 2.

Il rilievo I-1 chiede una scelta dell'utente (o una riga di codice e un test, se l'utente approva la correzione proposta); il resto del ramo è solido.

## 2. Rilievi

### I-1 (Important): un percorso concreto di `backend` annidato in una cartella di `ai` vince su `ai`, anche per i file che il rilevamento per contenuto riconosce come codice AI

- **Dove**: `bin/tollgate_flow/init.py:370-382` (`profile_blocks`: `lighting` e `_concrete_paths` per `backend` non guardano le cartelle degli altri verticali) con `templates/profiles/backend.toml:22-23` (`**/routes/**`, `**/handlers/**` a qualunque profondità) e la regola di precedenza `bin/tollgate_analysis/profiles.py:28-37` (vince il pattern con più segmenti letterali).
- **Cosa**: `**/routes/**` e `**/handlers/**` producono un percorso concreto che arriva fino alla cartella `routes/` o `handlers/`; se quella cartella sta dentro una cartella di `ai`, il percorso di `backend` ha un segmento letterale in più e vince. Il caso inverso (`server/ai/x.py` va ad `ai`) è fissato da `test_ai_folder_inside_backend_routes_to_ai`; questo no, e non è scritto in nessun documento (piano B5, decisione 2 e 5; spec rev 32; pagina approvata; piano principale).
- **Scenario che fallisce** (sonda `probe2.py`, frammenti veri del ramo): un progetto con `src/ai/routes/chat.ts` e `ai/handlers/tool.py`, entrambi trovati per contenuto da `ai` (un import di un SDK dei modelli), e `agents/handlers/x.py`. `init --propose` propone `ai` con `src/ai/**`, `/ai/**`, `/agents/**`, e `backend` con `src/ai/routes/**`, `ai/handlers/**`, `agents/handlers/**`. Dopo la copia, `profiles.vertical_for` dà `backend` per tutti e tre: un task su quei file va a `tollgate:implementer-backend` e `tollgate:reviewer-backend`, che non precaricano `rules-ai`, quindi le `R-AI-…` `[blocca]` (chiavi, modelli, uscite del modello) non le giudica più nessun revisore d'area. Prima di B5 gli stessi file andavano ad `ai`. `init` lo scrive solo in una riga d'avviso («corrisponde anche a «ai»: vince backend»), che l'utente non ha mai approvato come costo. È lo stesso meccanismo che il progetto di B, sezione 12 (`docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md:211`) ha voluto evitare per `supabase/` («non perde per specificità contro un percorso più lungo di `backend`»). Con `infra` lo stesso accade per `infra/handlers/lambda.py` (va a `backend`): lì il risultato è difendibile (è codice di un gestore), ma va scritto.
- **Come correggere** (scelta da portare all'utente, perché tocca il profilo approvato e un punto nuovo): (a) consigliata, a costo basso: in `profile_blocks` un file che il rilevamento per contenuto assegna a un altro verticale (`detected[area]`) non accende `backend` per percorso (lo si toglie da `lighting` di `backend`), così `src/ai/routes/chat.ts` resta ad `ai`; con un test in `ProfileBlocksTest` (`ai/handlers/tool.py` rilevato da `ai` → nessun `ai/handlers/**` in `backend`) e uno con i frammenti veri; (b) in alternativa, lasciare il comportamento e scriverlo come costo nella spec 11.4, nel piano principale (sezione 9) e come punto da far decidere all'utente, con un test che lo fissa. In tutti e due i casi aggiungere il caso `infra/handlers/` al costo scritto.

### M-1 (Minor): `_flag_present` legge anche i token dopo `--`

- **Dove**: `bin/tollgate_analysis/bash.py:1163-1170`.
- **Cosa**: `wrangler kv key put K -- --local` (valore letterale `--local` dopo `--`) conta come locale. Con Wrangler 4 il predefinito di KV è locale, quindi il danno resta su Wrangler 3 (predefinito remoto), come il caso residuo di D9.
- **Come correggere**: fermare la scansione al primo `--`, oppure scrivere il caso accanto a `--local=0` tra i buchi del piano principale.

### M-2 (Minor): `agents/implementer-backend.md:53` non nomina `d1 time-travel restore` tra le voci fermate

- La frase elenca `d1 create` e `d1 delete` ma non `d1 time-travel restore`, che è in `_DEFAULT_EFFECTS` (`bin/tollgate_analysis/bash.py:1003`). Correggere insieme alle voci 22 e 23 del triage.

### Punti del brief controllati senza rilievi

- `supabase/`, `.github/tollgate/`, `.claude/` e la cartella della proposta non accendono `backend`: `EXCLUDED_PREFIXES` (`init.py:37`) e `fragment.exclude` valgono per percorso, rilevamento e deriva; sonda: `supabase/functions/a/handlers/h.ts` → nessun profilo.
- Marcatori: solo estensioni sorgente, test e file grandi esclusi (`init.py:257-267`); nessun marcatore in `bin/` (`test_real_markers_not_in_tollgate_bin`).
- Wrangler (`probe.py`, 60 comandi): scritture remote fermate anche dietro `npx`, `npx --yes`, `npx -p`, `npm exec --`, `pnpm exec`, `pnpm dlx`, `bunx`, `node_modules/.bin/`, `env`; locali con `--local` libere anche dietro `npx`; letture libere; `--local false` e `--local --remote` fermati. Token di segnale: `run`, `--local`, `--remote` come nome di cartella, pacchetto o valore (`npm -w run deploy`, `npm --prefix run run deploy`, `yarn workspace run deploy`, `npx wrangler r2 object put run/k … --local`) danno il risultato giusto.
- Nessun `tollgate.toml` dell'utente riscritto: `init` scrive solo la proposta; lo script della prova copia la proposta nel progetto di prova in `/tmp`.
- Le `[blocca]` di `rules-backend` si giudicano tutte sul diff o sul report, nessuna sulla sola nota.
- Test: i nuovi che leggono i file veri hanno `test_real_` (o sono in `tests/test_rules_backend.py`); nessuna asserzione su `os.environ`.
- Evidenze: nessun `/home/` non anonimizzato, nessuna forma di token, nessun percorso `tool-results/`; il solo risultato di `WebFetch` (3201 caratteri) è un riassunto in italiano scritto dal modello, sotto il tetto di 5000.
- Agenti: il test di deriva (`tests/test_manifest.py`) passa; `tollgate:reviewer-backend` in `READONLY_TYPES` e in `config.DEFAULTS`.
- Coerenza: frammento, skill, pagina, `docs/uso/comandi.md` e spec rev 32 (8.5, 11.2, 11.4) dicono le stesse cose (23 marcatori, 6 pattern, `exclude`, `ACCOUNT_GROUPS`, `FLAG_EFFECTS`, `script_name`).

## 3. Triage dei minori rinviati (`W/final-deferred.md`)

| N. | Voce (in breve) | Esito | Motivo |
|---|---|---|---|
| 1 | `tuple(exclude)` ricostruita a ogni file | nessuna azione | Costo trascurabile (un prefisso, poche migliaia di file). |
| 2 | `_drift` passa `exclude` su file già filtrati | nessuna azione | Ridondante e innocuo; tiene la firma che il piano chiede. |
| 3 | `_EXCLUDE` accetta il newline come `_SEGMENT` | nessuna azione | I frammenti sono file del plugin, non input dell'utente; se si stringe, si stringono insieme a `_SEGMENT`. |
| 4 | Nessun test di `init` con due prefissi o a più segmenti | rinviato | B7: arriva con il secondo uso di `exclude` (profilo `database`); il parsing è già coperto. |
| 5 | `exclude` non nella spec 11.4 | nessuna azione | Scritto dal Task 9 (spec, sezione 11.4, rev 32). |
| 6 | `kv namespace --help` e gruppi nudi diventano effetti | nessuna azione | Ruling D8, già nel costo della spec 8.5. |
| 7 | Mancano test per `pnpm -w release`, `npm run-script deploy`, `-C`/`--dir`/`--prefix`, `yarn workspace deploy build` | da correggere | Aggiungere i quattro casi a `test_script_name` o `test_monorepo_deploy_scripts` (`tests/test_bash.py`): la decisione 7 li dà per coperti e le sonde passano. |
| 8 | Nessun test di `allow`/`commands` con le voci nuove | nessuna azione | `allow` e `commands` si leggono prima di ogni voce, con test già esistenti indipendenti dalla voce. |
| 9 | Nessun test del ripiego `text_effect` per `kv:namespace` e `--remote=false` | nessuna azione | Le regex nascono dalla stessa comprensione delle tabelle; `--remote=false` nel ripiego è un effetto, dalla parte sicura. |
| 10 | Buchi già scritti come costo | nessuna azione | Scritti dal Task 9 nella spec 8.5 e nel piano principale, sezione 9. |
| 11 | R-BACKEND-12 unisce due obblighi; la seconda parte passa con un report che tace | rinviato | Prossima revisione di `rules-backend` con l'utente (regola approvata, numeri stabili), come R-INFRA-06. |
| 12 | `Fonte:` di R-BACKEND-08 non cita `code-reviewer` | nessuna azione | Dal Task 4 cita «Fail Securely» di `security-reviewer`, che regge la parte sul corpo d'errore. |
| 13 | `USER_CHOICES` fissa solo R-BACKEND-01 | da correggere | Aggiungere R-BACKEND-02 (progetto di B, sezione 3.4) e R-BACKEND-12 (sezione 12) in `tests/test_rules_backend.py:33`. |
| 14 | `if any(...)` finale tautologico | da correggere | Togliere le due righe `tests/test_rules_backend.py:163-164`: l'`assertEqual(len(lines), 1)` sopra fa già il controllo. |
| 15 | `test_page_has_no_private_data` controlla solo `/home/` | nessuna azione | Stesso controllo di `infra`; pagina e rapporto controllati a mano in questa revisione, nessun dato privato. |
| 16 | `sources_main` non usato | da correggere | Togliere il metodo da `tests/test_rules_backend.py:276`. |
| 17 | Alcune regex dei test della pagina deboli | nessuna azione | Nessuno scenario concreto; la pagina è approvata e congelata. |
| 18 | `docs/profili/infra.md` dice ancora scoperte le scritture remote di KV, D1, R2 | rinviato | Prossima revisione di `rules-infra`/`docs/profili/infra.md` con l'utente (insieme a R-INFRA-06); la differenza è già scritta nel piano principale, sezione 9. |
| 19 | Il test del rinvio normalizza tutta la sezione | nessuna azione | Il test è saltato dopo l'approvazione e non tornerà attivo. |
| 20 | Nessun test che «Come rispondere» e «Rinvio» siano spariti | nessuna azione | Come `infra`; la pagina approvata è stata letta per intero. |
| 21 | Docstring dei test saltati dicono «col Task 5» | nessuna azione | Come `infra`; descrivono quando il test valeva. |
| 22 | `implementer-backend` elenca `psql` tra i comandi non coperti | da correggere | `psql` è in `_DEFAULT_EFFECTS`: in `agents/implementer-backend.md:53` sostituire l'esempio con un client non coperto (per esempio `mysql` o `mongosh` verso un host in linea) o spostare `psql` tra quelli fermati. |
| 23 | `kv namespace` e `r2 bucket` presentati come sempre fermati | da correggere | Nella stessa frase aggiungere «salvo le letture (`list`, `get`, `info`)» e `d1 time-travel restore` (M-2). |
| 24 | `assertIn("push", …)` debole | nessuna azione | Accanto c'è `assertIn("docker build", …)`; la sezione è corta e stabile. |
| 25 | `SAVED_READERS` è un elenco chiuso | rinviato | B6, prima della prossima prova reale: ripulire ogni `Bash` il cui comando nomina un percorso `tool-results/`, senza elenco di lettori. Per B5 la verifica a mano vale (nessun `tool-results/` nelle evidenze). |
| 26 | `tool_use_result.stderr` non sostituito | rinviato | B6, con la voce 25. |
| 27 | `Handler` del progetto di prova senza test | nessuna azione | Vetrina del progetto di prova, mai eseguita. |
| 28 | Il rapporto dice che il brief del revisore contiene R-BASE-05, 07, 10, 11 | da correggere | Correggere la frase in `docs/verifiche/2026-11-09-b5-prova-flusso.md:58` (nello stream c'è solo R-BASE-05; le altre le cita il revisore). |
| 29 | «riga con il testo della revisione» imprecisa | da correggere | Stessa riga 58: dire che il prompt dell'Agent è il percorso di `review-1.md` e che il testo sta nella riga del suo `Read`. |
| 30 | `registro-1/limiti.txt:1` dice «Task 9» | rinviato | B6: rendere generica l'intestazione in `spikes/run-b1-flow.sh`; le evidenze già registrate non si toccano. |
| 31 | In 11.4 il perché del `dod` vuoto è un rimando a 8.7 | nessuna azione | Il perché sta nella decisione 8, nella pagina e nel frammento. |
| 32 | I minori del Task 6 non sono nel blocco «A B6-B8, da B5» | nessuna azione | Li chiude questa tabella (voci 22 e 23). |
| 33 | Due parentesi consecutive nella frase finale di 8.5 | da correggere | Unire le due parentesi in una nella spec del nucleo, 8.5. |

Conteggi: da correggere 9, nessuna azione 18, rinviato 6.

## 4. Punti di forza

- `ACCOUNT_GROUPS` e `FLAG_EFFECTS` sono piccoli, dichiarativi e dalla parte sicura: una sotto-voce nuova di Wrangler è un effetto senza elenchi da tenere aggiornati; `_flag_present` è una definizione sola per i due modi.
- `script_name` copre le forme dei monorepo senza rompere `pnpm vitest run deploy` e simili.
- L'esclusione per frammento è stretta (forma validata, solo per il frammento che la dichiara) e applicata in modo uniforme a percorso, contenuto e deriva, con test su un repo git vero.
- Regole con «Si giudica su» e fonti dichiarate, «scelta nostra» dove manca la fonte, approvazione registrata; pagina chiara per l'utente.
- Prova reale riuscita al primo tentativo, con il precaricamento visto nelle trascrizioni (titoli `isMeta`) e nessun comando di servizio.
