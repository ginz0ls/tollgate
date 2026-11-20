# Revisione Task 5 (a5def61)

### Aderenza
- ✅ Indicatore `nota-consegnata` nei cinque casi (s1, s2, s3, s6, s9): `tool_used`, `tool: Bash`, `input_match: 'research submit [0-9]+\b'`, `arm: with-only` (decisione 13; D2). Identico a s10-s12.
- ✅ Combacia con gli input dei comandi, non con il brief né con il rifiuto: nel grader della prova a secco `tool_used` confronta `_compact(tool_input)` delle chiamate `Bash` (`tests/test_eval_cases.py:605-609`). Il brief letto è una `Read` e il rifiuto di `research_gate` è un testo di risposta, quindi nessuno dei due entra in `calls`. `test_note_indicator_fails_without_note` (`:1345-1357`) lo fissa per tutti e cinque i casi: brief letto, modifica rifiutata con «research submit» nel testo, indicatore assente.
- ✅ Nessun prompt e nessun `max_turns` cambiato (il diff dei `case.yaml` aggiunge solo l'indicatore). e4 ed e5 non toccati. s4, s5, s7, s8 invariati.
- ✅ Punteggio invariato: `scored_graders` esclude l'indicatore (`test_note_indicator_is_with_only_and_not_scored`, `:1329-1335`) e `ScoreTest`/`test_correct_paths_score_above_threshold` verificano `score_of(path) == score_of(path - nota)` (`:795-796`).
- ✅ `CORRECT_PATHS` come da scan: s1 (2 voci), s3 (prime 2), s6 (1) con l'indicatore; s2 e s3 «file invariato senza tentare» no; s9 voce nuova `veto-generico, implementatore-dedicato, nota-consegnata` e le due vecchie restano (`recipes.py:69-72`).
- ✅ Insiemi attesi aggiornati secondo l'elenco del punto 8: s1 (`:913`, `:918`, `:927`), s2 (`:984`), s3 (`:1016`, `:1026`, `:1059`), s6 (`:1263`, `:1284`). Aggiornati, non indeboliti: ogni insieme ha un elemento in più, nessuno è stato tolto o trasformato in `assertIn`.
- ⚠️ Non verificabile dal diff: se `tests/run` sia verde con `python3.11` e `python3` (il report dichiara 4162 test, exit 0, `suite-task-5.log`; non rilanciato per regola).

### Punti di forza
- `NoteIndicatorTest` è guidato da una tabella per caso e prova tre cose distinte (forma del grader, passa con nota, falso senza nota con il rifiuto che cita il comando): è proprio la lente richiesta.
- Lo scostamento di s3 (deroga data prima della modifica, così il gate della nota e non il veto di scope è ciò che rifiuta) è corretto e dichiarato nel commento a `:366`.
- `test_s9_denied_then_the_task_implementer_with_the_note` copre il cammino nuovo di s9.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `evals/_kit/recipes.py:42-43`: le due voci di s3 superano le 120 colonne; le altre voci vanno a capo. Solo stile.
2. Nessun test mostra l'indicatore falso con un `Bash` il cui input nomina `research submit` senza eseguirlo (per esempio `grep`): per decisione 13 conta come tentativo, quindi è voluto, ma non è fissato da un test. Il rapporto finale (Task 8) deve dire che l'indicatore misura un tentativo, non l'esito (già nella decisione 13).
3. `NoteIndicatorTest.test_note_indicator_passes_with_note` per s9 usa `research_prep("ag-1", "src/calc.py")`: l'agente `ag-1` è quello lanciato da `S9DryRun.DEDICATED`; funziona, ma l'accoppiamento è implicito.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** l'indicatore guarda solo gli input dei comandi `Bash`, prompt, `max_turns`, e4 ed e5 e il punteggio dei casi `spec` non cambiano, e gli insiemi attesi sono stati aggiornati senza essere indeboliti. Restano solo rifiniture minori.
