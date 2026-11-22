"""Di chi è il turno in un lavoro (C1, decisione 8): funzione pura, senza stato né I/O."""
from __future__ import annotations

from dataclasses import dataclass

# Fasi in cui il passo dopo è dell'utente: il merge (`pr_open`) e `approve plan` (`approval`).
USER_PHASES = ("pr_open", "approval")


@dataclass(frozen=True)
class TurnFacts:
    phase: str
    waiting: list[dict]


def waiting_on(facts: TurnFacts) -> str:
    """`decision` se qualcosa aspetta una scelta dell'utente, `user` se il passo dopo è suo,
    `agent` negli altri casi."""
    if facts.waiting:
        return "decision"
    if facts.phase in USER_PHASES:
        return "user"
    return "agent"
