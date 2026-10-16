### Task 10: Sottocomando `verify` (8.1)

**Files:**
- Create: `bin/tollgate_core/verify.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `verify`)
- Modify: `tests/helpers.py` (funzione `make_origin_repo`)
- Test: `tests/test_verify.py`

**Interfaces:**
- Consumes: `config.load_config`, `git.*`, `sessions.work_for_path`, `receipts.add`, `profiles.active_profiles`, `junit.parse_junit`, `paths.resolve_state`, `db.open_db`.
- Produces:
  - `verify.CommandSpec(name, command, report)`; `verify.gate_commands(cfg, files) -> list[CommandSpec]` (comandi del gate più i `gate` dei profili attivi; un nome di profilo diventa `profile:<profilo>:<comando>`); `verify.receipt_state(*, exit_code, report_configured, junit, allow_no_tests) -> str`; `verify.clean_env(env_allow, environ) -> dict`; `verify.run_verify(state, cwd, *, related=False, now=None, environ=None) -> tuple[int, list[str]]` (uscita e righe da stampare).
  - CLI: `tollgate verify [--related]`, uscita 0 se ogni ricevuta vale verde (anche `empty` o `uncounted` con `allow_no_tests` e uscita 0), 1 altrimenti.
  - `tests.helpers.make_origin_repo(root: Path, files: dict[str, str], toml: str) -> tuple[Path, Path, str]` (checkout principale, origin nudo, SHA della base), usato anche dal banco degli hook.

- [ ] **Step 1: Banco di prova con origin**

In `tests/helpers.py` aggiungere:

```python
def make_origin_repo(root, files: dict, toml: str):
    """Origin nudo e checkout principale con tollgate.toml sul predefinito (repo attivo, 7.1)."""
    root = Path(root)
    origin = root / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True,
                   capture_output=True)
    main = make_repo(root / "main")
    (main / "tollgate.toml").write_text(toml)
    for rel, text in files.items():
        p = main / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    git(main, "add", "-A")
    git(main, "commit", "-qm", "base")
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "-u", "origin", "main")
    git(main, "remote", "set-head", "origin", "main")
    git(main, "config", "tollgate.defaultBranch", "main")
    return main, origin, git(main, "rev-parse", "HEAD")
```

- [ ] **Step 2: Test**

`tests/test_verify.py`:

```python
import shutil
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.helpers import TempState, git, make_origin_repo
from tollgate_core import config, db, phases, verify
from tollgate_core.paths import repo_key
from tollgate_analysis.junit import Junit

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
TOML = textwrap.dedent('''
    schema_version = 1
    [gate]
    mode = "protected"
    [commands]
    verify = "sh check.sh"
    test_related = "sh related.sh {files}"
    gate = ["verify"]
    report = "junit:reports/junit.xml"
    report_related = "junit:reports/junit-related.xml"
    env_allow = ["PATH", "HOME"]
    [profiles.web]
    paths = ["web/**"]
    commands = { lint = "sh lint.sh" }
    gate = ["lint"]
''')
CHECK = textwrap.dedent('''
    mkdir -p reports
    test -n "$SEGRETO" && echo "segreto visibile" && exit 3
    cat > reports/junit.xml <<EOF
    <testsuite><testcase classname="t" name="a"/><testcase classname="t" name="b"><skipped/></testcase></testsuite>
    EOF
''')


class VerifyUnitTest(unittest.TestCase):
    def test_receipt_state(self):
        j = Junit(total=2, skipped=0, failed=0)
        st = verify.receipt_state
        self.assertEqual(st(exit_code=0, report_configured=True, junit=j, allow_no_tests=False),
                         "green")
        self.assertEqual(st(exit_code=1, report_configured=True, junit=j, allow_no_tests=False),
                         "red")
        self.assertEqual(st(exit_code=0, report_configured=True,
                            junit=Junit(total=1, failed=1), allow_no_tests=False), "red")
        self.assertEqual(st(exit_code=0, report_configured=True, junit=Junit(),
                            allow_no_tests=False), "empty")
        self.assertEqual(st(exit_code=0, report_configured=True, junit=None,
                            allow_no_tests=True), "red")
        self.assertEqual(st(exit_code=0, report_configured=False, junit=None,
                            allow_no_tests=True), "uncounted")

    def test_clean_env(self):
        self.assertEqual(verify.clean_env(["PATH"], {"PATH": "/bin", "TOKEN": "x"}),
                         {"PATH": "/bin"})

    def test_gate_commands_with_profiles(self):
        cfg = config.load_config_text(TOML)
        names = [c.name for c in verify.gate_commands(cfg, ["src/a.py"])]
        self.assertEqual(names, ["verify"])
        names = [c.name for c in verify.gate_commands(cfg, ["web/a.ts"])]
        self.assertEqual(names, ["verify", "profile:web:lint"])


class VerifyRunTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-verify-"))
        self.main, _, self.base = make_origin_repo(
            self.tmp, {"check.sh": CHECK, "related.sh": "exit 0\n",
                       ".gitignore": "reports/\n"}, TOML)
        self.wt = self.tmp / "wt"
        git(self.main, "worktree", "add", "-q", "-b", "tg/7-x", str(self.wt))
        conn = db.open_db(self.ts.state)
        self.work = phases.create_work(conn, repo_key=repo_key(str(self.tmp / "origin.git")),
                                       issue=7, level="L1", now=T0, worktree=str(self.wt),
                                       branch="tg/7-x", work_base_sha=self.base)
        conn.close()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _receipts(self):
        conn = db.open_db(self.ts.state)
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM receipts ORDER BY id")]
        finally:
            conn.close()

    def test_green_receipt_and_clean_env(self):
        (self.wt / "reports").mkdir()
        (self.wt / "reports" / "junit.xml").write_text("<vecchio/>")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin", "SEGRETO": "x"})
        self.assertEqual(code, 0, lines)
        r = self._receipts()[0]
        self.assertEqual((r["state"], r["tests_run"], r["tests_skipped"], r["work"], r["sha"]),
                         ("green", 1, 1, self.work, self.base))

    def test_dirty_worktree_refused(self):
        (self.wt / "sporco.txt").write_text("x")
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual(code, 1)
        self.assertIn("worktree non pulito", " ".join(lines))
        self.assertEqual(self._receipts(), [])

    def test_config_read_from_work_base(self):
        (self.wt / "tollgate.toml").write_text(TOML.replace('verify = "sh check.sh"', ""))
        git(self.wt, "commit", "-qam", "senza verify")
        code, _ = verify.run_verify(self.ts.state, self.wt, now=T0,
                                    environ={"PATH": "/usr/bin:/bin"})
        # la configurazione si legge dalla base del lavoro, non dal working tree (3.2)
        self.assertEqual(self._receipts()[0]["state"], "green")
        self.assertEqual(code, 0)

    def test_missing_command_is_unverified(self):
        cfg = self.tmp / "cfg.toml"
        cfg.write_text(TOML.replace('verify = "sh check.sh"\n', ""))
        code, lines = verify.run_verify(self.ts.state, self.wt, now=T0,
                                        environ={"PATH": "/usr/bin:/bin",
                                                 "TOLLGATE_TEST_CONFIG": str(cfg)})
        self.assertEqual(code, 1)
        self.assertEqual(self._receipts()[0]["state"], "unverified")
        self.assertIn("approve unverified-tests", " ".join(lines))

    def test_related_without_files_runs_gate(self):
        code, lines = verify.run_verify(self.ts.state, self.wt, related=True, now=T0,
                                        environ={"PATH": "/usr/bin:/bin"})
        self.assertEqual([r["command"] for r in self._receipts()], ["verify"])
        self.assertEqual(code, 0, lines)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_verify -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'tollgate_core.verify'`.

- [ ] **Step 4: `verify.py`**

```python
"""tollgate verify (spec 8.1): comandi del gate su HEAD, ambiente ripulito, ricevute."""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from tollgate_analysis import profiles as prof
from tollgate_analysis.junit import Junit, JunitError, parse_junit

from . import clock, db, git, receipts, sessions
from .config import Config, ConfigError, load_config
from .paths import State, ensure_dirs


@dataclass(frozen=True)
class CommandSpec:
    name: str
    command: str
    report: str


def _report_for(report, name: str) -> str:
    if isinstance(report, dict):
        return report.get(name, "")
    return report or ""


def _report_path(spec: str) -> str | None:
    return spec.split(":", 1)[1] if spec.startswith("junit:") else (spec or None)


def gate_commands(cfg: Config, files) -> list[CommandSpec]:
    cmds = cfg.get("commands")
    out = [CommandSpec(n, cmds.get(n, ""), _report_for(cmds["report"], n))
           for n in cmds["gate"]]
    profs = cfg.profiles
    for name in prof.active_profiles(files, profs, cfg.get("profiles.active")):
        p = profs[name]
        for n in p["gate"]:
            out.append(CommandSpec(f"profile:{name}:{n}", p["commands"].get(n, ""),
                                   _report_for(p["report"], n)))
    return out


def receipt_state(*, exit_code: int, report_configured: bool, junit: Junit | None,
                  allow_no_tests: bool) -> str:
    if report_configured and junit is None:
        return "red"     # report configurato e assente: resta rosso (8.1, decisione 11)
    if junit is None:
        return "red" if exit_code != 0 else "uncounted"
    if exit_code != 0 or junit.failed:
        return "red"
    if junit.total - junit.skipped == 0:
        return "empty"
    return "green"


def clean_env(env_allow, environ) -> dict:
    return {k: environ[k] for k in env_allow if k in environ}


def counts_green(state: str, exit_code: int, allow_no_tests: bool) -> bool:
    return state == "green" or (allow_no_tests and (
        state == "empty" or (state == "uncounted" and exit_code == 0)))


def _run_one(spec: CommandSpec, *, root: Path, files: list[str], env: dict, timeout_s: int,
             allow_no_tests: bool, log_dir: Path, tag: str):
    resolved = spec.command.replace("{files}", " ".join(shlex.quote(f) for f in files))
    report_rel = _report_path(spec.report)
    report = root / report_rel if report_rel else None
    if report is not None:
        report.unlink(missing_ok=True)
    log = log_dir / f"{tag}-{spec.name.replace(':', '_')}.log"
    t0 = time.monotonic()
    try:
        with open(log, "wb") as fh:
            exit_code = subprocess.run(["/bin/sh", "-c", resolved], cwd=root, env=env,
                                       stdout=fh, stderr=subprocess.STDOUT,
                                       timeout=timeout_s).returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    duration = time.monotonic() - t0
    junit = None
    if report is not None and report.is_file():
        try:
            junit = parse_junit(report.read_bytes())
        except JunitError as e:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"\n[tollgate] report non valido: {e}\n")
    state = receipt_state(exit_code=exit_code, report_configured=report is not None,
                          junit=junit, allow_no_tests=allow_no_tests)
    return resolved, exit_code, junit, duration, state, log


def run_verify(state: State, cwd, *, related: bool = False, now=None,
               environ=None) -> tuple[int, list[str]]:
    environ = os.environ if environ is None else environ
    root = git.toplevel(cwd)
    if root is None:
        return 1, ["tollgate verify: non sei in un repo git"]
    conn = db.open_db(state)
    try:
        work = sessions.work_for_path(conn, root)
        ref = work["work_base_sha"] if work is not None and work["work_base_sha"] \
            else git.default_ref(root)
        if ref is None:
            return 1, ["tollgate verify: nessun riferimento remoto da cui leggere tollgate.toml"]
        try:
            cfg = load_config(state, root, ref, env=environ)
        except ConfigError as e:
            return 1, [f"tollgate verify: {e}"]
        exclude = cfg.get("review.output_dirs") + [".tollgate-run/"]
        if not git.is_clean(root, exclude):
            return 1, ["tollgate verify: worktree non pulito: committa prima di verificare"]
        sha = git.head(root)
        base = ref if work is None else work["work_base_sha"]
        changed = [c for c in git.changes(root, base, head=sha) if c.status != "D"]
        files = [c.path for c in changed]
        allow = cfg.get("project.allow_no_tests")
        cmds = cfg.get("commands")
        specs = gate_commands(cfg, files)
        related_files = files
        if related and cmds["test_related"] and related_files:
            specs = [CommandSpec("related", cmds["test_related"], cmds["report_related"])]
        env = clean_env(cfg.get("commands.env_allow"), environ)
        log_dir = state.root / "logs"
        ensure_dirs(state)
        log_dir.mkdir(mode=0o700, exist_ok=True)
        now = now or clock.now()
        tag = f"{work['issue'] if work is not None else 'repo'}-{sha[:7]}-" \
              f"{now.strftime('%Y%m%dT%H%M%S')}"
        lines, all_ok = [], True
        for spec in specs:
            if not spec.command:
                receipts.add(conn, work=work["id"] if work is not None else None, sha=sha,
                             command=spec.name, resolved_command=None, exit_code=None,
                             tests_run=None, tests_skipped=None, duration=None, log=None,
                             produced_by="verify", state="unverified", now=now)
                lines.append(f"{spec.name}: unverified (comando non configurato: serve "
                             f"/tollgate:approve unverified-tests)")
                all_ok = False
                continue
            resolved, exit_code, junit, duration, st, log = _run_one(
                spec, root=root, files=related_files if spec.name == "related" else files,
                env=env, timeout_s=cfg.get("commands.timeout_s"), allow_no_tests=allow,
                log_dir=log_dir, tag=tag)
            receipts.add(conn, work=work["id"] if work is not None else None, sha=sha,
                         command=spec.name, resolved_command=resolved, exit_code=exit_code,
                         tests_run=(junit.total - junit.skipped) if junit else None,
                         tests_skipped=junit.skipped if junit else None, duration=duration,
                         log=str(log), produced_by="verify", state=st, now=now)
            good = counts_green(st, exit_code, allow)
            all_ok = all_ok and good
            run = f", {junit.total - junit.skipped} test" if junit else ""
            lines.append(f"{spec.name}: {st} (uscita {exit_code}{run}; log {log})")
        return (0 if all_ok else 1), lines
    finally:
        conn.close()
```

- [ ] **Step 5: CLI**

In `bin/tollgate_core/cli.py`: in `build_parser`, dopo il sottocomando `events`:

```python
    vp = sub.add_parser("verify", help="esegue i comandi del gate e registra le ricevute (8.1)")
    vp.add_argument("--related", action="store_true", help="solo i test correlati ai file cambiati")
```

In `main`, prima di `conn = db.open_db(state)` (dentro il `try`):

```python
        if args.cmd == "verify":
            from . import verify
            code, lines = verify.run_verify(state, Path.cwd(), related=args.related)
            print("\n".join(lines))
            return code
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK. `test_missing_command_is_unverified` dimostra che la configurazione si legge dalla base: il `tollgate.toml` modificato nel ramo non conta. Se fallisce perché `verify` ha letto il working tree, è un difetto del codice.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_core/verify.py bin/tollgate_core/cli.py tests/helpers.py tests/test_verify.py
git commit -m "tollgate P2: sottocomando verify con ricevute e ambiente ripulito"
```

---

