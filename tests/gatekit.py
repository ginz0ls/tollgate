"""Banco di prova del gate (P4): un repo git temporaneo con `origin` nudo locale, `tollgate.toml`
sul predefinito, il ramo `tg/7-x` con il piano registrato, e gli ingressi di `evaluate` già
composti. Nessuna rete, nessun DB, nessun `gh`: il gate si prova sui dati."""
import dataclasses
import shutil
import tempfile
from pathlib import Path

from tests.flowkit import PLAN, plan_text
from tests.helpers import git, make_origin_repo
from tests.hookkit import DEFAULT_FILES
from tollgate_analysis import prblock
from tollgate_analysis.junit import Junit
from tollgate_core import VERSION
from tollgate_core.config import load_config_text
from tollgate_gate.model import (BASE_FROM_CACHE, GITHUB, CommandResult, GateInputs, IssueFacts,
                                 PrFacts)

ISSUE = 7
BRANCH = "tg/7-x"
GATE_TOML = """schema_version = 1
[gate]
mode = "protected"
[commands]
verify = "true"
gate = ["verify"]
report = "junit:reports/junit.xml"
"""
# I test di `DEFAULT_FILES` e dei must-have di `plan_text`.
DEFAULT_IDS = ("tests.test_app::test_somma", "tests.test_app::test_zero")


class GateLab:
    """`GateLab(toml=GATE_TOML, files=None, plan=None)`: il predefinito ha `files` (di norma
    `DEFAULT_FILES`) e `toml`; il ramo `tg/7-x` registra `plan` (di norma `plan_text()`)."""

    def __init__(self, *, toml=GATE_TOML, files=None, plan=None):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate gate lab "))
        self.toml = toml
        self.main, self.origin, self.base = make_origin_repo(
            self.tmp, DEFAULT_FILES if files is None else files, toml)
        self.repo = self.main
        git(self.repo, "checkout", "-q", "-b", BRANCH)
        self.commit(PLAN, plan_text() if plan is None else plan, "piano")
        self.plan_sha = git(self.repo, "rev-parse", f"HEAD:{PLAN}")

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def head(self) -> str:
        return git(self.repo, "rev-parse", "HEAD")

    @property
    def cfg(self):
        return load_config_text(self.toml)

    def commit(self, rel: str, text: str, message: str = "cambio") -> str:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", message)
        return self.head

    def delete(self, rel: str, message: str = "cancella") -> str:
        git(self.repo, "rm", "-q", rel)
        git(self.repo, "commit", "-qm", message)
        return self.head

    def junit(self, ids_run, ids_skipped=(), ids_failed=()) -> Junit:
        """Un `Junit` come lo dà `parse_junit`: i falliti sono anche in `ids_run`, i saltati no."""
        run = list(dict.fromkeys([*ids_run, *ids_failed]))
        skipped = list(ids_skipped)
        return Junit(total=len(run) + len(skipped), skipped=len(skipped),
                     failed=len(list(ids_failed)), ids_run=run, ids_skipped=skipped,
                     ids_failed=list(ids_failed))

    def block(self, **override) -> dict:
        """Il blocco 18.1 di `prblock.build`, con valori validi per `tg/7-x`."""
        facts = {
            "schema_version": 1, "tollgate_version": VERSION, "issue": ISSUE, "level": "L1",
            "level_minimum": "L1", "level_cap": None, "level_cap_reason": None,
            "gate_mode": "protected", "plan": PLAN, "plan_sha": self.plan_sha, "spec": None,
            "spec_reviews_dir": None, "plan_reviews_dir": None,
            "spec_audit": {"adversarial": None, "lens": None}, "head_sha": self.head,
            "receipts": [{"command": "verify", "state": "green", "tests_run": 2}],
            "waivers_file": f".tollgate/waivers/{ISSUE}.toml", "blocks": [], "acts": [],
            "dod": {"L": "L1", "items": {"receipt": True}},
            "verdict": {"outcome": "ok", "cycles": 1, "findings_confirmed": 0,
                        "unverified": False},
            "findings": [], "fix_rounds": {}, "subagents": {"count": 0, "tokens": 0},
            "effects": [], "components_off": [], "off_periods": [], "tasks_over": [],
            "skills_absent": []}
        facts.update(override)
        return prblock.build(facts)

    def inputs(self, **override) -> GateInputs:
        """Gli ingressi di una PR valida su `tg/7-x`; `override` sostituisce i campi di
        `GateInputs` (`pr`, `block`, `commands`, …)."""
        block = override.pop("block", self.block())
        head = self.head
        body = f"Closes #{ISSUE}\n" + (prblock.render(block) if block else "")
        pr = PrFacts(1, head, BRANCH, "main", "main", body, False)
        values = dict(
            where=GITHUB, repo=self.repo, cfg=self.cfg, base_sha=self.base, head_sha=head,
            pr=pr, block=block, issue=IssueFacts(ISSUE, "open", ()),
            commands=[CommandResult("verify", "green", 0, len(DEFAULT_IDS),
                                    self.junit(DEFAULT_IDS))],
            base_ids={"verify": set(DEFAULT_IDS)}, base_ids_source=BASE_FROM_CACHE,
            waiver_text=None, sentinel_open=[])
        values.update(override)
        return GateInputs(**values)

    def with_pr(self, **changes) -> PrFacts:
        """La `PrFacts` di `inputs()` con alcuni campi cambiati."""
        return dataclasses.replace(self.inputs().pr, **changes)

