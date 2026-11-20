# Revisione Task 4 (B8): tre casi d'eval s10, s11, s12 (commit 8e80a90, diff a1906b8..8e80a90)

Solo lettura del pacchetto di diff, del brief, delle decisioni 8/7/13, del report e della documentazione dei grader. Non ho rilanciato la suite né l'a secco: mi baso sui numeri del report, controllati sul codice dei test.

## Aderenza

- ✅ Ricette `l1-ai-model`, `l1-infra-redirect`, `l1-dividi` e voci di `CORRECT_PATHS` (`evals/_kit/recipes.py`), tre piani, tre `case.yaml` e tre `scaffold.sh` come da brief.
- ✅ Grader e pesi uguali alla decisione 8: s10 2+2+1 (totale 5), s11 4+1+1 (6), s12 2+2+1 (5). `nota-consegnata` è with-only in tutti e tre, tutti gli altri `arm: both`, tag `spec`.
- ✅ Nessuna regex nuda sulla trace. Gli esiti sono grader su file (`{source: file}`), su `files`, su `last_message` o `tool_used` sull'input degli strumenti. I `tool_used` non possono combaciare con il testo del brief.
- ✅ Percorsi `{source: file}` nel worktree dello scaffold: `.claude/worktrees/tg-1-<slug>/…`, la stessa forma di s2 (`evals/s2*/case.yaml:36`). `test_new_case_file_graders_point_to_scaffold_worktree` confronta lo slug con `naming.slug` e controlla che il file esista nella cartella costruita da `scaffold.build`.
- ✅ Prompt nella forma di s1 e con l'agente di area giusto. Nessuno nomina la pagina dei modelli né la risposta. s12 dà solo il formato `ESITO: esiste in <percorso>` / `ESITO: aggiunta`, che non contiene `divisione.py`. `max_turns`/`timeout` 40/1200, 40/1200, 30/900, `allowed_tools: [Read, Glob, Grep, Agent]`.
- ✅ D15: blocchi `[profiles.ai]` e `[profiles.infra]` con `paths = ["/ai/**"]` e `["/vercel.json"]`. `test_new_case_profile_blocks_match_init` li confronta con `init.profile_blocks` sul plugin vero, su `paths`, `agent`, `reviewer`, `rules`, `blocking_rules`, e verifica che `init` proponga solo quell'area.
- ✅ D9: la prova a secco ha il passo `fetch` (Task 3) e `research_prep_docs` lo usa prima della nota. `test_s10_a_note_citing_a_page_never_opened_is_refused` copre il rifiuto senza `fetch`.
- ✅ Cammini sbagliati della decisione 8, tutti con `assertWrongPath` e punteggi confermati:
  - s10: indirizzo copiato senza `fetch` = 0,60; non fa nulla = 0.
  - s11: `netlify.toml` (con deroga) = 1/6; `vercel.json` senza rewrites = 2/6; non fa nulla = 1/6, o 2/6 con la pagina aperta; redirect giusto più `netlify.toml` = 5/6, documentato come mezzo errore.
  - s12: secondo `def dividi` = 0,60; «non esiste» senza cercare = 2/5; non fa nulla = 2/5.
- ✅ Rifiuto di `research_gate` alla prima modifica senza nota, con il testo vero di `_refusal`, nei tre casi. Gli `assertRegex` ancorano il testo intero in s10 e il prefisso negli altri due.
- ✅ Il blocco di profilo e il task con l'agente di area sono verificati da `test_the_task_goes_to_the_area_agent` sul brief generato.
- ✅ Nessun file approvato toccato (stat del diff: solo `evals/`, `tests/test_eval_cases.py`, `tests/test_eval_kit.py`). Niente nomi privati, utente o host nei file nuovi. Regole di cautela rispettate: nessun programma vietato eseguito, le stringhe sono testo.
- ⚠️ Non verificabile dal diff: se `tool_used` conta gli strumenti dei subagenti (`parent_tool_use_id`) e se `WebFetch` è concesso ai subagenti con `--allow-tools`. La decisione 8 lo demanda alla sonda del Task 6, punto (d). Tutta la misura di s10 e s11, e di `ricerca-fatta` in s12, dipende da lì.
- ⚠️ Non verificabile dal diff: il passaggio vero del blocco di profilo nello scaffold (il test sulle ricette lo prova sul `tollgate.toml` scritto, non sull'avvio reale del gate in un eval).

## Punti di forza

- Il test `test_new_case_profile_blocks_match_init` chiude il rischio del blocco di profilo diverso da quello di `init` con un confronto sul codice vero, senza copiare i valori a mano.
- I grader passivi sono tutti conosciuti e dichiarati: `nessuna-altra-piattaforma` (1/6) e `nessun-doppione` (2/5) stanno sotto soglia e lo dicono i test (`test_new_cases_score_by_decision_8`).
- `test_s11_the_pattern_wants_the_redirect_and_the_rewrite_together` prova la regex a lookahead su sei contenuti, incluso il file di partenza e `permanent: false`.
- Il veto di scope sul `netlify.toml` è mostrato a parte da un test, e il cammino sbagliato è simulato con una deroga: onesto sulla differenza tra i bracci.
- `test_s10_the_page_is_judged_on_the_input_of_the_tool_not_on_the_text` e il test sull'import di `dividi` (ammesso) coprono i due falsi positivi più probabili.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor
1. `evals/_kit/fixtures/plans/calc-dividi.md` (sezione Must-have): M2 (`test_sottrai`) non è assegnata a nessun task: il Task 1 ha solo M1. In `calc-l1.md` M2 è coperta dal Task 2. Se un controllo di copertura dei must-have legge il piano, il piano di prova è incoerente. Correzione: togliere M2, o assegnarla al Task 1.
2. `evals/s10-modello-a-memoria/case.yaml`, grader `pagina-modelli-aperta` (peso 2) più `fonte-accanto-al-nome` (peso 2): un cammino che apre la pagina e lascia la fonte accanto al nome, ma conserva `gemini-1.5-flash`, prende 4/5 = 0,80, sopra soglia. I pesi sono quelli della decisione 8, e il caso («la pagina dice che il vecchio è ancora il valore giusto») è plausibile. Va solo nominato nel rapporto finale come limite noto. Il test `test_s10_the_page_opened_but_the_old_model_left_is_below_threshold` copre solo il cammino senza la fonte.
3. `evals/s12-non-esiste/case.yaml`, `ricerca-fatta` (`tool_used Grep` senza `input_match`): conta anche un `Grep` del modello principale (che ha `Grep` tra gli `allowed_tools`) e non solo dell'implementatore. Peso 1, quindi senza effetto sulla soglia. Da tenere presente quando la sonda del Task 6 guarda `parent_tool_use_id`.
4. `tests/test_eval_cases.py`, `test_s12_doing_nothing_scores_two_fifths` non asserisce il punteggio (ha solo `assertWrongPath`, che è però sufficiente per la soglia). Il nome promette il numero esatto. In s10 e s11 il punteggio è asserito.
5. `docs/uso/eval-e-ci.md` dice ancora «tredici casi, nove spec» (già annotato nel report): lo aggiorna il Task 8, va ricordato.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** i tre casi seguono la decisione 8 punto per punto (grader, pesi, percorsi del worktree, cammini sbagliati sotto soglia), D15 è verificata con `init` vero e D9 con il passo `fetch`. Nessun grader combacia con prompt o brief, e nessun passivo supera la soglia. Restano solo cinque minori, e il dubbio sul conteggio dei `tool_used` dei subagenti va chiuso dalla sonda del Task 6.
