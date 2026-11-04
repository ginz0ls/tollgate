# Brief per la sessione che esegue B3-bis

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B3-bis senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-04-tollgate-b3bis-sentinella-modelli.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-04-tollgate-b3bis-esecuzione.md`: ramo `b3bis-sentinella-modelli`, worktree `.claude/worktrees/b3bis`, sessione avviata dalla radice del repo.

Il lavoro è finito quando:
- tutti gli 8 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la prova vera del Task 7 è riuscita, oppure il rapporto dice con chiarezza perché no;
- le cartelle vecchie di `/tmp` sono cancellate e una corsa di `tests/run` non ne lascia di nuove;
- `test_real_evidence_has_no_third_party_text` è verde sulle evidenze ripulite;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente è consegnato, in parole semplici, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-04-tollgate-b3bis-esecuzione.md`: le istruzioni.
2. Il piano B3-bis: per intero «Fatti verificati», «Decisioni di questo piano» (13 decisioni), «Review Focus» e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, **sezioni 9 e 10**: sono l'autorità.
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3 e 9 (blocco «A B3-bis»).
5. La spec del nucleo rev 29, sezioni 3, 3.1, 3.2, 6.1, 11.4, 16, 18.4.
6. `skills/rules-ai/SKILL.md` (R-AI-01, R-AI-03, R-AI-04, R-AI-08: famiglia e stabilità per fornitore) e `templates/profiles/ai.toml`.
7. `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/`: `README.md`, `progress.md` (forma delle `Ruling:`), `final-review.md` (lezioni, in particolare I-1 sul testo di terzi nelle evidenze), `cautele.md`, le regole per implementatori e revisori.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B3 e del 03/11/2026 su `/tmp` e sulle evidenze), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **La sentinella gira sul computer dell'utente all'avvio di un lavoro**, con la chiave API già nell'ambiente. Niente segreti su GitHub, niente job programmati, gli hook restano senza rete (progetto 9).
- **Fornitori:** Anthropic e Gemini; OpenAI e OpenRouter perché le loro pagine danno un elenco. **Avvisa** se c'è un modello stabile più nuovo della stessa famiglia o se uno in uso sta per essere ritirato; non blocca nulla.
- **Ciò che l'elenco non dà si salta, e si dice** (progetto 10): niente lettura di pagine web dei fornitori da parte della sentinella.
- **Una prova vera, una volta**, con le chiavi già nell'ambiente (progetto 10).
- **Pulizia di `/tmp`** approvata (progetto 10), con la regola stretta della decisione 10 e dell'eccezione 2 delle istruzioni.
- **Il repo `ginz0ls/tollgate` è pubblico:** nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né nome dell'host, niente chiavi, niente testo intero di pagine o skill di terzi.

## Punti delicati del piano

- **La chiave non esce mai da tollgate** (Global Constraints, decisione 5, Review Focus 1). La variabile dedicata `TOLLGATE_MODELS_ANTHROPIC_KEY` esiste solo perché `ANTHROPIC_API_KEY` nell'ambiente fa usare a Claude Code la chiave al posto dell'abbonamento (fatturazione a consumo): non protegge la chiave, che resta leggibile da qualunque comando della sessione, e i documenti lo dicono.
- **La rete ha una scadenza unica** (`DEADLINE_S = 20`) e i test non la raggiungono mai: `tests/helpers.no_network()` toglie le variabili delle chiavi e blocca i socket; `fetch` e `PLUGIN_ROOT` si risolvono al momento della chiamata, così i `mock.patch` funzionano.
- **Host delle API fuori da `bin/`**: stanno in `templates/models.toml`, così `test_real_markers_not_in_tollgate_bin` resta com'è e i progetti non ricevono gli host in `.github/tollgate/`.
- **`models_check.check` non solleva mai** e `start` non cambia esito per colpa sua; gira solo per un lavoro nuovo.
- **Nessun nome nuovo con `sentinel`**: è già del gate (workflow, componente, evento).
- **I test non fanno rete**, nemmeno su `127.0.0.1`: il client si prova con un `opener` finto.
- **Le evidenze si ripuliscono con un commit nuovo**; la storia non si riscrive, e l'utente lo sa.

## Stato al momento di questo brief

- `main` contiene il nucleo completo, B1, B2, B3 (unita il 03/11/2026 in un solo commit `72ed64c`, registro in `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/`), il brief di scrittura di B3-bis, le sezioni 9 e 10 del progetto di B e i tre file di questo piano. La suite su `main` ha 3394 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- `skills/rules-base/SKILL.md` e `skills/rules-ai/SKILL.md` sono approvate; il profilo `ai` si propone con `init`. Non esistono `[models]` in `config.py`, `templates/models.toml`, `bin/tollgate_analysis/models.py`, `bin/tollgate_flow/modelsfetch.py`, `bin/tollgate_flow/models_check.py`.
- In `/tmp` ci sono circa 22.500 cartelle `tollgate*` lasciate dai test (circa 150 MB).
- Sulla macchina: Claude Code 2.1.316 o successivo, `gh` 2.46.0, Superpowers 7.0.0, agent-skills 0.6.9. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I commit del piano di B3-bis su `main` non sono ancora stati inviati a GitHub: vanno con il primo push dopo il merge.

## Quanto costa

Nessun `claude -p` e nessun eval: B3-bis consuma solo l'abbonamento per i subagenti (implementatori e revisori sonnet, revisione finale opus), nessuna spesa in denaro. La prova vera fa una chiamata di elenco dei modelli per fornitore con le chiavi dell'utente: non usa modelli e non produce token (le pagine dei fornitori non dicono che sia gratuita).
