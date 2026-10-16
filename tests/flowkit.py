"""Banco di prova del flusso (P3a): repo con gate, stato e HOME temporanei, finto gh.

Compone `hookkit.Lab` (stessi `ts`, `tmp`, `main`, `origin`, `conn`, sessione `sess-flow`) e vi
aggiunge ciò che serve alla CLI: HOME temporanea con Superpowers, `gh` finto, segnale della
sessione prima di ogni chiamata a `bin/tollgate`."""
import json
import subprocess
import sys
from pathlib import Path

from tests.helpers import BIN, ROOT, git
from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML, Lab
from tollgate_core import VERSION, clock, sessions

SESSION = "sess-flow"
ORIGIN_URL = "https://github.com/prova/flow.git"
FAKEGH = ROOT / "tests" / "fakegh.py"
GATE_FILES = {f".github/workflows/tollgate-{n}.yml": f"name: tollgate-{n}\n"
              for n in ("guard", "run", "verdict", "base", "sentinel")}


class FlowLab:
    def __init__(self, *, toml=DEFAULT_TOML, files=None, gate=True, issue=None):
        tree = dict(DEFAULT_FILES, **(files or {}))
        if gate:
            tree.update(GATE_FILES)
            tree[".github/tollgate/VERSION"] = VERSION + "\n"
        self.lab = Lab(toml=toml, files=tree, work=issue is not None, session=SESSION,
                       issue=issue or 7, origin_url=ORIGIN_URL)
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

    def close(self) -> None:
        self.lab.close()
