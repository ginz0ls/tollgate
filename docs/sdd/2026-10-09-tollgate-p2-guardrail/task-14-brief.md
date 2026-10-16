### Task 14: Controlli `SessionStart` e `UserPromptExpansion` (atti)

**Files:**
- Create: `bin/tollgate_checks/_common.py`
- Create: `bin/tollgate_checks/session.py`
- Create: `bin/tollgate_checks/acts.py`
- Test: `tests/test_check_session.py`, `tests/test_check_acts.py`

**Interfaces:**
- Consumes: `Ctx`, `model.*`, `sessions`, `subagents`, `git`, `paths.repo_key`, `acts.ACT_TYPES`, `acts.APPROVE_OBJECTS`.
- Produces in `_common.py` (aiuti condivisi dai moduli; il nome con `_` non viene caricato dal registro):
  - `repo_key_of(repo) -> str | None`; `orphan_tg(ctx, repo) -> int | None` (numero dell'issue di un ramo `tg/<N>-*` senza lavoro attivo); `governing_work(ctx, path) -> object | None` (il lavoro le cui regole valgono per quel percorso: quello della sessione legata, o quello del cui worktree il percorso fa parte); `is_docs_md(rel) -> bool`; `locked_docs(work) -> set[str]`; `waiver_hint(v, issue) -> str`; `explain(violations, issue) -> str`; `status_lines(ctx, work) -> list[str]`.
- Modulo `session` (evento `session_start`, ordine 10): lega la sessione se il `cwd` è nel worktree di un lavoro attivo; segna `interrupted` i subagenti `running` di sessioni non vive; fa scadere gli atti; inietta stato e checkpoint (≤ 10 righe, ≤ 1.500 caratteri dal runner); indica `adopt` per un ramo `tg/*` senza lavoro.
- Modulo `acts` (evento `prompt_expansion`, ordine 10): registra l'atto con oggetto e target della decisione 15.

- [ ] **Step 1: Test**

`tests/test_check_session.py`:

```python
import json
import unittest
from datetime import timedelta

from tests.hookkit import SESSION, T0, Lab, sample
from tollgate_core import phases, sessions, subagents


def start_payload(lab, session, cwd=None, source="startup"):
    return sample("SessionStart-none", session_id=session, cwd=str(cwd or lab.wt), source=source)


def context_of(r):
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout else ""


class SessionStartTest(unittest.TestCase):
    def test_binds_new_session_in_worktree(self):
        lab = Lab()
        try:
            r = lab.hook(start_payload(lab, "s-nuova"))
            self.assertEqual(r.exit, 0)
            self.assertIn("s-nuova", json.loads(phases.get_work(lab.conn, lab.work)["sessions"]))
            self.assertTrue((lab.ts.dir / "bound" / "s-nuova").is_file())
            ctx = context_of(r)
            self.assertIn("#7", ctx)
            self.assertIn("execution", ctx)
            self.assertLessEqual(len(ctx.splitlines()), 10)
            self.assertLessEqual(len(ctx), 1500)
        finally:
            lab.close()

    def test_main_checkout_does_not_bind(self):
        lab = Lab(bind=False)
        try:
            lab.hook(start_payload(lab, "s-fuori", cwd=lab.main))
            self.assertNotIn("s-fuori", json.loads(phases.get_work(lab.conn,
                                                                   lab.work)["sessions"]))
        finally:
            lab.close()

    def test_interrupts_only_dead_sessions(self):
        lab = Lab()
        try:
            sessions.touch(lab.conn, "morta", now=T0 - timedelta(hours=2))
            sessions.touch(lab.conn, "viva", now=lab.now)
            for aid, sess in (("a-morto", "morta"), ("a-vivo", "viva")):
                subagents.start(lab.conn, agent_id=aid, type_="tollgate:implementer",
                                session=sess, work=lab.work, task=None, base_sha=lab.base,
                                fingerprint="f", now=T0)
            lab.hook(start_payload(lab, SESSION, source="resume"))
            self.assertEqual(subagents.get(lab.conn, "a-morto")["state"], "interrupted")
            self.assertEqual(subagents.get(lab.conn, "a-vivo")["state"], "running")
        finally:
            lab.close()

    def test_checkpoint_is_injected(self):
        lab = Lab()
        try:
            cp = lab.wt / "docs/superpowers/reviews/7/checkpoint.md"
            cp.parent.mkdir(parents=True)
            cp.write_text("Prossimo passo: task 3\n")
            r = lab.hook(start_payload(lab, SESSION, source="clear"))
            self.assertIn("Prossimo passo: task 3", context_of(r))
        finally:
            lab.close()

    def test_orphan_tg_branch_points_to_adopt(self):
        lab = Lab(work=False)
        try:
            r = lab.hook(start_payload(lab, "s1"))
            self.assertIn("/tollgate:adopt #7", context_of(r))
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

`tests/test_check_acts.py`:

```python
import unittest

from tests.hookkit import SESSION, Lab, sample
from tollgate_core import git


def expand(lab, name, args, session=SESSION, cwd=None):
    return lab.hook(sample("UserPromptExpansion-none", session_id=session,
                           cwd=str(cwd or lab.wt), command_name=name, command_args=args,
                           prompt=f"/{name} {args}".strip()))


class ActsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def acts(self):
        return [dict(r) for r in self.lab.conn.execute("SELECT * FROM acts ORDER BY n")]

    def test_approve_waiver(self):
        r = expand(self.lab, "tollgate:approve", "waiver w-7-1")
        self.assertEqual(r.exit, 0)
        a = self.acts()[0]
        self.assertEqual((a["type"], a["object"], a["target"], a["work"], a["session"]),
                         ("approve", "waiver", "w-7-1", self.lab.work, SESSION))
        self.assertEqual(a["typed_text"], "/tollgate:approve waiver w-7-1")

    def test_finish_bound_to_head(self):
        expand(self.lab, "tollgate:finish", "")
        a = self.acts()[0]
        self.assertEqual((a["type"], a["head_sha"]), ("finish", git.head(self.lab.wt)))

    def test_approve_pr_targets_head(self):
        expand(self.lab, "tollgate:approve", "pr")
        self.assertEqual(self.acts()[0]["target"], git.head(self.lab.wt))

    def test_invalid_object_not_recorded(self):
        r = expand(self.lab, "tollgate:approve", "boh 3")
        self.assertEqual(self.acts(), [])
        self.assertIn("non registrato", r.stdout)

    def test_adopt_from_unbound_session(self):
        expand(self.lab, "tollgate:adopt", "#9", session="altra", cwd=self.lab.main)
        a = self.acts()[0]
        self.assertEqual((a["type"], a["target"], a["work"]), ("adopt", "9", None))

    def test_non_tollgate_and_status_are_not_acts(self):
        expand(self.lab, "superpowers:brainstorming", "")
        expand(self.lab, "tollgate:status", "")
        self.assertEqual(self.acts(), [])

    def test_skill_tool_does_not_create_acts(self):
        p = sample("PostToolUse-Skill", session_id=SESSION, cwd=str(self.lab.wt),
                   tool_name="Skill", tool_input={"skill": "tollgate:approve",
                                                  "args": "waiver w-7-1"},
                   tool_response={"success": True})
        self.lab.hook(p)
        self.assertEqual(self.acts(), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_session tests.test_check_acts -v`
Expected: FAIL (nessun legame, nessun atto: i moduli non esistono).

- [ ] **Step 3: `_common.py`**

```python
"""Aiuti condivisi dai controlli (non è un controllo: il registro salta i nomi con _)."""
from __future__ import annotations

import re
from pathlib import Path

from tollgate_core import git
from tollgate_core.paths import repo_key

_TG = re.compile(r"^tg/(\d+)-")


def repo_key_of(repo) -> str | None:
    url = git.origin_url(repo) if repo else None
    return repo_key(url) if url else None


def orphan_tg(ctx, repo) -> int | None:
    """Ramo tg/<N>-* senza lavoro attivo per (repo, N): DB perso, serve adopt (12.4)."""
    if repo is None:
        return None
    m = _TG.match(git.branch(repo) or "")
    if not m:
        return None
    key = repo_key_of(repo)
    row = ctx.db.execute("SELECT 1 FROM work_items WHERE repo_key = ? AND issue = ? "
                         "AND phase <> 'closed'", (key, int(m.group(1)))).fetchone()
    return None if row else int(m.group(1))


def governing_work(ctx, path):
    """Le regole complete valgono nella sessione legata e per ogni percorso nel worktree (6.6)."""
    if ctx.bound and ctx.work is not None:
        return ctx.work
    return ctx.work_for_path(path) if path is not None else None


def is_docs_md(rel: str | None) -> bool:
    return bool(rel) and rel.startswith("docs/superpowers/") and rel.endswith(".md")


def locked_docs(work) -> set[str]:
    """Spec bloccata dopo approve spec, piano bloccato dopo la registrazione dello scope (6.2)."""
    out = set()
    if work["plan_sha"] and work["plan_path"]:
        out.add(work["plan_path"])
    if work["spec_path"] and work["worktree"]:
        approval = Path(work["worktree"]) / f"docs/superpowers/reviews/{work['issue']}" \
                                           "/spec-approval.md"
        if approval.exists():
            out.add(work["spec_path"])
    return out


def waiver_hint(v, issue) -> str:
    target = f"--test {' --test '.join(v.ids)} " if v.ids else ""
    return (f"tollgate waiver add {v.waiver_type} {v.path} {target}"
            f"--choice … --why … --cost …")


def explain(violations, issue) -> str:
    lines = [f"- {v.path}: {v.detail} (deroga: {waiver_hint(v, issue)})" for v in violations]
    return "\n".join(lines)


def status_lines(ctx, work) -> list[str]:
    lines = [f"tollgate: lavoro #{work['issue']} ({work['level']}), fase {work['phase']}"
             + (f" (prima: {work['phase_before_block']})" if work["phase"] == "blocked" else "")]
    for b in ctx.db.execute("SELECT id, type, reason FROM blocks WHERE work = ? AND closed "
                            "IS NULL ORDER BY id LIMIT 3", (work["id"],)):
        lines.append(f"blocco {b['id']} ({b['type']}): {b['reason'][:120]}")
    counts = {r[0]: r[1] for r in ctx.db.execute(
        "SELECT state, count(*) FROM tasks WHERE work = ? GROUP BY state", (work["id"],))}
    if counts:
        lines.append("task: " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    return lines
```

- [ ] **Step 4: `session.py`**

```python
"""SessionStart (spec 7.2): legame, subagenti di sessioni morte, stato e checkpoint."""
from __future__ import annotations

from pathlib import Path

from tollgate_core import sessions, subagents
from tollgate_hooks.model import inject, record

from ._common import orphan_tg, status_lines

CHECK = {"api": 1, "events": ["session_start"], "component": None, "order": 10}


def decide(event, ctx):
    out = [record("expire_acts")]
    for row in subagents.running(ctx.db):
        if row["session"] and row["session"] != event.session and not sessions.alive(
                ctx.db, row["session"], now=ctx.now, stale_minutes=ctx.stale_minutes):
            out.append(record("subagent_interrupt", agent_id=row["id"]))
    work = ctx.work
    if work is not None and not ctx.bound:
        path_work = ctx.work_for_path(event.cwd)
        if path_work is not None and path_work["id"] == work["id"]:
            out.append(record("bind", work=work["id"]))
    if work is None:
        n = orphan_tg(ctx, ctx.repo)
        if n is not None:
            out.append(inject(f"tollgate: ramo tg/{n}-* senza lavoro nel DB (DB perso?). Le "
                              f"scritture sono negate finché l'utente non lancia "
                              f"/tollgate:adopt #{n}."))
        return out
    lines = status_lines(ctx, work)
    if work["worktree"]:
        cp = Path(work["worktree"]) / f"docs/superpowers/reviews/{work['issue']}/checkpoint.md"
        try:
            lines += ["checkpoint:"] + cp.read_text(encoding="utf-8").strip().splitlines()
        except OSError:
            pass
    out.append(inject("\n".join(lines)))
    return out
```

- [ ] **Step 5: `acts.py`**

```python
"""UserPromptExpansion (spec 8.4): l'atto da command_name (forma lunga) e command_args."""
from __future__ import annotations

import shlex
from pathlib import Path

from tollgate_core import acts, git
from tollgate_hooks.model import inject, record

CHECK = {"api": 1, "events": ["prompt_expansion"], "component": None, "order": 10}
_TARGET_ARG = {"waiver", "effect", "finding", "level", "rounds", "spec"}


def _refuse(why: str):
    return [inject(f"tollgate: atto non registrato: {why}")]


def decide(event, ctx):
    name = str(event.raw.get("command_name") or "")
    if not name.startswith("tollgate:"):
        return []
    type_ = name.split(":", 1)[1]
    if type_ in ("off", "on") or type_ not in acts.ACT_TYPES:
        return []
    raw_args = str(event.raw.get("command_args") or "")
    try:
        args = shlex.split(raw_args)
    except ValueError:
        args = raw_args.split()
    work = ctx.work if ctx.bound else None
    work_id = work["id"] if work is not None else None
    head = git.head(Path(work["worktree"])) if work is not None and work["worktree"] else None
    obj = target = None
    if type_ == "finish":
        if work is None or not head:
            return _refuse("/tollgate:finish vale solo in una sessione legata a un lavoro")
    elif type_ == "approve":
        if not args or args[0] not in acts.APPROVE_OBJECTS:
            return _refuse(f"oggetto di approve sconosciuto: {args[0] if args else '(vuoto)'}")
        obj = args[0]
        if obj in _TARGET_ARG:
            if len(args) < 2:
                return _refuse(f"approve {obj} richiede un argomento")
            target = args[1]
        elif obj == "pr":
            if not head:
                return _refuse("approve pr vale solo in una sessione legata a un lavoro")
            target = head
    elif type_ == "reopen":
        if not args or args[0] not in ("spec", "plan"):
            return _refuse("reopen vuole spec o plan e un motivo")
        obj = args[0]
    elif type_ == "resolve":
        if not args:
            return _refuse("resolve vuole l'identificativo del blocco")
        target = args[0]
    elif type_ in ("adopt", "abandon"):
        if not args or not args[0].lstrip("#").isdigit():
            return _refuse(f"{type_} vuole il numero dell'issue (#N)")
        target = args[0].lstrip("#")
    if type_ in ("adopt", "cleanup"):
        work_id = None
    typed = str(event.raw.get("prompt") or f"/{name} {raw_args}".strip())
    label = " ".join(x for x in (type_, obj, target) if x)
    return [record("expire_acts"),
            record("act", type=type_, object=obj, target=target, args=args, typed_text=typed,
                   work=work_id, head_sha=head if type_ == "finish" else None),
            inject(f"tollgate: atto registrato ({label})")]
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_checks/_common.py bin/tollgate_checks/session.py bin/tollgate_checks/acts.py tests/test_check_session.py tests/test_check_acts.py
git commit -m "tollgate P2: controlli di SessionStart e degli atti dell'utente"
```

---
