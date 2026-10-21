- D11: `git.ls_files_at` usa `git ls-tree -r -z --name-only <ref> -- <prefix>` e divide su `\0`; `[]` se il riferimento non c'è.
- D15: nuova `git.blob_at(repo, ref: str, path: str) -> str | None` (SHA del blob di `path` nell'albero di `ref`, `None` se assente), con test in `test_git.py`.
- D16: firma `audits.last_closed(conn, work, kinds: tuple[str, ...]) -> sqlite3.Row | None` (al posto di `kind=None`): ultimo giro chiuso tra i tipi dati, **mai** una riga `superseded`; test dedicato (`superseded` più recente di un giro chiuso → restituito il chiuso).
- D17: `audits.suspended(...)` restituisce `{tipo: numero}` anche con numero 0; il docstring dice che si legge con `in`.
- D19: un solo costruttore `audits.cap_reason(kind: str, number: int) -> str` per i motivi dei blocchi dei tetti: `CAP_REASONS[kind]` più « (giro <n>)» per i tipi avversariali (es. «giri avversariali della spec esauriti (giro 4)»), il testo fisso per `spec-lens` («audit a lenti: tetto di cicli raggiunto»); `cap_kind` lo inverte. Test.
- D7: in `violations` `locked_docs` si calcola una volta per chiamata di `diff_violations` (parametro passato a `scope_exempt` o calcolo esterno al ciclo), non per file; `scope_exempt` esenta i file sotto `docs/superpowers/reviews/<issue del lavoro>/` (decisione 26).
- D10/D18e: in `tests/test_phases.py` le tabelle si chiamano `EXPECTED` e `CAUSES` (non «ALLOWED»): `EXPECTED["L2"]` prende `approve_spec`, `audit_clean`, `approve_plan`; `CAUSES` si estende. `tests/test_db.py:198-199` (`test_latest_version_is_4`) e la stringa `"4"` a riga ~219 passano a `db.latest_version()`/5.

