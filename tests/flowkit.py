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
from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML, Lab, sample
from tests.test_check_post_edit import SECTIONS
from tollgate_analysis import approvals, auditrules
from tollgate_core import (VERSION, audits, clock, events, git as core_git, phases, sessions,
                           subagents, tasks as task_store)
from tollgate_flow import gitw, start as flow_start

SESSION = "sess-flow"
ORIGIN_URL = "https://github.com/prova/flow.git"
FAKEGH = ROOT / "tests" / "fakegh.py"
PLAN = "docs/superpowers/plans/2026-10-16-somma.md"
SPEC = "docs/superpowers/specs/2026-10-20-prova.md"
ZERO_COUNTS = {k: 0 for k in auditrules.SEVERITIES}
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


def spec_text(slices: int = 1, pitch: bool = True, note: str = "") -> str:
    """Spec L2 con `slices` fette previste; senza `pitch` mancano «Tane di coniglio» e «Cosa non
    fare». `note` cambia il blob senza cambiare la forma."""
    out = ["# Prova", "", "## Obiettivo", "x", "", "## Fette previste"]
    out += [f"{k}. Fetta {k}" for k in range(1, slices + 1)]
    if pitch:
        out += ["", "## Tane di coniglio", "- nessuna, scelta fatta", "", "## Cosa non fare",
                "- niente extra"]
    if note:
        out += ["", note]
    return "\n".join(out) + "\n"


def round_message(row, counts: dict | None = None, *, kind: str | None = None) -> str:
    """Il messaggio finale di un agente di giro: un po' di prosa e la riga JSON della decisione 5
    con `code` e SHA della riga `spec_audit` `row`. `kind` sostituisce il tipo dichiarato."""
    kind = kind or row["kind"]
    data = {"v": 1, "kind": kind, "number": row["number"],
            "viewpoint": row["viewpoint"] if kind == auditrules.LENS_KIND else None,
            "spec_sha": row["spec_sha"]}
    if kind == auditrules.PLAN_KIND:
        data["plan_sha"] = row["sha"]
    data.update(code=row["code"], counts={**ZERO_COUNTS, **(counts or {})})
    return "Riepilogo dei rilievi.\n" + json.dumps(data)


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
        gitw.add_excludes(self.main, flow_start.EXCLUDES)     # come `start` in produzione
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

    def _blob(self, path) -> str:
        blob = core_git.blob_at(self.wt, "HEAD", path)
        if blob is None:
            raise AssertionError(f"{path} non è in HEAD")
        return blob

    def write_spec(self, slices: int = 1, pitch: bool = True, note: str = "") -> str:
        """Scrive e committa la spec del banco (`SPEC`); restituisce il blob in HEAD."""
        self.commit(SPEC, spec_text(slices, pitch, note), "spec")
        return self._blob(SPEC)

    def write_l2_plan(self, tasks: int = 1) -> str:
        """Scrive il piano valido in `PLAN` come farebbe Write (l'hook `post_edit` registra il
        `plan_path`), lo committa e restituisce il blob in HEAD. Richiede la fase `plan`."""
        path = self.wt / PLAN
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan_text(tasks=tasks))
        r = self.lab.post_edit(path)
        if r.exit != 0:
            raise AssertionError(f"piano rifiutato dall'hook: {r.stderr}")
        if phases.get_work(self.conn, self.work)["plan_path"] != PLAN:
            raise AssertionError("l'hook non ha registrato il plan_path")
        self.commit(PLAN, plan_text(tasks=tasks), "piano")
        return self._blob(PLAN)

    def approve_spec_file(self, slices: int = 1) -> None:
        """La spec approvata come la lascerebbe `approve spec`: spec_path registrato e
        `spec-approval.md` committato (il blob è quello della spec in HEAD)."""
        work = phases.get_work(self.conn, self.work)
        phases.set_spec_path(self.conn, self.work, SPEC, now=self.lab.now)
        fields = {"kind": "spec-approval", "path": SPEC, "sha": self._blob(SPEC),
                  "slices": slices, "adversarial": "closed", "lens": None,
                  "act_id": "act-1", "approved_at": clock.fmt(self.lab.now)}
        self.commit(approvals.approval_paths(work["issue"])[0],
                    approvals.render_approval(fields), "approvazione della spec")

    def write_report(self, kind: str, number: int = 1, *, issue: int | None = None,
                     counts: dict | None = None) -> None:
        """Committa il report `<kind>-<number>.md` con intestazione valida in
        `reviews/<issue>/` (default: il lavoro); `issue` diverso riproduce i report della
        prima fetta, che stanno nella cartella di un'altra issue."""
        work = phases.get_work(self.conn, self.work)
        issue = issue or work["issue"]
        fields = {"kind": kind, "number": number,
                  "spec_sha": self._blob(work["spec_path"] or SPEC),
                  "counts": {**ZERO_COUNTS, **(counts or {})}, "outcome": "empty"}
        if kind == "plan-adversarial":
            fields["plan_sha"] = self._blob(PLAN)
        self.commit(f"{approvals.REVIEWS_DIR}/{issue}/{kind}-{number}.md",
                    approvals.render_report(fields, "Nessun rilievo.\n"), f"report {kind}")

    def approve_plan_file(self, adversarial: str = "closed") -> None:
        """Il piano approvato come lo lascerebbe `approve plan`: `plan-approval.md` committato
        con lo `sha` del piano e lo `spec_sha` della spec in HEAD. Non fa nulla se il file è già
        così."""
        work = phases.get_work(self.conn, self.work)
        rel = approvals.approval_paths(work["issue"])[1]
        fields = {"kind": "plan-approval", "path": PLAN, "sha": self._blob(PLAN),
                  "spec_sha": self._blob(work["spec_path"] or SPEC), "adversarial": adversarial,
                  "act_id": "act-2", "approved_at": clock.fmt(self.lab.now)}
        target = self.wt / rel
        current = approvals.parse_approval(target.read_text()) if target.exists() else None
        if current and (current["sha"], current["spec_sha"]) == (fields["sha"],
                                                                 fields["spec_sha"]):
            return
        text = approvals.render_approval(fields)
        self.commit(rel, text, "approvazione del piano")

    def closed_round(self, kind: str, counts: dict, *, viewpoint: str | None = None,
                     sha: str | None = None) -> int:
        """Un giro chiuso, aperto e chiuso dalla libreria sul blob attuale in HEAD della spec
        (o del piano, per `plan-adversarial`); con `sha` dato si usa quello. L'esito è quello di
        `auditrules.outcome`. Restituisce il numero del giro."""
        counts = {**ZERO_COUNTS, **counts}
        spec_path = phases.get_work(self.conn, self.work)["spec_path"] or SPEC
        spec_blob = self._blob(spec_path)
        doc = self._blob(PLAN) if kind == auditrules.PLAN_KIND else spec_blob
        self.lab.now += timedelta(seconds=1)
        number = audits.open_round(self.conn, self.work, kind=kind, sha=sha or doc,
                                   spec_sha=spec_blob, viewpoint=viewpoint, code="c0de0000",
                                   now=self.lab.now)
        self.lab.now += timedelta(seconds=1)
        audits.close_round(self.conn, self.work, kind=kind, number=number, counts=counts,
                           outcome=auditrules.outcome(counts),
                           report_path=f"docs/superpowers/reviews/7/{kind}-{number}.md",
                           now=self.lab.now)
        return number

    def report_round(self, kind: str | None = None, counts: dict | None = None, *,
                     bad_json: bool = False, cut: bool = False) -> subprocess.CompletedProcess:
        """L'agente del giro aperto riporta: `SubagentStart` (solo se non è già partito: una
        seconda chiamata è un altro `SubagentStop` della stessa riga, quindi un altro veto) e
        `SubagentStop` con la riga JSON giusta, attraverso `hookkit.Lab.hook`. `kind` cambia il
        tipo dell'agente e dichiarato (default: quello del giro), `counts` completa i conteggi a
        zero, `bad_json` manda solo prosa, `cut` tronca il messaggio a metà della riga JSON.
        **Orologio:** `audit prepare` dalla CLI usa l'ora reale, gli hook del banco quella di
        `hookkit`: alla partenza `self.lab.now` diventa `opened` del giro più un secondo (può
        tornare indietro rispetto a prima, se il banco era già avanti), così `started >= opened`.
        Restituisce l'esito dello `SubagentStop` come `CompletedProcess` (`returncode` = uscita
        dell'hook)."""
        row = audits.open_round_row(self.conn, self.work)
        if row is None:
            raise AssertionError("nessun giro aperto")
        kind = kind or row["kind"]
        agent_id, agent_type = f"a-{kind}-{row['number']}", audits.AGENTS[kind]
        sub = subagents.get(self.conn, agent_id)
        if sub is None or sub["started"] is None:
            self.lab.now = clock.parse(row["opened"]) + timedelta(seconds=1)
            self.lab.hook(sample("SubagentStart-none", session_id=SESSION, cwd=str(self.wt),
                                 agent_id=agent_id, agent_type=agent_type))
        msg = round_message(row, counts, kind=kind)
        if bad_json:
            msg = "Ho letto il documento: niente di grave, ecco la prosa senza la riga JSON."
        elif cut:
            msg = msg[:-25]
        payload = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.wt),
                         agent_id=agent_id, agent_type=agent_type, last_assistant_message=msg,
                         agent_transcript_path="/non/esiste.jsonl")
        r = self.lab.hook(payload)
        return subprocess.CompletedProcess(["SubagentStop"], r.exit, r.stdout, r.stderr)

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
