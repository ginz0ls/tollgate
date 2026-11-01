# tollgate B: piano principale

Data: 27 ottobre 2026.
Progetto: `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (approvato dall'utente il 27 ottobre 2026), da qui «il progetto». Spec del nucleo: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 28 (scritta da B2; B2 è partita dalla 27, scritta da B1). Catalogo: `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, di cui B usa sei profili.

Il progetto dice **cosa** fa B e perché; questo documento dice **in che ordine** si costruisce, **cosa consegna** ogni fetta e **quando B è finito**. Il codice e i passi stanno nei piani delle singole fette.

Stato (1 novembre 2026): **B1 unita su `main`** il 29/10/2026, in fast-forward fino a `6b4fd3d` (piano `2026-10-27-tollgate-b1-informati-prima.md`, con `-esecuzione.md` e `-brief-sessione.md`; registro in `docs/sdd/2026-10-27-tollgate-b1-informati-prima/`); prova reale di un lavoro L1 (`docs/verifiche/2026-10-27-b1-prova-flusso.md`). **B2 sul ramo `b2-regole-base`, merge in attesa dell'OK dell'utente** (piano `2026-10-29-tollgate-b2-regole-di-base.md`, con `-esecuzione.md` e `-brief-sessione.md`): `rules-base` approvata dall'utente il 01/11/2026 (11 regole), blocco acceso, caricamento nei quattro agenti di codice, prova reale corta riuscita (`docs/verifiche/2026-10-29-b2-prova-flusso.md`), spec del nucleo alla revisione 28. Suite: 3218 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning` (come la CI). Le prove punto per punto di B1 sono nella sezione 8, quelle di B2 nella sezione 10, i rinvii alle fette successive nella sezione 9. B3 e successive: nessuna.

---

## 1. Regole

1. **Un piano per fetta, scritto al suo turno.** Il piano di B(n+1) si scrive quando B(n) è unito su `main`, partendo dal codice reale e dalle interfacce che B(n) ha prodotto davvero. La sezione 3 dà i nomi indicativi: valgono quelli del codice.
2. **Si costruisce con Superpowers** (subagent-driven-development), su un ramo e un worktree per fetta, con revisione finale su opus e merge su `main` solo con l'OK dell'utente. È lo stesso metodo di P1-P5.
3. **Una correzione della spec del nucleo** scoperta in una fetta diventa una nuova revisione della spec, scritta dall'ultimo task della fetta. Una correzione del progetto di B si scrive nel progetto, con la data e il motivo, solo per le scelte marcate «mia scelta»; quelle marcate «utente» si cambiano solo con l'utente.
4. **Le regole dei profili le approva l'utente** (progetto, sezione 5). Una fetta che porta un profilo non è finita finché la pagina del profilo non è approvata; il codice della fetta si può unire prima, con il profilo spento.
5. **Questo documento si aggiorna alla chiusura di ogni fetta**: stato in testa, riga della fetta nella sezione 2, nomi reali nella sezione 3.

---

## 2. Sequenza

| Fetta | Obiettivo | Richiede | Consegna | Finita quando |
|---|---|---|---|---|
| **B1 Informati prima** | Il meccanismo del passo «informati prima» (progetto 3), senza regole | `main` con il progetto di B e i quattro file del piano di B1 | Verifiche della sezione 3.5 del progetto; strumenti per informarsi agli implementatori (`WebFetch` e `WebSearch`; context7 non usabile dai subagenti, B1-V2); registrazione delle letture dagli hook; nota di ricerca con il comando `research submit`; controllo in `PreToolUse` (avviso in L0, blocco in L1 e L2, **spento finché `rules-base` non è approvata**: fino ad allora avviso a ogni livello); controllo del revisore del task; lavori iniziati prima di B esclusi; test, prova reale di un lavoro L1, spec del nucleo alla revisione 27 | Criteri della tabella «Copertura» del piano di B1 come test; prova reale L1 riuscita; revisione finale senza `critical` né `important` aperti. **Stato:** unita su `main` il 29/10/2026 (fino a `6b4fd3d`), prove nella sezione 8; due scostamenti dal progetto: la deroga di `adopt` (sezione 9) e `Grep` fuori dal matcher di `PostToolUse` (B1-V6) |
| **B2 Regole di base** | `rules-base` approvata e il blocco acceso | B1 | `skills/rules-base/SKILL.md` (sezione «Prima di scrivere», regola sui nomi dei modelli, progetto 3.4 e 3.6) con le fonti; verifica delle fonti da un agente di sola lettura; pagina per l'utente in parole semplici; caricamento di `rules-base` in ogni implementatore e revisore, generici compresi (progetto 4, riga `base`); approvazione registrata, che accende il blocco | Pagina approvata dall'utente; il blocco scatta in L1 e L2 (test e una prova reale corta). **Stato:** sul ramo `b2-regole-base`, merge in attesa dell'OK dell'utente; prove nella sezione 10. Le regole sono 11 (la verifica delle fonti ne ha tolte due bozze su 12 e l'utente ne ha rimessa una corretta); il rifiuto del blocco non si è visto dal vivo nella prova reale (la nota è arrivata prima di ogni modifica), è provato dai test sulla regola vera |
| **B3 Profili, infrastruttura e `ai`** | Il primo profilo verticale e ciò che serve a tutti | B2 | Frammenti di profilo nel plugin e `init` che propone solo i profili approvati e presenti nel repo; `rules-ai` con «Dove informarsi» (pagine ufficiali dei modelli di Gemini e Claude, progetto 4); `implementer-ai`, `reviewer-ai`; percorsi, `dod` | Pagina di `ai` approvata; profilo acceso; test e prova reale corta |
| **B4 `infra`** | Deploy, Vercel, Cloudflare, server | B3 | `rules-infra` con Vercel (progetto 4), agenti, percorsi (anche `vercel.json`), `dod` | Pagina approvata; profilo acceso |
| **B5 `backend`** | API e server, anche backend locale senza Supabase | B3 | `rules-backend`, agenti, percorsi, `dod` | Pagina approvata; profilo acceso |
| **B6 `frontend`** | Interfacce | B3 | `rules-frontend` (e `rules-a11y` solo se il revisore la richiede: catalogo 2.1, da decidere nel piano della fetta), agenti, percorsi, `dod` | Pagina approvata; profilo acceso |
| **B7 `database`** | Schema, migrazioni, RLS, edge function di Supabase | B3 | `rules-database`, agenti, specialista finale `final-database` (L2), percorsi, `dod` | Pagina approvata; profilo acceso |
| **B8 Eval e chiusura** | La misura minima e la chiusura di B | B1-B7 | 2-3 casi `claude plugin eval` sugli schemi della sezione 1 del progetto, con e senza plugin, tetto di 20 USD di costo stimato; rapporto; spec del nucleo e catalogo aggiornati; questo documento chiuso | Sezione 5 di questo documento |

B4, B5, B6 e B7 dipendono solo da B3 e non tra loro: l'ordine scritto è quello consigliato (prima le aree con più correzioni dell'utente sulla documentazione), e si può cambiare. Se due di loro risultano piccole quando si scrive il piano, si uniscono in una fetta (brief di scrittura, «due per fetta se sono piccoli»).

---

## 3. Interfacce tra le fette

I nomi li fissa la fetta che li produce; la successiva li copia dal codice, non da qui.

| Produce | Consuma | Contratto (indicativo) |
|---|---|---|
| B1 | B2 | **Interruttore del blocco.** `tollgate_analysis.research.RULES_BASE` (`"skills/rules-base/SKILL.md"`) e `research.enforced(skill_text: str \| None) -> bool`: vero solo se il frontmatter ha un campo `approved` non vuoto. B1-V7 è positivo (`claude plugin validate --strict` accetta il campo): **non esiste** un file `APPROVED`. Non conta come approvazione un valore vuoto, `null`, `~`, `false` o un indicatore di blocco YAML (`\|`, `>`); qualunque altro valore conta. B2 (rev 28) ha escluso anche `no`, `off` e `n`, e il confronto avviene dopo aver tolto gli apici (anche per `false`), in ogni combinazione di maiuscole, e ha scritto la data `approved: 2026-11-01`. Un file che non si legge dà `lookups.rules_switch(root) -> (acceso, errore)`: spento con traccia (evento `research_switch_unreadable`). Lo legge il gate (`research_gate`, `ctx.plugin_root`) con `lookups.rules_switch(root)`; `taskcmd.review_prepare` (per il brief del revisore) usa `lookups.rules_enforced(root)`, uguale a `rules_switch(root)[0]`. B2 scrive l'approvazione quando l'utente approva la pagina; nessun altro codice cambia. Il componente `[components] research_note` spegne il passo per un progetto (R10) |
| B1 | B2-B7 | **Nota di ricerca.** Formato con le sezioni `## Letto nel progetto`, `## Documentazione`, `## Cosa ho trovato`, `## Nessuna fonte esterna` (al posto di «Documentazione», non insieme); fonti nella forma `<URL> — <cosa dice>` o `context7:<libraryId> — <cosa dice>` (separatore ` — ` o ` - `); al più 8.000 caratteri. Comando `research submit <k>` (testo da stdin, heredoc con il delimitatore `'NOTA_DI_RICERCA_FINE'`, `research.HEREDOC_END`); `research show <k>` la rilegge. Codice: `tollgate_analysis.research` (`parse_note`, `check_note`, `submit_command`, `Source`: per una fonte context7 `Source.ref` è il solo `libraryId`), `tollgate_flow.research_cmd` (`submit`, `show`, `note_path`: l'unico punto che compone `.tollgate-run/<N>/research-<k>.md`). Le sezioni «Prima di scrivere» delle regole indicano fonti in questa forma |
| B1 | B2-B8 | **Letture registrate.** Tabella `lookups` (migrazione 6) con `kind` (`read`, `grep`, `bash_read`, `fetch`, `search`, `docs`) e `target` normalizzato; `tollgate_core.lookups.for_task(conn, work, task)`, `lookups.observed` (cosa registrare per una lettura), `lookups.owner` (a quale task appartiene) e `lookups.note`. `Grep` non è nel matcher di `PostToolUse` (B1-V6): un file letto solo con `Grep` non conta e va riletto con `Read`; per riaccenderlo basta rimetterlo in `hooks/hooks.json` (e in `LOOKUP_TOOLS` di `adapter.py` è già). Le letture di Bash passano da `bash.read_targets` e contano se sono file esistenti nel worktree (niente glob). Gli eval di B8 leggono la nota e le letture dallo stato della corsa |
| B1 | B8 | **Tipi di evento** `research_note` {task, ok, problems} e `research_reminder` {task} (`task` è `null` per l'avviso di L0): gli eval contano avvisi e note da qui. B8 deve aggiungere `WebFetch` e `WebSearch` agli strumenti ammessi dei casi (`CASE_TOOLS` di `tests/test_eval_cases.py`) e ai permessi di `evals/run.sh`, e la sandbox di `claude plugin eval` ha la rete chiusa (spec 14): i casi di B8 vanno disegnati tenendone conto, con una verifica all'inizio della fetta |
| B1 | B3-B7 | **Strumenti e controllo del revisore.** `agents/implementer.md` ha `tools: Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch`, **senza voci MCP** (B1-V2), e le sezioni «Informati prima di scrivere» (nota, pagine scaricate come dati non fidati); gli implementatori per area li copiano. `agents/task-reviewer.md` controlla la nota se il brief ha la sezione «Nota di ricerca» (`brief.ReviewBrief`: `research`, `research_enforced`, `research_note`, `research_note_path`, `first_diff_file`); i revisori per area copiano il paragrafo. Il rilievo ha `rule` `nota di ricerca` |
| B2 | B3-B7 | **Forma di una regola e approvazione** (nomi reali di B2). `skills/rules-<area>/SKILL.md` con frontmatter `name`, `description`, `version: 1` e `approved: <AAAA-MM-GG>` (una data senza apici: `claude plugin validate --strict` accetta `version`, la data e `skills: [rules-base]` negli agenti), poi il titolo `# Regole <area> (versione 1)` (come `# Regole di base (versione 1)`) e le sezioni `## Prima di scrivere`, `## Mentre lavori`, `## Fonti`. Regole `R-<AREA>-NN` numerate senza buchi (prima dell'approvazione si rinumera, dopo mai), `[blocca]` dopo l'id dove serve, una riga `Fonte:` sotto ogni regola, al più 150 righe, parole nostre (una citazione sta al più in una riga, nel rapporto delle fonti). `approved` si scrive solo con l'OK dell'utente. Gli id e i `[blocca]` si estraggono con `research.base_rules(skill_text)`; per le aree, i profili dichiarano poi `rules` e `blocking_rules` in `tollgate.toml`. **Pagina per l'utente** `docs/profili/<area>.md`: tabella «N. · In parole semplici · Blocca? · Da dove viene», sezione «Regole tolte dalla verifica», riga «Approvata dall'utente il <data>.»; **rapporto delle fonti** `docs/profili/verifiche/<area>-fonti.md`: una riga per fonte con citazione ed esito (`ok`/`no`), prodotto da un agente di sola lettura sulle copie locali delle fonti (con somma di controllo); una regola senza fonte `ok` esce dalla bozza. Test da copiare: `tests/test_rules_base.py` (`RulesBaseTest` per la skill, `RulesBasePageTest` per pagina e rapporto). **Come `rules-base` arriva agli agenti:** `skills: [rules-base]` nel frontmatter di `implementer`, `task-reviewer`, `final-reviewer` e `finding-verifier` (dopo `tools:`), fuori dal tetto di 3, mai nel brief e mai in `tasks.skills_required` (`test_manifest.py`: `test_code_agents_preload_rules_base`, `test_other_agents_do_not_preload`; `test_taskcmd.py`: `test_rules_base_not_required`). L'avviso del passo la nomina (`tollgate:rules-base`). Gli agenti per area la portano allo stesso modo (sezione 9); se `rules-<area>` si precarica nello stesso modo o resta nel brief, nel tetto di 3, lo decide B3. Le `R-BASE-NN` sono note al verdetto: `lookups.base_rules(root, active)` le dà a `task_verdict` e a `apply._final_rules` (con `active` uguale a `research.active` del lavoro), e solo le `[blocca]` bloccano, con l'interruttore acceso e solo nei lavori con il passo |
| B3 | B4-B7 | **Frammenti di profilo e attivazione.** Un frammento TOML per profilo nel plugin con le chiavi di 11.4 (`kind`, `paths`, `min_level`, `skills`, `agent`, `reviewer`, `reviewer_skills`, `final_specialist`, `rules`, `blocking_rules`, `dod`, `commands`, `gate`); `init --propose` e `init --update` aggiungono a `tollgate.toml` solo i profili con la regola approvata e con file corrispondenti nel repo. Agenti `tollgate:implementer-<area>` e `tollgate:reviewer-<area>` derivati dal testo di `implementer.md` e `task-reviewer.md` (con l'attribuzione MIT) |

---

## 4. Copertura del progetto

| Punto del progetto | Fetta |
|---|---|
| 1 Perché: l'implementatore senza `WebFetch`, `WebSearch`, context7 | B1 |
| 2 Obiettivo 1 (passo comune) e 2 (controllo sulle letture registrate) | B1 |
| 2 Obiettivo 3 (primo gruppo di profili) | B2 (`base`), B3-B7 |
| 2 Obiettivo 4 («Dove informarsi» per profilo) | B2-B7 |
| 2 Obiettivo 5 (implementatore e revisore per area) | B3-B7 |
| 2 Non obiettivi | nessuna fetta li costruisce; `security` è il primo candidato dopo B (sezione 7) |
| 2 Anti-obiettivo: frase vuota senza lettura registrata | B1 (controllo 3.3) |
| 2 Anti-obiettivo: passo troppo pesante | B1 (L0 solo avviso, una volta per lavoro); B3-B7 (`frontend` e `backend` con livello minimo L0) |
| 2 Anti-obiettivo: regole mai lette da una persona | B2-B7 (pagina approvata) |
| 2 Anti-obiettivo: fonti inventate | B1 (fonte dichiarata senza lettura = nota non valida); B2-B7 (verifica delle fonti delle regole) |
| 3.1 Avviso in L0, blocco in L1 e L2, L0 che cresce | B1 (meccanismo); B2 (accensione) |
| 3.2 Nota di ricerca | B1 |
| 3.3 Cosa controlla tollgate; pertinenza dal revisore | B1 |
| 3.4 «Dove informarsi» per profilo | B2 (`base`), B3-B7 |
| 3.5 Strumenti dell'implementatore, verifiche e ripieghi | B1 (Task 1 e seguenti); gli implementatori per area di B3-B7 copiano gli strumenti |
| 3.6 Giri di correzione, L0 | B1 |
| 3.6 Nomi dei modelli AI in `rules-base` | B2 |
| 4 I sei profili | B2-B7 |
| 5 Come nascono le regole; ordine; fine di B | B2-B7; sezione 5 qui sotto |
| 6 Lasciato a chi costruisce | B1 (nota, letture, confronto, messaggi, revisione della spec); B2 (come `rules-base` arriva agli agenti); questo documento (ordine e dimensione delle fette) |
| 7 Test della suite; prova reale L1 | B1 |
| 7 Eval minimi, tetto di 20 USD di costo stimato | B8 |
| 8 Vincoli; lavori iniziati prima di B | B1 (colonna `work_items.research`) e ogni fetta |

---

## 5. Quando B è finito

Dal progetto, sezione 5, più le regole del nucleo:
- le sei pagine (`base`, `ai`, `infra`, `backend`, `frontend`, `database`) sono approvate dall'utente e i profili sono accesi; un profilo che l'utente rinvia esce da B e lo dice il rapporto finale;
- il blocco del passo «informati prima» è acceso (B2);
- ogni fetta è unita su `main` con la revisione finale chiusa e la suite verde su Python 3.11 e 3.13, anche con `PYTHONWARNINGS=error::ResourceWarning` (come la CI: `-W` non vale nei sottoprocessi);
- gli eval minimi di B8 sono girati nel tetto di 20 USD di costo stimato, con il rapporto;
- la spec del nucleo e il catalogo dei profili riportano ciò che B ha cambiato, e questo documento ha lo stato finale.

---

## 6. Rischi della sequenza

| Rischio | Effetto | Come si gestisce |
|---|---|---|
| Le verifiche di B1 smentiscono un fatto portante (letture non registrabili, `agent_id` assente) | Il controllo 3.3 si indebolisce | Ripieghi già decisi nel progetto 3.5; il Task 1 di B1 li applica e il disegno dei task successivi lo dice |
| context7 non usabile dai subagenti del plugin (oggi, nella sessione dell'utente, il server di context7 espone solo gli strumenti di autenticazione) | Solo `WebFetch` e `WebSearch` | Ripiego del progetto 3.5: le regole «Dove informarsi» indicano URL ufficiali |
| L'utente non ha tempo per rivedere le pagine | Profili spenti a lungo | Il codice si unisce prima, con il profilo spento (regola 4); le pagine sono una per profilo e brevi |
| Il blocco rallenta troppo i lavori piccoli | Anti-obiettivo del progetto | L0 solo avviso; il conteggio degli avvisi e dei rifiuti è negli eventi e B8 lo misura |
| Il costo degli eval supera il tetto | Casi senza esito | Tetto di 20 USD di costo stimato con `--max-cost-usd` al residuo; al tetto ci si ferma e si chiede |

---

## 7. Decisioni di questo piano

Scelte di chi scrive, che l'utente può ribaltare.

1. **Il blocco spento prima di `rules-base` vale come avviso a ogni livello**, non come silenzio: il meccanismo si prova sui lavori veri da subito e nessun lavoro si ferma. Costo: qualche avviso in più finché B2 non è chiusa.
2. **L'interruttore è il campo `approved` di `rules-base`**, non un'opzione di `tollgate.toml`: l'approvazione è dell'utente sul plugin, non del singolo progetto. Il progetto può solo spegnere il passo con `[components] research_note = false`. Costo: per provare il blocco prima di B2 la prova reale di B1 usa una copia del plugin con una `rules-base` di prova, marcata come tale.
3. **Un profilo per fetta da B3 a B7**, con l'infrastruttura dei profili in B3 insieme al primo profilo (`ai`), perché i frammenti e `init` si provano meglio su un profilo vero. `ai` per primo: è l'area con le correzioni più frequenti dell'utente (nomi dei modelli scritti a memoria).
4. **Gli eval in una fetta a sé (B8)**, dopo tutti i profili: misurano il passo con le regole vere, non con la sola meccanica.
5. **`security` resta fuori da B** (progetto, «mia scelta, da segnalare»): primo profilo dopo B.

---

## 8. Prove di B1

Ogni riga della tabella «Copertura» del piano di B1, con il test o l'evidenza che la prova. «T» sta per `tests/`. Un punto senza prova in B1 lo dice, con il motivo. I numeri dei task sono quelli del piano di B1.

| Punto del progetto | Task | Prova |
|---|---|---|
| 1, causa tecnica: implementatore senza `WebFetch`, `WebSearch`, context7 | 5 | T`test_manifest.py`: `test_implementer_tools` (alla lettera, senza voci MCP), `test_implementer_mentions_untrusted_pages`, `test_implementer_mentions_research_submit`. Context7: **non provato come strumento** (B1-V2 negativo per autenticazione); ripiego del progetto 3.5 applicato, rapporto `docs/verifiche/2026-10-27-b1-verifiche.md` |
| 2, obiettivo 1: passo comune prima di modificare file | 4, 6, 7, 8 | T`test_check_research_gate.py`: `test_l1_without_note_denied_when_enforced`, `test_bash_write_by_implementer_denied`, `test_docs_and_run_files_exempt`; T`test_taskcmd.py`: `test_task_start_brief_has_research_cmd`; T`test_check_agents.py`: `test_implementer_reminder_mentions_note`; prova reale (nessuna modifica prima della nota valida) |
| 2, obiettivo 2: controllo delle fonti sulle letture registrate | 2, 3, 4, 6 | T`test_research.py`: `test_check_note_valid`, `test_check_note_url_normalized`, `test_check_note_context7`; T`test_check_lookups.py` (registrazione, per tipo di strumento); T`test_research_cmd.py`: `test_lookups_of_previous_round_count`, `test_lookups_of_other_task_do_not_count`; prova reale (prima consegna rifiutata, seconda valida) |
| 2, anti-obiettivo «frase vuota senza lettura registrata» | 3, 6, 7 | T`test_research.py`: `test_check_note_file_not_read`, `test_check_note_source_not_read`, `test_search_alone_not_a_source`, `test_parse_note_empty_sections`; T`test_check_research_gate.py`: `test_invalid_note_denied_with_problems`, `test_resubmitted_invalid_note_blocks_again` |
| 2, obiettivi 3 e 5 (primo gruppo di profili, agenti per area) | — | **Senza prova in B1:** sono B2-B7 (sezione 4 sopra) |
| 2, anti-obiettivo «passo troppo pesante»: L0 solo avviso, una volta per lavoro; permessi di `WebFetch` | 7, 5 | T`test_check_research_gate.py`: `test_l0_warns_once`, `test_l1_without_note_warned_when_not_enforced`, `test_reminder_per_task`; T`test_skill_contract.py`: `test_setup_proposes_web_permissions` (decisione 18). La domanda di permesso in una sessione interattiva **non è provata** (le prove con `claude -p` concedono gli strumenti con `--allowedTools`): lo dice il rapporto della prova reale |
| 2, anti-obiettivo «regole mai lette da una persona» | — | **Senza prova in B1:** sono le pagine approvate di B2-B7 |
| 2, anti-obiettivo «fonti inventate» nella nota | 3, 6 | T`test_research.py`: `test_check_note_source_not_read`; T`test_research_cmd.py`: `test_submit_invalid_lists_problems`; prova reale |
| 3.1 L0 avvisa, L1 e L2 bloccano; L0 che cresce; interruttore | 7 | T`test_check_research_gate.py`: `test_l0_warns_once`, `test_l0_grown_to_l1_blocks`, `test_l1_without_note_denied_when_enforced`, `test_l1_without_note_warned_when_not_enforced`, `test_component_off`; T`test_research.py`: `test_enforced`, `test_enforced_not_a_real_value`. L2: stessa regola di L1, **senza un test dedicato** |
| 3.2 contenuto della nota, «nessuna fonte esterna» con motivo | 3, 6, 8 | T`test_research.py`: `test_parse_note_complete`, `test_parse_note_none_with_reason`, `test_check_note_no_external_without_reason`; T`test_research_cmd.py`: `test_submit_valid_note`; T`test_brief.py`: `test_review_brief_fences_note` |
| 3.3 punti 1-4 | 3, 4, 6 | T`test_research.py` (`check_note`, `parse_note`, tetto di 8.000 caratteri: `test_parse_note_too_long`, e «non tutte e due»: `test_parse_note_both_sources_and_none`); T`test_check_lookups.py` (letture); T`test_research_cmd.py` |
| 3.3 pertinenza dal revisore del task | 8 | T`test_brief.py`: `test_review_brief_missing_note_enforced`, `test_review_brief_missing_note_not_enforced`; T`test_taskcmd.py`: `test_review_prepare_includes_note`, `test_review_prepare_enforced_when_rules_base_approved`; T`test_manifest.py`: `test_task_reviewer_checks_note`. **Provata solo in parte:** il giudizio di pertinenza è del modello; la prova reale mostra la sezione nel brief e nessun rilievo, ma nessun caso di nota non pertinente è stato mostrato a un revisore vero (è un caso per gli eval di B8) |
| 3.4 «Dove informarsi» | — | **Senza prova in B1:** sono le regole dei profili (B2-B7); B1 consegna il formato delle fonti (decisione 2) |
| 3.5 strumenti, pagine come dati non fidati | 5 | T`test_manifest.py`: `test_implementer_tools`, `test_implementer_mentions_untrusted_pages`; T`test_brief.py`: `test_review_brief_fences_note` |
| 3.5 le tre verifiche e i ripieghi | 1 | Rapporto `docs/verifiche/2026-10-27-b1-verifiche.md` (B1-V1..B1-V7), evidenze in `docs/verifiche/evidenze/b1/`; T`test_b1_scripts.py` per gli script. Conseguenze nei Task 3-7 |
| 3.5 context7 assente → solo `WebFetch` | 1, 5 | Rapporto del Task 1 (ripiego scattato); T`test_manifest.py`: `test_implementer_tools`; T`test_check_effects.py`: `test_doc_mcp_not_an_effect`, `test_other_mcp_still_effect`; T`test_check_lookups.py`: `test_doc_mcp_recorded` (su input sintetico: nessun campione `mcp_docs`) |
| 3.6 giri di correzione, nota del task; `reopen plan` | 2, 6, 7, 8 | T`test_scope.py`: `test_reset_plan_drops_task_lookups`; T`test_check_research_gate.py`: `test_round4_new_implementer_keeps_valid_note`, `test_reminder_again_after_plan_reset`, `test_refusal_ignores_problems_before_plan_reset`; T`test_taskcmd.py`: `test_fix_brief_points_to_delivered_note`; T`test_brief.py`: `test_fix_brief_points_to_note`. Il giro `--fix` **non è esercitato con il modello** (la prova reale è passata al primo giro) |
| 3.6 L0 senza task: un avviso per lavoro | 7 | T`test_check_research_gate.py`: `test_l0_warns_once`, `test_docs_exempt_in_l0`, `test_l0_bash_not_gated` |
| 3.6 nomi dei modelli in `rules-base` | — | **Senza prova in B1:** è una regola (B2) |
| 4 i profili; `base` caricata da ogni agente | — | **Senza prova in B1:** B2-B7 |
| 5 regole approvate; il blocco acceso dopo `rules-base` | 3, 7 | Interruttore: T`test_research.py`: `test_enforced`; T`test_check_research_gate.py`: `test_l1_without_note_denied_when_enforced` contro `test_l1_without_note_warned_when_not_enforced`; T`test_taskcmd.py`: `test_review_prepare_enforced_when_rules_base_approved`; prova reale con `approved: prova-b1` solo nella copia del plugin. L'approvazione vera è di **B2** |
| 6 dove sta la nota e in che formato | 3, 6 | T`test_research_cmd.py`: `test_submit_valid_note`, `test_resubmit_replaces`, `test_show_prints_note_and_outcome`; T`test_cli.py`: `test_research_submit_reads_stdin`, `test_research_submit_refused_exit_2`; T`test_research.py`: `test_submit_command_quotes_delimiter`, `test_template_is_parsed_with_problems`; T`test_check_cli_calls.py`: `test_heredoc_research_passes_bash_rules`; B1-V5 (heredoc integro) |
| 6 come gli hook registrano le letture | 2, 4 | T`test_check_lookups.py` (Read, WebFetch, WebSearch, Grep, MCP, `cat` da Bash, `cd`, collegamenti simbolici, comando fallito, sessione principale, sola lettura); T`test_hook_engine.py`: `test_post_lookup_kinds`, `test_lookup_op`; T`test_wrapper.py`: `test_main_session_read_exits_early`, `test_main_session_websearch_exits_early`, `test_subagent_read_reaches_python`, `test_early_exit_list_matches_unnamed_tools_constant`; T`test_manifest.py`: `test_post_tool_use_matcher_has_lookups`; T`test_lookups.py`; campioni `spikes/fixtures/hook-inputs/samples-b1.json` |
| 6 normalizzazione degli URL, libreria e context7 | 3 | T`test_research.py`: `test_url_forms`, `test_check_note_url_normalized`, `test_check_note_context7`, `test_doc_library`; T`test_check_lookups.py`: `test_webfetch_recorded_normalized`, `test_webfetch_redirect_records_only_requested_url`, `test_webfetch_error_code_not_recorded` |
| 6 come `rules-base` arriva agli agenti | — | **Senza prova in B1:** B2 |
| 6 testo dell'avviso e del rifiuto | 7 | T`test_check_research_gate.py`: `test_invalid_note_denied_with_problems`, `test_l1_without_note_warned_when_not_enforced`, `test_reminder_not_consumed_by_other_deny`, `test_failed_edit_does_not_consume_reminder` |
| 6 ordine e dimensione delle fette | — | Questo documento, sezione 2 (nessun test) |
| 6 revisione della spec del nucleo | 10 | Revisione 27 (intestazione e riga 27 della sezione 20); T`test_docs.py` (titoli di 1.2) verde. Le descrizioni sono verificate leggendo il codice del ramo, non da un test |
| 7 test della suite (quattro casi) | 7, 3 | T`test_check_research_gate.py`: `test_l1_without_note_denied_when_enforced`, `test_l0_warns_once`, `test_invalid_note_denied_with_problems`, `test_valid_note_passes`; T`test_research.py` |
| 7 prova reale L1 | 9 | `docs/verifiche/2026-10-27-b1-prova-flusso.md` (riuscita al primo tentativo di ogni passo, 29/10/2026; ripetuta con lo stesso esito dopo le correzioni della revisione finale, secondo tentativo di `passo1` e `passo2`). Limiti dichiarati nel rapporto: il ramo di `passo2` che scrive il piano con `Write` non è esercitato; il `WebFetch` della sessione principale nel passo 1 non è in `lookups` (decisione 5); l'uscita di `prepara` è ricopiata dal controller; `validate --strict` segnala `README_MISSING` e `ICON_MISSING` senza cambiare l'esito; token 46.532 (implementatore) e 27.783 (revisore) |
| 7 eval minimi | — | **Senza prova in B1:** B8 |
| 8 vincoli del nucleo | tutti | T`test_layers.py` (strati); T`test_db.py`: `test_latest_version_is_6`, `test_migration_6_columns`, `test_migration_makes_backup_first`; T`test_check_audit_round.py`: `test_ops_count_is_29`; suite senza rete né `claude` vero |
| 8 lavori iniziati prima di B; deroga per `adopt` | 2, 6, 7 | T`test_phases.py`: `test_create_work_research_flag`; T`test_db.py`: `test_migration_keeps_existing_works_outside`; T`test_start.py`: `test_new_work_has_research_on`; T`test_adopt.py`: `test_adopted_work_has_research_on`; T`test_check_research_gate.py`: `test_legacy_work_never_reminded`; T`test_research_cmd.py`: `test_refused_legacy_work`; T`test_check_lookups.py`: `test_legacy_work_not_recorded`; T`test_taskcmd.py`: `test_legacy_work_brief_without_research`, `test_legacy_review_brief_without_section` |

---

## 9. Rinvii dalle fette chiuse

Cose che B1 lascia alle fette successive, da leggere prima di scrivere il piano di B2 e seguenti. I rilievi minori che non riguardano le fette successive restano al triage finale di B1.

**A B2 (accensione del blocco): chiusi.** I quattro punti che seguono sono stati chiusi da B2, con le prove della sezione 10 (righe «Piano principale, sezione 9»).
- **Lavori in corso all'approvazione di `rules-base`.** I lavori con `research = 1` ancora in corso quando B2 accende l'interruttore non hanno un trattamento a parte: `research_gate` legge l'interruttore a ogni modifica, quindi dalla prima modifica successiva senza nota valida il rifiuto vale in qualunque task in corso, anche dove l'implementatore aveva già ricevuto l'avviso; il messaggio di rifiuto dice come consegnare la nota. Il rapporto di B2 lo dice all'utente.
- **Deroga di `adopt`** (progetto 8): `adopt` scrive `work_items.research = 1`, quindi un lavoro nato prima di B1 e adottato dopo riceve il passo. Il progetto dice che un lavoro iniziato prima di B continua con le sue regole; qui `adopt` è l'eccezione, per il motivo scritto in spec 12.2.
- **Obbligatorio nel task di B2 che crea `rules-base` (rinvio 13).** `research.enforced` oggi conta come approvato anche `approved: no` o `approved: off`. Il task aggiunge `no`, `off`, `n` e `false` a `_YAML_EMPTY` (`bin/tollgate_analysis/research.py`), con i test in `tests/test_research.py`; B2 scrive comunque una data.
- **Obbligatorio nel task di B2 che crea `rules-base` (rinvio 31).** `lookups.rules_enforced(root)` (la funzione unica usata da `research_gate` e `taskcmd`) tratta ogni `OSError` nel leggere `skills/rules-base/SKILL.md` come interruttore spento, senza traccia. Oggi il file non esiste e `FileNotFoundError` è il caso normale: nessun comportamento cambia prima di B2. Dopo B2 un errore diverso (permessi, cartella, I/O) farebbe passare in silenzio le modifiche senza nota. Il task distingue: `FileNotFoundError` vuol dire spento in silenzio; ogni altro `OSError` vuol dire spento con traccia (un `inject` «interruttore illeggibile» nel gate e una riga nel log), senza rifiutare alla cieca. Va provato con la skill vera, e con un test per ciascun ramo.

**A B3-B7 (profili).**
- Gli implementatori e i revisori per area copiano `agents/implementer.md` (strumenti senza MCP) e `agents/task-reviewer.md` (paragrafo sulla nota). Se context7 diventa usabile (autenticazione), si aggiungono le voci `mcp__context7__*` e `mcp__plugin_context7_context7__*` a `tools` e si prova `agent_id` degli strumenti MCP (B1-V3, non determinato): l'esenzione di `effects` e `lookup_rec` sono già pronti, ma `doc_library` legge `libraryId` o `context7CompatibleLibraryID` dalla documentazione pubblica di context7, non provati.
- `Grep` è fuori dal matcher di `PostToolUse` (B1-V6): chi legge un file solo con `Grep` lo riapre con `Read`. Se la latenza lo permette, rimetterlo è una riga di `hooks/hooks.json`.
- L'avviso sul `TOLLGATE_` nel testo della nota sta in `agents/implementer.md` e nel brief del task (`brief._impl_research`): chi copia l'implementatore deve portarlo.
- `research submit` non sa chi lo chiama: un subagente potrebbe consegnare la nota di un altro task `running` dello stesso lavoro (limite di progetto).
- Le letture da Bash sono best effort: nessun glob, nessuna cartella, nessun `cat < f` (`bash.read_targets`). Il rifiuto della nota dice quale file manca.
- **Da B2: ogni agente nuovo che scrive o rivede codice** (`implementer-<area>`, `reviewer-<area>`, `final-<area>`) **porta `skills: [rules-base]`** nel frontmatter, dopo `tools:`, e va aggiunto all'elenco di `test_code_agents_preload_rules_base`: copiare l'implementatore o il revisore generico non basta se si dimentica la riga. Gli agenti che lavorano su spec e piano non la caricano.
- **Da B2: cosa si è perso nell'implementatore.** Il rimando a `rules-base` ha sostituito i punti 1 e 2 di «Informati prima di scrivere» (decisione 11): R-BASE-01 chiede solo i file che il diff modifica, non più quelli che li chiamano, che il progetto (3.4, riga `base`) nominava. Chi scrive `rules-<area>` o l'implementatore per area decide se rimetterli. Gli agenti dicono «la gravità del brief» senza una fonte di gravità nel revisore finale (frase condizionata, ruling D6).
- **Da B2: test nuovi con la radice vera del plugin.** Con il blocco acceso nel repo un test che chiama `taskcmd.review_prepare` o `apply._final_rules` con la radice vera dipende dall'interruttore: servono una radice temporanea esplicita e una `rules-base` finta (come `Lab(plugin_root=…)`, `make_base_root` in `tests/test_check_task_verdict.py`). Restano sulla radice vera, senza dipenderne oggi, `tests/test_taskcmd.py` (righe 476, 491, 660), `tests/test_fixtask.py:180`, `tests/test_criteria_p3a.py:114` e `test_rejected_report_leaves_trace` di `tests/test_check_final_review.py`: da valutare nel triage di B2.
- **Da B2: come si prova il precaricamento di un agente per area.** Lo stream-json di `claude -p` con Claude Code 2.1.314 non ha `agent_transcript_path`: `spikes/b1/flowreg.py precarico` ripiega su un indizio. La prova sta nelle trascrizioni dei subagenti, in `~/.claude/projects/<cartella della prova>/<sessione>/subagents/agent-<agent_id>.jsonl`, dove la skill entra come messaggio `isMeta` prima di ogni turno dell'assistente. Da B3 si cercano lì (o si estende il modo di `flowreg`).
- **Da B2: test di pagina.** Chi copia `RulesBasePageTest` e `test_model_name_rule` ne eredita due fragilità: confrontano frasi quasi alla lettera e riconoscono la regola dalle parole italiane, quindi si rompono alla prima riformulazione. Nei test di una pagina nuova: cercare gli id, e controllare che «N.» coincida con l'id tra parentesi e che la data della riga «Approvata dall'utente il…» sia quella di `approved` (lo fa `test_page_approval_date_matches_skill`: copiarlo).
- **Da B2: ogni regola si giudica su ciò che il revisore vede.** Una `rules-<area>` ha regole verificabili con un sì o un no sul diff, sulla nota o sul report: il revisore del task li vede tutti nel brief (il report in una sezione propria, `brief.review_brief`), il revisore finale e il verificatore solo il diff. Una regola `[blocca]` che si regge solo sul report o sulla nota non è giudicabile dal revisore finale (revisione finale di B2, I-2).
- **Da B2: letture con glob (rinvio 37 di B1).** Un `cat` con glob non registra i file toccati (`bash.read_targets` non espande i glob): nella prova reale di B2 la prima consegna è stata rifiutata per file visti solo con `cat`/`ls` a glob. Da B3: una riga in `agents/implementer.md` o nel brief, «i file che elenchi nella nota aprili con `Read`», toglie il giro di rifiuto.
- **Da B2: test instabile.** `tests.test_cli.CliTest.test_db_restore_interactive_eof_and_ctrl_c` (Ctrl-C su un pty) è instabile sotto carico: se è rosso si ripete da solo prima di darlo per rotto (ruling D16).

**A B8 (eval e chiusura).**
- **Casi di eval con un implementatore L1 o L2** (`s1`, `s2`, `s3`, `s9`): dopo B2, con il blocco acceso, ricevono il rifiuto alla prima modifica senza nota valida e vanno ridisegnati con la nota (letture dichiarate e fonti realmente aperte). In B8 `WebFetch` e `WebSearch` vanno anche tra gli strumenti ammessi dei casi (sezione 3) e la sandbox ha la rete chiusa (spec 14).
- La prova reale di B1 ha un solo lavoro, piccolo, con un solo task: la tenuta su lavori grandi, L2, più task e il giro `--fix` con il modello è da misurare lì.
- **Da B2: il rifiuto dal vivo.** Nella prova reale di B2 l'implementatore ha consegnato la nota valida prima di ogni modifica, quindi il rifiuto del blocco con la regola vera è provato solo dai test (`test_real_rules_base_blocks_l1` e `…_l2`). Un caso di B8 con un implementatore vero che modifica prima della nota lo misura.
- **Da B2: casi già adattati.** `s1`, `s2` (la scorciatoia), `s3` e il `cycle` di `s6` (riusato da `e4`) hanno oggi una lettura dell'implementatore e un `research submit` con «Nessuna fonte esterna» (`research_prep` e l'azione `read` del banco di `tests/test_eval_cases.py`); B8 li ridisegna con la nota vera. `s9` non modifica file e non è cambiato.
- **Da B2: l'evento nuovo.** `research_switch_unreadable` non è contato da `tollgate stats`: gli eval che lo vogliono leggono il registro degli eventi (`tollgate events`).

---

## 10. Prove di B2

Ogni riga della tabella «Copertura» del piano di B2, con il test o l'evidenza che la prova. «T» sta per `tests/`. Un punto senza prova piena lo dice, con il motivo. I numeri dei task sono quelli del piano di B2.

| Punto del progetto | Task | Prova |
|---|---|---|
| 2, obiettivo 3: primo gruppo di profili, `base` | 3, 4, 5 | T`test_rules_base.py`: `test_frontmatter`, `test_real_rules_base_is_approved`, `test_has_title`, `test_first_section_is_prima_di_scrivere`, `test_rule_ids_consecutive`, `test_every_rule_has_a_source`, `test_at_most_150_lines`, `test_licenses_listed`; pagina `docs/profili/base.md` (`test_page_lists_every_rule`); `claude plugin validate --strict` ok |
| 2, obiettivo 4: «Dove informarsi» per `base` | 3 | T`test_rules_base.py`: `test_first_section_is_prima_di_scrivere`; la sezione «Prima di scrivere» della skill ha le regole con la loro fonte. Le pagine ufficiali dei fornitori sono il «Dove informarsi» dei profili di B3-B7: `base` dà solo il metodo |
| 2, anti-obiettivo «frase vuota senza lettura registrata» | B1; 3 | B1: controllo 3.3 (sezione 8). B2: T`test_rules_base.py`: `test_some_rules_block` (R-BASE-01, 03, 06 sono `[blocca]`); T`test_brief.py`: `test_review_note_section_names_base_rules_and_single_report`; prova reale (il revisore cita `R-BASE-06` come conferma). Il giudizio sul diff è del modello revisore: **provato in parte**, nessun caso di nota non pertinente mostrato a un revisore vero |
| 2, anti-obiettivo «regole mai lette da una persona» | 4, 5 | Approvazione dell'utente del 01/11/2026 (pagina `docs/profili/base.md`, «Approvata dall'utente il 2026-11-01»); T`test_rules_base.py`: `test_real_rules_base_is_approved`, `test_page_explains_what_changes`; decisione 13 non scattata (l'utente ha approvato). **Non c'è un test** che confronti la data della pagina con `approved` (sezione 9) |
| 2, anti-obiettivo «fonti inventate» nelle regole | 4 | `docs/profili/verifiche/base-fonti.md`: verificatore di sola lettura sulle copie locali (11 fonti `ok`, 2 `no` la prima volta; la bozza n. 10 corretta, verificata a parte: 1 `no`, 1 `ok`); T`test_rules_base.py`: `test_sources_report_covers_every_rule`. Le regole senza fonte `ok` sono uscite |
| 2, anti-obiettivo «passo troppo pesante» | 3 | R-BASE-09 (`test_rules_base.py`: `test_some_rules_block`); L0 solo avviso, invariato: T`test_check_research_gate.py`: `test_l0_warns_once`, `test_warning_names_rules_base` |
| 3.1: blocco in L1 e L2 | 5, 7 | T`test_check_research_gate.py`: `test_real_rules_base_blocks_l1`, `test_real_rules_base_blocks_l2` (regola vera, radice del repo, uscita 2 e messaggio «nota di ricerca mancante o non valida per il task 1»). Prova reale: nota valida prima di ogni modifica, nessun veto; **il rifiuto non si è visto dal vivo**, lo prova la riga dei test (`docs/verifiche/2026-10-29-b2-prova-flusso.md`) |
| 3.4, riga `base` | 3 | R-BASE-01, 02, 05 in `skills/rules-base/SKILL.md`; rapporto delle fonti, righe di R-BASE-01, 02, 05 (`ok`); T`test_rules_base.py`: `test_every_rule_has_a_source` |
| 3.6: nomi dei modelli in `rules-base` | 3 | R-BASE-04, `[blocca]`: T`test_rules_base.py`: `test_model_name_rule` (riconosce la regola da parole italiane: fragile, sezione 9) |
| 4, riga `base`: caricata da ogni implementatore e revisore, anche generici | 6 | T`test_manifest.py`: `test_code_agents_preload_rules_base`, `test_other_agents_do_not_preload`, `test_implementer_points_to_rules_base`, `test_reviewers_cite_base_rules`; prova reale: la skill è nelle trascrizioni dei due subagenti come messaggio `isMeta` iniziale e nessuno ha aperto `rules-base/SKILL.md` (lo stream-json non ha `agent_transcript_path`: raccolta a mano dal controller, non dallo script). Gli agenti per area sono di B3-B7 |
| 5, punti 1-4: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5 | T`test_rules_base.py` (`test_every_rule_has_a_source`, `test_sources_report_covers_every_rule`, `test_page_lists_every_rule`, `test_page_blocca_matches_skill`); rapporto delle fonti; la skill entra nel plugin con `approved` scritto solo nel commit dell'approvazione |
| 5, «la prima pagina da rivedere è `base`»; blocco spento fino all'approvazione | 5 | L'utente ha rivisto e approvato la pagina il 01/11/2026 (11 regole, la bozza n. 10 rimessa corretta, la bozza n. 11 tolta); prima del commit di `approved` il blocco era spento: T`test_check_research_gate.py`: `test_l1_without_note_warned_when_not_enforced` (radice temporanea senza approvazione); dopo, T`test_real_rules_base_is_approved` |
| 6: come `rules-base` arriva agli agenti | 6 | Decisioni 2 e 3 del piano di B2 (spec 6.3 rev 28); T`test_manifest.py` (riga sopra); T`test_check_research_gate.py`: `test_warning_names_rules_base`; T`test_taskcmd.py`: `test_rules_base_not_required`; `claude plugin validate --strict` accetta `skills: [rules-base]` |
| 8: lavori iniziati prima di B | — | **Invariato** (B1, `work_items.research`): T`test_check_research_gate.py`: `test_legacy_work_never_reminded` (sezione 8) |
| Piano principale, sezione 9: lavori in corso all'approvazione | 4, 8 | Pagina `docs/profili/base.md` («il rifiuto vale anche nei lavori già in corso e nei task già avvisati»; T`test_rules_base.py`: `test_page_explains_what_changes`); spec 12.2 rev 28 |
| Piano principale, sezione 9: rinvio 13 | 1 | T`test_research.py`: `test_enforced_refuses_no_off_n` |
| Piano principale, sezione 9: rinvio 31 | 1 | T`test_lookups.py`: `test_switch_missing_is_silent_off`, `test_switch_unreadable_reports_error`, `test_switch_approved`; T`test_check_research_gate.py`: `test_unreadable_switch_warns_and_logs_once`, `test_unreadable_switch_logged_with_valid_note`, `test_missing_switch_no_unreadable_event`. I primi due usano una radice con una cartella al posto di `SKILL.md`: con la skill vera il file si legge. Il primo prova anche che `_UNREADABLE` precede l'avviso normale e che la seconda modifica non lo ripete |
| Piano principale, sezione 3, B2 → B3-B7: forma di una regola, pagina, rapporto delle fonti | 3, 4, 8 | Sezione 3 di questo documento (nomi reali); `skills/rules-base/SKILL.md`, `docs/profili/base.md`, `docs/profili/verifiche/base-fonti.md` |
| Minori di B1 che il blocco acceso rende reali: task senza modifiche; copia con `git ls-files` | 1, 7 | T`test_brief.py`: `test_review_brief_no_changes_invalid_note_asks_nothing`, `test_review_brief_no_changes_asks_nothing_about_missing_note`; T`test_b1_scripts.py`: `test_flow_copy_is_made_of_tracked_files_only`, `test_flow_copy_fails_on_missing_tracked_file` (di guardia, già verde: `prepara` con `pipefail` si ferma), `test_flow_rules_vere_keeps_real_rules_base`, `test_flow_src_only_in_check_mode`; prova reale (copia del plugin con la skill vera) |
| Revisione della spec del nucleo | 8 | Revisione 28 (intestazione e riga 28 della sezione 20); T`test_docs.py` verde. Le descrizioni sono verificate leggendo il codice del ramo, non da un test |

**Prove oltre la tabella.**

| Cosa | Prova |
|---|---|
| Suite indipendente dall'interruttore del repo (decisione 7) | T`test_eval_cases.py` (`research_prep`: lettura dell'implementatore e `research submit` nei casi `s1`, `s2`, `s3`, `s6`/`e4`; in `e4` il `Write` non è negato); T`test_taskcmd.py`: `test_review_prepare_enforced_when_rules_base_approved` e le radici temporanee; T`test_b1_scripts.py` (riga della `rules-base` solo nella copia). Misura con un file di prova (mai committato): 11 rossi, 2 attesi e 9 corretti |
| Difetto della nota segnalato una volta sola (decisione 8, ruling D3) | T`test_brief.py`: `test_review_note_section_names_base_rules_and_single_report`; T`test_manifest.py`: `test_reviewers_cite_base_rules`. Il rispetto da parte del revisore è del modello |
| `R-BASE-…` note al verdetto, `[blocca]` solo con l'interruttore acceso e il passo attivo nel lavoro (giro 1 del Task 6 e revisione finale) | T`test_check_task_verdict.py`: `BaseRulesTest` (lavoro con il passo), `BaseRulesNoStepTest` e `BaseRulesComponentOffTest` (nessuna `R-BASE-…` blocca), `BaseRulesSwitchOffTest`, `BaseRulesUnreadableTest`; T`test_check_final_review.py`: stesse prove sul verdetto finale |
| Regole giudicabili sul report (revisione finale, I-2) | T`test_brief.py`: `ReviewReportTest`; T`test_taskcmd.py`: `test_report_reaches_review_brief_even_when_done`; T`test_manifest.py`: `test_reviewers_know_where_report_and_note_rules_are_judged`. Il revisore del task giudica sul report nel brief; il revisore finale e il verificatore solo sul diff |
| `rules-base` come comando `/tollgate:rules-base` | T`test_docs.py`: `test_every_skill_documented`; `docs/uso/comandi.md` |
| Prova reale corta | `docs/verifiche/2026-10-29-b2-prova-flusso.md` e `docs/verifiche/evidenze/b2/flusso/`: riuscita al primo tentativo di ogni passo (non composita), circa 0,92 USD stimati sull'abbonamento; token: implementatore 49.015, revisore 30.531. Limiti nel rapporto: rifiuto non visto, un solo lavoro piccolo, `--allowedTools`, altri plugin dell'utente attivi |
