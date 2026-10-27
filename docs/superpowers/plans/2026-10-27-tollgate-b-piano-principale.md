# tollgate B: piano principale

Data: 27 ottobre 2026.
Progetto: `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (approvato dall'utente il 27 ottobre 2026), da qui «il progetto». Spec del nucleo: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 26. Catalogo: `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, di cui B usa sei profili.

Il progetto dice **cosa** fa B e perché; questo documento dice **in che ordine** si costruisce, **cosa consegna** ogni fetta e **quando B è finito**. Il codice e i passi stanno nei piani delle singole fette.

Stato: piano di B1 scritto il 27 ottobre 2026 (`2026-10-27-tollgate-b1-informati-prima.md`, con `-esecuzione.md` e `-brief-sessione.md`). Nessuna fetta eseguita.

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
| **B1 Informati prima** | Il meccanismo del passo «informati prima» (progetto 3), senza regole | `main` con il progetto di B e i quattro file del piano di B1 | Verifiche della sezione 3.5 del progetto; strumenti per informarsi agli implementatori (`WebFetch`, `WebSearch`, context7 se usabile); registrazione delle letture dagli hook; nota di ricerca con il comando `research submit`; controllo in `PreToolUse` (avviso in L0, blocco in L1 e L2, **spento finché `rules-base` non è approvata**: fino ad allora avviso a ogni livello); controllo del revisore del task; lavori iniziati prima di B esclusi; test, prova reale di un lavoro L1, spec del nucleo alla revisione 27 | Criteri della tabella «Copertura» del piano di B1 come test; prova reale L1 riuscita; revisione finale senza `critical` né `important` aperti |
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
| B1 | B2 | **Interruttore del blocco.** `tollgate_analysis.research.RULES_BASE` (`"skills/rules-base/SKILL.md"`) e `research.enforced(skill_text: str \| None) -> bool`: vero solo se il frontmatter ha un campo `approved` non vuoto (oppure, se il Task 1 di B1 trova che `claude plugin validate --strict` rifiuta il campo, un file `skills/rules-base/APPROVED` non vuoto: vale il nome che B1 scrive nel codice). B2 scrive l'approvazione quando l'utente approva la pagina; nessun altro codice cambia. Il componente `[components] research_note` spegne il passo per un progetto (R10) |
| B1 | B2-B7 | **Nota di ricerca.** Formato con le sezioni `## Letto nel progetto`, `## Documentazione`, `## Cosa ho trovato`, `## Nessuna fonte esterna`; fonti nella forma `<URL> — <cosa dice>` o `context7:<libraryId> — <cosa dice>`; comando `research submit <k>` (testo da stdin, heredoc con il delimitatore `'NOTA_DI_RICERCA_FINE'`). Le sezioni «Prima di scrivere» delle regole indicano fonti in questa forma |
| B1 | B2-B8 | **Letture registrate.** Tabella `lookups` (migrazione 6) con `kind` (`read`, `grep`, `bash_read`, `fetch`, `search`, `docs`) e `target` normalizzato; `tollgate_core.lookups.for_task(conn, work, task)`. Gli eval di B8 leggono la nota e le letture dallo stato della corsa |
| B1 | B8 | **Tipi di evento** `research_note` {task, ok, problems} e `research_reminder` {task}: gli eval contano avvisi e note da qui. B8 deve aggiungere `WebFetch` e `WebSearch` agli strumenti ammessi dei casi (`CASE_TOOLS` di `tests/test_eval_cases.py`) e ai permessi di `evals/run.sh`, e la sandbox di `claude plugin eval` ha la rete chiusa (spec 14): i casi di B8 vanno disegnati tenendone conto, con una verifica all'inizio della fetta |
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
