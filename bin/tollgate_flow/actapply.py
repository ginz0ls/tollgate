"""`tollgate act apply [<id>]` (spec 8.4, decisione 13): effetti degli atti che non valgono dal DB.

L'hook registra l'atto, la CLI lo applica. L'atto si consuma sempre e una volta sola, prima
dell'applicatore: un rifiuto dell'applicatore non lo lascia pronto per un secondo tentativo.
`approve waiver` e `approve effect` non passano di qui (valgono già dal DB, 8.4 e 8.5)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tollgate_analysis import level as lv
from tollgate_core import acts, clock, config, db, git, phases, sessions, subagents, tasks


class ActApplyError(Exception):
    pass


def _label(row) -> str:
    return " ".join(x for x in (row["type"], row["object"], row["target"]) if x)


def _config(state, work) -> config.Config:
    wt = Path(work["worktree"])
    main = git.main_worktree(wt)
    base = work["work_base_sha"] or git.default_ref(main)
    try:
        return config.load_config(state, main, base)
    except config.ConfigError as e:
        raise ActApplyError(f"configurazione non valida: {e}") from e


def _resolve(conn, state, work, act, args, now, session) -> str:
    if act["target"] == "writer":
        cfg = _config(state, work)
        stopped = [r["id"] for r in subagents.running(conn, work=work["id"])
                   if not config.is_readonly(cfg, r["type"])]
        for agent_id in stopped:
            subagents.interrupt(conn, agent_id, now=now, session=session)
        return ("implementatori interrotti: " + ", ".join(stopped)) if stopped \
            else "nessun implementatore in corso da interrompere"
    block = None
    if act["target"].isdigit():
        block = conn.execute("SELECT id FROM blocks WHERE id = ? AND work = ? "
                             "AND closed IS NULL", (int(act["target"]), work["id"])).fetchone()
    if block is None:
        raise ActApplyError(f"blocco {act['target']}: non è un blocco aperto di questo lavoro")
    note = " ".join(args[1:]).strip() or "risolto dall'utente"
    phase = phases.close_block(conn, state, block["id"], note, now=now, session=session)
    unblocked = []
    if phase != "blocked":
        for t in conn.execute("SELECT number FROM tasks WHERE work = ? AND state = 'blocked' "
                              "ORDER BY number", (work["id"],)).fetchall():
            tasks.task_event(conn, work["id"], t["number"], "unblocked", now=now,
                             session=session)
            unblocked.append(t["number"])
    msg = f"blocco {block['id']} chiuso; fase {phase}"
    if unblocked:
        msg += "; task di nuovo pending: " + ", ".join(str(n) for n in unblocked)
    return msg


def _approve_level(conn, state, work, act, args, now, session) -> str:
    cap = act["target"]
    if cap not in phases.LEVELS:
        raise ActApplyError(f"livello sconosciuto: {cap} (L0, L1 o L2)")
    reason = " ".join(args[2:]).strip()
    if not reason:
        raise ActApplyError("approve level vuole un motivo: /tollgate:approve level <L> <motivo>")
    cfg = _config(state, work)
    wt, base = Path(work["worktree"]), work["work_base_sha"]
    if not base or not wt.is_dir():
        raise ActApplyError("lavoro senza base o worktree: il diff non è calcolabile")
    changes = git.changes(wt, base, exclude=config.output_excludes(cfg))
    paths = [c.path for c in changes] + [c.old_path for c in changes if c.old_path]
    cap_paths = lv.sensitive_in(paths, cfg.get("levels.sensitive_paths"))
    try:
        phases.set_level_cap(conn, work["id"], cap, reason, cap_paths, now=now, session=session)
    except phases.TransitionError as e:
        raise ActApplyError(str(e)) from e
    level = phases.get_work(conn, work["id"])["level"]
    return f"tetto {cap} fissato (livello {level}), valido finché il diff non tocca un " \
           f"percorso sensibile nuovo; percorsi sensibili attuali: {len(cap_paths)}"


APPLIERS = {
    ("resolve", None): _resolve,
    ("approve", "level"): _approve_level,
}


def _pick(conn, work, act_id, session, now):
    if act_id is not None:
        row = conn.execute("SELECT * FROM acts WHERE act_id = ?", (act_id,)).fetchone()
        if row is None:
            raise ActApplyError(f"atto {act_id} inesistente")
        if (row["type"], row["object"]) not in APPLIERS:
            raise ActApplyError(f"atto {act_id} ({_label(row)}) non si applica con act apply")
        return row
    marks = ",".join("(?, ?)" for _ in APPLIERS)
    keys = [x for k in APPLIERS for x in (k[0], k[1] or "")]
    row = conn.execute(
        "SELECT * FROM acts WHERE state = 'pending' AND session = ? AND work = ? "
        f"AND expires_at > ? AND (type, coalesce(object, '')) IN (VALUES {marks}) "
        "ORDER BY n DESC LIMIT 1", [session, work["id"], clock.fmt(now), *keys]).fetchone()
    if row is None:
        raise ActApplyError("nessun atto da applicare per questa sessione: dai prima "
                            "/tollgate:resolve o /tollgate:approve level")
    return row


def apply_act(state, cwd, act_id: str | None, *, now=None) -> str:
    now = now or clock.now()
    try:
        conn = db.open_db(state)
    except db.DbError as e:
        raise ActApplyError(str(e)) from e
    try:
        try:
            session = sessions.cli_session(state, cwd, "act", now=now)
        except sessions.CliSessionError as e:
            raise ActApplyError(str(e)) from e
        work = sessions.work_for_path(conn, cwd)
        if work is None:
            raise ActApplyError("nessun lavoro attivo per questa cartella: lancia il comando "
                                "dal worktree del lavoro")
        act = _pick(conn, work, act_id, session, now)
        try:
            acts.consume(conn, act["act_id"], type_=act["type"], object_=act["object"],
                         target=act["target"], now=now, work=work["id"], session=session)
        except acts.ActError as e:
            raise ActApplyError(str(e)) from e
        applier = APPLIERS[(act["type"], act["object"])]
        try:
            msg = applier(conn, state, work, act, json.loads(act["args"]), now, session)
        except (sqlite3.Error, phases.TransitionError, tasks.TaskTransitionError,
                git.GitError) as e:
            raise ActApplyError(str(e)) from e
        return f"atto {act['act_id']} applicato ({_label(act)}): {msg}"
    finally:
        conn.close()
