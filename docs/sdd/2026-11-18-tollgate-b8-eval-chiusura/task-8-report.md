# Task 8: report

## Cosa ho cambiato

Solo documenti. Nessun file in `skills/rules-*/SKILL.md`, `templates/profiles/*.toml`, `docs/profili/**`, `agents/*.md`, `docs/verifiche/evidenze/**` o `docs/verifiche/2026-11-18-b8-eval.md`. La frase «B chiusa» non compare in nessun file.

### Spec del nucleo (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`), revisione 35
- Intestazione: rev 35 (eval reali, sonda, decisioni 1-13, ruling) davanti alla 34.
- 1.2: la voce sugli eval cambia titolo (D17): «Gli eval girano in una sandbox con la rete limitata ai domini concessi, su casi costruiti», con il testo sui domini (`WEB_DOMAINS`), `WebSearch` e il limite di `.git/worktrees/` della 2.1.328.
- 1.3: i dodici casi `spec`.
- 6.3: `take_pending` e la prenotazione (decisione 5), con il limite `launch` più `resume` e i test.
- 7.2: `WebFetch` non conta con un `code` fuori da 200-299 né con l'avviso di redirect (due punti: tabella dei hook e «Cosa conta come lettura»).
- 8.5: blocco nuovo «Rev 35» (involucri con `inner_commands` e `true_inner_commands`, lanciatori, due livelli, script non tracciati, costi D3/D10, tabella `SUPABASE_COMMAND_VALUE_OPTIONS`, `--version`, CLI 2 e `db query`); rinvii «a B8» della rev 34 aggiornati.
- 11.2: `init --update` con `min_level` e `checklist` (sostituisce il «Limite che resta» di D12 di B7) e la riga in «Un `tollgate.toml` esistente».
- 14: casi 10-12; paragrafo «Casi di B8» (s10-s12, nota di consegna in s1/s2/s3/s6/s9, campagne e tetto, permessi web, passo `fetch`, pulizia, conteggi, limite della piattaforma); e2 a secco; tetto per campagna; link al rapporto di B8 accanto a quello di P5.
- 16: blocco «Verificato in B8» (sonda (a)-(g), eval reali, conteggi, righe `modelli:`, CLI 2, pagina dei modelli di Gemini); i quattro «(B8)» della lista «Ancora da verificare» passano a «rinviato a D».
- 20: riga 35.

### Catalogo
Stato («B ha costruito `base`, `ai`, `infra`, `backend`, `frontend`, `database`; gli altri profili restano bozza»), intestazione con B8, 2.2 (18 agenti: 7 generici, 10 di area, 1 specialista; verificato con `ls agents`), sezione 6 (paragrafo B8).

### Progetto di B
Avanzamento: «B8 eseguita sul ramo, unione in attesa» con i numeri; sezione 15: bullet «Esito di B8» (s9 è uno dei cinque casi con la nota, D2).

### Piano principale
- Revisione della spec (35) e catalogo nella testa; stato in testa con il paragrafo B8.
- Sezione 2, riga B8: consegna vera e stato.
- Sezione 3: tre righe esistenti aggiornate (B1 → B8 sui permessi e `CASE_TOOLS`, letture registrate, righe `modelli:`) e una riga nuova «B8 → dopo B» con i nomi reali.
- Sezione 5: ogni punto con la prova.
- Sezione 6: due righe con il misurato.
- Sezione 9: ogni voce che nominava B8 ha «Chiuso da B8 (decisione N)», «Visto dal vivo in parte» o «Aperto dopo B8 (decisione 12)» con il motivo; la riga di PP:288 corretta (`s9` cambia, D2); blocco «Dopo B» (regola mancante di s12, limite della piattaforma, elenco unico delle pagine, voci della decisione 12, segnaposto per i minori della revisione finale).
- Sezione 17 «Prove di B8» (tabella `Punto | Task | Prova`, più «Prove oltre la tabella»).

### `docs/uso/limiti.md`, `docs/uso/eval-e-ci.md`
- `limiti.md`: titolo e testo della voce sugli eval (insieme alla spec, D17).
- `eval-e-ci.md`: link al rapporto di B8 (D12), dodici casi `spec` con s10-s12 e l'indicatore della nota, sedici casi con una corsa vera, `strip-bash` descritto come nel codice (testo grezzo, non l'elenco dei programmi: la frase di Task 3 era invecchiata), limite della piattaforma, conteggio dei test e durata della suite.

## Frasi verificate sul codice
- `ENV_LOADERS` ha `cross-env-shell`; `LOADER_PACKAGES` ha solo `dotenv-cli` e `@dotenvx/dotenvx`; `MAX_LOADER_DEPTH = 2` (`bash.py`).
- Forme provate con `bash.parse` + `effect_reason` (solo testo): `dotenv -e vercel -- echo x` e `cross-env NODE_ENV=test jest aws` chiedono; `dotenv -- git push --force origin x`, `dotenv -- rm -rf /tmp/x`, `cross-env A=1 scripts/deploy`, `cross-env A=1 ./vercel --prod` passano; `dotenv -- doppler run -- dotenv -- vercel --prod` chiede («annidato»); `dotenv -- "supabase db push"`, `cross-env-shell "prisma migrate deploy"`, `doppler run --command '…'` chiedono; `supabase db dump -f --linked` e `db push -p x --local` passano; `db push -p --local` e `db reset --linked --version …` chiedono; `npm exec prisma -- -- migrate deploy` chiede.
- La tabella `SUPABASE_COMMAND_VALUE_OPTIONS` è più larga della decisione 2 (ruling D11): l'ho descritta com'è, con esempi presi dal codice.
- `take_pending`: ordine `(reserved_at IS NULL), reserved_at DESC, number`; il secondo `take_pending(resume=True)` senza numero resta in `apply._subagent_start`.
- `init._drift`: la riga ha la forma «profilo <area>: [profiles.<area>] <chiave>: aggiungi <chiave> = <valore>».
- `lookups.observed`: `code` intero fuori da 200-299, o `result` che comincia con `REDIRECT DETECTED`.
- `strip_bash_web` guarda il testo grezzo del comando (ruling I1), non l'elenco dei programmi; `anonymize` sostituisce `/home/<utente>`, `-home-<utente>-` e il nome come parola intera.
- `research_counts`: `mode=ro&immutable=1`, `-wal` = errore, tabella mancante = zero, corsa senza stato saltata.
- Domini web: `ai.google.dev`, `aistudio.google.com`, `vercel.com` (`scrub.WEB_DOMAINS`).
- Casi: grader e pesi di s10, s11, s12 letti dai `case.yaml`; l'indicatore è in s1, s2, s3, s6, s9; `e2` non è tra le cartelle di `evals/` (solo a secco).
- Agenti: `ls agents` dà 18 file.

## Pagine che invecchiano trovate
Quelle del piano (backend due frasi, frontend, infra due frasi, ai, frontend-fonti) più:
- `skills/rules-ai/SKILL.md`: cita `https://ai.google.dev/gemini-api/docs/models` alle righe 25, 31, 35, 39, 45, 49, 68, 78 (verificato con `grep`); `docs/profili/ai.md` non lo cita.
- `templates/models.toml` riga 23: la pagina delle deprecazioni di Gemini sta su `ai.google.dev` (dato del controllo dei modelli, non una skill; non toccato).
- **`docs/profili/database.md`, riga 97** («Chi ha già dichiarato il blocco a mano»): dice che `init --update` non propone niente; dalla rev 35 propone `min_level` e `checklist`. Non era nell'elenco del piano: l'ho aggiunta al blocco «Dopo B» e alla spec 11.2.

## Scostamenti dal piano
- Il blocco «Dopo B» sta in fondo alla sezione 9 come ultima voce dell'elenco, non come sezione numerata.
- La voce 5 del blocco «Dopo B» è un segnaposto esplicito per i minori della revisione finale (li scrive il controller).
- Nella riga di PP:288 ho scritto che `s9` cambia (D2) e ho lasciato il resto della riga, con la frase corretta in testa alla voce.
- I minori già rinviati nel ledger (Task 6: `ObservedWebFetchTest` dopo `__main__`, prefisso di `aistudio\.google\.com/docs/models`, docstring di `anonymize`, nome utente con `-` o `.`) non li ho copiati nel blocco: la decisione 12 dice che li aggiunge il controller. Il limite del nome utente con `-` o `.` è invece già nella voce sui limiti della pulizia (è nel rapporto di B8).

## Suite
Vedi sotto.

`PYTHONWARNINGS=error::ResourceWarning tests/run` (log `suite-task-8.log`): `exit 0`; Python 3.11.16 4175 test OK (skipped=13), Python 3.13.5 4175 test OK (skipped=11); nessun «unclosed». Prima di committare, `python3 -B -m unittest tests.test_docs` verde (anche dopo l'ultima modifica, che ha aggiunto i conteggi della suite al piano principale). Commit `8606917`.

## Fix round 1

I1: spec 14, «Come girano i casi» (riga 1654): ora dice che i casi `spec` sono dodici (i nove di P5, `s1`-`s9`, e i tre di B8, `s10`-`s12`, descritti in «Casi di B8») e poi elenca i nove di P5. Grep di «nove casi» in spec, `docs/uso/` e catalogo: nessun altro riferimento allo stato di oggi. `tests.test_docs` verde; suite `exit 0` (4175 test su 3.11 e su 3.13, nessun «unclosed»), log `suite-task-8-fix1.log`.
