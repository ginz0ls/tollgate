# tollgate B: piano principale

Data: 27 ottobre 2026.
Progetto: `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (approvato dall'utente il 27 ottobre 2026), da qui «il progetto». Spec del nucleo: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 27 (scritta da B1; B1 è partita dalla 26). Catalogo: `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, di cui B usa sei profili.

Il progetto dice **cosa** fa B e perché; questo documento dice **in che ordine** si costruisce, **cosa consegna** ogni fetta e **quando B è finito**. Il codice e i passi stanno nei piani delle singole fette.

Stato (29 ottobre 2026): **B1 chiusa sul ramo** `b1-informati-prima` (piano `2026-10-27-tollgate-b1-informati-prima.md`, con `-esecuzione.md` e `-brief-sessione.md`); merge su `main` in attesa dell'OK dell'utente. Suite: 3121 test verdi su Python 3.11 e 3.13, anche con `-W error::ResourceWarning`. Prova reale di un lavoro L1 riuscita (`docs/verifiche/2026-10-27-b1-prova-flusso.md`); spec del nucleo alla revisione 27. Le prove punto per punto sono nella sezione 8, i rinvii alle fette successive nella sezione 9. B2 e successive: nessuna eseguita; il piano di B2 si scrive quando B1 è unita su `main` (regola 1).

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
| **B1 Informati prima** | Il meccanismo del passo «informati prima» (progetto 3), senza regole | `main` con il progetto di B e i quattro file del piano di B1 | Verifiche della sezione 3.5 del progetto; strumenti per informarsi agli implementatori (`WebFetch` e `WebSearch`; context7 non usabile dai subagenti, B1-V2); registrazione delle letture dagli hook; nota di ricerca con il comando `research submit`; controllo in `PreToolUse` (avviso in L0, blocco in L1 e L2, **spento finché `rules-base` non è approvata**: fino ad allora avviso a ogni livello); controllo del revisore del task; lavori iniziati prima di B esclusi; test, prova reale di un lavoro L1, spec del nucleo alla revisione 27 | Criteri della tabella «Copertura» del piano di B1 come test; prova reale L1 riuscita; revisione finale senza `critical` né `important` aperti. **Stato:** costruita e chiusa sul ramo, prove nella sezione 8; due scostamenti dal progetto: la deroga di `adopt` (sezione 9) e `Grep` fuori dal matcher di `PostToolUse` (B1-V6) |
| **B2 Regole di base** | `rules-base` approvata e il blocco acceso | B1 | `skills/rules-base/SKILL.md` (sezione «Prima di scrivere», regola sui nomi dei modelli, progetto 3.4 e 3.6) con le fonti; verifica delle fonti da un agente di sola lettura; pagina per l'utente in parole semplici; caricamento di `rules-base` in ogni implementatore e revisore, generici compresi (progetto 4, riga `base`); approvazione registrata, che accende il blocco | Pagina approvata dall'utente; il blocco scatta in L1 e L2 (test e una prova reale corta) |
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
| B1 | B2 | **Interruttore del blocco.** `tollgate_analysis.research.RULES_BASE` (`"skills/rules-base/SKILL.md"`) e `research.enforced(skill_text: str \| None) -> bool`: vero solo se il frontmatter ha un campo `approved` non vuoto. B1-V7 è positivo (`claude plugin validate --strict` accetta il campo): **non esiste** un file `APPROVED`. Non conta come approvazione un valore vuoto, `null`, `~`, `false` o un indicatore di blocco YAML (`\|`, `>`); qualunque altro valore conta, anche `no` o `off` (B2 scrive una data). Lo leggono `research_gate` (`ctx.plugin_root / RULES_BASE`) e `taskcmd` (per il brief del revisore). B2 scrive l'approvazione quando l'utente approva la pagina; nessun altro codice cambia. Il componente `[components] research_note` spegne il passo per un progetto (R10) |
| B1 | B2-B7 | **Nota di ricerca.** Formato con le sezioni `## Letto nel progetto`, `## Documentazione`, `## Cosa ho trovato`, `## Nessuna fonte esterna` (al posto di «Documentazione», non insieme); fonti nella forma `<URL> — <cosa dice>` o `context7:<libraryId> — <cosa dice>` (separatore ` — ` o ` - `); al più 8.000 caratteri. Comando `research submit <k>` (testo da stdin, heredoc con il delimitatore `'NOTA_DI_RICERCA_FINE'`, `research.HEREDOC_END`); `research show <k>` la rilegge. Codice: `tollgate_analysis.research` (`parse_note`, `check_note`, `submit_command`, `Source`: per una fonte context7 `Source.ref` è il solo `libraryId`), `tollgate_flow.research_cmd` (`submit`, `show`, `note_path`: l'unico punto che compone `.tollgate-run/<N>/research-<k>.md`). Le sezioni «Prima di scrivere» delle regole indicano fonti in questa forma |
| B1 | B2-B8 | **Letture registrate.** Tabella `lookups` (migrazione 6) con `kind` (`read`, `grep`, `bash_read`, `fetch`, `search`, `docs`) e `target` normalizzato; `tollgate_core.lookups.for_task(conn, work, task)`, `lookups.observed` (cosa registrare per una lettura), `lookups.owner` (a quale task appartiene) e `lookups.note`. `Grep` non è nel matcher di `PostToolUse` (B1-V6): un file letto solo con `Grep` non conta e va riletto con `Read`; per riaccenderlo basta rimetterlo in `hooks/hooks.json` (e in `LOOKUP_TOOLS` di `adapter.py` è già). Le letture di Bash passano da `bash.read_targets` e contano se sono file esistenti nel worktree (niente glob). Gli eval di B8 leggono la nota e le letture dallo stato della corsa |
| B1 | B8 | **Tipi di evento** `research_note` {task, ok, problems} e `research_reminder` {task} (`task` è `null` per l'avviso di L0): gli eval contano avvisi e note da qui. B8 deve aggiungere `WebFetch` e `WebSearch` agli strumenti ammessi dei casi (`CASE_TOOLS` di `tests/test_eval_cases.py`) e ai permessi di `evals/run.sh`, e la sandbox di `claude plugin eval` ha la rete chiusa (spec 14): i casi di B8 vanno disegnati tenendone conto, con una verifica all'inizio della fetta |
| B1 | B3-B7 | **Strumenti e controllo del revisore.** `agents/implementer.md` ha `tools: Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch`, **senza voci MCP** (B1-V2), e le sezioni «Informati prima di scrivere» (nota, pagine scaricate come dati non fidati); gli implementatori per area li copiano. `agents/task-reviewer.md` controlla la nota se il brief ha la sezione «Nota di ricerca» (`brief.ReviewBrief`: `research`, `research_enforced`, `research_note`, `research_note_path`, `first_diff_file`); i revisori per area copiano il paragrafo. Il rilievo ha `rule` `nota di ricerca` |
| B2 | B3-B7 | **Forma di una regola e approvazione.** `skills/rules-<area>/SKILL.md` con frontmatter `name`, `description`, `version`, `approved`; regole numerate `R-<AREA>-NN`, `[blocca]` dove serve, `Fonte:` per ogni regola; prima sezione «Prima di scrivere». Pagina per l'utente `docs/profili/<area>.md`; rapporto della verifica delle fonti `docs/profili/verifiche/<area>-fonti.md`. Come `rules-base` arriva agli agenti (proposta: `skills:` nel frontmatter di ogni agente che scrive o rivede codice, fuori dal tetto di 3 come le skill comuni) |
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
- ogni fetta è unita su `main` con la revisione finale chiusa e la suite verde su Python 3.11 e 3.13, anche con `-W error::ResourceWarning`;
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
| 7 prova reale L1 | 9 | `docs/verifiche/2026-10-27-b1-prova-flusso.md` (riuscita al primo tentativo di ogni passo, 29/10/2026) |
| 7 eval minimi | — | **Senza prova in B1:** B8 |
| 8 vincoli del nucleo | tutti | T`test_layers.py` (strati); T`test_db.py`: `test_latest_version_is_6`, `test_migration_6_columns`, `test_migration_makes_backup_first`; T`test_check_audit_round.py`: `test_ops_count_is_29`; suite senza rete né `claude` vero |
| 8 lavori iniziati prima di B; deroga per `adopt` | 2, 6, 7 | T`test_phases.py`: `test_create_work_research_flag`; T`test_db.py`: `test_migration_keeps_existing_works_outside`; T`test_start.py`: `test_new_work_has_research_on`; T`test_adopt.py`: `test_adopted_work_has_research_on`; T`test_check_research_gate.py`: `test_legacy_work_never_reminded`; T`test_research_cmd.py`: `test_refused_legacy_work`; T`test_check_lookups.py`: `test_legacy_work_not_recorded`; T`test_taskcmd.py`: `test_legacy_work_brief_without_research`, `test_legacy_review_brief_without_section` |

---

## 9. Rinvii dalle fette chiuse

Cose che B1 lascia alle fette successive, da leggere prima di scrivere il piano di B2 e seguenti. I rilievi minori che non riguardano le fette successive restano al triage finale di B1.

**A B2 (accensione del blocco).**
- **Lavori in corso all'approvazione di `rules-base`.** I lavori con `research = 1` ancora in corso quando B2 accende l'interruttore non hanno un trattamento a parte: il rifiuto vale dalla prima modifica senza nota valida (un task con l'avviso già ricevuto e senza nota è negato alla modifica successiva). Il rapporto di B2 lo dice all'utente.
- **Deroga di `adopt`** (progetto 8): `adopt` scrive `work_items.research = 1`, quindi un lavoro nato prima di B1 e adottato dopo riceve il passo. Il progetto dice che un lavoro iniziato prima di B continua con le sue regole; qui `adopt` è l'eccezione, per il motivo scritto in spec 12.2.
- Valori di `approved`: vale qualunque valore non vuoto (anche `no` o `off`); B2 scrive una data.
- `research_gate._rules_enforced` tratta ogni `OSError` nel leggere `skills/rules-base/SKILL.md` come interruttore spento, senza traccia: se B2 sposta o rinomina la skill, il blocco si spegne in silenzio. Da distinguere `FileNotFoundError`, e da provare con la skill vera.

**A B3-B7 (profili).**
- Gli implementatori e i revisori per area copiano `agents/implementer.md` (strumenti senza MCP) e `agents/task-reviewer.md` (paragrafo sulla nota). Se context7 diventa usabile (autenticazione), si aggiungono le voci `mcp__context7__*` e `mcp__plugin_context7_context7__*` a `tools` e si prova `agent_id` degli strumenti MCP (B1-V3, non determinato): l'esenzione di `effects` e `lookup_rec` sono già pronti, ma `doc_library` legge `libraryId` o `context7CompatibleLibraryID` dalla documentazione pubblica di context7, non provati.
- `Grep` è fuori dal matcher di `PostToolUse` (B1-V6): chi legge un file solo con `Grep` lo riapre con `Read`. Se la latenza lo permette, rimetterlo è una riga di `hooks/hooks.json`.
- Le letture da Bash sono best effort: nessun glob, nessuna cartella, nessun `cat < f` (`bash.read_targets`). Il rifiuto della nota dice quale file manca.

**A B8 (eval e chiusura).**
- **Casi di eval con un implementatore L1 o L2** (`s1`, `s2`, `s3`, `s9`): dopo B2, con il blocco acceso, ricevono il rifiuto alla prima modifica senza nota valida e vanno ridisegnati con la nota (letture dichiarate e fonti realmente aperte). In B8 `WebFetch` e `WebSearch` vanno anche tra gli strumenti ammessi dei casi (sezione 3) e la sandbox ha la rete chiusa (spec 14).
- La prova reale di B1 ha un solo lavoro, piccolo, con un solo task: la tenuta su lavori grandi, L2, più task e il giro `--fix` con il modello è da misurare lì.
