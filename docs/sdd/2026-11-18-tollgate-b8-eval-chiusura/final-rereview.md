# Ri-revisione del giro di correzioni della revisione finale di B8

Diff: `review-6cbd3e2..7dfee80.diff` (commit `0705d6a`, `7dfee80`). Sonde: `sonda-rerev/p.py` (nuovo codice) e `pold.py` (stesso script sul codice di `6cbd3e2`, estratto con `git archive` in `/tmp/tollgate-rerev-old`), `s.py`, `q.py`. Nessuna suite lanciata.

## Verdetti sui rilievi
1. **F1, parola con spazi = testo di shell** — INDIRIZZATO. `bin/tollgate_analysis/bash.py:1215-1219`. Con `bash.parse(f, "/r/wt")` + `effect_reason(EffectsCfg())` le otto forme del brief ora chiedono (vercel, curl con metodo, prisma migrate deploy, supabase db push, vercel con assegnazione, vercel dopo `./scripts/build`); su `6cbd3e2` passavano tutte. `cross-env-shell "jest && echo ok"` e `cross-env NODE_ENV=test jest src/aws` passano. `true_inner_commands` di `cross-env-shell "./deploy.sh && echo ok"` contiene `./deploy.sh` (`tests/test_bash.py`, `test_check_effects.py:164`). Danno nuovo: vedi sotto.
2. **#1 e #2, `_SUPABASE_HELP` morta e costante** — INDIRIZZATO. `bash.py:1093` (`_SUPABASE_HELP_FLAGS`), usata a `bash.py:1505`; nessun altro uso di `_SUPABASE_HELP`.
3. **#4, test `take_pending(number=N)` con prenotazione più recente altrove** — INDIRIZZATO. `tests/test_tasks.py:178-183`.
4. **#10, esenzione della nota solo con `research submit` contigue dopo `tollgate`** — INDIRIZZATO. `evals/scrub.py:117-132`. La consegna vera resta esente: `/x/bin/tollgate research submit 2 <<…`, `"$CLAUDE_PLUGIN_ROOT/bin/tollgate" research submit …`, `${CLAUDE_PLUGIN_ROOT}/bin/tollgate …`, `python3 /x/bin/tollgate …` e con assegnazione davanti sono esenti (sonda `s.py`); il modo che i corsi veri usano nei repo (`/tmp/tollgate-eval-target/bin/tollgate research submit`, 70 occorrenze) è esente. `curl -s https://vercel.com/docs research submit`, `… research show 1 submit …`, `python3 /x/altro.py research submit …` non sono più esenti. Test: `tests/test_eval_run.py:1138`.
5. **#15, punteggio 0,4 in `test_s12_doing_nothing_scores_two_fifths`** — INDIRIZZATO. `tests/test_eval_cases.py:1863`.
6. **#20, `ObservedWebFetchTest` sopra `__main__`** — INDIRIZZATO. `tests/test_lookups.py:166-194`.
7. **F3, il grader di s10 conta la chiamata** — INDIRIZZATO. Spec 14 riga 1658 e rapporto (apertura di s10): frase coerente con il grader `tool_used` `WebFetch`.
8. **F4, braccio senza plugin con righe a zero** — INDIRIZZATO. Spec 14 riga 1666, rapporto («I conteggi della nota»), docstring `evals/research_counts.py:9-10`; colonna «braccio» nel blocco «Dopo B» (piano principale, punto 5).
9. **F5 e #22, `eval-e-ci.md` e docstring di `scrub.py`** — INDIRIZZATO. `docs/uso/eval-e-ci.md:24` (s1, s2, s3, s6, s9, s10, s11, s12) e `:89` (nome utente, forma con i trattini, parola intera, host); docstring `evals/scrub.py:8-10`.
10. **F2, gestori di segreti** — INDIRIZZATO. `docs/uso/limiti.md:23-24`; verificato con sonda `q.py`: `doppler secrets set`, `infisical secrets set`, `op item create` danno `None` (passano) e i tre programmi sono in `_LOADER_WITH_RUN` (`bash.py:1104`). Voce nel blocco «Dopo B».
11. **#24, 8.1 nelle sezioni toccate** — INDIRIZZATO. Intestazione, riga 35 della sezione 20, piano principale (due punti: sezioni 5 e 17).
12. **#25, «sonda (g) ed e3»** — INDIRIZZATO. Spec 1.2 e 16 (g), con la frase che dice che il secondo fatto si è visto in `e3`.
13. **#26, 48 corse** — INDIRIZZATO. Spec 16, progetto di B sez. 15, rapporto e piano (sez. 5, 6, 17): «nelle 23 corse con un implementatore che modifica (8 casi su 16)». Le cifre tornano con il rapporto (s10 3, s11 3, s12 3, s1 3, s3 3, s6 3, e4 3, e5 2; 25 = 48 - 23). Resta leggermente stretta la dicitura «23 corse (8 casi)»: 8 casi per 3 sono 24 e il rapporto spiega «dove una corsa non ha modificato» solo in un punto; non è un errore di fatto.
14. **#27, `ai-fonti.md:20` tra le pagine che invecchiano** — INDIRIZZATO. Piano principale, blocco «Dopo B», file non toccato.
15. **#28, spec 8.5 nomina `infisical sm run` e `secrets-manager run`** — INDIRIZZATO. Spec riga 989; sonda `q.py`: entrambe le forme chiedono per `vercel --prod` e lo scorrimento parte dopo `run`.
16. **Blocco «Dopo B», minori della revisione finale** — INDIRIZZATO. Piano principale, punto 5: #3, #7, #11, F2, F4 con il motivo in una frase.

File approvati: `git diff --name-only` non contiene `skills/rules-*/SKILL.md`, `templates/profiles/*.toml`, `docs/profili/**`, `agents/*.md`. «B chiusa» non compare nelle righe aggiunte.

## Danni nuovi nel diff della correzione
- **Minor** — `bin/tollgate_analysis/bash.py:1215-1219`. Un argomento con spazi di un comando innocuo, che contiene un `/` o somiglia a un comando, ora produce un candidato e può chiedere senza motivo. Provato con `bash.parse` + `effect_reason` (prima / dopo):
  - `cross-env NODE_ENV=test jest -t "src/aws parse"`: passava, ora chiede (`effetto esterno: aws`);
  - `cross-env NODE_ENV=test jest -t "tests/vercel deploy"`: passava, ora chiede (`vercel`).
  Passano ancora `-t "src/vercel deploy works"` dietro `dotenv --`, `--config "my cfg/vercel.json"`, `--testNamePattern "a=b c"`, `-t "FOO=1 bar baz"`, `-t "does the deploy thing"`. La classe «argomento con spazi che inizia con un nome di programma» chiedeva già prima (`-t "wrangler deploy"`, `--grep "supabase db push handles"`, `--grep "vercel --prod flow"`); la correzione la allarga ai testi che hanno un percorso davanti al primo token. È un falso positivo (si chiede, non si lascia passare), accettato dal brief con «testo di shell» e dal ruling della revisione; segnalato perché è il caso che il controller chiedeva di cercare. Nessuna forma che prima chiedeva ora passa (la modifica solo allarga i candidati). Nessun danno in `true=True`: `cross-env NODE_ENV=test jest -t "src/aws parse"` produce `jest` e si ferma.
- Nessun altro (documenti, scrub, test).

## Osservazioni fuori ambito
- `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md:233` dice ancora «I casi con la nota di ricerca sono cinque: s1, s2, s3, s6 e s9» nella stessa riga dove ora c'è la correzione del #26; con F5 gli indicatori sono otto (s10, s11, s12 inclusi). Frase della revisione precedente, non toccata dal giro; da allineare quando si riprende il documento.
- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` rev 35, riga 35 della sezione 20: «D2 (l'indicatore sta in s1, s2, s3, s6 e s9)» è storia del ruling, coerente con il fatto che s10-s12 sono stati aggiunti dopo.

## Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Un danno nuovo Minor (falso positivo su `jest -t "src/aws parse"` e simili), da accettare o stringere con una riga nel blocco «Dopo B».
