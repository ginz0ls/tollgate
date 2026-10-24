#!/usr/bin/env python3
"""Registro dei costi degli eval (decisione 8) e tabella dei risultati (decisione 23).

Il tetto complessivo è di 80 USD di `costUsd` (prezzo di listino stimato da `claude plugin eval`),
sommato su tutte le invocazioni del piano nel registro `budget.tsv`. Una riga con `costUsd` illeggibile
(`?`) vale tetto esaurito: si corregge a mano.

Uso:
  cost.py add <result.json> [--label ETICHETTA]   aggiunge una riga a budget.tsv (esce 3 se il costo è ignoto)
  cost.py remaining                               stampa il residuo in USD, a centesimi per difetto
  cost.py table <result.json>...                  tabella Markdown per caso
  cost.py plugin-check <result.json>              (trace in runs/ accanto) il plugin tollgate è caricato nelle trace del braccio con plugin

`TOLLGATE_EVAL_BUDGET` sposta il registro (i test non toccano mai quello del repo). Solo libreria standard."""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

TOTAL_USD = 80.0
PLUGIN_NAME = "tollgate"
HEADER = ("ora", "invocazione", "costUsd", "durationSeconds", "casi")
DEFAULT_BUDGET = Path(__file__).resolve().parents[1] / "docs" / "verifiche" / "evidenze" / "eval-p5" / "budget.tsv"
EXIT_UNKNOWN_COST = 3


def budget_path() -> Path:
    return Path(os.environ.get("TOLLGATE_EVAL_BUDGET") or DEFAULT_BUDGET)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ensure_header(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\t".join(HEADER) + "\n", encoding="utf-8")
        return
    first = path.read_text(encoding="utf-8").split("\n", 1)[0]
    if tuple(first.split("\t")) != HEADER:
        raise ValueError(f"intestazione di {path} inattesa: controlla a mano")


def spent(path: Path | None = None) -> float | None:
    """Somma dei costUsd del registro; `None` se una riga non è leggibile (fail-closed)."""
    path = path or budget_path()
    if not path.is_file():
        return 0.0
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0.0
    if tuple(lines[0].split("\t")) != HEADER:
        return None
    total = 0.0
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        try:
            value = float(cols[2])
        except (IndexError, ValueError):
            return None
        if not math.isfinite(value) or value < 0:
            return None
        total += value
    return total


def remaining(path: Path | None = None) -> float:
    """80 meno la somma dei costi; 0 se una riga è illeggibile (tetto esaurito finché non la si corregge)."""
    total = spent(path)
    if total is None:
        return 0.0
    return max(0.0, TOTAL_USD - total)


def _load(path: Path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def case_names(data: dict) -> list[str]:
    return [c["name"] for c in data.get("cases", []) if isinstance(c, dict) and isinstance(c.get("name"), str)]


def add(result: Path, label: str | None = None, path: Path | None = None) -> bool:
    """Aggiunge la riga dell'invocazione. `False` se il JSON manca o non porta costUsd e durationSeconds:
    la riga entra comunque, con `?`, e il residuo diventa 0."""
    path = path or budget_path()
    _ensure_header(path)
    data = _load(result)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = label or Path(result).parent.name
    known = bool(data) and _is_number(data.get("costUsd")) and _is_number(data.get("durationSeconds"))
    if known:
        row = (now, name, repr(float(data["costUsd"])), str(data["durationSeconds"]), ",".join(case_names(data)))
    else:
        row = (now, name, "?", "?", ",".join(case_names(data)) if data else "")
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(row).replace("\n", " ") + "\n")
    return known


# ---------------------------------------------------------------- tabella

def _runs(case: dict, arm: str) -> list[dict]:
    runs = (case.get("arms") or {}).get(arm) or []
    return [r for r in runs if isinstance(r, dict)]


def _trace_for(run: dict, result: Path) -> Path | None:
    """La trace copiata in `<cartella del risultato>/runs/<claude-eval-…>/trace.jsonl`."""
    tp = run.get("tracePath")
    if not isinstance(tp, str) or not tp:
        return None
    parts = Path(tp).parts
    if len(parts) < 3:
        return None
    return Path(result).parent / "runs" / parts[-3] / "trace.jsonl"


def _read_trace(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    out = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if isinstance(msg, dict):
                out.append(msg)
    return out


def trace_tokens(path: Path | None) -> dict[str, int] | None:
    """Token dell'ultimo messaggio `result` di una trace (VE8: nel JSON non ci sono)."""
    results = [m for m in _read_trace(path) if m.get("type") == "result" and isinstance(m.get("usage"), dict)]
    if not results:
        return None
    usage = results[-1]["usage"]
    keys = (("input", "input_tokens"), ("output", "output_tokens"),
            ("cache_read", "cache_read_input_tokens"), ("cache_write", "cache_creation_input_tokens"))
    return {k: int(usage.get(src) or 0) for k, src in keys}


def _fmt_score(value) -> str:
    return f"{value:.2f}" if _is_number(value) else "—"


def _fmt_delta(value) -> str:
    return f"{value:+.2f}" if _is_number(value) else "—"


def _case_tokens(case: dict, result: Path) -> str:
    total = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    found = False
    for arm in ("with", "without"):
        for run in _runs(case, arm):
            tokens = run.get("tokens") if isinstance(run.get("tokens"), dict) else None
            tokens = tokens or trace_tokens(_trace_for(run, result))
            if tokens:
                found = True
                for k in total:
                    total[k] += int(tokens.get(k) or 0)
    if not found:
        return "—"
    return f"in {total['input']} / out {total['output']} / cache lett. {total['cache_read']} / cache scr. {total['cache_write']}"


def table(results: list[Path]) -> str:
    """Una riga per caso: punteggio con e senza plugin, Δ, corse riuscite, costo, durata, token."""
    lines = ["| Caso | Con plugin | Senza plugin | Δ | Corse | Costo USD | Durata s | Token |",
             "| :- | -: | -: | -: | -: | -: | -: | :- |"]
    for result in results:
        data = _load(result)
        if data is None:
            raise ValueError(f"{result}: JSON illeggibile")
        for case in data.get("cases", []):
            agg = case.get("aggregates") or {}
            with_runs, without_runs = _runs(case, "with"), _runs(case, "without")
            ok = sum(1 for r in with_runs if not r.get("error"))
            planned = case.get("runsPerCase", len(with_runs))
            cost = sum(float(r.get("costUsd") or 0) + float(r.get("judgeCostUsd") or 0)
                       for r in with_runs + without_runs)
            dur = sum(float(r.get("durationSeconds") or 0) for r in with_runs + without_runs)
            lines.append("| {} | {} | {} | {} | {}/{} | {:.4f} | {:.0f} | {} |".format(
                case.get("name", "?"), _fmt_score(agg.get("score")), _fmt_score(agg.get("scoreWithout")),
                _fmt_delta(agg.get("delta")), ok, planned, cost, dur, _case_tokens(case, result)))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- controllo del plugin caricato

def plugin_loaded(trace: list[dict]) -> bool | None:
    """`True` se il messaggio `init` elenca il plugin tollgate, `False` se non lo elenca, `None` senza `init`."""
    for msg in trace:
        if msg.get("type") == "system" and msg.get("subtype") == "init":
            plugins = msg.get("plugins")
            if not isinstance(plugins, list):
                return False
            return any(isinstance(p, dict) and p.get("name") == PLUGIN_NAME for p in plugins)
    return None


def plugin_check(result: Path) -> list[str]:
    """I problemi trovati: una corsa del braccio con plugin senza tollgate caricato (un caricamento mancato
    è silenzioso), o una del braccio senza plugin che lo ha. Una trace mancante conta come non verificata."""
    data = _load(result)
    if data is None:
        return [f"{result}: JSON illeggibile"]
    problems: list[str] = []
    for case in data.get("cases", []):
        for arm, want in (("with", True), ("without", False)):
            for run in _runs(case, arm):
                if not run.get("tracePath"):
                    continue
                trace = _trace_for(run, result)
                loaded = plugin_loaded(_read_trace(trace))
                where = f"{case.get('name', '?')} ({arm}) {Path(run['tracePath']).parts[-3]}"
                if loaded is None:
                    problems.append(f"{where}: trace assente o senza messaggio init")
                elif loaded != want:
                    problems.append(f"{where}: plugin {PLUGIN_NAME} " + ("non caricato" if want else "caricato nel braccio senza plugin"))
    return problems


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "add":
        label = None
        if "--label" in rest:
            i = rest.index("--label")
            if i + 1 >= len(rest):
                print("--label vuole un valore", file=sys.stderr)
                return 2
            label = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        if len(rest) != 1:
            print("uso: cost.py add <result.json> [--label ETICHETTA]", file=sys.stderr)
            return 2
        if add(Path(rest[0]), label):
            return 0
        print(f"costo ignoto: {rest[0]} non porta costUsd e durationSeconds; riga con «?» in budget.tsv "
              "(residuo 0 finché non la correggi a mano)", file=sys.stderr)
        return EXIT_UNKNOWN_COST
    if cmd == "remaining" and not rest:
        # a centesimi per difetto: è il valore di --max-cost-usd
        print(f"{math.floor(remaining() * 100 + 1e-9) / 100:.2f}")
        return 0
    if cmd == "table" and rest:
        try:
            sys.stdout.write(table([Path(p) for p in rest]))
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    if cmd == "plugin-check" and len(rest) == 1:
        problems = plugin_check(Path(rest[0]))
        for p in problems:
            print(p)
        return 1 if problems else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
