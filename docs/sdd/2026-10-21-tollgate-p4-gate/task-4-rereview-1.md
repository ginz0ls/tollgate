# Task 4 — ri-revisione, giro di correzione 1 (a085abe)

### Verdetti sui rilievi
**I-1 — `plan_change_is_attention` fisso a `True` anche con `where="local"`.** INDIRIZZATO.
`evaluate.py:389` passa `plan_change_is_attention=ctx.is_github`; `evaluate.py:393-394` chiama `_plan_changed` solo se `ctx.is_github`. In locale il piano cambiato resta violazione di scope e non nasce `plan_changed` (decisione 9: `True` solo nel gate, `False` in `finish check`). Test `DiffTest.test_plan_changed_is_scope_violation_in_local` (`test_gate_evaluate.py`, nuovo): con `where="local"` il rosso `diff` contiene sia `PLAN` sia `src/extra.py`, e `plan_changed` non è in `attention`. Il test nel gate esistente (`plan_changed` + `out_of_scope` solo per `src/extra.py`) copre il caso opposto.

**I-2 — filtro dei `setup` sui nomi dell'artefatto, scritti in `Item.text`.** INDIRIZZATO.
`evaluate.py:186-190`: la lista è `["setup"] + [f"profile:{p}:setup" for p in ctx.cfg.profiles]`, cercata con `ctx.results.get(name)`; nessuna iterazione sui nomi di `results.json`. `cfg.profiles` (`tollgate_core/config.py:132-133`) viene dalla configurazione del predefinito, esclusa la chiave `active`. I nomi sconosciuti sono ignorati. Test: `test_setup_red_is_a_red_command` ora usa `PROFILE_TOML` (profili reali) e `test_artifact_names_never_reach_item_text` prova tre nomi ostili (`profile:inventato:setup`, `evil:setup`, `` `@x` setup ``) senza che compaiano in alcuna voce. Il secondo assert dell'ultimo test è ridondante con il primo, ma non nuoce.

### Controllo degli altri punti che scrivono `Item.text` (richiesto)
Esaminate tutte le f-string/stringhe di `text` a HEAD di `evaluate.py`:
- `components_off` (157): testo fisso/nomi da configurazione.
- 190, 196, 204-224: `spec.name` viene da `ctx.required` (`gate_commands`, configurazione), non dall'artefatto. `r.exit` e `r.junit.failed` sono interi.
- 275-279: solo conteggi (`len`); gli id dei test e i percorsi stanno in `data`, non in `text`.
- 318-325: testi fissi.
- 351: testo fisso; il diff del piano va in `data`.
- 364-376: `what = f"deroga {w.id} ({w.type})"`: `w` viene dal file delle deroghe (nel repo della PR), ma `waivers.py:68` rifiuta ogni `id` che non combaci con `_ID` (`^w-\d+-\d+$`) e ogni `type` fuori da `TYPES`; il resto (`file`, `pattern`, `choice`, `why`, `cost`) va solo in `data`.
- 391: `v.detail` è una stringa fissa di `diffcheck`/`testguard` (verificato nei `Violation(...)`), `v.waiver_type` è un enum; il percorso va in `data`.
- 415-424: conteggi in `text`, id in `data`. `manual_must_have` (424): `", ".join(res.manual)` va in `text` e viene dai must-have del piano registrato (testo del piano, scritto nel ramo della PR, ma bloccato dal `plan_sha` registrato); non è né artefatto né blocco né corpo: lo segnalo solo come origine non-config.
- `ev.errors.append(f"...{e}")` (437) non è un `Item.text`.
Nessun altro punto scrive nel `text` un valore dell'artefatto, del blocco o del corpo.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- `waivers.py:12` usa `_ID.match` con `$`: accetterebbe `w-1-1\n` (un solo newline finale) in `Item.text` (`evaluate.py:364`). Minore; `fullmatch` o `\Z` chiuderebbe il caso.
- `manual_must_have` (`evaluate.py:424`) mette nel `text` i nomi dei must-have manuali del piano registrato: se la regola «niente testo non-config in `Item.text`» vale in senso largo, andrebbero in `data`.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
