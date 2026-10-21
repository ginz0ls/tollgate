# Revisione Task 2 (P3c): analisi pura, forma della spec, intestazioni, recinti

Base 835aa1c, punta cf5f0e4. Eseguito solo `python3 -B -m unittest tests.test_specdoc tests.test_approvals tests.test_plan` (55 test, OK) e due sonde di `parse_header`/`render_approval` in scratch; nessun'altra esecuzione.

### Aderenza
- ✅ `specdoc.py`: `SLICES_SECTION`, `PITCH_SECTIONS`, `slices`, `slice_titles`, `pitch_problems` con il testo richiesto; recinti saltati con `plan._Fences` (specdoc.py:18); intestazioni `##` e voci dentro i recinti ignorate; senza sezione o senza voci 1 (specdoc.py:38). Decisione 8 (parte pura) rispettata.
- ✅ `approvals.py`: `REPORT_KINDS`, `SEVERITIES`, `parse_header` comune, `parse_approval` sopra di essa con contratto invariato (chiamanti adopt.py:157, openpr.py:405, finishcheck.py:194/253 compatibili), `parse_report_header` (kind, `number` intero >= 1, `counts` con le quattro chiavi intere >= 0), `approval_listing`.
- ✅ D12: `render_*` sollevano `ValueError` su a capo, `"`, categorie Cc/Zl/Zp (approvals.py, `_render_value`); test dedicato con `\n`, `\r`, `\x00`, `\x1b`, `"`; coperti anche i separatori che `splitlines` spezzerebbe (\x0b, \x0c, \x1c-\x1e, \x85, U+2028/9 sono tutti Cc/Zl/Zp).
- ✅ D18: `_value` toglie il commento dopo un valore tra virgolette (triage 30); round-trip approvazione e report verificato, compresi `None`, stringa vuota, stringa numerica tra virgolette (resta stringa).
- ✅ D13 e D3: `locate_spec_approval` è pura, docstring esplicito sul fatto che `files` lo sceglie il chiamante; propria con `path` uguale e qualunque `sha`, poi altre issue con `sha == spec_blob` (o solo `path` con `spec_blob=None`), vince il numero più basso (ordinamento numerico, non lessicale).
- ✅ D15: `check_l2` copre spec trovata e corrente, `plan-approval` con `sha` e `spec_sha`, report della spec nella cartella dell'approvazione trovata (anche di un'altra issue), `lens` solo con `slices > 1` e `lens: closed`, `adversarial: off` per spec e piano, report con intestazione non valida non contano. Ogni messaggio nomina il file o il report.
- ✅ D17: `_FENCE_OPEN` con al più 3 spazi (plan.py:16); vale per `check_plan` e `task_text` perché entrambi passano da `_Fences`; anche la chiusura con 4 spazi non chiude (corretto CommonMark). Unico uso di `_FENCE_OPEN` nel repo: plan.py:88.
- ✅ Strati: `tollgate_analysis` importa solo se stesso; stdlib soltanto.

### Le tre scelte non fissate dal piano
1. Approvazione mancante o superata, niente ricerca dei report: coerente con D15, che lega la cartella dei report all'approvazione trovata e corrente; senza di essa il problema è già detto. Accettabile. Piccola asimmetria: il ramo del piano (approvals.py, dopo `is_current(header, plan_blob)`) continua invece a cercare spec_sha e report anche con piano superato. Minor.
2. Approvazione propria con `sha` vecchio che vince su quella di un'altra issue con `sha` giusto: è la lettera di D13 («qualunque `sha`: chi chiama controlla `is_current`»), e `check_l2` la trasforma in «cambiata dopo l'approvazione». Corretta. Il caso reale (una fetta successiva con approvazione propria) è raro; nessun problema.
3. `counts` con esattamente le quattro gravità: coerente con il brief («le quattro chiavi») e con D18 («`counts` valido»); più rigido di quanto serva ma chiude la porta a chiavi spurie. Accettabile; va tenuto presente ai Task che scrivono i report (devono emettere solo le quattro).

### Punti di forza
- `parse_header` unico lettore; `parse_approval` ridotta a un filtro; nessuna duplicazione.
- Rendering rigoroso (nomi di campo, bool, tipi non ammessi, voci di dizionario) e round-trip testato per entrambi i tipi.
- Test che asseriscono: matrice di `check_l2`, fetta successiva con report in un'altra cartella, `blob=None`, intestazione di approvazione scambiata con quella di report, recinto a 3 e 4 spazi.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
- approvals.py, ramo piano di `check_l2`: `plan-approval.md` non confronta `header["path"]` con `plan_path`. Lo `sha` uguale implica stesso contenuto, quindi innocuo; basterebbe un controllo se si vuole il messaggio giusto per un piano spostato.
- approvals.py, `_reports`: il report non è legato allo `spec_sha`/`number` del nome file; un report scritto su una versione precedente della spec conta. ⚠️ D15 chiede solo «intestazione valida», quindi conforme; da tenere presente per il gate di P4.
- approvals.py, `check_l2`: `slices` non intero nell'intestazione (es. `"3"`) è ignorato in silenzio e il `lens` non viene richiesto. Fail-open su un file scritto solo dalla CLI; basterebbe trattarlo come problema.
- approvals.py, `_value`/`_PAIR`: chiavi duplicate in `counts` (e in `parse_header`) vincono l'ultima, senza segnalazione.
- tests/test_approvals.py, `test_spec_changed_after_approval`: asserisce solo che ci sia un problema stringa; non verifica il messaggio «cambiata dopo l'approvazione». Manca un caso: approvazione propria con `path` diverso che cade sull'altra issue.
- approvals.py, `approval_listing(paths)` senza annotazione di tipo (il brief dice `list[str]`).

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti del brief e voci D3/D12 di carry soddisfatti sul diff, decisioni 8, 13, 15, 17, 18 rispettate, test mirati verdi, nessun rilievo Critical o Important; i minori sono rifiniture.
