# Revisione Task 1 (forma `ext`), diff f3ca4a2..c437557

### Aderenza
- ✅ `fragments.py`: `_EXT = **/*.([A-Za-z0-9]+)`, provata per ultima in `parse_pattern` (dopo `name`); `Pattern.kind` e messaggio di `_parse` con la quarta forma (D6). `_NAME` non può catturare `**/*.x` (il primo carattere `*` non è ammesso), quindi nessuna ambiguità.
- ✅ `init._match`: `ext` solo dopo cartelle e `name`, non per i documenti, confronto esatto sul suffisso; `concrete_for` senza `globs.escape`; `_concrete_paths` tiene i valori `ext` in un insieme (un valore per estensione). `exclude` e `EXCLUDED_PREFIXES` si applicano prima, quindi valgono anche per `ext`.
- ✅ Vincoli: `profiles.py`, `globs`, `task_routing`, `profile_blocks` (I-1) non toccati; le uniche sedi che leggono `.kind` dei pattern sono `fragments.py` e `init.py:225-236` (grep). Strati invariati. Nessun test nuovo legge file veri, nessun `mkdtemp` nuovo (usano `self.plugin`, `self.put` esistenti).
- ✅ D6: `**/*.sql` esce da `test_load_rejects_other_pattern_forms`; `**/*.sql`, `**/*.json`, `**/*.Dockerfile` escono da `test_parse_pattern_rejects` ed entrano in `test_ext_pattern_parsed` (con `tsx`, `CSS`).
- ✅ Test previsti tutti presenti: fragments (2), init (7 inclusa la guardia `test_existing_forms_unchanged`), profiles (4 guardie, in classe a parte).
- ✅ Doc: una frase in `docs/uso/comandi.md:124`.
- ⚠️ Esito della suite (3773 test, due interpreti) e RED/GREEN sono affermazioni del report; `suite-task-1.log` non riletto qui (sola lettura, nessuna suite).
- Scostamento dichiarato in `test_exclude_multi_segment_prefix` (tests/test_init.py): accettabile. Con `**/*.tsx` a runtime `apps/api/x.tsx` resta coperto (decisione 2), quindi non si può asserire l'assenza dall'elenco dei file accesi. Il test copre comunque la parte che conta: `apps/api/x.tsx` da solo non propone nulla.

### Punti di forza
- Modifica chirurgica, ordine di precedenza chiaro e documentato nel docstring di `_match`; le guardie di `profiles` fissano la decisione 4 a runtime senza toccare `vertical_for`.
- Test di rifiuto con verifica del messaggio (`**/*.<estensione>`) e del nome file; casi limite buoni (`Foo.TSX` case-sensitive, documenti, `.github/tollgate/`, `exclude`).

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `docs/uso/comandi.md:124`: la frase prima dice ancora «possono avere tre forme» e la frase sull'estensione segue subito dopo. Correggere in «quattro forme» (cartella, cartella alla radice, nome di file, estensione) o riformulare, per non lasciare una contraddizione nello stesso paragrafo.
2. `bin/tollgate_core/fragments.py` (messaggio di `_parse`): f-string spezzata in due righe per niente (`f"**/<nome-file> o " f"**/*.<estensione>"`); unire in una.
3. `bin/tollgate_flow/init.py` (`_concrete_paths`): un file acceso da `name` resta come percorso esatto anche se un `**/*.<ext>` già lo copre (es. `**/vercel.json` + `**/*.json` danno sia `**/*.json` sia `web/vercel.json`). Innocuo ma ridondante; se si vuole coerenza con la regola «esatto già coperto si toglie», filtrare `exact` anche contro i valori `ext`. Non richiesto dal brief, quindi solo da valutare.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e voci di carry (D6) rispettati, vincoli di strato e di ambito intatti, test pertinenti; restano solo tre minori di rifinitura (il primo, nella documentazione, conviene sistemarlo).
