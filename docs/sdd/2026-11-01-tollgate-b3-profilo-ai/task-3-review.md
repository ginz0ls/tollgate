# Revisione Task 3 (bfc6b6f)

### Aderenza
- ✅ `git.tree_sizes_at` (git.py:333-346): `ls-tree -r -l -z`, `_check_ref`, assente -> `{}`, nomi con spazi/accenti, sottomoduli saltati (test_git).
- ✅ `EXCLUDED_PREFIXES` unica costante (init.py:36-37), usata da `profile_blocks` sia per i file sia per `detected`; pronta per il Task 4.
- ✅ D4: `globs.escape(prefisso) + "/**"` (init.py `_concrete_paths`), prefissi annidati ridotti, `[id]` escapato, test con `globs.match`; cartella alla radice testata con `match`, non come stringa.
- ✅ D2: `GitError` -> `_not_evaluated` (righe + README, code 0, anche con `--update`); `FragmentError` -> `_refuse` col nome del file. Test per entrambi.
- ✅ D8: README per profilo da `_plain` riga per riga poi `prbody.neutralize(max_len=4000)`; test sul carattere ESC.
- ✅ D14: i toml di prova (`BASE_TOML`) hanno `schema_version = 1` e `[gate] mode = "protected"`; agenti nella forma `tollgate:implementer-x`/`reviewer-x`; `cfg.warnings == []` asserito.
- ✅ D16: nessuna riga dei profili contiene «protezione»; la skill `init` ha il testo nuovo fuori dalla sezione «Codici d'uscita», senza `- **<n>`, senza `P<cifra>` né `tollgate <sottocomando>` nudo.
- ✅ D17: `_drift` segnala un file solo se `match_any` è falso e nessun `!p` lo riguarda; test sui due ordini; il caso rilevato (`detected`) usa la stessa condizione.
- ✅ D20: `profile_blocks` legge solo `plugin_root`; test con `git._proc` che solleva.
- ✅ Decisione 7: testo dell'utente non riscritto (`toml + found.text`, con `with_mode` come prima); blocco una volta sola (`test_update_twice_no_duplicate`); righe anche nel ramo «nulla da aggiornare» (`return InitResult(OK, [*lines, *found.lines])`, test dedicato); avviso `active`; sovrapposizioni con chi vince; al più 10 file con il totale.
- ✅ Decisione 12: agente mancante tolto con riga (profili nuovi); per i dichiarati solo «ora esiste»; `agent = ""` è una scelta.
- ✅ Decisione 4: solo `fragments.approved`; un dichiarato non approvato resta muto (test).
- ✅ Scostamento 1 (`tree_sizes_at` solo blob): coerente con «sottomoduli si saltano»; un link simbolico è un blob e resta. Accettato.
- ✅ Scostamento 2 (righe «togli» per `R-<AREA>-…` non più nella skill): giustificato dalla decisione 3 (una regola ignota in `blocking_rules` blocca sempre) ed è limitato al prefisso dell'area, quindi non tocca regole dell'utente. Accettato, ma non ha alcun test (rilievo M1).
- ⚠️ Scostamento 3 (blocchi scartati con «profili non valutati» se `current + blocchi` non passa `load_config_text`, init.py ~600-606): coerente con D2 (il resto della proposta si scrive, l'avviso è visibile, niente testo non valido nel `tollgate.toml`). Non testato (M2). Non verificabile dal diff se in pratica si possa raggiungere dato che `fragments.load` valida i frammenti.
- ⚠️ `test_real_trees_light_no_profile`: oggi `templates/profiles/` non esiste, quindi il test passa banalmente; avrà senso dal Task 7. L'albero di FlowLab è approssimato con quattro file finti, non quello vero (il brief chiedeva «entrambi»): non verificabile dal diff.

### Punti di forza
- `profile_blocks` pura sui dati, ben separata da `propose`; la catena frammento -> testo -> `tomlout` evita sostituzioni di stringhe.
- Test mirati ai rischi del focus (utente, due giri di `--update`, negazioni nei due ordini, README una riga per nota, git rotto).
- Il bug dell'a capo in `_plain` è stato preso e coperto da test; `_fenced` riga per riga è la forma giusta.
- Nessuna modifica a `globs`, `_OPS` o `EVENT_TYPES`; layer rispettati.

### Rilievi
Nessun Critical, nessun Important.

**Minor**
- M1 `bin/tollgate_flow/init.py` (`_drift`, ramo «togli»): comportamento aggiunto senza test. Aggiungere `test_declared_profile_stale_rule_removal_reported` (regola `R-X-09` in `rules` non nella skill -> riga «togli»; una regola dell'utente senza il prefisso `R-X-` non compare).
- M2 `init.py` (ramo `config.ConfigError` dopo `profile_blocks` in `propose`): nessun test (con `profile_blocks` mockato che restituisce testo non valido: `code == 0`, nessun blocco nel toml, riga «profili non valutati»).
- M3 `tests/test_init.py` `test_default_root_is_the_plugin`: usa la radice vera del plugin ma non ha il prefisso `test_real_` richiesto da global-constraints; asserisce solo `code == OK`, quindi non prova che il predefinito sia usato davvero (basterebbe un mock su `fragments.load` che registri la radice). Rinominare in `test_real_default_root_is_the_plugin` o rafforzarlo.
- M4 `init.py`: se `tree_sizes_at` torna `{}` per un errore git (non solleva), un profilo approvato dice «nessun file ... non proposto», fuorviante; trascurabile finché il riferimento è già stato risolto prima.
- M5 `skills/init/SKILL.md`: la frase «... vanno sempre mostrate all'utente e le righe `profilo …` ...» ha una costruzione zoppa; riscrivere in due frasi.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti, D2/D4/D8/D14/D16/D17/D20 e le decisioni 4, 5, 7, 12 sono rispettati e provati da test mirati; gli scostamenti sono ragionevoli. Restano solo rifiniture sui test mancanti dei due rami aggiunti dall'implementatore.
