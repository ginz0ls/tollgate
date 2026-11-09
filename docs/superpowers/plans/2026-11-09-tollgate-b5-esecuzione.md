# Esecuzione del piano B5: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md` con la skill `superpowers:subagent-driven-development`.

- **Progetto di B** (l'autorità): `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, comprese le sezioni 11 e **12 (9 novembre 2026: `services/` fuori da `backend`, scritture di KV e R2 da approvare salvo `--local`, D1 solo con `--remote`, edge function di Supabase a `database`)**. Le scelte marcate «utente» non si discutono; quelle marcate «mia scelta» si correggono solo con una `Ruling:` che dice il motivo.
- **Spec del nucleo:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 31. La revisione 32 la scrive il Task 9.
- **Piano principale di B:** `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, sezioni 1, 2, 3 (righe B3→B4-B7 e B4→B5-B7), 9 (blocchi «A B4-B7, da B3», «A B4-B8, da B3-bis», «A B5-B8, da B4») e 13.
- **Registro modello del metodo:** `docs/sdd/2026-11-06-tollgate-b4-profilo-infra/` (il più recente). Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md`, `preflight-brief.md` e `preflight-scan.md`, `task-5-fonti-brief.md` (brief del verificatore delle fonti, da estendere ai marcatori e all'esclusione), `task-9-rapporto-brief.md` (rapporto della prova), `final-review-brief.md` e `final-review.md`.

## Dove lavorare

- Ramo `b5-profilo-backend`, in un worktree isolato in `.claude/worktrees/b5`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Avvia la sessione dalla **radice del repo**, non dal worktree (memoria `sessioni-nei-worktree`).
- Il workspace SDD sta **nel worktree**: `.claude/worktrees/b5/.superpowers/sdd/<cartella stampata da sdd-workspace>`. Le copie delle fonti (`fonti/backend/`) stanno nel workspace e **non entrano mai in git** né nel registro.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (3668 su `main` dopo B4).
- **Tempi della suite.** Una corsa di `tests/run` dura da 25 a 90 minuti (due interpreti). Lanciala in background con lo strumento Bash e `run_in_background`, e controlla da solo il file d'uscita. Il brief di ogni implementatore lo dice, insieme al divieto di lanciare la suite completa più di una volta per giro quando bastano i file di test del task.
- **Implementatori fermi dopo la suite** (lezione di B4): il brief di ogni implementatore dice, in una riga a parte, «dopo aver lanciato la suite in background leggi tu il file d'uscita quando arriva la notifica, e se è verde committa e chiudi con il report: non aspettare un messaggio». Se un implementatore tace dopo la fine della suite, sollecitalo con `SendMessage` con il percorso del file d'uscita.
- **Spazio in `/tmp`.** `/tmp` è un tmpfs condiviso con altre sessioni. Prima della prima corsa controlla `df -h /tmp`: sotto 1 GB libero ti fermi e lo dici all'utente. Non spostare `TMPDIR` dentro `~/.claude` né fuori da `/tmp`.
- **Avvisi come errori, come la CI:** `PYTHONWARNINGS=error::ResourceWarning tests/run`.
- **Lucchetto di git.** La cartella è sincronizzata da MEGA: se un commit trova `.git/index.lock`, ritenta dopo qualche secondo; **non cancellare mai** `index.lock` a mano.

## Scan pre-flight

Prima del Task 1, un analista sonnet in sola lettura scrive `preflight-scan.md` (brief sul modello di `preflight-brief.md` di B4): tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme), tabella per task (test previsti contro codice previsto, file toccati da più task), conflitti con il progetto di B, con la spec rev 31 e con il codice reale di `main`. Lo giudichi tu: una `Ruling:` nel ledger e una voce in `carry.md` per ogni conflitto, **prima** di lanciare i task che ne dipendono. Punti da far guardare apposta:
- `[detect] exclude` (decisione 4) contro ogni chiamante di `init.concrete_for`, `_match`, `_concrete_paths`, `detect_files` e `_drift`, e contro i test di `tests/test_init.py` e `tests/test_fragments.py` che oggi rifiutano una chiave sconosciuta di `[detect]` (`test_detect_unknown_key_still_rejected` deve restare vero per le altre chiavi);
- i sei pattern e i marcatori del frammento vero contro gli alberi dei test che lanciano `init` dalla CLI con la radice vera (`ModeTest`, `FilesTest`, `ServicesTest`, `HintsTest`, `UpdateTest`, `ProtectScriptTest`) e contro `test_real_trees_light_no_profile` (decisione 17): un albero di prova con `server/`, `api/`, `functions/` o un file con `from flask import` accenderebbe `backend`;
- i marcatori contro `bin/` (`test_real_markers_not_in_tollgate_bin`) e contro i file dei progetti di prova esistenti (`spikes/b1/flow/`, `spikes/b3/flow/`, `spikes/b4/flow/`): un marcatore che compare lì cambia la proposta delle prove di B1-B4 e i loro test;
- `bash.effect_reason` con `FLAG_EFFECTS` e gli script dopo `run` (Task 2) contro `tests/test_bash.py`, `tests/test_effects.py`, `tests/test_check_effects.py` e `[external_effects] allow`/`commands`/`project_scripts`: nessun comando che oggi non è un effetto deve diventarlo, salvo quelli delle decisioni 6 e 7. **Lezione di B4 (ruling D13):** ogni token che fa da segnale (`run`, `run-script`, `workspace`, `--local`, `--remote`, `--preview`) va controllato contro i nomi comuni di cartelle e pacchetti dei monorepo (`docs`, `config`, `run`, `local`, `remote`, `preview`, `web`, `api`) in ogni posizione di un comando di `npm`, `pnpm`, `yarn`, `bun` e dietro `npx`;
- `test_area_agents_name_area_rules` e le frasi esatte di `tests/test_manifest.py` contro `AREAS` con `backend` (decisione 10) e contro la frase di `agents/implementer-infra.md` che cambia;
- `READONLY_TYPES` di `hooks/run` contro `config.DEFAULTS["review"]["readonly_agents"]` e `test_readonly_list_matches_config_and_agents`;
- `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=backend` contro i test esistenti di `tests/test_b1_scripts.py` (casi `b1`, `ai`, `infra`), i test rinominati con `test_real_` e `test_committed_evidence_has_no_long_web_results`; `SAVED_TOOLS` con `Bash` contro le evidenze già committate di B1-B4 (un `Bash` che stampa una copia salvata deve diventare un segnaposto; un `Bash` qualunque no).

## Ordine e modelli

1. **Task 1, 2, 3 (Step 1-6), 6, 7:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku. Il Task 2 (effetti) non dipende dal Task 1 e può partire subito dopo, uno alla volta (scrittore unico). Il Task 3 dipende dal Task 1 (`Fragment.exclude`).
2. **Task 3, Step 0** è del controller (copie delle fonti e punti (a)-(c) di «Da verificare prima del codice»), prima di lanciare l'implementatore del Task 3. Si può fare mentre gira lo scan o la baseline.
3. **Task 4:** Step 1 del controller (verificatore `Explore` sonnet in sola lettura, sul modello di `task-5-fonti-brief.md` di B4, esteso ai marcatori e a `exclude`); Step 2-5 di un implementatore sonnet.
4. **Task 5:** del controller con l'utente (fermata), poi un implementatore sonnet per gli Step 2-4. Dopo l'approvazione, nel ledger `Task 5: complete …` come per gli altri task; se l'utente rinvia, `Task 5: rinviato dall'utente` (Chiusura, variante del rinvio).
5. **Task 6** solo dopo il Task 5. **Task 7** dopo il Task 6 e il Task 2. **Task 8** del controller (esecuzione); il rapporto e la ripulitura delle evidenze li può scrivere un implementatore sonnet con un brief sul modello di `task-9-rapporto-brief.md` di B4, dopo la verifica a mano del controller (Task 8, Step 2). **Task 9:** implementatore sonnet, dopo il Task 8.
6. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
7. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice il progetto o la spec, vince il progetto, poi la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. **Ogni** riga `Ruling:` ha il costo, anche quelle che registrano una verifica (`costo: nessuno`): il rapporto prima del merge le riporta tutte con il costo. Una correzione che cambia la spec va nella revisione 32, scritta dal Task 9. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage, e quelli che riguardano B6-B8 finiscono nel piano principale di B. **Una ruling che toglie o aggiunge un token a un elenco di eccezioni o di segnali del veto** (come `PACKAGE_COMMANDS` in B4, o i token della decisione 7 qui) si controlla contro i nomi comuni di cartelle e pacchetti dei monorepo prima di scriverla (lezione di B4). Le regole approvate (`rules-base`, `rules-ai`, `rules-infra`) e le loro pagine e rapporti **non si toccano**; `rules-backend`, dopo il Task 5, cambia solo con l'utente.

## Lezioni dei piani precedenti

- **Le regole nascono come in B3 e B4:** bozza con la fonte per ogni regola, verificatore di sola lettura, pagina in parole semplici, approvazione dell'utente; solo le regole approvate entrano. Una regola nuova o con una fonte nuova ripassa dal verificatore.
- **La prova reale si divide:** script e test dell'implementatore (Task 7), esecuzione del controller (Task 8). Le correzioni del prodotto scoperte nella prova sono giri del task che possiede il codice, ognuna con un test, e si ripete solo il passo interessato. **Un esito ottenuto in più tentativi è «composito»**, e il rapporto lo dice.
- **Il piano scritto dal modello nel passo 1** (lezione di B4): se succede, il report dell'implementatore non prova da solo il precaricamento. Il rapporto lo dice, e il segnale che conta è il revisore che cita da sé una `R-BACKEND-…` che il task non nomina, o i titoli `isMeta` nelle trascrizioni dei subagenti.
- **Evidenze pubbliche** (lezione I-1 di B3 e B4): lo stream di `claude -p` contiene i `tool_result` di `WebFetch`, i testi delle skill caricate e anche i `Read`, `Grep` e `Bash` sulle copie delle pagine che Claude Code salva in `tool-results/`. Prima di ogni commit di evidenze e prima della copia del registro: `flowreg togli-pagine`, poi la verifica a mano (Task 8, Step 2) **prima di scrivere il rapporto**, poi `grep` del nome utente, dell'host, di `/home/`, degli id di sessione e delle forme di token. Il rapporto non dice «ripulito» per ciò che non ha controllato. Nei file nuovi niente nomi di progetti privati dell'utente.
- **Mai asserzioni che al fallimento mostrino `os.environ`** (incidente di B3-bis). Il brief di ogni implementatore lo dice.
- **Il brief del revisore contiene il report dell'implementatore.**
- **Workspace e registro.** Il workspace SDD sta nel worktree e si copia in `docs/sdd/` alla chiusura, senza i `.diff`, i log della suite e `fonti/`.

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Si parte da `docs/sdd/2026-11-06-tollgate-b4-profilo-infra/cautele.md`, copiato **per intero** con i percorsi di B5 (worktree `.claude/worktrees/b5`, ramo `b5-profilo-backend`, compreso l'elenco dei nomi delle chiavi, le righe sul testo non fidato, su `/tmp`, sui tempi della suite e sul test instabile `test_db_restore_interactive_eof_and_ctrl_c`); poi si aggiunge l'elenco qui sotto, che vince dove i due dicono cose diverse. Le **sole** eccezioni elencate dopo valgono **solo per il controller** e non vanno mai a un subagente.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` e una `HOME` temporanea.
- Mai leggere o scrivere i veri `~/.claude/settings.json`, `~/.claude/plugins/`, `~/.claude/projects/` (le copie delle fonti dai plugin le fa il controller, eccezione 1).
- Mai installare, abilitare o disinstallare plugin. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Chiavi, token e segreti**
- Mai leggere, stampare, copiare o scrivere il valore di una chiave o di un token (chiavi dei modelli, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `SUPABASE_ACCESS_TOKEN`, `DATABASE_URL`, `GH_TOKEN`, `GITHUB_TOKEN` e simili): né con `echo`, `env`, `printenv`, `set`, né in un test, in uno script, in un log, in un file. Si può sapere solo **se** una variabile è impostata.
- Non leggere né riportare `.env*`, `.dev.vars*`, `.vercel/`, `.wrangler/`, `supabase/.temp/`, `auth.json`, token o segreti. Nei test solo valori finti come `PROVA-123`.

**Esperimenti, servizi e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero, nessuna chiamata di rete (nemmeno su `127.0.0.1`), nessun server avviato su una porta, nessun repo su GitHub, nessun push verso la rete. `gh` nei test è `tests/fakegh.py`. Mai il `gh` vero.
- **Mai `wrangler`, `vercel`, `supabase`, `deno`, `node`, `docker`, `docker compose`, `npx`, `npm`, `pnpm`, `yarn`, `bunx`, `bun` veri**, in nessuna forma (nemmeno `--dry-run`, `--local`, `--help` o `--version`): scaricano pacchetti, eseguono codice o parlano con un servizio. Nei test e negli script i comandi di quei programmi sono solo testo dato a `bash.parse`. I file `.ts` dei progetti di prova non si eseguono.
- `spikes/run-b1-flow.sh`: solo `bash -n`, il modo `controlla` e i test di `tests/test_b1_scripts.py`. `spikes/b1/flowreg.py togli-pagine` solo sui file di `docs/verifiche/evidenze/` del worktree.

**Processi, git e file**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID.
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`. Mai `git stash`. Mai cancellare `.git/index.lock` a mano. Mai riscrivere la storia di git.
- Mai cancellare file o cartelle fuori dal worktree e dalle cartelle temporanee create dai propri test.
- La suite in background solo con lo strumento Bash e `run_in_background`, **mai con `&`, `nohup` o `setsid`**. Dopo averla lanciata, leggi tu il file d'uscita quando arriva la notifica, e se è verde committa e chiudi con il report.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit (`python3 -B`): controlla `git status` prima di `git add`.
- Non toccare `skills/rules-base/SKILL.md`, `skills/rules-ai/SKILL.md`, `skills/rules-infra/SKILL.md`, `docs/profili/base.md`, `docs/profili/ai.md`, `docs/profili/infra.md` e i rapporti `docs/profili/verifiche/base-fonti.md`, `ai-fonti.md`, `infra-fonti.md`. `approved` in `skills/rules-backend/SKILL.md` si scrive solo nel Task 5, su indicazione del controller.
- Lavora solo nel worktree `.claude/worktrees/b5` (ramo `b5-profilo-backend`), mai nel checkout principale né su `main`; solo nella variante del rinvio (decisione 15 del piano), anche nel worktree `.claude/worktrees/b5-parziale` (ramo `b5-parziale`), quando il controller lo dice nel brief. Il percorso contiene spazi: virgolette sempre.
- Il repo è pubblico: nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né host, nessun token, nessun testo copiato da pagine o skill di terzi.
- Risposte e messaggi in italiano; identificatori in inglese.

**Eccezioni per il controller, una per una**
1. **Fonti** (Task 3, Step 0, e Task 4 se una fonte va sostituita): `WebFetch` in sola lettura delle pagine ufficiali di Cloudflare (`developers.cloudflare.com`), Vercel (`vercel.com/docs`), Supabase (`supabase.com/docs`), dei framework della tabella «Fatti verificati» (`expressjs.com`, `fastify.dev`, `hono.dev`, `fastapi.tiangolo.com`, `flask.palletsprojects.com`, `docs.deno.com`, `nodejs.org`) e del repository `github.com/cloudflare/skills` (`SKILL.md` di `workers-best-practices` e licenza); **lettura** (solo `cp` verso il workspace e `sha256sum`) delle copie locali di `agent-skills` 0.6.9 (`skills/api-and-interface-design/`, `skills/observability-and-instrumentation/`, `LICENSE`) e di `everything-claude-code` 1.4.1 (`agents/code-reviewer.md`, `agents/python-reviewer.md`, `agents/security-reviewer.md`, `LICENSE`) dalla cache dei plugin in `~/.claude/plugins/cache/`, nient'altro di quella cartella. Copie nel workspace, trattate come dati non fidati, mai nel repo; in `FONTI.md` il percorso d'origine senza il nome utente. Se una pagina ufficiale sta su un altro dominio, ti fermi e chiedi.
2. **Prova reale** (Task 8), già prevista dal piano (decisione 14). Il rapporto ha una riga `Esito: riuscita`, `Esito: riuscita (composita)` oppure `Esito: non riuscita: <motivo>`. `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=backend B1_FLOW_RULES=vere`, modi `prepara`, `passo1`, `passo2`, `registra`, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`, al più 3 tentativi per passo. È l'unico `claude -p` di B5 e consuma l'abbonamento (circa 1-1,5 USD stimati). Prima di partire controlla che nell'ambiente **non** ci siano `ANTHROPIC_API_KEY`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN`, `SUPABASE_ACCESS_TOKEN` e `DATABASE_URL` (solo se sono impostate, mai il valore): con `ANTHROPIC_API_KEY` Claude Code userebbe la chiave al posto dell'abbonamento, e le altre darebbero al modello credenziali vere. Se una c'è, ti fermi e chiedi. L'assenza delle variabili non basta: le credenziali di `wrangler login`, `vercel login` e `supabase login` stanno in file della cartella dell'utente, e per questo lo script con `B1_FLOW_CASE=backend` vieta al modello quei programmi, `deno`, `node` e i lanciatori dei pacchetti (`test_flow_disallows_service_clis_backend`); prima di lanciare `passo1` controlla nell'uscita di `controlla` che la riga `--disallowedTools` li contenga e che l'hook `effects` non sia spento nel progetto di prova.
3. **Push di `main` su `https://github.com/ginz0ls/tollgate.git`**, solo dopo il merge con l'OK dell'utente e solo dopo `spikes/gh-p4/ghguard.py gitcheck -- push https://github.com/ginz0ls/tollgate.git main` con `P4_PROFILE=p5` uscito con 0; mai forzato. Poi `gh run list|view|watch` della CI di `main`, dalla guardia con lo stesso profilo (`run list` senza `--branch`). Nessun altro comando verso GitHub. Se GitHub risponde 500 a corpo vuoto, si ritentano solo le letture (memoria `github-500-transitorio`).

Vietati anche al controller: `claude plugin eval`; `wrangler`, `vercel`, `supabase`, `deno`, `node`, `docker`, `npx` veri; ogni operazione sui repo di prova di P4 e su altri repo; leggere o stampare chiavi e token; cambi di visibilità; cancellare repo o rami remoti; riscrivere la storia; cancellazioni in `/tmp` fuori dalle cartelle della prova.

## Quando fermarsi e chiedere

Solo in questi casi:
- **l'approvazione delle regole** (Task 5, Step 1): fermata prevista;
- una pagina ufficiale che smentisce un fatto della tabella «Fatti verificati» del piano al punto da cambiare una decisione (per esempio un comando di D1 con il predefinito remoto, o un comando di KV o R2 senza `--local`);
- più di 3 tentativi di un passo della prova reale, o una variabile di credenziali nell'ambiente prima della prova (eccezione 2);
- `/tmp` sotto 1 GB libero;
- un'operazione distruttiva o irreversibile, o un'operazione su GitHub fuori dall'eccezione 3;
- un'azione fuori da questo worktree (e da `.claude/worktrees/b5-parziale` nella variante del rinvio), come un merge su `main`;
- un piano rotto al punto che ogni strada è un'ipotesi;
- una pagina ufficiale che sta solo su un dominio fuori dall'eccezione 1.

Il messaggio all'utente di ognuna di queste fermate, salvo l'approvazione delle regole e il merge, comincia con la riga `Fermata: <caso>` (per esempio `Fermata: fatto smentito nel Task 3, Step 0`), così la condizione del brief corto la riconosce.

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

**Come chiedere all'utente** (memoria `feedback-spiegazioni-semplici`): prima la spiegazione in 2-4 frasi senza gergo, poi le strade con il costo esplicito (gratis, consumo dell'abbonamento o spesa vera), poi il consiglio. La pagina delle regole si presenta in breve: quante regole, quali bloccano, i punti dubbi in «Da decidere tu» con la proposta per ognuno, come rispondere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: «Decisioni di questo piano», «Review Focus», la tabella «Copertura», le righe `minor (deferred)` del ledger da sottoporre a triage, il rapporto della prova reale, le regole di cautela. Chiedigli in particolare di cercare: un file sotto `supabase/`, `.github/tollgate/`, `.claude/` o la cartella della proposta che accende `backend`; un marcatore che accende file di test, documenti o il codice di tollgate; una scrittura remota di Wrangler che passa senza veto, anche dietro `npx`, o una locale che chiede senza motivo fuori dai costi scritti; un token di segnale (`run`, `--local`, `--remote`) che un nome di cartella o di pacchetto può imitare; un percorso concreto di `backend` che vince su `infra` o su `ai` dove non deve; un `tollgate.toml` dell'utente riscritto; una regola `[blocca]` che si regge solo sulla nota; un test che dipenda in silenzio dai file veri del plugin senza il prefisso `test_real_` o dalle variabili della macchina; testo di terzi (anche da `Read`, `Grep`, `Bash` su `tool-results/`), token o dati dell'utente nelle evidenze; un agente d'area che diverge dal generico.
   Nel ledger una riga `Revisione finale (opus): <verdetto>, <n> critical, <n> important, <n> minor`. La revisione scrive in `final-review.md` una tabella di triage delle righe `minor (deferred)`, con l'esito di ognuna in una colonna: `da correggere`, `nessuna azione` o `rinviato`.
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano. Se una correzione tocca ciò che la prova reale ha provato, ripeti solo il passo interessato (eccezione 2). Quando non ne restano, nel ledger la riga `Revisione finale chiusa: 0 critical, 0 important aperti`.
3. **Suite tre volte**: `PYTHONWARNINGS=error::ResourceWarning tests/run` (python3.11 e python3), tre corse verdi, nessun «unclosed database», nessuna cartella nuova in `/tmp` dopo le corse. Nel ledger, per ogni corsa verde, la riga `Suite finale corsa <N>: verde su python3.11 e python3` seguita dal numero dei test; `<N>` conta solo le corse verdi (1, 2, 3); una corsa rossa si scrive `Suite finale corsa rossa: <motivo>` e non conta (per il test instabile del pty vale la regola delle cautele).
   **Variante del rinvio** (decisione 15 del piano): se l'utente rinvia al Task 5, nel ledger la riga `Task 5: rinviato dall'utente`; poi il Task 9 ridotto (riga `Task 9 ridotto: complete`), il ramo `b5-parziale` come dice la decisione 15, e i punti 1-3 su `b5-parziale`.
4. **Niente merge su `main` senza l'OK dell'utente.** Il rapporto all'utente prima del merge, in italiano e in parole semplici, contiene, **ciascuna come sezione con un titolo proprio**:
   - «Commit e test»: il numero dei commit del ramo e il numero dei test dell'ultima corsa;
   - «Regole approvate»: quante, quali bloccano, la data dell'approvazione;
   - «Decisioni prese durante il lavoro»: **l'elenco completo** delle righe `Ruling:` del ledger, **una per riga**, ognuna con il suo costo se sbagliata;
   - «Rilievi minori rinviati»: **l'elenco completo** delle voci della tabella di triage di `final-review.md` con l'esito `rinviato`, **una per riga**, ognuna con il motivo;
   - «Prova reale»: l'esito, se composito, il consumo stimato (nella variante del rinvio: «non fatta: regole rinviate»);
   - «Cosa cambia nei progetti»: `/tollgate:init --update` propone `backend` dove ci sono i suoi file; `services/` e `supabase/` non lo accendono; le scritture di KV e R2 chiedono il permesso salvo `--local`, quelle di D1 solo con `--remote`; gli script `deploy` dei monorepo chiedono il permesso; come aggiungere a mano un typecheck o i test delle API in `dod`; la pagina approvata di `infra` dice ancora che le scritture di KV, D1 e R2 non sono coperte, e ora lo sono;
   - per ultima, la riga «Posso unire su `main`?».
   **Variante del rinvio:** prima di questo rapporto, nel ledger una riga `b5-parziale: <sha> <oggetto>` per ogni commit del ramo (i Task 1 e 2, i loro giri di correzione, il Task 9 ridotto), aggiornata a ogni commit nuovo del ramo; sono le righe che il brief corto cerca e che restano anche se il ramo si toglie.
   Il merge, con l'OK, entra su `main` come un solo commit con l'oggetto `tollgate B5: profilo backend (server, API, Worker)` (nella variante del rinvio `tollgate B5 (parziale): esclusione per frammento ed effetti di Wrangler`), come per B4.
5. Dopo il merge (con l'OK):
   - push di `main` (eccezione 3) e attesa della CI verde su `main`;
   - copia il registro dal worktree in `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/` con un `README.md`, come per B4, dopo il controllo delle evidenze, e committalo su `main` (e push);
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`) con una riga che comincia con `- B5 eseguito` (nella variante del rinvio `- B5 parziale`, che dice cosa resta sul ramo): esito di B5, prossimo passo (scrivere il piano di B6, `frontend`);
   - **trascrizioni**: se una sessione del lavoro è partita dalla cartella del worktree, spostane i `.jsonl` (e le cartelle `<id>/`) con `mv -n` nella cartella della radice in `~/.claude/projects/`, mai il file della sessione attiva. Se tutte le sessioni sono partite dalla radice, dillo;
   - chiedi all'utente se rimuovere il worktree e il ramo `b5-profilo-backend` ormai uniti (nella variante del rinvio la domanda riguarda **solo** il worktree `.claude/worktrees/b5-parziale` e il ramo `b5-parziale`: `.claude/worktrees/b5` e `b5-profilo-backend` restano, perché contengono il workspace con le fonti e i Task 3-4 da riprendere, e il rapporto di chiusura lo dice);
   - **rapporto di chiusura all'utente**, in un messaggio a sé che comincia con la riga «Chiusura di B5», con: il commit del merge su `main`, l'esito della CI di `main`, il percorso del registro, la riga della memoria aggiornata, cosa è successo alle trascrizioni, e la domanda sul worktree.
