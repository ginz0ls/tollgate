"""tollgate verify (spec 8.1): comandi del gate su HEAD, ambiente ripulito, ricevute."""
from __future__ import annotations

import contextlib
import os
import shlex
import signal
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from tollgate_analysis import profiles as prof
from tollgate_analysis.junit import Junit, JunitError, parse_junit

from . import clock, db, git, receipts, sessions
from .config import Config, ConfigError, load_config, output_excludes
from .paths import State, ensure_dirs

TIMEOUT_EXIT = 124


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
    """Percorso del report relativo al worktree. Assoluto o con `..` è rifiutato, prima di ogni unlink."""
    rel = spec.split(":", 1)[1] if spec.startswith("junit:") else spec
    if not rel:
        return None
    path = PurePosixPath(rel)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError(f"report {rel!r} non valido: deve essere un percorso relativo al "
                          f"worktree, senza '..'")
    return rel


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
    # le variabili di test TOLLGATE_* non arrivano mai al comando, nemmeno se in env_allow
    return {k: environ[k] for k in env_allow
            if k in environ and not k.startswith("TOLLGATE_")}


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
    timed_out = False
    with open(log, "wb") as fh:
        # sessione propria: al timeout si uccide l'intero gruppo, figli in background compresi
        proc = subprocess.Popen(["/bin/sh", "-c", resolved], cwd=root, env=env,
                                stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            proc.communicate(timeout=timeout_s)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            exit_code = TIMEOUT_EXIT
            timed_out = True
    duration = time.monotonic() - t0
    if timed_out:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"\n[tollgate] timeout dopo {timeout_s} s\n")
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
    """Esegue i comandi e registra le ricevute. Errori di git o del DB diventano uscita 1."""
    environ = os.environ if environ is None else environ
    try:
        return _verify(state, cwd, related=related, now=now, environ=environ)
    except git.GitError as e:
        return 1, [f"tollgate verify: {e}"]
    except sqlite3.Error as e:
        return 1, [f"tollgate verify: errore del database: {e}"]


def _verify(state, cwd, *, related: bool, now, environ) -> tuple[int, list[str]]:
    root = git.toplevel(cwd)
    if root is None:
        return 1, ["tollgate verify: non sei in un repo git"]
    conn = db.open_db(state)
    try:
        work = sessions.work_for_path(conn, root)
        wid = work["id"] if work is not None else None
        # C13: senza work_base_sha si usa il riferimento di base del repo, mai None
        base = (work["work_base_sha"] if work is not None else None) or git.default_ref(root)
        if base is None:
            return 1, ["tollgate verify: nessun riferimento remoto da cui leggere tollgate.toml"]
        try:
            cfg = load_config(state, root, base, env=environ)
        except ConfigError as e:
            return 1, [f"tollgate verify: {e}"]
        exclude = output_excludes(cfg)
        if not git.is_clean(root, exclude):
            return 1, ["tollgate verify: worktree non pulito: committa prima di verificare"]
        sha = git.head(root)
        if sha is None:
            return 1, ["tollgate verify: nessun commit da verificare"]
        files = [c.path for c in git.changes(root, base, head=sha) if c.status != "D"]
        allow = cfg.get("project.allow_no_tests")
        cmds = cfg.get("commands")
        # decisione 12: --related esegue test_related sui file cambiati; se non trova test
        # ripiega sul gate completo (8.1)
        use_related = related and bool(files) and bool(cmds["test_related"])
        related_spec = CommandSpec("related", cmds["test_related"], cmds["report_related"])
        gate = gate_commands(cfg, files)
        # i percorsi dei report si validano prima di eseguire o cancellare alcunché
        try:
            for spec in ([related_spec] if use_related else []) + gate:
                _report_path(spec.report)
        except ConfigError as e:
            return 1, [f"tollgate verify: {e}"]
        env = clean_env(cfg.get("commands.env_allow"), environ)
        timeout_s = cfg.get("commands.timeout_s")
        now = now or clock.now()
        ensure_dirs(state)
        log_dir = state.root / "logs"
        log_dir.mkdir(mode=0o700, exist_ok=True)
        tag = (f"{work['issue'] if work is not None else 'repo'}-{sha[:7]}-"
               f"{now.strftime('%Y%m%dT%H%M%S')}")

        def execute(spec: CommandSpec) -> tuple[str, bool, str]:
            if not spec.command:
                receipts.add(conn, work=wid, sha=sha, command=spec.name, resolved_command=None,
                             exit_code=None, tests_run=None, tests_skipped=None, duration=None,
                             log=None, produced_by="verify", state="unverified", now=now)
                return "unverified", False, (f"{spec.name}: unverified (comando non configurato: "
                                             f"serve /tollgate:approve unverified-tests)")
            resolved, exit_code, junit, duration, st, log = _run_one(
                spec, root=root, files=files, env=env, timeout_s=timeout_s,
                allow_no_tests=allow, log_dir=log_dir, tag=tag)
            receipts.add(conn, work=wid, sha=sha, command=spec.name, resolved_command=resolved,
                         exit_code=exit_code,
                         tests_run=(junit.total - junit.skipped) if junit else None,
                         tests_skipped=junit.skipped if junit else None, duration=duration,
                         log=str(log), produced_by="verify", state=st, now=now)
            good = counts_green(st, exit_code, allow)
            run = f", {junit.total - junit.skipped} test" if junit else ""
            line = f"{spec.name}: {st} (uscita {exit_code}{run}; log {log})"
            if st == "uncounted" and not good:
                line += ("; uncounted: il comando è uscito 0 senza report, quindi non conta i test;"
                         " con allow_no_tests = false il verdetto è rosso")
            return st, good, line

        lines: list[str] = []
        if use_related:
            st, good, line = execute(related_spec)
            lines.append(line)
            if st != "empty":
                return (0 if good else 1), lines
            lines.append("nessun test correlato: si esegue il gate completo")
        all_ok = True
        for spec in gate:
            st, good, line = execute(spec)
            all_ok = all_ok and good
            lines.append(line)
        return (0 if all_ok else 1), lines
    finally:
        conn.close()
