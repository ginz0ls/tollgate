### Task 20: Prove dei criteri dal wrapper, revisione 21 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p2.py`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21: decisioni 1, 6, 7, 13, 15, 22 di questo piano)
- Modify: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (stato, sezione 3 con i nomi reali di P2, vincoli per P3)

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «criteri della colonna P2 → test» nel piano principale; i contratti reali di P2 per P3 e P4.

- [ ] **Step 1: Test dal wrapper vero**

`tests/test_criteria_p2.py` fa passare alcuni criteri da `hooks/run` e `bin/tollgate` veri, come li lancia Claude Code (input JSON su stdin):

```python
import json
import subprocess
import unittest

from tests.hookkit import SESSION, Lab, sample
from tests.helpers import ROOT

RUN = ROOT / "hooks" / "run"


def run(lab, event, payload):
    return subprocess.run([str(RUN), event], input=json.dumps(payload), capture_output=True,
                          text=True, env=lab.ts.env(), timeout=60)


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def test_push_denied_in_bound_session(self):              # criterio 7
        r = run(self.lab, "PreToolUse", sample(
            "PreToolUse-Bash", session_id=SESSION, cwd=str(self.lab.wt),
            tool_input={"command": "git push origin tg/7-demo"}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("open-pr", r.stderr)

    def test_session_start_injects_state(self):              # criterio 19
        r = run(self.lab, "SessionStart", sample("SessionStart-none", session_id=SESSION,
                                                 cwd=str(self.lab.wt)))
        self.assertEqual(r.returncode, 0)
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(ctx), 1500)

    def test_general_purpose_denied(self):                  # criterio 4, eval 9
        r = run(self.lab, "PreToolUse", sample(
            "PreToolUse-Agent", session_id=SESSION, cwd=str(self.lab.wt),
            tool_input={"description": "d", "prompt": "p", "subagent_type": "general-purpose"}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("/tollgate:execute", r.stderr)

    def test_read_tool_not_routed(self):
        r = run(self.lab, "PreToolUse", sample("PreToolUse-Read", session_id=SESSION,
                                               cwd=str(self.lab.wt)))
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
```

Run: `tests/run`
Expected: OK.

- [ ] **Step 2: Matrice dei criteri**

Per ogni criterio della colonna P2 del piano principale (2, 3, 4 hook, 5, 6, 7, 8, 13, 14, 15, 18 parte P2, 19, 20, 21 parte P2, 22 parte P2, 23, 29 parte P2, 30 parte P2, 31 parte hook, 32 parte hook, 34 push negato, 37 parte hook, 38 parte hook, 39 `SubagentStop`, 42 `plan-check`) scrivere nel ledger (o nel rapporto finale) il test che lo dimostra, con `file::classe.metodo`. Un criterio senza test è un buco: si aggiunge il test nel modulo che possiede il codice, prima di chiudere. Criteri che restano in parte a P3 o P4 (per esempio la parte «`task start` sceglie l'agente» del 38) si annotano come tali.

Controlli minimi attesi (se mancano, aggiungerli):
- 18: per ogni chiave di `[components]` usata da P2 (`scope_check`, `plan_check`, `test_guard`, `context_guard`, `subagent_receipt_gate`, `single_writer`, `readonly_check`, `task_size`, `task_budget`, `must_have_tests`, `report_fields`) un test che la mette a `false` e vede il controllo spento. Quelli non coperti dai Task 15-19 vanno in `tests/test_components_p2.py`, un test per chiave, con la stessa forma di `ReceiptGateOffTest`.
- 38: un profilo `web` con `skills = ["ui-ux-pro-max"]` e un task su `web/`: DONE senza aver invocato la skill → veto (con `tasks.add_task(..., skills_required=["ui-ux-pro-max"])`).
- 15: ricevuta `empty` con zero test, report vecchio cancellato, variabile non in `env_allow` non visibile: già in `tests/test_verify.py`.

- [ ] **Step 3: Revisione 21 della spec (completamento)**

Oltre a quanto scritto nel Task 1, la revisione 21 riporta:
- 7.1: classificazione degli hook di controllo (`PreToolUse`) e informativi (gli altri), anche per «Python mancante» (decisione 1); scadenza interna con `signal.alarm` e cane da guardia del wrapper (decisione 4); interruttore gestito dal wrapper con `off.log` importato negli eventi (decisione 5); segnalino `bound/` (decisione 22);
- 12.2: le colonne e la tabella della migrazione 2 (decisione 7);
- 11.3: forma del file del contesto `{"used_pct": …}` (decisione 13);
- 8.4: oggetto e target degli atti per ogni comando (decisione 15); un `approve waiver` vale in ogni stato dell'atto (decisione 10);
- 8.3: le deroghe dichiarate sciolgono la violazione in locale anche se in attesa; `open-pr` rifiuta finché ce ne sono in attesa (decisione 9);
- 8.1: report configurato e assente → `red`; `uncounted` solo senza report (decisione 11).

- [ ] **Step 4: Piano principale**

In `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`:
- intestazione «Stato»: P2 chiuso sul ramo (merge su `main` in attesa dell'OK dell'utente), con il numero di test;
- sezione 3, «Pacchetti»: aggiungere `tollgate_hooks` (motore: adattatore, contesto, registro, runner, operazioni `record`);
- sezione 3, «Contratti», righe P2 → P3/P4 con i nomi reali: `tollgate_analysis.plan.check_plan`, `level.*`, `testguard.check` e `GuardConfig`, `junit.parse_junit`, `waivers.*`, `bash.*`, `report.*`; `tollgate_core.verify.run_verify`, `receipts.*`, `scope.register_plan`, `tasks.assign` (che `task start` deve chiamare con `pending = "launch"`, o `"resume"` per i giri 1-3), `subagents.*`, `effects.*`, `sessions.*`; il contratto dei moduli di `tollgate_checks` e l'elenco `apply.OPS`;
- vincoli nuovi per P3: `task start` scrive il brief con `name` uguale a `tasks.implementer`; la statusline scrive `ctx/<session_id>.json` con `used_pct`; `start` pulisce i segnalini `bound/` delle sessioni chiuse; `open-pr` rifiuta con deroghe in attesa (`waivers.status`) e con effetti `requested`; `approve level` scrive `level_cap_paths`; i verdetti dei revisori e i report degli avversari sono moduli nuovi di `tollgate_checks` per `subagent_stop`, che devono controllare `subagents.state != 'tampered'`;
- sezione 4, nota alla riga 16: le due voci verificate nel Task 1 con il loro esito.

- [ ] **Step 5: Suite completa e commit**

Run: `tests/run`
Expected: OK su entrambe le versioni, nessun `ResourceWarning` con `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`.

```bash
git add tests/test_criteria_p2.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git add tests/test_components_p2.py 2>/dev/null || true
git commit -m "tollgate P2: prove dei criteri dal wrapper, spec rev 21, piano principale"
```
