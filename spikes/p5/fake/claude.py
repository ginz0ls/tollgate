#!/usr/bin/env python3
"""claude finto (dietro il wrapper `claude` che scrive il PATH, perché pyenv lo cambia) del modo controlla di run-p5-checks.sh: registra gli argomenti, nessun modello, nessuna rete.
`plugin eval` scrive result.json, aggregate-result.json e report.html con un costUsd fittizio e simula le cartelle di
--keep-temp con i file della sonda. Ambiente: P5_FAKE_CLAUDE_LOG, P5_FAKE_RUNS, P5_FAKE_COST (predefinito 0.25),
P5_FAKE_CLAUDE_MODE=nojson (nessun JSON, uscita 1)."""
import json
import os
import sys

args = sys.argv[1:]
with open(os.environ["P5_FAKE_CLAUDE_LOG"], "a") as fh:
    fh.write("".join(a + "\t" for a in args) + "\n")
if args == ["--version"]:
    print("2.1.309 (Claude Code) finto")
    sys.exit(0)
if args[:2] != ["plugin", "eval"]:
    sys.stderr.write("claude finto: comando non previsto: %s\n" % " ".join(args))
    sys.exit(2)


def opt(name):
    return args[args.index(name) + 1] if name in args else ""


if os.environ.get("P5_FAKE_CLAUDE_MODE") == "nojson":
    sys.stderr.write("claude finto: interrotto prima di scrivere il JSON\n")
    sys.exit(1)
case = opt("--case") or "tutti"
out_dir = opt("--output-dir")
result = {"schemaVersion": 1, "costUsd": float(os.environ.get("P5_FAKE_COST", "0.25")), "durationSeconds": 12.5,
          "claudeVersion": "2.1.309 (finto)", "cases": [{"name": case, "aggregates": {"score": 1.0}}],
          "aggregates": {"overallScore": 1.0}}
for path in (opt("--json"), os.path.join(out_dir, "aggregate-result.json")):
    with open(path, "w") as fh:
        json.dump(result, fh)
with open(opt("--report"), "w") as fh:
    fh.write("<html><body>report finto</body></html>\n")
runs = os.environ["P5_FAKE_RUNS"]
n = len([d for d in os.listdir(runs) if d.startswith("eval-run-")]) + 1
run_dir = os.path.join(runs, "eval-run-%d" % n)
ws, home = os.path.join(run_dir, "workspace"), os.path.join(run_dir, "home")
os.makedirs(os.path.join(ws, ".claude", "worktrees", "sonda-wt"))
os.makedirs(os.path.join(home, ".local", "state", "sonda"))
for rel, text in (("esiti.txt", "PYTHON3=ok 3\n"), ("sonda-hooks.jsonl", '{"event": "PreToolUse"}\n'),
                  ("sonda-scaffold.txt", "PWD=x\n"), (".claude/worktrees/sonda-wt/WT-OK", "")):
    with open(os.path.join(ws, rel), "w") as fh:
        fh.write(text)
with open(os.path.join(home, ".local", "state", "sonda", "hooks.jsonl"), "w") as fh:
    fh.write('{"event": "PreToolUse"}\n')
sys.stderr.write("Preserved sandbox: %s\n" % run_dir)
print("fatto (finto)")
