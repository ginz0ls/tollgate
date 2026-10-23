# Revisione finale del ramo p4-gate (P4: gate su GitHub)

Range: `b40284e..f981c97` (54 commit), evidenze in `docs/verifiche/evidenze` escluse.
Revisore: opus, in sola lettura, senza subagenti. Lettura a passate: (1) piano, decisioni,
ledger e spec 1.2 e 9; (2) i cinque workflow; (3) il pacchetto `tollgate_gate` per intero
(`verdict`, `github`, `guard`, `sentinel`, `run`, `baseids`, `artifacts`, `cli`, `model`,
`attention`, `evaluate`, `comment`, `install`, `protection`); (4) i moduli toccati di
`tollgate_core` (`ghcli`, `git`, `diffcheck`, `runner`, `cli`), `tollgate_flow` (`finishcheck`,
`openpr`, `start`, `gh`, `fixtask`, `taskcmd`, `init`), `tollgate_checks`, `tollgate_hooks`,
`prref`, `prblock`; (5) skill, modello `tollgate.toml`, test del Review Focus e suite.
Non ho riletto riga per riga `tollgate_analysis/workflows.py`, `approvals.py` e gli script di
`spikes/` (quattro e cinque giri di revisione ciascuno, con fuzz contro PyYAML per il primo):
ne ho controllato solo l'integrazione con i chiamanti.

Suite: `PYTHONS=python3 tests/run` (Python 3.13.5) su f981c97: 2457 test OK in 1253 s. Non ho
ripetuto la corsa con python3.11 (il ledger la riporta verde per ogni task).

## Strengths

- **Confine dei privilegi corretto nei workflow.** Nessun job che esegue codice del progetto ha
  un token di scrittura (`tollgate-run`, job `ids` di `tollgate-base`); ogni job con permessi di
  scrittura fa il checkout del ramo predefinito con `persist-credentials: false`, estrae artefatti
  e cache sotto `runner.temp` e non ha espressioni `${{ }}` nelle righe `run:`
  (`gate/workflows/*.yml`). La divisione di `tollgate-base` in due job (C-1 del Task 11) chiude
  l'unico punto in cui codice unito girava accanto a `GH_TOKEN`.
- **Fail-closed coerente sui dati non fidati.** `artifacts.validate`/`read_results`,
  `baseids.load`/`read_result` sono confini che trasformano ogni eccezione in un problema;
  `verdict.main` dopo aver letto lo SHA rende ogni guasto uno stato `error` esplicito
  (`bin/tollgate_gate/verdict.py:194-208`); `results.json.sha` e `config_sha` sono confrontati con
  la testa e con la punta (`verdict.py:118-126`).
- **Stati e fiducia ben modellati.** Nessuno stato per le PR verso altri rami (C-1 del piano),
  `shared_sha_prs` filtrato per `head.sha` (V5b), `STATUS_BOT` separato da `BOT_LOGINS` per gli
  stati (V6), sentinella che legge solo l'ultimo stato per contesto e tratta il push forzato come
  non verificato (`sentinel.py:166-176`, `193-215`).
- **Un solo calcolo.** `evaluate.evaluate` è davvero l'unico punto delle voci rosse e di
  `attenzione` per gate e `finish check`, a famiglie indipendenti; la sola differenza voluta
  (`plan_change_is_attention`) è legata a `ctx.is_github` e ha un test dedicato.
- **Testo non fidato tenuto fuori dagli argomenti e dal testo delle voci.** Commenti e stati
  passano da file; `Item.text` è scritto da tollgate, il resto sta in `Item.data` e passa da
  `prbody.neutralize`; tetti duri a 60.000 caratteri.
- **Prove reali documentate con onestà**, compresi i quattro difetti (D-1..D-4) trovati solo su
  GitHub e corretti con test.

## Issues

### Critical

Nessuno. Ho cercato in particolare un gate che si apre quando non deve: PR che modificano il CLI
o i workflow (guard rosso, obbligatorio), workflow omonimi di `tollgate-run` (controllo di
`workflow_run.path`), PR da fork e PR verso altri rami, SHA condivisi o superati, artefatti
manomessi, configurazione presa dalla PR, stati scritti con il token dell'utente, push forzati.
Ogni caso che ho costruito finisce in `failure`, `error` o assenza di stato, tranne quelli che
la spec 1.2 dichiara fuori garanzia (vedi «Declined to judge»).

### Important

**I-1. In `protected` una suite della base rossa non dà nessun segnale: «il segnale è il job»
non è vero.**
- Dove: `bin/tollgate_gate/baseids.py:243-262` (`publish_from`), `baseids.py:199-201`
  (`_publish` esce subito se la modalità non è `detect`), `bin/tollgate_gate/cli.py:517-531`
  (`cmd_base_ids` esce sempre con 0); test `tests/test_gate_sentinel.py:466-469`.
- Cosa: con `gate.mode = "protected"` e un comando della base `red`, `base-publish` non scrive
  nulla **ed esce con 0**; anche il job `ids` esce con 0. Entrambi i job di `tollgate-base` sono
  verdi. La spec 9.1 (riga 853) e il rapporto della prova (`docs/verifiche/2026-10-21-p4-prova-gate.md:28`,
  spec riga 1579) dicono «In `protected` non pubblica lo stato: il segnale è il job»; la prova
  reale ha visto solo il caso verde. `test_protected_mode_publishes_nothing` controlla che non ci
  siano chiamate a `gh`, non il codice d'uscita.
- Perché conta: in `protected` l'utente non ha nessun modo di sapere che il ramo predefinito è
  rotto. Per le PR il fallimento compare al più come voce **informativa** `base_failing_on_head`,
  e solo per i test che falliscono anche nella testa.
- Come correggere: `publish_from` (o `_publish`) restituisce 1 quando un comando di
  `result["commands"]` è `red`, in entrambe le modalità (in `detect` dopo stato e issue), così il
  job `tollgate-base` è rosso; un test per modalità che asserisce il codice d'uscita. In
  alternativa, se il job deve restare verde, correggere spec 9.1 e il rapporto e pubblicare
  `tollgate/base` anche in `protected` (non è un controllo obbligatorio, non blocca nulla).

### Minor

**M-1. Confronto degli identificativi della base vuoto senza voce.**
`bin/tollgate_gate/evaluate.py:315-323`: un comando richiesto senza voce in `base_ids`
(`i.base_ids.get(spec.name, ())`) o con un elenco vuoto perché nella base non è girato (setup
fallito, nessun report) passa senza alcun segnale; `baseids.load` scarta gli stati `commands` di
`ids.json`. Succede anche quando la cache dell'albero di `merge-base` è stata scritta con una
configurazione precedente (comando o profilo aggiunto dopo, chiave di cache solo per albero), in
`detect` dove le PR non devono essere aggiornate. Il test-guard copre le cancellazioni, non i test
rinominati o non più raccolti. Correzione: `load` restituisce anche gli stati; in `evaluate` una
voce «da leggere» (per esempio `base_ids_incomplete`) quando un comando richiesto manca da
`base_ids` o nella base non è `green`/`red` con JUnit.

**M-2. `base_test_ids = false` non ferma la suite della base nei workflow.**
`gate/workflows/tollgate-run.yml:31-79` (job `base`) e `tollgate-base.yml:15-47` (job `ids`)
eseguono comunque la suite; `cmd_base_ids` non legge il componente. La decisione 12 dice «Con
`base_test_ids = false` nessuna delle due cose gira». Effetto: minuti di Actions pagati in
`detect` per un controllo spento. Correzione: `gate base-ids` esce subito (scrivendo un
`ids.json` vuoto marcato come spento, o nulla) se il componente è spento nella configurazione
della punta, con un test.

**M-3. Stati di un giudizio precedente restano validi durante la rivalutazione dello stesso SHA.**
Su `edited` (corpo con il blocco cambiato), `reopened` o una seconda PR aperta sullo stesso SHA,
`tollgate/verdict` `success` dello SHA resta finché il nuovo `verdict` non lo sostituisce
(minuti: serve un intero `tollgate-run`); `guard` non pubblica `pending`. In quella finestra la PR
è unibile con un verdetto calcolato su un altro corpo. L'agente non può unire (7.4), quindi il
rischio è un merge umano nella finestra. Correzione possibile: `gate guard` (veloce, già su
`edited`) pubblica `tollgate/verdict` `pending` quando l'evento è `edited` con `changes.body` o
`changes.base`, oppure dichiarare il limite in 1.2.

**M-4. `[skip ci]` in un commit del ramo predefinito toglie la sentinella per quel push.**
GitHub non lancia i workflow `push` se il messaggio del commit di testa contiene `[skip ci]` e
simili; `tollgate-sentinel` controlla solo `before..after` del proprio evento, quindi i commit di
un push saltato non vengono mai controllati (in `detect` è l'unico controllo). Rientra in parte
nel «sabotaggio deliberato della CI» di 1.2, ma può nascere da un titolo di PR in un merge squash.
Correzione: dichiararlo in 1.2 e 9.3, o far partire l'intervallo della sentinella dall'ultimo
commit con `tollgate/sentinel` o con una sua esecuzione registrata.

**M-5. `config_sha` confrontato per commit, non per contenuto.** `verdict.py:121-122`: ogni merge
sul predefinito durante un `tollgate-run` rende `error` il verdetto di tutte le PR in volo, anche
se `tollgate.toml` non è cambiato. In `protected` con `strict` la PR va comunque aggiornata; in
`detect` è attrito puro. È la lettera della decisione 13 (M-6 del piano), quindi lo segnalo solo:
confrontare il blob di `tollgate.toml` e il `merge-base` darebbe lo stesso fail-closed con meno
rumore.

**M-6. `unverified` accettato per un comando configurato.** `evaluate.py:217-221`: uno stato
`unverified` in `results.json` vale `unverified` anche se `spec.command` non è vuoto, e con un
atto `approve unverified-tests` dichiarato nel blocco diventa solo `attenzione`. Il CLI vero lo
scrive solo per un comando vuoto (`run.py:69-70`); controllare `spec.command` costa una riga e
toglie una via per far passare un comando configurato con un artefatto scritto dalla PR.

**M-7. Righe oltre 100 caratteri** (rinvio del Task 12 da chiudere qui, più quelle nuove del
Task 16): `bin/tollgate_flow/gh.py:9,28,108-110` (fino a 125), `bin/tollgate_flow/init.py:198,419`,
`bin/tollgate_gate/evaluate.py:446`, `tests/fakegh.py:34`, `tests/test_init.py:244`.

**M-8. Testo delle eccezioni su stderr non codificato** (rinvio del Task 9, riesaminato):
`verdict.py:199-200` e `cli.py:570-571` scrivono il messaggio grezzo; una riga successiva che
comincia con `::` sarebbe letta come comando di workflow. Oggi i messaggi portano testo di git e
di `gh`, non della PR, e la prima riga ha sempre un prefisso: resta minore. Correzione: `json.dumps`
come in `_print`.

**M-9. `AgreementTest` non prova gli ingressi del gate vero** (rinvio del Task 13, riesaminato):
`tests/test_criteria_p4.py:49-73` riusa `inputs` locali (configurazione della base del lavoro,
base del lavoro) con `where=GITHUB`; le differenze reali (configurazione della punta,
`merge-base`, blocco dal corpo, artefatti) non sono confrontate. `BlockFeedsGateTest` copre il
blocco; manca un caso che faccia girare `verdict.main` sullo stesso albero e confronti le chiavi
rosse con `finish check`.

## Declined to judge

- PR da rami non `tg/*`, da fork, `tollgate-config/*` e PR con `level_cap` dichiarato superano
  `verdict` con i soli controlli sui test e `attenzione` rosso, che non è obbligatorio: è la
  spec (1.2, 9.2, 9.4; decisione 7), non un difetto.
- Codice della PR che falsifica `results.json` o i JUnit nel job `head`, o carica un artefatto
  `tollgate-base-ids` falso con il token di runtime: limite dichiarato in 1.2 («Il codice della PR
  che falsifica l'esito dei propri test») e nella decisione 12.
- Push diretto che toglie o modifica `tollgate-sentinel.yml` (i workflow `push` girano dalla
  versione del commit spinto), e la regola che salta il commit che reintroduce il workflow e i suoi
  antenati: «sabotaggio deliberato della CI», 1.2.
- Il codice unito che falsifica `ids.json` o avvelena la cache del predefinito: dichiarato in 1.2.
- Atti, deroghe e scope dichiarati dall'agente nel blocco o in `.tollgate/waivers/`: 1.2 («Il gate
  ne verifica la coerenza, non la legittimità»).
- Workflow del progetto con permessi diversi da `statuses`/`checks` (per esempio
  `contents: write` su `push`): le regole di `guard` sono quelle di 9.2.
- Azioni fissate alla versione maggiore `@v4` e non per SHA: limite dichiarato, rinviato a P5.
- `guard` confronta con la punta e non con il `merge-base` (un workflow cambiato sul predefinito
  dopo il punto di diramazione appare «modificato» nella PR): fail-closed, si risolve aggiornando
  il ramo, ed è la lettera di 9.2 per i file di tollgate.
- Qualità e copertura interna di `workflows.problems` e del giudizio L2 (`approvals`): quattro e
  più giri di revisione, fuori dal mio passaggio.
- Script di `spikes/` e guardie della prova reale: strumenti del controller, non prodotto; il
  falso positivo di `ghguard.py` è già corretto (8fa32ba) e coperto da test.
- Minori già rinviati nel ledger: non li ripropongo, salvo M-7, M-8 e M-9 che il ledger rimanda
  esplicitamente a questa revisione.

## Recommendations

1. Correggere I-1 prima del merge (piccolo: codice d'uscita più due test), e riallineare la frase
   di 9.1 e del rapporto se si sceglie l'altra via.
2. Nel giro di correzione, a basso costo: M-6 (una condizione), M-7 (formattazione), M-8
   (`json.dumps`), M-2 (uscita anticipata di `base-ids`).
3. M-1 e M-3 vanno decisi: sono segnali mancanti più che difetti; se non si correggono, vanno
   dichiarati in 1.2 insieme a M-4.
4. In P5, oltre al fissaggio delle azioni per SHA: un test di accordo che parta dagli ingressi del
   gate vero (M-9).

## Assessment

**Ready to merge? With fixes.** Nessun difetto che apra il gate quando non deve: i confini dei
privilegi, i controlli preliminari di `verdict`, la fiducia negli stati e il fail-closed sui dati
non fidati reggono ai casi che ho costruito. Resta un Important (I-1): in `protected` un ramo
predefinito con la suite rossa non dà nessun segnale, contro ciò che spec e rapporto affermano;
la correzione è piccola e locale.
