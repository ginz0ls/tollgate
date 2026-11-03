# Ri-revisione 2 del giro di correzione finale (b3-profilo-ai, dd0132d..7283c73)

Letti: regole, cautele, ri-revisione 1, report ("Fix round 2"), diff. Controllo mio, in sola lettura: script Python `-I -B` che scorre tutti i `.jsonl` di `docs/verifiche/evidenze/b3/` (JSON valido, stringhe di testo e `tool_result` oltre 5.000 caratteri, `tool_use_result` oltre 5.000 con origine). Nessuna suite lanciata.

### Verdetti sui rilievi

- **Nessun testo integrale di skill di terzi nelle evidenze pubbliche di b3:** INDIRIZZATO. Lo script non trova righe non JSON. Le stringhe oltre 5.000 caratteri sono solo queste:
  - `passo1/tentativo-1/claude.jsonl:139` (14.023): `tool_result` di un `Bash` `cat tests/test_smoke.py ai/__init__.py config.toml services/notify.py; ... cat /tmp/tollgate-b1/plugin/skills/rules-ai/SKILL.md`: file del progetto di prova e skill di tollgate. Unico titolo `#` nel testo: `# Regole ai (versione 1)`. CONFERMATO: la menzione di `claude-api` (offset 11.666) è la frase di `rules-ai` "Per il codice che usa l'SDK di Anthropic c'è anche la skill `claude-api`", non il testo della skill. Il `tool_use_result` di :139 (14.791) è lo stesso output.
  - `:152` (5.078, Grep) e `:160` (8.329, Read di `bin/tollgate_analysis/plan.py`), `:199` (8.644, `tool_use_result`): codice di tollgate.
  - `passo2/tentativo-1/claude.jsonl:33` (6.679): `Base directory for this skill: /tmp/tollgate-b1/plugin/skills/execute`, skill di tollgate (derivata da superpowers, ma è la `execute` di tollgate).
  - `grep -c "Base directory for this skill"`: passo 1 = 0 occorrenze, passo 2 = 1 (quella di tollgate). Le righe `:67` e `:96` del passo 1 sono ora `[skill di terzi tolta dalle evidenze: writing-plans, 10318 caratteri]` e `[... claude-api, 108300 caratteri]`, JSON valido.
- **I titoli delle skill di tollgate restano:** INDIRIZZATO. `# Regole ai (versione 1)` presente in :139; `rules-base` non è oltre il tetto e non è stata toccata (la correzione riscrive solo due righe, `:67` e `:96`).
- **`registra` lo fa in automatico, con test:** INDIRIZZATO. `togli_pagine` (`spikes/b1/flowreg.py`) scorre i blocchi `text` con `external_skill`; `registra` lancia già lo stesso comando. Test: `test_flowreg_togli_pagine_replaces_external_skills_but_keeps_tollgate_ones` (claude-api sostituita, rules-ai di tollgate e skill piccola tenute, due passate = idempotente) e `test_flow_registra_strips_external_skills_from_the_streams` (passa per `registra` via il banco finto, nessuna esecuzione di `run-b1-flow.sh` fuori dai test). Il report mostra RED (`:67` e `:96`) e GREEN, `tests.test_b1_scripts` 61 OK su entrambi gli interpreti.
- **Il test sulle evidenze versionate fallirebbe con una skill esterna oltre il tetto:** INDIRIZZATO. `test_committed_evidence_has_no_long_web_results` ora aggiunge `found` per ogni blocco `text` con `external_skill(...)` se il percorso contiene `evidenze/b3/`; il RED sulle righe :67 e :96 è mostrato nel report.
- **Il rapporto lo dice:** INDIRIZZATO. `docs/verifiche/2026-11-01-b3-prova-flusso.md` (anonimizzazione): riga riscritta con le due skill tolte, quelle di tollgate e i titoli `# Regole … (versione 1)` che restano, `registra` in automatico, test su `b3/`, B1 e B2 non toccate.

### Danni nuovi nel diff della correzione

Nessuno Critical/Important. Minor:
- **Minor. `spikes/b1/flowreg.py` (`external_skill`):** "di tollgate" è deciso da `"tollgate" in path.lower()` sul percorso. Una skill di terzi installata sotto un percorso che contiene "tollgate" (per esempio `.claude/skills/` del progetto di prova in `/tmp/tollgate-b1/...`) non verrebbe tolta, e anche il test non la segnalerebbe. Nella prova attuale non succede (lo script sopra non trova nulla); da tenere a mente per le prove future. Un test più stretto sarebbe `.../plugin/skills/` o l'elenco dei nomi delle skill di tollgate.
- **Minor.** Il controllo copre solo i blocchi `text` che iniziano con il prefisso `Base directory for this skill:`; altre forme di iniezione del testo di una skill (per esempio il `Skill` come `tool_result`) non sono viste. Non ce ne sono nelle evidenze di b3 (lo script lo conferma).
- **Minor.** B1, B2 e gh-p4 contengono ancora testo di skill di terzi (non toccati per scelta): coerente con il rilievo, limitato a b3.

### Osservazioni fuori ambito

- La storia git conserva ancora le pagine di WebFetch in `f8f5331` e il testo integrale di `claude-api`/`writing-plans` nei commit precedenti a `7283c73`: la scelta di riscrivere la storia prima della prima spinta resta dell'utente (già segnalata).

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
