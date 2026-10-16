### Task 3: Scope, ricevute, effetti, registro di `OFF`, ricevuta `uncounted` nella DoD

**Files:**
- Create: `bin/tollgate_core/scope.py`
- Create: `bin/tollgate_core/receipts.py`
- Create: `bin/tollgate_core/effects.py`
- Create: `bin/tollgate_core/offlog.py`
- Modify: `bin/tollgate_core/dod.py` (`_receipt`)
- Test: `tests/test_scope.py`, `tests/test_receipts.py`, `tests/test_effects.py`, `tests/test_offlog.py`, `tests/test_dod.py`

**Interfaces:**
- Consumes: `db.tx`, `events.record_event`, `phases.get_work`, `phases.set_phase`, `tasks.add_task`, `clock`.
- Produces:
  - `scope.paths(conn, work) -> set[str]`; `scope.register_plan(conn, state, work, *, plan_path, plan_sha, scope_paths: list[str], plan_tasks: list[tuple[int, list[str]]], advance: bool, now, session=None) -> None` (errore `ValueError` se il piano è già registrato); `scope.set_plan_path(conn, work, plan_path, *, now) -> None`.
  - `receipts.STATES`; `receipts.add(conn, *, work, sha, command, resolved_command, exit_code, tests_run, tests_skipped, duration, log, produced_by, state, now, session=None) -> int`; `receipts.latest(conn, work, sha) -> list[Row]` (l'ultima per comando); `receipts.any_since(conn, work, since: str) -> bool`.
  - `effects.effect_key(command: str, work: int | None, sha: str | None) -> str`; `effects.effect_id(key) -> str` (`e-` + 8 esadecimali); `effects.get(conn, key) -> Row | None`; `effects.request(conn, *, key, command, work, sha, now, session=None) -> None`; `effects.mark_executed(conn, *, key, act_id, now, session=None) -> None`; `effects.executed_at(row) -> str | None`.
  - `offlog.LOG_NAME = "off.log"`; `offlog.import_log(conn, state) -> int` (eventi scritti).
  - `dod._receipt` accetta `uncounted` con `allow_no_tests` e uscita 0.

- [ ] **Step 1: Test**

`tests/test_scope.py`:

```python
import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, scope, tasks

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_register_plan_l1_advances(self):
        scope.register_plan(self.conn, self.ts.state, self.w,
                            plan_path="docs/superpowers/plans/p.md", plan_sha="s1",
                            scope_paths=["src/a.py", "tests/test_a.py"],
                            plan_tasks=[(1, ["tdd"]), (2, [])], advance=True, now=T0)
        self.assertEqual(scope.paths(self.conn, self.w), {"src/a.py", "tests/test_a.py"})
        w = phases.get_work(self.conn, self.w)
        self.assertEqual((w["phase"], w["plan_path"], w["plan_sha"]),
                         ("execution", "docs/superpowers/plans/p.md", "s1"))
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["skills_required"], '["tdd"]')
        self.assertEqual(self.conn.execute(
            "SELECT count(*) FROM events WHERE type='scope_registered'").fetchone()[0], 1)

    def test_register_twice_rejected_and_scope_unchanged(self):
        scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md", plan_sha="s1",
                            scope_paths=["a"], plan_tasks=[(1, [])], advance=False, now=T0)
        with self.assertRaises(ValueError):
            scope.register_plan(self.conn, self.ts.state, self.w, plan_path="p.md",
                                plan_sha="s2", scope_paths=["a", "b"], plan_tasks=[(1, [])],
                                advance=False, now=T0)
        self.assertEqual(scope.paths(self.conn, self.w), {"a"})

    def test_set_plan_path_only_once(self):
        scope.set_plan_path(self.conn, self.w, "p.md", now=T0)
        scope.set_plan_path(self.conn, self.w, "altro.md", now=T0)
        self.assertEqual(phases.get_work(self.conn, self.w)["plan_path"], "p.md")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_receipts.py`:

```python
import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import clock, db, phases, receipts

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


def add(conn, work, command, state, at, sha="h1", exit_code=0):
    return receipts.add(conn, work=work, sha=sha, command=command, resolved_command=command,
                        exit_code=exit_code, tests_run=3, tests_skipped=0, duration=1.0,
                        log="/tmp/x.log", produced_by="verify", state=state, now=at)


class ReceiptsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_latest_per_command(self):
        add(self.conn, self.w, "verify", "red", T0)
        add(self.conn, self.w, "verify", "green", T0 + timedelta(seconds=1))
        add(self.conn, self.w, "lint", "green", T0)
        got = {r["command"]: r["state"] for r in receipts.latest(self.conn, self.w, "h1")}
        self.assertEqual(got, {"verify": "green", "lint": "green"})
        ev = self.conn.execute("SELECT count(*) FROM events WHERE type='receipt'").fetchone()[0]
        self.assertEqual(ev, 3)

    def test_any_since(self):
        add(self.conn, self.w, "verify", "red", T0)
        self.assertTrue(receipts.any_since(self.conn, self.w, clock.fmt(T0 - timedelta(1))))
        self.assertFalse(receipts.any_since(self.conn, self.w, clock.fmt(T0 + timedelta(1))))

    def test_unknown_state(self):
        with self.assertRaises(ValueError):
            add(self.conn, self.w, "verify", "boh", T0)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_effects.py`:

```python
import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, effects

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_id_is_deterministic(self):
        k1 = effects.effect_key("npm publish", None, "abc")
        self.assertEqual(k1, effects.effect_key("npm publish", None, "abc"))
        self.assertNotEqual(k1, effects.effect_key("npm publish", None, "def"))
        self.assertRegex(effects.effect_id(k1), r"^e-[0-9a-f]{8}$")

    def test_request_execute_request_again(self):
        k = effects.effect_key("npm publish", None, "abc")
        effects.request(self.conn, key=k, command="npm publish", work=None, sha="abc",
                        now=T0, session="s1")
        self.assertEqual(effects.get(self.conn, k)["state"], "requested")
        self.assertIsNone(effects.executed_at(effects.get(self.conn, k)))
        effects.mark_executed(self.conn, key=k, act_id="a-3", now=T0, session="s1")
        self.assertEqual(effects.get(self.conn, k)["state"], "executed")
        effects.request(self.conn, key=k, command="npm publish", work=None, sha="abc",
                        now=T0, session="s1")
        row = effects.get(self.conn, k)
        self.assertEqual(row["state"], "requested")
        self.assertEqual(effects.executed_at(row), "2026-10-09T10:00:00.000000Z")
        types = [r[0] for r in self.conn.execute("SELECT type FROM events ORDER BY seq")]
        self.assertEqual(types, ["effect_requested", "effect_executed", "effect_requested"])


if __name__ == "__main__":
    unittest.main()
```

`tests/test_offlog.py`:

```python
import unittest

from tests.helpers import TempState
from tollgate_core import db, offlog


class OffLogTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_import_keeps_original_times_and_empties_log(self):
        (self.ts.dir / offlog.LOG_NAME).write_text(
            "2026-10-09T08:00:00.000000Z off 1791540000\n"
            "riga rovinata\n"
            "2026-10-09T09:00:00.000000Z on\n")
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 2)
        rows = self.conn.execute("SELECT type, at, data FROM events ORDER BY seq").fetchall()
        self.assertEqual([(r[0], r[1]) for r in rows],
                         [("off", "2026-10-09T08:00:00.000000Z"),
                          ("on", "2026-10-09T09:00:00.000000Z")])
        self.assertIn('"until": 1791540000', rows[0][2])
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)

    def test_no_log(self):
        self.assertEqual(offlog.import_log(self.conn, self.ts.state), 0)


if __name__ == "__main__":
    unittest.main()
```

In `tests/test_dod.py` aggiungere (con gli import di `receipts` e dell'ora `T0` del file):

```python
class UncountedTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=1, level="L0", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _receipt(self, exit_code):
        receipts.add(self.conn, work=self.w, sha="h", command="verify", resolved_command="x",
                     exit_code=exit_code, tests_run=None, tests_skipped=None, duration=0.1,
                     log=None, produced_by="verify", state="uncounted", now=T0)

    def test_uncounted_ok_only_with_allow_no_tests_and_exit_zero(self):
        self._receipt(0)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=True,
                               required_commands=["verify"])[0]
        self.assertTrue(item.ok)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=False,
                               required_commands=["verify"])[0]
        self.assertFalse(item.ok)

    def test_uncounted_with_failure_is_red(self):
        self._receipt(1)
        item = dod.compute_dod(self.conn, self.w, head_sha="h", allow_no_tests=True,
                               required_commands=["verify"])[0]
        self.assertFalse(item.ok)
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_scope tests.test_receipts tests.test_effects tests.test_offlog tests.test_dod -v`
Expected: FAIL con `ModuleNotFoundError` per `scope`, `receipts`, `effects`, `offlog`.

- [ ] **Step 3: `scope.py`**

```python
"""Scope del piano e registrazione del piano (spec 7.5, 6.2)."""
from __future__ import annotations

from . import clock, db, phases, tasks
from .events import record_event


def paths(conn, work: int) -> set[str]:
    return {r[0] for r in conn.execute("SELECT path FROM scope WHERE work = ?", (work,))}


def set_plan_path(conn, work: int, plan_path: str, *, now) -> None:
    """In L2 il piano si registra come percorso; scope e plan_sha arrivano con approve plan."""
    with db.tx(conn):
        conn.execute("UPDATE work_items SET plan_path = ?, updated = ? "
                     "WHERE id = ? AND plan_path IS NULL", (plan_path, clock.fmt(now), work))


def register_plan(conn, state, work: int, *, plan_path: str, plan_sha: str,
                  scope_paths: list[str], plan_tasks: list[tuple[int, list[str]]],
                  advance: bool, now, session=None) -> None:
    """Scope e task dal piano; una volta registrato lo scope non cresce (7.5)."""
    with db.tx(conn):
        row = phases.get_work(conn, work)
        if row["plan_sha"] is not None:
            raise ValueError("piano già registrato: per cambiarlo serve /tollgate:reopen plan")
        ts = clock.fmt(now)
        conn.execute("UPDATE work_items SET plan_path = ?, plan_sha = ?, updated = ? "
                     "WHERE id = ?", (plan_path, plan_sha, ts, work))
        for p in dict.fromkeys(scope_paths):
            conn.execute("INSERT INTO scope (work, path, origin, registered_at) "
                         "VALUES (?, ?, 'plan', ?)", (work, p, ts))
        for number, skills in plan_tasks:
            tasks.add_task(conn, work, number, source="plan", skills_required=skills, now=now,
                           session=session)
        record_event(conn, "scope_registered",
                     {"count": len(set(scope_paths)), "plan": plan_path, "plan_sha": plan_sha},
                     now=now, session=session, work=work)
    if advance:
        phases.set_phase(conn, state, work, "execution", "advance", now=now, session=session)
```

- [ ] **Step 4: `receipts.py`**

```python
"""Ricevute locali (spec 8.1): le producono solo verify e finish check."""
from __future__ import annotations

from . import clock, db
from .events import record_event

STATES = ("green", "red", "empty", "uncounted", "unverified")


def add(conn, *, work: int | None, sha: str, command: str, resolved_command: str | None,
        exit_code: int | None, tests_run: int | None, tests_skipped: int | None,
        duration: float | None, log: str | None, produced_by: str, state: str, now,
        session=None) -> int:
    if state not in STATES:
        raise ValueError(f"stato di ricevuta sconosciuto: {state}")
    with db.tx(conn):
        cur = conn.execute(
            "INSERT INTO receipts (work, sha, command, resolved_command, exit, tests_run, "
            "tests_skipped, duration, log, produced_by, state, at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (work, sha, command, resolved_command, exit_code, tests_run, tests_skipped,
             duration, log, produced_by, state, clock.fmt(now)))
        record_event(conn, "receipt", {"sha": sha, "command": command, "state": state,
                                       "tests_run": tests_run},
                     now=now, session=session, work=work)
        return cur.lastrowid


def latest(conn, work: int | None, sha: str) -> list:
    return conn.execute(
        "SELECT r.* FROM receipts r WHERE r.work IS ? AND r.sha = ? AND r.id = "
        "(SELECT max(id) FROM receipts x WHERE x.work IS r.work AND x.sha = r.sha "
        "AND x.command = r.command) ORDER BY r.command", (work, sha)).fetchall()


def any_since(conn, work: int, since: str) -> bool:
    return conn.execute("SELECT 1 FROM receipts WHERE work = ? AND at >= ? LIMIT 1",
                        (work, since)).fetchone() is not None
```

- [ ] **Step 5: `effects.py`**

```python
"""Effetti esterni come intenti (spec 8.5): veto, atto, una esecuzione, avviso se ripetuto."""
from __future__ import annotations

import hashlib
import json

from . import clock, db
from .events import record_event


def effect_key(command: str, work: int | None, sha: str | None) -> str:
    raw = f"{command}\0{'' if work is None else work}\0{sha or ''}"
    return hashlib.sha256(raw.encode("utf-8", "surrogateescape")).hexdigest()


def effect_id(key: str) -> str:
    return f"e-{key[:8]}"


def get(conn, key: str):
    return conn.execute("SELECT * FROM intents WHERE idempotency_key = ?",
                        (f"effect:{key}",)).fetchone()


def executed_at(row) -> str | None:
    return json.loads(row["data"] or "{}").get("executed_at") if row else None


def request(conn, *, key: str, command: str, work: int | None, sha: str | None, now,
            session=None) -> None:
    eid = effect_id(key)
    with db.tx(conn):
        row = get(conn, key)
        if row is None:
            data = {"id": eid, "command": command, "sha": sha}
            conn.execute("INSERT INTO intents (work, action, idempotency_key, data, state, at) "
                         "VALUES (?, 'effect', ?, ?, 'requested', ?)",
                         (work, f"effect:{key}", json.dumps(data), clock.fmt(now)))
        else:
            conn.execute("UPDATE intents SET state = 'requested' WHERE id = ?", (row["id"],))
        record_event(conn, "effect_requested", {"command_hash": key, "id": eid},
                     now=now, session=session, work=work)


def mark_executed(conn, *, key: str, act_id: str, now, session=None) -> None:
    with db.tx(conn):
        row = get(conn, key)
        if row is None:
            raise ValueError(f"effetto {effect_id(key)} mai richiesto")
        data = json.loads(row["data"] or "{}")
        data["executed_at"] = clock.fmt(now)
        data["act_id"] = act_id
        conn.execute("UPDATE intents SET state = 'executed', outcome = ?, data = ? WHERE id = ?",
                     (clock.fmt(now), json.dumps(data), row["id"]))
        record_event(conn, "effect_executed", {"command_hash": key, "id": effect_id(key),
                                               "act_id": act_id},
                     now=now, session=session, work=row["work"])
```

- [ ] **Step 6: `offlog.py`**

```python
"""Import in `events` delle accensioni e degli spegnimenti scritti dal wrapper (decisione 5)."""
from __future__ import annotations

import os
import re

from . import clock
from .events import record_event
from .paths import State

LOG_NAME = "off.log"
_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z) (off|on)(?: (\d+))?\s*$")


def import_log(conn, state: State) -> int:
    log = state.root / LOG_NAME
    work_file = state.root / f".{LOG_NAME}.{os.getpid()}"
    try:
        log.rename(work_file)   # atomico: due hook insieme non importano due volte
    except FileNotFoundError:
        return 0
    n = 0
    try:
        for line in work_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _LINE.match(line)
            if not m:
                continue
            data = {"until": int(m.group(3))} if m.group(3) else {}
            record_event(conn, m.group(2), data, now=clock.parse(m.group(1)))
            n += 1
    finally:
        work_file.unlink(missing_ok=True)
    return n
```

- [ ] **Step 7: `dod._receipt`**

In `bin/tollgate_core/dod.py`, `_receipt` legge anche l'uscita e accetta `uncounted` con `allow_no_tests` e uscita 0 (decisione 11):

```python
def _receipt(conn, work: int, head_sha: str, allow_no_tests: bool,
             required_commands: list[str]) -> tuple[bool, str]:
    if not required_commands:
        return False, "nessun comando richiesto"
    rows = conn.execute(
        "SELECT r.command, r.state, r.exit FROM receipts r WHERE r.work = ? AND r.sha = ? "
        "AND r.id = (SELECT max(id) FROM receipts x WHERE x.work = r.work AND x.sha = r.sha "
        "AND x.command = r.command) ORDER BY r.command", (work, head_sha)).fetchall()
    if not rows:
        return False, f"nessuna ricevuta su {head_sha}"

    def ok(r) -> bool:
        if r["state"] == "green":
            return True
        if allow_no_tests and r["state"] == "empty":
            return True
        return allow_no_tests and r["state"] == "uncounted" and r["exit"] == 0

    bad = [f"{r['command']}={r['state']}" for r in rows if not ok(r)]
    have = {r["command"] for r in rows}
    missing = [c for c in required_commands if c not in have]
    if missing:
        bad.append("mancano: " + ", ".join(missing))
    return (not bad), ", ".join(bad)
```

- [ ] **Step 8: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 9: Commit**

```bash
git add bin/tollgate_core/scope.py bin/tollgate_core/receipts.py bin/tollgate_core/effects.py bin/tollgate_core/offlog.py bin/tollgate_core/dod.py tests/test_scope.py tests/test_receipts.py tests/test_effects.py tests/test_offlog.py tests/test_dod.py
git commit -m "tollgate P2: scope, ricevute, effetti, registro di OFF; uncounted nella DoD"
```

---

