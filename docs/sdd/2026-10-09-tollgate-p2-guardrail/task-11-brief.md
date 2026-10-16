### Task 11: Sottocomandi `waiver add` e `block open`

**Files:**
- Create: `bin/tollgate_core/waiver_cli.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomandi `waiver add`, `block open`)
- Test: `tests/test_waiver_cli.py`

**Interfaces:**
- Consumes: `waivers.*`, `sessions.work_for_path`, `phases.open_block`, `events.record_event`, `git.toplevel`.
- Produces:
  - `waiver_cli.add_waiver(state, cwd, *, type_, file=None, pattern=None, tests=(), choice, why, cost, now=None) -> str` (id della deroga; `UsageError` su errori d'uso).
  - `waiver_cli.open_block_cmd(state, cwd, *, type_, reason, now=None) -> int`.
  - CLI: `tollgate waiver add <tipo> [<file>] [--pattern G] [--test ID]... --choice T --why T --cost T`; `tollgate block open <tipo> --reason T`.

- [ ] **Step 1: Test**

`tests/test_waiver_cli.py`:

```python
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.helpers import TempState, git, make_repo
from tollgate_analysis import waivers
from tollgate_core import db, phases, waiver_cli
from tollgate_core.cli import UsageError

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class WaiverCliTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-waiver-"))
        self.wt = make_repo(self.tmp / "wt")
        (self.wt / "a").write_text("x")
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-qm", "x")
        conn = db.open_db(self.ts.state)
        self.work = phases.create_work(conn, repo_key="r", issue=7, level="L1", now=T0,
                                       worktree=str(self.wt), branch="tg/7-x")
        conn.close()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_two_waivers(self):
        w1 = waiver_cli.add_waiver(self.ts.state, self.wt / "src", type_="scope", file="src/x.py",
                                   choice="c", why="w", cost="k", now=T0)
        w2 = waiver_cli.add_waiver(self.ts.state, self.wt, type_="test", file="tests/t.py",
                                   tests=["t::a"], choice="c", why="w", cost="k", now=T0)
        self.assertEqual((w1, w2), ("w-7-1", "w-7-2"))
        wf = waivers.parse((self.wt / ".tollgate/waivers/7.toml").read_text())
        self.assertEqual((wf.issue, wf.branch, [w.id for w in wf.waivers]),
                         (7, "tg/7-x", ["w-7-1", "w-7-2"]))
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(conn.execute("SELECT count(*) FROM events WHERE type="
                                          "'waiver_added'").fetchone()[0], 2)
        finally:
            conn.close()

    def test_errors(self):
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="boh", file="a", choice="c",
                                  why="w", cost="k", now=T0)
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.wt, type_="scope", choice="c", why="w",
                                  cost="k", now=T0)
        with self.assertRaises(UsageError):
            waiver_cli.add_waiver(self.ts.state, self.tmp, type_="scope", file="a", choice="c",
                                  why="w", cost="k", now=T0)

    def test_block_open(self):
        bid = waiver_cli.open_block_cmd(self.ts.state, self.wt, type_="test_spec_conflict",
                                        reason="il test contraddice la spec", now=T0)
        conn = db.open_db(self.ts.state)
        try:
            self.assertEqual(phases.get_work(conn, self.work)["phase"], "blocked")
            self.assertEqual(conn.execute("SELECT type FROM blocks WHERE id = ?",
                                          (bid,)).fetchone()[0], "test_spec_conflict")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che fallisca**

Run: `python3 -B -m unittest tests.test_waiver_cli -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: `waiver_cli.py`**

```python
"""tollgate waiver add, tollgate block open (spec 8.3): li usa l'agente, dal worktree."""
from __future__ import annotations

from pathlib import Path

from tollgate_analysis import waivers

from . import clock, db, git, phases, sessions
from .events import record_event
from .paths import State


def _work(conn, cwd):
    from .cli import UsageError
    root = git.toplevel(cwd)
    work = sessions.work_for_path(conn, root or cwd)
    if work is None:
        raise UsageError("nessun lavoro attivo in questa cartella: lancialo dal worktree "
                         "del lavoro")
    return work


def add_waiver(state: State, cwd, *, type_: str, file: str | None = None,
               pattern: str | None = None, tests=(), choice: str, why: str, cost: str,
               now=None) -> str:
    from .cli import UsageError
    if type_ not in waivers.TYPES:
        raise UsageError(f"tipo di deroga sconosciuto: {type_} (ammessi: "
                         f"{', '.join(waivers.TYPES)})")
    if (file is None) == (pattern is None):
        raise UsageError("indica un file oppure --pattern, non entrambi")
    now = now or clock.now()
    conn = db.open_db(state)
    try:
        work = _work(conn, cwd)
        path = Path(work["worktree"]) / waivers.path_for(work["issue"])
        if path.exists():
            try:
                wf = waivers.parse(path.read_text(encoding="utf-8"))
            except ValueError as e:
                raise UsageError(f"{path}: {e}") from e
        else:
            wf = waivers.WaiverFile(work["issue"], work["branch"] or "", [])
        wid = waivers.next_id(wf)
        wf.waivers.append(waivers.Waiver(wid, type_, file, pattern, list(tests), choice, why,
                                         cost, "agent"))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(waivers.dumps(wf), encoding="utf-8")
        tmp.replace(path)
        record_event(conn, "waiver_added", {"id": wid, "type": type_}, now=now,
                     work=work["id"])
        return wid
    finally:
        conn.close()


def open_block_cmd(state: State, cwd, *, type_: str, reason: str, now=None) -> int:
    from .cli import UsageError
    if type_ not in phases.BLOCK_TYPES:
        raise UsageError(f"tipo di blocco sconosciuto: {type_}")
    conn = db.open_db(state)
    try:
        work = _work(conn, cwd)
        return phases.open_block(conn, state, work["id"], type_, reason, now=now or clock.now())
    finally:
        conn.close()
```

- [ ] **Step 4: CLI**

In `build_parser`:

```python
    wp = sub.add_parser("waiver", help="deroghe (8.3)")
    wsub = wp.add_subparsers(dest="waiver_cmd", required=True)
    wa = wsub.add_parser("add", help="dichiara una deroga in .tollgate/waivers/<N>.toml")
    wa.add_argument("type", metavar="tipo")
    wa.add_argument("file", nargs="?", metavar="file")
    wa.add_argument("--pattern", metavar="GLOB")
    wa.add_argument("--test", action="append", default=[], metavar="ID")
    wa.add_argument("--choice", required=True)
    wa.add_argument("--why", required=True)
    wa.add_argument("--cost", required=True)
    bp = sub.add_parser("block", help="blocchi del lavoro (8.3)")
    bsub = bp.add_subparsers(dest="block_cmd", required=True)
    bo = bsub.add_parser("open", help="apre un blocco; lo chiude l'utente")
    bo.add_argument("type", metavar="tipo")
    bo.add_argument("--reason", required=True)
```

In `main`, accanto a `verify`:

```python
        if args.cmd == "waiver":
            from . import waiver_cli
            print(waiver_cli.add_waiver(state, Path.cwd(), type_=args.type, file=args.file,
                                        pattern=args.pattern, tests=args.test,
                                        choice=args.choice, why=args.why, cost=args.cost))
            return 0
        if args.cmd == "block":
            from . import waiver_cli
            print(waiver_cli.open_block_cmd(state, Path.cwd(), type_=args.type,
                                            reason=args.reason))
            return 0
```

e aggiungere `phases.TransitionError` all'`except` finale di `main` (`except (db.DbError, UsageError, phases.TransitionError) as e:`).

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_core/waiver_cli.py bin/tollgate_core/cli.py tests/test_waiver_cli.py
git commit -m "tollgate P2: sottocomandi waiver add e block open"
```

---
