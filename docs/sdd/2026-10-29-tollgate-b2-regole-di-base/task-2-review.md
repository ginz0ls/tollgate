# Revisione Task 2 (d9ca5de..7e59364)

### Aderenza
- ✅ Nessun file di `bin/` né di `hooks/` cambia: il commit tocca solo `tests/test_eval_cases.py` e `tests/test_taskcmd.py` (stat del pacchetto; `git diff --stat d9ca5de..7e59364 -- bin hooks` vuoto).
- ✅ Il file di prova non è nel commit e `git status` del worktree è pulito. Nessuna cartella `skills/rules-base/` nel worktree.
- ✅ Azione `read` (`tests/test_eval_cases.py`, `_Session._do_read`): `PostToolUse` di `Read` con `tool_input.file_path` e `agent_id` dell'implementatore (registrato dal `SubagentStart` di `impl_launch`). `lookups.observed` (`bin/tollgate_core/lookups.py:62`) usa solo `file_path`, quindi l'assenza di contenuto in `tool_response` non falsa la simulazione. Il percorso `{wt}/rel` è sostituito come per gli altri passi.
- ✅ Nota «Nessuna fonte esterna»: passa da `_do_bash`, che esegue davvero `research submit <k>`. Sezioni `Letto nel progetto` / `Nessuna fonte esterna` / `Cosa ho trovato` corrispondono a `bin/tollgate_analysis/research.py:13-16`. La validità è provata dall'esecuzione con interruttore acceso: la `Write` successiva non è negata (altrimenti i test sarebbero rossi).
- ✅ D1: corretti s1, s2 (solo cammino della scorciatoia), s3, `cycle` di s6 (riusato da e4); s9 non toccato. La `Read` va su un file che il caso ha già (`src/calc.py`, `tests/test_calc.py`, `README.md`). Asserzione di e4 aggiunta (`out[4]` è il `Write`: 0 bash, 1 agent, 2 read, 3 submit, 4 edit; indice giusto).
- ✅ Indici `out[n]` spostati: s1 (+2: 4→6, 5→7, 6→8; direct 5→7), s2 (1→3, 2→4), s3 (1→3, 2→4, 3→5; bash 3→5). Ogni asserzione punta allo stesso passo di prima (veto della prima modifica, esito del `verify`, `waiver add`, commit negato). Nessuna asserzione indebolita; in più s3 `unchanged_file_path` asserisce «file fuori scope:», che rafforza.
- ✅ D2/D14/D16 rispettati nel report (attesi i due rossi `test_docs` e `test_b1_scripts:555`; seconda misura limitata ai moduli rossi, poi suite intera senza file).
- ✅ Decisione 7(a): `ReviewDoneTest.prepare(approved=False)` usa sempre una radice temporanea tramite `mock.patch.object(taskcmd.db, "BIN_PATH", …)`; il test «enforced» passa `approved=True`. Il test `test_review_prepare_enforced_...` conserva la stessa prova.
- Verifica mia: copia di `HEAD` in una cartella di lavoro temporanea (fuori dal repo), moduli `test_eval_cases` + `test_taskcmd` (155 test), con e senza il file di prova: stesso esito nei due casi, un solo rosso identico (`S?` test sul testo del veto `task start`, regex `'[^']+'` contro un percorso non quotato). È un artefatto della mia copia (percorso senza spazi, quindi non quotato da `shlex`), non del commit, ed è uguale con e senza interruttore. Gli altri 154 sono verdi in entrambi.

### Punti di forza
- Il banco riproduce il comportamento vero dell'implementatore invece di aggirare il veto; helper unico `research_prep` (DRY), docstring che dichiara il perché.
- Modifica minima e chirurgica; priorità (a) della decisione 7 rispettata dove possibile.
- Asserzione aggiunta in s3 che impedisce al veto della nota di mascherare quello di scope; asserzione di e4 che documenta la dipendenza.

### Rilievi
Critical: nessuno. Important: nessuno.

Minor
- `tests/test_taskcmd.py:476,491,660`, `tests/test_fixtask.py:180`, `tests/test_criteria_p3a.py:114`: chiamano `review_prepare` / `task review-prepare` con la radice vera. Non asseriscono sulla gravità e sono verdi con il file di prova (misura dell'implementatore), quindi non dipendono dall'interruttore, ma restano implicitamente legati al repo. Rendere esplicita la radice solo se uno di questi test comincia ad asserire sulla nota.
- `tests/test_eval_cases.py` (test `s3_the_veto_does_not_depend_on_the_starting_folder`, edit senza `PREP`, riga ~957): con interruttore acceso la prima modifica senza nota è negata comunque; l'asserzione `assertIn("file fuori scope")` regge solo perché il testo del veto contiene entrambi i motivi. Misurato verde, ma fragile se il messaggio cambia. Aggiungere `*self.PREP` per isolare il motivo.
- Il riferimento «S?» sopra: la mia misura non ha toccato il repo; il rosso della copia non è del commit.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** la suite è resa indipendente dall'interruttore con modifiche solo di test, l'azione `read` e la nota simulano fedelmente l'implementatore, gli indici e le asserzioni sono corretti e nulla è nel commit che non debba esserci. Restano solo due rifiniture Minor.
