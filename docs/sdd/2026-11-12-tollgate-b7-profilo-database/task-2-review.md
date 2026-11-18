# Revisione Task 2 (rinvii piccoli di B6), commit 8db63e2

### Aderenza
- ✅ Lookahead di `SAVED_PATH` (`spikes/b1/flowreg.py:32`): ora ammette `, } ] : \` dopo `tool-results`. Verificato con la regex su stringhe mirate: `tool-results.txt`, `tool-results-old/x`, `tool-results-` non corrispondono; `tool-results,`, `tool-results}`, `tool-results:`, `tool-results/a,b` sì. Il lookahead è solo ampliato con caratteri separatori, quindi non lascia passare nulla di prima e non tocca nomi simili.
- ✅ Test dei cinque casi di punteggiatura, dei negativi (stream invariato, `third_party_blocks == []`, 0 sostituzioni), di stdout+stderr (entrambi sostituiti, idempotente) e dei sei prefissi di lettura (`<`, `cat`, `python3 -c`, `jq`, `awk`, `cp`): corrispondono a decisione 17 e al brief.
- ✅ `test_committed_evidence_has_no_long_web_results` resta valido (non modificato; ripetuto da solo: OK). Il lookahead può solo aggiungere blocchi trovati, quindi non lo indebolisce.
- ✅ `_concrete_paths` (`bin/tollgate_flow/init.py:~256-262`): un percorso esatto (`file`) si toglie solo se coperto da `folder_paths` o da un `ext_paths` proposto, calcolato sui `found` dello stesso frammento (`patterns`). Se nessun file attiva l'estensione, `ext_paths` è vuoto e l'esatto resta. Output ordinato come prima. D10 rispettata, nessun caso reale cambia (nessuna modifica a frammenti veri).
- ✅ `_parse` (`bin/tollgate_core/fragments.py:~93`): concatenando i pezzi vecchi si ottiene lo stesso testo; la prima parte resta f-string con `{name}`. `test_parse_error_message` lo confronta con `assertEqual` esatto.
- ✅ Nessun file fuori elenco, nessun `__pycache__`, nessun programma vietato. `bash -n` non rilanciato (lo script non è nel diff).
- ⚠️ Il RED riportato (6 falliti sulla base) e la suite verde (3918 test, due interpreti) sono dichiarati dal report e non rilanciati. Plausibili: i test nuovi che "passano già" sono dichiarati tali.

### Punti di forza
- Cambio minimo e chirurgico nei tre punti, test onesti: i quattro che passano già sulla base sono dichiarati come vincoli di non regressione.
- Il test stdout+stderr controlla anche l'idempotenza e che `third_party_blocks` torni vuoto.
- `test_name_path_dropped_when_ext_covers` asserisce anche la copertura reale con `globs.match`.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
- `bin/tollgate_flow/init.py:254`: la riga del docstring è di 103 caratteri (le altre del file restano entro 100). Spezzarla.
- `tests/test_b1_scripts.py` (`..._folder_followed_by_punctuation`): i casi controllano solo che il blocco sia trovato e tolto; non verificano il nome nel segnaposto. Non necessario, nota di completezza. Il quirk già noto del nome `a` per `a=/x/tool-results` resta (estetico, già in decisione 17).
- Effetto collaterale accettato: `tool-results:` come testo in un comando (per esempio `grep "tool-results: x"`) ora conta come cartella e fa togliere l'uscita. Fallisce dal lato sicuro (toglie di più, mai di meno).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** i tre rinvii sono realizzati come da brief e D10; lookahead e `_concrete_paths` verificati con controlli mirati, messaggio di `_parse` identico. Resta solo un minore di lunghezza riga.
