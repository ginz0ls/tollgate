"""Banco di prova del flusso (P3a): repo con gate, stato e HOME temporanei, finto gh.

Compone `hookkit.Lab` (stessi `ts`, `tmp`, `main`, `origin`, `conn`, sessione `sess-flow`) e vi
aggiunge ciò che serve alla CLI: HOME temporanea con Superpowers, `gh` finto, segnale della
sessione prima di ogni chiamata a `bin/tollgate`."""
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from tests.helpers import BIN, ROOT, git
from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML, Lab
from tests.test_check_post_edit import SECTIONS
from tollgate_core import VERSION, clock, events, phases, sessions, tasks as task_store

SESSION = "sess-flow"
ORIGIN_URL = "https://github.com/prova/flow.git"
FAKEGH = ROOT / "tests" / "fakegh.py"
PLAN = "docs/superpowers/plans/2026-10-16-somma.md"
GATE_FILES = {f".github/workflows/tollgate-{n}.yml": f"name: tollgate-{n}\n"
              for n in ("guard", "run", "verdict", "base", "sentinel")}

# Script del banco per i must-have: scrive reports/junit.xml con i test di tests/ids.txt
# (una riga `classname::name ok` oppure `classname::name fail` per test) ed esce 1 se ce n'è uno
# che fallisce. Il repo del banco lo riceve da solo se il tollgate.toml lo nomina.
JUNIT_FAKE = """import pathlib
import sys
from xml.sax.saxutils import quoteattr

ids = pathlib.Path("tests/ids.txt")
cases, failed = [], False
for line in ids.read_text().splitlines() if ids.exists() else []:
    parts = line.split()
    if len(parts) != 2 or parts[1] not in ("ok", "fail"):
        continue
    classname, _, name = parts[0].partition("::")
    body = "<failure message=\\"x\\"/>" if parts[1] == "fail" else ""
    failed = failed or parts[1] == "fail"
    cases.append(f"<testcase classname={quoteattr(classname)} name={quoteattr(name)}>{body}"
                 "</testcase>")
out = pathlib.Path("reports")
out.mkdir(exist_ok=True)
(out / "junit.xml").write_text("<testsuite>" + "".join(cases) + "</testsuite>")
sys.exit(1 if failed else 0)
"""
JUNIT_FILES = {"tools/junit_fake.py": JUNIT_FAKE}
JUNIT_TOML = """schema_version = 1
[gate]
mode = "protected"
[commands]
verify = "python3 tools/junit_fake.py"
gate = ["verify"]
report = "junit:reports/junit.xml"
"""


def plan_text(task2="- Create: `docs/uso.md`", tasks=2):
    """Piano valido per plan-check: il Task 1 tocca src/app.py, il Task 2 il file `task2`;
    da `tasks` = 3 in poi altri task con un file ciascuno, con `tasks` = 1 solo il primo."""
    out = []
    for s in SECTIONS:
        body = ("M1. Somma — test: tests.test_app::test_somma\n"
                "M2. Zero — test: tests.test_app::test_zero") if s == "Must-have" else "x"
        out += [f"## {s}", body, ""]
    out += ["### Task 1: Somma", "- Modify: `src/app.py`", "- Test: `tests/test_app.py`",
            "**Must-have**: M1", ""]
    if tasks >= 2:
        out += ["### Task 2: Pagina", task2, ""]
    for k in range(3, tasks + 1):
        out += [f"### Task {k}: Extra {k}", f"- Create: `docs/extra-{k}.md`", ""]
    return "\n".join(out) + "\n"


class FlowLab:
    def __init__(self, *, toml=DEFAULT_TOML, files=None, gate=True, issue=None, level="L1",
                 phase="execution"):
        tree = dict(DEFAULT_FILES, **(files or {}))
        if "junit_fake" in toml:
            tree.update(JUNIT_FILES)
        if gate:
            tree.update(GATE_FILES)
            tree[".github/tollgate/VERSION"] = VERSION + "\n"
        self.lab = Lab(level=level, phase=phase, toml=toml, files=tree,
                       work=issue is not None, session=SESSION,
                       issue=issue or 7, origin_url=ORIGIN_URL,
                       worktree=issue is not None)
        self.ts, self.tmp, self.main, self.origin = (self.lab.ts, self.lab.tmp, self.lab.main,
                                                     self.lab.origin)
        self.conn, self.work, self.wt = self.lab.conn, self.lab.work, self.lab.wt
        self.home = self.tmp / "home dir"
        plugins = self.home / ".claude" / "plugins"
        plugins.mkdir(parents=True)
        (plugins / "installed_plugins.json").write_text(json.dumps({
            "version": 2,
            "plugins": {"superpowers@claude-plugins-official": [{
                "scope": "user", "version": "7.0.0",
                "installPath": str(plugins / "superpowers")}]}}))
        self.gh_data = self.tmp / "fakegh-data.json"
        self.gh_log = self.tmp / "fakegh.log"
        self.set_gh()

    def __getattr__(self, name):
        """pre_edit, post_edit, bash, goto, events... sono quelli di hookkit.Lab."""
        if name == "lab":
            raise AttributeError(name)
        return getattr(self.lab, name)

    def set_gh(self, **data) -> None:
        """Riscrive i dati letti dal finto gh (vedi tests/fakegh.py)."""
        self.gh_data.write_text(json.dumps(data))

    def gh_calls(self) -> list[dict]:
        if not self.gh_log.exists():
            return []
        return [json.loads(x) for x in self.gh_log.read_text().splitlines()]

    def env(self) -> dict:
        e = self.ts.env()
        e.update(TOLLGATE_GH=str(FAKEGH), TOLLGATE_FAKEGH_DATA=str(self.gh_data),
                 TOLLGATE_FAKEGH_LOG=str(self.gh_log), HOME=str(self.home))
        return e

    def cli(self, *argv, cwd=None, session=SESSION) -> subprocess.CompletedProcess:
        """Scrive il segnale come farebbe l'hook di PreToolUse, poi esegue bin/tollgate."""
        cwd = str(cwd or self.main)
        sessions.note_cli_call(self.ts.state, session, cwd, list(argv), now=clock.now())
        return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), *argv], cwd=cwd,
                              env=self.env(), capture_output=True, text=True, timeout=120)

    def hook(self, payload, now=None):
        return self.lab.hook(payload, now=now)

    def git(self, *args, repo=None):
        return git(repo or self.main, *args)

    def register_plan(self, tasks: int = 1) -> None:
        """Il piano L1 di `plan_text` (task 1 e, se `tasks` > 1, i seguenti) registrato come
        farebbe l'hook di PostToolUse: scope, task `pending` e fase `execution`.
        Richiede il lavoro in fase `plan`."""
        path = self.wt / PLAN
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan_text(tasks=tasks))
        r = self.lab.post_edit(path)
        if r.exit != 0:
            raise AssertionError(f"piano rifiutato dall'hook: {r.stderr}")
        phase = phases.get_work(self.conn, self.work)["phase"]
        if phase != "execution":
            raise AssertionError(f"dopo il piano la fase è {phase}, non execution")

    def commit(self, path, text, msg) -> str:
        """Scrive `path` nel worktree, lo committa e registra l'evento `commit` che scriverebbe
        l'hook di PostToolUse. Restituisce lo SHA."""
        target = self.wt / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        git(self.wt, "add", "--", str(path))
        git(self.wt, "commit", "-q", "-m", msg)
        sha = git(self.wt, "rev-parse", "HEAD")
        self.lab.now += timedelta(seconds=1)
        events.record_event(self.conn, "commit", {"sha": sha}, now=self.lab.now,
                            session=SESSION, work=self.work)
        return sha

    def close_tasks(self) -> None:
        """Ogni task del lavoro `done` con verdetto `approved`, passando per le transizioni."""
        for row in self.conn.execute("SELECT number FROM tasks WHERE work = ? ORDER BY number",
                                     (self.work,)).fetchall():
            state = task_store.get_task(self.conn, self.work, row["number"])["state"]
            for event in {"pending": ("start", "report_done", "approved"),
                          "running": ("report_done", "approved"),
                          "review": ("approved",), "done": ()}.get(state, ()):
                self.lab.now += timedelta(seconds=1)
                task_store.task_event(self.conn, self.work, row["number"], event, now=self.lab.now)
            if task_store.get_task(self.conn, self.work, row["number"])["state"] != "done":
                raise AssertionError(f"task {row['number']} non chiudibile da {state}")

    def close(self) -> None:
        self.lab.close()
