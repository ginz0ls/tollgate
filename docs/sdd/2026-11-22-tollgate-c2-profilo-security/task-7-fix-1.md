# Task 7, ritocchi dopo la revisione (decisioni del controller)

La revisione (`task-7-review.md`) ha approvato il Task 7 con 6 minori. Tre si chiudono ora, prima della prova reale, perché sono testo che la prova eseguirà. Leggi i rilievi 1, 3 e 5 per intero in `task-7-review.md`.

- **m1** `agents/final-security.md` (la frase «Un rischio che nessuna regola copre si segnala lo stesso…»): diventa «Un rischio che nessuna regola di `rules-security` copre, nemmeno una di quelle che spettano al revisore del task, si segnala lo stesso, con il passo del piano che tocca e la gravità del suo effetto» (così una regola sul report che non blocca non diventa un rilievo bloccante in revisione finale). `test_final_security_reviews_by_risk` (`tests/test_manifest.py`) fissa la frase (le parole «nemmeno una di quelle»).
- **m3** `agents/reviewer-security.md`: «Se nello stesso task è attiva un'altra area» → «nello stesso lavoro», come la skill.
- **m5** `tests/test_manifest.py` (`test_real_security_agent_names_forbidden_tools`): ogni nome di programma si cerca tra accenti gravi (`` `bun` ``), non come sottostringa; mostra che togliere `` `bun` `` dall'agente ora dà rosso (su una copia temporanea).

Vincoli: nessun altro testo degli agenti cambia; i paragrafi derivati dai generici restano identici (`test_area_agents_derive_from_generic`). Test mirati: `python3 -B -m unittest tests.test_manifest`. `claude plugin validate --strict .` (uscita 0).

Commit a parte, prima di quello del Task 8, con l'oggetto «tollgate C2: agenti di security, ritocchi dopo la revisione»: solo `agents/final-security.md`, `agents/reviewer-security.md`, `tests/test_manifest.py`. La suite completa è una sola, quella del Task 8, lanciata con tutte e due le modifiche nel worktree; dopo `exit 0` fai i due commit in quest'ordine (prima i ritocchi del Task 7, poi il Task 8). In fondo a `task-7-report.md` aggiungi un «Fix round 1» con cosa hai cambiato, i test, il comando e l'output.
