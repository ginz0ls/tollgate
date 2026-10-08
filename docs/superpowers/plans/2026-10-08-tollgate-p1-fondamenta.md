# tollgate P1: fondamenta

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire il pacchetto `tollgate_core` e il CLI `bin/tollgate` con i sottocomandi di base: cartella di stato, configurazione, DB con migrazioni e copie, eventi, fasi e blocchi, `tasks`, atti, Definition of Done, statistiche, `status`, `stats`, `events`, `db restore`.

**Architecture:** Libreria Python di sola libreria standard sotto `bin/tollgate_core/`, un modulo per responsabilità. Ogni funzione che scrive riceve una connessione SQLite e l'ora come argomenti, così i test fissano il tempo. `bin/tollgate` è un punto d'ingresso sottile che chiama `tollgate_core.cli.main`. P2-P4 useranno queste funzioni, non il DB direttamente.

**Tech Stack:** Python ≥ 3.11 (`sqlite3`, `tomllib`, `argparse`, `unittest`), git. Test con `unittest`, eseguiti con Python 3.11 (il minimo della spec) e con il `python3` di sistema (3.13).

**Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 20): sezioni 0, 2, 3, 3.1, 3.2, 6.3 (transizioni di `tasks`), 8.4, 8.7, 11.4, 12, 18.1 (forma di `acts`), 18.4; criteri 17 (parte DB), 25, 43. Piano principale: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (riga P1 e contratti della sezione 3).

## Global Constraints

- Solo libreria standard in `bin/` (spec 3: «CLI Python, solo libreria standard»). Nessuna dipendenza esterna nemmeno nei test.
- Python ≥ 3.11 (spec 2). Ogni task passa `tests/run`, che usa `python3.11` e `python3`.
- Cartella di stato: `~/.local/state/tollgate` (spec 0). Le variabili `TOLLGATE_STATE`, `TOLLGATE_GH`, `TOLLGATE_TEST_CONFIG` valgono solo se nella cartella di `TOLLGATE_STATE` c'è il file `.tollgate-test` (spec 3.1).
- SQLite in WAL, `synchronous=FULL`, `busy_timeout=5000`; copia con la API di backup a ogni cambio di fase, ultime 10 (spec 12.1).
- Migrazioni solo in avanti, con una copia prima di ciascuna (spec 12.4).
- Eventi: busta `{"v": 1, "seq", "at", "host", "session", "work", "repo_key", "issue", "type", "data"}`, `seq` monotono, sola aggiunta, unica cancellazione la potatura oltre `events_days` (spec 18.4, 12.2).
- Identificatori in inglese, messaggi all'utente in italiano (spec 0, «Lingua»).
- Nessun file `__pycache__` nel repo: `bin/tollgate` imposta `sys.dont_write_bytecode` e `tests/run` usa `-B`.
- Commit dopo ogni task.

## Decisioni di questo piano

Scelte che la spec lascia aperte, prese qui; il costo se sbagliate è indicato.

1. **La radice del repo è la radice del plugin.** Il codice va in `bin/` e `tests/` accanto a `docs/`, `spikes/` e `statusline/`, come nell'albero della spec 3 (`statusline/` c'è già). Costo se sbagliata: uno spostamento di cartelle prima di P2.
2. **Test con `unittest`, non pytest:** per girare su Python 3.11 senza installare nulla.
3. **Colonne in più rispetto a 12.2**, tutte richieste da altre sezioni della spec: `work_items.plan_sha` (6.2, 18.1), `subagents.session` (le sessioni non vive di 12.4), `acts.target`, `acts.args`, `acts.head_sha` (18.1 e l'atto `finish` legato a HEAD, 8.4), `receipts.at`. `meta` è una tabella chiave-valore.
4. **`block_opened` porta `{id, type}`**, non solo l'identificativo: `stats` deve contare i blocchi `needs_you` (criterio 43).
5. **`stats` stampa JSON.** È un comando per persone e agenti; il formato leggibile, se serve, arriva in P5 con la documentazione.
6. **`status --checkpoint` resta a P3:** scrive in `docs/superpowers/reviews/<N>/` del worktree, che crea P3. P1 consegna `status` in sola lettura.
7. **Una migrazione dal DB vuoto non fa la copia:** non c'è niente da proteggere. Dalla versione 1 in poi la copia si fa sempre.

## Review Focus

1. **Due processi che scrivono insieme** (due hook nello stesso momento): nessun `database is locked` entro `busy_timeout`, e `seq` resta strettamente crescente. Test in Task 4.
2. **File del DB guasto** (byte casuali al posto del DB): `open_db` solleva `DbCorrupt` con il comando di ripristino nel messaggio; `db restore` riporta l'ultima copia integra. Test in Task 3 e Task 10.
3. **`true` dove serve un intero** (`max_turns = true`): in Python `bool` è un `int`, e senza un controllo esplicito passerebbe. Deve essere un errore di tipo. Test in Task 2.
4. **`TOLLGATE_STATE` senza il file sentinella:** ignorata. Altrimenti un agente potrebbe dirottare il DB con una variabile d'ambiente. Test in Task 1.
5. **Un lavoro chiuso e poi riaperto sulla stessa issue:** il vincolo di unicità vale solo tra i lavori attivi, quindi un nuovo lavoro è ammesso; due attivi no. Test in Task 3.

## Mappa dei file

| File | Responsabilità |
|---|---|
| `bin/tollgate` | Punto d'ingresso: controlla Python ≥ 3.11 e chiama `tollgate_core.cli.main` |
| `bin/tollgate_core/__init__.py` | `VERSION` |
| `bin/tollgate_core/paths.py` | Cartella di stato, variabili di test, chiave del repo |
| `bin/tollgate_core/clock.py` | Ora UTC e formato delle date nel DB |
| `bin/tollgate_core/config.py` | `tollgate.toml`: valori predefiniti, tipi, chiavi sconosciute, lettura da un riferimento git |
| `bin/tollgate_core/db.py` | Apertura, schema, migrazioni, copie, integrità, ripristino |
| `bin/tollgate_core/events.py` | Registrazione, esportazione e potatura degli eventi |
| `bin/tollgate_core/phases.py` | Lavori, fasi (12.3) e blocchi |
| `bin/tollgate_core/tasks.py` | Task e transizioni di `tasks.state` (6.3) |
| `bin/tollgate_core/acts.py` | Atti dell'utente (8.4) |
| `bin/tollgate_core/dod.py` | Definition of Done (8.7) |
| `bin/tollgate_core/stats.py` | Statistiche dagli eventi (3.1, criterio 43) |
| `bin/tollgate_core/cli.py` | `status`, `stats`, `events`, `db restore`, `--version` |
| `tests/__init__.py`, `tests/helpers.py` | Percorso di import e cartella di stato temporanea con sentinella |
| `tests/run` | Esegue la suite con `python3.11` e `python3` |
| `tests/test_*.py` | Un file di test per modulo |

---

### Task 1: Scheletro, cartella di stato e chiave del repo

**Files:**
- Create: `bin/tollgate`
- Create: `bin/tollgate_core/__init__.py`
- Create: `bin/tollgate_core/paths.py`
- Create: `bin/tollgate_core/clock.py`
- Create: `bin/tollgate_core/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/helpers.py`
- Create: `tests/run`
- Test: `tests/test_paths.py`

**Interfaces:**
- Produces:
  - `tollgate_core.VERSION: str` (`"0.1.0"`).
  - `paths.State(root: Path, test_mode: bool)` con le proprietà `db_path`, `backup_dir`, `broken_dir`.
  - `paths.resolve_state(env: Mapping[str, str] | None = None) -> State`.
  - `paths.test_env(state: State, name: str, env: Mapping[str, str] | None = None) -> str | None`.
  - `paths.ensure_dirs(state: State) -> None`.
  - `paths.repo_key(url: str) -> str`.
  - `clock.now() -> datetime` (UTC, con fuso); `clock.fmt(dt: datetime) -> str`; `clock.parse(s: str) -> datetime`.
  - `cli.main(argv: list[str]) -> int`.
  - `tests.helpers.TempState` con `.dir: Path`, `.state: State`, `.env() -> dict`, `.cleanup()`; `tests.helpers.ROOT`, `tests.helpers.BIN`.

- [ ] **Step 1: Scrivere l'infrastruttura dei test**

`tests/__init__.py`:

```python
import sys
from pathlib import Path

_BIN = Path(__file__).resolve().parents[1] / "bin"
if str(_BIN) not in sys.path:
    sys.path.insert(0, str(_BIN))
```

`tests/helpers.py`:

```python
import os
import shutil
import tempfile
from pathlib import Path

from tollgate_core.paths import SENTINEL, State

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"


class TempState:
    """Cartella di stato temporanea con la sentinella dei test (spec 3.1)."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="tollgate-test-"))
        (self.dir / SENTINEL).write_text("")
        self.state = State(self.dir, True)

    def env(self):
        e = dict(os.environ)
        e["TOLLGATE_STATE"] = str(self.dir)
        return e

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)
```

`tests/run` (eseguibile, `chmod +x`):

```bash
#!/usr/bin/env bash
# Esegue la suite con Python 3.11 (minimo della spec) e con python3 di sistema.
set -euo pipefail
cd "$(dirname "$0")/.."
for py in ${PYTHONS:-python3.11 python3}; do
  command -v "$py" >/dev/null || { echo "manca $py" >&2; exit 1; }
  echo "== $("$py" --version)"
  "$py" -B -m unittest discover -s tests -t . "$@"
done
```

- [ ] **Step 2: Scrivere i test che falliscono**

`tests/test_paths.py`:

```python
import subprocess
import sys
import tempfile
import unittest
from datetime import timezone
from pathlib import Path

from tests.helpers import BIN, TempState
from tollgate_core import VERSION, clock
from tollgate_core.paths import (
    default_state_root, ensure_dirs, repo_key, resolve_state, test_env,
)


class StateTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()

    def tearDown(self):
        self.t.cleanup()

    def test_state_with_sentinel_is_test_mode(self):
        s = resolve_state({"TOLLGATE_STATE": str(self.t.dir)})
        self.assertEqual(s.root, self.t.dir)
        self.assertTrue(s.test_mode)
        self.assertEqual(s.db_path, self.t.dir / "tollgate.db")
        self.assertEqual(s.backup_dir, self.t.dir / "backup")

    def test_state_without_sentinel_is_ignored(self):
        bare = Path(tempfile.mkdtemp())
        s = resolve_state({"TOLLGATE_STATE": str(bare)})
        self.assertEqual(s.root, default_state_root())
        self.assertFalse(s.test_mode)

    def test_default_root(self):
        self.assertEqual(default_state_root(), Path.home() / ".local" / "state" / "tollgate")

    def test_test_env_only_in_test_mode(self):
        env = {"TOLLGATE_STATE": str(self.t.dir), "TOLLGATE_GH": "/tmp/fake-gh"}
        self.assertEqual(test_env(resolve_state(env), "TOLLGATE_GH", env), "/tmp/fake-gh")
        env2 = {"TOLLGATE_GH": "/tmp/fake-gh"}
        self.assertIsNone(test_env(resolve_state(env2), "TOLLGATE_GH", env2))

    def test_test_env_rejects_unknown_name(self):
        with self.assertRaises(ValueError):
            test_env(self.t.state, "PATH", {})

    def test_ensure_dirs(self):
        ensure_dirs(self.t.state)
        self.assertTrue(self.t.state.backup_dir.is_dir())


class RepoKeyTest(unittest.TestCase):
    def test_forms(self):
        cases = {
            "https://github.com/Owner/Name.git": "github.com/owner/name",
            "https://github.com/owner/name/": "github.com/owner/name",
            "git@github.com:Owner/Name.git": "github.com/owner/name",
            "ssh://git@github.com/owner/name.git": "github.com/owner/name",
            "https://user@github.com/owner/name": "github.com/owner/name",
            "https://github.com:443/owner/name.git": "github.com/owner/name",
        }
        for url, key in cases.items():
            with self.subTest(url=url):
                self.assertEqual(repo_key(url), key)


class ClockTest(unittest.TestCase):
    def test_roundtrip_and_order(self):
        a = clock.now()
        self.assertEqual(a.tzinfo, timezone.utc)
        self.assertEqual(clock.parse(clock.fmt(a)), a)
        b = clock.parse("2026-10-08T10:00:00.000000Z")
        c = clock.parse("2026-10-08T10:00:01.000000Z")
        self.assertLess(clock.fmt(b), clock.fmt(c))


class EntryPointTest(unittest.TestCase):
    def test_version(self):
        r = subprocess.run([sys.executable, str(BIN / "tollgate"), "--version"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), f"tollgate {VERSION}")
```

- [ ] **Step 3: Eseguire i test e vederli fallire**

Run: `chmod +x tests/run && tests/run`
Expected: FAIL, `ModuleNotFoundError: No module named 'tollgate_core'`.

- [ ] **Step 4: Scrivere il codice**

`bin/tollgate_core/__init__.py`:

```python
"""Libreria di base di tollgate: stato, configurazione, DB, eventi, fasi, task, atti."""

VERSION = "0.1.0"
```

`bin/tollgate_core/clock.py`:

```python
"""Ora UTC e formato unico delle date nel DB: le stringhe si confrontano in ordine."""
from datetime import datetime, timezone

_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def now() -> datetime:
    return datetime.now(timezone.utc)


def fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(_FMT)


def parse(s: str) -> datetime:
    return datetime.strptime(s, _FMT).replace(tzinfo=timezone.utc)
```

`bin/tollgate_core/paths.py`:

```python
"""Cartella di stato, variabili di test e chiave del repo (spec 0 e 3.1)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

STATE_ENV = "TOLLGATE_STATE"
SENTINEL = ".tollgate-test"
TEST_ENVS = ("TOLLGATE_STATE", "TOLLGATE_GH", "TOLLGATE_TEST_CONFIG")


@dataclass(frozen=True)
class State:
    root: Path
    test_mode: bool

    @property
    def db_path(self) -> Path:
        return self.root / "tollgate.db"

    @property
    def backup_dir(self) -> Path:
        return self.root / "backup"

    @property
    def broken_dir(self) -> Path:
        return self.root / "broken"


def default_state_root() -> Path:
    return Path.home() / ".local" / "state" / "tollgate"


def resolve_state(env: Mapping[str, str] | None = None) -> State:
    """`TOLLGATE_STATE` vale solo con la sentinella: senza, un agente potrebbe dirottare il DB."""
    env = os.environ if env is None else env
    candidate = env.get(STATE_ENV)
    if candidate and (Path(candidate) / SENTINEL).is_file():
        return State(Path(candidate), True)
    return State(default_state_root(), False)


def test_env(state: State, name: str, env: Mapping[str, str] | None = None) -> str | None:
    if name not in TEST_ENVS:
        raise ValueError(f"variabile di test sconosciuta: {name}")
    env = os.environ if env is None else env
    return env.get(name) if state.test_mode else None


def ensure_dirs(state: State) -> None:
    for d in (state.root, state.backup_dir):
        d.mkdir(mode=0o700, parents=True, exist_ok=True)


_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)


def repo_key(url: str) -> str:
    """URL di origin normalizzato: senza protocollo, utente, porta e `.git`, in minuscolo."""
    u = _SCHEME.sub("", url.strip())
    if "@" in u.split("/")[0]:
        u = u.split("@", 1)[1]
    host, _, path = u.partition("/")
    if ":" in host:
        h, _, after = host.partition(":")
        if after.isdigit():
            host = h
        else:
            host, path = h, after + ("/" + path if path else "")
    key = f"{host}/{path}".rstrip("/")
    if key.endswith(".git"):
        key = key[:-4]
    return key.lower()
```

`bin/tollgate_core/cli.py`:

```python
"""Sottocomandi di bin/tollgate (spec 3.1). P1: status, stats, events, db restore."""
from __future__ import annotations

import argparse

from . import VERSION


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tollgate")
    p.add_argument("--version", action="version", version=f"tollgate {VERSION}")
    p.add_subparsers(dest="cmd")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd is None:
        build_parser().print_help()
    return 0
```

`bin/tollgate` (eseguibile, `chmod +x`):

```python
#!/usr/bin/env python3
"""CLI di tollgate. Solo libreria standard (spec 3)."""
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    sys.stderr.write("tollgate richiede Python >= 3.11\n")
    sys.exit(2)
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tollgate_core.cli import main  # noqa: E402

sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 5: Eseguire i test e vederli passare**

Run: `chmod +x bin/tollgate && tests/run`
Expected: due blocchi (`== Python 3.11.x`, `== Python 3.13.x`), ognuno con `OK`.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate bin/tollgate_core tests
git commit -m "tollgate P1: scheletro, cartella di stato e chiave del repo"
```

---

### Task 2: Configurazione (`tollgate.toml`)

**Files:**
- Create: `bin/tollgate_core/config.py`
- Modify: `tests/helpers.py` (aggiunge `git` e `make_repo`)
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `paths.State`, `paths.test_env` (Task 1).
- Produces:
  - `config.ConfigError(Exception)`, `config.ConfigNotFound(ConfigError)`.
  - `config.Config(data: dict, warnings: list[str])` con `get(dotted: str)` (per esempio `cfg.get("tasks.max_turns")`) e la proprietà `profiles -> dict[str, dict]` (i profili dichiarati, senza `active`).
  - `config.DEFAULTS: dict`, `config.PROFILE_DEFAULTS: dict`.
  - `config.load_config_text(text: str, source: str = "tollgate.toml") -> Config`.
  - `config.load_config_at(repo: Path, ref: str) -> Config`: legge `git show <ref>:tollgate.toml`, mai il working tree (spec 3.2).
  - `config.load_config(state: State, repo: Path, ref: str, env=None) -> Config`: come `load_config_at`, ma in modalità di test `TOLLGATE_TEST_CONFIG` indica un file da usare al suo posto.
  - `tests.helpers.git(repo: Path, *args) -> str`, `tests.helpers.make_repo(path: Path) -> Path`.

Regole (spec 11.4 e 12.2): chiave o sezione sconosciuta → avviso in `warnings`; chiave nota con tipo sbagliato → `ConfigError`; `schema_version` obbligatorio e uguale a 1; `[gate] mode` obbligatorio, `protected` o `detect`. Sezioni aperte: `[commands]` accetta altri comandi (stringhe), `[components]` altri interruttori (booleani), `[profiles]` altri profili (tabelle con il contratto di `PROFILE_DEFAULTS`). I profili non hanno valori predefiniti: esistono solo quelli dichiarati.

- [ ] **Step 1: Aggiungere gli aiuti git ai test**

In fondo a `tests/helpers.py`:

```python
import subprocess


def git(repo, *args):
    r = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True)
    return r.stdout.strip()


def make_repo(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    return path
```

- [ ] **Step 2: Scrivere i test che falliscono**

`tests/test_config.py`:

```python
import tempfile
import unittest
from pathlib import Path

from tests.helpers import TempState, git, make_repo
from tollgate_core.config import (
    ConfigError, ConfigNotFound, load_config, load_config_at, load_config_text,
)

MIN = 'schema_version = 1\n[gate]\nmode = "detect"\n'


class LoadTextTest(unittest.TestCase):
    def test_minimal_gets_defaults(self):
        c = load_config_text(MIN)
        self.assertEqual(c.get("gate.mode"), "detect")
        self.assertEqual(c.get("tasks.max_turns"), 60)
        self.assertEqual(c.get("tasks.max_tokens"), {"L0": 0, "L1": 400000, "L2": 800000})
        self.assertEqual(c.get("acts.ttl_minutes"), 10)
        self.assertEqual(c.get("review.stale_minutes"), 30)
        self.assertEqual(c.get("retention.events_days"), 180)
        self.assertTrue(c.get("components.must_have_tests"))
        self.assertEqual(c.warnings, [])
        self.assertEqual(c.profiles, {})

    def test_missing_schema_version(self):
        with self.assertRaisesRegex(ConfigError, "schema_version"):
            load_config_text('[gate]\nmode = "detect"\n')

    def test_newer_schema_version(self):
        with self.assertRaisesRegex(ConfigError, "aggiornare"):
            load_config_text('schema_version = 2\n[gate]\nmode = "detect"\n')

    def test_missing_mode(self):
        with self.assertRaisesRegex(ConfigError, "gate.mode"):
            load_config_text("schema_version = 1\n")

    def test_bad_mode(self):
        with self.assertRaisesRegex(ConfigError, "gate.mode"):
            load_config_text('schema_version = 1\n[gate]\nmode = "strict"\n')

    def test_invalid_toml(self):
        with self.assertRaisesRegex(ConfigError, "TOML non valido"):
            load_config_text("schema_version = \n")

    def test_unknown_section_and_key_warn(self):
        c = load_config_text(MIN + "[nuova]\nx = 1\n[tasks]\nfoo = 2\nmax_turns = 40\n")
        self.assertIn("sezione sconosciuta: nuova", c.warnings)
        self.assertIn("chiave sconosciuta: tasks.foo", c.warnings)
        self.assertEqual(c.get("tasks.max_turns"), 40)

    def test_wrong_type_is_error(self):
        with self.assertRaisesRegex(ConfigError, "tasks.max_turns"):
            load_config_text(MIN + '[tasks]\nmax_turns = "60"\n')

    def test_bool_where_int_is_error(self):
        with self.assertRaisesRegex(ConfigError, "tasks.max_turns"):
            load_config_text(MIN + "[tasks]\nmax_turns = true\n")

    def test_int_where_bool_is_error(self):
        with self.assertRaisesRegex(ConfigError, "project.allow_no_tests"):
            load_config_text(MIN + "[project]\nallow_no_tests = 1\n")

    def test_list_of_wrong_items_is_error(self):
        with self.assertRaisesRegex(ConfigError, "commands.gate"):
            load_config_text(MIN + "[commands]\ngate = [1]\n")

    def test_open_commands_and_components(self):
        c = load_config_text(MIN + '[commands]\nlint = "npm run lint"\n'
                                   "[components]\nnuovo = false\n")
        self.assertEqual(c.get("commands.lint"), "npm run lint")
        self.assertIs(c.get("components.nuovo"), False)
        with self.assertRaisesRegex(ConfigError, "commands.lint"):
            load_config_text(MIN + "[commands]\nlint = 3\n")
        with self.assertRaisesRegex(ConfigError, "components.nuovo"):
            load_config_text(MIN + '[components]\nnuovo = "no"\n')

    def test_report_string_or_map(self):
        a = load_config_text(MIN + '[commands]\nreport = "junit:r.xml"\n')
        self.assertEqual(a.get("commands.report"), "junit:r.xml")
        b = load_config_text(MIN + '[commands]\nreport = { verify = "junit:r.xml" }\n')
        self.assertEqual(b.get("commands.report"), {"verify": "junit:r.xml"})
        with self.assertRaisesRegex(ConfigError, "commands.report"):
            load_config_text(MIN + "[commands]\nreport = { verify = 1 }\n")

    def test_max_tokens_map_of_ints(self):
        with self.assertRaisesRegex(ConfigError, "tasks.max_tokens"):
            load_config_text(MIN + '[tasks]\nmax_tokens = { L1 = "molti" }\n')

    def test_profiles(self):
        c = load_config_text(MIN + '[profiles]\nactive = ["web"]\n'
                                   '[profiles.web]\npaths = ["web/**"]\nskills = ["ui-ux-pro-max"]\nextra = 1\n')
        self.assertEqual(c.get("profiles.active"), ["web"])
        web = c.profiles["web"]
        self.assertEqual(web["paths"], ["web/**"])
        self.assertEqual(web["kind"], "vertical")
        self.assertEqual(web["min_level"], "L0")
        self.assertIn("chiave sconosciuta: profiles.web.extra", c.warnings)
        with self.assertRaisesRegex(ConfigError, "profiles.web.kind"):
            load_config_text(MIN + '[profiles.web]\nkind = "orizzontale"\n')
        with self.assertRaisesRegex(ConfigError, "profiles.web.min_level"):
            load_config_text(MIN + '[profiles.web]\nmin_level = "L3"\n')
        with self.assertRaisesRegex(ConfigError, "profiles.web"):
            load_config_text(MIN + "[profiles]\nweb = 3\n")


class LoadFromGitTest(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo(Path(tempfile.mkdtemp()) / "r")
        (self.repo / "tollgate.toml").write_text(MIN + "[tasks]\nmax_turns = 41\n")
        git(self.repo, "add", "tollgate.toml")
        git(self.repo, "commit", "-qm", "c")
        (self.repo / "tollgate.toml").write_text(MIN + "[tasks]\nmax_turns = 99\n")

    def test_reads_ref_not_working_tree(self):
        self.assertEqual(load_config_at(self.repo, "HEAD").get("tasks.max_turns"), 41)

    def test_missing_file(self):
        git(self.repo, "rm", "-q", "--cached", "tollgate.toml")
        git(self.repo, "commit", "-qm", "rm")
        with self.assertRaises(ConfigNotFound):
            load_config_at(self.repo, "HEAD")

    def test_test_config_override_only_in_test_mode(self):
        t = TempState()
        try:
            f = t.dir / "test.toml"
            f.write_text(MIN + "[tasks]\nmax_turns = 7\n")
            env = {"TOLLGATE_STATE": str(t.dir), "TOLLGATE_TEST_CONFIG": str(f)}
            self.assertEqual(load_config(t.state, self.repo, "HEAD", env).get("tasks.max_turns"), 7)
            from tollgate_core.paths import State
            real = State(t.dir, False)
            self.assertEqual(load_config(real, self.repo, "HEAD", env).get("tasks.max_turns"), 41)
        finally:
            t.cleanup()
```

- [ ] **Step 3: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ModuleNotFoundError: No module named 'tollgate_core.config'`.

- [ ] **Step 4: Scrivere il codice**

`bin/tollgate_core/config.py`:

```python
"""Caricamento e validazione di tollgate.toml (spec 11.4, 12.2, 3.2)."""
from __future__ import annotations

import copy
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .paths import State, test_env

SCHEMA_VERSION = 1


class ConfigError(Exception):
    pass


class ConfigNotFound(ConfigError):
    pass


DEFAULTS: dict = {
    "schema_version": SCHEMA_VERSION,
    "project": {"allow_no_tests": False},
    "commands": {
        "setup": "", "verify": "", "test_related": "", "gate": ["verify"],
        "report": "", "report_related": "",
        "env_allow": ["PATH", "HOME", "LANG", "CI", "NODE_ENV"], "timeout_s": 900,
    },
    "gate": {"mode": ""},
    "acts": {"ttl_minutes": 10},
    "hooks": {"timeout_s": 20},
    "levels": {
        "sensitive_paths": ["**/migrations/**", "**/auth/**"],
        "sensitive_labels": ["security", "database"],
        "l0_max_files": 2, "l0_max_lines": 50, "l0_max_bytes": 4000,
    },
    "context": {"warn_pct": 45, "stop_pct": 55},
    "plan": {
        "required_sections": ["Fatti verificati", "Decisioni", "Interfacce", "Must-have",
                              "Scope", "Punti di arresto", "Rischi"],
        "max_scope_files": 30,
    },
    "scope": {
        "always": [],
        "lockfiles": {"package-lock.json": "package.json", "pnpm-lock.yaml": "package.json",
                      "poetry.lock": "pyproject.toml"},
    },
    "external_effects": {"commands": [], "project_scripts": ["deploy", "release"],
                         "allow": [], "mcp_allow": []},
    "test_guard": {
        "test_globs": [],
        "fixture_globs": ["**/fixtures/**/*.json", "**/__snapshots__/**"],
        "ci_globs": [".github/workflows/**"],
        "verification_globs": [
            "**/vitest.config.*", "**/vitest.setup.*", "**/jest.config.*", "**/playwright.config.*",
            "**/.mocharc.*", "**/conftest.py", "**/pytest.ini", "**/tox.ini", "**/setupTests.*",
            "**/.coveragerc", "**/.nycrc*", "**/cypress.config.*", "**/karma.conf.*",
            "**/.env.test", "scripts/check*"],
        "verification_watch": [
            "**/package.json", "**/vite.config.*", "**/tsconfig*.json", "**/setup.cfg",
            "**/pyproject.toml", "**/Makefile", "**/.babelrc", "**/babel.config.*",
            "**/.swcrc", "**/.npmrc"],
        "skip_markers": [], "assert_markers": [],
    },
    "spec_audit": {"spec_rounds": 4, "plan_rounds": 2, "spec_audit_cycles": 30},
    "tasks": {"task_lines_warn": 200, "task_lines_max": 500, "task_files_warn": 8,
              "max_turns": 60, "max_tokens": {"L0": 0, "L1": 400000, "L2": 800000}},
    "review": {
        "readonly_agents": ["tollgate:task-reviewer", "tollgate:final-reviewer",
                            "tollgate:finding-verifier", "tollgate:plan-adversary",
                            "tollgate:spec-adversary", "tollgate:spec-auditor", "Explore"],
        "output_dirs": ["reports/", "coverage/"], "max_findings": 15,
        "stale_minutes": 30, "models": {},
    },
    "severity": {
        "blocker": "perdita o esposizione di dati, azione eseguita due volte, sicurezza compromessa",
        "major": "un comportamento sbagliato o un passo che fallirebbe così com'è",
        "moderate": "debito o attrito che emergerà più avanti",
        "minor": "redazionale",
    },
    "retention": {"retention_days": 30, "events_days": 180},
    "profiles": {"active": []},
    "components": {k: True for k in (
        "scope_check", "plan_check", "test_guard", "context_guard", "subagent_receipt_gate",
        "single_writer", "readonly_check", "final_review", "spec_adversary", "spec_audit",
        "plan_adversary", "base_test_ids", "sentinel", "task_size", "task_budget",
        "definition_of_done", "must_have_tests", "report_fields", "reviewer_standard",
        "spec_pitch")},
}

PROFILE_DEFAULTS: dict = {
    "kind": "vertical", "cross": [], "paths": ["**"], "setup": "", "commands": {}, "gate": [],
    "test_related": "", "report": "", "test_globs": [], "skip_markers": [],
    "assert_markers": [], "plan_sections": [], "min_level": "L0", "dod": [], "checklist": "",
    "skills": [], "agent": "", "reviewer": "", "reviewer_skills": [], "final_specialist": "",
}

# Chiavi con un tipo che il valore predefinito non descrive.
_STR_MAP = "mappa di stringhe"
_INT_MAP = "mappa di interi"
_STR_OR_MAP = "stringa o mappa di stringhe"
_SPECIAL = {
    "commands.report": _STR_OR_MAP, "tasks.max_tokens": _INT_MAP, "review.models": _STR_MAP,
    "scope.lockfiles": _STR_MAP, "profiles.*.commands": _STR_MAP, "profiles.*.report": _STR_OR_MAP,
}
_ENUMS = {"gate.mode": ("protected", "detect"), "profiles.*.kind": ("vertical", "cross"),
          "profiles.*.min_level": ("L0", "L1", "L2")}
# Sezioni che accettano chiavi nuove, con il tipo delle chiavi nuove.
_OPEN = {"commands": str, "components": bool}


@dataclass
class Config:
    data: dict
    warnings: list[str] = field(default_factory=list)

    def get(self, dotted: str):
        node = self.data
        for part in dotted.split("."):
            node = node[part]
        return node

    @property
    def profiles(self) -> dict[str, dict]:
        return {k: v for k, v in self.data["profiles"].items() if k != "active"}


def _is_str_map(v) -> bool:
    return isinstance(v, dict) and all(isinstance(x, str) for x in v.values())


def _type_ok(value, default, special: str | None) -> bool:
    if special == _STR_MAP:
        return _is_str_map(value)
    if special == _INT_MAP:
        return isinstance(value, dict) and all(
            isinstance(x, int) and not isinstance(x, bool) for x in value.values())
    if special == _STR_OR_MAP:
        return isinstance(value, str) or _is_str_map(value)
    if isinstance(default, bool):
        return isinstance(value, bool)
    if isinstance(default, int):
        return isinstance(value, int) and not isinstance(value, bool)
    if isinstance(default, str):
        return isinstance(value, str)
    if isinstance(default, list):
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    return False


def _describe(default, special) -> str:
    if special:
        return special
    if isinstance(default, list):
        return "lista di stringhe"
    return type(default).__name__


def _set_key(table: dict, key: str, value, default, path: str, pattern: str) -> None:
    special = _SPECIAL.get(pattern)
    if not _type_ok(value, default, special):
        raise ConfigError(f"tipo sbagliato per {path}: atteso {_describe(default, special)}, "
                          f"trovato {type(value).__name__}")
    allowed = _ENUMS.get(pattern)
    if allowed and value not in allowed:
        raise ConfigError(f"valore non ammesso per {path}: {value!r} (ammessi: {', '.join(allowed)})")
    table[key] = value


def _merge_profile(name: str, raw, warnings: list[str]) -> dict:
    if not isinstance(raw, dict):
        raise ConfigError(f"tipo sbagliato per profiles.{name}: atteso una tabella")
    prof = copy.deepcopy(PROFILE_DEFAULTS)
    for key, value in raw.items():
        path = f"profiles.{name}.{key}"
        if key not in PROFILE_DEFAULTS:
            warnings.append(f"chiave sconosciuta: {path}")
            continue
        _set_key(prof, key, value, PROFILE_DEFAULTS[key], path, f"profiles.*.{key}")
    return prof


def load_config_text(text: str, source: str = "tollgate.toml") -> Config:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{source}: TOML non valido: {e}") from e
    if "schema_version" not in raw:
        raise ConfigError(f"{source}: manca schema_version")
    sv = raw["schema_version"]
    if not isinstance(sv, int) or isinstance(sv, bool):
        raise ConfigError(f"{source}: schema_version deve essere un intero")
    if sv > SCHEMA_VERSION:
        raise ConfigError(f"{source}: schema_version {sv} non supportata da questa versione di "
                          f"tollgate: aggiornare il plugin")
    if sv < 1:
        raise ConfigError(f"{source}: schema_version {sv} non valida")
    data = copy.deepcopy(DEFAULTS)
    warnings: list[str] = []
    for section, table in raw.items():
        if section == "schema_version":
            continue
        if section not in DEFAULTS:
            warnings.append(f"sezione sconosciuta: {section}")
            continue
        if not isinstance(table, dict):
            raise ConfigError(f"tipo sbagliato per {section}: atteso una tabella")
        for key, value in table.items():
            path = f"{section}.{key}"
            if section == "profiles" and key != "active":
                data["profiles"][key] = _merge_profile(key, value, warnings)
            elif key in DEFAULTS[section]:
                _set_key(data[section], key, value, DEFAULTS[section][key], path, path)
            elif section in _OPEN:
                sample = "" if _OPEN[section] is str else True
                _set_key(data[section], key, value, sample, path, path)
            else:
                warnings.append(f"chiave sconosciuta: {path}")
    if not data["gate"]["mode"]:
        raise ConfigError(f"{source}: manca gate.mode (lo scrive /tollgate:init)")
    return Config(data, warnings)


def load_config_at(repo: Path, ref: str) -> Config:
    """Legge tollgate.toml da un riferimento git, mai dal working tree (spec 3.2)."""
    r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:tollgate.toml"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise ConfigNotFound(f"tollgate.toml assente in {ref}")
    return load_config_text(r.stdout, source=f"{ref}:tollgate.toml")


def load_config(state: State, repo: Path, ref: str, env=None) -> Config:
    override = test_env(state, "TOLLGATE_TEST_CONFIG", env)
    if override:
        return load_config_text(Path(override).read_text(), source=override)
    return load_config_at(repo, ref)
```

- [ ] **Step 5: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_core/config.py tests/helpers.py tests/test_config.py
git commit -m "tollgate P1: caricamento e validazione di tollgate.toml"
```

---

### Task 3: DB, schema, migrazioni, copie e ripristino

**Files:**
- Create: `bin/tollgate_core/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `paths.State`, `paths.ensure_dirs`, `clock` (Task 1).
- Produces:
  - `db.DbError(Exception)`, `db.DbCorrupt(DbError)`, `db.DbTooNew(DbError)`.
  - `db.BIN_PATH: Path` (percorso assoluto di `bin/tollgate`) e `db.restore_hint() -> str` (`"<BIN_PATH> db restore"`).
  - `db.MIGRATIONS: list[tuple[int, list[str]]]` (versione, istruzioni SQL) e `db.latest_version() -> int`.
  - `db.open_db(state: State) -> sqlite3.Connection`: crea cartelle e DB, imposta i pragma, applica le migrazioni. Connessione in autocommit (`isolation_level=None`) con `row_factory = sqlite3.Row`.
  - `db.tx(conn)`: context manager con `BEGIN IMMEDIATE`; se la connessione è già in una transazione si unisce a quella.
  - `db.backup(conn, state: State, reason: str) -> Path`: copia con la API di SQLite in `backup/`, tiene le ultime 10.
  - `db.integrity_ok(path: Path) -> bool`.
  - `db.restore(state: State, *, interactive: bool, confirm: Callable[[str], bool]) -> str`.
  - Schema versione 1: le tabelle di 12.2 con le colonne della «Decisione 3». `work_items` ha l'indice univoco parziale `(repo_key, issue) WHERE phase <> 'closed'`.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_db.py`:

```python
import os
import sqlite3
import unittest
from unittest import mock

from tests.helpers import TempState
from tollgate_core import db

TABLES = {"meta", "work_items", "scope", "receipts", "blocks", "subagents", "review_cycles",
          "findings", "spec_audit", "acts", "intents", "tasks", "events"}


def insert_work(conn, issue=1, phase="plan", repo="github.com/o/r"):
    conn.execute(
        "INSERT INTO work_items (repo_key, issue, level, phase, created, updated) "
        "VALUES (?, ?, 'L1', ?, 'x', 'x')", (repo, issue, phase))


class OpenTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()

    def tearDown(self):
        self.t.cleanup()

    def test_pragmas_and_tables(self):
        conn = db.open_db(self.t.state)
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(conn.execute("PRAGMA synchronous").fetchone()[0], 2)
        self.assertEqual(conn.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
        self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(TABLES <= names, TABLES - names)
        self.assertEqual(conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()[0], "1")

    def test_fresh_db_makes_no_backup_and_reopen_is_idempotent(self):
        db.open_db(self.t.state).close()
        db.open_db(self.t.state).close()
        self.assertEqual(list(self.t.state.backup_dir.glob("*.db")), [])

    def test_newer_db_is_refused(self):
        conn = db.open_db(self.t.state)
        conn.execute("UPDATE meta SET value='99' WHERE key='schema_version'")
        conn.close()
        with self.assertRaises(db.DbTooNew):
            db.open_db(self.t.state)

    def test_migration_makes_backup_first(self):
        db.open_db(self.t.state).close()
        extra = db.MIGRATIONS + [(2, ["CREATE TABLE extra (x INTEGER)"])]
        with mock.patch.object(db, "MIGRATIONS", extra):
            conn = db.open_db(self.t.state)
        backups = list(self.t.state.backup_dir.glob("*migrazione-2*.db"))
        self.assertEqual(len(backups), 1)
        old = sqlite3.connect(backups[0])
        self.assertIsNone(old.execute(
            "SELECT name FROM sqlite_master WHERE name='extra'").fetchone())
        self.assertIsNotNone(conn.execute(
            "SELECT name FROM sqlite_master WHERE name='extra'").fetchone())

    def test_corrupt_file(self):
        self.t.state.db_path.write_bytes(os.urandom(4096))
        with self.assertRaises(db.DbCorrupt) as cm:
            db.open_db(self.t.state)
        self.assertIn(str(db.BIN_PATH) + " db restore", str(cm.exception))
        self.assertTrue(db.BIN_PATH.is_absolute())

    def test_unique_active_work(self):
        conn = db.open_db(self.t.state)
        insert_work(conn, phase="plan")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_work(conn, phase="execution")
        conn.execute("UPDATE work_items SET phase='closed'")
        insert_work(conn, phase="plan")
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 2)


class TxTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_rollback_on_error(self):
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                insert_work(self.conn)
                raise RuntimeError("x")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)

    def test_nested_joins_outer(self):
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                with db.tx(self.conn):
                    insert_work(self.conn)
                raise RuntimeError("x")
        self.assertEqual(self.conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)


class BackupTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_keeps_last_ten(self):
        paths = [db.backup(self.conn, self.t.state, f"prova-{i}") for i in range(12)]
        left = sorted(p.name for p in self.t.state.backup_dir.glob("*.db"))
        self.assertEqual(len(left), 10)
        self.assertEqual(left[-1], paths[-1].name)
        self.assertNotIn(paths[0].name, left)

    def test_backup_is_consistent(self):
        insert_work(self.conn)
        p = db.backup(self.conn, self.t.state, "fase")
        self.assertTrue(db.integrity_ok(p))
        self.assertEqual(sqlite3.connect(p).execute("SELECT count(*) FROM work_items").fetchone()[0], 1)


class RestoreTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        conn = db.open_db(self.t.state)
        insert_work(conn)
        db.backup(conn, self.t.state, "fase")
        conn.close()

    def tearDown(self):
        self.t.cleanup()

    def corrupt(self):
        for suffix in ("", "-wal", "-shm"):
            p = self.t.state.db_path.with_name(self.t.state.db_path.name + suffix)
            if p.exists():
                p.unlink()
        self.t.state.db_path.write_bytes(os.urandom(4096))

    def test_refuses_healthy_db(self):
        with self.assertRaisesRegex(db.DbError, "integro"):
            db.restore(self.t.state, interactive=True, confirm=lambda q: True)

    def test_refuses_without_terminal(self):
        self.corrupt()
        with self.assertRaisesRegex(db.DbError, "terminale"):
            db.restore(self.t.state, interactive=False, confirm=lambda q: True)

    def test_cancel(self):
        self.corrupt()
        self.assertEqual(db.restore(self.t.state, interactive=True, confirm=lambda q: False),
                         "annullato")

    def test_restores_last_good_copy(self):
        self.corrupt()
        msg = db.restore(self.t.state, interactive=True, confirm=lambda q: True)
        self.assertIn("ripristinata", msg)
        conn = db.open_db(self.t.state)
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 1)
        self.assertEqual(len(list(self.t.state.broken_dir.rglob("tollgate.db"))), 1)

    def test_no_good_copy_gives_empty_db(self):
        for b in self.t.state.backup_dir.glob("*.db"):
            b.write_bytes(os.urandom(4096))
        self.corrupt()
        msg = db.restore(self.t.state, interactive=True, confirm=lambda q: True)
        self.assertIn("/tollgate:adopt", msg)
        conn = db.open_db(self.t.state)
        self.assertEqual(conn.execute("SELECT count(*) FROM work_items").fetchone()[0], 0)
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'db' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/db.py`:

```python
"""DB SQLite nella cartella di stato (spec 12.1, 12.2, 12.4)."""
from __future__ import annotations

import re
import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from . import clock
from .paths import State, ensure_dirs

BIN_PATH = Path(__file__).resolve().parents[1] / "tollgate"
KEEP_BACKUPS = 10


class DbError(Exception):
    pass


class DbCorrupt(DbError):
    pass


class DbTooNew(DbError):
    pass


def restore_hint() -> str:
    return f"{BIN_PATH} db restore"


# Le istruzioni non contengono ';' al loro interno: la lista è divisa a mano.
SCHEMA_V1 = [
    "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    """CREATE TABLE work_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_key TEXT NOT NULL, issue INTEGER NOT NULL,
        level TEXT NOT NULL CHECK (level IN ('L0','L1','L2')),
        level_cap TEXT CHECK (level_cap IS NULL OR level_cap IN ('L0','L1','L2')),
        level_cap_reason TEXT,
        phase TEXT NOT NULL CHECK (phase IN
            ('spec_audit','plan','approval','execution','review','pr_open','closed','blocked')),
        phase_before_block TEXT,
        branch TEXT, worktree TEXT, work_base_sha TEXT, gate_mode TEXT,
        spec_path TEXT, plan_path TEXT, plan_sha TEXT,
        sessions TEXT NOT NULL DEFAULT '[]',
        created TEXT NOT NULL, updated TEXT NOT NULL, closed_reason TEXT)""",
    "CREATE UNIQUE INDEX work_items_active ON work_items(repo_key, issue) WHERE phase <> 'closed'",
    """CREATE TABLE scope (
        work INTEGER NOT NULL REFERENCES work_items(id), path TEXT NOT NULL,
        origin TEXT NOT NULL, registered_at TEXT NOT NULL, PRIMARY KEY (work, path))""",
    """CREATE TABLE receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, work INTEGER REFERENCES work_items(id),
        sha TEXT NOT NULL, command TEXT NOT NULL, resolved_command TEXT, exit INTEGER,
        tests_run INTEGER, tests_skipped INTEGER, duration REAL, log TEXT,
        produced_by TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('green','red','empty','uncounted','unverified')),
        at TEXT NOT NULL)""",
    """CREATE TABLE blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, work INTEGER NOT NULL REFERENCES work_items(id),
        type TEXT NOT NULL CHECK (type IN
            ('needs_you','test_spec_conflict','dependency','permission','transient')),
        reason TEXT NOT NULL, opened TEXT NOT NULL, closed TEXT, resolution TEXT)""",
    """CREATE TABLE subagents (
        id TEXT PRIMARY KEY, name TEXT, type TEXT, work INTEGER REFERENCES work_items(id),
        task INTEGER, session TEXT, agent_base_sha TEXT, fingerprint TEXT,
        started TEXT, ended TEXT, resumes INTEGER NOT NULL DEFAULT 0,
        declared_status TEXT, state TEXT, tokens INTEGER, duration REAL)""",
    """CREATE TABLE review_cycles (
        work INTEGER NOT NULL REFERENCES work_items(id), number INTEGER NOT NULL,
        sha TEXT, patch_id TEXT, outcome TEXT, findings_confirmed INTEGER,
        counted INTEGER NOT NULL DEFAULT 1, PRIMARY KEY (work, number))""",
    """CREATE TABLE findings (
        id TEXT NOT NULL, work INTEGER NOT NULL REFERENCES work_items(id), cycle INTEGER,
        source TEXT,
        severity TEXT CHECK (severity IN ('blocker','major','moderate','minor')),
        confidence REAL, file TEXT, line INTEGER, text TEXT,
        verification TEXT CHECK (verification IS NULL OR
            verification IN ('confirmed','rejected','unverified')),
        verification_reason TEXT, user_decision TEXT, PRIMARY KEY (work, id))""",
    """CREATE TABLE spec_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, work INTEGER NOT NULL REFERENCES work_items(id),
        kind TEXT NOT NULL, number INTEGER NOT NULL, viewpoint TEXT, counts TEXT,
        outcome TEXT, report_path TEXT)""",
    """CREATE TABLE acts (
        n INTEGER PRIMARY KEY AUTOINCREMENT, act_id TEXT UNIQUE,
        type TEXT NOT NULL, object TEXT, target TEXT, args TEXT NOT NULL DEFAULT '[]',
        at TEXT NOT NULL, typed_text TEXT, source TEXT NOT NULL, actor TEXT, session TEXT,
        work INTEGER REFERENCES work_items(id), head_sha TEXT,
        state TEXT NOT NULL CHECK (state IN ('pending','consumed','expired')),
        expires_at TEXT, consumed_at TEXT)""",
    """CREATE TABLE intents (
        id INTEGER PRIMARY KEY AUTOINCREMENT, work INTEGER REFERENCES work_items(id),
        action TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE, data TEXT,
        state TEXT NOT NULL, outcome TEXT, at TEXT NOT NULL)""",
    """CREATE TABLE tasks (
        work INTEGER NOT NULL REFERENCES work_items(id), number INTEGER NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('plan','fix')), source TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('pending','running','review','done','blocked')),
        fix_rounds INTEGER NOT NULL DEFAULT 0, implementer TEXT, agent_type TEXT,
        reviewer_type TEXT, skills_required TEXT NOT NULL DEFAULT '[]',
        skills_used TEXT NOT NULL DEFAULT '[]', commits TEXT NOT NULL DEFAULT '[]',
        verdict TEXT, review_code TEXT, PRIMARY KEY (work, number))""",
    """CREATE TABLE events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT, v INTEGER NOT NULL, at TEXT NOT NULL,
        host TEXT NOT NULL, session TEXT, work INTEGER, repo_key TEXT, issue INTEGER,
        type TEXT NOT NULL, data TEXT NOT NULL)""",
    "CREATE INDEX events_work ON events(work, seq)",
]

MIGRATIONS: list[tuple[int, list[str]]] = [(1, SCHEMA_V1)]


def latest_version() -> int:
    return MIGRATIONS[-1][0]


@contextmanager
def tx(conn: sqlite3.Connection):
    """Transazione con il lucchetto di scrittura preso subito; si unisce a una già aperta."""
    if conn.in_transaction:
        yield conn
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def _version(conn: sqlite3.Connection) -> int:
    if not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'").fetchone():
        return 0
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    return int(row[0]) if row else 0


def _migrate(conn: sqlite3.Connection, state: State) -> None:
    current = _version(conn)
    if current > latest_version():
        raise DbTooNew(f"il DB ha lo schema {current}, questa versione di tollgate arriva a "
                       f"{latest_version()}: aggiornare il plugin")
    for target, statements in MIGRATIONS:
        if target <= current:
            continue
        if current > 0:
            backup(conn, state, f"migrazione-{target}")
        with tx(conn):
            # Un altro processo può aver migrato mentre aspettavamo il lucchetto.
            current = _version(conn)
            if current >= target:
                continue
            for stmt in statements:
                conn.execute(stmt)
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
                         (str(target),))
        current = target


def open_db(state: State) -> sqlite3.Connection:
    ensure_dirs(state)
    conn = sqlite3.connect(state.db_path, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        _migrate(conn, state)
    except sqlite3.DatabaseError as e:
        conn.close()
        raise DbCorrupt(f"DB di tollgate guasto ({state.db_path}): {e}. "
                        f"Ripristino dal terminale: {restore_hint()}. "
                        f"Per spegnere tollgate: touch {state.root / 'OFF'}") from e
    except BaseException:
        conn.close()
        raise
    return conn


def backup(conn: sqlite3.Connection, state: State, reason: str) -> Path:
    """Copia coerente con la API di backup (in WAL il file da solo non lo è)."""
    ensure_dirs(state)
    tag = re.sub(r"[^a-z0-9-]+", "-", reason.lower()).strip("-") or "copia"
    stamp = clock.now().strftime("%Y%m%dT%H%M%S%fZ")
    dst_path = state.backup_dir / f"tollgate-{stamp}-{tag}.db"
    n = 1
    while dst_path.exists():
        dst_path = state.backup_dir / f"tollgate-{stamp}-{n}-{tag}.db"
        n += 1
    dst = sqlite3.connect(dst_path)
    try:
        conn.backup(dst)
    finally:
        dst.close()
    for old in sorted(state.backup_dir.glob("tollgate-*.db"))[:-KEEP_BACKUPS]:
        old.unlink()
    return dst_path


def integrity_ok(path: Path) -> bool:
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        return False


def restore(state: State, *, interactive: bool, confirm: Callable[[str], bool]) -> str:
    """Ripristino dal terminale, senza atto: solo con un DB che non supera integrity_check."""
    if not state.db_path.exists():
        raise DbError(f"nessun DB in {state.db_path}: niente da ripristinare")
    if integrity_ok(state.db_path):
        raise DbError("il DB è integro: niente da ripristinare")
    if not interactive:
        raise DbError("db restore va lanciato da un terminale interattivo")
    if not confirm(f"Il DB {state.db_path} è guasto. Spostarlo da parte e ripristinare "
                   f"l'ultima copia integra? [s/N] "):
        return "annullato"
    dest = state.broken_dir / clock.now().strftime("%Y%m%dT%H%M%S%fZ")
    dest.mkdir(parents=True)
    for suffix in ("", "-wal", "-shm"):
        p = state.db_path.with_name(state.db_path.name + suffix)
        if p.exists():
            shutil.move(str(p), dest / p.name)
    for candidate in sorted(state.backup_dir.glob("tollgate-*.db"), reverse=True):
        if integrity_ok(candidate):
            shutil.copy2(candidate, state.db_path)
            open_db(state).close()
            return f"ripristinata la copia {candidate.name}; il DB guasto è in {dest}"
    open_db(state).close()
    return (f"nessuna copia integra: DB vuoto; il DB guasto è in {dest}. "
            f"Per ogni lavoro con un ramo tg/* lancia /tollgate:adopt #N")
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/db.py tests/test_db.py
git commit -m "tollgate P1: DB, migrazioni, copie e ripristino"
```

---

### Task 4: Eventi

**Files:**
- Create: `bin/tollgate_core/events.py`
- Test: `tests/test_events.py`

**Interfaces:**
- Consumes: `db.open_db`, `db.tx` (Task 3); `clock` (Task 1).
- Produces:
  - `events.EVENT_TYPES: frozenset[str]`: i tipi di 18.4.
  - `events.record_event(conn, type_: str, data: dict | None = None, *, now: datetime, session: str | None = None, work: int | None = None, host: str | None = None) -> int` (il `seq`). Ricava `repo_key` e `issue` dal lavoro. Rifiuta con `ValueError` un tipo fuori elenco o un lavoro inesistente. Si unisce alla transazione del chiamante, se c'è.
  - `events.export_events(conn, after_seq: int) -> list[dict]`: buste ordinate per `seq`, con `data` già decodificato.
  - `events.to_jsonl(items: list[dict]) -> str`.
  - `events.prune_events(conn, now: datetime, events_days: int) -> int` (righe cancellate).

Busta (18.4): `{"v": 1, "seq", "at", "host", "session", "work", "repo_key", "issue", "type", "data"}`. `seq` viene da `AUTOINCREMENT`, quindi non si riusa nemmeno dopo la potatura.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_events.py`:

```python
import json
import subprocess
import sys
import textwrap
import unittest
from datetime import timedelta

from tests.helpers import BIN, TempState
from tollgate_core import clock, db, events

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
KEYS = {"v", "seq", "at", "host", "session", "work", "repo_key", "issue", "type", "data"}


class EventsTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.conn.execute(
            "INSERT INTO work_items (repo_key, issue, level, phase, created, updated) "
            "VALUES ('github.com/o/r', 42, 'L1', 'plan', 'x', 'x')")
        self.work = self.conn.execute("SELECT id FROM work_items").fetchone()[0]

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_envelope(self):
        seq = events.record_event(self.conn, "veto", {"rule": "scope", "event": "pre_edit",
                                                      "reason": "fuori scope"},
                                  now=T0, session="s1", work=self.work, host="h")
        (e,) = events.export_events(self.conn, 0)
        self.assertEqual(set(e), KEYS)
        self.assertEqual(e["seq"], seq)
        self.assertEqual(e["v"], 1)
        self.assertEqual(e["at"], "2026-10-08T10:00:00.000000Z")
        self.assertEqual((e["repo_key"], e["issue"], e["work"]), ("github.com/o/r", 42, self.work))
        self.assertEqual(e["data"]["rule"], "scope")

    def test_without_work(self):
        events.record_event(self.conn, "off", {}, now=T0)
        (e,) = events.export_events(self.conn, 0)
        self.assertIsNone(e["work"])
        self.assertIsNone(e["repo_key"])
        self.assertTrue(e["host"])

    def test_rejects_unknown_type_and_work(self):
        with self.assertRaises(ValueError):
            events.record_event(self.conn, "boh", {}, now=T0)
        with self.assertRaises(ValueError):
            events.record_event(self.conn, "veto", {}, now=T0, work=999)

    def test_export_after_seq_and_jsonl(self):
        seqs = [events.record_event(self.conn, "commit", {"i": i}, now=T0) for i in range(5)]
        got = events.export_events(self.conn, seqs[1])
        self.assertEqual([e["seq"] for e in got], seqs[2:])
        lines = events.to_jsonl(got).splitlines()
        self.assertEqual([json.loads(x)["data"]["i"] for x in lines], [2, 3, 4])

    def test_prune_keeps_recent_and_seq_never_reused(self):
        old = T0 - timedelta(days=200)
        events.record_event(self.conn, "commit", {}, now=old)
        last_old = events.record_event(self.conn, "commit", {}, now=old)
        events.record_event(self.conn, "commit", {}, now=T0)
        self.assertEqual(events.prune_events(self.conn, T0, 180), 2)
        self.assertEqual(len(events.export_events(self.conn, 0)), 1)
        self.conn.execute("DELETE FROM events")
        new = events.record_event(self.conn, "commit", {}, now=T0)
        self.assertGreater(new, last_old + 1)

    def test_joins_caller_transaction(self):
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                events.record_event(self.conn, "commit", {}, now=T0)
                raise RuntimeError("x")
        self.assertEqual(events.export_events(self.conn, 0), [])


class ConcurrencyTest(unittest.TestCase):
    """Più processi (hook) che creano e scrivono lo stesso DB nello stesso momento."""

    def setUp(self):
        self.t = TempState()

    def tearDown(self):
        self.t.cleanup()

    def test_three_writers(self):
        code = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(BIN)!r})
            from tollgate_core import clock, db, events
            from tollgate_core.paths import resolve_state
            conn = db.open_db(resolve_state())
            for i in range(100):
                events.record_event(conn, "commit", {{"i": i}}, now=clock.now(), session=sys.argv[1])
        """)
        procs = [subprocess.Popen([sys.executable, "-B", "-c", code, f"s{n}"],
                                  env=self.t.env(), stderr=subprocess.PIPE, text=True)
                 for n in range(3)]
        for p in procs:
            _, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, err)
        conn = db.open_db(self.t.state)
        got = events.export_events(conn, 0)
        self.assertEqual(len(got), 300)
        seqs = [e["seq"] for e in got]
        self.assertEqual(seqs, sorted(set(seqs)))
        for s in ("s0", "s1", "s2"):
            mine = [e["data"]["i"] for e in got if e["session"] == s]
            self.assertEqual(mine, list(range(100)))
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'events' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/events.py`:

```python
"""Registro degli eventi (spec 18.4): sola aggiunta, seq monotono, potatura oltre events_days."""
from __future__ import annotations

import json
import socket
import sqlite3
from datetime import datetime, timedelta

from . import clock
from .db import tx

ENVELOPE_VERSION = 1
EVENT_TYPES = frozenset({
    "session_start", "act", "phase_change", "level_change", "scope_registered", "waiver_added",
    "block_opened", "block_closed", "commit", "receipt", "subagent_start", "subagent_stop",
    "veto", "effect_requested", "effect_executed", "review_cycle", "pr_opened", "pr_updated",
    "merge_detected", "sentinel_alert", "spec_audit_round", "act_expired", "task_change",
    "finding", "off", "on",
})
_COLUMNS = "seq, v, at, host, session, work, repo_key, issue, type, data"


def record_event(conn: sqlite3.Connection, type_: str, data: dict | None = None, *,
                 now: datetime, session: str | None = None, work: int | None = None,
                 host: str | None = None) -> int:
    if type_ not in EVENT_TYPES:
        raise ValueError(f"tipo di evento sconosciuto: {type_}")
    with tx(conn):
        repo_key = issue = None
        if work is not None:
            row = conn.execute("SELECT repo_key, issue FROM work_items WHERE id = ?",
                               (work,)).fetchone()
            if row is None:
                raise ValueError(f"lavoro {work} inesistente")
            repo_key, issue = row[0], row[1]
        cur = conn.execute(
            "INSERT INTO events (v, at, host, session, work, repo_key, issue, type, data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ENVELOPE_VERSION, clock.fmt(now), host or socket.gethostname(), session, work,
             repo_key, issue, type_, json.dumps(data or {}, ensure_ascii=False, sort_keys=True)))
        return cur.lastrowid


def _as_dict(row) -> dict:
    d = {k: row[k] for k in ("seq", "v", "at", "host", "session", "work", "repo_key", "issue",
                             "type")}
    d["data"] = json.loads(row["data"])
    return d


def export_events(conn: sqlite3.Connection, after_seq: int) -> list[dict]:
    rows = conn.execute(f"SELECT {_COLUMNS} FROM events WHERE seq > ? ORDER BY seq",
                        (after_seq,)).fetchall()
    return [_as_dict(r) for r in rows]


def to_jsonl(items: list[dict]) -> str:
    return "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in items)


def prune_events(conn: sqlite3.Connection, now: datetime, events_days: int) -> int:
    limit = clock.fmt(now - timedelta(days=events_days))
    with tx(conn):
        return conn.execute("DELETE FROM events WHERE at < ?", (limit,)).rowcount
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/events.py tests/test_events.py
git commit -m "tollgate P1: registro degli eventi"
```

---

### Task 5: Lavori, fasi e blocchi

**Files:**
- Create: `bin/tollgate_core/phases.py`
- Test: `tests/test_phases.py`

**Interfaces:**
- Consumes: `db.tx`, `db.backup` (Task 3); `events.record_event` (Task 4); `paths.State`, `clock` (Task 1).
- Produces:
  - `phases.PHASES`, `phases.SEQUENCES: dict[str, tuple[str, ...]]`, `phases.INITIAL: dict[str, str]`, `phases.CLOSE_CAUSES`.
  - `phases.TransitionError(Exception)`, `phases.WorkExists(Exception)`.
  - `phases.check_transition(level: str, frm: str, to: str, cause: str) -> None` (solleva `TransitionError`).
  - `phases.create_work(conn, *, repo_key: str, issue: int, level: str, now, session: str | None = None, branch=None, worktree=None, work_base_sha=None, gate_mode=None, spec_path=None, from_approved_spec: bool = False) -> int`: riga e fase iniziale nella stessa transazione, evento `phase_change` con `from: null`.
  - `phases.get_work(conn, work: int) -> sqlite3.Row`; `phases.find_active(conn, repo_key: str, issue: int) -> sqlite3.Row | None`; `phases.find_latest(conn, repo_key: str, issue: int) -> sqlite3.Row | None` (anche chiusi).
  - `phases.bind_session(conn, work: int, session: str, *, now) -> None`.
  - `phases.set_phase(conn, state, work: int, to: str, cause: str, *, now, session=None) -> None`: fuori da ogni transazione (solleva `RuntimeError` altrimenti), perché dopo il commit fa la copia del DB.
  - `phases.set_level(conn, work: int, level: str, *, now, session=None) -> None`: solo verso l'alto.
  - `phases.open_block(conn, state, work: int, type_: str, reason: str, *, now, session=None) -> int`; `phases.close_block(conn, state, block_id: int, resolution: str, *, now, session=None) -> str` (la fase dopo la chiusura).

Cause riconosciute da `check_transition` (spec 12.3): `advance` per i passaggi in avanti senza condizione; `finish_check_green` per `execution` → `review`; `needs_fix` e `start` per `review` → `execution`; `start` e `sync` per `pr_open` → `execution`; `reopen_spec`, `reopen_plan`; `l0_grew` per `execution` → `plan` in L0, che porta il livello a L1; `merged`, `closed_unmerged`, `abandoned` per `closed`, da qualunque fase. `blocked` si raggiunge e si lascia solo con `open_block` e `close_block`.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_phases.py`:

```python
import itertools
import json
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases
from tollgate_core.phases import TransitionError

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
OPEN_PHASES = ["spec_audit", "plan", "approval", "execution", "review", "pr_open"]
CAUSES = ["advance", "finish_check_green", "needs_fix", "start", "sync", "reopen_spec",
          "reopen_plan", "l0_grew", "merged"]
BACK = {("review", "execution", "needs_fix"), ("review", "execution", "start"),
        ("pr_open", "execution", "start"), ("pr_open", "execution", "sync")}
EXPECTED = {
    "L0": {("execution", "review", "finish_check_green"), ("review", "pr_open", "advance"),
           ("execution", "plan", "l0_grew")} | BACK,
    "L1": {("plan", "execution", "advance"), ("execution", "review", "finish_check_green"),
           ("review", "pr_open", "advance"), ("execution", "plan", "reopen_plan")} | BACK,
    "L2": {("spec_audit", "plan", "advance"), ("plan", "approval", "advance"),
           ("approval", "execution", "advance"), ("execution", "review", "finish_check_green"),
           ("review", "pr_open", "advance"),
           ("plan", "spec_audit", "reopen_spec"), ("approval", "spec_audit", "reopen_spec"),
           ("execution", "spec_audit", "reopen_spec"),
           ("approval", "plan", "reopen_plan"), ("execution", "plan", "reopen_plan")} | BACK,
}


class CheckTransitionTest(unittest.TestCase):
    """Criterio 25: ogni transizione fuori da 12.3 è rifiutata."""

    def test_table_is_exact(self):
        for level, expected in EXPECTED.items():
            allowed = set()
            for frm, to, cause in itertools.product(OPEN_PHASES, OPEN_PHASES, CAUSES):
                try:
                    phases.check_transition(level, frm, to, cause)
                    allowed.add((frm, to, cause))
                except TransitionError:
                    pass
            with self.subTest(level=level):
                self.assertEqual(allowed, expected)

    def test_closed(self):
        for frm in OPEN_PHASES + ["blocked"]:
            for cause in ("merged", "closed_unmerged", "abandoned"):
                phases.check_transition("L1", frm, "closed", cause)
            with self.assertRaises(TransitionError):
                phases.check_transition("L1", frm, "closed", "advance")
        with self.assertRaises(TransitionError):
            phases.check_transition("L1", "closed", "plan", "start")

    def test_blocked_only_through_blocks(self):
        with self.assertRaises(TransitionError):
            phases.check_transition("L1", "plan", "blocked", "advance")
        with self.assertRaises(TransitionError):
            phases.check_transition("L1", "blocked", "plan", "advance")


class WorkTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def new(self, level="L1", issue=7, **kw):
        return phases.create_work(self.conn, repo_key="github.com/o/r", issue=issue,
                                  level=level, now=T0, session="s1", **kw)

    def backups(self):
        return len(list(self.t.state.backup_dir.glob("*.db")))

    def test_initial_phases(self):
        self.assertEqual(phases.get_work(self.conn, self.new("L0", 1))["phase"], "execution")
        self.assertEqual(phases.get_work(self.conn, self.new("L1", 2))["phase"], "plan")
        self.assertEqual(phases.get_work(self.conn, self.new("L2", 3))["phase"], "spec_audit")
        w = self.new("L2", 4, spec_path="docs/s.md", from_approved_spec=True)
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "plan")
        first = events.export_events(self.conn, 0)[0]
        self.assertEqual(first["type"], "phase_change")
        self.assertEqual(first["data"], {"from": None, "to": "execution", "cause": "start"})

    def test_sessions_and_duplicates(self):
        w = self.new()
        self.assertEqual(json.loads(phases.get_work(self.conn, w)["sessions"]), ["s1"])
        phases.bind_session(self.conn, w, "s2", now=T0)
        phases.bind_session(self.conn, w, "s2", now=T0)
        self.assertEqual(json.loads(phases.get_work(self.conn, w)["sessions"]), ["s1", "s2"])
        with self.assertRaises(phases.WorkExists):
            self.new()
        self.assertEqual(phases.find_active(self.conn, "github.com/o/r", 7)["id"], w)

    def test_set_phase_records_and_backs_up(self):
        w = self.new()
        phases.set_phase(self.conn, self.t.state, w, "execution", "advance", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["phase"], "execution")
        self.assertEqual(self.backups(), 1)
        last = events.export_events(self.conn, 0)[-1]
        self.assertEqual(last["data"], {"from": "plan", "to": "execution", "cause": "advance"})
        with self.assertRaises(TransitionError):
            phases.set_phase(self.conn, self.t.state, w, "pr_open", "advance", now=T0)
        self.assertEqual(self.backups(), 1)

    def test_set_phase_refuses_open_transaction(self):
        w = self.new()
        with self.assertRaises(RuntimeError):
            with db.tx(self.conn):
                phases.set_phase(self.conn, self.t.state, w, "execution", "advance", now=T0)

    def test_l0_grew(self):
        w = self.new("L0")
        phases.set_phase(self.conn, self.t.state, w, "plan", "l0_grew", now=T0)
        row = phases.get_work(self.conn, w)
        self.assertEqual((row["phase"], row["level"]), ("plan", "L1"))
        types = [e["type"] for e in events.export_events(self.conn, 0)]
        self.assertIn("level_change", types)

    def test_set_level_only_up(self):
        w = self.new("L1")
        phases.set_level(self.conn, w, "L2", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["level"], "L2")
        with self.assertRaises(TransitionError):
            phases.set_level(self.conn, w, "L1", now=T0)

    def test_closed_then_new_work(self):
        w = self.new()
        phases.set_phase(self.conn, self.t.state, w, "closed", "abandoned", now=T0)
        self.assertEqual(phases.get_work(self.conn, w)["closed_reason"], "abandoned")
        self.assertIsNone(phases.find_active(self.conn, "github.com/o/r", 7))
        w2 = self.new()
        self.assertEqual(phases.find_latest(self.conn, "github.com/o/r", 7)["id"], w2)


class BlockTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)
        phases.set_phase(self.conn, self.t.state, self.w, "execution", "advance", now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def phase(self):
        return phases.get_work(self.conn, self.w)["phase"]

    def test_two_blocks_restore_previous_phase(self):
        b1 = phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r1", now=T0)
        b2 = phases.open_block(self.conn, self.t.state, self.w, "transient", "r2", now=T0)
        self.assertEqual(self.phase(), "blocked")
        self.assertEqual(phases.close_block(self.conn, self.t.state, b1, "ok", now=T0), "blocked")
        self.assertEqual(phases.close_block(self.conn, self.t.state, b2, "ok", now=T0),
                         "execution")
        self.assertIsNone(phases.get_work(self.conn, self.w)["phase_before_block"])
        opened = [e for e in events.export_events(self.conn, 0) if e["type"] == "block_opened"]
        self.assertEqual(opened[0]["data"], {"id": b1, "type": "needs_you"})

    def test_close_twice_and_bad_type(self):
        b = phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
        phases.close_block(self.conn, self.t.state, b, "ok", now=T0)
        with self.assertRaises(TransitionError):
            phases.close_block(self.conn, self.t.state, b, "ok", now=T0)
        with self.assertRaises(ValueError):
            phases.open_block(self.conn, self.t.state, self.w, "boh", "r", now=T0)

    def test_set_phase_from_blocked_only_to_closed(self):
        phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
        with self.assertRaises(TransitionError):
            phases.set_phase(self.conn, self.t.state, self.w, "review", "finish_check_green",
                             now=T0)
        phases.set_phase(self.conn, self.t.state, self.w, "closed", "merged", now=T0)
        self.assertEqual(self.phase(), "closed")
        with self.assertRaises(TransitionError):
            phases.open_block(self.conn, self.t.state, self.w, "needs_you", "r", now=T0)
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'phases' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/phases.py`:

```python
"""Lavori, fasi (spec 12.3) e blocchi (spec 8.3)."""
from __future__ import annotations

import json
import sqlite3

from . import clock, db
from .events import record_event
from .paths import State

PHASES = ("spec_audit", "plan", "approval", "execution", "review", "pr_open", "closed", "blocked")
SEQUENCES = {
    "L0": ("execution", "review", "pr_open", "closed"),
    "L1": ("plan", "execution", "review", "pr_open", "closed"),
    "L2": ("spec_audit", "plan", "approval", "execution", "review", "pr_open", "closed"),
}
INITIAL = {"L0": "execution", "L1": "plan", "L2": "spec_audit"}
LEVELS = ("L0", "L1", "L2")
BLOCK_TYPES = ("needs_you", "test_spec_conflict", "dependency", "permission", "transient")
CLOSE_CAUSES = frozenset({"merged", "closed_unmerged", "abandoned"})
_FORWARD_CONDITION = {("execution", "review"): "finish_check_green"}
_BACK = {
    ("review", "execution"): {"needs_fix", "start"},
    ("pr_open", "execution"): {"start", "sync"},
    ("plan", "spec_audit"): {"reopen_spec"},
    ("approval", "spec_audit"): {"reopen_spec"},
    ("execution", "spec_audit"): {"reopen_spec"},
    ("approval", "plan"): {"reopen_plan"},
    ("execution", "plan"): {"reopen_plan"},
}


class TransitionError(Exception):
    pass


class WorkExists(Exception):
    pass


def check_transition(level: str, frm: str, to: str, cause: str) -> None:
    if frm == "closed":
        raise TransitionError("il lavoro è chiuso")
    if to == "closed":
        if cause in CLOSE_CAUSES:
            return
        raise TransitionError(f"chiusura solo per {', '.join(sorted(CLOSE_CAUSES))}")
    if "blocked" in (frm, to):
        raise TransitionError("la fase blocked si apre e si chiude solo con i blocchi")
    if level == "L0" and (frm, to, cause) == ("execution", "plan", "l0_grew"):
        return
    seq = SEQUENCES[level]
    if frm in seq and to in seq:
        if seq.index(to) == seq.index(frm) + 1:
            needed = _FORWARD_CONDITION.get((frm, to), "advance")
            if cause == needed:
                return
            raise TransitionError(f"{frm} → {to} solo con {needed}")
        if cause in _BACK.get((frm, to), ()):
            return
    raise TransitionError(f"transizione non ammessa in {level}: {frm} → {to} ({cause})")


def get_work(conn: sqlite3.Connection, work: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM work_items WHERE id = ?", (work,)).fetchone()
    if row is None:
        raise ValueError(f"lavoro {work} inesistente")
    return row


def find_active(conn, repo_key: str, issue: int):
    return conn.execute("SELECT * FROM work_items WHERE repo_key = ? AND issue = ? "
                        "AND phase <> 'closed'", (repo_key, issue)).fetchone()


def find_latest(conn, repo_key: str, issue: int):
    return conn.execute("SELECT * FROM work_items WHERE repo_key = ? AND issue = ? "
                        "ORDER BY id DESC LIMIT 1", (repo_key, issue)).fetchone()


def create_work(conn, *, repo_key: str, issue: int, level: str, now, session=None, branch=None,
                worktree=None, work_base_sha=None, gate_mode=None, spec_path=None,
                from_approved_spec: bool = False) -> int:
    if level not in LEVELS:
        raise ValueError(f"livello sconosciuto: {level}")
    phase = "plan" if (level == "L2" and from_approved_spec) else INITIAL[level]
    ts = clock.fmt(now)
    with db.tx(conn):
        try:
            cur = conn.execute(
                "INSERT INTO work_items (repo_key, issue, level, phase, branch, worktree, "
                "work_base_sha, gate_mode, spec_path, sessions, created, updated) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (repo_key, issue, level, phase, branch, worktree, work_base_sha, gate_mode,
                 spec_path, json.dumps([session] if session else []), ts, ts))
        except sqlite3.IntegrityError as e:
            raise WorkExists(f"esiste già un lavoro attivo per {repo_key}#{issue}") from e
        work = cur.lastrowid
        record_event(conn, "phase_change", {"from": None, "to": phase, "cause": "start"},
                     now=now, session=session, work=work)
    return work


def bind_session(conn, work: int, session: str, *, now) -> None:
    with db.tx(conn):
        sessions = json.loads(get_work(conn, work)["sessions"])
        if session not in sessions:
            sessions.append(session)
            conn.execute("UPDATE work_items SET sessions = ?, updated = ? WHERE id = ?",
                         (json.dumps(sessions), clock.fmt(now), work))


def _change_phase(conn, work: int, frm: str, to: str, cause: str, now, session) -> None:
    conn.execute("UPDATE work_items SET phase = ?, updated = ? WHERE id = ?",
                 (to, clock.fmt(now), work))
    record_event(conn, "phase_change", {"from": frm, "to": to, "cause": cause},
                 now=now, session=session, work=work)


def set_phase(conn, state: State, work: int, to: str, cause: str, *, now, session=None) -> None:
    if conn.in_transaction:
        raise RuntimeError("set_phase va chiamato fuori da una transazione: "
                           "la copia del DB deve vedere solo dati confermati")
    with db.tx(conn):
        row = get_work(conn, work)
        check_transition(row["level"], row["phase"], to, cause)
        _change_phase(conn, work, row["phase"], to, cause, now, session)
        if to == "closed":
            conn.execute("UPDATE work_items SET closed_reason = ? WHERE id = ?", (cause, work))
        if cause == "l0_grew":
            conn.execute("UPDATE work_items SET level = 'L1' WHERE id = ?", (work,))
            record_event(conn, "level_change", {"from": "L0", "to": "L1"},
                         now=now, session=session, work=work)
    db.backup(conn, state, f"fase-{to}")


def set_level(conn, work: int, level: str, *, now, session=None) -> None:
    if level not in LEVELS:
        raise ValueError(f"livello sconosciuto: {level}")
    with db.tx(conn):
        current = get_work(conn, work)["level"]
        if LEVELS.index(level) < LEVELS.index(current):
            raise TransitionError("il livello si abbassa solo con un atto dell'utente (tetto)")
        if level != current:
            conn.execute("UPDATE work_items SET level = ?, updated = ? WHERE id = ?",
                         (level, clock.fmt(now), work))
            record_event(conn, "level_change", {"from": current, "to": level},
                         now=now, session=session, work=work)


def open_block(conn, state: State, work: int, type_: str, reason: str, *, now,
               session=None) -> int:
    if type_ not in BLOCK_TYPES:
        raise ValueError(f"tipo di blocco sconosciuto: {type_}")
    if conn.in_transaction:
        raise RuntimeError("open_block va chiamato fuori da una transazione")
    with db.tx(conn):
        row = get_work(conn, work)
        if row["phase"] == "closed":
            raise TransitionError("il lavoro è chiuso")
        cur = conn.execute("INSERT INTO blocks (work, type, reason, opened) VALUES (?, ?, ?, ?)",
                           (work, type_, reason, clock.fmt(now)))
        block = cur.lastrowid
        changed = row["phase"] != "blocked"
        if changed:
            conn.execute("UPDATE work_items SET phase_before_block = ? WHERE id = ?",
                         (row["phase"], work))
            _change_phase(conn, work, row["phase"], "blocked", "block", now, session)
        record_event(conn, "block_opened", {"id": block, "type": type_},
                     now=now, session=session, work=work)
    if changed:
        db.backup(conn, state, "fase-blocked")
    return block


def close_block(conn, state: State, block_id: int, resolution: str, *, now,
                session=None) -> str:
    if conn.in_transaction:
        raise RuntimeError("close_block va chiamato fuori da una transazione")
    with db.tx(conn):
        b = conn.execute("SELECT * FROM blocks WHERE id = ?", (block_id,)).fetchone()
        if b is None or b["closed"] is not None:
            raise TransitionError(f"blocco {block_id} inesistente o già chiuso")
        work = b["work"]
        conn.execute("UPDATE blocks SET closed = ?, resolution = ? WHERE id = ?",
                     (clock.fmt(now), resolution, block_id))
        record_event(conn, "block_closed", {"id": block_id}, now=now, session=session, work=work)
        row = get_work(conn, work)
        still_open = conn.execute("SELECT count(*) FROM blocks WHERE work = ? AND closed IS NULL",
                                  (work,)).fetchone()[0]
        changed = still_open == 0 and row["phase"] == "blocked"
        if changed:
            back = row["phase_before_block"]
            conn.execute("UPDATE work_items SET phase_before_block = NULL WHERE id = ?", (work,))
            _change_phase(conn, work, "blocked", back, "unblock", now, session)
        phase = get_work(conn, work)["phase"]
    if changed:
        db.backup(conn, state, f"fase-{phase}")
    return phase
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/phases.py tests/test_phases.py
git commit -m "tollgate P1: lavori, fasi e blocchi (criterio 25)"
```

---

### Task 6: Task del piano e transizioni di `tasks.state`

**Files:**
- Create: `bin/tollgate_core/tasks.py`
- Test: `tests/test_tasks.py`

**Interfaces:**
- Consumes: `db.tx` (Task 3); `events.record_event` (Task 4); `phases.create_work` (Task 5, solo nei test).
- Produces:
  - `tasks.STATES`, `tasks.TASK_EVENTS`, `tasks.TaskTransitionError(Exception)`.
  - `tasks.add_task(conn, work: int, number: int, *, source: str, kind: str = "plan", skills_required: list[str] | None = None, now, session=None) -> None` (stato `pending`; `ValueError` se il numero esiste già).
  - `tasks.next_number(conn, work: int) -> int`.
  - `tasks.get_task(conn, work: int, number: int) -> sqlite3.Row`.
  - `tasks.task_event(conn, work: int, number: int, event: str, *, now, session=None) -> str` (il nuovo stato).
  - `tasks.add_skill_used(conn, work: int, number: int, skill: str) -> None`.

Eventi e transizioni (spec 6.3, tabella «Transizioni di `tasks.state`»):

| Da | Evento | A | Effetto |
|---|---|---|---|
| `pending` | `start` | `running` | |
| `running` | `report_done` | `review` | |
| `running` | `report_blocked` | `blocked` | |
| `running` | `needs_context` | `running` | nessun giro consumato |
| `running` | `budget_exceeded` | `blocked` | |
| `running` | `interrupted` | `pending` | nessun giro consumato |
| `review` | `fix` | `running` | `fix_rounds` + 1, `verdict = "changes"` |
| `review` | `approved` | `done` | `verdict = "approved"` |
| `blocked` | `unblocked` | `pending` | |

Ogni cambio registra `task_change` con `{number, kind, state, fix_rounds, verdict}` (18.4).

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_tasks.py`:

```python
import itertools
import json
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases, tasks
from tollgate_core.tasks import TaskTransitionError

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
EXPECTED = {
    ("pending", "start"): "running", ("running", "report_done"): "review",
    ("running", "report_blocked"): "blocked", ("running", "needs_context"): "running",
    ("running", "budget_exceeded"): "blocked", ("running", "interrupted"): "pending",
    ("review", "fix"): "running", ("review", "approved"): "done",
    ("blocked", "unblocked"): "pending",
}


class TasksTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def force(self, number, state):
        self.conn.execute("UPDATE tasks SET state = ? WHERE work = ? AND number = ?",
                          (state, self.w, number))

    def test_table_is_exact(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        allowed = {}
        for state, event in itertools.product(tasks.STATES, tasks.TASK_EVENTS):
            self.force(1, state)
            try:
                allowed[(state, event)] = tasks.task_event(self.conn, self.w, 1, event, now=T0)
            except TaskTransitionError:
                pass
        self.assertEqual(allowed, EXPECTED)

    def test_fix_rounds_counted_by_cli(self):
        tasks.add_task(self.conn, self.w, 2, source="plan:2", now=T0)
        tasks.task_event(self.conn, self.w, 2, "start", now=T0)
        for _ in range(3):
            tasks.task_event(self.conn, self.w, 2, "report_done", now=T0)
            tasks.task_event(self.conn, self.w, 2, "fix", now=T0)
        tasks.task_event(self.conn, self.w, 2, "needs_context", now=T0)
        tasks.task_event(self.conn, self.w, 2, "interrupted", now=T0)
        row = tasks.get_task(self.conn, self.w, 2)
        self.assertEqual((row["fix_rounds"], row["state"], row["verdict"]), (3, "pending", "changes"))

    def test_start_only_from_pending(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        tasks.task_event(self.conn, self.w, 1, "start", now=T0)
        with self.assertRaises(TaskTransitionError):
            tasks.task_event(self.conn, self.w, 1, "start", now=T0)

    def test_approved_sets_verdict_and_event(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", skills_required=["a"], now=T0)
        for e in ("start", "report_done", "approved"):
            tasks.task_event(self.conn, self.w, 1, e, now=T0)
        row = tasks.get_task(self.conn, self.w, 1)
        self.assertEqual((row["state"], row["verdict"]), ("done", "approved"))
        self.assertEqual(json.loads(row["skills_required"]), ["a"])
        last = [e for e in events.export_events(self.conn, 0) if e["type"] == "task_change"][-1]
        self.assertEqual(last["data"], {"number": 1, "kind": "plan", "state": "done",
                                        "fix_rounds": 0, "verdict": "approved"})

    def test_numbers_duplicates_unknowns(self):
        self.assertEqual(tasks.next_number(self.conn, self.w), 1)
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        self.assertEqual(tasks.next_number(self.conn, self.w), 2)
        with self.assertRaises(ValueError):
            tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        with self.assertRaises(ValueError):
            tasks.add_task(self.conn, self.w, 3, source="x", kind="altro", now=T0)
        with self.assertRaises(ValueError):
            tasks.task_event(self.conn, self.w, 1, "boh", now=T0)
        with self.assertRaises(ValueError):
            tasks.get_task(self.conn, self.w, 99)

    def test_skills_used(self):
        tasks.add_task(self.conn, self.w, 1, source="plan:1", now=T0)
        tasks.add_skill_used(self.conn, self.w, 1, "tdd")
        tasks.add_skill_used(self.conn, self.w, 1, "tdd")
        self.assertEqual(json.loads(tasks.get_task(self.conn, self.w, 1)["skills_used"]), ["tdd"])
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'tasks' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/tasks.py`:

```python
"""Task del piano e transizioni di tasks.state (spec 6.3)."""
from __future__ import annotations

import json
import sqlite3

from . import db
from .events import record_event

STATES = ("pending", "running", "review", "done", "blocked")
KINDS = ("plan", "fix")
_TRANSITIONS = {
    ("pending", "start"): "running",
    ("running", "report_done"): "review",
    ("running", "report_blocked"): "blocked",
    ("running", "needs_context"): "running",
    ("running", "budget_exceeded"): "blocked",
    ("running", "interrupted"): "pending",
    ("review", "fix"): "running",
    ("review", "approved"): "done",
    ("blocked", "unblocked"): "pending",
}
TASK_EVENTS = tuple(sorted({e for _, e in _TRANSITIONS}))
_VERDICT = {"fix": "changes", "approved": "approved"}


class TaskTransitionError(Exception):
    pass


def get_task(conn, work: int, number: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM tasks WHERE work = ? AND number = ?",
                       (work, number)).fetchone()
    if row is None:
        raise ValueError(f"task {number} del lavoro {work} inesistente")
    return row


def next_number(conn, work: int) -> int:
    return conn.execute("SELECT coalesce(max(number), 0) + 1 FROM tasks WHERE work = ?",
                        (work,)).fetchone()[0]


def _log(conn, row, *, now, session) -> None:
    record_event(conn, "task_change",
                 {"number": row["number"], "kind": row["kind"], "state": row["state"],
                  "fix_rounds": row["fix_rounds"], "verdict": row["verdict"]},
                 now=now, session=session, work=row["work"])


def add_task(conn, work: int, number: int, *, source: str, kind: str = "plan",
             skills_required: list[str] | None = None, now, session=None) -> None:
    if kind not in KINDS:
        raise ValueError(f"tipo di task sconosciuto: {kind}")
    with db.tx(conn):
        try:
            conn.execute("INSERT INTO tasks (work, number, kind, source, state, skills_required) "
                         "VALUES (?, ?, ?, ?, 'pending', ?)",
                         (work, number, kind, source, json.dumps(skills_required or [])))
        except sqlite3.IntegrityError as e:
            raise ValueError(f"task {number} già presente nel lavoro {work}") from e
        _log(conn, get_task(conn, work, number), now=now, session=session)


def task_event(conn, work: int, number: int, event: str, *, now, session=None) -> str:
    if event not in TASK_EVENTS:
        raise ValueError(f"evento di task sconosciuto: {event}")
    with db.tx(conn):
        row = get_task(conn, work, number)
        new = _TRANSITIONS.get((row["state"], event))
        if new is None:
            raise TaskTransitionError(f"task {number}: {event} non ammesso da {row['state']}")
        fix_rounds = row["fix_rounds"] + (1 if event == "fix" else 0)
        verdict = _VERDICT.get(event, row["verdict"])
        conn.execute("UPDATE tasks SET state = ?, fix_rounds = ?, verdict = ? "
                     "WHERE work = ? AND number = ?", (new, fix_rounds, verdict, work, number))
        _log(conn, get_task(conn, work, number), now=now, session=session)
    return new


def add_skill_used(conn, work: int, number: int, skill: str) -> None:
    with db.tx(conn):
        used = json.loads(get_task(conn, work, number)["skills_used"])
        if skill not in used:
            used.append(skill)
            conn.execute("UPDATE tasks SET skills_used = ? WHERE work = ? AND number = ?",
                         (json.dumps(used), work, number))
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/tasks.py tests/test_tasks.py
git commit -m "tollgate P1: task del piano e loro transizioni"
```

---

### Task 7: Atti dell'utente

**Files:**
- Create: `bin/tollgate_core/acts.py`
- Test: `tests/test_acts.py`

**Interfaces:**
- Consumes: `db.tx` (Task 3); `events.record_event` (Task 4); `phases.create_work` (Task 5, solo nei test); `clock` (Task 1).
- Produces:
  - `acts.ACT_TYPES`, `acts.APPROVE_OBJECTS`, `acts.ActError(Exception)`.
  - `acts.is_one_shot(type_: str, object_: str | None) -> bool`: vero per `finish`, `approve effect`, `approve pr`, `approve rebase`, `sync`, `adopt`, `cleanup`, `abandon` (8.4).
  - `acts.record_act(conn, *, type_: str, object_: str | None = None, target: str | None = None, args: list[str] | None = None, typed_text: str, source: str = "claude-code", actor: str | None = None, session: str | None, work: int | None = None, head_sha: str | None = None, now, ttl_minutes: int) -> str` (l'`act_id`, nella forma `a-<n>` di 18.1).
  - `acts.find_usable(conn, *, type_: str, object_: str | None = None, target: str | None = None, work: int | None, session: str | None, now, head_sha: str | None = None) -> sqlite3.Row | None`.
  - `acts.consume(conn, act_id: str, *, now, session=None) -> None`.
  - `acts.expire_stale(conn, *, now, session=None) -> list[str]`.
  - `acts.invalidate_finish(conn, work: int, head_sha: str, *, now, session=None) -> list[str]`.

Regole (spec 8.4): ogni atto nasce `pending` e diventa `consumed` o `expired`. Un atto vale solo per lo stesso lavoro e lo stesso oggetto (`type`, `object`, `target`). **Tutti tranne `finish`** valgono solo nella sessione in cui sono stati digitati e scadono dopo `ttl_minutes` (`expires_at` escluso: all'istante della scadenza l'atto non vale più). **`finish`** non scade e non è legato alla sessione: vale finché HEAD del lavoro è lo SHA registrato.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_acts.py`:

```python
import unittest
from datetime import timedelta

from tests.helpers import TempState
from tollgate_core import acts, clock, db, events, phases

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


class ActsTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)
        self.w2 = phases.create_work(self.conn, repo_key="github.com/o/r", issue=2, level="L1",
                                     now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def waiver(self, **kw):
        base = dict(type_="approve", object_="waiver", target="w-1-3",
                    typed_text="/tollgate:approve waiver w-1-3", session="s1", work=self.w,
                    now=T0, ttl_minutes=10)
        base.update(kw)
        return acts.record_act(self.conn, **base)

    def usable(self, **kw):
        base = dict(type_="approve", object_="waiver", target="w-1-3", work=self.w,
                    session="s1", now=T0 + timedelta(minutes=5))
        base.update(kw)
        return acts.find_usable(self.conn, **base)

    def test_record_and_event(self):
        a = self.waiver()
        self.assertEqual(a, "a-1")
        e = [x for x in events.export_events(self.conn, 0) if x["type"] == "act"][0]
        self.assertEqual(e["data"]["act_id"], "a-1")
        self.assertEqual((e["data"]["type"], e["data"]["object"], e["data"]["target"]),
                         ("approve", "waiver", "w-1-3"))
        self.assertEqual(e["data"]["source"], "claude-code")

    def test_binding_and_ttl(self):
        self.waiver()
        self.assertIsNotNone(self.usable())
        self.assertIsNone(self.usable(session="s2"))
        self.assertIsNone(self.usable(work=self.w2))
        self.assertIsNone(self.usable(target="w-1-4"))
        self.assertIsNotNone(self.usable(now=T0 + timedelta(minutes=9, seconds=59)))
        self.assertIsNone(self.usable(now=T0 + timedelta(minutes=10)))

    def test_consume_once(self):
        a = self.waiver()
        acts.consume(self.conn, a, now=T0)
        self.assertIsNone(self.usable())
        with self.assertRaises(acts.ActError):
            acts.consume(self.conn, a, now=T0)

    def test_finish_bound_to_head_not_session_or_time(self):
        acts.record_act(self.conn, type_="finish", typed_text="/tollgate:finish", session="s1",
                        work=self.w, head_sha="abc", now=T0, ttl_minutes=10)
        later = T0 + timedelta(hours=3)
        self.assertIsNotNone(acts.find_usable(self.conn, type_="finish", work=self.w,
                                              session="s9", now=later, head_sha="abc"))
        self.assertIsNone(acts.find_usable(self.conn, type_="finish", work=self.w,
                                           session="s1", now=T0, head_sha="def"))
        self.assertIsNone(acts.find_usable(self.conn, type_="finish", work=self.w2,
                                           session="s1", now=T0, head_sha="abc"))
        self.assertEqual(acts.expire_stale(self.conn, now=later), [])
        self.assertEqual(acts.invalidate_finish(self.conn, self.w, "def", now=later), ["a-1"])
        self.assertIsNone(acts.find_usable(self.conn, type_="finish", work=self.w,
                                           session="s1", now=later, head_sha="abc"))

    def test_expire_stale(self):
        a = self.waiver()
        b = self.waiver(target="w-1-4", now=T0 + timedelta(minutes=8))
        self.assertEqual(acts.expire_stale(self.conn, now=T0 + timedelta(minutes=10)), [a])
        types = [e["type"] for e in events.export_events(self.conn, 0)]
        self.assertIn("act_expired", types)
        self.assertIsNotNone(self.usable(target="w-1-4", now=T0 + timedelta(minutes=10)))
        self.assertNotEqual(a, b)

    def test_without_work(self):
        acts.record_act(self.conn, type_="adopt", target="3", typed_text="/tollgate:adopt #3",
                        session="s1", work=None, now=T0, ttl_minutes=10)
        self.assertIsNotNone(acts.find_usable(self.conn, type_="adopt", target="3", work=None,
                                              session="s1", now=T0))

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.waiver(type_="boh")
        with self.assertRaises(ValueError):
            self.waiver(object_="boh")
        with self.assertRaises(ValueError):
            acts.record_act(self.conn, type_="finish", typed_text="/tollgate:finish",
                            session="s1", work=self.w, now=T0, ttl_minutes=10)

    def test_one_shot(self):
        self.assertTrue(acts.is_one_shot("finish", None))
        self.assertTrue(acts.is_one_shot("approve", "effect"))
        self.assertTrue(acts.is_one_shot("abandon", None))
        self.assertFalse(acts.is_one_shot("approve", "waiver"))
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'acts' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/acts.py`:

```python
"""Atti dell'utente (spec 8.4): registrazione, legame, scadenza, consumo."""
from __future__ import annotations

import json
import sqlite3
from datetime import timedelta

from . import clock, db
from .events import record_event

ACT_TYPES = frozenset({"finish", "approve", "reopen", "resolve", "sync", "adopt", "abandon",
                       "cleanup", "off", "on"})
APPROVE_OBJECTS = frozenset({"spec", "plan", "waiver", "level", "effect", "finding", "rounds",
                             "unverified-review", "unverified-tests", "rebase", "pr"})
_ONE_SHOT = frozenset({("finish", None), ("approve", "effect"), ("approve", "pr"),
                       ("approve", "rebase"), ("sync", None), ("adopt", None),
                       ("cleanup", None), ("abandon", None)})


class ActError(Exception):
    pass


def is_one_shot(type_: str, object_: str | None) -> bool:
    return (type_, object_) in _ONE_SHOT


def record_act(conn, *, type_: str, object_: str | None = None, target: str | None = None,
               args: list[str] | None = None, typed_text: str, source: str = "claude-code",
               actor: str | None = None, session: str | None, work: int | None = None,
               head_sha: str | None = None, now, ttl_minutes: int) -> str:
    if type_ not in ACT_TYPES:
        raise ValueError(f"atto sconosciuto: {type_}")
    if type_ == "approve" and object_ not in APPROVE_OBJECTS:
        raise ValueError(f"oggetto di approve sconosciuto: {object_}")
    if type_ == "finish" and (work is None or not head_sha):
        raise ValueError("finish richiede il lavoro e lo SHA di HEAD")
    expires = None if type_ == "finish" else clock.fmt(now + timedelta(minutes=ttl_minutes))
    with db.tx(conn):
        cur = conn.execute(
            "INSERT INTO acts (type, object, target, args, at, typed_text, source, actor, "
            "session, work, head_sha, state, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)",
            (type_, object_, target, json.dumps(args or []), clock.fmt(now), typed_text, source,
             actor, session, work, head_sha, expires))
        act_id = f"a-{cur.lastrowid}"
        conn.execute("UPDATE acts SET act_id = ? WHERE n = ?", (act_id, cur.lastrowid))
        record_event(conn, "act", {"act_id": act_id, "type": type_, "object": object_,
                                   "target": target, "args": args or [], "source": source,
                                   "actor": actor}, now=now, session=session, work=work)
    return act_id


def find_usable(conn, *, type_: str, object_: str | None = None, target: str | None = None,
                work: int | None, session: str | None, now, head_sha: str | None = None):
    sql = ("SELECT * FROM acts WHERE state = 'pending' AND type = ? AND object IS ? "
           "AND target IS ? AND work IS ?")
    params: list = [type_, object_, target, work]
    if type_ == "finish":
        sql += " AND head_sha = ?"
        params.append(head_sha)
    else:
        sql += " AND session IS ? AND expires_at > ?"
        params += [session, clock.fmt(now)]
    return conn.execute(sql + " ORDER BY n DESC LIMIT 1", params).fetchone()


def consume(conn, act_id: str, *, now, session=None) -> None:
    with db.tx(conn):
        row = conn.execute("SELECT state, work FROM acts WHERE act_id = ?", (act_id,)).fetchone()
        if row is None or row["state"] != "pending":
            raise ActError(f"atto {act_id} inesistente o non più valido")
        conn.execute("UPDATE acts SET state = 'consumed', consumed_at = ? WHERE act_id = ?",
                     (clock.fmt(now), act_id))


def _expire(conn, rows, *, now, session) -> list[str]:
    ids = []
    for r in rows:
        conn.execute("UPDATE acts SET state = 'expired' WHERE act_id = ?", (r["act_id"],))
        record_event(conn, "act_expired", {"act_id": r["act_id"]}, now=now, session=session,
                     work=r["work"])
        ids.append(r["act_id"])
    return ids


def expire_stale(conn, *, now, session=None) -> list[str]:
    with db.tx(conn):
        rows = conn.execute("SELECT act_id, work FROM acts WHERE state = 'pending' "
                            "AND type <> 'finish' AND expires_at <= ? ORDER BY n",
                            (clock.fmt(now),)).fetchall()
        return _expire(conn, rows, now=now, session=session)


def invalidate_finish(conn, work: int, head_sha: str, *, now, session=None) -> list[str]:
    with db.tx(conn):
        rows = conn.execute("SELECT act_id, work FROM acts WHERE state = 'pending' "
                            "AND type = 'finish' AND work = ? AND head_sha <> ? ORDER BY n",
                            (work, head_sha)).fetchall()
        return _expire(conn, rows, now=now, session=session)
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/acts.py tests/test_acts.py
git commit -m "tollgate P1: atti dell'utente"
```

---

### Task 8: Definition of Done

**Files:**
- Create: `bin/tollgate_core/dod.py`
- Test: `tests/test_dod.py`

**Interfaces:**
- Consumes: `phases.get_work`, `phases.create_work` (Task 5); `tasks.add_task`, `tasks.task_event`, `tasks.add_skill_used` (Task 6, gli ultimi due solo nei test).
- Produces:
  - `dod.DodItem(key: str, label: str, ok: bool | None, detail: str = "")` (dataclass immutabile). `ok = None` vuol dire «non calcolata», e conta come mancante.
  - `dod.ITEMS_BY_LEVEL: dict[str, tuple[str, ...]]`.
  - `dod.EXTERNAL_KEYS = ("guard_scope", "must_have", "approvals", "specialists")`: voci che calcolano P2-P4 e passano a `compute_dod`.
  - `dod.compute_dod(conn, work: int, *, head_sha: str, allow_no_tests: bool, external: Mapping[str, bool | None] | None = None, profile_items: Mapping[str, bool | None] | None = None) -> list[DodItem]`.
  - `dod.dod_passes(items: list[DodItem]) -> bool`.

Voci (spec 8.7). Dal DB, in P1: `receipt` (su `head_sha`, per ogni comando l'ultima ricevuta è `green`, oppure `empty` con `allow_no_tests`), `tasks_approved` (almeno un task, tutti `done` con verdetto `approved`), `findings` (nessun rilievo `blocker` o `major` confermato senza `user_decision`), `skills` (per ogni task `skills_required` ⊆ `skills_used`). Da fuori: `guard_scope`, `must_have`, `approvals`, `specialists`, e le voci dei profili (`profile:<comando>`), richieste a tutti i livelli.

| Livello | Voci |
|---|---|
| L0 | `receipt`, `guard_scope` |
| L1 | `receipt`, `guard_scope`, `tasks_approved`, `findings`, `must_have`, `skills` |
| L2 | come L1, più `approvals`, `specialists` |

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_dod.py`:

```python
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, dod, phases, tasks

T0 = clock.parse("2026-10-08T10:00:00.000000Z")
EXT_OK = {"guard_scope": True, "must_have": True, "approvals": True, "specialists": True}


class DodTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def work(self, level, issue=1):
        return phases.create_work(self.conn, repo_key="github.com/o/r", issue=issue,
                                  level=level, now=T0)

    def receipt(self, w, state, command="verify", sha="h1"):
        self.conn.execute(
            "INSERT INTO receipts (work, sha, command, produced_by, state, at) "
            "VALUES (?, ?, ?, 'verify', ?, 'x')", (w, sha, command, state))

    def done_task(self, w, n, required=(), used=()):
        tasks.add_task(self.conn, w, n, source=f"plan:{n}", skills_required=list(required),
                       now=T0)
        for s in used:
            tasks.add_skill_used(self.conn, w, n, s)
        for e in ("start", "report_done", "approved"):
            tasks.task_event(self.conn, w, n, e, now=T0)

    def finding(self, w, fid, severity, verification, decision=None):
        self.conn.execute(
            "INSERT INTO findings (id, work, severity, verification, user_decision) "
            "VALUES (?, ?, ?, ?, ?)", (fid, w, severity, verification, decision))

    def items(self, w, **kw):
        base = dict(head_sha="h1", allow_no_tests=False, external=EXT_OK)
        base.update(kw)
        return {i.key: i for i in dod.compute_dod(self.conn, w, **base)}

    def test_items_per_level(self):
        self.assertEqual(set(self.items(self.work("L0", 1))), {"receipt", "guard_scope"})
        self.assertEqual(set(self.items(self.work("L1", 2))),
                         {"receipt", "guard_scope", "tasks_approved", "findings", "must_have",
                          "skills"})
        self.assertEqual(set(self.items(self.work("L2", 3))),
                         {"receipt", "guard_scope", "tasks_approved", "findings", "must_have",
                          "skills", "approvals", "specialists"})

    def test_receipt_rules(self):
        w = self.work("L0")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.receipt(w, "red")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.receipt(w, "green")
        self.assertTrue(self.items(w)["receipt"].ok)
        self.receipt(w, "red", command="web.lint")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.assertIn("web.lint", self.items(w)["receipt"].detail)
        self.assertFalse(self.items(w, head_sha="h2")["receipt"].ok)

    def test_empty_needs_allow_no_tests(self):
        w = self.work("L0")
        self.receipt(w, "empty")
        self.assertFalse(self.items(w)["receipt"].ok)
        self.assertTrue(self.items(w, allow_no_tests=True)["receipt"].ok)

    def test_tasks_findings_skills(self):
        w = self.work("L1")
        self.assertFalse(self.items(w)["tasks_approved"].ok)
        self.done_task(w, 1, required=["tdd"], used=["tdd"])
        self.assertTrue(self.items(w)["tasks_approved"].ok)
        self.assertTrue(self.items(w)["skills"].ok)
        tasks.add_task(self.conn, w, 2, source="plan:2", skills_required=["a"], now=T0)
        self.assertFalse(self.items(w)["tasks_approved"].ok)
        self.assertFalse(self.items(w)["skills"].ok)
        self.assertIn("a", self.items(w)["skills"].detail)
        self.finding(w, "f-1-1", "major", "confirmed")
        self.assertFalse(self.items(w)["findings"].ok)
        self.conn.execute("UPDATE findings SET user_decision = 'downgraded:minor'")
        self.assertTrue(self.items(w)["findings"].ok)
        self.finding(w, "f-1-2", "blocker", "rejected")
        self.finding(w, "f-1-3", "moderate", "confirmed")
        self.assertTrue(self.items(w)["findings"].ok)

    def test_external_missing_counts_as_failing(self):
        w = self.work("L0")
        self.receipt(w, "green")
        items = dod.compute_dod(self.conn, w, head_sha="h1", allow_no_tests=False)
        guard = [i for i in items if i.key == "guard_scope"][0]
        self.assertIsNone(guard.ok)
        self.assertFalse(dod.dod_passes(items))

    def test_profile_items_and_pass(self):
        w = self.work("L1")
        self.receipt(w, "green")
        self.done_task(w, 1)
        items = dod.compute_dod(self.conn, w, head_sha="h1", allow_no_tests=False,
                                external=EXT_OK, profile_items={"profile:web.a11y": True})
        self.assertIn("profile:web.a11y", [i.key for i in items])
        self.assertTrue(dod.dod_passes(items))
        items = dod.compute_dod(self.conn, w, head_sha="h1", allow_no_tests=False,
                                external=EXT_OK, profile_items={"profile:web.a11y": False})
        self.assertFalse(dod.dod_passes(items))
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'dod' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/dod.py`:

```python
"""Definition of Done per livello (spec 8.7): ogni voce viene da un dato, mai da un giudizio."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping

from .phases import get_work

EXTERNAL_KEYS = ("guard_scope", "must_have", "approvals", "specialists")
ITEMS_BY_LEVEL = {
    "L0": ("receipt", "guard_scope"),
    "L1": ("receipt", "guard_scope", "tasks_approved", "findings", "must_have", "skills"),
    "L2": ("receipt", "guard_scope", "tasks_approved", "findings", "must_have", "skills",
           "approvals", "specialists"),
}
LABELS = {
    "receipt": "Ricevuta green sullo SHA",
    "guard_scope": "test-guard e scope senza violazioni non derogate",
    "tasks_approved": "Ogni task done con verdetto approved",
    "findings": "Nessun rilievo blocker o major confermato senza approve finding",
    "must_have": "Ogni must-have ha i suoi test eseguiti e verdi",
    "skills": "Skill dei profili usate",
    "approvals": "Spec e piano approvati, report avversariali presenti",
    "specialists": "Specialisti finali passati",
}


@dataclass(frozen=True)
class DodItem:
    key: str
    label: str
    ok: bool | None
    detail: str = ""


def _receipt(conn, work: int, head_sha: str, allow_no_tests: bool) -> tuple[bool, str]:
    rows = conn.execute(
        "SELECT r.command, r.state FROM receipts r WHERE r.work = ? AND r.sha = ? AND r.id = "
        "(SELECT max(id) FROM receipts x WHERE x.work = r.work AND x.sha = r.sha "
        "AND x.command = r.command) ORDER BY r.command", (work, head_sha)).fetchall()
    if not rows:
        return False, f"nessuna ricevuta su {head_sha}"
    bad = [f"{r['command']}={r['state']}" for r in rows
           if not (r["state"] == "green" or (r["state"] == "empty" and allow_no_tests))]
    return (not bad), ", ".join(bad)


def _tasks(conn, work: int) -> tuple[bool, str]:
    rows = conn.execute("SELECT number, state, verdict FROM tasks WHERE work = ? ORDER BY number",
                        (work,)).fetchall()
    if not rows:
        return False, "nessun task"
    bad = [str(r["number"]) for r in rows if r["state"] != "done" or r["verdict"] != "approved"]
    return (not bad), ("task non chiusi: " + ", ".join(bad)) if bad else ""


def _findings(conn, work: int) -> tuple[bool, str]:
    rows = conn.execute(
        "SELECT id FROM findings WHERE work = ? AND severity IN ('blocker', 'major') "
        "AND verification = 'confirmed' AND user_decision IS NULL ORDER BY id",
        (work,)).fetchall()
    return (not rows), ", ".join(r["id"] for r in rows)


def _skills(conn, work: int) -> tuple[bool, str]:
    missing = []
    for r in conn.execute("SELECT number, skills_required, skills_used FROM tasks "
                          "WHERE work = ? ORDER BY number", (work,)):
        lack = [s for s in json.loads(r["skills_required"])
                if s not in json.loads(r["skills_used"])]
        if lack:
            missing.append(f"task {r['number']}: {', '.join(lack)}")
    return (not missing), "; ".join(missing)


def compute_dod(conn, work: int, *, head_sha: str, allow_no_tests: bool,
                external: Mapping[str, bool | None] | None = None,
                profile_items: Mapping[str, bool | None] | None = None) -> list[DodItem]:
    external = external or {}
    level = get_work(conn, work)["level"]
    computed = {
        "receipt": lambda: _receipt(conn, work, head_sha, allow_no_tests),
        "tasks_approved": lambda: _tasks(conn, work),
        "findings": lambda: _findings(conn, work),
        "skills": lambda: _skills(conn, work),
    }
    items = []
    for key in ITEMS_BY_LEVEL[level]:
        if key in computed:
            ok, detail = computed[key]()
        else:
            ok = external.get(key)
            detail = "non calcolata" if ok is None else ""
        items.append(DodItem(key, LABELS[key], ok, detail))
    for key, ok in (profile_items or {}).items():
        items.append(DodItem(key, f"Voce del profilo {key.removeprefix('profile:')}", ok,
                             "non calcolata" if ok is None else ""))
    return items


def dod_passes(items: list[DodItem]) -> bool:
    return all(i.ok is True for i in items)
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/dod.py tests/test_dod.py
git commit -m "tollgate P1: Definition of Done dai dati"
```

---

### Task 9: Statistiche dagli eventi

**Files:**
- Create: `bin/tollgate_core/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `events.record_event`, `events.export_events` (Task 4); `phases` (Task 5); `clock` (Task 1).
- Produces: `stats.compute_stats(conn, *, now, work: int | None = None, since: datetime | None = None) -> dict` con le chiavi:
  - `vetoes`: `{"total": int, "by_rule": {regola: int}}` (eventi `veto`, `data.rule`);
  - `needs_you`: int (eventi `block_opened` con `data.type == "needs_you"`); `blocks`: int (tutti i `block_opened`);
  - `waivers`: int (`waiver_added`); `finding_overrides`: int (eventi `act` con `type == "approve"` e `object == "finding"`);
  - `off_hours`: float, due decimali: ore tra un `off` e il successivo `on` (o `now`), dentro la finestra;
  - `phase_hours`: `{fase: float}`, dai `phase_change` del lavoro (o di tutti i lavori), esclusa `closed`;
  - `tokens`: `{"total": int, "by_agent": {tipo: int}}` (eventi `subagent_stop`, `data.tokens` e `data.type`);
  - `fix_rounds`: int (somma, per task, del massimo `fix_rounds` visto nei `task_change`); `review_cycles`: int (eventi `review_cycle`).

Finestra: con `work`, dal primo evento del lavoro al `phase_change` verso `closed` (o `now`); senza, da `since` (o dall'inizio) a `now`. Gli eventi `off` e `on` non hanno lavoro e si tagliano sulla finestra. Con `since`, si contano solo gli eventi con `at ≥ since`.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_stats.py`:

```python
import unittest
from datetime import timedelta

from tests.helpers import TempState
from tollgate_core import clock, db, events, phases, stats

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


def h(hours):
    return T0 + timedelta(hours=hours)


class StatsTest(unittest.TestCase):
    """Criterio 43: due veti, un needs_you e un'ora di OFF, più tempo per fase e token."""

    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        c, st = self.conn, self.t.state
        self.w = phases.create_work(c, repo_key="github.com/o/r", issue=5, level="L1", now=T0)
        phases.set_phase(c, st, self.w, "execution", "advance", now=h(1))
        events.record_event(c, "veto", {"event": "pre_edit", "rule": "scope", "reason": "x"},
                            now=h(1.5), work=self.w)
        events.record_event(c, "veto", {"event": "pre_bash", "rule": "effects", "reason": "y"},
                            now=h(1.6), work=self.w)
        b = phases.open_block(c, st, self.w, "needs_you", "budget", now=h(2))
        phases.close_block(c, st, b, "diviso", now=h(2.5))
        events.record_event(c, "off", {}, now=h(3))
        events.record_event(c, "on", {}, now=h(4))
        events.record_event(c, "subagent_stop", {"id": "a1", "type": "tollgate:implementer",
                                                 "task": 1, "declared_status": "DONE",
                                                 "tokens": 1000}, now=h(4.5), work=self.w)
        events.record_event(c, "subagent_stop", {"id": "a2", "type": "tollgate:task-reviewer",
                                                 "task": 1, "declared_status": None,
                                                 "tokens": 300}, now=h(4.6), work=self.w)
        for fr in (0, 1, 2):
            events.record_event(c, "task_change", {"number": 1, "kind": "plan",
                                                   "state": "running", "fix_rounds": fr,
                                                   "verdict": None}, now=h(4.7), work=self.w)
        events.record_event(c, "waiver_added", {}, now=h(4.8), work=self.w)
        events.record_event(c, "act", {"act_id": "a-9", "type": "approve", "object": "finding",
                                       "target": "f-1-1", "args": [], "source": "claude-code",
                                       "actor": None}, now=h(4.9), work=self.w)
        events.record_event(c, "review_cycle", {"number": 1, "outcome": "ok",
                                                "findings_confirmed": 0}, now=h(5), work=self.w)
        phases.set_phase(c, st, self.w, "closed", "merged", now=h(6))
        events.record_event(c, "off", {}, now=h(7))

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def test_work_numbers(self):
        s = stats.compute_stats(self.conn, now=h(10), work=self.w)
        self.assertEqual(s["vetoes"], {"total": 2, "by_rule": {"scope": 1, "effects": 1}})
        self.assertEqual(s["needs_you"], 1)
        self.assertEqual(s["blocks"], 1)
        self.assertEqual(s["off_hours"], 1.0)
        self.assertEqual(s["phase_hours"], {"plan": 1.0, "execution": 4.5, "blocked": 0.5})
        self.assertEqual(s["tokens"], {"total": 1300, "by_agent": {"tollgate:implementer": 1000,
                                                                   "tollgate:task-reviewer": 300}})
        self.assertEqual(s["fix_rounds"], 2)
        self.assertEqual(s["waivers"], 1)
        self.assertEqual(s["finding_overrides"], 1)
        self.assertEqual(s["review_cycles"], 1)

    def test_global_window_counts_open_off(self):
        s = stats.compute_stats(self.conn, now=h(10))
        self.assertEqual(s["off_hours"], 4.0)
        self.assertEqual(s["vetoes"]["total"], 2)

    def test_since(self):
        s = stats.compute_stats(self.conn, now=h(10), since=h(1.55))
        self.assertEqual(s["vetoes"], {"total": 1, "by_rule": {"effects": 1}})
        self.assertEqual(s["off_hours"], 4.0)
```

Conto atteso del tempo per fase: `plan` 0→1 h, `execution` 1→2 e 2,5→6 h (4,5), `blocked` 2→2,5 h. OFF: un'ora dentro il lavoro (3→4); nella finestra globale 3→4 più 7→10.

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL, `ImportError: cannot import name 'stats' from 'tollgate_core'`.

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/stats.py`:

```python
"""Statistiche dagli eventi (spec 3.1, criterio 43): quanto tollgate frena e quanto protegge."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from . import clock
from .events import export_events


def _hours(seconds: float) -> float:
    return round(seconds / 3600, 2)


def _off_seconds(evts: list[dict], start: datetime | None, end: datetime) -> float:
    total = 0.0
    off_at = None
    for e in evts:
        if e["type"] == "off" and off_at is None:
            off_at = clock.parse(e["at"])
        elif e["type"] == "on" and off_at is not None:
            total += _overlap(off_at, clock.parse(e["at"]), start, end)
            off_at = None
    if off_at is not None:
        total += _overlap(off_at, end, start, end)
    return total


def _overlap(a: datetime, b: datetime, start: datetime | None, end: datetime) -> float:
    lo = max(a, start) if start else a
    hi = min(b, end)
    return max(0.0, (hi - lo).total_seconds())


def _phase_seconds(changes: list[dict], end: datetime) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for cur, nxt in zip(changes, changes[1:] + [None]):
        phase = cur["data"]["to"]
        if phase == "closed":
            continue
        stop = clock.parse(nxt["at"]) if nxt else end
        out[phase] += (stop - clock.parse(cur["at"])).total_seconds()
    return out


def compute_stats(conn, *, now: datetime, work: int | None = None,
                  since: datetime | None = None) -> dict:
    every = export_events(conn, 0)
    if since is not None:
        since_s = clock.fmt(since)
        every = [e for e in every if e["at"] >= since_s]
    switches = [e for e in every if e["type"] in ("off", "on")]
    if work is not None:
        mine = [e for e in every if e["work"] == work]
        start = clock.parse(mine[0]["at"]) if mine else now
        closing = [e for e in mine if e["type"] == "phase_change" and e["data"]["to"] == "closed"]
        end = clock.parse(closing[-1]["at"]) if closing else now
    else:
        mine = [e for e in every if e["work"] is not None]
        start, end = since, now

    vetoes = Counter(e["data"].get("rule", "?") for e in mine if e["type"] == "veto")
    opened = [e for e in mine if e["type"] == "block_opened"]
    tokens = Counter()
    for e in mine:
        if e["type"] == "subagent_stop" and e["data"].get("tokens"):
            tokens[e["data"].get("type") or "?"] += e["data"]["tokens"]
    fix = {}
    for e in mine:
        if e["type"] == "task_change":
            key = (e["work"], e["data"]["number"])
            fix[key] = max(fix.get(key, 0), e["data"].get("fix_rounds") or 0)
    phase_secs: dict[str, float] = defaultdict(float)
    by_work: dict[int, list[dict]] = defaultdict(list)
    for e in mine:
        if e["type"] == "phase_change":
            by_work[e["work"]].append(e)
    for changes in by_work.values():
        for phase, secs in _phase_seconds(changes, now).items():
            phase_secs[phase] += secs

    return {
        "vetoes": {"total": sum(vetoes.values()), "by_rule": dict(vetoes)},
        "needs_you": sum(1 for e in opened if e["data"].get("type") == "needs_you"),
        "blocks": len(opened),
        "waivers": sum(1 for e in mine if e["type"] == "waiver_added"),
        "finding_overrides": sum(1 for e in mine if e["type"] == "act"
                                 and e["data"].get("type") == "approve"
                                 and e["data"].get("object") == "finding"),
        "off_hours": _hours(_off_seconds(switches, start, end)),
        "phase_hours": {k: _hours(v) for k, v in phase_secs.items()},
        "tokens": {"total": sum(tokens.values()), "by_agent": dict(tokens)},
        "fix_rounds": sum(fix.values()),
        "review_cycles": sum(1 for e in mine if e["type"] == "review_cycle"),
    }
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Commit**

```bash
git add bin/tollgate_core/stats.py tests/test_stats.py
git commit -m "tollgate P1: statistiche dagli eventi (criterio 43)"
```

---

### Task 10: Sottocomandi `status`, `stats`, `events`, `db restore`

**Files:**
- Modify: `bin/tollgate_core/cli.py` (sostituisce lo scheletro del Task 1)
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: tutto quanto sopra; in particolare `db.open_db`, `db.restore`, `db.DbError`, `events.export_events`, `events.to_jsonl`, `phases.find_latest`, `stats.compute_stats`, `paths.resolve_state`, `paths.repo_key`.
- Produces:
  - `cli.main(argv: list[str]) -> int`: 0 se va bene, 1 per un errore spiegato su stderr, 2 per un errore di sintassi (argparse).
  - `cli.current_repo_key(cwd: Path) -> str | None`: chiave del repo dall'`origin` della cartella, `None` fuori da un repo o senza `origin`.
  - `tollgate status [--json]`: lavori non chiusi del repo corrente (di tutti i repo fuori da un repo), con fase, livello, task per stato e blocchi aperti. Sola lettura.
  - `tollgate stats [--since AAAA-MM-GG] [--work N]`: JSON di `compute_stats`; `N` è il numero dell'issue nel repo corrente, ultimo lavoro anche se chiuso.
  - `tollgate events --after-seq N`: JSONL (18.4), ordinato per `seq`.
  - `tollgate db restore`: chiama `db.restore` senza aprire prima il DB; interattivo solo se stdin e stdout sono un terminale.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_cli.py`:

```python
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import BIN, TempState, git, make_repo
from tollgate_core import clock, db, events, phases

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


class CliTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.repo = make_repo(Path(tempfile.mkdtemp()) / "r")
        git(self.repo, "remote", "add", "origin", "git@github.com:O/R.git")
        self.outside = Path(tempfile.mkdtemp())

    def tearDown(self):
        self.t.cleanup()

    def run_cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(BIN / "tollgate"), *args],
                              cwd=cwd or self.outside, env=self.t.env(), capture_output=True,
                              text=True, stdin=subprocess.DEVNULL)

    def seed(self):
        conn = db.open_db(self.t.state)
        w = phases.create_work(conn, repo_key="github.com/o/r", issue=5, level="L1", now=T0)
        phases.create_work(conn, repo_key="github.com/o/altro", issue=6, level="L0", now=T0)
        phases.open_block(conn, self.t.state, w, "needs_you", "budget del task 2", now=T0)
        conn.close()
        return w

    def test_no_args_prints_help(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertIn("status", r.stdout)

    def test_status_filters_by_repo(self):
        self.seed()
        r = self.run_cli("status", cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("#5 github.com/o/r", r.stdout)
        self.assertIn("blocco", r.stdout)
        self.assertIn("budget del task 2", r.stdout)
        self.assertNotIn("#6", r.stdout)
        everywhere = self.run_cli("status")
        self.assertIn("#6", everywhere.stdout)

    def test_status_json(self):
        self.seed()
        r = self.run_cli("status", "--json", cwd=self.repo)
        (item,) = json.loads(r.stdout)
        self.assertEqual((item["issue"], item["phase"], item["phase_before_block"]),
                         (5, "blocked", "plan"))
        self.assertEqual(item["blocks"][0]["type"], "needs_you")

    def test_events_after_seq(self):
        conn = db.open_db(self.t.state)
        for i in range(3):
            events.record_event(conn, "commit", {"i": i}, now=T0)
        conn.close()
        r = self.run_cli("events", "--after-seq", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([json.loads(x)["seq"] for x in r.stdout.splitlines()], [2, 3])

    def test_stats_work(self):
        self.seed()
        r = self.run_cli("stats", "--work", "5", cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["needs_you"], 1)
        missing = self.run_cli("stats", "--work", "99", cwd=self.repo)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("nessun lavoro", missing.stderr)
        outside = self.run_cli("stats", "--work", "5")
        self.assertEqual(outside.returncode, 1)
        self.assertEqual(self.run_cli("stats", "--since", "ieri").returncode, 2)

    def test_corrupt_db(self):
        self.t.state.db_path.write_bytes(os.urandom(4096))
        r = self.run_cli("status")
        self.assertEqual(r.returncode, 1)
        self.assertIn("db restore", r.stderr)
        r = self.run_cli("db", "restore")
        self.assertEqual(r.returncode, 1)
        self.assertIn("terminale", r.stderr)

    def test_restore_refuses_healthy_db(self):
        db.open_db(self.t.state).close()
        r = self.run_cli("db", "restore")
        self.assertEqual(r.returncode, 1)
        self.assertIn("integro", r.stderr)
```

- [ ] **Step 2: Eseguire i test e vederli fallire**

Run: `tests/run`
Expected: FAIL in `tests.test_cli`, per esempio `test_status_filters_by_repo` con `returncode 2` (sottocomando sconosciuto).

- [ ] **Step 3: Scrivere il codice**

`bin/tollgate_core/cli.py` (intero):

```python
"""Sottocomandi di bin/tollgate (spec 3.1). P1: status, stats, events, db restore."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import VERSION, clock, db, events, phases, stats
from .paths import repo_key, resolve_state


class UsageError(Exception):
    pass


def current_repo_key(cwd: Path) -> str | None:
    r = subprocess.run(["git", "-C", str(cwd), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    url = r.stdout.strip()
    return repo_key(url) if r.returncode == 0 and url else None


def _date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise argparse.ArgumentTypeError("data attesa nella forma AAAA-MM-GG") from e


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tollgate", description="CLI di tollgate")
    p.add_argument("--version", action="version", version=f"tollgate {VERSION}")
    sub = p.add_subparsers(dest="cmd")
    st = sub.add_parser("status", help="stato dei lavori attivi (sola lettura)")
    st.add_argument("--json", action="store_true", help="uscita in JSON")
    sp = sub.add_parser("stats", help="statistiche dagli eventi, in JSON")
    sp.add_argument("--since", type=_date, metavar="AAAA-MM-GG")
    sp.add_argument("--work", type=int, metavar="N", help="numero dell'issue nel repo corrente")
    ep = sub.add_parser("events", help="eventi in JSONL dopo un seq")
    ep.add_argument("--after-seq", type=int, default=0, metavar="N")
    dp = sub.add_parser("db", help="manutenzione del DB")
    dsub = dp.add_subparsers(dest="db_cmd", required=True)
    dsub.add_parser("restore", help="ripristina l'ultima copia integra (solo da terminale)")
    return p


def _status(conn, key: str | None) -> list[dict]:
    sql, params = "SELECT * FROM work_items WHERE phase <> 'closed'", []
    if key:
        sql += " AND repo_key = ?"
        params.append(key)
    out = []
    for w in conn.execute(sql + " ORDER BY repo_key, issue", params).fetchall():
        blocks = [{"id": b["id"], "type": b["type"], "reason": b["reason"]}
                  for b in conn.execute("SELECT id, type, reason FROM blocks WHERE work = ? "
                                        "AND closed IS NULL ORDER BY id", (w["id"],))]
        counts = {r["state"]: r["n"] for r in conn.execute(
            "SELECT state, count(*) AS n FROM tasks WHERE work = ? GROUP BY state", (w["id"],))}
        out.append({"issue": w["issue"], "repo_key": w["repo_key"], "level": w["level"],
                    "level_cap": w["level_cap"], "phase": w["phase"],
                    "phase_before_block": w["phase_before_block"], "branch": w["branch"],
                    "blocks": blocks, "tasks": counts})
    return out


def _print_status(items: list[dict]) -> None:
    if not items:
        print("nessun lavoro attivo")
        return
    for it in items:
        phase = it["phase"]
        if phase == "blocked":
            phase += f" (prima: {it['phase_before_block']})"
        print(f"#{it['issue']} {it['repo_key']}  fase {phase}  livello {it['level']}")
        if it["tasks"]:
            print("  task: " + ", ".join(f"{n} {s}" for s, n in sorted(it["tasks"].items())))
        for b in it["blocks"]:
            print(f"  blocco {b['id']} ({b['type']}): {b['reason']}")


def _restore(state) -> int:
    interactive = sys.stdin.isatty() and sys.stdout.isatty()

    def confirm(question: str) -> bool:
        return input(question).strip().lower() in ("s", "si", "sì", "y", "yes")

    print(db.restore(state, interactive=interactive, confirm=confirm))
    return 0


def _stats(conn, args) -> int:
    work = None
    if args.work is not None:
        key = current_repo_key(Path.cwd())
        if key is None:
            raise UsageError("--work richiede di essere in un repo con origin")
        row = phases.find_latest(conn, key, args.work)
        if row is None:
            raise UsageError(f"nessun lavoro per #{args.work} in {key}")
        work = row["id"]
    result = stats.compute_stats(conn, now=clock.now(), work=work, since=args.since)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    state = resolve_state()
    try:
        if args.cmd == "db":
            return _restore(state)
        conn = db.open_db(state)
        try:
            if args.cmd == "status":
                items = _status(conn, current_repo_key(Path.cwd()))
                if args.json:
                    print(json.dumps(items, ensure_ascii=False, indent=2))
                else:
                    _print_status(items)
                return 0
            if args.cmd == "stats":
                return _stats(conn, args)
            if args.cmd == "events":
                sys.stdout.write(events.to_jsonl(events.export_events(conn, args.after_seq)))
                return 0
        finally:
            conn.close()
    except (db.DbError, UsageError) as e:
        print(f"tollgate: {e}", file=sys.stderr)
        return 1
    return 0
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python.

- [ ] **Step 5: Prova a mano dal terminale**

Run: `TOLLGATE_STATE=$(mktemp -d) && touch $TOLLGATE_STATE/.tollgate-test && TOLLGATE_STATE=$TOLLGATE_STATE bin/tollgate status && TOLLGATE_STATE=$TOLLGATE_STATE bin/tollgate stats`
Expected: `nessun lavoro attivo`, poi un JSON con `"vetoes": {"by_rule": {}, "total": 0}`.

- [ ] **Step 6: Commit**

```bash
git add bin/tollgate_core/cli.py tests/test_cli.py
git commit -m "tollgate P1: sottocomandi status, stats, events e db restore"
```

---

### Task 11: Chiusura di P1 nel piano principale

**Files:**
- Modify: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (stato in testa, sezione 3 «Pacchetti» e «Contratti»)

**Interfaces:**
- Consumes: i nomi reali prodotti dai Task 1-10.

- [ ] **Step 1: Verificare la suite intera**

Run: `tests/run`
Expected: `OK` con entrambe le versioni di Python, nessun test saltato.

- [ ] **Step 2: Aggiornare il piano principale**

Regola 6 del piano principale. Modifiche:
- in testa, «Stato»: P1 chiuso, con il percorso di questo piano;
- sezione 3, riga `tollgate_core`: i moduli reali (`paths`, `clock`, `config`, `db`, `events`, `phases`, `tasks`, `acts`, `dod`, `stats`, `cli`);
- sezione 3, «Contratti» prodotti da P1: sostituire i nomi indicativi con le firme reali di `load_config`, `open_db`, `tx`, `backup`, `record_event`, `export_events`, `set_phase`, `open_block`, `close_block`, `task_event`, `record_act`, `find_usable`, `consume`, `invalidate_finish`, `compute_dod`;
- aggiungere una riga ai contratti: «P2 e P3 scrivono nel DB solo con le funzioni di `tollgate_core`, dentro `db.tx`; `set_phase`, `open_block` e `close_block` vanno chiamati fuori da una transazione, perché fanno la copia del DB dopo il commit».

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "piano principale: P1 chiuso, interfacce reali di tollgate_core"
```
