# Task 2: report dell'implementatore

**Status:** DONE
**Commit:** `cf770f1` tollgate C2: sicurezza fin dal progetto per chi pianifica, implementa e rivede (sopra `0ae01de`)

## Cosa ho fatto

La decisione 20 nel testo degli agenti, con gli stessi paragrafi parola per parola nel generico e nelle copie, applicati con uno script che sostituisce ogni ancora esattamente una volta per file (così le copie non possono divergere):

- `implementer.md` e `implementer-{ai,infra,backend,frontend,database}.md`: la sezione `## Sicurezza fin dal progetto`, subito prima di `## Non lanci subagenti`, quindi dopo `## Il lavoro` e fuori dalla sezione «Area» (nelle copie «Area» sta prima di «Il lavoro»). Inoltre la voce `done` di «Report finale» richiama la riga `Sicurezza:`. Il blocco JSON d'esempio non cambia.
- `task-reviewer.md` e `reviewer-*`: una voce nuova nell'elenco di «Parte 2: qualità», prima di «Struttura».
- `final-reviewer.md` e `final-database.md`: una voce nuova in «Cosa controllare», prima di «Lista di controllo dell'area». La voce «Qualità e architettura» resta com'era, «sicurezza» compresa.
- `spec-adversary.md`: una voce in «Cosa cercare», prima di «Giri precedenti». `plan-adversary.md`: una voce in coda a «Cosa cercare», dopo «Fatti e interfacce». Ognuno resta con un solo blocco JSON.
- `docs/uso/comandi.md`: un paragrafo in `/tollgate:start` (avversari in L2, riga `Sicurezza:` degli implementatori in L1 e L2) e una frase in `/tollgate:execute` (la sezione, le due forme della riga, il controllo del revisore).

Non cambiano: `finding-verifier.md`, `spec-auditor.md`, i frontmatter (righe `model:` comprese), le sezioni «Area», le regole, i frammenti, le pagine approvate, `plan.required_sections`.

## Testo esatto dei paragrafi aggiunti

### Implementatori (generico e cinque copie)

```
## Sicurezza fin dal progetto

La sicurezza fa parte di ogni task, anche quando nessun profilo di sicurezza è attivo. Mentre scrivi il codice:
- **Input non fidato validato al confine**: ciò che arriva dall'esterno (richieste, parametri, file caricati, risposte di altri servizi) si controlla dove entra, prima di usarlo.
- **Nessun segreto nel codice né nei log**: chiavi, token e password si leggono dalla configurazione o dall'ambiente, non finiscono nei test, nei log né nei messaggi d'errore; nei test servono solo valori finti.
- **Accesso chiuso per difetto**: chi non ha il permesso riceve un rifiuto, e un test prova il caso negato, non solo quello permesso.
- **Valori predefiniti che rifiutano**: un'opzione mancante o una configurazione sbagliata chiude, non apre.
- **Permessi minimi**: al codice, ai token e ai processi solo i permessi che servono al task.

Nel report il campo `done` chiude con la riga `Sicurezza: <cosa hai considerato>` (per esempio quale input validi al confine e quale caso negato provi), oppure `Sicurezza: il task non tocca input esterni, accessi, dati o segreti` quando è così.
```

Voce `done` di «Report finale» (prima → dopo):
`- \`done\`: cosa hai implementato (o tentato, se bloccato). \`tests\`: …` → `- \`done\`: cosa hai implementato (o tentato, se bloccato), con in fondo la riga \`Sicurezza:\` della sezione «Sicurezza fin dal progetto». \`tests\`: …`

### Revisori del task (generico e cinque copie), «Parte 2: qualità»

```
- Sicurezza fin dal progetto: il campo `done` del report ha la riga `Sicurezza:`? Controlla il diff contro di essa: input non fidato validato al confine, nessun segreto nel codice né nei log, accesso chiuso per difetto con il test del caso negato, valori predefiniti che rifiutano, permessi minimi. Una riga assente, o un diff che la smentisce, è un rilievo, con la regola dell'area se ce n'è una, altrimenti con il passo del piano.
```

### Revisori finali (`final-reviewer`, `final-database`), «Cosa controllare»

```
- **Sicurezza fin dal progetto**: dove il diff tocca input dall'esterno, accessi, dati o segreti, l'input è validato al confine, nessun segreto sta nel codice né nei log, l'accesso è chiuso per difetto con un test del caso negato, i valori predefiniti rifiutano e i permessi sono i minimi. Un difetto si segnala con la regola dell'area se ce n'è una, altrimenti con il passo del piano.
```

### Avversari, «Cosa cercare»

`spec-adversary.md`:
```
- **Sicurezza fin dal progetto**: la spec che tocca input dall'esterno, login, permessi, dati personali, segreti, file caricati o chiamate verso l'esterno dice chi può usare ciò che si costruisce, quali dati e segreti tocca e cosa succede con un input ostile. Se non lo dice, è un rilievo.
```
`plan-adversary.md`: la stessa voce con «il piano» al posto di «la spec».

### `docs/uso/comandi.md`

`/tollgate:start`, paragrafo nuovo prima di quello sulla modalità `detect`:
> La sicurezza fin dal progetto vale in ogni lavoro, anche quando nessun profilo di sicurezza è attivo: in L2 gli avversari di spec e piano chiedono chi può usare ciò che si costruisce, quali dati e segreti tocca e cosa succede con un input ostile, e in L1 e L2 ogni implementatore chiude il report con la riga `Sicurezza:` (cosa ha considerato, oppure che il task non tocca input esterni, accessi, dati o segreti).

`/tollgate:execute`, frase dopo «Un task che tocca due aree usa gli agenti generici.»:
> Ogni implementatore, generico o di area, segue la sezione «Sicurezza fin dal progetto» (input validato al confine, nessun segreto nel codice né nei log, accesso chiuso per difetto con il test del caso negato, valori predefiniti che rifiutano, permessi minimi) e chiude il campo `done` del report con la riga `Sicurezza: <cosa ha considerato>` oppure `Sicurezza: il task non tocca input esterni, accessi, dati o segreti`; il revisore del task controlla quella riga e il diff contro di essa.

## Test

Tre test nuovi in `tests/test_manifest.py`:
- `test_security_by_design_in_every_implementer`: per `implementer` e ogni `implementer-*` una sola `\n## Sicurezza fin dal progetto\n`, dopo `\n## Il lavoro\n`; nella sezione «input», «segreti», «caso negato», «valori predefiniti», «permessi minimi» e le due forme esatte della riga `Sicurezza:`; nessun id `R-…-NN` né le frasi «sul tuo report», «si giudicano sul report», «si giudicano sul diff» (D13); una sola voce `- \`done\`` in «Report finale», e nomina `` `Sicurezza:` ``.
- `test_reviewers_check_security_line`: «Parte 2: qualità» di `task-reviewer` e di ogni `reviewer-*` nomina `` `Sicurezza:` `` e il diff, senza id con due cifre; «Cosa controllare» di `final-reviewer` e `final-{FINAL_AREAS}` nomina la sicurezza fin dal progetto e il caso negato, senza id con due cifre né «si giudicano sul report». Il test itera su `FINAL_AREAS`, così il Task 7 (`final-security`) è già coperto.
- `test_adversaries_look_for_security`: in «Cosa cercare» di `spec-adversary` e `plan-adversary` c'è una sola voce `- **Sicurezza fin dal progetto**`, con «chi può usare», «dati», «segreti», «input ostile» e «rilievo».

`test_area_agents_derive_from_generic` resta il controllo che le copie abbiano i paragrafi nuovi. Prova di mutazione in memoria (senza toccare file): togliendo «che rifiutano» da una voce di `implementer-ai.md` il confronto del test di deriva trova 1 paragrafo mancante.

### RED

`python3 -B -m unittest tests.test_manifest` (prima del testo degli agenti):
```
FAIL: test_security_by_design_in_every_implementer (agent='implementer'), …-ai, -infra, -backend, -frontend, -database
FAIL: test_reviewers_check_security_line (agent='task-reviewer'), reviewer-ai, -infra, -backend, -frontend, -database, final-reviewer, final-database
ERROR: test_adversaries_look_for_security (agent='spec-adversary'), (agent='plan-adversary')
  ValueError: not enough values to unpack (expected 1, got 0)   (la voce non c'è)
AssertionError: '`Sicurezza:`' not found in "- Separazione delle responsabilità, …"
Ran 64 tests in 0.491s
FAILED (failures=14, errors=2)
```
Solo i tre test nuovi sono rossi; gli altri 61 erano verdi.

### GREEN

- `python3 -B -m unittest tests.test_manifest tests.test_docs`: `Ran 71 tests in 0.517s` / `OK`.
- `claude plugin validate --strict .`: `✔ Validation passed`, uscita 0 (un solo avviso della directory, `ICON_MISSING`, che non cambia l'esito e c'era già).
- `PYTHONWARNINGS=error::ResourceWarning tests/run` (log in `W/suite-task-2.log`):
  ```
  == Python 3.11.16
  Ran 4357 tests in 1946.461s
  OK (skipped=13)
  == Python 3.13.5
  Ran 4357 tests in 1970.001s
  OK (skipped=11)
  exit 0
  ```
  Nessun «unclosed» né avviso nel log.

## File cambiati

`agents/implementer.md`, `agents/implementer-{ai,infra,backend,frontend,database}.md`, `agents/task-reviewer.md`, `agents/reviewer-{ai,infra,backend,frontend,database}.md`, `agents/final-reviewer.md`, `agents/final-database.md`, `agents/spec-adversary.md`, `agents/plan-adversary.md`, `docs/uso/comandi.md`, `tests/test_manifest.py` (18 file, 16 agenti come dice lo scan).

## Scostamenti dal piano e perché

- Nessuno nella sostanza. Due scelte di forma, entrambe dentro la decisione 20:
  - la riga `Sicurezza:` sta nella sezione nuova e la voce `done` di «Report finale» la richiama; il blocco JSON d'esempio resta `"done": "…"`, perché la riga è dentro il valore di `done` e lo scan (4-bis, 3c) chiede solo che resti lì;
  - in `comandi.md` ho scritto «anche quando nessun profilo di sicurezza è attivo» e non «senza il profilo `security`»: se l'utente rinvia l'approvazione, i Task 1-3 si uniscono su `main` da soli (decisione 19) e lì il profilo `security` non esiste ancora. Il testo degli agenti dice la stessa cosa per lo stesso motivo.
- Il test sugli implementatori controlla anche «permessi minimi» e la voce `done`. Lo Step 1 non lo chiede: sono il quinto punto e la seconda forma della decisione 20.

## Autorevisione

- Completezza: i 16 agenti del brief sono tutti toccati, `finding-verifier.md` e `spec-auditor.md` no; i cinque punti dell'implementatore e le due forme della riga ci sono; i revisori del task controllano la riga e il diff, i finali hanno la voce in «Cosa controllare», gli avversari hanno la voce con le sette situazioni (input esterni, login, permessi, dati personali, segreti, file caricati, chiamate verso l'esterno) e le tre domande. Ci sono le due righe di `comandi.md`.
- D13: la sezione nuova sta dopo `## Il lavoro` e fuori da «Area» in tutte le copie; nessun id `R-…-NN` e nessuna delle tre frasi vietate nei paragrafi nuovi (lo controllano i test); ogni avversario ha un solo blocco JSON (`test_audit_json_fields_in_agent_text` verde).
- Il frontmatter è invariato (`git diff` non tocca le righe tra `---`). Il resto del testo degli agenti non cambia: il diff aggiunge solo le righe nuove e la voce `done`.
- Nessuna sezione obbligatoria nuova del piano o della spec, nessuna regola in `rules-base`.

## Dubbi

- La voce del revisore del task dice che una riga `Sicurezza:` assente è un rilievo, «con la regola dell'area se ce n'è una, altrimenti con il passo del piano». Per una riga che manca in un task senza profilo non c'è un passo del piano specifico. Il revisore citerà probabilmente il passo del task, e la gravità resta alla sua scala (la decisione 20 non la fissa). Non ho aggiunto una gravità: sarebbe una scelta nuova.
- Il preflight (D2) avverte già che gli avversari con la voce nuova faranno quasi certamente un rilievo sulla spec e sul piano della prova del Task 9. Non è un difetto di questo task, ma il Task 8/9 deve tenerne conto.

## Fix round 1

Decisioni del controller in `task-2-fix-1.md`: corretti m1, m2, m3, m4, m6, m7 e m8; m5 resta com'è. Gli stessi paragrafi, parola per parola, nel generico e in ogni copia (sostituzioni con uno script, un'ancora esatta per file). Nessun altro testo degli agenti cambia; D13 rispettata (nessun id `R-…-NN`, nessuna delle tre frasi, un solo blocco JSON negli avversari).

### Cosa ho cambiato

- **m1 (test).** `test_security_by_design_in_every_implementer` vuole le cinque voci della sezione con i titoli in grassetto, in quest'ordine (`**Input non fidato validato al confine**`, `**Nessun segreto nel codice né nei log**`, `**Accesso chiuso per difetto**`, `**Valori predefiniti che rifiutano**`, `**Permessi minimi**`), più «caso negato». `test_reviewers_check_security_line` guarda la sola voce e non più tutta la sezione, con `assertEqual(len(items), 1, …)`. Nel revisore del task cerca `` `Sicurezza:` ``, «diff», «caso negato» e «valori predefiniti»; nel revisore finale «validato al confine», «segret» e «caso negato». `test_adversaries_look_for_security` vuole «input dall'esterno» e fa `assertEqual(len(items), 1, "voce sulla sicurezza assente o ripetuta")` prima di usare la voce: niente più `ValueError`.
- **m2 + m4 (revisore del task e cinque copie, voce di «Parte 2: qualità»).** La frase «Una riga assente, o un diff che la smentisce, è un rilievo, …» diventa:
  > La sola riga assente è un rilievo `minor`, con `file` il primo file del diff, `line` 1 e `rule` il passo del task: non chiede modifiche. Un diff che smentisce la riga, o che ha uno di questi difetti, è un rilievo con la regola dell'area se ce n'è una, altrimenti con il passo del piano, e la gravità che gli dà la scala di «Standard del revisore». Ciò che la sezione «Sicurezza fin dal progetto» chiede all'implementatore (per esempio il test del caso negato) non è `extra`.

  È coerente con il verdetto dello stesso file: `file` (stringa), `line` (intero 1), `rule` (il passo, come `"Task 3, passo 2"` dell'esempio), `severity` `minor`, che secondo «Standard del revisore» è una nota e non ferma il task.
- **m3 (implementatore e cinque copie).** In coda al paragrafo di chiusura della sezione:
  > La riga sta in fondo alla stessa stringa di `done`, senza andare a capo: un a capo vero dentro un valore JSON rende il report illeggibile.

  La voce `done` di «Report finale» diventa «con in fondo, nella stessa stringa e senza andare a capo, la riga `Sicurezza:` della sezione «Sicurezza fin dal progetto».». Il nome «riga `Sicurezza:`» resta, perché lo usano il piano, il Task 9 e `comandi.md`.
- **m6 (`plan-adversary.md`).** La voce chiude ora così:
  > … e cosa succede con un input ostile; basta che lo dica la spec approvata a cui il piano rimanda, senza ripeterlo. Se non lo dicono né il piano né la spec approvata, è un rilievo.

  `spec-adversary.md` non cambia.
- **m7 (`final-reviewer.md`, `final-database.md`).** La frase finale della voce diventa:
  > Un difetto si segnala una volta sola, anche se riguarda pure «Qualità e architettura», con la regola dell'area se ce n'è una, altrimenti con il passo del piano.
- **m8 (`docs/uso/comandi.md`, `/tollgate:start`).** Il paragrafo diventa:
  > La sicurezza fin dal progetto vale in ogni lavoro con agenti (L1 e L2), anche quando nessun profilo di sicurezza è attivo: in L2 gli avversari di spec e piano chiedono chi può usare ciò che si costruisce, quali dati e segreti tocca e cosa succede con un input ostile, e ogni implementatore chiude il report con la riga `Sicurezza:` (cosa ha considerato, oppure che il task non tocca input esterni, accessi, dati o segreti). In L0 implementa la sessione, senza agenti, e la riga non c'è.

I test controllano anche le frasi nuove: «senza andare a capo» nella sezione e nella voce `done` (m3); «La sola riga assente è un rilievo `minor`», «`line` 1», «`rule` il passo del task» e «non è `extra`» nella voce del revisore del task (m2, m4); «si segnala una volta sola» nella voce del revisore finale (m7); «spec approvata» nella voce di `plan-adversary` (m6).

### Mutazioni B, F e G (prima di toccare il testo degli agenti)

Su copie `git archive HEAD` in `mktemp -d /tmp/tollgate-mut-XXXXXX`, cancellate dopo l'uso. Ho applicato ogni mutazione a tutti i file interessati e lanciato `python3 -B -m unittest tests.test_manifest`, una volta con il test di `cf770f1` e una volta con il test stretto da m1. B: tolte le prime tre voci della sezione dai sei implementatori. F: voce dei sei revisori del task ridotta a «- Sicurezza fin dal progetto: `Sicurezza:` diff.». G: voce dei due revisori finali ridotta a «- **Sicurezza fin dal progetto**: caso negato.».
```
== mutazione B, test vecchio: OK
== mutazione B, test nuovo: FAILED (failures=6)    implementer, implementer-ai, -infra, …
== mutazione F, test vecchio: OK
== mutazione F, test nuovo: FAILED (failures=6)    task-reviewer, reviewer-ai, -infra, …
== mutazione G, test vecchio: OK
== mutazione G, test nuovo: FAILED (failures=2)    final-reviewer, final-database
```
Con la voce di `spec-adversary` tolta (copia temporanea dei file tracciati), il test dà `AssertionError: 0 != 1 : voce sulla sicurezza assente o ripetuta` e non più `ValueError`.

### RED (controlli delle frasi nuove, prima del testo)

`python3 -B -m unittest tests.test_manifest`:
```
FAIL: test_adversaries_look_for_security (agent='plan-adversary')
FAIL: test_reviewers_check_security_line (agent='task-reviewer'), reviewer-ai, -infra, -backend, -frontend, -database, final-reviewer, final-database
FAIL: test_security_by_design_in_every_implementer (agent='implementer'), -ai, -infra, -backend, -frontend, -database
Ran 64 tests in 0.658s
FAILED (failures=15)
```

### GREEN

- `python3 -B -m unittest tests.test_manifest tests.test_docs`: `Ran 71 tests` / `OK`.
- `claude plugin validate --strict .`: uscita 0.
- `PYTHONWARNINGS=error::ResourceWarning tests/run` (log in `W/suite-task-2-fix-1.log`, su HEAD con il Task 3):
  ```
  == Python 3.11.16
  Ran 4366 tests in 2299.430s
  OK (skipped=13)
  == Python 3.13.5
  Ran 4366 tests in 2278.317s
  OK (skipped=11)
  exit 0
  ```
  Nel log non ci sono «unclosed» né avvisi.

### Commit

Il commit è nuovo, senza amend, sopra `e27db19`: `c0a60df`, «tollgate C2: sicurezza fin dal progetto, rifiniture dopo la revisione». File: i 15 agenti toccati (`spec-adversary.md` non cambia), `docs/uso/comandi.md`, `tests/test_manifest.py`.

### Dubbi

Nessuno nuovo. m5 («dati» largo nella seconda forma) resta per decisione del controller.
