# Revisione Task 6 (6464a1d, intervallo aeb48b4..6464a1d)

### Aderenza
- ✅ Frontmatter: `name`, `description` (contiene `backend`), `skills: [rules-base, rules-backend]` in entrambi; `tools` del revisore `Read, Grep, Glob, Bash, WebFetch` (agents/reviewer-backend.md:4). Attribuzione MIT presente. Il resto è identico agli `-infra` (diff solo su nome, description, skills, sezione d'area): nessuna divergenza non dichiarata.
- ✅ Vincoli di testo (D13): una sola frase con «sul tuo report» (implementer-backend.md:113) che nomina 01, 02, 05, 12, cioè esattamente le `Si giudica su: report` di rules-backend (SKILL.md:16, 20, 34, 62); revisore: una frase «si giudicano sul report» e una «si giudicano sul diff» (reviewer-backend.md:54), con 8 id sul diff; nessun programma nudo (si usa `<programma>`). `test_manifest` e `test_wrapper` rilanciati: 92 OK.
- ✅ Sezione d'area: `--local` per KV e R2; D1 locale senza `--remote`/`--preview`; non coperti e non lanciati (altri gruppi di Wrangler, `wrangler dev` remoto, client remoti, build Docker con push); niente server su porta; `WebFetch` solo su URL citati, dati non fidati; nessun rilievo `R-BACKEND-…` in un task senza modifiche.
- ✅ Veri rispetto a `bash.py`: `FLAG_EFFECTS` unless_local per KV e R2 (bash.py:1012-1021), with_remote per D1 execute/migrations apply (:1022-1023), `ACCOUNT_GROUPS` (:1006), `d1 create|delete` in `_DEFAULT_EFFECTS` (:1002); `supabase` fermato (:1249).
- ✅ `implementer-infra.md`: cambia solo la frase dei comandi non coperti; nomina build Docker con push e altri gruppi di Wrangler, non più KV/D1/R2.
- ✅ `reviewer-backend` in `READONLY_TYPES` (hooks/run:56) e in `readonly_agents` (config.py:77); `implementer-backend` no. Il test di coerenza è verde.
- ✅ final-reviewer e finding-verifier nominano le `R-BACKEND-…`; `test_final_reviewers_leave_report_rules_of_areas` copre `backend` tramite `AREAS`.
- ✅ Guardie di smistamento (test_profiles.py: `vertical_for` per `api/vercel.json`, `server/Dockerfile` → infra, `server/ai/x.py` → ai; `wrangler.jsonc` + `edge/index.ts` → generico con `split_candidate`) e di verdetto: corrette e verdi. Il test generico usa `edge/**` per backend, scostamento dichiarato e sensato.
- ⚠️ Il RED degli elenchi è dichiarato ottenuto ripristinando `hooks/run` e `config.py` dopo averli scritti nello stesso passo: non verificabile dal diff, ma il test è presente e verde.

### Punti di forza
Derivazione fedele dai modelli, deriva tenuta dai test; guardie scritte come richiesto; test `test_real_infra_agent_names_uncovered_commands` mirato; report onesto sugli scostamenti.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. agents/implementer-backend.md:115 — «Quello che non copre non lo lanci comunque: … i client dei database remoti (per esempio `psql` verso un host in linea)». `psql` è in `_DEFAULT_EFFECTS` (bash.py:984), quindi tollgate lo ferma di default; è non coperto solo se il progetto lo mette in `allow`. Il piano diceva «quando il progetto lo ha in `allow`», qui la condizione è caduta. Nessun danno (il modello non lo lancia in ogni caso), ma l'affermazione è imprecisa. Correzione: aggiungere «quando il progetto li ha in `allow`» o togliere l'esempio `psql`.
2. agents/implementer-backend.md:115 — «i gruppi che agiscono sull'account (`kv namespace`, `r2 bucket`…)»: le letture (`list`, `get`, `info`) non sono ferme (decisione 6). Frase leggibile come assoluta; basta «salvo le letture».
3. tests/test_manifest.py (test infra): `assertIn("push", …)` è debole (la parola compare altrove); `docker build` + `gruppi di Wrangler` già bastano.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** i due agenti sono derivati fedelmente, i vincoli di testo e gli elenchi di sola lettura sono a posto, le affermazioni su Wrangler corrispondono al codice tranne un'imprecisione minore su `psql`.
