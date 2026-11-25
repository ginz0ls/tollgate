# Task 1: revisione (revisore Fable)

Pacchetto: `review-7822aed..0ae01de.diff` (un commit, `0ae01de`, 30 file, +143 −58). Letto una volta; i controlli fuori dal diff sono elencati in fondo, ciascuno con il rischio che lo motiva. Nessun test rilanciato: le evidenze dell'implementatore bastano (vedi «Test»).

### Aderenza

**Decisione 14, frontmatter**
- ✅ `model: fable` nei 12 agenti che rivedono (`task-reviewer`, `reviewer-{ai,infra,backend,frontend,database}`, `final-reviewer`, `final-database`, `finding-verifier`, `spec-auditor`, `spec-adversary`, `plan-adversary`) e `model: opus` nei 6 implementatori. Verificato su tutti e 18 i file a `0ae01de`: alias, nessun ID completo.
- ✅ Vincolo «degli agenti esistenti cambia solo la riga `model:`»: ogni file di `agents/` ha un solo hunk con una riga tolta e una aggiunta (stat: 18 file × `2 +-`).

**Decisione 14, giro 4**
- ✅ `bin/tollgate_flow/taskcmd.py:22` `MODEL_HINT = "opus"`; `:176-178` il suggerimento è il valore di `[review] models` per quell'implementatore, e solo se `renamed` ripiega su `MODEL_HINT`. Primo avvio e giri 1-3 invariati (prima: `cfg…get(…)` quando non `renamed`; ora lo stesso). Il commento `:174-175` dice la regola nuova.
- ✅ `skills/execute/SKILL.md:34` e `:46` aggiornate; nessun `model: inherit` resta in `bin`, `skills`, `hooks`, `templates`, `docs/uso`, `README.md`, `evals` (unica occorrenza di «inherit»: `docs/uso/comandi.md:190`, che dice che non è ammesso).

**Decisione 14, prove ed eval**
- ✅ `spikes/run-b1-flow.sh:83` `MODEL=opus`; `spikes/b1/run-b1-checks.sh:34` `B1_MODEL:-opus`; `evals/run.sh:47` `MODEL=claude-opus-5-5`; `tests/test_eval_run.py:250`, `tests/test_b1_scripts.py:190`, `:569`, `:753`, `tests/test_brief.py:65-70` allineati.

**Decisione 14, test**
- ✅ `REVIEW_MODEL`, `WRITER_MODEL` in `tests/test_manifest.py` (interfaccia per i Task 2 e 7); `test_agents_frontmatter`, `test_final_agents_frontmatter`, `AUDIT_AGENTS` usano le costanti.
- ✅ Test nuovi presenti e con asserzioni vere: `test_no_agent_on_sonnet`, `test_agent_models_by_role`, `test_no_sonnet_in_skills_and_scripts` (la regex `SONNET_PIN` è quella della decisione, alla lettera), `test_fix_round_4_hints_opus`, `test_fix_round_4_uses_review_models`; `test_sixth_round_name_launch_inherit` → `…_opus`.
- ✅ Nessun test ripropone sonnet (`"tollgate:implementer" = "fable"`).

**Decisioni del controller**
- ⚠️ D5 (`claude plugin validate --strict .` accetta `fable` e `opus`): non rilanciato (nessun `claude` vero per il revisore); vale il «verificato» del controller e l'uscita 0 riportata dall'implementatore.
- ✅ D6: `tests/test_taskcmd.py:142` e `:475` sono `assertNotIn("model:", summary)`; le righe `:252-258` tolte perché ripetute da `test_fix_round_4_uses_review_models`; `test_no_sonnet_in_skills_and_scripts` controlla `model: inherit` in ogni `SKILL.md`.
- ✅ D11: `docs/uso/eval-e-ci.md:42`, nella stessa riga: `p5` e `b8` misurate su sonnet, campagna nuova, `--campagna`, predefinita ancora `b8`.

**Decisione 14, documentazione**
- ✅ `docs/uso/comandi.md:174-192`, sezione «Modelli degli agenti»: ruoli, scelta dell'utente, `[review] models` con alias, account senza il modello, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`.
- ✅ Le frasi sul comportamento di tollgate sono vere sul codice: `[review] models` lo leggono solo `taskcmd.py:176`, `finalreview.py:127`, `audit.py:478`; le righe di lancio stampano ` model: <m>` (`finalreview.py:67`); `review-prepare` non lo legge, quindi «il revisore del task usa il modello della sua definizione» è esatto; `config.py:119` non valida il valore (`_STR_MAP`), come dice la pagina.
- ⚠️ Tre sfumature della stessa sezione vanno oltre la riga dei «Fatti verificati» (Minor 1): non verificabili da qui senza la pagina.

**Vincoli globali**
- ✅ Solo libreria standard; nessun import nuovo in `bin/` (strati intatti); gate, regole, frammenti e pagine approvate non toccati; nessun file nuovo, nessun `__pycache__`; identificatori in inglese, testi in italiano; niente di privato nei testi nuovi.
- ✅ «In più»: solo l'asserzione `set(agents) == reviewers | writers` in `test_agent_models_by_role` (ogni agente ha un ruolo). Utile, non sovra-ingegneria; conseguenza per il Task 7 dichiarata nel report.

**Test (evidenze)**
- ✅ RED credibile (41 fallimenti sui test nuovi e cambiati; l'unico già verde è spiegato). GREEN 413 test. Suite: 4354 test su 3.11 e 3.13, `exit 0`; 4349 della linea di base + 5 test nuovi = 4354. `suite-task-1.log` pulito: nessun avviso, nessun «unclosed».

### Punti di forza

- Cambio chirurgico: 9 righe in `taskcmd.py`, nessun contratto toccato (`ImplBrief.model_hint` e il riepilogo restano come prima).
- `hint or MODEL_HINT` copre anche il valore vuoto, non solo l'assenza della chiave.
- `test_fix_round_4_uses_review_models` asserisce anche il nome `-r4` e l'assenza di `opus` e `inherit`: distingue davvero il comportamento nuovo dal vecchio.
- `test_agent_models_by_role` deriva i revisori da `config.DEFAULTS`, non da un elenco copiato: un agente nuovo senza ruolo fa fallire il test.
- La pagina d'uso dice con onestà il limite (valore non validato) invece di tacerlo, e non ripropone sonnet negli esempi.
- Report preciso: ogni affermazione controllata sul diff è risultata vera.

### Rilievi

#### Critical
Nessuno.

#### Important
Nessuno.

#### Minor

1. **`docs/uso/comandi.md:192`: tre frasi più forti del fatto verificato.** La riga della pagina dei subagenti in `fatti-verificati.md` dice: con `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` «il campo `model` e il parametro della chiamata si ignorano»; l'avviso c'è «nelle sessioni interattive»; il caso descritto è `availableModels` che blocca il modello.
   - (a) «resta il modello di `CLAUDE_CODE_SUBAGENT_MODEL`, o quello della sessione» è una deduzione dall'ordine delle precedenze (dichiarata dall'implementatore). È coerente con quell'ordine, ma non è letta sulla pagina.
   - (b) «con un avviso **solo** nelle sessioni interattive»: il «solo» non è nel fatto.
   - (c) «Se l'account non può usare il modello chiesto (per esempio perché `availableModels` lo esclude)»: generalizza a ogni indisponibilità un comportamento verificato per il solo `availableModels`. È il punto che conta di più per chi non ha Fable sull'account.
   - Perché: è documentazione per l'utente su un comportamento di Claude Code; la decisione 14 chiede «i fatti della pagina».
   - Come correggere: il controller rilegge la pagina e conferma, oppure si riduce al fatto: «…ignora sia la riga `model:` sia il `model` della chiamata, e la scelta qui sopra non vale»; togliere «solo»; «Se `availableModels` esclude il modello chiesto, …».

2. **`docs/uso/comandi.md:176` e `docs/uso/eval-e-ci.md:42`: data «22/11/2026».** Nello stesso file le date sono in forma ISO («approvate dall'utente (2026-11-17)», `comandi.md:172`). Rifinitura: `2026-11-22`.

3. **`tests/test_taskcmd.py:249-253`: `test_models_override_in_summary` è ora un sottoinsieme esatto** delle prime quattro righe di `test_fix_round_4_uses_review_models` (`:505-508`). Imposto dal piano («il primo avvio resta com'è in `:248-251`»), quindi resta; si può togliere la ripetizione dal test nuovo o lasciarla com'è.

4. **`tests/test_manifest.py:23-24`: `SONNET_PIN` non vede `MODEL="sonnet"` con le virgolette** (né `--model=sonnet`). La regex è quella della decisione 14, alla lettera (imposto dal piano), e gli script di oggi non usano quella forma: nessun rischio attuale, solo una guardia meno larga del nome. Eventuale allargamento: `MODEL="?(…)`.

5. **`evals/run.sh:47` con `campaign=b8` predefinita (`:52`):** una corsa su opus senza `--campagna` scrive nel registro di `b8`, che la decisione 14 vuole intatto. È la scelta di D11 (la pagina lo dice e il tetto di 20 USD resta il limite di spesa), quindi non è un difetto del task; lo segnalo perché la protezione è solo una frase di documentazione fino alla campagna nuova (Task 10 / D).

### Controlli fuori dal diff (rischio → controllo)

- Testi residui che fissano ancora sonnet o `inherit` e contraddicono la pagina nuova → `git grep -i "sonnet|haiku|inherit"` a `0ae01de` su `bin`, `skills`, `hooks`, `templates`, `docs/uso`, `README.md`, `evals`, `agents`: restano solo `rules-ai:35` (indirizzo di una `Fonte:`, approvata) e le menzioni volute in `comandi.md` ed `eval-e-ci.md`.
- Frasi di `comandi.md` su dove vale `[review] models` → lettura di `finalreview.py:30-33`, `:67`, `:126-127`, `audit.py:475-484`, `taskcmd.py:174-215`, `config.py:119`: confermate.
- `test_agent_models_by_role` fragile se `readonly_agents` avesse voci senza agente → `config.py:76-82`: 12 voci `tollgate:` più `Explore`, pari ai 12 revisori; 18 agenti in `agents/`.
- Un hook che confronta il `model` della chiamata `Agent` con un valore atteso → nessuno in `bin/tollgate_hooks`, `bin/tollgate_checks`, `hooks`.
- Prenotazione dei costi degli eval tarata sui prezzi di sonnet → `evals/cost.py`: prenota con «?» e somma il `costUsd` vero; nessuna stima per modello.
- Rumore nella suite → `suite-task-1.log` (15 righe) contro `suite-baseline.log`: identici salvo conteggi e `exit 0`.

### Valutazione

**Qualità del task:** Approvato

**Motivo:** Tutti i requisiti della decisione 14 e di D5, D6, D11 sono nel diff e i test nuovi distinguono il comportamento nuovo dal vecchio; restano cinque Minor, di cui il primo (frasi di `comandi.md:192` più forti del fatto verificato) conviene chiuderlo con una rilettura della pagina da parte del controller.
