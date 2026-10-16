"""Verdetto del revisore del task (spec 18.5, 8.6, decisione 10).

Un verdetto che non rispetta il formato, o che non porta lo SHA e il codice del brief di
`review-prepare`, non è valido e non diventa mai `approved`."""
from __future__ import annotations

from dataclasses import dataclass, field

from .report import json_candidates

OUTCOMES = ("approved", "changes")
SEVERITIES = ("blocker", "major", "moderate", "minor")
BLOCKING = ("blocker", "major")
SPEC_FLAGS = ("missing", "extra")


@dataclass
class TaskVerdict:
    """`outcome` è l'esito effettivo (None se il verdetto non è valido); `declared` quello
    scritto dal revisore; `findings` sono i soli rilievi validi; `dropped` quelli scartati."""
    valid: bool
    problems: list[str] = field(default_factory=list)
    outcome: str | None = None
    declared: str | None = None
    findings: list[dict] = field(default_factory=list)
    dropped: int = 0


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _finding_ok(f) -> bool:
    """Prova obbligatoria: regola, file e riga (8.6); la gravità è una delle quattro."""
    return (isinstance(f, dict) and f.get("severity") in SEVERITIES
            and all(isinstance(f.get(k), str) and f[k].strip() for k in ("rule", "file"))
            and _is_int(f.get("line")))


def _may_block(f) -> bool:
    """Un rilievo scartato che poteva essere bloccante: gravità non dichiarata `moderate` o
    `minor` (anche illeggibile) conta come bloccante, in modo fail-closed."""
    return not (isinstance(f, dict) and f.get("severity") in ("moderate", "minor"))


def parse_task_verdict(text: str | None, *, task: int, sha: str, code: str,
                       standard: bool) -> TaskVerdict:
    cands = json_candidates(text or "", "outcome")
    if not cands:
        return TaskVerdict(False, ["manca il blocco JSON del verdetto (18.5), o è malformato"])
    data = cands[0]      # l'ultimo del testo: un esempio citato prima non conta
    declared = data.get("outcome") if isinstance(data.get("outcome"), str) else None
    problems = []
    if declared not in OUTCOMES:
        problems.append(f"outcome sconosciuto: usa «approved» o «changes» (trovato {declared!r})")
    if not _is_int(data.get("task")) or data["task"] != task:
        problems.append(f"task diverso da {task}")
    if data.get("sha") != sha:
        problems.append("sha diverso da quello del brief di revisione")
    if data.get("code") != code:
        problems.append("code diverso da quello del brief di revisione")
    spec = data.get("spec_compliance")
    if not isinstance(spec, list) or any(x not in SPEC_FLAGS for x in spec):
        problems.append("spec_compliance deve essere una lista di «missing» o «extra» "
                        "(vuota se il codice aderisce)")
        spec = []
    raw = data.get("findings", [])
    if not isinstance(raw, list):
        problems.append("findings deve essere una lista")
        raw = []
    if problems:
        return TaskVerdict(False, problems, None, declared)
    findings = [f for f in raw if _finding_ok(f)]
    outcome = declared
    if standard:
        blocking = bool(spec) or any(f["severity"] in BLOCKING for f in findings)
        lost = [f for f in raw if not _finding_ok(f) and _may_block(f)]
        if declared == "changes" and not blocking and lost:
            # Un `changes` il cui rilievo bloccante è senza prova non diventa `approved`.
            return TaskVerdict(False, ["rilievo bloccante senza file, riga o regola: "
                                       "riscrivilo"], None, declared)
        outcome = "changes" if blocking else "approved"
    return TaskVerdict(True, [], outcome, declared, findings, len(raw) - len(findings))
