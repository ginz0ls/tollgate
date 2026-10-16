### Task 19: `SubagentStop`: implementatori (8.1, 6.3) e sola lettura (7.3)

**Files:**
- Create: `bin/tollgate_checks/subagent_stop.py`
- Test: `tests/test_check_subagent_stop.py`

**Interfaces:**
- Consumes: `report.parse_report`, `report.transcript_tokens`, `receipts.latest`, `receipts.any_since`, `verify.counts_green`, `git.*`, `subagents.get`.
- Produces: modulo `subagent_stop` (evento `subagent_stop`, ordine 20). Ordine dei controlli per un implementatore: tetto di token (componente `task_budget`, prima di tutto, 6.3) → report a campi fissi (`report_fields`) → dimensione del task (`task_size`) → ricevuta (`subagent_receipt_gate`) → skill dei profili → transizione del task. Ogni veto conta in `subagents.vetoes`; dopo 2 veti si apre `needs_you` e il subagente chiude (8.1). Sola lettura con impronta cambiata (`readonly_check`) → riga `tampered` e `needs_you`. `agent_type` vuoto o `agent_id` mai visto → ignorato.

- [ ] **Step 1: Test**

`tests/test_check_subagent_stop.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from tests.hookkit import DEFAULT_TOML, SESSION, Lab, sample
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import git as tg_git, phases, receipts, subagents, tasks

IMPL = "tollgate:implementer"


def report(status="DONE", **extra):
    data = {"v": 1, "task": 1, "status": status, "done": "fatto", "tests": "verify green",
            "files": ["src/app.py"], "must_have": [], "concerns": "", "left": "",
            "size_reason": None}
    data.update(extra)
    return "Fine.\n```json\n" + json.dumps(data) + "\n```"


class Base(unittest.TestCase):
    toml = DEFAULT_TOML

    def setUp(self):
        self.lab = Lab(toml=self.toml)
        with_scope(self.lab, ("src/app.py", "tests/test_app.py", "src/big.py"))
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        self.start("a1", IMPL, task=1)

    def tearDown(self):
        self.lab.close()

    def start(self, aid, atype, task=None):
        subagents.start(self.lab.conn, agent_id=aid, type_=atype, session=SESSION,
                        work=self.lab.work, task=task, base_sha=tg_git.head(self.lab.wt),
                        fingerprint=tg_git.fingerprint(self.lab.wt, ["reports/", "coverage/"]),
                        now=self.lab.now)

    def stop(self, aid="a1", atype=IMPL, text=None, transcript=None):
        p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.lab.wt),
                   agent_id=aid, agent_type=atype, last_assistant_message=text,
                   agent_transcript_path=transcript or "/non/esiste.jsonl")
        if text is None:
            p.pop("last_assistant_message")
        return self.lab.hook(p)

    def commit(self, content="def somma(a, b):\n    return b + a\n", path="src/app.py"):
        (self.lab.wt / path).write_text(content)
        git(self.lab.wt, "add", "-A")
        git(self.lab.wt, "commit", "-qm", "lavoro")
        return git(self.lab.wt, "rev-parse", "HEAD")

    def green(self, sha, state="green"):
        receipts.add(self.lab.conn, work=self.lab.work, sha=sha, command="verify",
                     resolved_command="true", exit_code=0, tests_run=0 if state == "empty" else 2,
                     tests_skipped=0, duration=0.1, log=None, produced_by="verify", state=state,
                     now=self.lab.now)

    def task_state(self):
        return tasks.get_task(self.lab.conn, self.lab.work, 1)["state"]


class ReceiptGateTest(Base):
    def test_done_without_receipt_two_vetoes_then_needs_you(self):
        self.commit()
        self.assertEqual(self.stop(text=report()).exit, 2)
        self.assertEqual(self.stop(text=report()).exit, 2)
        r = self.stop(text=report())
        self.assertEqual(r.exit, 0)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")
        self.assertEqual(self.task_state(), "blocked")

    def test_done_with_green_receipt(self):
        self.green(self.commit())
        self.assertEqual(self.stop(text=report()).exit, 0)
        self.assertEqual(self.task_state(), "review")
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "done")

    def test_done_with_changes_but_no_commit(self):
        (self.lab.wt / "src/app.py").write_text("x = 3\n")
        r = self.stop(text=report())
        self.assertEqual(r.exit, 2)
        self.assertIn("committa", r.stderr)

    def test_done_without_changes_passes(self):
        self.assertEqual(self.stop(text=report()).exit, 0)

    def test_blocked_with_red_receipt_closes(self):
        self.green(self.commit(), state="red")
        self.assertEqual(self.stop(text=report("BLOCKED", concerns="manca un dato")).exit, 0)
        self.assertEqual(self.task_state(), "blocked")

    def test_needs_context_without_receipt_or_block(self):
        self.assertEqual(self.stop(text=report("NEEDS_CONTEXT")).exit, 2)

    def test_invalid_report(self):
        r = self.stop(text='{"status": "DONE"}')
        self.assertEqual(r.exit, 2)
        self.assertIn("non valido", r.stderr)

    def test_report_from_handback(self):
        self.green(self.commit())
        subagents.set_report(self.lab.conn, "a1", report())
        self.assertEqual(self.stop(text=None).exit, 0)

    def test_internal_and_unknown_ignored(self):
        self.assertEqual(self.stop(aid="mai-visto").exit, 0)
        self.assertEqual(self.stop(atype="").exit, 0)


class BudgetAndSizeTest(Base):
    def test_tokens_over_cap_block_even_with_green(self):
        self.green(self.commit())
        tr = Path(tempfile.mkdtemp()) / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {
            "id": "m", "usage": {"input_tokens": 500000, "output_tokens": 1}}}) + "\n")
        self.assertEqual(self.stop(text=report(), transcript=str(tr)).exit, 0)
        self.assertEqual(self.task_state(), "blocked")
        self.assertEqual(subagents.get(self.lab.conn, "a1")["state"], "budget")

    def test_size_reason_required_over_max(self):
        sha = self.commit("".join(f"x{i} = {i}\n" for i in range(600)), path="src/big.py")
        self.green(sha)
        self.assertEqual(self.stop(text=report()).exit, 2)
        self.assertEqual(self.stop(text=report(size_reason="generato da uno schema")).exit, 0)


class AllowNoTestsTest(Base):
    toml = DEFAULT_TOML + "[project]\nallow_no_tests = true\n"

    def test_empty_receipt_counts(self):
        self.green(self.commit(), state="empty")
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReceiptGateOffTest(Base):
    toml = DEFAULT_TOML + "[components]\nsubagent_receipt_gate = false\n"

    def test_done_without_receipt_passes(self):
        self.commit()
        self.assertEqual(self.stop(text=report()).exit, 0)


class ReadonlyTest(Base):
    def test_tampering_reviewer(self):
        self.start("r1", "tollgate:task-reviewer")
        (self.lab.wt / "src/app.py").write_text("manomesso\n")
        self.assertEqual(self.stop(aid="r1", atype="tollgate:task-reviewer", text="ok").exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "r1")["state"], "tampered")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")

    def test_clean_reviewer(self):
        self.start("r2", "tollgate:task-reviewer")
        self.stop(aid="r2", atype="tollgate:task-reviewer", text="ok")
        self.assertEqual(subagents.get(self.lab.conn, "r2")["state"], "done")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_check_subagent_stop -v`
Expected: FAIL.

- [ ] **Step 3: `subagent_stop.py`**

```python
"""SubagentStop (spec 7.2, 8.1, 6.3, 7.3): implementatori e sola lettura. Revisori e avversari: P3."""
from __future__ import annotations

import json
import posixpath
from pathlib import Path

from tollgate_analysis import globs, report
from tollgate_core import git, receipts, subagents
from tollgate_core.verify import counts_green
from tollgate_hooks.model import deny, record

CHECK = {"api": 1, "events": ["subagent_stop"], "component": None, "order": 20}
MAX_VETOES = 2
_GENERATED = ["**/*.min.js", "**/*.generated.*", "**/__snapshots__/**", "**/dist/**"]


def _readonly(ctx, row, work):
    out = []
    if ctx.component("readonly_check") and work is not None and work["worktree"] \
            and row["fingerprint"]:
        wt = Path(work["worktree"])
        if git.fingerprint(wt, ctx.cfg("review.output_dirs")) != row["fingerprint"]:
            return [record("subagent_finish", agent_id=row["id"], state="tampered"),
                    record("block", work=work["id"], type="needs_you",
                           reason=f"il subagente di sola lettura {row['type']} ha cambiato "
                                  f"file: il suo verdetto non vale (7.3)")]
    return out + [record("subagent_finish", agent_id=row["id"], state="done")]


def _task_lines(ctx, wt: Path, base: str, head: str) -> int:
    lockfiles = set(ctx.cfg("scope.lockfiles"))
    return sum(c.added + c.removed for c in git.changes(wt, base, head=head)
               if posixpath.basename(c.path) not in lockfiles
               and not globs.match_any(_GENERATED, c.path))


def _skill_missing(task) -> list[str]:
    used = json.loads(task["skills_used"])
    tail = {u.split(":")[-1] for u in used}
    return [s for s in json.loads(task["skills_required"])
            if s not in used and s.split(":")[-1] not in tail]


def decide(event, ctx):
    if not event.agent_type or not event.agent_id:
        return []
    row = subagents.get(ctx.db, event.agent_id)
    if row is None or row["started"] is None:
        return []      # subagente interno di Claude Code, mai visto a SubagentStart (P0)
    work = ctx.db.execute("SELECT * FROM work_items WHERE id = ?",
                          (row["work"],)).fetchone() if row["work"] is not None else None
    if ctx.readonly(event.agent_type):
        return _readonly(ctx, row, work)
    if work is None or not work["worktree"]:
        return [record("subagent_finish", agent_id=row["id"], state="done")]
    wid, aid = work["id"], row["id"]
    task = None
    if row["task"] is not None:
        task = ctx.db.execute("SELECT * FROM tasks WHERE work = ? AND number = ?",
                              (wid, row["task"])).fetchone()
    running = task is not None and task["state"] == "running"
    tokens = report.transcript_tokens(event.raw.get("agent_transcript_path") or "")
    cap = ctx.cfg("tasks.max_tokens").get(work["level"], 0)
    if ctx.component("task_budget") and cap and tokens > cap and running:
        return [record("subagent_finish", agent_id=aid, state="budget", tokens=tokens),
                record("task", work=wid, number=task["number"], event="budget_exceeded"),
                record("block", work=wid, type="needs_you",
                       reason=f"budget superato: {tokens} token oltre il tetto di {cap} sul task "
                              f"{task['number']}. Proposta: dividere il task")]
    rep = report.parse_report(event.raw.get("last_assistant_message") or row["report"])

    def veto(msg: str):
        if row["vetoes"] >= MAX_VETOES:
            out = [record("subagent_finish", agent_id=aid, state="done",
                          declared_status=rep.status, tokens=tokens)]
            if running:
                out.append(record("task", work=wid, number=task["number"],
                                  event="report_blocked"))
            return out + [record("block", work=wid, type="needs_you",
                                 reason=f"implementatore chiuso dopo {MAX_VETOES} veti: {msg}")]
        return [record("subagent_veto", agent_id=aid),
                deny(f"{msg} (veto {row['vetoes'] + 1} di {MAX_VETOES})",
                     rule="subagent_stop")]

    if ctx.component("report_fields") and not rep.valid:
        return veto("report finale non valido: mancano " + ", ".join(rep.missing)
                    + ". Chiudi con un blocco JSON con i campi di 18.5")
    wt = Path(work["worktree"])
    head, base = git.head(wt), row["agent_base_sha"]
    commits = git.rev_list(wt, base, head) if base and head and base != head else []
    if ctx.component("task_size") and commits and not rep.data.get("size_reason"):
        lines = _task_lines(ctx, wt, base, head)
        if lines > ctx.cfg("tasks.task_lines_max"):
            return veto(f"il task cambia {lines} righe, oltre task_lines_max "
                        f"({ctx.cfg('tasks.task_lines_max')}): aggiungi size_reason al report "
                        f"oppure dividi il task")
    done = rep.status in ("DONE", "DONE_WITH_CONCERNS")
    if ctx.component("subagent_receipt_gate"):
        allow = ctx.cfg("project.allow_no_tests")
        if done and commits:
            latest = receipts.latest(ctx.db, wid, head)
            if not latest or not all(counts_green(r["state"], r["exit"], allow) for r in latest):
                return veto(f"DONE senza ricevuta green su {head[:10]}: lancia "
                            f"'{ctx.plugin_bin}' verify")
        elif done:
            if row["fingerprint"] and git.fingerprint(
                    wt, ctx.cfg("review.output_dirs")) != row["fingerprint"]:
                return veto("file modificati senza commit: committa e verifica")
        else:
            has_block = ctx.db.execute("SELECT 1 FROM blocks WHERE work = ? AND closed IS NULL",
                                       (wid,)).fetchone() is not None
            if not has_block and not receipts.any_since(ctx.db, wid, row["started"]):
                return veto(f"con {rep.status} serve una ricevuta ('{ctx.plugin_bin}' verify) "
                            f"oppure un blocco ('{ctx.plugin_bin}' block open <tipo> "
                            f"--reason …)")
    if done and task is not None:
        missing = _skill_missing(task)
        if missing:
            return veto("skill dei profili non usate: " + ", ".join(missing))
    out = [record("subagent_finish", agent_id=aid, state="done", declared_status=rep.status,
                  tokens=tokens)]
    if running:
        if done:
            out.append(record("task", work=wid, number=task["number"], event="report_done"))
        elif rep.status == "BLOCKED":
            out.append(record("task", work=wid, number=task["number"], event="report_blocked"))
            if ctx.db.execute("SELECT 1 FROM blocks WHERE work = ? AND closed IS NULL",
                              (wid,)).fetchone() is None:
                out.append(record("block", work=wid, type="needs_you",
                                  reason=f"task {task['number']} BLOCKED: "
                                         f"{rep.data.get('concerns') or rep.data.get('left') or ''}"[:500]))
    return out
```

- [ ] **Step 4: Verificare che passi**

Run: `tests/run`
Expected: OK. Nota su `test_tokens_over_cap_block_even_with_green`: il tetto L1 predefinito è 400.000; 500.001 token lo superano.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_checks/subagent_stop.py tests/test_check_subagent_stop.py
git commit -m "tollgate P2: SubagentStop per implementatori e subagenti di sola lettura"
```

---

