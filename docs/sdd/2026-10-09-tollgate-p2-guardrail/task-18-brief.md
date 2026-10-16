### Task 18: Subagenti: `PreToolUse Agent` e `SendMessage`, `SubagentStart`, `PostToolUse Agent`, `Skill`, `SubagentHandback`

**Files:**
- Create: `bin/tollgate_checks/agents.py`
- Create: `bin/tollgate_checks/send_message.py`
- Create: `bin/tollgate_checks/subagent_start.py`
- Create: `bin/tollgate_checks/post_agent.py`
- Create: `bin/tollgate_checks/skills.py`
- Create: `bin/tollgate_checks/handback.py`
- Test: `tests/test_check_agents.py`

**Interfaces:**
- Consumes: `subagents.*`, `tasks.assign` (nei test), `report.is_turn_cut`, `git.head`, `git.fingerprint`, `_common.governing_work`.
- Produces:
  - Modulo `agents` (`pre_agent`, ordine 20): guardia del contesto (componente `context_guard`, file della decisione 13), subagenti fermi oltre `stale_minutes` → `interrupted`, scrittore unico (componente `single_writer`), in `execution` L1/L2 solo il tipo, il `name` e il primo piano voluti da `task start`.
  - Modulo `send_message` (`pre_send_message`, ordine 20): risolve `to` per nome o `agent_id`; riprese ammesse con `pending = 'resume'` o per rispondere a `NEEDS_CONTEXT`.
  - Modulo `subagent_start` (`subagent_start`, ordine 20): riga in `subagents` con base e impronta (non sovrascritte alla ripresa), associazione al task in sospeso, promemoria dell'implementatore (≤ 2.000 caratteri dal runner).
  - Modulo `post_agent` (`post_agent`, ordine 20): nome → `agent_id`; report da `handbackReport`; taglio di `maxTurns` (componente `task_budget`) → riga chiusa `cut`, task `blocked`, blocco `needs_you`.
  - Modulo `skills` (`post_skill`, ordine 20): skill usata dal task dell'implementatore.
  - Modulo `handback` (`subagent_handback`, ordine 10): report del subagente in auto mode.
  - Promemoria iniettato all'implementatore: contiene il percorso assoluto di `bin/tollgate` e la riga «prima di DONE: commit, poi `<bin> verify`».

- [ ] **Step 1: Test**

`tests/test_check_agents.py`:

```python
import json
import unittest
from datetime import timedelta

from tests.hookkit import SESSION, T0, Lab, sample
from tests.helpers import git
from tests.test_check_writes import with_scope
from tollgate_core import phases, subagents, tasks

IMPL = "tollgate:implementer"


def agent_payload(lab, atype, name=None, bg=False):
    ti = {"description": "d", "prompt": "p", "subagent_type": atype, "run_in_background": bg}
    if name:
        ti["name"] = name
    return sample("PreToolUse-Agent", session_id=SESSION, cwd=str(lab.wt), tool_input=ti)


def send(lab, to, agent_id=None):
    extra = {"agent_id": agent_id, "agent_type": IMPL} if agent_id else {}
    return lab.hook(sample("PreToolUse-SendMessage", session_id=SESSION, cwd=str(lab.wt),
                           tool_input={"to": to, "message": "continua", "summary": "s"},
                           **extra))


def start(lab, agent_id, atype=IMPL):
    return lab.hook(sample("SubagentStart-none", session_id=SESSION, cwd=str(lab.wt),
                           agent_id=agent_id, agent_type=atype))


class PreAgentTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)

    def tearDown(self):
        self.lab.close()

    def assign(self, pending="launch"):
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending=pending, now=self.lab.now)

    def test_general_purpose_denied_with_execute_hint(self):
        r = self.lab.hook(agent_payload(self.lab, "general-purpose"))
        self.assertEqual(r.exit, 2)
        self.assertIn("/tollgate:execute", r.stderr)

    def test_implementer_rules(self):
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 2)
        self.assign()
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL)).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1", bg=True)).exit, 2)
        self.assertEqual(self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1")).exit, 0)

    def test_readonly_always_allowed(self):
        for t in ("tollgate:task-reviewer", "Explore", "probe:reviewer-frontend"):
            self.assertEqual(self.lab.hook(agent_payload(self.lab, t)).exit, 0)

    def test_single_writer_and_stale(self):
        subagents.start(self.lab.conn, agent_id="a-vecchio", type_=IMPL, session=SESSION,
                        work=self.lab.work, task=None, base_sha=self.lab.base, fingerprint="f",
                        now=self.lab.now)
        self.assign()
        r = self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1"))
        self.assertEqual(r.exit, 2)
        self.assertIn("/tollgate:resolve writer", r.stderr)
        r = self.lab.hook(agent_payload(self.lab, IMPL, "tg-7-t1"),
                          now=self.lab.now + timedelta(minutes=31))
        self.assertEqual(r.exit, 0)
        self.assertEqual(subagents.get(self.lab.conn, "a-vecchio")["state"], "interrupted")

    def test_context_guard(self):
        d = self.lab.ts.dir / "ctx"
        d.mkdir()
        for pct, code in ((60, 2), (50, 0), (None, 0)):
            (d / f"{SESSION}.json").write_text(json.dumps({"used_pct": pct}))
            with self.subTest(pct=pct):
                r = self.lab.hook(agent_payload(self.lab, "Explore"))
                self.assertEqual(r.exit, code)
                if pct == 50:
                    self.assertIn("contesto", r.stdout)


class StartAndResumeTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        with_scope(self.lab)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="launch", now=self.lab.now)

    def tearDown(self):
        self.lab.close()

    def test_start_associates_task_and_keeps_base_on_resume(self):
        r = start(self.lab, "a1")
        self.assertIn("verify", r.stdout)
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["task"], row["agent_base_sha"]), (1, self.lab.base))
        self.assertIsNone(tasks.get_task(self.lab.conn, self.lab.work, 1)["pending"])
        (self.lab.wt / "src/app.py").write_text("x = 2\n")
        git(self.lab.wt, "commit", "-qam", "lavoro")
        subagents.finish(self.lab.conn, "a1", state="done", now=self.lab.now)
        start(self.lab, "a1")
        row = subagents.get(self.lab.conn, "a1")
        self.assertEqual((row["agent_base_sha"], row["resumes"]), (self.lab.base, 1))

    def test_name_registry_and_send_message(self):
        start(self.lab, "a1")
        post = sample("PostToolUse-Agent-foreground-manual", session_id=SESSION,
                      cwd=str(self.lab.wt))
        post["tool_input"]["name"] = "tg-7-t1"
        post["tool_response"]["agentId"] = "a1"
        self.lab.hook(post)
        self.assertEqual(subagents.by_name(self.lab.conn, "tg-7-t1", work=self.lab.work)["id"],
                         "a1")
        subagents.finish(self.lab.conn, "a1", state="done", declared_status="DONE",
                         now=self.lab.now)
        self.assertEqual(send(self.lab, "mai-visto").exit, 2)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 2)
        tasks.assign(self.lab.conn, self.lab.work, 1, implementer="tg-7-t1", agent_type=IMPL,
                     pending="resume", now=self.lab.now)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 0)
        self.assertEqual(send(self.lab, "a1").exit, 0)

    def test_needs_context_resume_allowed(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        start(self.lab, "a1")
        subagents.set_name(self.lab.conn, "a1", "tg-7-t1", session=SESSION, work=self.lab.work,
                           now=self.lab.now)
        subagents.finish(self.lab.conn, "a1", state="done", declared_status="NEEDS_CONTEXT",
                         now=self.lab.now)
        self.assertEqual(send(self.lab, "tg-7-t1").exit, 0)

    def test_turn_cut_closes_row_and_blocks_task(self):
        tasks.task_event(self.lab.conn, self.lab.work, 1, "start", now=self.lab.now)
        cut = sample("PostToolUse-Agent-maxturns-cut", session_id=SESSION, cwd=str(self.lab.wt))
        aid = cut["tool_response"]["agentId"]
        start(self.lab, aid)
        self.lab.hook(cut)
        self.assertEqual(subagents.get(self.lab.conn, aid)["state"], "cut")
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 1)["state"], "blocked")
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "blocked")
        self.assertEqual(subagents.running(self.lab.conn, work=self.lab.work), [])

    def test_skill_and_handback(self):
        start(self.lab, "a1")
        self.lab.hook(sample("PostToolUse-Skill", session_id=SESSION, cwd=str(self.lab.wt),
                             agent_id="a1", agent_type=IMPL, tool_name="Skill",
                             tool_input={"skill": "superpowers:test-driven-development"},
                             tool_response={"success": True}))
        self.assertIn("test-driven-development",
                      tasks.get_task(self.lab.conn, self.lab.work, 1)["skills_used"])
        hb = sample("PostToolUse-SubagentHandback", session_id=SESSION, cwd=str(self.lab.wt),
                    agent_id="a1", agent_type=IMPL, tool_input={"message": "{\"status\":\"DONE\"}"})
        self.lab.hook(hb)
        self.assertEqual(subagents.get(self.lab.conn, "a1")["report"], '{"status":"DONE"}')


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_check_agents -v`
Expected: FAIL.

- [ ] **Step 3: `agents.py`**

```python
"""PreToolUse Agent (spec 7.2, 6.3): contesto, subagenti fermi, scrittore unico, implementatore."""
from __future__ import annotations

import json

from tollgate_core import subagents
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["pre_agent"], "component": None, "order": 20}


def context_pct(ctx, session: str):
    try:
        data = json.loads((ctx.state.root / "ctx" / f"{session}.json").read_text())
        v = data.get("used_pct")
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
    except (OSError, ValueError, AttributeError):
        return None


def live_writers(ctx, work_id, exclude=()):
    rows = subagents.running(ctx.db, work=work_id)
    stale = [r for r in rows if subagents.is_stale(r, now=ctx.now,
                                                    stale_minutes=ctx.stale_minutes)]
    live = [r for r in rows if r not in stale and r["id"] not in exclude
            and not ctx.readonly(r["type"])]
    return live, [record("subagent_interrupt", agent_id=r["id"]) for r in stale]


def decide(event, ctx):
    work = governing_work(ctx, event.cwd)
    if work is None:
        return []
    out = []
    if ctx.component("context_guard"):
        pct = context_pct(ctx, event.session)
        if pct is not None and pct >= ctx.cfg("context.stop_pct"):
            return [deny(f"contesto al {pct:.0f}%: nessun nuovo subagente. Scrivi il checkpoint "
                         f"(tollgate status --checkpoint) e fai /clear (6.3)", rule="context")]
        if pct is not None and pct >= ctx.cfg("context.warn_pct"):
            out.append(inject(f"tollgate: contesto al {pct:.0f}%; a "
                              f"{ctx.cfg('context.stop_pct')}% servirà checkpoint e /clear."))
    ti = event.tool_input
    atype = str(ti.get("subagent_type") or "general-purpose")
    if ctx.readonly(atype):
        return out
    live, interrupts = live_writers(ctx, work["id"])
    out += interrupts
    if ctx.component("single_writer") and live:
        w = live[0]
        return out + [deny(f"scrittore unico: {w['type']} ({w['id']}) è ancora in corso nel "
                           f"lavoro #{work['issue']}. Se la sua sessione è caduta: "
                           f"/tollgate:resolve writer", rule="single_writer")]
    if work["phase"] != "execution" or work["level"] not in ("L1", "L2"):
        return out
    pending = ctx.db.execute("SELECT * FROM tasks WHERE work = ? AND pending = 'launch' "
                             "ORDER BY number", (work["id"],)).fetchall()
    cand = [t for t in pending if t["agent_type"] == atype]
    if not cand:
        hint = (f"; il task {pending[0]['number']} aspetta {pending[0]['agent_type']}"
                if pending else "")
        return out + [deny(f"in execution l'unico subagente che scrive è l'implementatore scelto "
                           f"da tollgate task start: {atype} non ha un task start in sospeso"
                           f"{hint}. Usa /tollgate:execute (6.3)", rule="writer")]
    t = cand[0]
    if ti.get("name") != t["implementer"]:
        return out + [deny(f"l'implementatore va lanciato con name «{t['implementer']}» "
                           f"(scritto nel brief): serve per riprenderlo con SendMessage",
                           rule="writer")]
    if ti.get("run_in_background"):
        return out + [deny("l'implementatore si lancia in primo piano: i task sono in sequenza",
                           rule="writer")]
    return out
```

- [ ] **Step 4: `send_message.py`**

```python
"""PreToolUse SendMessage (spec 7.2, 6.3): le riprese seguono le regole dello scrittore."""
from __future__ import annotations

from tollgate_core import subagents
from tollgate_hooks.model import deny

from ._common import governing_work
from .agents import live_writers

CHECK = {"api": 1, "events": ["pre_send_message"], "component": None, "order": 20}


def decide(event, ctx):
    work = governing_work(ctx, event.cwd)
    if work is None:
        return []
    to = str(event.tool_input.get("to") or event.tool_input.get("recipient") or "")
    target = subagents.by_name(ctx.db, to, work=work["id"]) or (
        subagents.get(ctx.db, to) if to else None)
    from_main = event.agent_id is None
    in_exec = work["phase"] == "execution" and work["level"] in ("L1", "L2")
    if target is None:
        if from_main and in_exec:
            return [deny(f"destinatario «{to}» mai registrato: in execution vale come un "
                         f"implementatore senza task start (6.3)", rule="writer")]
        return []
    if ctx.readonly(target["type"]) or not target["type"]:
        return []
    if not from_main:
        return [deny("un subagente non riprende un subagente che scrive", rule="writer")]
    if not in_exec:
        return []
    task = None
    if target["task"] is not None:
        task = ctx.db.execute("SELECT * FROM tasks WHERE work = ? AND number = ?",
                              (work["id"], target["task"])).fetchone()
    ok = task is not None and (
        (task["pending"] == "resume" and task["agent_type"] == target["type"])
        or (task["state"] == "running" and target["declared_status"] == "NEEDS_CONTEXT"))
    if not ok:
        return [deny(f"ripresa di {to} negata: serve tollgate task start {target['task']} --fix, "
                     f"oppure una risposta a NEEDS_CONTEXT (6.3)", rule="writer")]
    if ctx.component("single_writer"):
        live, _ = live_writers(ctx, work["id"], exclude=(target["id"],))
        if live:
            return [deny(f"scrittore unico: {live[0]['id']} è ancora in corso",
                         rule="single_writer")]
    return []
```

- [ ] **Step 5: `subagent_start.py`, `post_agent.py`, `skills.py`, `handback.py`**

`subagent_start.py`:

```python
"""SubagentStart (spec 7.2): base, impronta e tipo; associazione al task; promemoria."""
from __future__ import annotations

from pathlib import Path

from tollgate_core import git, subagents
from tollgate_hooks.model import inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["subagent_start"], "component": None, "order": 20}


def decide(event, ctx):
    if not event.agent_type or not event.agent_id:
        return []
    work = governing_work(ctx, event.cwd)
    row = subagents.get(ctx.db, event.agent_id)
    resume = row is not None and row["started"] is not None
    wt = Path(work["worktree"]) if work is not None and work["worktree"] else None
    base = git.head(wt) if wt is not None and wt.is_dir() else None
    fp = git.fingerprint(wt, ctx.cfg("review.output_dirs")) if base else None
    implementer = not ctx.readonly(event.agent_type)
    out = [record("subagent_start", agent_id=event.agent_id, type=event.agent_type,
                  work=work["id"] if work is not None else None,
                  task=row["task"] if row is not None else None, base_sha=base, fingerprint=fp,
                  take_pending=implementer and work is not None, resume=resume)]
    if implementer and work is not None:
        out.append(inject(
            f"tollgate: sei un subagente che scrive nel lavoro #{work['issue']}. Lavora solo sui "
            f"file dello scope del task, con TDD. Prima di DONE: committa, poi lancia "
            f"'{ctx.plugin_bin}' verify e controlla che la ricevuta sia green. Chiudi con il "
            f"report JSON di 18.5 (v, task, status, done, tests, files, must_have, concerns, "
            f"left, size_reason). Se un test contraddice la specifica: "
            f"'{ctx.plugin_bin}' block open test_spec_conflict --reason \"…\" e BLOCKED."))
    return out
```

`post_agent.py`:

```python
"""PostToolUse Agent (spec 7.2): nome → agent_id, report in primo piano, taglio di maxTurns."""
from __future__ import annotations

from tollgate_analysis import report
from tollgate_core import subagents
from tollgate_hooks.model import inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["post_agent"], "component": None, "order": 20}


def decide(event, ctx):
    tr = event.tool_response or {}
    aid = tr.get("agentId")
    if not aid:
        return []
    work = governing_work(ctx, event.cwd)
    wid = work["id"] if work is not None else None
    out = []
    if event.tool_input.get("name"):
        out.append(record("subagent_name", agent_id=aid, name=str(event.tool_input["name"]),
                          work=wid))
    hb = tr.get("handbackReport")
    if isinstance(hb, dict) and isinstance(hb.get("text"), str):
        out.append(record("subagent_report", agent_id=aid, text=hb["text"]))
    if ctx.component("task_budget") and report.is_turn_cut(tr):
        row = subagents.get(ctx.db, aid)
        if row is not None and row["state"] == "running":
            out.append(record("subagent_finish", agent_id=aid, state="cut"))
        task = row["task"] if row is not None else None
        if wid is not None and task is not None:
            t = ctx.db.execute("SELECT state FROM tasks WHERE work = ? AND number = ?",
                               (wid, task)).fetchone()
            if t is not None and t["state"] == "running":
                out += [record("task", work=wid, number=task, event="budget_exceeded"),
                        record("block", work=wid, type="needs_you",
                               reason=f"budget superato: maxTurns esaurito sul task {task}. "
                                      f"Proposta: dividere il task")]
        out.append(inject("tollgate: il subagente ha esaurito maxTurns. Il task è bloccato con "
                          "needs_you: non riprenderlo con SendMessage."))
    return out
```

`skills.py`:

```python
"""PostToolUse Skill (spec 7.2, 6.3): la skill usata dall'implementatore va al suo task."""
from __future__ import annotations

from tollgate_core import subagents
from tollgate_hooks.model import record

CHECK = {"api": 1, "events": ["post_skill"], "component": None, "order": 20}


def decide(event, ctx):
    if not event.agent_id:
        return []
    row = subagents.get(ctx.db, event.agent_id)
    skill = event.tool_input.get("skill") or event.tool_input.get("command")
    if row is None or row["task"] is None or row["work"] is None or not skill:
        return []
    return [record("skill_used", work=row["work"], number=row["task"], skill=str(skill))]
```

`handback.py`:

```python
"""PostToolUse SubagentHandback (spec 7.2): in auto mode è l'unica fonte del report."""
from __future__ import annotations

from tollgate_hooks.model import record

CHECK = {"api": 1, "events": ["subagent_handback"], "component": None, "order": 10}


def decide(event, ctx):
    msg = event.tool_input.get("message")
    if not event.agent_id or not isinstance(msg, str):
        return []
    return [record("subagent_report", agent_id=event.agent_id, text=msg)]
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK. Se il campione `PostToolUse-Agent-maxturns-cut` non porta il taglio nella forma attesa, vale il Task 1 e il Task 8: il test usa l'input reale.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_checks/agents.py bin/tollgate_checks/send_message.py bin/tollgate_checks/subagent_start.py bin/tollgate_checks/post_agent.py bin/tollgate_checks/skills.py bin/tollgate_checks/handback.py tests/test_check_agents.py
git commit -m "tollgate P2: controlli dei subagenti (scrittore unico, riprese, nomi, maxTurns, skill)"
```

---

