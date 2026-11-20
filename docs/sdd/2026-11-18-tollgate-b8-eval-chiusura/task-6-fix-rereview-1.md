# Ri-revisione Task 6, giro di correzione 1 (commit c1108aa)

### Verdetti sui rilievi
1. **`anonymize` lasciava il nome utente nella forma `-home-<utente>-` dei percorsi di progetto**: INDIRIZZATO. `evals/scrub.py:177-185` aggiunge la regex `-home-<utente>-` -> `-home-USER-` dentro `clean`, la stessa funzione usata per i file di testo e per le colonne di testo dei `.db` (`_scrub_db(path, clean)`). Il test `test_anonymize_project_folder_names_with_dashes` (tests/test_eval_run.py) copre jsonl (riga JSON e riga libera con `/tmp/claude-1000/-home-…`), un .txt senza trattino finale (resta intatto), una colonna `.db` e verifica che i byte dell'utente non restino nel file `.db`. Eseguito: OK. Nessuna stampa del valore.
2. **`research_counts.count` si rompeva con una cartella relativa**: INDIRIZZATO. `evals/research_counts.py:50` usa `Path(run_dir).resolve()` prima di `as_uri`. Il test `test_research_counts_accepts_a_relative_folder` chiama `count` e `table` con percorso relativo dopo `chdir`. Eseguito: OK.

Controlli richiesti:
- Sottostringhe: la regex richiede il trattino finale, quindi `-home-<utente>x` non cambia (verificato dal test). Resta teorico il caso `…-home-<utente>-altro` dove `<utente>` è prefisso di un altro nome: stessa classe di rischio già accettata per `/home/<utente>\b` (che trova anche `/home/<utente>-x`); falso positivo solo in direzione prudente (si anonimizza di più).
- Controllo «valore corto o riservato»: `_check_values` (scrub.py:171-174, chiamato a scrub.py:223) è ancora la prima istruzione di `anonymize`, prima di `_patterns` e di qualsiasi lettura/scrittura. Invariato dal diff.

### Danni nuovi nel diff della correzione
Nessuno. Minor facoltativo: la docstring di `anonymize` (scrub.py:219) cita solo `/home/<user>` e `host`, non la forma con i trattini.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
