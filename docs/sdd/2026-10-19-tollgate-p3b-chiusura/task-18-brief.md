### Task 18: Criteri, revisione 23 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p3b.py`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 23), `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «Prove dei criteri di P3b» nel piano principale; i contratti reali P3b → P3c e P4, compreso il blocco 18.1.

- [ ] **Step 1: Test dal programma vero** (`test_criteria_p3b.py`, `FlowLab` più `hooks/run` reale come in `test_criteria_p3a.py`):
  - `test_finish_to_pr_end_to_end` (criteri 9, 12, 40, 41): `UserPromptExpansion` di `/tollgate:finish` attraverso `hooks/run` → atto; `finish check` → 0; `review prepare`; `SubagentStart`/`SubagentStop` del revisore finale con un verdetto con un rilievo senza `rule`; `review prepare` → verificatore; `SubagentStop` del verificatore; `review prepare` → «finish open-pr»; `finish open-pr` (segnale scritto dal `PreToolUse Bash` vero) → PR nel finto `gh`, fase `pr_open`, blocco JSON con `verdict.outcome == "ok"`;
  - `test_needs_fix_then_from_findings_consumes_cycle` (criteri 26 e 37);
  - `test_sync_after_default_advanced` (criterio 16);
  - `test_adopt_after_db_lost` (criterio 17).
- [ ] **Step 2: Matrice.** Nel piano principale la tabella «Prove dei criteri di P3b» (formato `file::Classe.metodo`) per 1 (adozione eseguita), 9, 12, 16, 17 (`adopt`), 18 (`final_review`, `definition_of_done`), 26, 28 (interruzione dopo `finish check`), 31 (`finish check` rosso), 37 (`--from-findings`), 38 (`final_specialist`), 40 (verificatore), 41, 42 (DoD), con «Resta a» per P3c (41 seconda frase, decisione 26; 37 `plan_sha` di `approve plan`) e P4 (42 nel gate, 18 `definition_of_done` nel gate). Un criterio senza test è un buco: il test si aggiunge nel modulo che possiede il codice.
- [ ] **Step 3: Revisione 23 della spec**: le decisioni 1-26 nelle sezioni 3.1 (sottocomandi nuovi, segnale con `argv` consumato), 6.4 (`finish check`, revisione, `open-pr`), 6.5 (`sync`, merge e chiusura), 8.4 (atti applicabili, `approve rounds` sui giri di correzione, `abandon` senza lavoro), 8.6 (`[blocca]` con `blocking_rules`, nomi dei profili), 8.7 (DoD dei rilievi e `unverified-tests`), 10 (stadi del ciclo, codice per ciclo, tetti), 11.4 (`blocking_rules`), 12.2 (migrazione 4), 12.4 (`adopt`, `cleanup`), 15 (criterio 41 diviso), 16 (esiti G1-G5 del Task 1 e della prova reale), 18.1 (contratto di `prblock`, marcatore `<!-- tollgate-verdict` per P4), 18.4 (eventi nuovi), 20 (riga 23).
- [ ] **Step 4: Piano principale**: la riga P3c della sequenza riceve la seconda frase del criterio 41 (decisione 26); «Stato» (P3b chiuso sul ramo, merge in attesa dell'OK dell'utente, numero di test); sezione 3 con i moduli reali e i contratti P3b → P3c/P4 (`prblock.FIELDS/parse`, `reviews`, `intents`, `violations`, `finishcheck.check` come interfaccia che P4 sostituisce, `GATE_MARKER`), i vincoli per P3c e P4 emersi qui e i rinviati della revisione finale.
- [ ] **Step 5: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi, nessun «unclosed database».

```bash
git add tests/test_criteria_p3b.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "tollgate P3b: prove dei criteri, spec rev 23, piano principale"
```

---

## Copertura: criteri, vincoli e rinviati → task

| Voce | Task |
|---|---|
| Criterio 1 (adozione proposta da `start` ed eseguita) | 12, 18 |
| Criterio 9 Revisori | 3, 8, 9, 10, 18 |
| Criterio 12 PR | 9, 18 |
| Criterio 16 Sync | 7, 9, 10, 11, 18 |
| Criterio 17 Adozione (`adopt`) | 12, 18 |
| Criterio 18 Componenti (`final_review`, `definition_of_done`) | 9 |
| Criterio 26 Da correggere | 3, 8, 14, 18 |
| Criterio 28 Ripresa (interruzione dopo `finish check`) | 6, 7 |
| Criterio 31 `finish check` rosso | 6 |
| Criterio 37 `--from-findings` | 14, 18 |
| Criterio 38 `final_specialist` in L2 | 7, 8 |
| Criterio 40 Revisione (verificatore) | 3, 8, 18 |
| Criterio 41 DoD (prima frase; seconda a P3c) | 6, 9, 18 |
| Criterio 42 Must-have nella DoD (gate a P4) | 6 |
| Blocco JSON 18.1 per P4 | 9 (decisione 11), 18 |
| Vincoli (1)-(9) di P3a per P3b | vedi «Rilievi ripresi qui» |
| m9, m11, m12, m13 | 5; 2; 10 e 15; 2 |
| Righe 55, 56, 74, 102, 108, 133 | 12 e 13; 9; 12; 2; 5; 15 |
| Messaggio breve di `cli_calls` | 2 |
| `dod._findings`, `abandon` della sessione, commit estranei del `sync` | 3; 2; 11 |
