#!/usr/bin/env python3
"""B1-V6 e B1-V3 a secco, senza `claude` e senza rete (lo lancia `run-b1-checks.sh latenza`).

Costruisce sotto `--root` (di norma /tmp/tollgate-b1) uno stato con la sentinella, una HOME temporanea e un repo attivo con un
lavoro L1 in esecuzione e un implementatore registrato da `hooks/run SubagentStart`; poi misura `--runs` invocazioni di
`hooks/run PostToolUse` con un Bash `cat` da subagente (il percorso che `post_lookup` farà) e altrettante con un `Read` senza
`agent_id` (il costo della sola shell). In più prova a secco un `PreToolUse` di uno strumento MCP dell'implementatore (B1-V3).
Scrive `latenza.json` e `b1v3-prova.json` in `--out` e stampa mediana e 95° percentile. Le cartelle e i file che esistono già
si rinominano in `<nome>.prev-<tempo>`: niente si cancella."""
import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "bin"))

from tollgate_core import db, git as core_git, phases     # noqa: E402
from tollgate_core.paths import SENTINEL, State, repo_key    # noqa: E402

SESSION = "sess-b1-latenza"
AGENT = "agent-impl-b1"
MCP_TOOL = "mcp__plugin_context7_context7__query-docs"
TOML = 'schema_version = 1\n[gate]\nmode = "protected"\n[commands]\nverify = "true"\ngate = ["verify"]\n'
FILES = {"src/app.py": "def somma(a, b):\n    return a + b\n", ".gitignore": "reports/\n"}
T0 = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)


def rot(path):
    """Se `path` esiste lo rinomina in `<path>.prev-<tempo>` (mai cancellare)."""
    path = Path(path)
    if path.exists() or path.is_symlink():
        path.rename(path.with_name(path.name + ".prev-" + time.strftime("%Y%m%d-%H%M%S") + "-%d" % time.monotonic_ns()))


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=b1", "-c", "user.email=b1@example.com",
                        "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, check=True)
    return r.stdout.strip()


def build_repo(base):
    origin, main = base / "origin.git", base / "main"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)
    main.mkdir(parents=True)
    git(main, "init", "-q", "-b", "main")
    (main / "tollgate.toml").write_text(TOML)
    for rel, text in FILES.items():
        (main / rel).parent.mkdir(parents=True, exist_ok=True)
        (main / rel).write_text(text)
    git(main, "add", "-A")
    git(main, "commit", "-qm", "base")
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "-u", "origin", "main")
    git(main, "remote", "set-head", "origin", "main")
    git(main, "config", "tollgate.defaultBranch", "main")
    wt = base / "wt 7"
    git(main, "worktree", "add", "-q", "-b", "tg/7-demo", str(wt))
    return main, wt, git(main, "rev-parse", "HEAD")


def make_work(state_dir, main, wt, base_sha):
    state = State(state_dir, True)
    conn = db.open_db(state)
    try:
        work = phases.create_work(conn, repo_key=repo_key(core_git.origin_url(main)), issue=7, level="L1", now=T0,
                                  session=SESSION, branch="tg/7-demo", worktree=str(wt), work_base_sha=base_sha,
                                  gate_mode="protected")
        seq = phases.SEQUENCES["L1"]
        cur = phases.get_work(conn, work)["phase"]
        while cur != "execution":
            nxt = seq[seq.index(cur) + 1]
            phases.set_phase(conn, state, work, nxt, phases._FORWARD_CONDITION.get((cur, nxt), "advance"), now=T0 + timedelta(seconds=1))
            cur = nxt
        return work
    finally:
        conn.close()


def clean_env(state_dir, home):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("TOLLGATE_", "P4_", "P5_", "B1_"))}
    env.update(TOLLGATE_STATE=str(state_dir), HOME=str(home), PYTHONDONTWRITEBYTECODE="1")
    return env


def run_hook(event, payload, env):
    """Una invocazione di hooks/run: ritorna (secondi, codice, stdout, stderr)."""
    start = time.perf_counter()
    r = subprocess.run(["bash", str(PLUGIN_ROOT / "hooks" / "run"), event], input=json.dumps(payload), text=True,
                       capture_output=True, env=env, cwd=str(HERE))
    return time.perf_counter() - start, r.returncode, r.stdout, r.stderr


def envelope(event, wt, **extra):
    base = {"session_id": SESSION, "transcript_path": "/tmp/tollgate-b1/transcript.jsonl", "cwd": str(wt),
            "permission_mode": "acceptEdits", "hook_event_name": event}
    base.update(extra)
    return base


def p95(values):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def summarize(label, values):
    ms = [v * 1000 for v in values]
    return {"label": label, "n": len(ms), "median_ms": round(statistics.median(ms), 1), "p95_ms": round(p95(ms), 1),
            "min_ms": round(min(ms), 1), "max_ms": round(max(ms), 1), "samples_ms": [round(v, 1) for v in ms]}


def write_json(path, data):
    rot(path)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="/tmp/tollgate-b1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=50)
    args = ap.parse_args(argv)
    root, out = Path(args.root), Path(args.out)
    if args.runs < 1:
        sys.exit("--runs deve essere almeno 1")
    state_dir, home, base = root / "state", root / "latenza-home", root / "latenza"
    for p in (state_dir, home, base):
        rot(p)
    for p in (state_dir, home, base, out):
        p.mkdir(parents=True, exist_ok=True)
    (state_dir / SENTINEL).write_text("")
    main_repo, wt, base_sha = build_repo(base)
    work = make_work(state_dir, main_repo, wt, base_sha)
    env = clean_env(state_dir, home)

    secs, rc, _, err = run_hook("SubagentStart", envelope("SubagentStart", wt, agent_id=AGENT, agent_type="tollgate:implementer"), env)
    if rc != 0:
        sys.exit("SubagentStart: uscita %d: %s" % (rc, err[:300]))

    cat_pre = envelope("PostToolUse", wt, agent_id=AGENT, agent_type="tollgate:implementer", tool_name="Bash",
                       tool_input={"command": "cat src/app.py", "description": "Legge il file"},
                       tool_response={"stdout": FILES["src/app.py"], "stderr": "", "interrupted": False},
                       tool_use_id="toolu_b1_cat")
    read_pre = envelope("PostToolUse", wt, tool_name="Read", tool_input={"file_path": str(wt / "src" / "app.py")},
                        tool_response={"type": "text", "file": {"filePath": str(wt / "src" / "app.py"), "content": FILES["src/app.py"]}},
                        tool_use_id="toolu_b1_read")
    series = {}
    for label, payload in (("post_bash_subagent", cat_pre), ("post_read_no_agent", read_pre)):
        times = []
        for i in range(args.runs + 1):
            secs, rc, _, err = run_hook("PostToolUse", payload, env)
            if rc != 0:
                sys.exit("%s: uscita %d: %s" % (label, rc, err[:300]))
            if i:                                    # la prima è di riscaldamento (cache del disco), non conta
                times.append(secs)
        series[label] = summarize(label, times)

    secs, rc, stdout, stderr = run_hook("PreToolUse", envelope(
        "PreToolUse", wt, agent_id=AGENT, agent_type="tollgate:implementer", tool_name=MCP_TOOL,
        tool_input={"libraryId": "/python/cpython", "query": "tomllib"}, tool_use_id="toolu_b1_mcp"), env)
    v3 = {"tool_name": MCP_TOOL, "agent_id": AGENT, "exit_code": rc, "stdout": stdout, "stderr": stderr,
          "denied": rc == 2, "seconds": round(secs, 3), "work": work}
    write_json(out / "latenza.json", {"runs": args.runs, "series": series, "work": work, "root": str(root)})
    write_json(out / "b1v3-prova.json", v3)
    for s in series.values():
        print("%s: n=%d mediana %.1f ms, 95° percentile %.1f ms" % (s["label"], s["n"], s["median_ms"], s["p95_ms"]))
    print("B1-V3 a secco: uscita %d (%s)" % (rc, "negato" if rc == 2 else "non negato"))


if __name__ == "__main__":
    main()
