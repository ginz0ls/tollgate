# Task 5, ri-revisione del giro di correzione 1 (00065d7..039146b)

### Verdetti sui rilievi

**I-1. `is_config_branch` ignora `cross_repo`: PR da fork su `tollgate-config/*` senza test-guard né scope.**
INDIRIZZATO. `bin/tollgate_gate/evaluate.py:121` ora richiede `not pr.cross_repo`. Gli unici due usi (`:423` test-guard/scope, `:632` famiglia `issue`) leggono la proprietà, quindi un ramo di fork vale come ramo qualunque (`not_tg_branch`, `no_issue`) e il test-guard gira. Test `test_config_branch_from_a_fork_is_a_manual_pr` (`tests/test_gate_evaluate.py`): fork, `test_deleted` rosso e voci `no_issue`/`not_tg_branch`; stesso repo, nessun rosso `diff`.

**I-2. `_findings` fail-open senza `verdict` o con `cycles` non intero.**
INDIRIZZATO. `evaluate.py:~690`: `not isinstance(last, int) or _finding_cycle(f) in (None, last)`; senza ultimo ciclo leggibile ogni bloccante conta, coerente con l'id malformato. Test `test_blocking_finding_without_usable_verdict_is_red` copre verdict assente, `cycles` stringa, verdict non dizionario, più il caso `blocking: False` che resta senza rosso.

**Ruling 1. `level_cap` emesso ogni volta che il blocco dichiara un tetto.**
INDIRIZZATO. `evaluate.py:~480-492`: con tetto valido sempre `level_cap` (testo diverso sotto/sopra il minimo); `level_below_minimum` solo senza tetto e sotto il minimo (`elif below`). Nessun doppione né contraddizione: le due voci sono mutuamente esclusive. Test `test_cap_is_reported_even_above_the_minimum` (anche `attention_state == "failure"`; secondo caso L2/L2 con percorso sensibile).

**Ruling 2. Test di `block_missing` con `definition_of_done` spento.**
INDIRIZZATO. `test_block_missing_on_tg_is_red_even_with_dod_off`: gate con `[components] definition_of_done = false`, blocco assente, rosso `block_missing`.

**Ruling 3. Test del file di tollgate spostato.**
INDIRIZZATO. `test_moved_tollgate_file_counts_by_its_old_name`: `git mv` fuori dal perimetro, risultato il vecchio nome. Nota: il test preesistente `test_deleted_and_moved_tollgate_files_count` continua a provare solo la cancellazione nonostante il nome (cosmetico).

### Danni nuovi nel diff della correzione
Nessuno. Verificato che non ci sono casi fail-closed che danno rosso dove la spec vuole verde: il fork-config diventa rosso solo se il diff viola test-guard/scope, come ogni PR manuale; il ramo `tollgate-config/*` dello stesso repo resta invariato. `level_cap` con testo fisso: solo livelli validati nel `text`, motivo in `data`.

### Osservazioni fuori ambito
- Il nome di `test_deleted_and_moved_tollgate_files_count` è fuorviante (testa solo la cancellazione); i minori differiti restano quelli del registro.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
