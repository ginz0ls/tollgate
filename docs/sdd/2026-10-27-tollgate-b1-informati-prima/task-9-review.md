# Revisione Task 9, Step 1 (db7cd80)

Letti: reviewer-rules, cautele, brief, carry (Task 9), report, `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `spikes/b1/flow/*`, `tests/test_b1_scripts.py` (classe `FlowScriptTest`), modelli `run-p4-flow.sh` e `run-b1-checks.sh`. Non ho lanciato script né suite. Controlli mirati: `bin/tollgate_core/db.py:186` (schema `lookups`), `cli.py:84,481` (formato di `events`), `paths.py:29,45` (nome del DB, sentinella), `.claude-plugin/plugin.json:7` (`experimental.evals`), `hooks/run:123,204` (nomi dei log), `tests/fakegh.py` (import solo stdlib, niente `__pycache__` nel repo).

## Aderenza
- ✅ Rifiuto fuori da `/tmp/tollgate-b1/` (`run-b1-flow.sh:69-73`, chiamato prima di ogni scrittura in `prepara`, `claude_step`, `passo2`, `registra`; `..` e prefissi simili rifiutati; test `:534`). Rifiuto senza `--plugin-dir` (`:86`, prima di validate e di `claude`).
- ✅ Nessun `rm`. Gli unici spostamenti sono `mv` in `rot` (`:61-66`), dentro `$TMP` e `$OUT`. Nessuna variabile non quotata in operazioni distruttive.
- ✅ Scritture solo in `$TMP` e `docs/verifiche/evidenze/b1/flusso/` (`validate/`, `passo*/`, `registro-N/`, `exit-codes.txt`). Il `gh` finto è uno shim `sh` che fa `exec python3 .../fakegh.py` (stdlib, nessun `__pycache__` nel repo). Nessuna scrittura in `~/.claude` o `~/.local/state/tollgate`.
- ✅ `TOLLGATE_STATE="$STATE"` con sentinella creata da `prepara`, `verifica_stato` (`:75-78`) prima di ogni passo; `registra` esporta lo stesso stato.
- ✅ `PATH="$GHBIN:$PATH"` per `claude`; `TOLLGATE_GH` e `TOLLGATE_FAKEGH_*` impostati (`:246-247`).
- ✅ Ogni passo ha `--model sonnet`, `--permission-mode acceptEdits`, `--allowedTools` esatto della ruling (senza MCP), `timeout`, `--disallowedTools` (gh per percorso, `command gh`, `gh repo|api|auth|secret`, `git push` https/http/ssh/git@/force/-f/mirror/delete, curl e wget anche per percorso). `claude -p` costruito in un solo punto (`:84`).
- ✅ Evidenze mai cancellate (solo `mv`; tentativi in cartelle nuove; `exit-codes.txt` in append).
- ✅ Prompt di `passo2`: `Write` del piano con il testo tra marcatori, poi commit, poi `/tollgate:execute`, "Non lanciare /tollgate:finish" (`:96-103`, test `:632`). L'heredoc non rivaluta backtick o `$` del piano (espansione di `$(cat ...)` non ricorsiva).
- ✅ Issue #1: `spikes/b1/flow/issue-1.md` coincide con il testo del brief; `prepara` lo scrive nei dati del `gh` finto (`:181-191`).
- ✅ `approved: prova-b1` solo nella copia (`:144-153`, test `:544`); `plugin validate --strict` sulla copia prima del primo `claude -p`, con arresto (`:213-226`, `:239`); Grep fuori dal matcher e `registra` lo dichiara (`flowreg.py:84-86`).
- ✅ Test su radici finte; nessuna scrittura nelle evidenze del repo (cleanup `:503-508`). Nessun `__pycache__` nel commit né nell'albero.
- ❌ `registra` non raccoglie correttamente il conto dei Grep con più tentativi (I2).
- ❌ Il tetto di 3 tentativi non è un tetto della prova (I1).
- ⚠️ Non verificabile senza `claude` vero: l'esito di `plugin validate --strict` sulla copia (vedi I3 e il campo `approved`); il campo `parent_tool_use_id` nel flusso.

## Punti di forza
- Struttura fedele ai modelli, rifiuti prima di qualsiasi effetto, guardie ripetute dove contano (radice, stato, `gh` in testa).
- `flowreg.py` è solo lettura (`mode=ro`) e solo stdlib; test dedicato.
- Test di validate fallita: dimostra che non parte `claude -p` e non si consuma un tentativo.
- Il piano di prova passa `plan-check` già in `prepara`.

## Rilievi

### Critical
Nessuno.

### Important

**I1. `run-b1-flow.sh:139` e `:237-238`: `prepara` azzera il tetto di 3 tentativi.**
`rot ... "$OUT/passo1" "$OUT/passo2"` sposta le evidenze in `passo1.prev-<tempo>`; il conteggio `while [ -e "$OUT/$id/tentativo-$n" ]` riparte da 1. Scenario: 3 tentativi di `passo2` falliti, `prepara`, altri 3, e così via, senza limite di consumo né di sessioni `claude`. Il tetto è un vincolo di sicurezza di tutta la prova. Il test `tests/test_b1_scripts.py:675-678` consacra il comportamento.
Correzione: contare i tentativi di `<passo>` su `$OUT/<passo>/tentativo-*` e su `$OUT/<passo>.prev-*/tentativo-*` (funzione unica), rifiutare se la somma è >= `MAX_ATTEMPTS`; numerare il nuovo tentativo come somma+1 così i nomi non si ripetono tra cartelle. Aggiornare il test: dopo `prepara` il quarto tentativo è comunque rifiutato (anche con 2+1 tentativi tra due cartelle). Per coerenza, `registra` (`:289`) legge solo le cartelle correnti: va bene dopo un `prepara` (stato nuovo), ma va dichiarato.

**I2. `run-b1-flow.sh:289-293` + `flowreg.py:77-81`: il conto dei Grep è sbagliato con più tentativi o più passi.**
Il ciclo invoca `flowreg.py comandi` una volta per file e appende un blocco "# strumenti del modello" per ciascuno; `_count` restituisce la prima riga `Grep: ` trovata, cioè quella del primo blocco che ne ha una. Scenario: passo1 con 2 Grep, passo2 con 7: `grep-non-registrati.txt` dice 2 invece di 9; con zero Grep in passo1, il valore è quello di passo2 solo per caso. È il dato che il rapporto deve riportare per B1-V6. Il test `:688` usa un solo tentativo e non lo vede.
Correzione: una sola chiamata `flowreg.py comandi "${files[@]}"` (la funzione somma già su più file e stampa un solo blocco), oppure `_count` che somma tutte le righe. Aggiungere un test con due file di flusso (passo1 e passo2).

**I3. `run-b1-flow.sh:142`: la copia per sottoinsieme esclude `evals` e `LICENSES`.**
`.claude-plugin/plugin.json:7` dichiara `"experimental": {"evals": "evals"}`: nella copia il percorso non esiste, quindi `plugin validate --strict` (o il caricamento) può fallire o divergere dal plugin vero; `agents/*.md` e `skills/execute/SKILL.md` citano `LICENSES/superpowers-MIT.txt`. I modelli (`run-p4-flow.sh:68`) usano il plugin intero. Un elenco bianco si rompe in silenzio a ogni nuova cartella di primo livello. Il fallimento sarebbe sicuro (si ferma senza consumare tentativi), ma blocca il controller per un difetto dello script. ⚠️ non verificabile senza `claude`.
Correzione: copiare tutto tranne `.git`, `.github`, `.superpowers`, `docs`, `spikes`, `tests`, `__pycache__` (elenco nero), oppure almeno aggiungere `evals` e `LICENSES`; test che ogni percorso citato da `plugin.json` esista nella copia.

### Minor
- **M1. `tests/test_b1_scripts.py:23,627`**: il `claude` finto registra solo cwd, argomenti e `TOLLGATE_STATE`: nessun test asserisce che il `PATH` del processo `claude` inizi con `ghbin` né `TOLLGATE_GH`/`TOLLGATE_FAKEGH_DATA`. Il controllo a `run-b1-flow.sh:236` verifica solo l'ipotetico `PATH`, non quello passato. Far registrare `PATH` al finto e asserire.
- **M2. `run-b1-flow.sh:248`**: `timeout` senza `-k`; un `claude` che ignora SIGTERM supera il tetto. Aggiungere `-k 30`.
- **M3. `run-b1-flow.sh:284-305`**: `registra` esce 0 anche se `events`, `stats` o `status` falliscono (gli errori finiscono solo nei `.err`). Stampare un elenco dei `.err` non vuoti. Gli eventi `research_note`/`research_reminder`/`veto` non sono separati per passo come dice il brief («del passo»): `eventi-ricerca.jsonl` ha tutto; basta il campo `seq`/`at`, ma va dichiarato nel rapporto.
- **M4. `run-b1-flow.sh:294`**: `gh ` nella regex sovra-corrisponde ("through ") e perde `gh` a fine riga; accettabile come segnale conservativo.
- **M5. Divieti a prefisso (`:53-56`)**: non coprono `git -C x push https://...`, `git push --force-with-lease`, `git remote set-url origin <https>` seguito da `git push origin`, né `env gh`. In più `Write`/`Edit` nudi in `--allowedTools` valgono per qualsiasi percorso, quindi `acceptEdits` non limita il modello alla cartella di lavoro. Il modello di minaccia è lo stesso di p4 (modello cooperativo) e `comandi-rischiosi.txt` rileva a posteriori; basta dichiararlo nel rapporto.
- **M6. `flowreg.py:28`**: `parent_tool_use_id is not None` dà 0 subagenti anche se il campo manca del tutto. Distinguere "campo assente" da "null" e stamparlo.
- **M7. `:218`**: le validazioni fallite non finiscono in `exit-codes.txt`; sono tracciate in `validate/validate-N.txt` e non c'è consumo di modello, quindi nessun tetto è necessario.

## Dubbi dell'implementatore
1. **Sottoinsieme di cartelle**: sì, manca qualcosa (`evals`, `LICENSES`): vedi I3.
2. **Validazione fallita che non consuma un tentativo**: giusto. Non lancia il modello (cautele), lascia l'evidenza in `validate/`. Nessun rilievo oltre M7.
3. **Conteggio dei subagenti con `parent_tool_use_id`**: ragionevole (il campo è dei messaggi `assistant` dello stream-json, `null` al livello principale), ma non verificato: M6 lo rende visibile se il campo non c'è.

## Valutazione
**Qualità del task:** Da correggere.
**Motivo:** sicurezza dello script solida (radice, stato, `gh` finto, divieti, nessuna cancellazione), ma il tetto di tentativi si azzera con `prepara` (I1), il conto dei Grep di `registra` è errato con più tentativi (I2) e la copia del plugin per sottoinsieme esclude `evals` citato da `plugin.json` (I3).
