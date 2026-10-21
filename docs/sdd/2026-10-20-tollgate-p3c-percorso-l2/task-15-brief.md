### Task 15: Criteri, revisione 24 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p3c.py` (la classe `LaterSliceTest` c'è già dal Task 9)
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 24), `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «Prove dei criteri di P3c» nel piano principale; i contratti reali di P3c verso P4 e P5.

- [ ] **Step 1: Test dal programma vero** (`test_criteria_p3c.py`, `FlowLab` più `hooks/run` reale come in `test_criteria_p3b.py`; i subagenti non si lanciano, i loro eventi li scrive il test):
  - `test_l2_spec_to_execution_end_to_end` (criteri 24, 37, 41): `start` L2; Write di un piano in `spec_audit` → `deny`; spec senza `## Cosa non fare` committata; `audit prepare`; `SubagentStop` dell'avversario con zero rilievi → `major` meccanico, giro non pulito; `UserPromptExpansion` di `/tollgate:approve spec 1` e `act apply` → rifiuto; spec corretta, nuovo giro pulito, `approve spec 1` → `spec-approval.md`, fase `plan`; Edit sulla spec → `deny`; piano, giro del piano non pulito, piano corretto, giro pulito → `approval`; `/tollgate:approve plan` → `plan_sha` = blob del piano corretto, fase `execution`;
  - `test_cap_and_suspension_in_pr_block` (criterio 24: quarto giro non pulito → `needs_you`; `resolve` → «avversariale sospeso»; fino a `open-pr` → blocco 18.1 con `spec_audit.adversarial == "suspended"`);
  - `test_three_slices_lens_audit_and_component_off` (criteri 24 e 35: tre fette, `approve spec 3` rifiutato finché l'audit a lenti è aperto; con `spec_audit = false` accettato e `lens: off`);
  - `test_reopen_spec_from_execution` (criterio 37).
- [ ] **Step 2: Matrice.** Nel piano principale la tabella «Prove dei criteri di P3c» (formato `file::Classe.metodo`) per 18 (`spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch`), 24, 35 (parte locale), 37 (`plan_sha` di `approve plan`, `reopen`), 41 (seconda frase), con «Resta a» per P4 (35 nel gate: `attenzione` rosso; report e approvazioni L2 ricalcolati nel gate con `approvals.check_l2`). Un criterio senza test è un buco: il test si aggiunge nel modulo che possiede il codice.
- [ ] **Step 3: Revisione 24 della spec**: le decisioni 1-27 nelle sezioni 0 (`superseded`), 3 (agenti, skill `spec-audit` e `reopen`), 3.1 (`audit prepare|decline`, `start --spec`, `audit` del coordinatore), 5 (proposta delle issue delle fette in `approve spec`, livello L2 con `--spec`), 6.1, 6.2 (giri, codice, lettura a HEAD, punti di vista meccanici, conferma e rifiuto del costo, pitch meccanico, passaggio `plan → approval` della CLI), 8.4 (atti applicabili `approve spec`, `approve plan`, `reopen`, sospensioni da `resolve`), 7.4 e 8.3 (file di `reviews/<N>/` esenti dallo scope dei commit, decisione 26), 8.7 (voce `approvals` con `check_l2`), 12.2 (migrazione 5), 12.3 (cause `approve_spec`, `audit_clean`, `approve_plan`; `reopen` toglie la registrazione), 12.4 (`adopt` delle fette successive), 15 (criterio 41 intero a P3c), 16 (esiti del Task 1 e della prova reale), 18.1 (`spec_reviews_dir` di una fetta successiva), 18.3 (riga JSON dei giri con `code` e `plan_sha`, `render_*`), 18.4 (`plan_reset`, cause nuove), 20 (riga 24).
- [ ] **Step 4: Piano principale**: «Stato» (P3c chiuso sul ramo, merge in attesa dell'OK dell'utente, numero di test); sezione 2 (P3c); sezione 3 con i moduli reali (`audits`, `audit`, `l2acts`, `auditrules`, `specdoc`, `audit_round`), i contratti P3c → P4 (`approvals.check_l2`, `locate_spec_approval`, `parse_report_header`, prefissi dei tetti e sospensioni nel blocco 18.1), i vincoli per P4 emersi qui e i rinviati della revisione finale.
- [ ] **Step 5: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi, nessun «unclosed database».

```bash
git add tests/test_criteria_p3c.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "tollgate P3c: prove dei criteri, spec rev 24, piano principale"
```

---

## Copertura: criteri, vincoli e rinviati → task

| Voce | Task |
|---|---|
| Criterio 18 Componenti (`spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch`) | 5, 6, 7, 15 |
| Criterio 24 Audit della spec (sei punti) | 3 (contatore), 6 (tetto), 7 (approvazione, fette, spec cambiata, blocco), 9 (`--spec`), 15 |
| Criterio 35 Componenti spenti (parte locale; gate a P4) | 7, 15 |
| Criterio 37 Flusso dopo l'approvazione (`plan_sha` di `approve plan`, `reopen spec`) | 7, 8, 15 |
| Criterio 41, seconda frase (spec senza `## Cosa non fare` → rilievo dell'avversario) | 6, 15 |
| Parti «Resta a P3c» della matrice (18: chiavi L2; 37: `plan_sha`; 41: seconda frase) | come sopra |
| Vincoli per P3c (1)-(6) del piano principale | vedi «Rilievi ripresi qui» |
| Vincoli per P3b e P3c (1) segnale, (2) programma | Global Constraints, 5, 13 |
| Rinviato della riga 83 (recinti del piano) | 2 |
| P1: `from_approved_spec` senza `spec_path` | 4 |
| Triage P3b, righe 5, 21-25, 30-32, 38-40 | 11 (30 e 31 nei Task 2 e 9) |
| Triage P3b, righe 34, 36, 49-51, 55, 60, 62, 67, 71-73, 82 | 12 |
| Triage P3b, righe 77-79 | 13 |
| Sezioni 6.2, 8.4 (`approve spec`, `approve plan`, `reopen`), 18.3 della spec | 2-10 |
| Review Focus 1-6 | 8, 8, 6 e 7, 6 e 7, 9, 7 |
| Decisioni 26-27 (esenzione di `reviews/<N>/`, fasi e blocchi) | 4, 6, 7 |
