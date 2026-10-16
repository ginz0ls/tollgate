"""Sottocomandi di bin/tollgate (spec 3.1): radice di composizione, importa anche il flusso."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import VERSION, clock, db, events, phases, stats, verify
from .paths import repo_key, resolve_state


class UsageError(Exception):
    pass


def current_repo_key(cwd: Path) -> str | None:
    r = subprocess.run(["git", "-C", str(cwd), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    url = r.stdout.strip()
    return repo_key(url) if r.returncode == 0 and url else None


def _date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise argparse.ArgumentTypeError("data attesa nella forma AAAA-MM-GG") from e


def _issue_number(value: str) -> int:
    try:
        n = int(value.lstrip("#"))
    except ValueError as e:
        raise argparse.ArgumentTypeError("numero di issue atteso (7 oppure #7)") from e
    if n < 1:
        raise argparse.ArgumentTypeError("numero di issue atteso (7 oppure #7)")
    return n


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tollgate", description="CLI di tollgate")
    p.add_argument("--version", action="version", version=f"tollgate {VERSION}")
    sub = p.add_subparsers(dest="cmd")
    st = sub.add_parser("status", help="stato dei lavori attivi (sola lettura)")
    st.add_argument("--json", action="store_true", help="uscita in JSON")
    st.add_argument("--checkpoint", action="store_true",
                    help="scrive il checkpoint nel worktree del lavoro (6.3)")
    st.add_argument("--note", metavar="TESTO", help="nota da aggiungere al checkpoint")
    sp = sub.add_parser("stats", help="statistiche dagli eventi, in JSON")
    sp.add_argument("--since", type=_date, metavar="AAAA-MM-GG")
    sp.add_argument("--work", type=int, metavar="N", help="numero dell'issue nel repo corrente")
    ep = sub.add_parser("events", help="eventi in JSONL dopo un seq")
    ep.add_argument("--after-seq", type=int, default=0, metavar="N")
    dp = sub.add_parser("db", help="manutenzione del DB")
    dsub = dp.add_subparsers(dest="db_cmd", required=True)
    dsub.add_parser("restore", help="ripristina l'ultima copia integra (solo da terminale)")
    sa = sub.add_parser("start", help="avvia o riprende il lavoro su un'issue (6.1)")
    sa.add_argument("issue", type=_issue_number, metavar="N")
    sa.add_argument("--level", choices=("L1", "L2"), help="livello scelto dall'utente")
    sa.add_argument("--confirm", action="store_true",
                    help="conferma gli avvisi che la prima chiamata ha elencato (codice 3)")
    sa.add_argument("--reopen-execution", action="store_true",
                    help="in review o pr_open riporta la fase a execution")
    tp = sub.add_parser("task", help="task del piano (6.3)")
    tsub = tp.add_subparsers(dest="task_cmd", required=True)
    ts = tsub.add_parser("start", help="assegna il task a un implementatore e scrive il brief")
    ts.add_argument("number", type=int, metavar="K")
    ts.add_argument("--fix", action="store_true", help="giro di correzione dopo un verdetto")
    tr = tsub.add_parser("review-prepare", help="prepara diff e brief del revisore del task")
    tr.add_argument("number", type=int, metavar="K")
    td = tsub.add_parser("done", help="chiude il task approvato dal revisore")
    td.add_argument("number", type=int, metavar="K")
    ap = sub.add_parser("act", help="atti dell'utente (8.4)")
    asub = ap.add_subparsers(dest="act_cmd", required=True)
    aa = asub.add_parser("apply", help="applica un atto registrato (resolve, approve level)")
    aa.add_argument("act_id", nargs="?", metavar="ID", help="senza id: l'ultimo atto pending")
    hp = sub.add_parser("hook", help="solo per hooks/run: adattatore per Claude Code")
    hp.add_argument("event", metavar="evento")
    vp = sub.add_parser("verify", help="esegue i comandi del gate e registra le ricevute (8.1)")
    vp.add_argument("--related", action="store_true",
                    help="solo i test correlati ai file cambiati")
    wp = sub.add_parser("waiver", help="deroghe (8.3)")
    wsub = wp.add_subparsers(dest="waiver_cmd", required=True)
    wa = wsub.add_parser("add", help="dichiara una deroga in .tollgate/waivers/<N>.toml")
    wa.add_argument("type", metavar="tipo")
    wa.add_argument("file", nargs="?", metavar="file")
    wa.add_argument("--pattern", metavar="GLOB")
    wa.add_argument("--test", action="append", default=[], metavar="ID")
    wa.add_argument("--choice", required=True)
    wa.add_argument("--why", required=True)
    wa.add_argument("--cost", required=True)
    bp = sub.add_parser("block", help="blocchi del lavoro (8.3)")
    bsub = bp.add_subparsers(dest="block_cmd", required=True)
    bo = bsub.add_parser("open", help="apre un blocco; lo chiude l'utente")
    bo.add_argument("type", metavar="tipo")
    bo.add_argument("--reason", required=True)
    return p


def _status(conn, key: str | None) -> list[dict]:
    from tollgate_flow import checkpoint
    sql, params = "SELECT * FROM work_items WHERE phase <> 'closed'", []
    if key:
        sql += " AND repo_key = ?"
        params.append(key)
    out = []
    for w in conn.execute(sql + " ORDER BY repo_key, issue", params).fetchall():
        blocks = [{"id": b["id"], "type": b["type"], "reason": b["reason"]}
                  for b in conn.execute("SELECT id, type, reason FROM blocks WHERE work = ? "
                                        "AND closed IS NULL ORDER BY id", (w["id"],))]
        counts = {r["state"]: r["n"] for r in conn.execute(
            "SELECT state, count(*) AS n FROM tasks WHERE work = ? GROUP BY state", (w["id"],))}
        out.append({"issue": w["issue"], "repo_key": w["repo_key"], "level": w["level"],
                    "level_cap": w["level_cap"], "phase": w["phase"],
                    "phase_before_block": w["phase_before_block"], "branch": w["branch"],
                    "blocks": blocks, "tasks": counts,
                    "stopped_by": checkpoint.stopped_by(conn, w["id"])})
    return out


def _print_status(items: list[dict]) -> None:
    if not items:
        print("nessun lavoro attivo")
        return
    for it in items:
        phase = it["phase"]
        if phase == "blocked":
            phase += f" (prima: {it['phase_before_block']})"
        print(f"#{it['issue']} {it['repo_key']}  fase {phase}  livello {it['level']}")
        if it["tasks"]:
            print("  task: " + ", ".join(f"{n} {s}" for s, n in sorted(it["tasks"].items())))
        for b in it["blocks"]:
            print(f"  blocco {b['id']} ({b['type']}): {b['reason']}")
        for s in it["stopped_by"]:
            print(f"  {s}")


def _restore(state) -> int:
    interactive = sys.stdin.isatty() and sys.stdout.isatty()

    def confirm(question: str) -> bool:
        return input(question).strip().lower() in ("s", "si", "sì", "y", "yes")

    print(db.restore(state, interactive=interactive, confirm=confirm))
    return 0


def _stats(conn, args) -> int:
    work = None
    if args.work is not None:
        key = current_repo_key(Path.cwd())
        if key is None:
            raise UsageError("--work richiede di essere in un repo con origin")
        row = phases.find_latest(conn, key, args.work)
        if row is None:
            raise UsageError(f"nessun lavoro per #{args.work} in {key}")
        work = row["id"]
    result = stats.compute_stats(conn, now=clock.now(), work=work, since=args.since)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    if args.cmd == "hook":
        from tollgate_hooks.runner import run_hook
        r = run_hook(args.event, sys.stdin.read(), alarm=True)
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        return r.exit
    if args.cmd == "status" and args.note is not None and not args.checkpoint:
        parser.error("--note si usa con --checkpoint")
    state = resolve_state()
    try:
        if args.cmd == "db":
            return _restore(state)
        if args.cmd == "verify":
            code, lines = verify.run_verify(state, Path.cwd(), related=args.related)
            print("\n".join(lines))
            return code
        if args.cmd == "start":
            from tollgate_flow import start as flow_start
            result = flow_start.start(state, Path.cwd(), args.issue, level=args.level,
                                      confirm=args.confirm,
                                      reopen_execution=args.reopen_execution,
                                      claude_dir=Path.home() / ".claude")
            print("\n".join(result.lines))
            return result.code
        if args.cmd == "task":
            from tollgate_flow import taskcmd
            try:
                if args.task_cmd == "review-prepare":
                    print(taskcmd.review_prepare(state, Path.cwd(), args.number))
                elif args.task_cmd == "done":
                    print(taskcmd.task_done(state, Path.cwd(), args.number))
                else:
                    path, summary = taskcmd.task_start(state, Path.cwd(), args.number,
                                                       fix=args.fix,
                                                       claude_dir=Path.home() / ".claude")
                    print(f"{path}\n{summary}")
            except taskcmd.TaskError as e:
                print(f"tollgate: {e}", file=sys.stderr)
                return 1
            return 0
        if args.cmd == "act":
            from tollgate_flow import actapply
            try:
                print(actapply.apply_act(state, Path.cwd(), args.act_id))
            except actapply.ActApplyError as e:
                print(f"tollgate: {e}", file=sys.stderr)
                return 1
            return 0
        if args.cmd == "waiver":
            from . import waiver_cli
            print(waiver_cli.add_waiver(state, Path.cwd(), type_=args.type, file=args.file,
                                        pattern=args.pattern, tests=args.test,
                                        choice=args.choice, why=args.why, cost=args.cost))
            return 0
        if args.cmd == "block":
            from . import waiver_cli
            print(waiver_cli.open_block_cmd(state, Path.cwd(), type_=args.type,
                                            reason=args.reason))
            return 0
        if args.cmd == "status":
            if not state.db_path.exists():
                # sola lettura: senza DB non si crea nulla
                if args.checkpoint:
                    print("tollgate: nessun lavoro attivo per questa cartella: lancia il "
                          "comando dal worktree del lavoro", file=sys.stderr)
                    return 1
                print("[]" if args.json else "nessun lavoro attivo")
                return 0
            if args.checkpoint:
                from tollgate_flow import checkpoint
                try:
                    print(f"checkpoint scritto: "
                          f"{checkpoint.write_checkpoint(state, Path.cwd(), note=args.note)}")
                except checkpoint.CheckpointError as e:
                    print(f"tollgate: {e}", file=sys.stderr)
                    return 1
                return 0
        conn = db.open_db(state)
        try:
            if args.cmd == "status":
                items = _status(conn, current_repo_key(Path.cwd()))
                if args.json:
                    print(json.dumps(items, ensure_ascii=False, indent=2))
                else:
                    _print_status(items)
                return 0
            if args.cmd == "stats":
                return _stats(conn, args)
            if args.cmd == "events":
                try:
                    sys.stdout.write(
                        events.to_jsonl(events.export_events(conn, args.after_seq)))
                    sys.stdout.flush()
                except BrokenPipeError:
                    # il lettore ha chiuso (| head): evita il traceback anche alla chiusura di stdout
                    os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
                return 0
        finally:
            conn.close()
    except (db.DbError, UsageError, phases.TransitionError) as e:
        print(f"tollgate: {e}", file=sys.stderr)
        return 1
    except sqlite3.Error as e:
        print(f"tollgate: errore del database: {e}", file=sys.stderr)
        return 1
    return 0
