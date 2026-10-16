### Task 2: Migrazione 2, sessioni, subagenti, assegnazione dei task

**Files:**
- Modify: `bin/tollgate_core/db.py` (dopo `SCHEMA_V1`, e `MIGRATIONS`)
- Create: `bin/tollgate_core/sessions.py`
- Create: `bin/tollgate_core/subagents.py`
- Modify: `bin/tollgate_core/tasks.py`
- Modify: `tests/test_db.py:39,56` (versione attesa da `"1"` a `str(db.latest_version())`)
- Test: `tests/test_sessions.py`, `tests/test_subagents.py`, `tests/test_tasks.py`, `tests/test_db.py`

**Interfaces:**
- Consumes: `db.open_db`, `db.tx`, `db.backup`, `events.record_event`, `phases.create_work`, `phases.bind_session`, `phases.get_work`, `tasks.task_event`, `clock`.
- Produces:
  - `db.latest_version() == 2`.
  - `sessions.touch(conn, session: str, *, now) -> None`; `sessions.alive(conn, session, *, now, stale_minutes: int) -> bool`; `sessions.bound_work(conn, session) -> Row | None`; `sessions.work_for_path(conn, path) -> Row | None`; `sessions.mark_bound(state, session) -> None`; `sessions.BOUND_DIR = "bound"`.
  - `subagents.start(conn, *, agent_id, type_, session, work, task, base_sha, fingerprint, now) -> bool` (vero se ripresa); `subagents.touch(conn, agent_id, *, now)`; `subagents.set_name(conn, agent_id, name, *, session, work, now)`; `subagents.set_report(conn, agent_id, text)`; `subagents.add_veto(conn, agent_id) -> int`; `subagents.finish(conn, agent_id, *, state, now, declared_status=None, tokens=None, session=None)`; `subagents.get(conn, agent_id) -> Row | None`; `subagents.by_name(conn, name, *, work) -> Row | None`; `subagents.running(conn, *, work=None) -> list[Row]`; `subagents.interrupt(conn, agent_id, *, now, session=None)`; `subagents.STATES`.
  - `tasks.assign(conn, work, number, *, implementer, agent_type, pending, reviewer_type=None, now, session=None)`; `tasks.take_pending(conn, work, *, agent_type, resume: bool) -> int | None`; `tasks.add_commit(conn, work, number, sha)`; `tasks.PENDING = ("launch", "resume")`.

- [ ] **Step 1: Test della migrazione**

In `tests/test_db.py` sostituire `"1"` con `str(db.latest_version())` nelle due asserzioni sulla versione (righe 39 e 56) e aggiungere:

```python
class MigrationV2Test(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()

    def tearDown(self):
        self.ts.cleanup()

    def test_from_v1_adds_columns_and_backup(self):
        saved = db.MIGRATIONS[:]
        try:
            db.MIGRATIONS[:] = saved[:1]
            db.open_db(self.ts.state).close()
        finally:
            db.MIGRATIONS[:] = saved
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "2")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(subagents)")}
            self.assertTrue({"last_seen", "vetoes", "report"} <= cols)
            self.assertIn("pending", {r[1] for r in conn.execute("PRAGMA table_info(tasks)")})
            self.assertIn("level_cap_paths",
                          {r[1] for r in conn.execute("PRAGMA table_info(work_items)")})
            conn.execute("SELECT session, last_seen FROM session_seen").fetchall()
        finally:
            conn.close()
        self.assertTrue(list(self.ts.state.backup_dir.glob("tollgate-*-migrazione-2.db")))
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_db -v`
Expected: FAIL in `test_from_v1_adds_columns_and_backup` (versione `"1"`).

- [ ] **Step 3: Migrazione**

In `bin/tollgate_core/db.py`, dopo `SCHEMA_V1`:

```python
# Migrazione 2 (piano P2, decisione 7): dati che servono agli hook.
SCHEMA_V2 = [
    "CREATE TABLE session_seen (session TEXT PRIMARY KEY, last_seen TEXT NOT NULL)",
    "ALTER TABLE subagents ADD COLUMN last_seen TEXT",
    "ALTER TABLE subagents ADD COLUMN vetoes INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE subagents ADD COLUMN report TEXT",
    "ALTER TABLE tasks ADD COLUMN pending TEXT "
    "CHECK (pending IS NULL OR pending IN ('launch','resume'))",
    "ALTER TABLE work_items ADD COLUMN level_cap_paths TEXT NOT NULL DEFAULT '[]'",
    "CREATE INDEX subagents_work ON subagents(work, state)",
]

MIGRATIONS: list[tuple[int, list[str]]] = [(1, SCHEMA_V1), (2, SCHEMA_V2)]
```

(sostituisce la riga `MIGRATIONS` esistente).

- [ ] **Step 4: Verificare che passi**

Run: `python3 -B -m unittest tests.test_db -v`
Expected: PASS.

- [ ] **Step 5: Test di sessioni e subagenti**

`tests/test_sessions.py`:

```python
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.helpers import TempState
from tollgate_core import db, phases, sessions

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class SessionsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_alive_by_last_seen(self):
        sessions.touch(self.conn, "s1", now=T0)
        self.assertTrue(sessions.alive(self.conn, "s1", now=T0 + timedelta(minutes=29),
                                       stale_minutes=30))
        self.assertFalse(sessions.alive(self.conn, "s1", now=T0 + timedelta(minutes=31),
                                        stale_minutes=30))
        self.assertFalse(sessions.alive(self.conn, "mai-vista", now=T0, stale_minutes=30))

    def test_bound_work_and_path(self):
        wt = self.ts.dir / "wt 7"
        (wt / "src").mkdir(parents=True)
        w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                               session="s1", worktree=str(wt))
        self.assertEqual(sessions.bound_work(self.conn, "s1")["id"], w)
        self.assertIsNone(sessions.bound_work(self.conn, "s2"))
        self.assertEqual(sessions.work_for_path(self.conn, wt / "src" / "nuovo.py")["id"], w)
        self.assertIsNone(sessions.work_for_path(self.conn, self.ts.dir / "altro"))

    def test_closed_work_is_not_bound(self):
        w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                               session="s1")
        phases.set_phase(self.conn, self.ts.state, w, "closed", "abandoned", now=T0)
        self.assertIsNone(sessions.bound_work(self.conn, "s1"))

    def test_mark_bound_creates_marker(self):
        sessions.mark_bound(self.ts.state, "s1")
        self.assertTrue((self.ts.dir / sessions.BOUND_DIR / "s1").is_file())
        sessions.mark_bound(self.ts.state, "../fuori")
        self.assertFalse((self.ts.dir / "fuori").exists())


if __name__ == "__main__":
    unittest.main()
```

`tests/test_subagents.py`:

```python
import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import TempState
from tollgate_core import db, phases, subagents, tasks

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class SubagentsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0,
                                    session="s1")
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def _start(self, now=T0):
        return subagents.start(self.conn, agent_id="a1", type_="tollgate:implementer",
                               session="s1", work=self.w, task=1, base_sha="b0",
                               fingerprint="f0", now=now)

    def test_start_then_resume_keeps_base(self):
        self.assertFalse(self._start())
        subagents.finish(self.conn, "a1", state="done", declared_status="NEEDS_CONTEXT", now=T0)
        resumed = subagents.start(self.conn, agent_id="a1", type_="tollgate:implementer",
                                  session="s1", work=self.w, task=1, base_sha="b9",
                                  fingerprint="f9", now=T0 + timedelta(minutes=1))
        self.assertTrue(resumed)
        row = subagents.get(self.conn, "a1")
        self.assertEqual((row["agent_base_sha"], row["resumes"], row["state"]), ("b0", 1, "running"))
        self.assertIsNone(row["ended"])

    def test_name_before_start_is_merged(self):
        subagents.set_name(self.conn, "a1", "tg-7-t1", session="s1", work=self.w, now=T0)
        self._start()
        self.assertEqual(subagents.by_name(self.conn, "tg-7-t1", work=self.w)["id"], "a1")

    def test_vetoes_and_report(self):
        self._start()
        self.assertEqual(subagents.add_veto(self.conn, "a1"), 1)
        self.assertEqual(subagents.add_veto(self.conn, "a1"), 2)
        subagents.set_report(self.conn, "a1", "testo")
        self.assertEqual(subagents.get(self.conn, "a1")["report"], "testo")

    def test_interrupt_returns_running_task_to_pending(self):
        tasks.task_event(self.conn, self.w, 1, "start", now=T0)
        self._start()
        subagents.interrupt(self.conn, "a1", now=T0 + timedelta(hours=1))
        self.assertEqual(subagents.get(self.conn, "a1")["state"], "interrupted")
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["state"], "pending")
        self.assertEqual(subagents.running(self.conn, work=self.w), [])

    def test_finish_records_event(self):
        self._start()
        subagents.finish(self.conn, "a1", state="done", declared_status="DONE", tokens=123, now=T0)
        ev = self.conn.execute("SELECT data FROM events WHERE type='subagent_stop'").fetchone()
        self.assertIn('"tokens": 123', ev["data"])

    def test_unknown_state_rejected(self):
        self._start()
        with self.assertRaises(ValueError):
            subagents.finish(self.conn, "a1", state="boh", now=T0)


if __name__ == "__main__":
    unittest.main()
```

In `tests/test_tasks.py` aggiungere:

```python
class AssignTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)
        self.w = phases.create_work(self.conn, repo_key="r", issue=7, level="L1", now=T0)
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_assign_and_take_launch(self):
        tasks.assign(self.conn, self.w, 1, implementer="tg-7-t1", agent_type="tollgate:implementer",
                     pending="launch", now=T0)
        self.assertIsNone(tasks.take_pending(self.conn, self.w, agent_type="general-purpose",
                                             resume=False))
        self.assertIsNone(tasks.take_pending(self.conn, self.w, agent_type="tollgate:implementer",
                                             resume=True))
        self.assertEqual(tasks.take_pending(self.conn, self.w, agent_type="tollgate:implementer",
                                            resume=False), 1)
        self.assertIsNone(tasks.get_task(self.conn, self.w, 1)["pending"])

    def test_assign_rejects_unknown_pending(self):
        with self.assertRaises(ValueError):
            tasks.assign(self.conn, self.w, 1, implementer="x", agent_type="y", pending="boh",
                         now=T0)

    def test_add_commit_dedup(self):
        tasks.add_commit(self.conn, self.w, 1, "abc")
        tasks.add_commit(self.conn, self.w, 1, "abc")
        self.assertEqual(tasks.get_task(self.conn, self.w, 1)["commits"], '["abc"]')
```

(Se `tests/test_tasks.py` non definisce già `T0`, `TempState`, `db`, `phases`, aggiungere gli import come in `tests/test_subagents.py`.)

- [ ] **Step 6: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_sessions tests.test_subagents tests.test_tasks -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_core.sessions'` e `AttributeError: module 'tollgate_core.tasks' has no attribute 'assign'`.

- [ ] **Step 7: `sessions.py`**

```python
"""Sessioni viste dagli hook, sessione viva e lavoro legato (spec 0, 6.6, 12.4)."""
from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

from . import clock, db
from .paths import State, ensure_dirs

BOUND_DIR = "bound"
_SAFE = re.compile(r"^[A-Za-z0-9_-]+$")


def touch(conn, session: str, *, now) -> None:
    with db.tx(conn):
        conn.execute("INSERT INTO session_seen (session, last_seen) VALUES (?, ?) "
                     "ON CONFLICT(session) DO UPDATE SET last_seen = excluded.last_seen",
                     (session, clock.fmt(now)))


def alive(conn, session: str, *, now, stale_minutes: int) -> bool:
    row = conn.execute("SELECT last_seen FROM session_seen WHERE session = ?",
                       (session,)).fetchone()
    return row is not None and row[0] > clock.fmt(now - timedelta(minutes=stale_minutes))


def bound_work(conn, session: str):
    """Il lavoro attivo a cui la sessione è legata (il più recente, se più d'uno)."""
    for row in conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' "
                            "ORDER BY updated DESC, id DESC"):
        if session in json.loads(row["sessions"]):
            return row
    return None


def work_for_path(conn, path) -> object | None:
    """Il lavoro attivo il cui worktree contiene il percorso (risolto, anche se non esiste)."""
    p = Path(path).resolve()
    for row in conn.execute("SELECT * FROM work_items WHERE phase <> 'closed' "
                            "AND worktree IS NOT NULL ORDER BY id"):
        wt = Path(row["worktree"]).resolve()
        if p == wt or wt in p.parents:
            return row
    return None


def mark_bound(state: State, session: str) -> None:
    """Segnalino per il wrapper (decisione 22): la sessione è legata a un lavoro."""
    if not _SAFE.match(session):
        return
    ensure_dirs(state)
    d = state.root / BOUND_DIR
    d.mkdir(mode=0o700, exist_ok=True)
    (d / session).touch()
```

- [ ] **Step 8: `subagents.py`**

```python
"""Righe di `subagents` (spec 6.3, 7.2, 12.2): partenza, ripresa, nome, chiusura."""
from __future__ import annotations

from datetime import timedelta

from . import clock, db, tasks
from .events import record_event

STATES = ("running", "done", "cut", "budget", "interrupted", "tampered")


def get(conn, agent_id: str):
    return conn.execute("SELECT * FROM subagents WHERE id = ?", (agent_id,)).fetchone()


def start(conn, *, agent_id: str, type_: str, session: str, work: int | None,
          task: int | None, base_sha: str | None, fingerprint: str | None, now) -> bool:
    """Registra la partenza; alla ripresa (stessa riga) non tocca agent_base_sha né l'impronta."""
    ts = clock.fmt(now)
    with db.tx(conn):
        row = get(conn, agent_id)
        resumed = row is not None and row["started"] is not None
        if row is None:
            conn.execute("INSERT INTO subagents (id, type, work, task, session, agent_base_sha, "
                         "fingerprint, started, last_seen, state) "
                         "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running')",
                         (agent_id, type_, work, task, session, base_sha, fingerprint, ts, ts))
        elif not resumed:
            conn.execute("UPDATE subagents SET type = ?, work = coalesce(work, ?), task = ?, "
                         "session = ?, agent_base_sha = ?, fingerprint = ?, started = ?, "
                         "last_seen = ?, state = 'running' WHERE id = ?",
                         (type_, work, task, session, base_sha, fingerprint, ts, ts, agent_id))
        else:
            conn.execute("UPDATE subagents SET resumes = resumes + 1, state = 'running', "
                         "ended = NULL, last_seen = ?, task = coalesce(task, ?) WHERE id = ?",
                         (ts, task, agent_id))
        record_event(conn, "subagent_start", {"id": agent_id, "type": type_, "task": task,
                                              "resumed": resumed},
                     now=now, session=session, work=work)
    return resumed


def touch(conn, agent_id: str, *, now) -> None:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET last_seen = ? WHERE id = ?",
                     (clock.fmt(now), agent_id))


def set_name(conn, agent_id: str, name: str, *, session: str, work: int | None, now) -> None:
    """Il nome arriva da PostToolUse Agent, che in background può precedere SubagentStart."""
    with db.tx(conn):
        if get(conn, agent_id) is None:
            conn.execute("INSERT INTO subagents (id, name, work, session, last_seen) "
                         "VALUES (?, ?, ?, ?, ?)",
                         (agent_id, name, work, session, clock.fmt(now)))
        else:
            conn.execute("UPDATE subagents SET name = ? WHERE id = ?", (name, agent_id))


def set_report(conn, agent_id: str, text: str) -> None:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET report = ? WHERE id = ?", (text, agent_id))


def add_veto(conn, agent_id: str) -> int:
    with db.tx(conn):
        conn.execute("UPDATE subagents SET vetoes = vetoes + 1 WHERE id = ?", (agent_id,))
        row = get(conn, agent_id)
        return row["vetoes"] if row else 0


def finish(conn, agent_id: str, *, state: str, now, declared_status: str | None = None,
           tokens: int | None = None, session: str | None = None) -> None:
    if state not in STATES or state == "running":
        raise ValueError(f"stato di chiusura non ammesso: {state}")
    with db.tx(conn):
        row = get(conn, agent_id)
        if row is None:
            raise ValueError(f"subagente {agent_id} sconosciuto")
        started = clock.parse(row["started"]) if row["started"] else now
        conn.execute("UPDATE subagents SET ended = ?, state = ?, declared_status = ?, "
                     "tokens = coalesce(?, tokens), duration = ? WHERE id = ?",
                     (clock.fmt(now), state, declared_status, tokens,
                      (now - started).total_seconds(), agent_id))
        record_event(conn, "subagent_stop",
                     {"id": agent_id, "type": row["type"], "task": row["task"],
                      "declared_status": declared_status, "tokens": tokens, "state": state},
                     now=now, session=session or row["session"], work=row["work"])


def by_name(conn, name: str, *, work: int | None):
    return conn.execute("SELECT * FROM subagents WHERE name = ? AND work IS ? "
                        "ORDER BY coalesce(started, last_seen) DESC LIMIT 1",
                        (name, work)).fetchone()


def running(conn, *, work: int | None = None) -> list:
    sql, params = "SELECT * FROM subagents WHERE state = 'running'", []
    if work is not None:
        sql += " AND work = ?"
        params.append(work)
    return conn.execute(sql + " ORDER BY started", params).fetchall()


def is_stale(row, *, now, stale_minutes: int) -> bool:
    seen = row["last_seen"] or row["started"]
    return seen is not None and seen <= clock.fmt(now - timedelta(minutes=stale_minutes))


def interrupt(conn, agent_id: str, *, now, session: str | None = None) -> None:
    """Un implementatore interrotto riporta il suo task a pending senza consumare un giro."""
    with db.tx(conn):
        row = get(conn, agent_id)
        if row is None or row["state"] != "running":
            return
        conn.execute("UPDATE subagents SET state = 'interrupted', ended = ? WHERE id = ?",
                     (clock.fmt(now), agent_id))
        if row["work"] is not None and row["task"] is not None:
            t = conn.execute("SELECT state FROM tasks WHERE work = ? AND number = ?",
                             (row["work"], row["task"])).fetchone()
            if t is not None and t["state"] == "running":
                tasks.task_event(conn, row["work"], row["task"], "interrupted", now=now,
                                 session=session)
        record_event(conn, "subagent_stop", {"id": agent_id, "type": row["type"],
                                             "task": row["task"], "declared_status": None,
                                             "tokens": None, "state": "interrupted"},
                     now=now, session=session or row["session"], work=row["work"])
```

- [ ] **Step 9: `tasks.py`**

Aggiungere in fondo a `bin/tollgate_core/tasks.py`:

```python
PENDING = ("launch", "resume")


def assign(conn, work: int, number: int, *, implementer: str, agent_type: str, pending: str,
           reviewer_type: str | None = None, now, session=None) -> None:
    """Scritto da `task start` (P3): chi può partire o riprendere su questo task (6.3)."""
    if pending not in PENDING:
        raise ValueError(f"pending sconosciuto: {pending}")
    with db.tx(conn):
        row = get_task(conn, work, number)
        conn.execute("UPDATE tasks SET implementer = ?, agent_type = ?, reviewer_type = ?, "
                     "pending = ? WHERE work = ? AND number = ?",
                     (implementer, agent_type, reviewer_type, pending, work, number))
        _log(conn, row, now=now, session=session)


def take_pending(conn, work: int, *, agent_type: str, resume: bool) -> int | None:
    """Associa un subagente che parte (o riprende) al task in sospeso del suo tipo."""
    want = "resume" if resume else "launch"
    with db.tx(conn):
        row = conn.execute("SELECT number FROM tasks WHERE work = ? AND pending = ? "
                           "AND agent_type = ? ORDER BY number LIMIT 1",
                           (work, want, agent_type)).fetchone()
        if row is None:
            return None
        conn.execute("UPDATE tasks SET pending = NULL WHERE work = ? AND number = ?",
                     (work, row["number"]))
        return row["number"]


def add_commit(conn, work: int, number: int, sha: str) -> None:
    with db.tx(conn):
        commits = json.loads(get_task(conn, work, number)["commits"])
        if sha not in commits:
            commits.append(sha)
            conn.execute("UPDATE tasks SET commits = ? WHERE work = ? AND number = ?",
                         (json.dumps(commits), work, number))
```

- [ ] **Step 10: Verificare che passino e suite completa**

Run: `tests/run`
Expected: tutti i test OK su entrambe le versioni.

- [ ] **Step 11: Commit**

```bash
git add bin/tollgate_core/db.py bin/tollgate_core/sessions.py bin/tollgate_core/subagents.py bin/tollgate_core/tasks.py tests/test_db.py tests/test_sessions.py tests/test_subagents.py tests/test_tasks.py
git commit -m "tollgate P2: migrazione 2, sessioni, subagenti, assegnazione dei task"
```

---
