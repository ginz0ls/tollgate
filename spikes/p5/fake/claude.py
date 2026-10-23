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
tmp = os.environ.get("TMPDIR") or os.environ["P5_FAKE_RUNS"]
os.makedirs(tmp, exist_ok=True)
n = len([d for d in os.listdir(tmp) if d.startswith("claude-eval-")]) + 1
run_dir = os.path.join(tmp, "claude-eval-fake%d" % n)
ws, home = os.path.join(run_dir, "sealed", "home", "cwd"), os.path.join(run_dir, "sealed", "home")
os.makedirs(os.path.join(ws, ".claude", "worktrees", "sonda-wt"))
os.makedirs(os.path.join(home, ".local", "state", "sonda"))
os.makedirs(os.path.join(home, ".claude", "plugins"))
os.makedirs(os.path.join(run_dir, "out"))
os.makedirs(os.path.join(run_dir, "config"))
os.makedirs(os.path.join(run_dir, "sealed", "tmp"))
for rel, text in (("esiti.txt", "PYTHON3=ok 3\n"), ("sonda-hooks.jsonl", '{"event": "PreToolUse"}\n'),
                  ("sonda-scaffold.txt", "PWD=x\n"), ("scritto-da-hook.md", "x\n"), ("altro.txt", "non va copiato\n"),
                  (".claude/worktrees/sonda-wt/WT-OK", "")):
    with open(os.path.join(ws, rel), "w") as fh:
        fh.write(text)
for rel, text in ((".local/state/sonda/hooks.jsonl", '{"event": "PreToolUse"}\n'), (".claude/plugins/installed_plugins.json", "{}\n"),
                  (".bashrc", "non va copiato\n")):
    with open(os.path.join(home, rel), "w") as fh:
        fh.write(text)
with open(os.path.join(run_dir, "out", "trace.jsonl"), "w") as fh:
    fh.write('{"type": "system", "subtype": "init"}\n')
    if os.environ.get("P5_FAKE_TRACE_TOKEN") == "1":          # una forma di token costruita a runtime
        fh.write('{"testo": "gh' + 'p_' + 'b' * 24 + '"}\n')
settings = {"sandbox": {"enabled": True}}
if os.environ.get("P5_FAKE_SETTINGS_TOKEN") == "1":
    settings["apiKeyHelper"] = {"token": "valore-finto"}
with open(os.path.join(run_dir, "config", "settings.json"), "w") as fh:
    json.dump(settings, fh)
os.chmod(os.path.join(run_dir, "sealed"), 0)           # come l'eval vero: la corsa tenuta è in sola lettura, sealed/ a modo 000
os.chmod(run_dir, 0o500)
result = {"schemaVersion": 1, "costUsd": float(os.environ.get("P5_FAKE_COST", "0.25")), "durationSeconds": 12.5,
          "claudeVersion": "2.1.309 (finto)", "cases": [{"name": case, "aggregates": {"score": 1.0},
                                                           "arms": {"with": [{"tracePath": os.path.join(run_dir, "out", "trace.jsonl")}]}}],
          "aggregates": {"overallScore": 1.0}}
for path in (opt("--json"), os.path.join(out_dir, "aggregate-result.json")):
    with open(path, "w") as fh:
        json.dump(result, fh)
with open(opt("--report"), "w") as fh:
    fh.write("<html><body>report finto</body></html>\n")
sys.stderr.write("\u26a0 kept %s: home/ and tmp/ in it were written by the plugin under test and are sealed in %s/sealed (mode 000)\n" % (run_dir, run_dir))
print("fatto (finto)")
