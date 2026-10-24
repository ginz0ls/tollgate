"""L'esecuzione degli eval (Task 11 di P5): `evals/run.sh` e `evals/cost.py`.

Mai un `claude` vero: nel `PATH` c'è un `claude` finto che registra gli argomenti e scrive un `result.json` nella forma
reale di `claude plugin eval` (VE8, visto nelle sonde del Task 1). HOME, TMPDIR, registro dei costi, radice delle
evidenze e bersaglio sono cartelle temporanee: nessun test scrive in `docs/verifiche/evidenze/eval-p5/`."""
import fcntl
import io
import json
import os
import signal
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from evals import cost
from tests.helpers import ROOT

RUN_SH = ROOT / "evals" / "run.sh"
def cost_remaining(budget):
    with mock.patch.dict(os.environ, TOLLGATE_EVAL_BUDGET=str(budget), TOLLGATE_EVAL_TEST_MODE="1"):
        return cost.remaining()


HEADER = "ora\tinvocazione\tcostUsd\tdurationSeconds\tcasi\n"

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
            fh.write(json.dumps({"type": "result", "total_cost_usd": 0.5, "usage": {
                "input_tokens": 10, "output_tokens": 100, "cache_read_input_tokens": 1000,
                "cache_creation_input_tokens": 50}}) + "\n")
        with open(os.path.join(run, "config", "settings.json"), "w") as fh:
            fh.write("{}\n")
        if os.environ.get("FAKE_SYMLINK_SETTINGS"):
            os.remove(os.path.join(run, "config", "settings.json"))
            os.symlink(os.environ["FAKE_SYMLINK_SETTINGS"], os.path.join(run, "config", "settings.json"))
        with open(os.path.join(cwd, "ESITO.txt"), "w") as fh:
            fh.write("ok\n")
        with open(os.path.join(cwd, "segreto.txt"), "w") as fh:
            fh.write("ghp_" + "A" * 20 + "\n")
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
                   TOLLGATE_EVAL_TEST_MODE="1")
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
        self.assertEqual(self.run_sh("spec").returncode, 0)
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
        for var in ("TOLLGATE_EVAL_BUDGET", "TOLLGATE_EVAL_EVIDENCE", "TOLLGATE_EVAL_TARGET"):
            with self.subTest(var=var):
                env = {"TOLLGATE_EVAL_TEST_MODE": "", "TOLLGATE_EVAL_BUDGET": "", "TOLLGATE_EVAL_EVIDENCE": "",
                       "TOLLGATE_EVAL_TARGET": "", var: str(self.tmp / "x")}
                r = self.run_sh("spec", **env)
                self.assertEqual(r.returncode, 64)
                self.assertIn(var, r.stderr)
                self.assertEqual(self.calls(), [])
        self.assertFalse((self.tmp / "x").exists())

    def test_preamble_prints_paths_and_test_mode(self):
        self.write_budget(5)
        r = self.run_sh("spec")
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
        r = self.run_sh("--a-secco", "spec")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.budget.read_bytes(), before)
        self.assertFalse(Path(str(self.budget) + ".lock").exists())
        self.assertEqual(self.out_dirs(), [])
        self.assertIn("residuo del tetto: 60.00", r.stdout)
        self.assertIn("a secco", r.stdout)
        self.write_budget(80)
        self.assertEqual(self.run_sh("--a-secco", "spec").returncode, 1)


    def test_prints_command_and_residual(self):
        self.write_budget(20)
        r = self.run_sh("spec")
        self.assertIn("residuo del tetto: 60.00", r.stdout)
        self.assertIn("claude plugin eval", r.stdout)
        self.assertRegex(r.stdout, r"costo dell'invocazione 1\.25 USD; residuo 58\.75 USD")


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
        self.real = ROOT / "docs" / "verifiche" / "evidenze" / "eval-p5"
        self.budget = self.real / "budget.tsv"

    def snapshot(self):
        return (self.budget.read_bytes(), sorted(p.name for p in self.real.iterdir()))

    def test_dry_run_reads_real_registry(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("TOLLGATE_", "CLAUDE"))}
        env.update(HOME=str(self.home), TMPDIR=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                   PATH=f"{self.bin}:{os.environ['PATH']}")
        before = self.snapshot()
        r = subprocess.run(["bash", str(RUN_SH), "--a-secco", "spec"], capture_output=True, text=True, env=env,
                           timeout=300, stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse(self.marker.exists(), "claude è stato lanciato")
        self.assertEqual(self.snapshot(), before)               # registro uguale byte per byte, nessuna cartella né lock nuovi
        remaining = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "cost.py"), "remaining"],
                                   capture_output=True, text=True, env=env).stdout.strip()
        self.assertRegex(remaining, r"^\d+\.\d\d$")
        self.assertIn(f"residuo del tetto: {remaining} USD", r.stdout)
        self.assertNotIn("TEST_MODE", r.stdout)
        self.assertIn(f"registro dei costi: {self.budget}", r.stdout)
        cmd = next(line for line in r.stdout.splitlines() if line.startswith("comando: "))
        for flag in ("--no-publish", "--allow-tools Bash Write Edit", f"--max-cost-usd {remaining} "):
            self.assertIn(flag, cmd)
        self.assertIn("/tmp/tollgate-eval-target", cmd)


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
        self.assertEqual(cost.remaining(), 80.0)               # nessun registro
        self.budget.write_text(HEADER + "a\tb\t12.5\t3\tc\n\na\tb\t0.25\t3\tc\n", encoding="utf-8")
        self.assertAlmostEqual(cost.remaining(), 67.25)
        self.budget.write_text(HEADER + "a\tb\t90\t3\tc\n", encoding="utf-8")
        self.assertEqual(cost.remaining(), 0.0)

    def test_remaining_fail_closed(self):
        for bad in ("a\tb\t?\t?\tc\n", "a\tb\tnan\t1\tc\n", "a\tb\n", "a\tb\t-3\t1\tc\n"):
            with self.subTest(bad=bad):
                self.budget.write_text(HEADER + bad, encoding="utf-8")
                self.assertEqual(cost.remaining(), 0.0)
        self.budget.write_text("intestazione\tsbagliata\n", encoding="utf-8")
        self.assertEqual(cost.remaining(), 0.0)

    def test_remaining_cli_rounds_down_to_cents(self):
        self.budget.write_text(HEADER + "a\tb\t0.1234\t3\tc\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-B", str(ROOT / "evals" / "cost.py"), "remaining"], capture_output=True,
                           text=True, env={**os.environ, "TOLLGATE_EVAL_BUDGET": str(self.budget), "TOLLGATE_EVAL_TEST_MODE": "1"})
        self.assertEqual(r.stdout.strip(), "79.87")

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
        when = cost.reserve("spec (with-without)")
        self.assertEqual(cost.remaining(), 0.0)                      # prenotata = tetto chiuso
        res = self.result(make_result([case_entry("s1", [1.0], None)], cost_usd=2.5, duration=9))
        self.assertTrue(cost.add(res, "spec (with-without)", reserved=when))
        lines = self.budget.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1].split("\t")[2:], ["2.5", "9", "s1"])
        self.assertAlmostEqual(cost.remaining(), 77.5)
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


if __name__ == "__main__":
    unittest.main()
