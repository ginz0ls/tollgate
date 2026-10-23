# Revisione Task 15 (aeb5109..201a868)

### Aderenza
- ✅ `skills/init/SKILL.md`: opzioni (`--propose|--update` mutuamente esclusivi e obbligatori, `--merges-per-month` predefinito 20, `--service NOME=IMMAGINE[,PORTA]`) come in `bin/tollgate_core/cli.py:95-107`; codici 0/1 come `init.OK, init.REFUSED` (`bin/tollgate_flow/init.py:25`); rifiuti `tollgate: …` (`init.py:58,356-394`); «nulla da aggiornare» exit 0 (`init.py:403-418`); «Durata del gate non misurata» (`init.py:229`); righe `modalità del gate`, `protezione incompleta: manca`, `workflow esistente fuori regola`, `avviso:` esistono (`init.py:427-433`). Passi nell'ordine del README (copia, commit prima della protezione, `protect.sh` solo con protezione da attivare; `init.py:262-290`). Mai copia, mai `protect.sh`; «non determinata» rimanda a `! <programma> init --propose …` (`init.py:376-380`). Token separato.
- ✅ Programma sempre `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`; nessuna skill contiene «P4» (regex `\bP[0-9][a-z]?\b`).
- ✅ `start`: avvisi di Actions, protezione e `detect` con issue di sentinella coincidono testualmente con `start.py:308-341`.
- ✅ `execute`: `--from-gate`, marcatore `<!-- tollgate-verdict`, solo commenti del bot, SHA dal marcatore, rifiuti (`fixtask.py:20-65`).
- ✅ `status` rimanda a `start` (ruling accettato).
- ✅ `finish`: tre tipi di riga con i prefissi stampati (`finishcheck.py:161-163,260,275`); `FOLDED` = guard_scope/must_have/approvals (`finishcheck.py:29`); riga salvata `da leggere (voci del gate): …` come `finishcheck.py:275-278`; «da leggere» rosso su `tollgate/attention` come `attention.py` docstring. D21b coperto.
- ✅ D18a: i sottocomandi `gate` si controllano contro `tollgate_gate.cli.build_parser()` (`tests/test_skill_contract.py:85-102`).
- ⚠️ `claude plugin validate --strict .` riportato dall'implementatore, non rilanciato.

### Punti di forza
Le righe citate delle skill corrispondono quasi tutte parola per parola al codice; la regola «mai copiare/mai protect.sh» è esplicita e testata; `finish` spiega bene perché le righe di attenzione non sono errori.

### Rilievi

**Important**
1. `tests/test_skill_contract.py` (diff, righe ~93-107 rimosse): `test_options_exist_in_parser` è stato **cancellato**, non esteso. Il report dice «opzioni anche del parser gate» ma nel file non c'è più alcun controllo sulle opzioni (`grep` su `options` dà zero). Le skill citano ora `--propose`, `--update`, `--service`, `--merges-per-month`, `--from-gate` ecc.: un'opzione inventata o rinominata non farebbe fallire nulla, ed è esattamente il contratto che il task doveva rafforzare. Verifica da me (script one-shot con parser nucleo + gate): oggi tutte le opzioni esistono, quindi basta ripristinare il test e far camminare anche `gate_cli.build_parser()` (`walk` su entrambi). Il report inoltre afferma una cosa non vera.

**Minor**
2. `skills/finish/SKILL.md` (riga delle `informative:`): elenca «PR non `tg/*`» tra le informative, ma `not_tg_branch` è in `READ` (`bin/tollgate_gate/attention.py:14`, emessa in `evaluate.py:652`). Correggere spostandola tra le «da leggere» o toglierla. Il test D21b controlla solo i prefissi, non l'elenco: potrebbe derivare dalle chiavi di `attention.GROUPS` per non far divergere skill e codice.
3. `skills/init/SKILL.md` («Entrano nel job `head` di `tollgate-run`») e, con lo stesso testo, `bin/tollgate_flow/init.py` (README, «Messi nel job `head` di `tollgate-run`»): dopo il giro 1 del Task 11 i servizi entrano in tre job (`head` e `base` di `tollgate-run`, `ids` di `tollgate-base`; `install.SERVICES_WORKFLOWS = {"run": 2, "base": 1}`, `install.py:23`). Il testo è falso. Correggere skill e README (il README è fuori dal diff ma è la fonte della frase) e l'help `--service` se serve.
4. `tests/test_skill_contract.py:104-111` (`test_gate_calls_are_checked_against_the_gate_parser`): D18a è coperto solo da un test sintetico che asserisce fatti sul parser (`"sentinel" in gate_top`, `"inventato" not in gate_top`) e sulla regex, ma non esercita il ramo `if first == "gate"` di `test_program_subcommands_exist_in_parser`: togliendo quel ramo nessun test fallisce. Per un solo caso non basta: estrarre il controllo di una chiamata in una funzione (`check_call(first, second)`) usata dal test vero e da quello sintetico (con un caso valido e uno inventato che deve fallire). Se nessuna skill cita `gate` oggi, è comunque il modo di avere la garanzia.
5. `test_init_skill_never_copies_or_protects` e `test_finish_separates_…` sono controlli di presenza di sottostringhe: provano che la frase c'è, non il comportamento. Accettabile per un contratto di testo, ma `assertIn(f'"{prefix}', code)` (`finishcheck.py`) è quasi una tautologia.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** contenuto delle skill accurato e coerente col codice, ma il contratto è stato indebolito: il test delle opzioni è sparito (e il report dice il contrario). Va ripristinato esteso al parser gate; i minori 2-4 sono correzioni rapide nello stesso giro.
