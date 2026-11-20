"""L'esecuzione degli eval (Task 11 di P5): `evals/run.sh` e `evals/cost.py`.

Mai un `claude` vero: nel `PATH` c'è un `claude` finto che registra gli argomenti e scrive un `result.json` nella forma
reale di `claude plugin eval` (VE8, visto nelle sonde del Task 1). HOME, TMPDIR, registro dei costi, radice delle
evidenze e bersaglio sono cartelle temporanee: nessun test scrive in `docs/verifiche/evidenze/eval-p5/` né in `eval-b8/`.
Nome utente e host nei test sono sempre finti (`utente-prova`, `macchina-prova`): mai quelli veri."""
import fcntl
import io
import json
import os
import signal
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from evals import cost, research_counts, scrub
from tests.helpers import ROOT

RUN_SH = ROOT / "evals" / "run.sh"
def cost_remaining(budget):
    with mock.patch.dict(os.environ, TOLLGATE_EVAL_BUDGET=str(budget), TOLLGATE_EVAL_TEST_MODE="1"):
        return cost.remaining()


HEADER = "ora\tinvocazione\tcostUsd\tdurationSeconds\tcasi\n"

FAKE_USER, FAKE_HOST = "utente-prova", "macchina-prova"
LONG_PAGE = "PAGINA-DI-TERZI " * 100
SEARCH_SNIPPET = "FRAMMENTO-DI-TERZI per Gemini"
SHELL_PAGE = "CORPO-DELLA-PAGINA-LETTA-CON-CURL"

FAKE_CLAUDE = r'''#!__PY__
"""claude finto: registra gli argomenti, scrive result.json e finge le corse tenute di --keep-temp."""
import json, os, sys, time
args = sys.argv[1:]
log = os.environ["FAKE_CLAUDE_LOG"]
with open(log, "a") as fh:
    fh.write(json.dumps({"args": args, "path": os.environ.get("PATH", ""), "tmpdir": os.environ.get("TMPDIR", ""),
                         "stdin": sys.stdin.read(), "cwd": os.getcwd(), "pid": os.getpid()}) + "\n")
if os.environ.get("FAKE_SLEEP"):
    time.sleep(float(os.environ["FAKE_SLEEP"]))
if os.environ.get("FAKE_TOKEN_STDOUT"):
    sys.stdout.write("ghp_" + "B" * 20 + "\n")
if os.environ.get("FAKE_LEAK_STDOUT"):
    sys.stdout.write("cartella /home/%s sulla macchina %s\n" % (os.environ["TOLLGATE_EVAL_FAKE_USER"], os.environ["TOLLGATE_EVAL_FAKE_HOST"]))
def opt(name):
    return args[args.index(name) + 1]
tmp = os.environ["TMPDIR"]
mode = os.environ.get("FAKE_PLUGIN", "loaded")      # loaded | missing
arms = {"with": [], "without": []}
for arm in ("with", "without"):
    if arm == "without" and opt("--ablation") == "none":
        continue
    for n in range(int(opt("--runs"))):
        run = os.path.join(tmp, "claude-eval-%s%d%s" % ("W" if arm == "with" else "O", n, os.urandom(2).hex()))
        os.makedirs(os.path.join(run, "out"))
        os.makedirs(os.path.join(run, "config"))
        cwd = os.path.join(run, "sealed", "home", "cwd")
        os.makedirs(cwd)
        os.makedirs(os.path.join(run, "sealed", "home", ".claude", "plugins"))
        plugins = [{"name": "cc-plugin-agents-md", "path": "builtin", "source": "cc-plugin-agents-md@builtin"}]
        if arm == "with" and mode == "loaded":
            plugins.insert(0, {"name": "tollgate", "path": "/x", "source": "tollgate@inline", "version": "0.5.0"})
        with open(os.path.join(run, "out", "trace.jsonl"), "w") as fh:
            fh.write(json.dumps({"type": "system", "subtype": "init", "plugins": plugins}) + "\n")
            if os.environ.get("FAKE_WEB_TRACE"):
                def put(kind, content, **extra):
                    fh.write(json.dumps({"type": kind, "message": {"role": kind, "content": content}, **extra}) + "\n")
                put("assistant", [{"type": "tool_use", "id": "w1", "name": "WebFetch",
                                   "input": {"url": "https://ai.google.dev/gemini-api/docs/models", "prompt": "elenca"}}])
                put("user", [{"type": "tool_result", "tool_use_id": "w1", "content": os.environ["FAKE_LONG_PAGE"]}],
                    tool_use_result={"bytes": 1600, "code": 200, "codeText": "OK", "result": os.environ["FAKE_LONG_PAGE"],
                                     "durationMs": 12, "url": "https://ai.google.dev/gemini-api/docs/models"})
                put("assistant", [{"type": "tool_use", "id": "w2", "name": "WebSearch", "input": {"query": "modelli gemini"}}])
                put("user", [{"type": "tool_result", "tool_use_id": "w2", "content": os.environ["FAKE_SNIPPET"]}],
                    tool_use_result={"query": "modelli gemini", "durationSeconds": 1.5,
                                     "results": [{"tool_use_id": "srv1", "content": [{"title": os.environ["FAKE_SNIPPET"], "url": "https://t.example/x"}]},
                                                 os.environ["FAKE_SNIPPET"]]})
                put("assistant", [{"type": "tool_use", "id": "w3", "name": "Bash",
                                   "input": {"command": "curl -s https://vercel.com/docs/project-configuration"}}])
                put("user", [{"type": "tool_result", "tool_use_id": "w3", "content": os.environ["FAKE_SHELL_PAGE"]}],
                    tool_use_result={"stdout": os.environ["FAKE_SHELL_PAGE"], "stderr": "", "interrupted": False})
            if os.environ.get("FAKE_DENIED_ROW"):
                fh.write(json.dumps({"type": "system", "subtype": "permission_denied", "tool_name": "WebFetch",
                                     "tool_use_id": "toolu_X", "agent_id": "a1", "decision_reason_type": "mode",
                                     "message": "Permission to use WebFetch has been denied.", "uuid": "u1",
                                     "session_id": "s1"}) + "\n")
            if os.environ.get("FAKE_LEAK"):
                fh.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
                    {"type": "text", "text": "lavoro in /home/%s/.cache sulla macchina %s" % (os.environ["TOLLGATE_EVAL_FAKE_USER"],
                                                                                        os.environ["TOLLGATE_EVAL_FAKE_HOST"])}]}}) + "\n")
            fh.write(json.dumps({"type": "result", "total_cost_usd": 0.5, "usage": {
                "input_tokens": 10, "output_tokens": 100, "cache_read_input_tokens": 1000,
                "cache_creation_input_tokens": 50}}) + "\n")
        with open(os.path.join(run, "config", "settings.json"), "w") as fh:
            fh.write('{"cacheDir": "/home/%s/.cache"}\n' % os.environ["TOLLGATE_EVAL_FAKE_USER"] if os.environ.get("FAKE_LEAK") else "{}\n")
        if os.environ.get("FAKE_SYMLINK_SETTINGS"):
            os.remove(os.path.join(run, "config", "settings.json"))
            os.symlink(os.environ["FAKE_SYMLINK_SETTINGS"], os.path.join(run, "config", "settings.json"))
        with open(os.path.join(cwd, "ESITO.txt"), "w") as fh:
            fh.write("ok\n")
        with open(os.path.join(cwd, "segreto.txt"), "w") as fh:
            fh.write("ghp_" + "A" * 20 + "\n")
        state = os.path.join(run, "sealed", "home", ".local", "state", "tollgate")
        os.makedirs(state)
        open(os.path.join(state, "migrate.lock"), "w").close()
        with open(os.path.join(state, "stato.txt"), "w") as fh:
            fh.write("ok\n")
        if os.environ.get("FAKE_STATE_DB") and arm == "with":
            import sqlite3
            conn = sqlite3.connect(os.path.join(state, "tollgate.db"))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, type TEXT, host TEXT, data TEXT)")
            conn.execute("CREATE TABLE lookups (id INTEGER PRIMARY KEY, kind TEXT, target TEXT)")
            host = os.environ["TOLLGATE_EVAL_FAKE_HOST"]
            for typ, data in (("research_note", {"ok": True}), ("research_note", {"ok": False}), ("research_reminder", {"task": 1}),
                              ("veto", {"rule": "research_gate"}), ("veto", {"rule": "altra"})):
                conn.execute("INSERT INTO events (type, host, data) VALUES (?, ?, ?)", (typ, host, json.dumps(data)))
            conn.execute("INSERT INTO lookups (kind, target) VALUES ('fetch', 'https://vercel.com/docs')")
            conn.commit()
            conn.close()
        os.makedirs(os.path.join(cwd, ".git"))
        with open(os.path.join(cwd, ".git", "config"), "w") as fh:
            fh.write("x\n")
        os.chmod(os.path.join(run, "sealed"), 0)
        os.chmod(run, 0o500)
        arms[arm].append({"score": 1.0 if arm == "with" else 0.5, "passed": True, "turns": 4, "costUsd": 0.01,
                          "judgeCostUsd": 0, "durationSeconds": 10, "startedAt": "2026-10-24T10:00:00.000Z",
                          "error": None, "tracePath": os.path.join(run, "out", "trace.jsonl"), "graders": []})
        sys.stderr.write("\u26a0 kept %s: home/ and tmp/ in it are sealed\n" % run)
if os.environ.get("FAKE_EXTRA_KEPT"):
    sys.stderr.write("\u26a0 kept %s: x\n" % os.environ["FAKE_EXTRA_KEPT"])
cases = []
sel = opt("--case") if "--case" in args else None
for name in ([sel] if sel else ["s1-fake", "s2-fake"]):
    c = {"name": name, "runsPerCase": int(opt("--runs")), "arms": {k: v for k, v in arms.items() if v},
         "aggregates": {"score": 1.0, "passRate": 1}}
    if arms["without"]:
        c["aggregates"].update(scoreWithout=0.5, passRateWithout=0, delta=0.5)
    cases.append(c)
if not os.environ.get("FAKE_NO_RESULT"):
    with open(opt("--json"), "w") as fh:
        json.dump({"schemaVersion": 1, "durationSeconds": 32, "costUsd": float(os.environ.get("FAKE_COST", "1.25")),
                   "partial": False, "cases": cases,
                   "aggregates": {"casesTotal": len(cases)}}, fh)
sys.exit(int(os.environ.get("FAKE_RC", "0")))
'''


def make_result(cases, cost_usd=1.25, duration=32):
    """Un result.json nella forma di VE8."""
    return {"schemaVersion": 1, "claudeVersion": "2.1.309", "durationSeconds": duration, "costUsd": cost_usd,
            "partial": False, "cases": cases, "aggregates": {"casesTotal": len(cases)}}


def case_entry(name, with_scores, without_scores, trace_root="/x/claude-eval-"):
    def runs(scores, prefix):
        return [{"score": s, "passed": s >= 0.66, "turns": 3, "costUsd": 0.1, "judgeCostUsd": 0,
                 "durationSeconds": 7, "error": None,
                 "tracePath": f"{trace_root}{prefix}{i}/out/trace.jsonl"} for i, s in enumerate(scores)]
    arms = {"with": runs(with_scores, "W")}
    agg = {"score": sum(with_scores) / len(with_scores), "passRate": 1}
    if without_scores is not None:
        arms["without"] = runs(without_scores, "O")
        agg.update(scoreWithout=sum(without_scores) / len(without_scores), passRateWithout=0,
                   delta=agg["score"] - sum(without_scores) / len(without_scores))
    return {"name": name, "runsPerCase": len(with_scores), "arms": arms, "aggregates": agg}


class EvalRunBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-test-evalrun-"))
        self.addCleanup(self.cleanup)
        self.home = self.tmp / "home"
        self.bin = self.tmp / "bin"
        self.evidence = self.tmp / "evidenze"
        self.budget = self.tmp / "budget.tsv"
        self.target = self.tmp / "target"
        self.evtmp = self.tmp / "evtmp"
        self.log = self.tmp / "claude.log"
        for d in (self.home, self.bin, self.evidence):
            d.mkdir()
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE.replace("__PY__", sys.executable), encoding="utf-8")
        fake.chmod(0o755)

    def cleanup(self):
        for p in self.tmp.rglob("*"):          # le corse finte sono sigillate come quelle vere
            try:
                if p.is_dir() and not p.is_symlink():
                    p.chmod(0o700)
            except OSError:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_budget(self, *costs):
        rows = "".join(f"2026-10-23T19:00:0{i}Z\tprova\t{c}\t5\tx\n" for i, c in enumerate(costs))
        self.budget.write_text(HEADER + rows, encoding="utf-8")

    def env(self, **extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("TOLLGATE_", "CLAUDE", "FAKE_"))}
        env.update(HOME=str(self.home), TMPDIR=str(self.tmp), PYTHONDONTWRITEBYTECODE="1",
                   PATH=f"{self.bin}:{os.environ['PATH']}", FAKE_CLAUDE_LOG=str(self.log),
                   TOLLGATE_EVAL_BUDGET=str(self.budget), TOLLGATE_EVAL_EVIDENCE=str(self.evidence),
                   TOLLGATE_EVAL_TARGET=str(self.target), TOLLGATE_EVAL_TMPDIR=str(self.evtmp),
                   TOLLGATE_EVAL_TEST_MODE="1", TOLLGATE_EVAL_FAKE_USER=FAKE_USER, TOLLGATE_EVAL_FAKE_HOST=FAKE_HOST,
                   FAKE_LONG_PAGE=LONG_PAGE, FAKE_SNIPPET=SEARCH_SNIPPET, FAKE_SHELL_PAGE=SHELL_PAGE)
        env.update(extra)
        return env

    def run_sh(self, *args, **extra):
        return subprocess.run(["bash", str(RUN_SH), *args], capture_output=True, text=True, env=self.env(**extra),
                              timeout=300, stdin=subprocess.DEVNULL)

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def rows(self):
        return [line.split("\t") for line in self.budget.read_text().splitlines()[1:]]

    def out_dirs(self):
        return sorted(p for p in self.evidence.iterdir() if p.is_dir())


class RunShTest(EvalRunBase):
    def test_syntax(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(RUN_SH)]).returncode, 0)

    def test_always_no_publish(self):
        r = self.run_sh("spec")
        self.assertEqual(r.returncode, 0, r.stderr)
        args = self.calls()[0]["args"]
        self.assertIn("--no-publish", args)
        self.assertNotIn("--publish-report", args)
        self.assertEqual(args[:2], ["plugin", "eval"])
        for flag in ("--scaffold", "--trust-plugin", "--keep-temp"):
            self.assertIn(flag, args)
        self.assertEqual(args[args.index("--model") + 1], "claude-sonnet-5-5")
        self.assertEqual(args[args.index("--threshold") + 1], "0.66")
        i = args.index("--allow-tools")
        self.assertEqual(args[i + 1:i + 4], ["Bash", "Write", "Edit"])

    def test_refuses_without_budget(self):
        self.write_budget(80)
        r = self.run_sh("spec")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.calls(), [])
        self.assertIn("esaurito", r.stderr)

    def test_refuses_unreadable_budget_row(self):
        self.budget.write_text(HEADER + "2026-10-23T19:00:00Z\tx\t?\t?\ty\n", encoding="utf-8")
        r = self.run_sh("spec")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.calls(), [])

    def test_max_cost_is_remaining(self):
        self.write_budget(30.25, 0.25)
        self.assertEqual(self.run_sh("--campagna", "p5", "spec").returncode, 0)
        args = self.calls()[0]["args"]
        self.assertEqual(args[args.index("--max-cost-usd") + 1], "49.50")

    def test_cost_added_on_nonzero_exit(self):
        for rc in (1, 2):
            with self.subTest(rc=rc):
                self.write_budget(10)
                r = self.run_sh("spec", FAKE_RC=str(rc), FAKE_COST="2.5")
                self.assertEqual(r.returncode, rc, r.stderr)
                rows = self.rows()
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[1][2], "2.5")
                self.assertEqual(rows[1][3], "32")
                self.assertEqual(rows[1][4], "s1-fake,s2-fake")
                self.assertIn("spec", rows[1][1])

    def test_missing_result_stops_and_asks(self):
        self.write_budget(10)
        r = self.run_sh("spec", FAKE_NO_RESULT="1", FAKE_RC="2")
        self.assertEqual(r.returncode, 3)
        self.assertIn("costo ignoto: controlla a mano prima di continuare", r.stderr)
        self.assertEqual(self.rows()[-1][2], "?")
        again = self.run_sh("spec")                      # la riga con «?» chiude il tetto: niente di nuovo
        self.assertEqual(again.returncode, 1)
        self.assertEqual(len(self.calls()), 1)

    def test_shim_first_in_path(self):
        self.assertEqual(self.run_sh("spec").returncode, 0)
        call = self.calls()[0]
        shim = self.target / "tests" / "evalbin"
        self.assertEqual(call["path"].split(":")[0], str(shim))
        self.assertTrue((shim / "gh").is_file() and (shim / "python3").is_file())
        self.assertEqual(call["args"][2], str(self.target))       # la radice valutata è la copia, mai il repo
        self.assertEqual(call["tmpdir"], str(self.evtmp.resolve()))
        self.assertEqual(call["stdin"], "")
        self.assertNotIn("--plugin-dir", call["args"])

    def test_output_dir_fixed(self):
        self.assertEqual(self.run_sh("spec").returncode, 0)
        args = self.calls()[0]["args"]
        out, = self.out_dirs()
        self.assertRegex(out.name, r"^\d{8}T\d{6}Z-spec$")
        self.assertEqual(args[args.index("--output-dir") + 1], str(out))
        self.assertEqual(args[args.index("--json") + 1], str(out / "result.json"))
        self.assertEqual(args[args.index("--report") + 1], str(out / "report.html"))
        self.assertTrue((out / "result.json").is_file())
        self.assertTrue((out / "stdout.txt").is_file() and (out / "stderr.txt").is_file())

    def test_refuses_other_output_or_publish(self):
        for extra in (["--output-dir", "/x"], ["--output-dir=/x"], ["--json", "/x/r.json"], ["--report", "/x/r.html"],
                      ["--publish-report"], ["--publish"], ["--no-publish"], ["--model", "x"]):
            with self.subTest(extra=extra):
                r = self.run_sh("spec", *extra)
                self.assertEqual(r.returncode, 64)
                self.assertEqual(self.calls(), [])
        self.assertEqual(self.out_dirs(), [])

    def test_selectors(self):
        cases = {"spec": (["--tag", "spec"], "with-without"), "extra": (["--tag", "extra"], "none"),
                 "s1-done-senza-ricevuta": (["--case", "s1-done-senza-ricevuta"], "with-without"),
                 "e1-audit-a-lenti": (["--case", "e1-audit-a-lenti"], "none")}
        for selector, (select, ablation) in cases.items():
            with self.subTest(selector=selector):
                self.log.unlink(missing_ok=True)
                self.assertEqual(self.run_sh(selector).returncode, 0)
                args = self.calls()[0]["args"]
                self.assertEqual(args[args.index(select[0]) + 1], select[1])
                self.assertEqual(args[args.index("--ablation") + 1], ablation)
                self.assertEqual(args[args.index("--runs") + 1], "3")

    def test_runs_option_and_bad_selectors(self):
        self.assertEqual(self.run_sh("spec", "--runs", "5").returncode, 0)
        args = self.calls()[0]["args"]
        self.assertEqual(args[args.index("--runs") + 1], "5")
        self.log.unlink()
        for bad in (["nessun-caso"], ["../evals"], [], ["spec", "extra"], ["spec", "--runs", "0"],
                    ["spec", "--runs", "x"], ["spec", "--runs"], ["--runs", "3"]):
            with self.subTest(bad=bad):
                self.assertEqual(self.run_sh(*bad).returncode, 64)
        self.assertEqual(self.calls(), [])

    def test_tmpdir_refused_under_tmp(self):
        env = {"TOLLGATE_EVAL_TEST_MODE": ""}
        link = self.home / "via-tmp"
        link.symlink_to("/tmp")
        for d in (self.tmp / "t", "/tmp/tollgate-x", "/var/tmp/x", "/dev/shm/x", str(self.home / "a" / ".." / ".." / "x"),
                  str(link / "tollgate-eval-sub"), "relativo"):
            with self.subTest(d=str(d)):
                r = self.run_sh("spec", TOLLGATE_EVAL_TMPDIR=str(d), **env)
                self.assertEqual(r.returncode, 64, r.stderr)
                self.assertEqual(self.calls(), [])

    def test_runs_copied_without_tokens(self):
        self.assertEqual(self.run_sh("spec", "--runs", "1").returncode, 0)
        out, = self.out_dirs()
        runs = sorted(p.name for p in (out / "runs").iterdir())
        self.assertEqual([n[:14] for n in runs], ["claude-eval-O0", "claude-eval-W0"])
        w = out / "runs" / runs[1]
        self.assertTrue((w / "trace.jsonl").is_file())
        self.assertTrue((w / "settings.json").is_file())
        self.assertTrue((w / "cwd" / "ESITO.txt").is_file())
        self.assertFalse((w / "cwd" / ".git").exists())
        self.assertTrue((w / "home" / ".local" / "state" / "tollgate" / "stato.txt").is_file())
        self.assertFalse((w / "home" / ".local" / "state" / "tollgate" / "migrate.lock").exists())
        self.assertFalse((w / "cwd" / "segreto.txt").exists())
        self.assertIn("segreto.txt", (w / "file-non-copiati.txt").read_text())
        self.assertNotIn("ghp_", "".join(p.read_text(errors="replace") for p in out.rglob("*")
                                         if p.is_file() and p.name != "result.json" and p.suffix != ".html"
                                         and p.name != "stderr.txt"))

    def test_kept_dir_outside_eval_tmp_not_copied(self):
        stray = self.tmp / "claude-eval-ESTRANEA"
        stray.mkdir()
        (stray / "out").mkdir()
        (stray / "out" / "trace.jsonl").write_text("{}\n")
        other = self.evtmp / "altra-cartella"
        other.mkdir(parents=True)
        for d in (stray, other):
            with self.subTest(d=d.name):
                r = self.run_sh("spec", "--runs", "1", FAKE_EXTRA_KEPT=str(d))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("ignorata", r.stdout)
                self.assertFalse(any((o / "runs" / d.name).exists() for o in self.out_dirs()))

    def test_plugin_not_loaded_stops(self):
        self.write_budget(10)
        r = self.run_sh("spec", "--runs", "1", FAKE_PLUGIN="missing", FAKE_COST="2")
        self.assertEqual(r.returncode, 4)
        self.assertNotIn(r.returncode, (0, 1, 2))
        self.assertIn("plugin tollgate non caricato: controlla prima di continuare", r.stderr)
        self.assertEqual(self.rows()[-1][2], "2.0")          # il costo è entrato comunque
        self.assertTrue((self.out_dirs()[0] / "tabella.md").is_file())      # la tabella c'è anche così

    def test_plugin_loaded_extra_ablation_none(self):
        r = self.run_sh("extra", "--runs", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        out, = self.out_dirs()
        self.assertEqual([p.name[:14] for p in (out / "runs").iterdir()], ["claude-eval-W0"])
        self.assertTrue((out / "tabella.md").is_file())

    def test_timeout_without_result_is_unknown_cost(self):
        r = self.run_sh("spec", FAKE_SLEEP="20", FAKE_NO_RESULT="1", TOLLGATE_EVAL_TIMEOUT="1")
        self.assertEqual(r.returncode, 3)
        out, = self.out_dirs()
        self.assertEqual((out / "claude.rc").read_text().strip(), "124")

    def test_interrupt_leaves_reservation(self):
        """SIGTERM allo script mentre claude gira: la riga «?» è già in budget.tsv e il residuo è 0."""
        proc = subprocess.Popen(["bash", str(RUN_SH), "spec"], env=self.env(FAKE_SLEEP="30"), stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        fake_pid = None
        try:
            for _ in range(200):
                if self.calls():
                    fake_pid = self.calls()[0]["pid"]
                    break
                time.sleep(0.1)
            self.assertIsNotNone(fake_pid, "il claude finto non è partito")
            os.kill(proc.pid, signal.SIGTERM)             # il PID del processo avviato qui, mai per nome
            proc.wait(timeout=30)
        finally:
            if proc.poll() is None:
                os.kill(proc.pid, signal.SIGKILL)
                proc.wait()
            if fake_pid:
                try:
                    os.kill(fake_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "?")
        self.assertIn("spec", rows[0][1])
        self.assertEqual(cost_remaining(self.budget), 0.0)

    def test_reservation_replaced_by_real_cost(self):
        self.write_budget(10)
        self.assertEqual(self.run_sh("spec").returncode, 0)
        rows = self.rows()
        self.assertEqual(len(rows), 2)               # la riga prenotata è stata sostituita, non duplicata
        self.assertEqual(rows[1][2], "1.25")

    def test_env_paths_need_test_mode(self):
        for var in ("TOLLGATE_EVAL_BUDGET", "TOLLGATE_EVAL_EVIDENCE", "TOLLGATE_EVAL_TARGET",
                    "TOLLGATE_EVAL_FAKE_USER", "TOLLGATE_EVAL_FAKE_HOST"):
            with self.subTest(var=var):
                env = {"TOLLGATE_EVAL_TEST_MODE": "", "TOLLGATE_EVAL_BUDGET": "", "TOLLGATE_EVAL_EVIDENCE": "",
                       "TOLLGATE_EVAL_TARGET": "", "TOLLGATE_EVAL_FAKE_USER": "", "TOLLGATE_EVAL_FAKE_HOST": "",
                       var: str(self.tmp / "x")}
                r = self.run_sh("spec", **env)
                self.assertEqual(r.returncode, 64)
                self.assertIn(var, r.stderr)
                self.assertEqual(self.calls(), [])
        self.assertFalse((self.tmp / "x").exists())

    def test_preamble_prints_paths_and_test_mode(self):
        self.write_budget(5)
        r = self.run_sh("--campagna", "p5", "spec")
        for text in (f"registro dei costi: {self.budget}", f"cartella delle evidenze: {self.evidence}",
                     f"bersaglio: {self.target}", f"TMPDIR dell'eval: {self.evtmp.resolve()}",
                     "residuo del tetto: 75.00 USD", "TEST_MODE attivo"):
            self.assertIn(text, r.stdout)

    def test_timeout_validated(self):
        for bad in ("abc", "0", "-5", "1.5", "", "007"):
            with self.subTest(bad=bad):
                r = self.run_sh("spec", TOLLGATE_EVAL_TIMEOUT=bad) if bad else None
                if r is None:
                    continue
                self.assertEqual(r.returncode, 64)
                self.assertEqual(self.calls(), [])
                self.assertFalse(self.budget.exists())          # niente prenotazione

    def test_second_invocation_refused_by_lock(self):
        self.budget.parent.mkdir(exist_ok=True)
        with open(str(self.budget) + ".lock", "w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            r = self.run_sh("spec")
        self.assertEqual(r.returncode, 64)
        self.assertIn("un'altra invocazione", r.stderr)
        self.assertEqual(self.calls(), [])

    def test_token_in_evidence_stops(self):
        self.write_budget(10)
        r = self.run_sh("spec", "--runs", "1", FAKE_TOKEN_STDOUT="1")
        self.assertEqual(r.returncode, 4)
        self.assertIn("forma di token nelle evidenze: non committare", r.stderr)
        self.assertNotIn("ghp_BBBB", r.stdout + r.stderr)
        self.assertEqual(self.rows()[-1][2], "1.25")                 # il costo è già registrato
        self.assertIn("stdout.txt", (self.out_dirs()[0] / "file-con-token.txt").read_text())

    def test_symlinked_settings_not_followed(self):
        outside = self.tmp / "fuori.json"
        outside.write_text('{"fuori": "SEGNALE-FUORI"}\n')
        self.assertEqual(self.run_sh("spec", "--runs", "1", FAKE_SYMLINK_SETTINGS=str(outside)).returncode, 0)
        out, = self.out_dirs()
        self.assertFalse(any("SEGNALE-FUORI" in p.read_text(errors="replace") for p in out.rglob("*") if p.is_file()))

    def test_dry_run_in_test_mode_touches_nothing(self):
        self.write_budget(20)
        before = self.budget.read_bytes()
        r = self.run_sh("--a-secco", "--campagna", "p5", "spec")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.budget.read_bytes(), before)
        self.assertFalse(Path(str(self.budget) + ".lock").exists())
        self.assertEqual(self.out_dirs(), [])
        self.assertIn("residuo del tetto: 60.00", r.stdout)
        self.assertIn("a secco", r.stdout)
        self.write_budget(80)
        self.assertEqual(self.run_sh("--a-secco", "--campagna", "p5", "spec").returncode, 1)
        self.budget.write_text(HEADER + "2026-10-23T19:00:00Z\tx\t?\t?\ty\n", encoding="utf-8")      # prenotazione rimasta
        before = self.budget.read_bytes()
        r = self.run_sh("--a-secco", "spec")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.budget.read_bytes(), before)
        self.assertEqual(self.calls(), [])

    def test_dry_run_ignores_held_lock(self):
        self.write_budget(20)
        with open(str(self.budget) + ".lock", "w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_sh("--a-secco", "--campagna", "p5", "spec").returncode, 0)       # a secco non prende il lock


    def test_prints_command_and_residual(self):
        self.write_budget(20)
        r = self.run_sh("--campagna", "p5", "spec")
        self.assertIn("residuo del tetto: 60.00", r.stdout)
        self.assertIn("claude plugin eval", r.stdout)
        self.assertRegex(r.stdout, r"costo dell'invocazione 1\.25 USD; residuo 58\.75 USD")

    # ---- campagne e permessi web (decisioni 6 e 7 di B8)

    def test_default_campaign_is_b8(self):
        r = self.run_sh("spec")
        self.assertEqual(r.returncode, 0, r.stderr)
        args = self.calls()[0]["args"]
        self.assertEqual(args[args.index("--max-cost-usd") + 1], "20.00")
        self.assertIn("campagna: b8 (tetto 20 USD)", r.stdout)
        self.assertEqual(cost.DEFAULT_CAMPAIGN, "b8")
        with mock.patch.dict(os.environ, {k: v for k, v in os.environ.items() if k != "TOLLGATE_EVAL_BUDGET"}, clear=True):
            self.assertEqual(cost.budget_path(), cost.budget_path("b8"))
        self.assertEqual(self.run_sh("--campagna", "b8", "spec", "--runs", "1").returncode, 0)     # esplicita = predefinita

    def test_p5_campaign_keeps_80_and_its_registry(self):
        r = self.run_sh("--campagna", "p5", "spec")
        self.assertEqual(r.returncode, 0, r.stderr)
        args = self.calls()[0]["args"]
        self.assertEqual(args[args.index("--max-cost-usd") + 1], "80.00")
        self.assertIn("campagna: p5 (tetto 80 USD)", r.stdout)
        self.assertEqual(cost.CAMPAIGNS["p5"], cost.Campaign("eval-p5", 80.0))
        self.assertEqual(cost.CAMPAIGNS["b8"], cost.Campaign("eval-b8", 20.0))
        with mock.patch.dict(os.environ, {k: v for k, v in os.environ.items() if k != "TOLLGATE_EVAL_BUDGET"}, clear=True):
            self.assertEqual(cost.budget_path("p5"), ROOT / "docs" / "verifiche" / "evidenze" / "eval-p5" / "budget.tsv")
            self.assertEqual(cost.budget_path("b8"), ROOT / "docs" / "verifiche" / "evidenze" / "eval-b8" / "budget.tsv")

    def test_cap_message_names_campaign(self):
        for campaign, cap in (("b8", 20), ("p5", 80)):
            with self.subTest(campaign=campaign):
                self.write_budget(cap)
                r = self.run_sh("--campagna", campaign, "spec")
                self.assertEqual(r.returncode, 1)
                self.assertIn(f"tetto di {cap} USD della campagna {campaign} esaurito", r.stderr)
                self.assertEqual(self.calls(), [])

    def test_b8_grants_web_tools(self):
        self.assertEqual(self.run_sh("spec").returncode, 0)
        args = self.calls()[0]["args"]
        i = args.index("--allow-tools")
        self.assertEqual(args[i + 1:i + 8], ["Bash", "Write", "Edit", "WebFetch(domain:ai.google.dev)",
                                            "WebFetch(domain:aistudio.google.com)", "WebFetch(domain:vercel.com)",
                                            "WebSearch"])
        self.assertEqual(args[i + 8], "--threshold")
        self.log.unlink()
        self.assertEqual(self.run_sh("--campagna", "p5", "spec").returncode, 0)
        args = self.calls()[0]["args"]
        i = args.index("--allow-tools")
        self.assertEqual(args[i + 1:i + 5], ["Bash", "Write", "Edit", "--threshold"])
        self.assertNotIn("WebSearch", args)

    def test_grants_follow_web_domains(self):
        """I permessi sono costruiti da `scrub.WEB_DOMAINS`: `run.sh` non ha un elenco suo."""
        self.assertNotIn("ai.google.dev", RUN_SH.read_text(encoding="utf-8"))
        self.assertNotIn("vercel.com", RUN_SH.read_text(encoding="utf-8"))
        listed = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "scrub.py"), "domains"], capture_output=True,
                                text=True, check=True).stdout.split("\n")
        self.assertEqual(listed, [*scrub.WEB_DOMAINS, ""])
        self.assertEqual(self.run_sh("spec").returncode, 0)
        args = self.calls()[0]["args"]
        i = args.index("--allow-tools")
        self.assertEqual(args[i + 4:i + 4 + len(scrub.WEB_DOMAINS)], [f"WebFetch(domain:{d})" for d in scrub.WEB_DOMAINS])

    def test_campaign_folder_follows_cost_info(self):
        """Cartella e tetto della campagna vengono da `cost.py info`: `run.sh` non li ripete."""
        text = RUN_SH.read_text(encoding="utf-8")
        for campaign in cost.CAMPAIGNS.values():
            self.assertNotIn(campaign.folder, text)
        for name, campaign in cost.CAMPAIGNS.items():
            with self.subTest(campaign=name):
                info = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "cost.py"), "info", "--campagna", name],
                                      capture_output=True, text=True, check=True).stdout.split("\n")
                self.assertEqual(info, [campaign.folder, f"{campaign.total_usd:g}", ""])
                r = self.run_sh("--a-secco", "--campagna", name, "spec")
                self.assertIn(f"(tetto {campaign.total_usd:g} USD)", r.stdout)

    def test_unknown_campaign_rejected(self):
        for bad in (["--campagna", "p6"], ["--campagna=zzz"], ["--campagna", ""]):
            with self.subTest(bad=bad):
                r = self.run_sh(*bad, "spec")
                self.assertEqual(r.returncode, 64, r.stderr)
                self.assertEqual(self.calls(), [])
        r = self.run_sh("spec", "--campagna")
        self.assertEqual(r.returncode, 64)
        self.assertFalse(self.budget.exists())                    # niente prenotazione
        self.assertEqual(self.out_dirs(), [])

    # ---- pulizia delle evidenze (decisioni 9 e 10 di B8)

    def test_run_strips_web_results_from_traces(self):
        self.assertEqual(self.run_sh("spec", "--runs", "1", FAKE_WEB_TRACE="1").returncode, 0)
        out, = self.out_dirs()
        traces = sorted(out.glob("runs/*/trace.jsonl"))
        self.assertEqual(len(traces), 2)
        for trace in traces:
            with self.subTest(trace=trace.parent.name):
                self.assertEqual(scrub.flowreg.third_party_blocks(trace), [])
        text = "".join(p.read_text(errors="replace") for p in out.rglob("*") if p.is_file() and p.name == "trace.jsonl")
        for page in ("PAGINA-DI-TERZI", "FRAMMENTO-DI-TERZI", SHELL_PAGE):
            self.assertNotIn(page, text)
        self.assertIn("https://ai.google.dev/gemini-api/docs/models", text)       # l'indirizzo resta nel segnaposto
        self.assertIn("modelli gemini", text)
        self.assertIn("risultato di Bash verso vercel.com", text)

    def test_a_trace_with_a_string_message_row_is_cleaned_and_exits_0(self):
        """Una riga `system/permission_denied` (`message` stringa) non ferma la pulizia: uscita 0, non 5."""
        r = self.run_sh("spec", "--runs", "1", FAKE_WEB_TRACE="1", FAKE_DENIED_ROW="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        out, = self.out_dirs()
        for trace in out.glob("runs/*/trace.jsonl"):
            with self.subTest(trace=trace.parent.name):
                self.assertEqual(scrub.flowreg.third_party_blocks(trace), [])
                rows = [json.loads(x) for x in trace.read_text().splitlines()]
                self.assertTrue(any(x.get("subtype") == "permission_denied" for x in rows))
        text = "".join(p.read_text(errors="replace") for p in out.rglob("trace.jsonl"))
        self.assertNotIn("PAGINA-DI-TERZI", text)

    def test_strip_failure_exits_5(self):
        real = sys.executable
        wrapper = self.bin / "python3"
        wrapper.write_text(f'#!/bin/sh\ncase "$*" in *strip-web*) exit 1 ;; esac\nexec "{real}" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
        self.write_budget(10)
        r = self.run_sh("spec", "--runs", "1", FAKE_WEB_TRACE="1")
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn("evidenze non ripulite: non committare", r.stderr)
        self.assertEqual(self.rows()[-1][2], "1.25")                 # il costo è già registrato

    def test_anonymizer_failure_exits_5(self):
        for user, host in (("abc", FAKE_HOST), (FAKE_USER, "root")):
            with self.subTest(user=user, host=host):
                r = self.run_sh("spec", "--runs", "1", TOLLGATE_EVAL_FAKE_USER=user, TOLLGATE_EVAL_FAKE_HOST=host)
                self.assertEqual(r.returncode, 5, r.stderr)
                self.assertIn("evidenze non ripulite", r.stderr)

    def test_run_anonymizes_copied_runs(self):
        r = self.run_sh("spec", "--runs", "1", FAKE_LEAK="1", FAKE_LEAK_STDOUT="1", FAKE_STATE_DB="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        out, = self.out_dirs()
        for value in (FAKE_USER, FAKE_HOST):
            found = [p for p in out.rglob("*") if p.is_file() and value.encode() in p.read_bytes()]
            self.assertEqual(found, [], f"un valore da anonimizzare è rimasto in {[p.name for p in found]}")
            self.assertNotIn(value, r.stdout + r.stderr)
        w = next(out.glob("runs/claude-eval-W0*"))
        self.assertIn("/home/USER/.cache", (w / "settings.json").read_text())
        self.assertIn("/home/USER/.cache sulla macchina HOST", (w / "trace.jsonl").read_text())
        self.assertIn("/home/USER", (out / "stdout.txt").read_text())
        state = w / "home" / ".local" / "state" / "tollgate"
        self.assertEqual(sorted(p.name for p in state.iterdir()), ["stato.txt", "tollgate.db"])      # niente -wal né -shm
        with closing(sqlite3.connect(f"{(state / 'tollgate.db').as_uri()}?mode=ro", uri=True)) as conn:
            self.assertEqual({r[0] for r in conn.execute("SELECT host FROM events")}, {"HOST"})
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_run_anonymizes_on_unknown_cost(self):
        r = self.run_sh("spec", FAKE_NO_RESULT="1", FAKE_RC="2", FAKE_LEAK_STDOUT="1")
        self.assertEqual(r.returncode, 3)
        out, = self.out_dirs()
        text = (out / "stdout.txt").read_text()
        self.assertIn("/home/USER", text)
        self.assertNotIn(FAKE_USER, text)
        self.assertNotIn(FAKE_HOST, text)
        self.assertEqual(self.rows()[-1][2], "?")
        self.budget.unlink()
        r = self.run_sh("spec", FAKE_NO_RESULT="1", FAKE_RC="2", TOLLGATE_EVAL_FAKE_USER="abc")
        self.assertEqual(r.returncode, 5, r.stderr)                      # anche qui, se la pulizia fallisce, 5
        self.assertIn("evidenze non ripulite", r.stderr)
        self.assertEqual(self.rows()[-1][2], "?")

    def test_run_writes_research_counts(self):
        self.assertEqual(self.run_sh("spec", "--runs", "1", FAKE_STATE_DB="1").returncode, 0)
        out, = self.out_dirs()
        nota = (out / "nota.md").read_text()
        row = next(line for line in nota.splitlines() if "claude-eval-W0" in line)
        self.assertEqual([c.strip() for c in row.strip("|").split("|")[1:]],
                         ["1", "1", "1", "0", "1", "0", "0", "0", "1", "0", "0"])
        self.assertIn("claude-eval-O0", nota.split("saltate")[1])            # il braccio senza plugin non ha lo stato


class DryRunRealRegistryTest(unittest.TestCase):
    """`--a-secco` come lo lancia il controller: senza TEST_MODE e senza variabili TOLLGATE_EVAL_*, sul registro vero
    (letto soltanto). La HOME temporanea sta nella radice del repo e non sotto /tmp, perché il TMPDIR dell'eval, per
    regola, non può stare sotto /tmp; il bersaglio è costruito in /tmp/tollgate-eval-target come nella corsa vera."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix=".tollgate-test-home-", dir=ROOT))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.assertFalse(str(self.home.resolve()).startswith(("/tmp", "/var/tmp", "/dev/shm")))
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.marker = self.home / "claude-lanciato"
        fake = self.bin / "claude"
        fake.write_text(f"#!/bin/sh\ntouch '{self.marker}'\nexit 99\n")
        fake.chmod(0o755)
        self.real = ROOT / "docs" / "verifiche" / "evidenze" / "eval-b8"       # la campagna predefinita
        self.budget = self.real / "budget.tsv"
        self.p5 = ROOT / "docs" / "verifiche" / "evidenze" / "eval-p5"

    def snapshot(self):
        return (self.budget.read_bytes(), sorted(p.name for p in self.real.iterdir()))

    def lock_held(self, budget):
        """Il lock del registro è tenuto da un'altra invocazione? Tentativo non bloccante su un fd in sola lettura;
        se il file manca nessun lock è tenuto (e non lo si crea)."""
        try:
            fd = os.open(str(budget) + ".lock", os.O_RDONLY)
        except FileNotFoundError:
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        finally:
            os.close(fd)
        return False

    def test_dry_run_reads_real_registry(self):
        if self.lock_held(self.budget):
            self.skipTest("una corsa vera tiene il lock del registro: il test ricostruirebbe il suo bersaglio")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("TOLLGATE_", "CLAUDE"))}
        env.update(HOME=str(self.home), TMPDIR=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                   PATH=f"{self.bin}:{os.environ['PATH']}")
        cost_py = [sys.executable, "-B", str(ROOT / "evals" / "cost.py"), "remaining"]
        probe = subprocess.run(cost_py, capture_output=True, text=True, env=env)
        remaining = probe.stdout.strip()
        exhausted = probe.returncode != 0 or not remaining or float(remaining) < 0.01   # anche una riga «?» chiude il tetto
        before = self.snapshot()
        r = subprocess.run(["bash", str(RUN_SH), "--a-secco", "spec"], capture_output=True, text=True, env=env,
                           timeout=300, stdin=subprocess.DEVNULL)
        self.assertFalse(self.marker.exists(), "claude è stato lanciato")
        self.assertEqual(self.snapshot(), before)               # registro uguale byte per byte, nessuna cartella né lock nuovi
        if exhausted:
            self.assertEqual(r.returncode, 1, r.stderr + r.stdout)
            return
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertRegex(remaining, r"^\d+\.\d\d$")
        self.assertIn(f"residuo del tetto: {remaining} USD", r.stdout)
        self.assertNotIn("TEST_MODE", r.stdout)
        self.assertIn(f"registro dei costi: {self.budget}", r.stdout)
        cmd = next(line for line in r.stdout.splitlines() if line.startswith("comando: "))
        for flag in ("--no-publish", "--allow-tools Bash Write Edit", "WebSearch", f"--max-cost-usd {remaining} "):
            self.assertIn(flag, cmd)
        self.assertIn("/tmp/tollgate-eval-target", cmd)

    def test_p5_registry_untouched_by_b8(self):
        """Né la corsa a secco di `b8` né quella di `p5` toccano il registro di P5 (uguale byte per byte), e nemmeno la sua cartella."""
        p5_budget = self.p5 / "budget.tsv"
        if self.lock_held(self.budget) or self.lock_held(p5_budget):
            self.skipTest("una corsa vera tiene il lock: il test ricostruirebbe il suo bersaglio")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("TOLLGATE_", "CLAUDE"))}
        env.update(HOME=str(self.home), TMPDIR=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                   PATH=f"{self.bin}:{os.environ['PATH']}")
        before = (p5_budget.read_bytes(), sorted(p.name for p in self.p5.iterdir()))
        b8_before = self.budget.read_bytes()      # con le corse vere di B8 ha anche le loro righe: conta che non cambi
        for args in (["--a-secco", "spec"], ["--a-secco", "--campagna", "b8", "extra"], ["--a-secco", "--campagna", "p5", "spec"]):
            with self.subTest(args=args):
                r = subprocess.run(["bash", str(RUN_SH), *args], capture_output=True, text=True, env=env, timeout=300,
                                   stdin=subprocess.DEVNULL)
                self.assertFalse(self.marker.exists(), "claude è stato lanciato")
                self.assertIn(f"registro dei costi: {p5_budget if 'p5' in args else self.budget}", r.stdout)
                self.assertEqual((p5_budget.read_bytes(), sorted(p.name for p in self.p5.iterdir())), before)
        self.assertEqual(self.budget.read_bytes(), b8_before)         # il registro di B8 resta com'era

    def test_held_lock_gives_skip_not_error(self):
        with mock.patch.object(self, "lock_held", return_value=True):
            with self.assertRaises(unittest.SkipTest):
                self.test_dry_run_reads_real_registry()
        self.assertFalse(self.marker.exists())

    def test_lock_held_detection(self):
        budget = self.home / "b.tsv"
        self.assertFalse(self.lock_held(budget))
        self.assertFalse(Path(str(budget) + ".lock").exists())           # non lo crea
        with open(str(budget) + ".lock", "w") as fh:
            self.assertFalse(self.lock_held(budget))                     # file presente ma libero
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertTrue(self.lock_held(budget))


class CostTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-test-cost-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.budget = self.tmp / "budget.tsv"
        patcher = mock.patch.dict(os.environ, TOLLGATE_EVAL_BUDGET=str(self.budget), TOLLGATE_EVAL_TEST_MODE="1")
        patcher.start()
        self.addCleanup(patcher.stop)

    def result(self, data, name="result.json"):
        p = self.tmp / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_remaining(self):
        self.assertEqual(cost.remaining(campaign="p5"), 80.0)               # nessun registro
        self.budget.write_text(HEADER + "a\tb\t12.5\t3\tc\n\na\tb\t0.25\t3\tc\n", encoding="utf-8")
        self.assertAlmostEqual(cost.remaining(campaign="p5"), 67.25)
        self.budget.write_text(HEADER + "a\tb\t90\t3\tc\n", encoding="utf-8")
        self.assertEqual(cost.remaining(campaign="p5"), 0.0)

    def test_remaining_fail_closed(self):
        for bad in ("a\tb\t?\t?\tc\n", "a\tb\tnan\t1\tc\n", "a\tb\n", "a\tb\t-3\t1\tc\n"):
            with self.subTest(bad=bad):
                self.budget.write_text(HEADER + bad, encoding="utf-8")
                self.assertEqual(cost.remaining(), 0.0)
        self.budget.write_text("intestazione\tsbagliata\n", encoding="utf-8")
        self.assertEqual(cost.remaining(), 0.0)

    def test_remaining_cli_rounds_down_to_cents(self):
        self.budget.write_text(HEADER + "a\tb\t0.1234\t3\tc\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "cost.py"), "remaining", "--campagna", "p5"], capture_output=True,
                           text=True, env={**os.environ, "TOLLGATE_EVAL_BUDGET": str(self.budget), "TOLLGATE_EVAL_TEST_MODE": "1"})
        self.assertEqual(r.stdout.strip(), "79.87")

    def test_campaigns_and_default(self):
        self.assertEqual(cost.remaining(), 20.0)                       # nessun registro: tetto di b8
        self.assertEqual(cost.remaining(campaign="p5"), 80.0)
        self.assertEqual(cost.remaining(self.budget), 20.0)            # con `path` il tetto resta quello della campagna
        self.budget.write_text(HEADER + "a\tb\t12.5\t3\tc\n", encoding="utf-8")
        self.assertEqual(cost.remaining(self.budget), 7.5)
        self.assertEqual(cost.remaining(self.budget, "p5"), 67.5)
        self.assertEqual(cost.spent(), 12.5)
        with self.assertRaises(ValueError):
            cost.remaining(campaign="p6")

    def test_cli_campaign_option(self):
        def cli(*args):
            return subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "cost.py"), *args], capture_output=True, text=True,
                                  env={**os.environ, "TOLLGATE_EVAL_BUDGET": str(self.budget), "TOLLGATE_EVAL_TEST_MODE": "1"})
        self.assertEqual(cli("remaining").stdout.strip(), "20.00")
        self.assertEqual(cli("remaining", "--campagna", "p5").stdout.strip(), "80.00")
        self.assertEqual(cli("info").stdout.split(), ["eval-b8", "20"])
        self.assertEqual(cli("info", "--campagna", "p5").stdout.split(), ["eval-p5", "80"])
        for args in (("remaining", "--campagna", "x"), ("info", "--campagna", "x"), ("reserve", "--label", "a", "--campagna", "x")):
            with self.subTest(args=args):
                self.assertEqual(cli(*args).returncode, 64)
        self.assertFalse(self.budget.exists())
        self.assertEqual(cli("remaining", "--campagna").returncode, 2)
        reserved = cli("reserve", "--label", "prova", "--campagna", "p5")
        self.assertEqual(reserved.returncode, 0)
        self.assertEqual(cli("remaining", "--campagna", "p5").stdout.strip(), "0.00")
        res = self.result(make_result([case_entry("s1", [1.0], None)], cost_usd=2.5, duration=9))
        self.assertEqual(cli("add", str(res), "--label", "prova", "--reserved", reserved.stdout.strip(), "--campagna", "p5").returncode, 0)
        self.assertEqual(cli("remaining", "--campagna", "p5").stdout.strip(), "77.50")
        self.assertEqual(cli("remaining").stdout.strip(), "17.50")

    def test_add_row(self):
        res = self.result(make_result([case_entry("s1", [1.0], [0.5])], cost_usd=0.25, duration=17))
        self.assertTrue(cost.add(res, "spec (with-without)"))
        lines = self.budget.read_text().splitlines()
        self.assertEqual(lines[0] + "\n", HEADER)
        cols = lines[1].split("\t")
        self.assertEqual(len(cols), 5)
        self.assertRegex(cols[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(cols[1:], ["spec (with-without)", "0.25", "17", "s1"])
        self.assertTrue(cost.add(res, "x"))
        self.assertAlmostEqual(cost.spent(), 0.5)

    def test_add_unknown_cost_writes_question_mark(self):
        for res in (self.tmp / "manca.json", self.result({"cases": []}, "senza-costo.json")):
            self.assertFalse(cost.add(res, "x"))
        self.assertEqual([r.split("\t")[2] for r in self.budget.read_text().splitlines()[1:]], ["?", "?"])
        self.assertEqual(cost.remaining(), 0.0)

    def test_add_refuses_foreign_header(self):
        self.budget.write_text("altro\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            cost.add(self.result(make_result([])), "x")

    def test_cost_table(self):
        res = self.result(make_result([case_entry("s1-done", [1.0, 0.5, 1.0], [0.0, 0.5, 0.0]),
                                       case_entry("e1-audit", [0.75], None)]))
        out = cost.table([res])
        rows = out.splitlines()
        self.assertEqual(rows[0].count("|"), 9)
        self.assertIn("Con plugin", rows[0]); self.assertIn("Senza plugin", rows[0]); self.assertIn("Δ", rows[0])
        s1 = next(r for r in rows if "s1-done" in r)
        self.assertRegex(s1, r"\| s1-done \| 0\.83 \| 0\.17 \| \+0\.67 \| 3/3 \| 0\.6000 \| 42 \| — \|")
        e1 = next(r for r in rows if "e1-audit" in r)
        self.assertRegex(e1, r"\| e1-audit \| 0\.75 \| — \| — \| 1/1 \| 0\.1000 \| 7 \| — \|")

    def test_cost_table_tokens_from_copied_traces(self):
        res = self.result(make_result([case_entry("s1", [1.0], None, trace_root="/home/x/claude-eval-")]))
        trace = self.tmp / "runs" / "claude-eval-W0" / "trace.jsonl"
        trace.parent.mkdir(parents=True)
        trace.write_text(json.dumps({"type": "system", "subtype": "init"}) + "\n" + json.dumps(
            {"type": "result", "usage": {"input_tokens": 10, "output_tokens": 838, "cache_read_input_tokens": 85625,
                                         "cache_creation_input_tokens": 12393}}) + "\n", encoding="utf-8")
        row = next(r for r in cost.table([res]).splitlines() if r.startswith("| s1 "))
        self.assertIn("in 10 / out 838 / cache lett. 85625 / cache scr. 12393", row)

    def test_cost_table_from_real_probe_result(self):
        real = ROOT / "docs" / "verifiche" / "evidenze" / "eval-p5" / "20261023T201225Z-sonda-nl-bash" / "result.json"
        if not real.is_file():
            self.skipTest("evidenza del Task 1 assente")
        row = next(r for r in cost.table([real]).splitlines() if r.startswith("| nl-bash "))
        self.assertRegex(row, r"\| nl-bash \| 0\.92 \| 0\.42 \| \+0\.50 \| 1/1 \| 0\.1321 \| 32 \|")

    def test_reserve_then_add_replaces_row_atomically(self):
        when = cost.reserve("spec (with-without)", campaign="p5")
        self.assertEqual(cost.remaining(campaign="p5"), 0.0)                      # prenotata = tetto chiuso
        res = self.result(make_result([case_entry("s1", [1.0], None)], cost_usd=2.5, duration=9))
        self.assertTrue(cost.add(res, "spec (with-without)", reserved=when, campaign="p5"))
        lines = self.budget.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1].split("\t")[2:], ["2.5", "9", "s1"])
        self.assertAlmostEqual(cost.remaining(campaign="p5"), 77.5)
        self.assertEqual([p.name for p in self.tmp.iterdir() if p.name.endswith(".tmp")], [])

    def test_add_unknown_keeps_reserved_question_mark(self):
        when = cost.reserve("x")
        self.assertFalse(cost.add(self.tmp / "manca.json", "x", reserved=when))
        self.assertEqual([r.split("\t")[2] for r in self.budget.read_text().splitlines()[1:]], ["?"])
        self.assertEqual(cost.remaining(), 0.0)

    def test_recorded_cost_is_max_of_total_and_sum_of_runs(self):
        entry = case_entry("s1", [1.0, 1.0], [0.0])              # 3 corse da 0.1
        entry["arms"]["with"][0]["judgeCostUsd"] = 2.0           # giudice non incluso nel totale
        res = self.result(make_result([entry], cost_usd=0.2))
        self.assertTrue(cost.add(res, "a"))
        self.assertAlmostEqual(float(self.budget.read_text().splitlines()[1].split("\t")[2]), 2.3)
        res = self.result(make_result([case_entry("s1", [1.0], None)], cost_usd=5.0), "b.json")
        self.assertTrue(cost.add(res, "b"))
        self.assertEqual(float(self.budget.read_text().splitlines()[2].split("\t")[2]), 5.0)

    def test_plugin_check_without_traces_fails(self):
        entry = case_entry("s1", [0.0], None)
        entry["arms"]["with"][0].update(tracePath=None, error="timeout")
        res = self.result(make_result([entry]))
        self.assertIn("nessuna corsa", cost.plugin_check(res)[0])

    def test_budget_env_ignored_outside_test_mode(self):
        with mock.patch.dict(os.environ, {"TOLLGATE_EVAL_TEST_MODE": ""}):
            with self.assertRaises(SystemExit) as ctx, mock.patch("sys.stderr", new=io.StringIO()):
                cost.budget_path()
        self.assertEqual(ctx.exception.code, 64)

    def test_plugin_check(self):
        res = self.tmp / "result.json"
        res.write_text(json.dumps(make_result([case_entry("s1", [1.0], [0.0], trace_root="/home/x/claude-eval-")])))
        self.assertTrue(cost.plugin_check(res))                       # nessuna trace copiata: non verificato
        def trace(name, plugins):
            p = self.tmp / "runs" / name / "trace.jsonl"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"type": "system", "subtype": "init", "plugins": plugins}) + "\n")
        trace("claude-eval-W0", [{"name": "tollgate"}])
        trace("claude-eval-O0", [{"name": "cc-plugin-agents-md"}])
        self.assertEqual(cost.plugin_check(res), [])
        trace("claude-eval-W0", [{"name": "altro"}])
        self.assertIn("non caricato", cost.plugin_check(res)[0])
        trace("claude-eval-W0", [{"name": "tollgate"}])
        trace("claude-eval-O0", [{"name": "tollgate"}])
        self.assertIn("braccio senza plugin", cost.plugin_check(res)[0])


# ---------------------------------------------------------------- pulizia delle evidenze: evals/scrub.py

def jsonl(path: Path, *rows) -> Path:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path


def use(uid, name, tool_input, parent=None):
    return {"type": "assistant", "parent_tool_use_id": parent,
            "message": {"role": "assistant", "content": [{"type": "tool_use", "id": uid, "name": name, "input": tool_input}]}}


def result(uid, text, tool_use_result=None, parent=None):
    row = {"type": "user", "parent_tool_use_id": parent,
           "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": uid, "content": text}]}}
    if tool_use_result is not None:
        row["tool_use_result"] = tool_use_result
    return row


class ScrubBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-test-scrub-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def rows(self, path):
        return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


class StripWebResultsTest(ScrubBase):
    def test_every_web_result_goes_whatever_its_length(self):
        page = "X" * 1000
        trace = jsonl(self.tmp / "trace.jsonl",
                      use("w1", "WebFetch", {"url": "https://ai.google.dev/x", "prompt": "p"}),
                      result("w1", page, {"bytes": 1000, "code": 200, "codeText": "OK", "result": page, "durationMs": 7,
                                          "url": "https://ai.google.dev/x", "ok": True, "extra": None}),
                      use("w2", "WebSearch", {"query": "modelli"}),
                      result("w2", "RIASSUNTO-DI-TERZI", {"query": "modelli", "durationSeconds": 1.5,
                                                          "results": [{"tool_use_id": "s1", "content": [{"title": "TITOLO-DI-TERZI", "url": "https://t.example"}]},
                                                                      "FRAMMENTO-DI-TERZI"]}),
                      use("b1", "Bash", {"command": "ls"}), result("b1", "RESTA-QUI", {"stdout": "RESTA-QUI"}))
        self.assertEqual(scrub.strip_web_results(trace), 2)
        raw = trace.read_text(encoding="utf-8")
        for gone in (page, "RIASSUNTO-DI-TERZI", "TITOLO-DI-TERZI", "FRAMMENTO-DI-TERZI"):
            self.assertNotIn(gone, raw)
        fetch, search, bash_row = self.rows(trace)[1], self.rows(trace)[3], self.rows(trace)[5]
        self.assertEqual(fetch["message"]["content"][0]["content"], f"{scrub.flowreg.PAGE_PLACEHOLDER} https://ai.google.dev/x, 1000 caratteri]")
        res = fetch["tool_use_result"]
        self.assertEqual((res["bytes"], res["code"], res["durationMs"], res["ok"], res["extra"]), (1000, 200, 7, True, None))
        self.assertTrue(res["result"].startswith(scrub.flowreg.PAGE_PLACEHOLDER))
        self.assertTrue(res["url"].startswith(scrub.flowreg.PAGE_PLACEHOLDER))
        self.assertEqual(search["tool_use_result"]["durationSeconds"], 1.5)
        self.assertTrue(search["tool_use_result"]["results"][1].startswith(scrub.flowreg.PAGE_PLACEHOLDER))
        self.assertIn("modelli", search["message"]["content"][0]["content"])               # l'interrogazione resta nel segnaposto
        self.assertEqual(bash_row["tool_use_result"], {"stdout": "RESTA-QUI"})              # un Bash qualunque non si tocca
        self.assertEqual(scrub.flowreg.third_party_blocks(trace), [])
        self.assertEqual(scrub.strip_web_results(trace), 0)                                # si può rilanciare
        self.assertEqual(trace.read_text(encoding="utf-8"), raw)

    def test_subagent_results_and_error_results(self):
        trace = jsonl(self.tmp / "trace.jsonl", use("w1", "WebFetch", {"url": "https://vercel.com/a"}, parent="p1"),
                      result("w1", "ERRORE-DI-TERZI lungo", None, parent="p1"))
        self.assertEqual(scrub.strip_web_results(trace), 1)
        self.assertNotIn("ERRORE-DI-TERZI", trace.read_text(encoding="utf-8"))

    def test_committed_p5_traces_stay_the_same(self):
        traces = sorted((ROOT / "docs" / "verifiche" / "evidenze" / "eval-p5").glob("*/runs/*/trace.jsonl"))
        if not traces:
            self.skipTest("nessuna trace di P5")
        for source in traces[::10] + traces[-1:]:
            copy = self.tmp / "copia.jsonl"
            shutil.copyfile(source, copy)
            with self.subTest(source=source.parent.name):
                self.assertEqual(scrub.strip_web_results(copy), 0)
                self.assertEqual(scrub.strip_bash_web(copy, scrub.WEB_DOMAINS), 0)
                self.assertEqual(copy.read_bytes(), source.read_bytes())
                self.assertEqual(scrub.flowreg.third_party_blocks(copy), [])


class StringMessageRowTest(ScrubBase):
    """Una riga con `message` di tipo stringa (`system/permission_denied`, forma vista dal vivo) resta com'è."""
    DENIED = {"type": "system", "subtype": "permission_denied", "tool_name": "WebFetch", "tool_use_id": "toolu_X",
              "agent_id": "a1", "decision_reason_type": "mode", "message": "Permission to use WebFetch has been denied.",
              "uuid": "u1", "session_id": "s1"}

    def trace(self):
        return jsonl(self.tmp / "trace.jsonl", self.DENIED,
                     use("w1", "WebFetch", {"url": "https://vercel.com/x"}), result("w1", "PAGINA-LUNGA " * 600, None),
                     use("b1", "Bash", {"command": "curl -s https://vercel.com/docs"}),
                     result("b1", "CORPO-LETTO " * 50, {"stdout": "CORPO-LETTO " * 50, "stderr": "", "interrupted": False}))

    def test_strip_web_and_strip_bash_leave_the_row_alone(self):
        trace = self.trace()
        for cmd, gone in (("strip-web", "PAGINA-LUNGA"), ("strip-bash", "CORPO-LETTO")):
            with self.subTest(cmd=cmd):
                r = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "scrub.py"), cmd, str(trace)],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn(gone, trace.read_text(encoding="utf-8"))
                self.assertEqual(self.rows(trace)[0], self.DENIED)

    def test_anonymize_leaves_the_row_alone(self):
        out = self.tmp / "out"
        run = out / "runs" / "claude-eval-W0aaaa"
        run.mkdir(parents=True)
        jsonl(run / "trace.jsonl", self.DENIED)
        scrub.anonymize(out, "utente-prova", "macchina-prova")
        self.assertEqual(self.rows(run / "trace.jsonl"), [self.DENIED])


class StripBashWebTest(ScrubBase):
    def test_strip_bash_web(self):
        note = "python3 /x/bin/tollgate research submit 1 <<'NOTA'\n## Fonti\n- https://vercel.com/docs/project-configuration\nNOTA"
        commands = {"curl": "curl -s https://vercel.com/docs/project-configuration | head -n 50",
                    "ls": "ls -la",
                    "nota": note,
                    "sed": "sed -i 's#FONTE#https://vercel.com/docs/project-configuration#' nota.md",
                    "illeggibile": "curl 'https://ai.google.dev/gemini-api/docs/models",
                    "altro-dominio": "curl -s https://example.org/pagina",
                    "python": "python3 -c \"import urllib.request as u; print(u.urlopen('https://ai.google.dev/x').read())\"",
                    "heredoc": "python3 - <<'EOF'\nimport urllib.request\nprint(urllib.request.urlopen('https://vercel.com/docs').read())\nEOF",
                    "herestring": "python3 <<< \"import urllib.request as u; u.urlopen('https://vercel.com/docs')\"",
                    "xargs": "echo https://vercel.com/docs | xargs curl -s",
                    "perl": "perl -e 'print `curl -s ai.google.dev`'",
                    "dominio-simile": "curl -s https://notvercel.com/pagina"}
        rows = []
        for name, command in commands.items():
            rows += [use(name, "Bash", {"command": command}), result(name, "RISULTATO-" + name + " " + "R" * 3000,
                                                                       {"stdout": "RISULTATO-" + name + " " + "R" * 3000, "stderr": "", "interrupted": False})]
        trace = jsonl(self.tmp / "trace.jsonl", *rows)
        self.assertEqual(scrub.strip_bash_web(trace, scrub.WEB_DOMAINS), 7)
        raw = trace.read_text(encoding="utf-8")
        for name in ("curl", "illeggibile", "python", "heredoc", "herestring", "xargs", "perl"):
            self.assertNotIn("RISULTATO-" + name, raw)
        for name in ("ls", "nota", "sed", "altro-dominio", "dominio-simile"):
            self.assertIn("RISULTATO-" + name, raw)
        curl = self.rows(trace)[1]
        self.assertTrue(curl["message"]["content"][0]["content"].startswith(scrub.flowreg.PAGE_PLACEHOLDER))
        self.assertEqual(curl["tool_use_result"]["stdout"], curl["message"]["content"][0]["content"])
        self.assertEqual(curl["tool_use_result"]["interrupted"], False)
        self.assertEqual(scrub.strip_bash_web(trace, scrub.WEB_DOMAINS), 0)               # si può rilanciare
        self.assertEqual(scrub.strip_bash_web(trace, ()), 0)                              # senza domini concessi: niente

    def test_note_delivery_is_exempt_only_after_the_tollgate_program(self):
        exempt = {"python": "python3 /x/bin/tollgate research submit 1 <<'NOTA'\nhttps://vercel.com/docs\nNOTA",
                  "diretto": "/x/bin/tollgate research submit 2 <<'NOTA'\nhttps://vercel.com/docs\nNOTA"}
        replaced = {"curl": "curl -s https://vercel.com/docs research submit",
                    "lontane": "python3 /x/bin/tollgate research show 1 submit https://vercel.com/docs",
                    "altro-programma": "python3 /x/altro.py research submit 1 https://vercel.com/docs"}
        rows = []
        for name, command in {**exempt, **replaced}.items():
            rows += [use(name, "Bash", {"command": command}),
                     result(name, "RISULTATO-" + name + " " + "R" * 3000,
                            {"stdout": "RISULTATO-" + name + " " + "R" * 3000, "stderr": "", "interrupted": False})]
        trace = jsonl(self.tmp / "trace.jsonl", *rows)
        self.assertEqual(scrub.strip_bash_web(trace, scrub.WEB_DOMAINS), len(replaced))
        raw = trace.read_text(encoding="utf-8")
        for name in exempt:
            self.assertIn("RISULTATO-" + name, raw)
        for name in replaced:
            self.assertNotIn("RISULTATO-" + name, raw)


class AnonymizeTest(ScrubBase):
    USER, HOST = "utente-prova", "macchina-prova"

    def make_db(self, path, keep_open=False):
        conn = sqlite3.connect(path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, host TEXT, data TEXT, n INTEGER, raw BLOB)")
        conn.execute("INSERT INTO events (host, data, n, raw) VALUES (?, ?, 7, ?)",
                     (self.HOST, f'{{"cwd": "/home/{self.USER}/proj", "altro": "{self.HOST}-2"}}', b"\x00\xffblob"))
        conn.execute("INSERT INTO events (host, data, n) VALUES ('altro', 'niente', 8)")
        return conn

    def snapshot(self, root):
        return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

    def test_anonymize_text_and_db(self):
        out = self.tmp / "out"
        (out / "runs" / "c").mkdir(parents=True)
        (out / "a.txt").write_text(f"in /home/{self.USER}/.cache sulla macchina {self.HOST} e su {self.HOST}-2, /home/{self.USER}x\n")
        (out / "runs" / "c" / "t.jsonl").write_text(json.dumps({"cwd": f"/home/{self.USER}/p", "h": self.HOST}) + "\n")
        (out / "senza.txt").write_text("niente da togliere\n")
        (out / "binario.bin").write_bytes(b"\xff\xfe" + f"/home/{self.USER}".encode())
        (out / "link.txt").symlink_to(out / "senza.txt")
        live = self.make_db(self.tmp / "live.db")             # connessione aperta: i dati sono ancora nel -wal
        for suffix in ("", "-wal", "-shm"):
            shutil.copyfile(self.tmp / f"live.db{suffix}", out / "runs" / "c" / f"tollgate.db{suffix}")
        live.close()
        self.assertTrue((out / "runs" / "c" / "tollgate.db-wal").exists())
        changed = scrub.anonymize(out, self.USER, self.HOST)
        self.assertEqual(changed, 3)                           # il database e i due file di testo
        self.assertEqual((out / "a.txt").read_text(), f"in /home/USER/.cache sulla macchina HOST e su HOST-2, /home/{self.USER}x\n")
        self.assertEqual((out / "senza.txt").read_text(), "niente da togliere\n")
        self.assertTrue((out / "binario.bin").read_bytes().endswith(self.USER.encode()))     # non è testo: resta com'è
        self.assertEqual(sorted(p.name for p in (out / "runs" / "c").iterdir()), ["t.jsonl", "tollgate.db"])    # -wal e -shm spariti
        db = out / "runs" / "c" / "tollgate.db"
        with closing(sqlite3.connect(f"{db.as_uri()}?mode=ro&immutable=1", uri=True)) as conn:
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            rows = conn.execute("SELECT host, data, n, raw FROM events ORDER BY seq").fetchall()
        self.assertEqual(rows[0][0], "HOST")
        self.assertEqual(json.loads(rows[0][1]), {"cwd": "/home/USER/proj", "altro": "HOST-2"})
        self.assertEqual((rows[0][2], rows[1]), (7, ("altro", "niente", 8, None)))
        self.assertEqual(rows[0][3], b"\x00\xffblob")                           # un BLOB non è testo: non si tocca
        data = db.read_bytes()
        for value in (self.USER, self.HOST):
            self.assertTrue(value.encode() not in data, "un valore è rimasto nel file (pagine libere comprese)")   # VACUUM
        self.assertEqual(scrub.anonymize(out, self.USER, self.HOST), 0)          # si può rilanciare

    def test_anonymize_project_folder_names_with_dashes(self):
        """Claude Code scrive i percorsi come nomi di cartella con i trattini (`-home-<utente>--cache-…`)."""
        out = self.tmp / "out"
        out.mkdir()
        old = f"/x/projects/-home-{self.USER}--cache-a"
        new = "/x/projects/-home-USER--cache-a"
        (out / "t.jsonl").write_text(json.dumps({"p": old}) + f"\n/tmp/claude-1000/-home-{self.USER}--cache-b\n")
        (out / "altro.txt").write_text(f"-home-{self.USER}x e -home-{self.USER}\n")
        conn = sqlite3.connect(out / "s.db", isolation_level=None)
        conn.execute("CREATE TABLE e (data TEXT)")
        conn.execute("INSERT INTO e VALUES (?)", (old,))
        conn.close()
        self.assertEqual(scrub.anonymize(out, self.USER, self.HOST), 3)
        self.assertEqual(json.loads((out / "t.jsonl").read_text().splitlines()[0]), {"p": new})
        self.assertEqual((out / "t.jsonl").read_text().splitlines()[1], "/tmp/claude-1000/-home-USER--cache-b")
        self.assertEqual((out / "altro.txt").read_text(), f"-home-{self.USER}x e -home-USER\n",
                         "senza il trattino finale la forma delle cartelle non c'è; resta la parola intera")
        with closing(sqlite3.connect(f"{(out / 's.db').as_uri()}?mode=ro&immutable=1", uri=True)) as conn:
            self.assertEqual(conn.execute("SELECT data FROM e").fetchone()[0], new)
        self.assertNotIn(self.USER.encode(), (out / "s.db").read_bytes())

    def test_anonymize_user_name_as_a_whole_word(self):
        """Il nome utente come parola intera (le colonne proprietario e gruppo di `ls -la`) diventa `USER`."""
        out = self.tmp / "out"
        out.mkdir()
        line = f"drwxrwxr-x 2 {self.USER} {self.USER} 4096 19 nov 06.13 ."
        want = "drwxrwxr-x 2 USER USER 4096 19 nov 06.13 ."
        (out / "ls.txt").write_text(line + f"\n{self.USER}x e x{self.USER}\n")
        conn = sqlite3.connect(out / "s.db", isolation_level=None)
        conn.execute("CREATE TABLE e (data TEXT)")
        conn.execute("INSERT INTO e VALUES (?)", (line,))
        conn.close()
        self.assertEqual(scrub.anonymize(out, self.USER, self.HOST), 2)
        self.assertEqual((out / "ls.txt").read_text(), want + f"\n{self.USER}x e x{self.USER}\n")
        with closing(sqlite3.connect(f"{(out / 's.db').as_uri()}?mode=ro&immutable=1", uri=True)) as conn:
            self.assertEqual(conn.execute("SELECT data FROM e").fetchone()[0], want)
        self.assertNotIn(self.USER.encode(), (out / "s.db").read_bytes())
        with self.assertRaises(ValueError):
            scrub.anonymize(out, "abc", self.HOST)

    def test_anonymize_real_tollgate_schema(self):
        from tollgate_core import db as core_db, events as core_events
        from tollgate_core.paths import State
        out = self.tmp / "out"
        root = out / "runs" / "c" / "home" / ".local" / "state" / "tollgate"
        conn = core_db.open_db(State(root, True))
        try:
            core_events.record_event(conn, "research_note", {"ok": True, "cwd": f"/home/{self.USER}/proj"},
                                     now=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc), host=self.HOST)
        finally:
            conn.close()
        self.assertEqual(scrub.anonymize(out, self.USER, self.HOST), 1)
        self.assertEqual(sorted(p.name for p in root.iterdir() if p.is_file() and p.name != "migrate.lock"), ["tollgate.db"])      # niente -wal né -shm
        with closing(sqlite3.connect(f"{(root / 'tollgate.db').as_uri()}?mode=ro", uri=True)) as conn:
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            host, data = conn.execute("SELECT host, data FROM events").fetchone()
        self.assertEqual(host, "HOST")
        self.assertEqual(json.loads(data)["cwd"], "/home/USER/proj")
        raw = (root / "tollgate.db").read_bytes()
        for value in (self.USER, self.HOST):
            self.assertTrue(value.encode() not in raw, "un valore è rimasto nel file")

    def test_anonymize_cli_never_prints_the_values(self):
        out = self.tmp / "out"
        out.mkdir()
        (out / "a.txt").write_text(f"/home/{self.USER}/x {self.HOST}\n")
        r = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "scrub.py"), "anonymize", str(out), self.USER, self.HOST],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((out / "a.txt").read_text(), "/home/USER/x HOST\n")
        for value in (self.USER, self.HOST):
            self.assertNotIn(value, r.stdout + r.stderr)

    def test_anonymize_refuses_short_or_reserved_values(self):
        out = self.tmp / "out"
        out.mkdir()
        (out / "a.txt").write_text(f"/home/{self.USER}/x {self.HOST}\n")
        conn = self.make_db(out / "x.db")
        conn.close()
        before = self.snapshot(out)
        for user, host in (("abc", self.HOST), (self.USER, "abc"), ("root", self.HOST), (self.USER, "Test"), ("USER", self.HOST),
                           ("", self.HOST), (self.USER, "tool")):
            with self.subTest(user=user, host=host):
                r = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "scrub.py"), "anonymize", str(out), user, host],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertEqual(self.snapshot(out), before)
                with self.assertRaises(ValueError):
                    scrub.anonymize(out, user, host)


class ResearchCountsTest(ScrubBase):
    def make_state(self, run, *, events=True, lookups_table=True):
        from tollgate_core import db as core_db, events as core_events, lookups as core_lookups
        from tollgate_core.paths import State
        root = run / "home" / ".local" / "state" / "tollgate"
        now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
        conn = core_db.open_db(State(root, True))
        try:
            core_events.record_event(conn, "research_note", {"task": 1, "ok": True, "problems": []}, now=now, host=FAKE_HOST)
            core_events.record_event(conn, "research_note", {"task": 1, "ok": True, "problems": []}, now=now, host=FAKE_HOST)
            core_events.record_event(conn, "research_note", {"task": 2, "ok": False, "problems": ["x"]}, now=now, host=FAKE_HOST)
            core_events.record_event(conn, "research_reminder", {"task": 1}, now=now, host=FAKE_HOST)
            core_events.record_event(conn, "research_switch_unreadable", {"error": "x"}, now=now, host=FAKE_HOST)
            core_events.record_event(conn, "veto", {"event": "pre_edit", "rule": "research_gate", "reason": "r"}, now=now, host=FAKE_HOST)
            core_events.record_event(conn, "veto", {"event": "pre_bash", "rule": "effects", "reason": "r"}, now=now, host=FAKE_HOST)
            for kind, target in (("read", "a.py"), ("read", "b.py"), ("fetch", "https://vercel.com/docs")):
                core_lookups.record(conn, work=1, task=1, agent_id=None, session=None, kind=kind, target=target, now=now)
        finally:
            conn.close()
        return root / "tollgate.db"

    def snapshot(self, root):
        return sorted((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns) for p in root.rglob("*"))

    def test_research_counts_reads_state(self):
        run = self.tmp / "runs" / "claude-eval-W0"
        self.make_state(run)
        got = research_counts.count(run)
        self.assertEqual(got, {"note_ok": 2, "note_ko": 1, "reminders": 1, "switch_unreadable": 1, "research_vetoes": 1,
                               "lookups_read": 2, "lookups_grep": 0, "lookups_bash_read": 0, "lookups_fetch": 1,
                               "lookups_search": 0, "lookups_docs": 0})

    def test_research_counts_accepts_a_relative_folder(self):
        run = self.tmp / "runs" / "claude-eval-W0"
        self.make_state(run)
        before = os.getcwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.tmp.parent)
        rel = Path(self.tmp.name)
        self.assertEqual(research_counts.count(rel / "runs" / "claude-eval-W0")["note_ok"], 2)
        self.assertIn("| claude-eval-W0 | 2 |", research_counts.table(rel))

    def test_research_counts_leaves_no_files(self):
        run = self.tmp / "runs" / "claude-eval-W0"
        self.make_state(run)
        before = self.snapshot(self.tmp)
        research_counts.count(run)
        self.assertEqual(self.snapshot(self.tmp), before)
        with mock.patch("sys.stdout", new=io.StringIO()):
            self.assertEqual(research_counts.main([str(self.tmp)]), 0)
        self.assertEqual(self.snapshot(self.tmp), before)

    def test_research_counts_refuses_wal(self):
        run = self.tmp / "runs" / "claude-eval-W0"
        db = self.make_state(run)
        Path(f"{db}-wal").write_bytes(b"")
        with self.assertRaises(research_counts.WalError):
            research_counts.count(run)
        r = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "research_counts.py"), str(self.tmp)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("-wal", r.stderr)
        self.assertFalse(Path(f"{db}-shm").exists())

    def test_research_counts_state_without_tables_is_zero(self):
        run = self.tmp / "runs" / "claude-eval-W0"
        db = run / "home" / ".local" / "state" / "tollgate" / "tollgate.db"
        db.parent.mkdir(parents=True)
        with closing(sqlite3.connect(db)) as conn:
            conn.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, type TEXT, data TEXT)")         # come uno stato di prima di B1
            conn.execute("INSERT INTO events (type, data) VALUES ('research_note', '{\"ok\": true}')")
            conn.commit()
        got = research_counts.count(run)
        self.assertEqual((got["note_ok"], got["lookups_read"]), (1, 0))
        db2 = self.tmp / "runs" / "claude-eval-W1" / "home" / ".local" / "state" / "tollgate" / "tollgate.db"
        db2.parent.mkdir(parents=True)
        with closing(sqlite3.connect(db2)) as conn:
            conn.execute("CREATE TABLE altro (x)")
            conn.commit()
        self.assertEqual(set(research_counts.count(self.tmp / "runs" / "claude-eval-W1").values()), {0})

    def test_research_counts_table_skips_runs_without_state(self):
        self.make_state(self.tmp / "runs" / "claude-eval-W0")
        (self.tmp / "runs" / "claude-eval-O0").mkdir(parents=True)
        text = research_counts.table(self.tmp)
        self.assertIn("| claude-eval-W0 | 2 | 1 | 1 | 1 | 1 | 2 | 0 | 0 | 1 | 0 | 0 |", text)
        self.assertNotIn("| claude-eval-O0", text)
        self.assertIn("claude-eval-O0", text.split("saltate")[1])


class GitignoreTest(unittest.TestCase):
    def test_gitignore_has_b8_lock(self):
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("docs/verifiche/evidenze/eval-b8/*.lock", lines)
        self.assertIn("docs/verifiche/evidenze/eval-p5/*.lock", lines)
        self.assertEqual((ROOT / "docs/verifiche/evidenze/eval-b8/budget.tsv").read_text(encoding="utf-8") .split("\n")[0],
                         HEADER.rstrip("\n"))


if __name__ == "__main__":
    unittest.main()
