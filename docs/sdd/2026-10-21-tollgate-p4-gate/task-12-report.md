# Report Task 12: init, misura della modalità, protezione letta da start

Commit: 5475e54 «tollgate P4: init con la misura della modalità e la proposta dei file; protezione letta da start».

## Implementato
- `bin/tollgate_gate/protection.py`: `classify`, `REQUIRED_FIELDS`, `missing`, `protection_body` (rifiuta `-1`, 0, non interi), `body_template` (corpo con `"__APP_ID__"` che `protect.sh` sostituisce), `ProtectionRead`, `read` (mai eccezioni: errore di `gh` → `undetermined` con nota), `actions_enabled` (V9). Costanti `BASE_JOB = "tollgate-base"` e `BASE_APP_SLUG`.
- `bin/tollgate_flow/init.py`: `propose(...) -> InitResult(code, lines, folder)`, `with_mode` (cambia solo la riga `[gate] mode`), stima dei minuti, workflow esistenti fuori regola (decisione 15, `workflows.problems`), suggerimento jest-junit, `protect.sh` generato con valori sempre tra apici.
- `bin/tollgate_core/cli.py`: `init --propose|--update [--merges-per-month N (default 20)] [--service NOME=IMMAGINE[,PORTA]]...`.
- `bin/tollgate_flow/start.py`: `_check_gate_runs` in `_checks` (avvio nuovo) e in `_resume`: Actions in entrambe le modalità, protezione solo in `protected`.
- `bin/tollgate_gate/install.py`: solo `ports` (parametro facoltativo di `files`, `ports: ["P:P"]` sotto il servizio).
- `templates/tollgate.toml` (con `__MODE__`), `tests/test_protection.py`, `tests/test_init.py`, `ProtectionTest` in `tests/test_start.py`, `tests/fakegh.py`.

## Scostamenti dal brief, da sapere
1. **Forma della porta**: `NOME=IMMAGINE,PORTA` (virgola) e non `IMMAGINE:PORTA`. I due punti sono già del tag dell'immagine (`postgres:16`, `redis:7`): con `:PORTA` il tag sarebbe stato letto come porta. La spec 9.6 non dice come esporre le porte; la scelta è mia, con `ports: ["P:P"]`. `install.files(..., ports=None)` è il solo cambio a `install.py`.
2. **`propose`** ha un parametro in più, facoltativo: `ports: dict[str, int] | None = None`. La firma del brief resta valida.
3. **Estimate**: minuti a merge = 2 × ceil(durata/60) (base + gate, ipotesi: la suite di base dura come il gate, detta nel README), × merge al mese. Predefinito 20 merge al mese, scelta mia.
4. **Avvisi in più in `start`** (a basso costo, sulla stessa lettura): ramo senza protezione (404), e `tollgate.toml` `protected` con piano che non offre la protezione (403 «Upgrade…»). Con `undetermined` il testo è quello della decisione 19.
5. **`start` in ripresa** legge anche Actions e protezione (la decisione 19 dice «a ogni avvio»): due GET in più anche lì.
6. **`protect.sh`** filtra il check-run per nome esatto `tollgate-base` **e** `app.slug == "github-actions"` (V6: un check-run omonimo di un'altra app non conta), richiede `status == completed`, un solo `app.id` distinto, intero positivo; SHA primo argomento (40 hex) o `origin/<ramo>`. `protect.sh` e `protection.json` si generano solo se il ramo non è protetto o la protezione ha campi mancanti; con protezione completa il README lo dice.
7. `fakegh.py`: `PUT .../branches/<ramo>/protection` (registra il corpo in `protection_puts`) e `commits/<sha>/check-runs` (con `--jq` valuta solo il filtro di `protect.sh`: nome e slug). Detto nel docstring.
8. Un titolo del README conteneva «tollgate init» nudo e faceva fallire `test_manifest.BareProgramInMessagesTest`: riscritto; i rimandi a comandi nel testo usano le skill (`/tollgate:init`, `/tollgate:finish`).
9. `init` fa `git fetch origin` (come `start`); un fallimento è un avviso, non un rifiuto.

## TDD
RED (moduli assenti / comportamento assente):
- `python3.11 -B -m unittest tests.test_protection` → `ImportError: cannot import name 'protection' from 'tollgate_gate'` (1 error).
- `python3.11 -B -m unittest tests.test_init` → `Ran 1 test ... FAILED (errors=1)` (import di `tollgate_flow.init`).
- `python3.11 -B -m unittest tests.test_start.ProtectionTest` → `Ran 8 tests ... FAILED (failures=9)` (nessun avviso su protezione e Actions).

GREEN:
- `python3.11 -B -m unittest tests.test_protection` → 17 test OK (dopo aver corretto il mio conteggio atteso su `missing({})`: 5 voci, non 7: i campi assenti di push forzato e cancellazione non sono «abilitati»).
- `python3.11 -B -m unittest tests.test_init` → 42 test OK. Primo giro: 2 fallimenti reali, corretti: `protect.sh` lasciava `"15368"` tra virgolette (escape perso nel generatore: ora `sed 's/"__APP_ID__"/'"$APP_ID"'/'`) e un testo del README.
- `python3.11 -B -m unittest tests.test_start` → 81 test OK.
- `tests/run`, un interprete per volta in parallelo: `PYTHONS=python3.11 tests/run` → `Ran 2262 tests in 631.084s OK`; `PYTHONS=python3 tests/run` → `Ran 2262 tests in 618.291s OK`. (Il primo giro unico, con un titolo del README fuori regola, aveva dato 1 fallimento in `test_manifest`: corretto.)

## Autorevisione
- Brief: tutti i test nominati ci sono (`test_classify`, `test_missing_fields`, `test_body_never_minus_one`, `test_detect_proposal`, `test_protected_unset_proposes_command`, `test_token_without_admin_undetermined`, `test_files_tree`, `test_minutes_estimate`, `test_jest_junit_hint`, `test_update_only_changed_files`, `test_existing_workflow_violations_listed`, `test_untrusted_names`, e i quattro di `ProtectionTest`).
- `init` non fa chiamate `gh` in scrittura (test `test_no_write_call_to_github`); `protect.sh` si prova con `gh` finto nel `PATH`, mai con il vero (il test verifica che `command -v gh` sia il wrapper).
- Strati: `protection.py` importa solo `tollgate_core.ghcli`; `test_layers` verde.

## Dubbi
- La forma `,PORTA` va confermata dal controller (scostamento 1).
- `README.md` di `--update` elenca come «Da cancellare» i file sotto `.github/tollgate/` assenti dalla versione nuova; i workflow del gate non si cancellano mai da qui.
- `finish`/`verify` come sola fonte delle ricevute per la stima: se nessuna ha `duration`, «non misurata».

## Fix round 1
Commit: vedi `git log` («... (Task 12, fix round 1)»), base 8c3b417.

- **I-1**: `install.validate_services(services, ports=None)` è l'unica regola (nome `[a-z0-9][a-z0-9-]*` con `fullmatch`, immagine, porta); `_services_block` la usa e `init.propose` la chiama, senza regex né `SERVICE_NAME` propri. Il nome ora è solo minuscole, cifre e `-` anche in `install` (prima ammetteva maiuscole e `_`; i test del Task 11 non li usavano). RED: `test_one_rule_for_init_and_install` (ERROR: `validate_services` assente). I casi con a capo finale (`"db\n"`, `"x\n"`) erano già rifiutati da `fullmatch` del Task 11: i test li fissano per `init`, CLI e `install.files`.
- **I-2**: `_gate_seconds(state, key, commands)` fa JOIN con `work_items` sul `repo_key` dell'origin e usa solo `state = 'green'`; ricevute con `work` nullo o di altri repo non contano (docstring). RED: `test_receipts_of_another_repo_do_not_count`, `test_receipts_without_work_do_not_count`, `test_only_green_receipts_count`. I test della stima ora usano un lavoro reale (`issue=7`).
- **Minori**: workflow esistenti e file «da cancellare» nel README dentro un recinto (`prbody.neutralize`), a terminale con i caratteri non stampabili come `?` (RED `test_workflow_names_are_neutralized_in_the_readme`); passo «compila `[commands]`» quando `tollgate.toml` viene dal modello (RED `test_template_readme_says_to_fill_commands`, più il caso contrario); `--update` senza file cambiati segnala ramo senza protezione o campi mancanti e rimanda a `--propose` (RED `test_update_with_nothing_changed_still_reports_missing_protection`); docstring di `fakegh.py` entro 100 caratteri.
- Non fatto: `with_mode` con apici singoli e array multiriga (minore già coperto da rivalidazione, fail-closed).
- `tests/run` in parallelo, un interprete per volta: python3.11 `Ran 2287 tests in 639.527s OK`; python3 (3.13.5) `Ran 2287 tests in 632.121s OK`.
