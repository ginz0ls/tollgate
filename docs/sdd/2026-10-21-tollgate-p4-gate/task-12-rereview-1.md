# Ri-revisione Task 12, giro di correzione 1 (8c3b417..195d750)

Controlli: diff letto; `python3 -B -m unittest tests.test_init.{EstimateTest,HintsTest,UpdateTest,ServicesTest}` (28 test, OK); `prbody.neutralize` provato a mano con backtick, recinto di backtick, `-->`, `<!--`, `@`; grep dei nomi di servizio nei test del Task 11.

### Verdetti sui rilievi

**I-1 Regola dei nomi di servizio non chiusa (a capo finale, due regole divergenti).** INDIRIZZATO. Una sola regola in `install.validate_services` (`bin/tollgate_gate/install.py`, `fullmatch` su nome e immagine); `_services_block` la chiama; `init.propose` la chiama e non ha più `SERVICE_NAME` né `_services`. `test_one_rule_for_init_and_install` copre `"db\n"`, `"x\n"`, maiuscole, `_`, `-db` sia con `install.files` sia con `validate_services`, e `hasattr(init, "SERVICE_NAME")` falso; `test_untrusted_names` e `_through_the_api` aggiungono i casi con a capo e `d_b`.
- La regola più stretta non rompe nulla: i servizi dei test del Task 11 sono `db`, `cache`, `true`, `a b`, `d: b` (`tests/test_gate_workflows.py:417,445,450`), nessuno con maiuscole o `_` validi. I workflow generati usano nomi in `[a-z0-9-]`, quindi restano validi. Il test di Task 11 `test_invalid_service_is_rejected` resta coerente.

**I-2 Stima dei minuti con ricevute di altri repo.** INDIRIZZATO. `_gate_seconds` fa `JOIN work_items w ON w.id = r.work WHERE w.repo_key = ? AND r.state = 'green'` (`bin/tollgate_flow/init.py`). Il `repo_key(url)` con `url = git.origin_url(main)` è lo stesso modo di `start.py:388-390` e `closing.py:55`; `init` ora rifiuta con messaggio chiaro se manca l'origin. Test: `test_receipts_of_another_repo_do_not_count`, `test_receipts_without_work_do_not_count`, `test_only_green_receipts_count` (rossa più recente e `empty` non contano). Passano.

**Minore: nomi dei workflow nel README.** INDIRIZZATO. Violazioni e file «da cancellare» passano da `prbody.neutralize` (recinto di lunghezza adattiva, `@` e `<!--`/`-->` disinnescati con ZWSP); provato a mano: un recinto di 4 backtick dentro il testo viene racchiuso da 5, `## Falso` resta dentro il recinto. A terminale `_plain` sostituisce con `?` i caratteri non stampabili (a capo compreso). `test_workflow_names_are_neutralized_in_the_readme` lo verifica.

**Minore: README dice di compilare `[commands]`.** INDIRIZZATO. Con `from_template` compare sotto il passo 1; test positivo e negativo.

**Minore: `--update` senza file cambiati segnala la protezione.** INDIRIZZATO. Ritorna prima di `_write`: nessun file scritto (lo conferma `test_update_with_nothing_changed`, `folder` assente), e l'uscita aggiunge ramo senza protezione o campi mancanti più il rimando a `--propose`. Test dedicato.

**Minore: riga lunga nella docstring di `tests/fakegh.py`.** NON INDIRIZZATO. Il giro ha riflusso le righe 30-33, ma `tests/fakegh.py:34` è ancora di 144 caratteri («`state`; 404 se manca) e `issues?state=open` (da `open_issues`, ... un valore per riga; il»), cioè oltre 100 e oltre 141. Va riformattata.

### Danni nuovi nel diff della correzione

- **Minor** `bin/tollgate_flow/init.py:418` (105 caratteri), `:198` (107) e `tests/test_init.py:244` (106): righe nuove oltre il tetto di 100 che la stessa correzione chiedeva di rispettare.
- Nessun Critical né Important.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** I-1 e I-2 indirizzati, nessun danno nuovo Critical/Important. Resta aperto un solo minore: la riga di 144 caratteri in `tests/fakegh.py:34` (più tre righe nuove di 105-107 caratteri), che non blocca ma contraddice quanto dichiarato nel report.
