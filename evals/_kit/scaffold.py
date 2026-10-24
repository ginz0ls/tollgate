#!/usr/bin/env python3
"""Scaffold degli eval (decisione 3): costruisce nel workspace lo stato di tollgate voluto da una ricetta.

Gira prima dell'agente, con la HOME della corsa, fuori dalla sandbox. Usa solo il programma come
processo (`bin/tollgate`, `hooks/run`) e il gh finto (`tests/fakegh.py`): mai il DB, mai l'interno dei
pacchetti di `bin/`. Il segnale della sessione `scaffold` e gli eventi `commit` li scrive `hooks/run`
dagli eventi `PreToolUse` e `PostToolUse` che lo scaffold gli manda, nella forma di `tests/hookkit.py`.

Uso: `python3 scaffold.py <ricetta>` nel workspace vuoto; `HOME` è quella della corsa. Le variabili
`TOLLGATE_*` esistono solo negli ambienti dei sottoprocessi dello scaffold: nel processo padre e nei
file scritti non entrano mai (Review Focus 1)."""
from __future__ import annotations

import json
import os
import pwd
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True      # lanciato come script dallo scaffold.sh: nessun __pycache__ nella radice valutata
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from evals._kit import recipes  # noqa: E402

BIN = ROOT / "bin" / "tollgate"
HOOK = ROOT / "hooks" / "run"
FAKEGH = ROOT / "tests" / "fakegh.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

SESSION = "scaffold"
ORIGIN_URL = "https://github.com/prova/eval.git"
ORIGIN_DIR = ".origin.git"
SENTINEL = ".tollgate-test"
STEP_TIMEOUT_S = 120
# `.origin.git/` è il nudo locale; il resto sono i segnaposto che la sandbox crea nella cartella di
# partenza (rapporto delle verifiche, I1). `/.claude/*` e non `/.claude/`: i worktree di tollgate
# stanno in `.claude/worktrees/` (già escluso da `start`) e il progetto di prova non versiona nulla
# sotto `.claude/`, quindi escludere il contenuto non nasconde niente.
PLACEHOLDERS = frozenset({".bash_profile", ".bashrc", ".claude", ".eval-artifacts", ".gitconfig",
                          ".gitmodules", ".idea", ".mcp.json", ".profile", ".ripgreprc", ".vscode",
                          ".zprofile", ".zshrc"})
EXCLUDES = ("/.origin.git/", "/.claude", "/.bash_profile", "/.bashrc", "/.claude/*", "/.eval-artifacts",
            "/.gitconfig", "/.gitmodules", "/.idea", "/.mcp.json", "/.profile", "/.ripgreprc",
            "/.vscode", "/.zprofile", "/.zshrc")
# Cartella Superpowers per `installed_plugins.json`: solo SKILL.md vuoti (la sandbox non lo carica).
SUPERPOWERS_SKILLS = ("brainstorming", "writing-plans", "executing-plans", "test-driven-development",
                      "subagent-driven-development", "systematic-debugging",
                      "verification-before-completion", "requesting-code-review")
GATE_WORKFLOWS = ("guard", "run", "verdict", "base", "sentinel")
CLEAN_REPORT = {"blocker": 0, "major": 0, "moderate": 0, "minor": 0}


class ScaffoldError(Exception):
    pass


@dataclass(frozen=True)
class Built:
    worktree: Path
    work_branch: str
    state_root: Path


class _Builder:
    def __init__(self, recipe: recipes.Recipe, workspace: Path, home: Path, state: Path | None):
        self.r = recipe
        self.ws = Path(workspace).resolve()
        self.home = Path(home).resolve()
        self.state_root = Path(state).resolve() if state else \
            self.home / ".local" / "state" / "tollgate"
        self.eval_dir = self.home / ".tollgate-eval"
        self.gh_data = self.eval_dir / "fakegh-data.json"
        self.gh_log = self.eval_dir / "fakegh.log"
        self.wt: Path | None = None
        self.branch: str | None = None
        self._env = self._make_env()

    # ----- ambiente e processi -------------------------------------------------------------

    def _make_env(self) -> dict:
        """L'ambiente dei sottoprocessi: niente variabili ereditate di tollgate, git o Claude Code."""
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("TOLLGATE_", "GIT_", "CLAUDE"))}
        env.update(HOME=str(self.home), TOLLGATE_STATE=str(self.state_root),
                   TOLLGATE_GH=str(FAKEGH), TOLLGATE_FAKEGH_DATA=str(self.gh_data),
                   TOLLGATE_FAKEGH_LOG=str(self.gh_log), TOLLGATE_GH_RETRY_DELAYS="0,0",
                   PYTHONDONTWRITEBYTECODE="1")
        return env

    def _run(self, argv, cwd, *, what, ok=(0,), stdin=None) -> subprocess.CompletedProcess:
        try:
            r = subprocess.run([str(a) for a in argv], cwd=str(cwd), env=self._env, input=stdin,
                               capture_output=True, text=True, timeout=STEP_TIMEOUT_S)
        except subprocess.TimeoutExpired as e:
            raise ScaffoldError(f"{what}: nessuna risposta in {STEP_TIMEOUT_S} s") from e
        if r.returncode not in ok:
            raise ScaffoldError(f"{what}: uscita {r.returncode}\n{r.stdout}{r.stderr}".rstrip())
        return r

    def _git(self, cwd, *args, ok=(0,)) -> str:
        return self._run(["git", "-C", cwd, "-c", "user.name=eval", "-c",
                          "user.email=eval@example.invalid", "-c", "commit.gpgsign=false", *args],
                         cwd, what=f"git {args[0]}", ok=ok).stdout.strip()

    def _hook(self, event: str, payload: dict, *, what: str) -> subprocess.CompletedProcess:
        r = self._run([HOOK, event], self.ws, what=f"hook {event} ({what})",
                      stdin=json.dumps(payload))
        if self._denied(r.stdout):
            raise ScaffoldError(f"hook {event} ({what}) ha negato: {r.stdout.strip()[:300]}")
        return r

    @staticmethod
    def _denied(stdout: str) -> bool:
        """Un `deny` scritto in JSON su stdout con uscita 0 vale come un'uscita 2."""
        try:
            data = json.loads(stdout) if stdout.strip().startswith("{") else {}
        except ValueError:
            return False
        out = data.get("hookSpecificOutput")
        return isinstance(data, dict) and (
            data.get("decision") in ("block", "deny")
            or (isinstance(out, dict) and out.get("permissionDecision") in ("deny", "block")))

    def _cli(self, argv, cwd, *, ok=(0,)) -> subprocess.CompletedProcess:
        return self._run([sys.executable, "-B", BIN, *argv], cwd,
                         what=f"tollgate {' '.join(argv)}", ok=ok)

    def _bash_event(self, command: str, cwd, *, post: bool, agent: tuple[str, str] | None = None):
        """PreToolUse o PostToolUse di Bash: i campi di primo livello prima di `tool_input`."""
        payload = {"session_id": SESSION, "cwd": str(cwd),
                   "hook_event_name": "PostToolUse" if post else "PreToolUse", "tool_name": "Bash"}
        if agent:
            payload.update(agent_id=agent[0], agent_type=agent[1])
        payload["tool_input"] = {"command": command, "description": "scaffold"}
        if post:
            payload["tool_response"] = {"stdout": "", "stderr": "", "interrupted": False}
        self._hook(payload["hook_event_name"], payload, what=command[:60])

    def _subagent_event(self, event: str, cwd, agent_id: str, agent_type: str, message=None):
        payload = {"session_id": SESSION, "cwd": str(cwd), "hook_event_name": event,
                   "agent_id": agent_id, "agent_type": agent_type}
        if message is not None:
            payload.update(stop_hook_active=False, last_assistant_message=message,
                           agent_transcript_path="/non/esiste.jsonl")
        self._hook(event, payload, what=agent_id)

    @staticmethod
    def _command(*argv: str) -> str:
        return f"python3 {shlex.quote(str(BIN))} " + " ".join(shlex.quote(a) for a in argv)

    def _tollgate(self, argv, cwd, *, signal=False) -> subprocess.CompletedProcess:
        """Un comando del programma. Con `signal` lo scaffold manda prima l'evento di PreToolUse
        di Bash: è `cli_calls` a scrivere il segnale della sessione `scaffold` (decisione 3)."""
        if signal:
            self._bash_event(self._command(*argv), cwd, post=False)
        return self._cli(argv, cwd)

    # ----- cartelle, HOME e stato ----------------------------------------------------------

    @staticmethod
    def _only_placeholders(ws: Path) -> bool:
        """Il workspace contiene solo i segnaposto noti della sandbox: file vuoti o cartelle vuote."""
        for entry in ws.iterdir():
            if entry.name not in PLACEHOLDERS:
                return False
            if entry.is_symlink():
                return False
            if entry.is_dir():
                for sub in entry.rglob("*"):
                    if sub.is_symlink() or (sub.is_file() and sub.stat().st_size):
                        return False
            elif entry.stat().st_size:
                return False
        return True

    def _check_places(self) -> None:
        real = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        if self.home == real:
            raise ScaffoldError(f"{self.home} è la HOME vera dell'utente: lo scaffold scrive solo "
                                "in una HOME della corsa")
        if (self.home / ".claude" / "settings.json").exists():
            raise ScaffoldError(f"{self.home} sembra una HOME vera (c'è .claude/settings.json): "
                                "lo scaffold scrive solo in una HOME della corsa")
        if (self.home / ".claude" / "plugins" / "installed_plugins.json").exists():
            raise ScaffoldError(f"{self.home} ha già un registro dei plugin: lo scaffold "
                                "costruisce da zero (HOME vera?)")
        if self.state_root.exists() and any(p.name != SENTINEL for p in self.state_root.iterdir()):
            raise ScaffoldError(f"{self.state_root} non è vuota: lo scaffold costruisce da zero")
        if self.ws.exists() and not self._only_placeholders(self.ws):
            raise ScaffoldError(f"il workspace {self.ws} non è vuoto (a parte i segnaposto "
                                "della sandbox)")

    def _write_home(self) -> None:
        self.state_root.mkdir(parents=True, exist_ok=True)
        (self.state_root / SENTINEL).write_text("")
        sp = self.eval_dir / "superpowers"
        for name in SUPERPOWERS_SKILLS:
            (sp / "skills" / name).mkdir(parents=True, exist_ok=True)
            (sp / "skills" / name / "SKILL.md").write_text("")
        plugins = self.home / ".claude" / "plugins"
        plugins.mkdir(parents=True, exist_ok=True)
        (plugins / "installed_plugins.json").write_text(json.dumps({
            "version": 2, "plugins": {"superpowers@claude-plugins-official": [{
                "scope": "user", "version": "7.0.0", "installPath": str(sp)}]}}))
        data = {"auth": True, "prs": [], "issues": {str(self.r.issue): {
            "number": self.r.issue, "title": self.r.issue_title,
            "body": self.r.issue_body, "state": "OPEN",
            "labels": [], "author_association": "OWNER"}}}
        data.update(self.r.gh_data)
        self.gh_data.write_text(json.dumps(data))

    def _version(self) -> str:
        out = self._cli(["--version"], self.ws).stdout.split()
        if len(out) != 2:
            raise ScaffoldError("`tollgate --version` ha un'uscita inattesa")
        return out[1]

    # ----- il checkout principale ----------------------------------------------------------

    def _make_checkout(self) -> None:
        ws = self.ws
        shutil.copytree(FIXTURES / "project", ws, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
        for name in GATE_WORKFLOWS:
            self._write(ws, f".github/workflows/tollgate-{name}.yml", f"name: tollgate-{name}\n")
        self._write(ws, ".github/tollgate/VERSION", self._version() + "\n")
        for rel, text in self.r.extra_files.items():
            self._write(ws, rel, text)
        subprocess.run(["git", "init", "-q", "-b", "main", str(ws)], check=True,
                       env=self._env, capture_output=True)
        bare = ws / ORIGIN_DIR
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True,
                       env=self._env, capture_output=True)
        exclude = ws / ".git" / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as f:
            f.write("\n".join(EXCLUDES) + "\n")
        # nome e posta nella configurazione locale: l'agente deve poter committare con la HOME della corsa
        self._git(ws, "config", "user.name", "eval")
        self._git(ws, "config", "user.email", "eval@example.invalid")
        self._git(ws, "config", "commit.gpgsign", "false")
        self._git(ws, "add", "-A")
        self._git(ws, "commit", "-qm", "base")
        self._git(ws, "remote", "add", "origin", ORIGIN_URL)
        self._git(ws, "config", f"url.{bare}.insteadOf", ORIGIN_URL)
        self._git(ws, "push", "-q", "-u", "origin", "main")
        self._git(ws, "remote", "set-head", "origin", "main")
        self._git(ws, "config", "tollgate.defaultBranch", "main")

    @staticmethod
    def _write(root: Path, rel: str, text: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    # ----- primitive -----------------------------------------------------------------------

    def start(self) -> None:
        argv = ["start", str(self.r.issue)] + ([] if self.r.level == "L0" else ["--level", self.r.level])
        self._tollgate(argv, self.ws, signal=True)
        prefix = f"refs/heads/tg/{self.r.issue}-"
        path = branch = None
        for block in self._git(self.ws, "worktree", "list", "--porcelain").split("\n\n"):
            fields = dict(line.partition(" ")[::2] for line in block.splitlines())
            if fields.get("branch", "").startswith(prefix):
                path, branch = fields["worktree"], fields["branch"].removeprefix("refs/heads/")
        if path is None:
            raise ScaffoldError(f"dopo `start` nessun worktree per il ramo tg/{self.r.issue}-*")
        self.wt, self.branch = Path(path), branch

    def commit(self, paths: list[str], message: str, *, agent: tuple[str, str] | None = None) -> str:
        """Il commit della sessione (o dell'agente) e l'evento di PostToolUse che lo fa registrare."""
        self._git(self.wt, "add", "--", *paths)
        self._git(self.wt, "commit", "-qm", message)
        self._bash_event(f"git commit -qm {shlex.quote(message)}", self.wt, post=True, agent=agent)
        return self._git(self.wt, "rev-parse", "HEAD")

    def overlay(self, name: str) -> list[str]:
        """Copia nel worktree i file di `fixtures/changes/<name>/`; i percorsi relativi copiati."""
        src = FIXTURES / "changes" / name
        if not src.is_dir():
            raise ScaffoldError(f"cambio {name} assente in fixtures/changes/")
        copied = []
        for f in sorted(p for p in src.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            rel = f.relative_to(src).as_posix()
            self._write(self.wt, rel, f.read_text(encoding="utf-8"))
            copied.append(rel)
        return copied

    def register_plan(self) -> None:
        """Il piano scritto con Write e committato: PostToolUse della Write lo registra e porta la
        fase a `execution` (livello L1)."""
        rel = f"docs/superpowers/plans/{self.r.plan}.md"
        text = (FIXTURES / "plans" / f"{self.r.plan}.md").read_text(encoding="utf-8")
        self._write(self.wt, rel, text)
        path = str(self.wt / rel)
        payload = {"session_id": SESSION, "cwd": str(self.wt), "hook_event_name": "PostToolUse",
                   "tool_name": "Write", "tool_input": {"file_path": path, "content": text},
                   "tool_response": {"type": "create", "filePath": path}}
        self._hook("PostToolUse", payload, what="Write del piano")
        self.commit([rel], "piano")

    def write_plan(self) -> None:
        """Il piano di L2, scritto e committato dal coordinatore: lo registra `audit prepare`."""
        rel = f"docs/superpowers/plans/{self.r.plan}.md"
        self._write(self.wt, rel, (FIXTURES / "plans" / f"{self.r.plan}.md").read_text(encoding="utf-8"))
        self.commit([rel], "piano")

    def task_start(self, number: int) -> tuple[str, str, str]:
        """`task start`: ritorna (nome dell'implementatore, tipo dell'implementatore, tipo del revisore)."""
        out = self._tollgate(["task", "start", str(number)], self.wt).stdout.strip().splitlines()[-1]
        m = re.search(r"task \d+: (\S+) name=(\S+)", out)
        rev = re.search(r"revisore: (\S+)", out)
        if not m or not rev:
            raise ScaffoldError(f"`task start` ha un'uscita inattesa: {out}")
        return m.group(2), m.group(1), rev.group(1)

    def task_done(self, number: int) -> None:
        """Il ciclo del task come lo vedono gli hook: implementatore (lancio, commit, ricevuta `verify`,
        report 18.5), `task review-prepare`, revisore con il verdetto, `task done`."""
        name, impl_type, rev_type = self.task_start(number)
        launch = {"session_id": SESSION, "cwd": str(self.wt), "hook_event_name": "PreToolUse",
                  "tool_name": "Agent",
                  "tool_input": {"description": f"Task {number}", "prompt": "Esegui il brief.",
                                 "subagent_type": impl_type, "name": name,
                                 "run_in_background": False}}
        self._hook("PreToolUse", launch, what="lancio dell'implementatore")
        impl = (f"ag-impl-{number}", impl_type)
        self._subagent_event("SubagentStart", self.wt, *impl)
        files = self.overlay(f"{recipes.PLAN_CHANGES.get(self.r.plan, self.r.plan)}/{number}")
        self.commit(files, f"task {number}", agent=impl)
        self._tollgate(["verify"], self.wt)
        report = {"v": 1, "task": number, "status": "DONE", "done": "fatto", "tests": "verify green",
                  "files": files, "must_have": [], "concerns": "", "left": "", "size_reason": None}
        self._subagent_event("SubagentStop", self.wt, *impl,
                             message="Fine.\n```json\n" + json.dumps(report) + "\n```")
        prep = self._tollgate(["task", "review-prepare", str(number)], self.wt).stdout.splitlines()
        brief = Path(prep[0]).read_text(encoding="utf-8")
        ids = re.search(r'"sha": "([0-9a-f]+)", "code": "([0-9a-f]+)"', brief)
        if not ids:
            raise ScaffoldError("il brief di revisione non riporta sha e code")
        verdict = {"v": 1, "task": number, "sha": ids.group(1), "code": ids.group(2),
                   "outcome": "approved", "spec_compliance": [], "findings": []}
        rev = (f"ag-rev-{number}", rev_type)
        self._subagent_event("SubagentStart", self.wt, *rev)
        self._subagent_event("SubagentStop", self.wt, *rev,
                             message="Verdetto.\n```json\n" + json.dumps(verdict) + "\n```")
        self._tollgate(["task", "done", str(number)], self.wt)

    def audit_round(self) -> None:
        """Un giro di audit chiuso pulito: `audit prepare` apre il giro e stampa il brief; l'agente del
        giro riporta la riga JSON del brief con i conteggi a zero; il report che l'hook scrive si committa."""
        out = self._tollgate(["audit", "prepare"], self.wt).stdout
        m = re.search(r'agente: (\S+) brief: "([^"]+)"', out)
        if not m:
            raise ScaffoldError(f"`audit prepare` non ha aperto un giro:\n{out}")
        agent_type, brief = m.group(1), Path(m.group(2))
        example = next((ln for ln in reversed(brief.read_text(encoding="utf-8").splitlines())
                        if ln.startswith("{") and '"counts"' in ln), None)
        if example is None:
            raise ScaffoldError("il brief del giro non riporta la riga JSON")
        data = json.loads(example)
        data["counts"] = dict(CLEAN_REPORT)
        agent_id = f"ag-{data['kind']}-{data['number']}"
        self._subagent_event("SubagentStart", self.wt, agent_id, agent_type)
        self._subagent_event("SubagentStop", self.wt, agent_id, agent_type,
                             message="Nessun rilievo.\n" + json.dumps(data))
        self.commit_reviews(f"report {data['kind']} {data['number']}")

    def commit_reviews(self, message: str) -> None:
        """Committa i file nuovi o cambiati di `reviews/<N>/` (report dei giri, approvazioni): i file non
        committati non contano per `audit prepare` (decisione 3 di P3c)."""
        folder = f"docs/superpowers/reviews/{self.r.issue}"
        if self._git(self.wt, "status", "--porcelain", "--", folder):
            self.commit([folder], message)

    def user_act(self, act: tuple[str, ...]) -> None:
        """L'atto dell'utente: UserPromptExpansion con la sessione `scaffold` (legata al lavoro da
        `start`), poi `act apply` dalla cartella del lavoro."""
        type_, args = act[0], list(act[1:])
        raw = " ".join(shlex.quote(a) for a in args)
        payload = {"session_id": SESSION, "cwd": str(self.wt), "hook_event_name": "UserPromptExpansion",
                   "expansion_type": "slash_command", "command_name": f"tollgate:{type_}",
                   "command_args": raw, "command_source": "plugin",
                   "prompt": f"/tollgate:{type_} {raw}".strip()}
        self._hook("UserPromptExpansion", payload, what=f"atto {type_}")
        self._tollgate(["act", "apply"], self.wt, signal=True)
        self.commit_reviews(f"atto {type_}")

    def finish(self) -> None:
        self._tollgate(["finish", "check"], self.wt, signal=True)
        if self.r.finish != "open-pr":
            return
        self.user_prompt_finish()
        if self.r.level != "L0":
            self.final_review()
        self._tollgate(["finish", "open-pr"], self.wt, signal=True)
        if self.r.gate_comment:
            self.gate_comment()
        if self.r.reopen_execution:
            self._tollgate(["start", str(self.r.issue), "--reopen-execution", "--confirm"], self.ws,
                           signal=True)

    def user_prompt_finish(self) -> None:
        payload = {"session_id": SESSION, "cwd": str(self.wt), "hook_event_name": "UserPromptExpansion",
                   "expansion_type": "slash_command", "command_name": "tollgate:finish",
                   "command_args": "", "command_source": "plugin", "prompt": "/tollgate:finish"}
        self._hook("UserPromptExpansion", payload, what="atto finish")

    def final_review(self) -> None:
        """Il ciclo di revisione finale `ok` (L1 e L2): `review prepare` lancia il revisore, che riporta
        il verdetto senza rilievi (sha e codice letti dal brief), e si ripete finché non resta un agente."""
        for _ in range(4):
            out = self._tollgate(["review", "prepare"], self.wt).stdout
            launches = re.findall(r'agente: (\S+) brief: "([^"]+)"', out)
            if not launches:
                return
            for agent_type, brief in launches:
                text = Path(brief).read_text(encoding="utf-8")
                ids = re.search(r'"sha": "([0-9a-f]+)", "code": "([0-9a-f]+)"', text)
                if not ids:
                    raise ScaffoldError(f"il brief {brief} non riporta sha e codice")
                if agent_type.endswith("finding-verifier"):
                    raise ScaffoldError("senza rilievi non serve il verificatore: ciclo inatteso")
                verdict = {"v": 1, "sha": ids.group(1), "code": ids.group(2), "outcome": "ok", "findings": []}
                agent_id = f"ag-{agent_type.rpartition(':')[2]}"
                self._subagent_event("SubagentStart", self.wt, agent_id, agent_type)
                self._subagent_event("SubagentStop", self.wt, agent_id, agent_type,
                                     message="Verdetto.\n```json\n" + json.dumps(verdict) + "\n```")
        raise ScaffoldError("la revisione finale non si chiude in quattro passi")

    def gate_comment(self) -> None:
        """Il commento del bot sulla PR, nei dati del gh finto: lo SHA è la testa del lavoro."""
        data = json.loads(self.gh_data.read_text(encoding="utf-8"))
        sha = self._git(self.wt, "rev-parse", "HEAD")
        if not data["prs"]:
            raise ScaffoldError("nessuna PR nei dati del gh finto")
        data["prs"][-1].setdefault("comments", []).append({
            "id": 1, "author": {"login": "github-actions"},
            "body": self.r.gate_comment.replace("{sha}", sha)})
        self.gh_data.write_text(json.dumps(data))

    def merge_default(self) -> None:
        """La prima fetta è unita sul predefinito: spec e approvazioni (già committate sul ramo del lavoro)
        entrano su main e main è spinto sull'`origin` nudo."""
        self._git(self.ws, "merge", "-q", "--ff-only", self.branch)
        self._git(self.ws, "push", "-q", "origin", "main")

    # ----- composizione --------------------------------------------------------------------

    def build(self) -> Built:
        r = self.r
        self._check_places()
        self._write_home()
        self._make_checkout()
        self.start()
        if r.level == "L0" and r.change:
            self.commit(self.overlay(r.change), "lavoro")
        if r.level == "L2" and r.spec:
            rel = f"docs/superpowers/specs/{r.spec}.md"
            self._write(self.wt, rel, (FIXTURES / "specs" / f"{r.spec}.md").read_text(encoding="utf-8"))
            self.commit([rel], "spec")
        for _ in range(r.audit_rounds):
            self.audit_round()
        rest = [a for a in r.acts if a[:2] not in (("approve", "spec"), ("approve", "plan"))]
        for act in [a for a in r.acts if a[:2] == ("approve", "spec")]:
            self.user_act(act)                      # prima del piano
        if r.level == "L2" and r.plan:
            self.write_plan()
        for _ in range(r.plan_audit_rounds):
            self.audit_round()
        if r.plan_audit_rounds:
            self._tollgate(["audit", "prepare"], self.wt)       # il giro è pulito: il piano passa ad `approval`
        for act in [a for a in r.acts if a[:2] == ("approve", "plan")]:
            self.user_act(act)
        if r.level == "L1" and r.plan:
            self.register_plan()
        for number in r.tasks_done:
            self.task_done(number)
        if r.task_started is not None:
            self.task_start(r.task_started)
        for act in rest:
            self.user_act(act)
        if r.merge_default:
            self.merge_default()
        if r.finish:
            self.finish()
        self._check_phase()
        return Built(self.wt, self.branch, self.state_root)

    def _check_phase(self) -> None:
        if self.r.phase is None:
            return
        items = json.loads(self._cli(["status", "--json"], self.ws).stdout)
        mine = [i for i in items if i["issue"] == self.r.issue]
        if not mine or mine[0]["phase"] != self.r.phase:
            got = mine[0]["phase"] if mine else "nessun lavoro"
            raise ScaffoldError(f"la ricetta {self.r.name} doveva finire in fase {self.r.phase}: {got}")


def build(recipe: recipes.Recipe, *, workspace: Path, home: Path, state: Path | None = None) -> Built:
    """Costruisce lo stato della ricetta. `state=None`: la cartella predefinita di `home`."""
    return _Builder(recipe, workspace, home, state).build()


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in recipes.RECIPES:
        print("uso: scaffold.py <ricetta>   (ricette: " + ", ".join(sorted(recipes.RECIPES)) + ")",
              file=sys.stderr)
        return 2
    home = os.environ.get("HOME")
    if not home:
        print("scaffold: HOME non impostata", file=sys.stderr)
        return 2
    try:
        build(recipes.RECIPES[argv[0]], workspace=Path.cwd(), home=Path(home))
    except (ScaffoldError, OSError, subprocess.SubprocessError) as e:
        print(f"scaffold: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
