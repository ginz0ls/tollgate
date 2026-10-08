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
