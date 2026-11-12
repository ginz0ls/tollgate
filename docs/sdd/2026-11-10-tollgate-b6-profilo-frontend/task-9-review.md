# Task 9: revisione (pacchetto 34ea952..c462940, commit c462940)

Sola lettura. Nessuna suite rilanciata. Controlli fatti con `grep` e con letture mirate di `bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py`, `bin/tollgate_analysis/profiles.py`, `templates/profiles/frontend.toml`, `agents/*-frontend.md`, `hooks/run`, `tests/`.

## Aderenza

- ✅ Quattro file toccati, tutti quelli del brief: spec del nucleo, piano principale, progetto di B (solo la riga di avanzamento), catalogo. Nessun file approvato vietato è toccato (`docs/profili/*`, `skills/`, `docs/profili/verifiche/` non compaiono nel diff).
- ✅ Intestazione «Revisione: **33**» e riga 33 della sezione 20 (`nucleo-design.md:2066`, dopo la 32). La riga riporta decisioni 1-17 (coincidono con `decisions.md`), ruling D1-D10, il divieto di `node`/`npm`, la scelta dell'utente («Approva e tieni tutto», ventidue punti: `docs/profili/frontend.md` dice «ventidue»).
- ✅ D10 e D3. 11.2 riscrive «`init` non propone i pattern così come sono» in «per le forme a cartella e a nome ... (la forma `ext` è l'eccezione)»; la forma `name` è «dopo e solo se nessuna forma a cartella ha acceso il file (seguita da `ext`)». Il codice conferma (`init.py:_match`, 217-237: cartella, poi `name`, poi `ext`; i documenti non accendono `ext`; `concrete_for` dà il pattern stesso). In 6.3 a parità vince il primo blocco dichiarato (`profiles.vertical_for`, `s > best_score`) e `init` scrive i blocchi in ordine alfabetico (`fragments.load_approved` ordina con `sorted(directory.glob(...))`); P37 e P38 sono nella tabella.
- ✅ Tabella P1-P38 in 6.3: confrontata riga per riga, con uno script, con la tabella della decisione 4 del piano di B6. Le 36 righe note coincidono nei casi «A runtime» e il «Perché, costo» è un riassunto fedele (nessun costo perso o cambiato); P37 e P38 sono quelle dei ruling. I test `test_real_precedence_p1` … `p38` esistono tutti (38 in `tests/test_init.py`).
- ✅ Quarta forma in 11.4: `_EXT` è `\*\*/\*\.([A-Za-z0-9]+)`, quindi `**/*.sql`, `**/*.json`, `**/*.Dockerfile` accettati e `**/*.module.css`, `src/**/*.tsx`, `*.tsx`, `**/*.{tsx,jsx}` rifiutati, come scritto. Frammento: 9 pattern nell'ordine dichiarato, `dod = []`, `commands = {}`, `skills = []`, `reviewer_skills = []`, 8 marcatori, 6 prefissi di `exclude`, nessun `cross`: tutto coincide con `frontend.toml`.
- ✅ Numeri: 12 regole e 10 `[blocca]` (01-09 e 11) coincidono con `skills/rules-frontend/SKILL.md`; 3894 test e `skipped=13` (3.11) / `11` (3.13) con `suite-task-9.log`; 1,45 = 0,51 + 0,94, Claude Code 2.1.322, token 110.902 e 68.698, 1.238 caratteri, «lo accendono 4 file», `paths = ["**/*.tsx", "/web/**", "src/components/**"]` coincidono con il rapporto della prova (versione `HEAD`). `525d8d8` è su `main`.
- ✅ Divieto di `node`/`npm` per `implementer-frontend` in ogni progetto scritto come costo, in 6.3 (con il ciclo RED/GREEN che non gira, il rimedio del `dod` e «la revisione finale lo riceve come costo da valutare») e nel blocco «A B7-B8, da B6».
- ✅ Pagina approvata di `backend` che invecchia: in 11.2 e nel blocco «A B7-B8, da B6», con i casi che restano veri (P10, P32, P33, P38).
- ✅ Sezione 15 «Prove di B6»: 32 righe di «Copertura» → 32 righe della tabella (script: nessuna riga manca; differenze solo di formattazione nella colonna Task, tranne il rimando a `test_a11y_rules_name_a_wcag_criterion` e a `test_rule_ids_consecutive`, aggiunti). Ho estratto tutti i 112 nomi `test_...` citati nella sezione e cercato `def <nome>` in `tests/`: nessuno manca. Controllato a campione che il file attribuito sia quello giusto (`test_profiles.py`, `test_wrapper.py`, `test_taskcmd.py`, `test_init.py`, `test_b1_scripts.py`).
- ✅ Ordine corretto in 7.1 (`READONLY_TYPES` di `hooks/run:56` e `config.DEFAULTS` contengono `reviewer-frontend`), 7.3 (`tools: Read, Grep, Glob, Bash, WebFetch` in `agents/reviewer-frontend.md`), 8.7 e catalogo 2, 2.1, 2.2, 2.3, 3, 4, 6.
- ⚠️ La prova reale (16, sezione 15) dipende dal rapporto `docs/verifiche/2026-11-10-b6-prova-flusso.md` che un altro implementatore sta correggendo (diff non committato). Dalle correzioni emerge che: il task 1 non è un testimone pulito del precaricamento; il modello ha lanciato `tollgate plan-check`, che non esiste (`exit=2`, senza effetto); le evidenze hanno una cartella `prepara/` in più. Spec 16 e sezione 15 sono già compatibili (dicono che il piano non è un testimone pulito e che il segnale sta nel task 2 e nel revisore; nessun programma vietato), ma non citano né il comando inesistente né il task 1. Da riallineare a correzione conclusa (vedi Minor 3).
- ⚠️ `suite-task-9.log` non mostra se la corsa è stata fatta con `PYTHONWARNINGS=error::ResourceWarning` (il brief, Step 4, chiede entrambe le corse). Il Stato del piano scrive «con `PYTHONWARNINGS=...` all'ultimo giro con codice (Task 7)», quindi non attribuisce la garanzia al Task 9; è documentazione senza codice nuovo. Le tre corse finali la coprono.

## Punti di forza

- La rev 33 è costruita sul codice reale: ogni affermazione verificabile (forma `ext`, ordine delle forme in `_match`, `_concrete_paths`, ordine alfabetico, `active_profiles` che resta attivo con un `.tsx` sotto `server/`) corrisponde a `init.py` e `profiles.py`.
- I costi della tabella sono riportati con la stessa gravità del piano e portano un rimando a un test; gli scostamenti dal catalogo sono dichiarati (`app/**/page.*` esce, `**/*.astro` entra, `dod` vuoto).
- Il blocco «A B7-B8, da B6» raccoglie tutti i `minor (deferred)` dei Task 1-7 che toccano B7-B8 (verificato contro `progress.md`), più le ruling D1, D5 e quelle su node/npm e sulle pagine che invecchiano.
- Lo Stato del piano e la riga di avanzamento del progetto sono onesti sul punto di partenza: B5 portata a «unita su `main`», B6 «unione in attesa».

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

1. `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md:207` (sezione 9, voce «Chiuso da B4 per `infra` e da B6 per `**/*.{tsx,jsx}`...»): l'intestazione è stata riscritta ma il corpo conserva «La forma con `*` iniziale resta rifiutata (accenderebbe ogni file di un tipo): chi ne ha bisogno (`database`, `frontend`) decide la forma nel piano della sua fetta». Da B6 `**/*.<estensione>` è accettata (11.4), quindi la frase al presente è falsa. Correzione: farla passare al passato con «fino a B6» o aggiungere «ora ammessa nella sola forma `ext`», come si è fatto per le altre voci.
2. Catalogo `2026-10-08-tollgate-profili-verticali.md` (sezione 2, «Percorsi predefiniti»): la frase «`init` non li copia così come sono: propone percorsi concreti» resta intatta e la deroga per `ext` compare solo più avanti nello stesso paragrafo. Non è falso come in 11.2 (il paragrafo la dice), ma D10 chiedeva coerenza di quelle frasi. Correzione facoltativa: «(salvo la forma `ext`, sotto)».
3. Spec 16 (riga «Prova reale corta») e piano sezione 15: dopo che il rapporto sarà corretto, aggiungere il comando inesistente `tollgate plan-check` (nessun effetto) e dire che il task 1 non prova il precaricamento; oggi lo si deduce solo dalla frase sul piano. Il numero «Stato (10 novembre 2026)» in testa al piano non è stato aggiornato pur riportando fatti dell'11/11.
4. La voce «A B6-B8, da B5» della sezione 9 dice «Stato dopo B6 in testa a ogni voce che lo riguarda», ma due voci («Dai minori del ledger, `init` e `fragments`» e la voce sul rinvio di `routes/`) lo portano a metà o in fondo. Solo estetico.

## Valutazione

**Qualità del task:** Approvato.

**Motivo:** la rev 33 non contraddice il codice (forma `ext`, `fragments.py`, `init.py`, `frontend.toml`, agenti, `hooks/run`) né il progetto di B; i numeri e i nomi dei test coincidono con i file; D3 e D10, P37-P38, il costo di `node`/`npm` e la pagina di `backend` che invecchia ci sono tutti. Restano quattro minori di testo e la dipendenza dal rapporto della prova in correzione.
