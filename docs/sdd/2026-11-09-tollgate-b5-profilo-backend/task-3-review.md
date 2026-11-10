# Revisione Task 3 (dcae551..8e5574c)

Controlli fatti: pacchetto di revisione, skill, frammento, test, `comandi.md`; confronto con le fonti in `fonti/backend/` (solo per obblighi aggiunti e frasi copiate); `python3 -B -m unittest tests.test_rules_backend` (22 test OK); ricerca di nomi privati (nessuno); sovrapposizione di sequenze di 4 parole tra skill e fonti (solo URL e il titolo di sezione «Prefer Addition Over Modification»).

### Aderenza
- ✅ Frontmatter, titolo, sezioni, 12 regole consecutive, 10 `[blocca]` (tutte su diff o report), 10 e 11 non bloccanti, nessun `approved`, 75 righe (<150).
- ✅ Riga «Un endpoint è…» con le tre forme (`skills/rules-backend/SKILL.md:10`); `onRequest` in `functions/` è nella pagina di Pages Functions.
- ✅ Frammento: sei pattern in ordine, 24 marcatori nelle due forme di virgolette, `exclude = ["supabase/"]`, `skills/reviewer_skills/commands/dod` vuoti, un commento con la fonte per gruppo; `export function POST(` e `ExportedHandler<` restano; `workers/**` assente.
- ✅ Decisioni del controller: R-BACKEND-07 cita pagine binding/segreti, R-BACKEND-03 le skill MIT; sezione «Fonti» dice che da everything-claude-code si prendono solo temi con parole nostre; nessun file in `LICENSES/`; nessun marcatore in `bin/` (test); nessuna `--opzione` nella skill (R-BACKEND-12 dice «l'opzione della modalità locale»); `comandi.md` senza «Argomenti:», «solo l'utente» o programma nudo.
- ✅ Report: le affermazioni sulle fonti per regola reggono (controllate 03, 06, 07, 08, 12); RED/GREEN credibili.
- ✅ R-BACKEND-02: l'estensione a libreria standard e framework è dichiarata «scelta nostra».
- ⚠️ Non verificabile da me: la corrispondenza fonte per fonte dei marcatori e dei pattern (Task 4), la suite completa (dichiarata verde nel report, non rilanciata).

### Punti di forza
- Le regole sono con parole proprie; nessuna citazione lunga; `Fonte:` precise per sezione.
- La regola sull'endpoint dice come riconoscerlo nel diff; ogni `[blocca]` ha un giudice concreto.
- Il test delle fonti ammesse (`test_every_rule_names_a_source_of_the_allowed_kinds`) è una variante ragionata del test di `infra`; le trappole di testo e i marcatori in `bin/` sono coperti.
- Il frammento è commentato per gruppo e coerente con le decisioni 2, 3, 4, 8, 9, 12.

### Rilievi

**Critical:** nessuno.

**Important**
1. `skills/rules-backend/SKILL.md:41` (R-BACKEND-09, `[blocca]`, imposto dal piano). «Un caso d'errore per ogni input che l'endpoint valida e per ogni risorsa che può mancare» è un obbligo senza fonte. Il catalogo 2.3 dice solo «test delle API»; la lista «Verification» di `api-and-interface-design` (righe 356-360 della copia) non parla di test. L'obbligo è anche pesante come regola bloccante (richiede di enumerare input e risorse). Correzione: o limitare l'obbligo a ciò che le fonti dicono (un test che chiama l'endpoint, con caso riuscito) e portare il resto come «scelta nostra» in «Da decidere tu» (Task 4), oppure dichiararlo «scelta nostra» nella `Fonte:` e farlo confermare all'utente nel Task 5. Il vincolo «nessun obbligo senza fonte se non dichiarato scelta nostra» oggi non è rispettato.
2. `skills/rules-backend/SKILL.md:35` (R-BACKEND-05, `[blocca]`). Il pezzo «e che il task lo chiede» non è in «Hyrum's Law» né in «Prefer Addition Over Modification» (che parlano di compatibilità, non di chiedere il permesso al task). Stesso trattamento: dichiararlo scelta nostra o toglierlo e lasciare «il report dice chi li usa».

**Minor**
3. `SKILL.md:55` (R-BACKEND-12). Due obblighi in una regola; la seconda parte («il report non riporta comandi… che scrivono sui dati di un servizio in linea») si giudica male: un report che tace passa. Meglio «il report non dice di aver lanciato…» o spostarla in R-BACKEND-12b/nota sul veto. «o un database» estende la fonte (Wrangler su KV/D1/R2) a ogni database senza dichiararlo.
4. `SKILL.md:51` (R-BACKEND-08). La parte «né nel corpo di una risposta d'errore» ha base in `ecc-code-reviewer` («Error message leakage») e nella riga 83 di `api-and-interface-design`, ma la `Fonte:` cita solo `security-reviewer` (principio «Fail Securely», debole). Aggiungere `agents/code-reviewer.md` alla `Fonte:`.
5. `tests/test_rules_backend.py:31-34` (`USER_CHOICES`). Copre solo R-BACKEND-01; R-BACKEND-02 (riga `backend` della 3.4) e R-BACKEND-12 (sezione 12) sono scelte dell'utente e non sono fissate.
6. `tests/test_rules_backend.py:~151` (`test_endpoint_rules_say_how_to_recognize_an_endpoint`). L'`if any(...)` finale è tautologico dopo l'`assertEqual(len(lines), 1)`: o si toglie o si inverte (se nessuna regola parla di endpoint, la riga non serve).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** struttura, frammento, test e vincoli di forma sono solidi; due regole bloccanti (R-BACKEND-09 e R-BACKEND-05) aggiungono obblighi senza fonte e senza la dichiarazione «scelta nostra», contro il vincolo del piano (anche se in parte imposti dalla bozza del piano). Correzioni piccole.
