# Ri-revisione giro 1 Task 2 (511a449..75d9f98)

### Verdetti sui rilievi
1. **(Important) Lab/FlowLab creano il lavoro con una chiave diversa da `repo_key(git.origin_url(repo))`**: INDIRIZZATO. `tests/hookkit.py` (Lab.__init__) ora calcola `key_source = core_git.origin_url(self.main)` dopo il ramo `origin_url`, quindi la chiave è quella vista da hook e CLI (get-url espande insteadOf); `git.origin_url` non toccato. `tests/test_flowkit.py::test_work_repo_key_matches_origin_url_and_hook_finds_it` fissa `work_items.repo_key == repo_key(core_git.origin_url(main))`, verifica che `orphan_tg` (che usa `repo_key_of`, `_common.py:79-91`) sul worktree dia `None` (lavoro trovato) e che `bash` dal worktree esca 0. Test mirato rilanciato (`python3 -B -m unittest tests.test_flowkit tests.test_check_acts`): 29 OK. Report con suite 721 OK su 3.11 e 3.13.
2. **(Minor) Nessun test per l'esclusione di off/on dalla riga «programma»**: INDIRIZZATO. `tests/test_check_acts.py` `ProgramLineTest.test_off_and_on_get_no_program_line` (subTest per `tollgate:off` e `tollgate:on`, assertNotIn «programma»).

### Danni nuovi nel diff della correzione
Nessuno. Nel caso default (senza `origin_url`) `core_git.origin_url(main)` coincide con il percorso dell'origin, come prima. Unica nota estetica (Minor, non bloccante): in `test_flowkit.py` l'import `from types import SimpleNamespace` è separato dagli altri da una riga vuota.

### Osservazioni fuori ambito
- Resta aperta per il Task 3 la questione già segnalata: `prereq.is_github` deve leggere `config --get remote.origin.url` (l'URL github finto compare solo nella config, non in `get-url`).

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
