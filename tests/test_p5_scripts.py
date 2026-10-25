"""Lo script delle verifiche reali di P5 (Task 1), la sonda di `claude plugin eval` e il workflow della sonda di CI,
provati senza rete e senza `claude`: `bash -n`, il modo `controlla` (che gira su repo nudi locali con `gh` e `claude` finti
davanti nel PATH e passa ogni comando da `ghguard.py` col profilo p5) e prove dirette dei file della sonda."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

P5 = ROOT / "spikes" / "p5"
SCRIPT = P5 / "run-p5-checks.sh"
PLUGIN = P5 / "probe-plugin"
CASES = sorted((PLUGIN / "evals").iterdir())
BUDGET = ROOT / "docs" / "verifiche" / "evidenze" / "eval-p5" / "budget.tsv"
GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists"}      # decisione 2: solo deterministici
SECRET = "zz-valore-segreto-della-prova"

try:
    import yaml
except ImportError:                                                   # PyYAML non è nella libreria standard
    yaml = None


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("P4_", "P5_", "TOLLGATE_", "GIT_"))}
    env.update(extra)
    return env


class ScriptShapeTest(unittest.TestCase):
    def test_syntax(self):
        for script in [SCRIPT, P5 / "probe-bin" / "sonda-shim", P5 / "probe-bin" / "python3", *[c / "scaffold.sh" for c in CASES]]:
            with self.subTest(script.name):
                r = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
        for py in [P5 / "fake" / "gh", P5 / "fake" / "claude.py", PLUGIN / "bin" / "sonda", *(PLUGIN / "hooks").glob("*.py")]:
            with self.subTest(py.name):
                compile(py.read_text(), str(py), "exec")

    def test_the_script_never_runs_claude_p_nor_destructive_commands(self):
        text = SCRIPT.read_text()
        self.assertNotRegex(text, r"claude\s+-p\b")
        self.assertNotRegex(text, r"\brm\s+-[a-zA-Z]*[rR]")
        self.assertNotRegex(text, r"\b(pkill|killall)\b")
        self.assertNotRegex(text, r"\bkill\s")
        # le prove negative nominano i comandi vietati (check_git_negativi) e i commenti li descrivono: non sono comandi
        code = re.sub(r"(?s)check_git_negativi\(\) \{.*?\n\}\n", "", text)
        code = re.sub(r"(?m)^\s*#.*$", "", code)
        self.assertNotRegex(code, r"--force|push\s+(-f|--force)|--no-verify|reset --hard|git stash|--amend")
        self.assertNotRegex(text, r"\bgh\s+auth\s+(login|refresh|token)")

    def test_gh_is_only_called_through_the_guarded_helpers(self):
        for number, line in enumerate(SCRIPT.read_text().splitlines(), 1):
            code = line.split("#", 1)[0] if not line.lstrip().startswith(("echo", "printf", "gh_q()")) else ""
            with self.subTest(number):
                self.assertNotRegex(code, r"(?:^|[;&|(`]\s*|\$\(\s*|\bthen\s+|\bdo\s+)gh\s+\S",
                                    f"riga {number}: gh fuori da gh_call/gh_read/gh_q")

    def test_network_git_goes_only_through_git_net(self):
        allowed_local = ("git clone -q --no-hardlinks --branch main \"$SOURCE\"", "config --get-regexp")
        in_remotes = False
        for number, line in enumerate(SCRIPT.read_text().splitlines(), 1):
            in_remotes = in_remotes or line.startswith("make_remotes()")
            if line.startswith("make_source()"):
                in_remotes = False
            code = line.split("#", 1)[0]
            if not re.search(r"\bgit\b.*\b(push|pull|fetch|ls-remote|clone)\b", code) or in_remotes:
                continue
            with self.subTest(number):
                self.assertTrue(any(a in code for a in allowed_local) or "git_net" in code or code.lstrip().startswith('"'),
                                f"riga {number}: git con la rete fuori da git_net: {code.strip()}")

    def test_exactly_one_claude_eval_command_with_every_precaution(self):
        text = SCRIPT.read_text()
        self.assertEqual(len(re.findall(r"claude plugin eval", re.sub(r"(?m)^\s*#.*$", "", text.split("check_claude_log()")[0]))), 1)
        command = re.search(r"local -a cmd=\(claude plugin eval(.*?)\n\s*shown=", text, re.S).group(1)
        for flag in ("--no-publish", "--trust-plugin", "--runs 1", '--model "$MODEL"', "--scaffold", "--allow-tools Bash Write Edit",
                     '--max-cost-usd "$cap"', '--json "$dir/result.json"', '--output-dir "$dir"', '--report "$dir/report.html"',
                     "--keep-temp"):
            self.assertIn(flag, command)
        self.assertIn("MODEL=claude-sonnet-5-5", text)
        self.assertIn("BUDGET_TOTAL=80", text)
        self.assertIn("CAP_MAX=3", text)
        self.assertRegex(text, r'PATH="\$shim_dir:\$PATH"')
        self.assertIn('shim_dir="${5:-$here/probe-bin}"', text)

    def test_budget_ledger_is_committed_with_the_exact_header(self):
        self.assertEqual(BUDGET.read_text().splitlines()[0], "ora\tinvocazione\tcostUsd\tdurationSeconds\tcasi")

    def test_the_eval_runs_are_the_planned_ones(self):
        text = SCRIPT.read_text()
        calls = re.findall(r"(?m)^\s+eval_run (\S+) (\S+) \"\$(\w+)\" (\S+)(?: \"(.*)\")?$", text)
        self.assertEqual([(c[0], c[1], c[3]) for c in calls],
                         [("sonda-nl-bash", "with-without", "nl-bash"), ("sonda-nl-worktree", "none", "nl-worktree"),
                          ("sonda-ws-worktree", "none", "ws-worktree"), ("sonda-skill", "none", "skill"),
                          ("sonda-radice-tmp", "none", "skill"), ("sonda-ve1-dependencies", "none", "skill")])
        self.assertEqual(calls[4][4], "$tmp_target/probe-bin")           # D10: lo shim copiato nella radice /tmp
        self.assertIn("tmp_target=\"${P5_TMP_TARGET:-/tmp/tollgate-eval-target-sonda}\"", text)


class ControllaTest(unittest.TestCase):
    """Il modo `controlla`, una volta sola: dura circa un minuto."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="tollgate-p5-controlla-"))
        r = subprocess.run(["bash", str(SCRIPT), "controlla"], capture_output=True, text=True,
                           env=clean_env(P5_CHECK_DIR=str(cls.tmp), GH_HOST="altro.example", GH_REPO="x/y",
                                         GH_ENTERPRISE_TOKEN="a", GITHUB_ENTERPRISE_TOKEN="b"), timeout=900)
        cls.out, cls.err, cls.rc = r.stdout, r.stderr, r.returncode

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_it_passes_cleanly(self):
        self.assertEqual(self.rc, 0, self.out[-3000:] + self.err[-2000:])
        self.assertIn("CONTROLLA: ok", self.out)
        for bad in ("VIOLAZIONE", "FALLITO", "DOVEVA FALLIRE", "NON FERMATO", "MA RIFIUTATO", "manca "):
            self.assertNotIn(bad, self.out)
        self.assertEqual(self.err, "")

    def test_every_mode_runs(self):
        for mode in ("cerca-token-pulito", "ci-sonda", "pins", "detect-cache", "detect-pin", "raccogli", "eval-sonda",
                     "eval-tetto-residuo"):
            self.assertIn(f"modo {mode}: ok", self.out)

    def test_token_search_stops_on_a_token_and_never_prints_it(self):
        self.assertIn("modo cerca-token-sporco: fermato come previsto", self.out)
        self.assertIn("cerca-token: il sorgente sporco è segnalato", self.out)
        self.assertIn("cerca-token: percorso stampato", self.out)
        self.assertIn("cerca-token: il testo trovato non è stampato", self.out)
        self.assertIn("cerca-token: l'ammissione esplicita è stampata", self.out)
        self.assertIn("ci-sonda: nessun repo creato con token nella storia", self.out)
        for name in ("modo-cerca-token-sporco.log", "modo-ci-sonda-sporco.log"):
            self.assertNotIn("p_aaaa", (self.tmp / name).read_text())

    def test_the_repo_is_created_once_and_privately_and_branches_are_pushed(self):
        log = (self.tmp / "gh.log").read_text()
        self.assertEqual(log.count("repo\tcreate\t"), 1)
        self.assertIn("repo\tcreate\tginz0ls/tollgate\t--private\t", log)
        self.assertRegex(self.out, r"ginz0ls/tollgate: main,p5-probe-ci")
        self.assertRegex(self.out, r"ginz0ls/tollgate-p4-detect: main,p5-probe-cache,p5-probe-cache-[0-9-]+,p5-probe-pin")

    def test_pin_restore_happens_even_when_a_step_fails(self):
        self.assertIn("detect-pin: valore iniziale rimesso (false)", self.out)
        self.assertIn("detect-pin dopo un passo fallito: valore iniziale rimesso (false)", self.out)
        self.assertIn("detect-pin: ripristino verificato anche dopo il fallimento", self.out)
        self.assertIn("modo detect-pin-push-rifiutato: fermato come previsto", self.out)
        puts = [line for line in (self.tmp / "gh.log").read_text().splitlines() if line.startswith("api\t--method\tPUT")]
        self.assertTrue(puts)
        self.assertEqual(sum("sha_pinning_required=true" in p for p in puts), sum("sha_pinning_required=false" in p for p in puts))

    def test_a_500_on_a_read_is_retried_and_recorded(self):
        retries = (self.tmp / "out" / "ritentativi.log").read_text()
        self.assertIn("tentativo 1 dopo un 5xx", retries)
        self.assertTrue(list((self.tmp / "out").glob("ramo-p5-probe-cache.*.prev-*")))      # il tentativo fallito resta

    def test_budget_cap_is_the_minimum_of_three_and_the_residual(self):
        self.assertIn("tetto 1.50", self.out)
        self.assertIn("tetto 1.25", self.out)
        caps = re.findall(r"--max-cost-usd\t([0-9.]+)", (self.tmp / "claude.log").read_text())
        self.assertIn("3.00", caps)
        self.assertIn("1.50", caps)
        self.assertTrue(all(0 < float(c) <= 3 for c in caps), caps)
        self.assertIn("modo eval-tetto-esaurito: fermato come previsto", self.out)
        self.assertIn("eval-sonda: con il tetto esaurito claude non è stato lanciato", self.out)

    def test_unknown_cost_stops_everything_that_follows(self):
        self.assertIn("eval-sonda: costo ignoto segnalato", self.out)
        self.assertIn("eval-sonda: dopo un costo ignoto non parte altro", self.out)
        self.assertIn("costo ignoto: controlla a mano prima di continuare", (self.tmp / "modo-eval-costo-ignoto.log").read_text())

    def test_every_budget_row_is_written_whatever_the_exit(self):
        rows = (self.tmp / "eval" / "budget.tsv").read_text().splitlines()
        self.assertEqual(rows[0], "ora\tinvocazione\tcostUsd\tdurationSeconds\tcasi")
        self.assertEqual(len(rows), 7)
        for row in rows[1:]:
            fields = row.split("\t")
            self.assertEqual(len(fields), 5)
            float(fields[2]), float(fields[3])

    def test_eval_evidence_is_kept_and_the_probe_files_are_copied(self):
        self.assertIn("shim della sonda in testa al PATH di ogni eval: sì", self.out)
        folder = next((self.tmp / "eval").glob("*-sonda-skill"))
        for name in ("result.json", "aggregate-result.json", "report.html", "stdout.txt", "stderr.txt"):
            self.assertTrue((folder / name).exists(), name)
        names = {p.name for p in (folder / "corse").rglob("*") if p.is_file()}
        self.assertTrue({"trace.jsonl", "settings.json", "esiti.txt", "sonda-hooks.jsonl", "sonda-scaffold.txt", "scritto-da-hook.md",
                         "WT-OK", "hooks.jsonl", "installed_plugins.json"} <= names, names)
        self.assertFalse({"altro.txt", ".bashrc"} & names)                    # dalla home sigillata solo i file della sonda
        self.assertIn("TMPDIR dell eval:", (folder / "tmpdir.txt").read_text())

    def test_sealed_runs_are_made_readable_and_only_the_probe_files_are_copied(self):
        for line in ("corsa tenuta: trace copiata", "corsa tenuta: file della sonda copiati", "corsa tenuta: nient'altro copiato",
                     "P5_EVAL_TMPDIR usato per le corse"):
            self.assertIn(line, self.out)
        self.assertTrue(list((self.tmp / "evtmp").glob("claude-eval-*")))     # TMPDIR passato al solo claude plugin eval
        for run in (self.tmp / "evtmp").glob("claude-eval-*"):
            self.assertTrue(os.access(run / "sealed", os.R_OK | os.X_OK), run)

    def test_raccogli_corse_finds_the_evidence_folder_from_the_trace_path(self):
        self.assertIn("modo raccogli-corse: ok", self.out)
        self.assertIn("raccogli-corse: corsa riassegnata alla sua evidenza dalla tracePath", self.out)

    def test_raccogli_corse_refuses_anything_that_is_not_a_claude_eval_run_before_any_chmod(self):
        for line in ("raccogli-corse: 7 cartelle non valide rifiutate", "raccogli-corse: nessun chmod sulle cartelle rifiutate (500 0 500)",
                     "raccogli-corse: niente copiato dalle rifiutate"):
            self.assertIn(line, self.out)
        log = (self.tmp / "modo-raccogli-corse-rifiutate.log").read_text()
        for refused in ("altro/claude-eval-zzz", "non-una-corsa", "nested/claude-eval-qqq", "/sealed", "claude-eval-link", " /tmp", "evtmp"):
            self.assertIn(refused, log)

    def test_a_token_in_the_trace_or_a_probe_file_blocks_that_copy_only(self):
        self.assertIn("trace con un token: non copiata e registrata, il resto sì", self.out)
        self.assertIn("nessun token nelle evidenze", self.out)

    def test_eval_tmpdir_is_compared_after_realpath(self):
        self.assertIn("P5_EVAL_TMPDIR sotto /tmp (anche via .. o collegamento) rifiutato prima di lanciare", self.out)
        self.assertEqual(self.out.count("modo eval-tmpdir-rifiutato: fermato come previsto"), 5)
        self.assertIn("realpath -m", SCRIPT.read_text())

    def test_settings_with_credentials_are_not_copied_and_the_fact_is_recorded(self):
        self.assertIn("settings.json con credenziali: non copiato e registrato", self.out)

    def test_pins_pick_the_latest_tag_of_each_major_dereferenced(self):
        rows = [r.split("\t") for r in (self.tmp / "out" / "pins.tsv").read_text().splitlines()[1:]]
        checkout = {r[2]: r for r in rows if r[0] == "checkout"}
        self.assertEqual(set(checkout), {"v4.2.2", "v5.0.0"})
        self.assertTrue(all(len(r[3]) == 40 and r[4] == "dereferenziato" for r in rows))
        engines = dict(((r[0], r[1]), r[2]) for r in (l.split("\t") for l in (self.tmp / "out" / "pins-motore.tsv").read_text().splitlines()[1:]))
        self.assertEqual(engines[("checkout", "v4.2.2")], "node20")
        self.assertEqual(engines[("checkout", "v5.0.0")], "node24")

    def test_every_registered_command_passes_the_p5_guard(self):
        self.assertIn("comandi gh controllati:", self.out)
        self.assertIn("claude plugin eval registrati:", self.out)
        self.assertIn("righe RIFIUTATO nel registro: 0", self.out)
        self.assertRegex(self.out, r"guard_args: (\d+) fermati su \1;")
        self.assertRegex(self.out, r"comandi legittimi ammessi: (\d+) su \1")
        self.assertRegex(self.out, r"git: (\d+) fermati su \1")

    def test_registered_commands_name_no_other_repo(self):
        text = (self.tmp / "out" / "comandi.log").read_text() + (self.tmp / "gh.log").read_text().replace("\t", " ")
        for repo in set(re.findall(r"ginz0ls/[A-Za-z0-9._-]+", text)):
            self.assertIn(re.sub(r"\.git$", "", repo.rstrip(".")), ("ginz0ls/tollgate", "ginz0ls/tollgate-p4-detect"))
        self.assertNotIn("protected", text)

    def test_cache_mode_and_ci_summaries_are_saved(self):
        self.assertIn("Cache mode:", (self.tmp / "out" / "cache-mode.txt").read_text())
        self.assertIn("sonda: rc=", (self.tmp / "out" / "ci-riepilogo.txt").read_text())
        self.assertRegex((self.tmp / "out" / "prs-aperte.txt").read_text(), r"\Acreate\npr [0-9]+\n\Z")

    def test_gh_host_repo_and_enterprise_tokens_never_reach_the_gh_calls(self):
        self.assertIn("gh finti: GH_HOST, GH_REPO e i token enterprise non arrivano mai", self.out)
        seen = (self.tmp / "gh.log.env").read_text().splitlines()
        self.assertTrue(seen)
        for line in seen:
            self.assertTrue(all(f.endswith("=") for f in line.split("\t") if f), line)

    def test_an_orphan_pr_is_closed_by_the_trap_when_a_later_step_fails(self):
        self.assertIn("modo detect-cache-registro-bloccato: fermato come previsto", self.out)
        self.assertIn("detect-cache: PR chiusa dal trap dopo un errore", self.out)

    def test_unknown_cost_writes_a_question_mark_row_that_blocks_the_cap(self):
        row = [l for l in (self.tmp / "eval-b3" / "budget.tsv").read_text().splitlines() if "\t?\t?\t" in l]
        self.assertEqual(len(row), 1)
        self.assertIn("eval-sonda: con una riga costUsd ? budget_cap rifiuta (fail-closed)", self.out)

    def test_p5_only_runs_just_the_named_invocations_and_rejects_typos(self):
        self.assertIn("modo eval-solo: ok", self.out)
        self.assertIn("modo eval-solo-etichetta-sbagliata: fermato come previsto", self.out)
        self.assertIn("eval-sonda con P5_ONLY: 2 invocazioni registrate", self.out)
        rows = (self.tmp / "eval-b4" / "budget.tsv").read_text().splitlines()[1:]
        self.assertEqual([r.split("\t")[1] for r in rows], ["sonda-skill (none)", "sonda-ve1-dependencies (none)"])
        self.assertIn("sonda-nl-bash: saltata (P5_ONLY)", (self.tmp / "modo-eval-solo.log").read_text())

    def test_network_git_never_prompts_for_credentials(self):
        self.assertIn("git di rete: GIT_TERMINAL_PROMPT=0", self.out)
        self.assertIn("env GIT_TERMINAL_PROMPT=0", SCRIPT.read_text())

    def test_polling_calls_are_recorded_too(self):
        log = (self.tmp / "out" / "comandi.log").read_text()
        self.assertGreater(len(re.findall(r"gh run list --repo ginz0ls/tollgate --workflow ci-probe\.yml", log)), 0)
        self.assertEqual(log.count(" gh run list --repo"), (self.tmp / "gh.log").read_text().count("run\tlist\t"))


class ProbeBinTest(unittest.TestCase):
    def test_python3_shim_skips_pyenv_and_runs_the_system_python(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-p5-shim-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        pyenv = tmp / "pyenv" / "shims"
        pyenv.mkdir(parents=True)
        (pyenv / "python3").write_text("#!/usr/bin/env bash\necho shim di pyenv >&2\nexit 127\n")
        (pyenv / "python3").chmod(0o755)
        probe = str(P5 / "probe-bin")
        env = {"PATH": f"{probe}:{pyenv}:/usr/bin:/bin"}
        r = subprocess.run(["python3", "-c", "print(6*7)"], capture_output=True, text=True, env=env)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "42"), r.stderr)
        self.assertNotIn("pyenv", r.stderr)
        self.assertTrue(os.access(P5 / "probe-bin" / "python3", os.X_OK))
        # il PATH di chi lancia resta com'era dopo lo shim, e sonda-shim gira dalla stessa cartella
        r = subprocess.run(["sonda-shim"], capture_output=True, text=True, env=env)
        self.assertEqual(r.stdout.strip(), "SONDA-SHIM-OK")

    def test_python3_shim_without_usr_bin_takes_the_first_python_outside_home(self):
        text = (P5 / "probe-bin" / "python3").read_text()
        self.assertIn("/usr/bin/python3", text)
        self.assertIn("/home/*", text)
        self.assertIn("exit 127", text)


class ProbePluginTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-p5-sonda-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home, self.work = self.tmp / "home", self.tmp / "work"
        self.home.mkdir()
        self.work.mkdir()

    def env(self, **extra):
        env = clean_env(HOME=str(self.home), SONDA_SEGRETO=SECRET, CLAUDE_PLUGIN_ROOT=str(PLUGIN), TMPDIR=str(self.tmp))
        env.update(extra)
        return env

    def test_manifest_has_no_dependencies_and_hooks_cover_the_events(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "sonda")
        self.assertNotIn("dependencies", manifest)
        self.assertEqual(manifest["experimental"], {"evals": "evals"})
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "PreToolUse", "PostToolUse", "UserPromptExpansion", "SubagentStop"})
        self.assertIn("post.py", hooks["PostToolUse"][0]["hooks"][0]["command"])
        self.assertEqual(hooks["PostToolUse"][0]["matcher"], "Bash")
        self.assertEqual(hooks["PreToolUse"][0]["matcher"], "Bash")
        self.assertIn("guard.py", hooks["PreToolUse"][0]["hooks"][0]["command"])
        for event in hooks:
            self.assertTrue(any("record.py" in h["command"] for entry in hooks[event] for h in entry["hooks"]), event)

    def test_skill_and_agent(self):
        skill = (PLUGIN / "skills" / "prova" / "SKILL.md").read_text()
        self.assertRegex(skill, r"(?m)^disable-model-invocation: true$")
        self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/bin/sonda"', skill)
        self.assertIn("sonda:sonda-sub", skill)
        self.assertNotIn("SONDA-SUB", skill)                         # il comando compare solo nel subagente (VE9)
        agent = (PLUGIN / "agents" / "sonda-sub.md").read_text()
        self.assertIn("`echo SONDA-SUB`", agent)
        self.assertRegex(agent, r"(?m)^tools: Bash$")

    def run_guard(self, command=None, raw=None):
        event = raw if raw is not None else json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                                        "tool_input": {"command": command}})
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "guard.py")], input=event, capture_output=True,
                           text=True, env=self.env())
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def test_guard_denies_touch_negato_with_a_recognisable_reason_and_allows_the_rest(self):
        out = self.run_guard("touch NEGATO")["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("SONDA-MOTIVO-NEGATO-7f3a", out["permissionDecisionReason"])
        self.assertIsNotNone(self.run_guard("cd x && touch NEGATO && ls"))
        for command in ("touch AMMESSO", "touch WT-OK", "touch NEGATO2", "echo NEGATO", "sonda-shim", ""):
            self.assertIsNone(self.run_guard(command), command)
        self.assertIsNone(self.run_guard(raw="non è json"))
        self.assertIsNone(self.run_guard(raw=json.dumps({"tool_name": "Read"})))
        self.assertIsNone(self.run_guard(raw=json.dumps({"tool_input": {"command": 5}})))

    def test_the_deny_reason_is_not_in_any_prompt(self):
        for case in CASES:
            self.assertNotIn("SONDA-MOTIVO-NEGATO", (case / "case.yaml").read_text().split("graders:")[0], case.name)

    def run_record(self, event, name="PreToolUse", **env):
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "record.py"), name], input=json.dumps(event),
                           capture_output=True, text=True, env=self.env(**env))
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_record_writes_only_the_allowed_values_and_the_names_of_the_rest(self):
        event = {"hook_event_name": "PreToolUse", "cwd": str(self.work), "tool_name": "Bash", "session_id": "s",
                 "tool_input": {"command": f"echo {SECRET}"}, "transcript_path": "/home/x/t.jsonl"}
        self.run_record(event, CLAUDE_CONFIG_DIR=str(self.tmp / "cfg"), PWD=str(self.work))
        for path in (self.work / "sonda-hooks.jsonl", self.home / ".local" / "state" / "sonda" / "hooks.jsonl"):
            text = path.read_text()
            self.assertNotIn(SECRET, text)
            self.assertNotIn("transcript", text.replace('"transcript_path"', ""))
            record = json.loads(text.splitlines()[0])
            self.assertEqual(set(record["env"]), {"HOME", "PATH", "CLAUDE_CONFIG_DIR", "CLAUDE_PLUGIN_ROOT", "PWD", "TMPDIR"})
            self.assertEqual(record["env"]["HOME"], str(self.home))
            self.assertEqual(record["env"]["CLAUDE_PLUGIN_ROOT"], str(PLUGIN))
            self.assertEqual(record["event"], "PreToolUse")
            self.assertEqual(record["event_cwd"], str(self.work))
            self.assertEqual(record["tool_name"], "Bash")
            self.assertIn("SONDA_SEGRETO", record["env_names"])
            self.assertIn("PATH", record["env_names"])
            self.assertEqual(record["event_keys"], sorted(event))

    def test_record_appends_per_event_and_survives_a_missing_home_or_bad_input(self):
        for name in ("PreToolUse", "UserPromptExpansion", "SubagentStop"):
            self.run_record({"cwd": str(self.work)}, name)
        lines = (self.work / "sonda-hooks.jsonl").read_text().splitlines()
        self.assertEqual([json.loads(l)["event"] for l in lines], ["PreToolUse", "UserPromptExpansion", "SubagentStop"])
        env = self.env()
        env.pop("HOME")
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "record.py"), "SubagentStop"], input="{non json",
                           capture_output=True, text=True, env=env, cwd=self.work)
        self.assertEqual(r.returncode, 0)
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "record.py"), "SubagentStop"], input="{}",
                           capture_output=True, text=True, env=self.env(HOME="/nonexistent/sonda/home"), cwd=self.work)
        self.assertEqual(r.returncode, 0)                      # scrittura impossibile: avviso su stderr, esito invariato

    def test_the_hooks_do_not_write_where_tollgate_keeps_its_state(self):
        for name in ("record.py", "guard.py"):
            self.assertNotIn("tollgate", (PLUGIN / "hooks" / name).read_text().replace("tollgate P5", ""))
        self.assertNotIn(".local/state/tollgate", (PLUGIN / "bin" / "sonda").read_text())

    def scaffold(self, case, **env):
        return subprocess.run(["bash", str(PLUGIN / "evals" / case / "scaffold.sh")], cwd=self.work, capture_output=True,
                              text=True, env=self.env(**env), timeout=120)

    def test_scaffold_builds_the_repo_the_worktree_and_the_registry(self):
        r = self.scaffold("nl-bash")
        self.assertEqual(r.returncode, 0, r.stderr)
        info = dict(l.split("=", 1) for l in (self.work / "sonda-scaffold.txt").read_text().splitlines())
        self.assertEqual(info["PWD"], str(self.work))
        self.assertEqual(info["HOME"], str(self.home))
        self.assertEqual(info["CLAUDE_CONFIG_DIR"], "UNSET")
        self.assertEqual(info["ROOT_GUESS"], str(PLUGIN))
        self.assertEqual(info["ROOT_GUESS_IS_PLUGIN"], "yes")
        self.assertIn("SONDA_SEGRETO", info["ENV_NAMES"].split(","))
        self.assertNotIn(SECRET, (self.work / "sonda-scaffold.txt").read_text())
        self.assertEqual(info["WORKTREE_LIST"], "2")
        self.assertTrue((self.work / ".claude" / "worktrees" / "sonda-wt" / ".git").exists())
        registry = json.loads((self.home / ".claude" / "plugins" / "installed_plugins.json").read_text())
        self.assertEqual(registry["version"], 2)
        self.assertIn("superpowers@claude-plugins-official", registry["plugins"])
        self.assertEqual(len(info["INSTALLED_PLUGINS_SHA256"]), 64)
        self.assertEqual(subprocess.run(["git", "-C", str(self.work), "log", "--oneline"], capture_output=True, text=True).stdout.count("\n"), 1)

    def test_ws_worktree_scaffold_makes_the_workspace_itself_a_worktree(self):
        r = self.scaffold("ws-worktree")
        self.assertEqual(r.returncode, 0, r.stderr)
        info = dict(l.split("=", 1) for l in (self.work / "sonda-scaffold.txt").read_text().splitlines())
        self.assertEqual(info["DOT_GIT_IS_FILE"], "yes")
        self.assertEqual(info["GITDIR_OUTSIDE_WORKSPACE"], "yes")
        self.assertEqual(info["BRANCH"], "tg/1-sonda")
        self.assertEqual(info["WORKTREE_LIST"], "2")
        self.assertTrue(info["DOT_GIT_CONTENT"].startswith(f"gitdir: {self.home}/proj/.git/worktrees/"))
        git = lambda *a: subprocess.run(["git", "-C", str(self.work), *a], capture_output=True, text=True)
        self.assertEqual(git("status", "--short", "--branch").returncode, 0)
        (self.work / "ws-file").write_text("x")
        self.assertEqual(git("add", "ws-file").returncode, 0)
        c = git("-c", "user.name=s", "-c", "user.email=s@example.invalid", "commit", "-q", "-m", "x")
        self.assertEqual(c.returncode, 0, c.stderr)
        self.assertNotIn(SECRET, (self.work / "sonda-scaffold.txt").read_text())

    def test_ws_worktree_scaffold_refuses_a_workspace_that_is_not_empty(self):
        (self.work / "gia-qui").write_text("x")
        r = self.scaffold("ws-worktree")
        self.assertEqual(r.returncode, 1)
        self.assertIn("non è vuoto", r.stderr)

    def run_post(self, event):
        return subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "post.py")], input=json.dumps(event),
                              capture_output=True, text=True, env=self.env())

    def test_post_hook_returns_a_recognisable_context_and_writes_a_new_file(self):
        r = self.run_post({"hook_event_name": "PostToolUse", "cwd": str(self.work), "tool_name": "Bash"})
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PostToolUse")
        self.assertIn("SONDA-CONTESTO-POST", out["additionalContext"])
        self.assertTrue((self.work / "scritto-da-hook.md").exists())
        (self.work / "scritto-da-hook.md").write_text("cambiato\n")
        self.run_post({"cwd": str(self.work)})
        self.assertEqual((self.work / "scritto-da-hook.md").read_text(), "cambiato\n")     # non lo riscrive
        r = self.run_post({"cwd": "/nonexistent/sonda"})
        self.assertEqual(r.returncode, 0)                                                   # scrittura impossibile: esito invariato
        self.assertIn("SONDA-CONTESTO-POST", r.stdout)

    def test_scaffold_refuses_a_home_that_looks_real(self):
        for marker in (".claude/settings.json", ".local/state/tollgate/x"):
            home = self.tmp / ("home-" + marker.replace("/", "_"))
            path = home / marker
            path.parent.mkdir(parents=True)
            path.write_text("{}")
            work = self.tmp / ("work-" + marker.replace("/", "_"))
            work.mkdir()
            r = subprocess.run(["bash", str(PLUGIN / "evals" / "nl-bash" / "scaffold.sh")], cwd=work, capture_output=True,
                               text=True, env=self.env(HOME=str(home)), timeout=60)
            self.assertEqual(r.returncode, 1, marker)
            self.assertIn("la HOME sembra quella vera", r.stderr)
            self.assertEqual(os.listdir(work), [])

    def test_bin_sonda_writes_every_outcome_of_ve3(self):
        self.assertEqual(self.scaffold("skill").returncode, 0)
        shim = self.tmp / "shim"
        shim.mkdir()
        shutil.copy(P5 / "probe-bin" / "sonda-shim", shim / "sonda-shim")
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "bin" / "sonda")], cwd=self.work, capture_output=True, text=True,
                           env=self.env(PATH=f"{shim}:{os.environ['PATH']}"), timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        esiti = dict(l.split("=", 1) for l in (self.work / "esiti.txt").read_text().splitlines())
        self.assertTrue(esiti["PYTHON3"].startswith("ok "))
        self.assertTrue(esiti["GIT"].startswith("ok git version"))
        self.assertEqual(esiti["PLUGIN_ROOT_READABLE"], "yes")
        self.assertEqual(esiti["ENV_CLAUDE_PLUGIN_ROOT"], str(PLUGIN))
        self.assertEqual(esiti["ENV_CLAUDE_PLUGIN_ROOT_EQUALS_FILE_ROOT"], "yes")
        self.assertEqual(esiti["HOME"], str(self.home))
        for key in ("STATE_MKDIR", "STATE_WRITE", "STATE_READ", "WORKTREES_WRITE_EXISTING", "WORKTREES_WRITE_NEW", "INSTALLED_PLUGINS_READ"):
            self.assertEqual(esiti[key], "ok", key)
        self.assertEqual(esiti["INSTALLED_PLUGINS_UNCHANGED"], "yes")
        self.assertEqual(esiti["SHIM_FOUND"], "yes")
        self.assertEqual(esiti["SHIM_FIRST_IN_PATH"], "yes")
        self.assertEqual(esiti["SHIM_RUN"], "ok")
        self.assertTrue((self.work / ".claude" / "worktrees" / "sonda-wt" / "SONDA-WRITE").exists())
        self.assertFalse((self.home / ".local" / "state" / "tollgate").exists())

    def test_bin_sonda_notices_a_rewritten_registry_and_reports_failures_without_stopping(self):
        self.assertEqual(self.scaffold("skill").returncode, 0)
        (self.home / ".claude" / "plugins" / "installed_plugins.json").write_text("{}")
        (self.work / ".claude" / "worktrees").rename(self.tmp / "spostata")
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "bin" / "sonda")], cwd=self.work, capture_output=True, text=True,
                           env=self.env(PATH="/usr/bin:/bin"), timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        esiti = dict(l.split("=", 1) for l in (self.work / "esiti.txt").read_text().splitlines())
        self.assertEqual(esiti["INSTALLED_PLUGINS_UNCHANGED"], "no")
        self.assertTrue(esiti["WORKTREES_WRITE_EXISTING"].startswith("fail:"))
        self.assertEqual(esiti["SHIM_FOUND"], "no")
        self.assertTrue(esiti["SHIM_RUN"].startswith("fail"))


class ProbeCasesTest(unittest.TestCase):
    def read(self, name):
        return (PLUGIN / "evals" / name / "case.yaml").read_text()

    def test_there_are_distinct_cases_and_identical_scaffolds(self):
        self.assertEqual([c.name for c in CASES], ["nl-bash", "nl-worktree", "skill", "ws-worktree"])
        scaffolds = {(c / "scaffold.sh").read_text() for c in CASES if c.name != "ws-worktree"}
        self.assertEqual(len(scaffolds), 1)
        self.assertIn('worktree add -q "$ws" -b tg/1-sonda', (PLUGIN / "evals" / "ws-worktree" / "scaffold.sh").read_text())
        for case in CASES:
            self.assertTrue(os.access(case / "scaffold.sh", os.X_OK))
            self.assertEqual(set(os.listdir(case)), {"case.yaml", "scaffold.sh"})

    def test_case_headers_and_deterministic_graders_only(self):
        for case in CASES:
            text = self.read(case.name)
            with self.subTest(case.name):
                self.assertIn('schema_version: "1.1"', text)
                self.assertIn(f"name: {case.name}", text)
                self.assertRegex(text, r"(?m)^runs: 1$")
                self.assertIn("scaffold_script: scaffold.sh", text)
                types = set(re.findall(r"(?m)^    type: (\w+)$", text))
                self.assertTrue(types and types <= GRADER_TYPES, types)
                self.assertNotRegex(text, r"type: (llm|baseline)")

    def test_natural_language_case_checks_the_deny_the_control_and_the_worktree(self):
        text = self.read("nl-bash")
        self.assertIn("touch NEGATO", text)
        self.assertIn("touch AMMESSO", text)
        self.assertRegex(text, r"(?s)path: NEGATO\n    exists: false")
        self.assertRegex(text, r"(?s)path: AMMESSO\n    exists: true")
        self.assertRegex(text, r"(?s)path: \.claude/worktrees/sonda-wt/WT-OK\n    exists: true")
        self.assertIn("SONDA-MOTIVO-NEGATO-7f3a", text)
        self.assertIn("`cd .claude/worktrees/sonda-wt && touch WT-OK && pwd`", text)       # un solo comando: VE10 anche se il cd non persiste
        self.assertIn("esegui solo `pwd`", text)                                           # e un comando separato per misurare se persiste
        self.assertNotIn("/sonda:", text)

    def test_hook_diagnostics_d18_and_ve12_graders(self):
        nl = self.read("nl-bash")
        self.assertRegex(nl, r"(?s)pattern: 'SONDA-CONTESTO-POST'")
        self.assertRegex(nl, r"(?s)path: scritto-da-hook\.md\n    exists: true")
        self.assertRegex(nl, r"(?s)target: files\n    pattern: 'scritto-da-hook")
        ws = self.read("ws-worktree")
        self.assertIn("SONDA-WS-$((40+2))", ws)                    # il comando nel prompt, l'uscita «SONDA-WS-42» solo nella trace
        self.assertNotIn("SONDA-WS-42", ws.split("graders:")[0])
        self.assertIn('"event": "SessionStart"', ws)
        self.assertIn("git commit", ws.replace(" -c user.name=sonda -c user.email=sonda@example.invalid", ""))

    def test_worktree_case_grants_enterworktree_and_the_skill_case_the_skill_and_agent(self):
        self.assertIn("allowed_tools: [Read, EnterWorktree]", self.read("nl-worktree"))
        skill = self.read("skill")
        self.assertIn('prompt: "/sonda:prova"', skill)
        self.assertIn("allowed_tools: [Read, Skill, Agent]", skill)
        for event in ("UserPromptExpansion", "SubagentStop"):
            self.assertIn(f'"event": "{event}"', skill)
        self.assertRegex(skill, r"(?s)tool: Skill\n    input_match: 'prova'\n    arm: with-only")
        self.assertIn("echo SONDA-SUB", skill)

    @unittest.skipUnless(yaml, "PyYAML assente")
    def test_cases_parse_as_yaml_with_named_graders(self):
        for case in CASES:
            doc = yaml.safe_load(self.read(case.name))
            with self.subTest(case.name):
                names = [g["name"] for g in doc["graders"]]
                self.assertEqual(len(names), len(set(names)))
                for grader in doc["graders"]:
                    self.assertIn(grader["type"], GRADER_TYPES)
                    target = grader.get("target")
                    if isinstance(target, dict):
                        self.assertEqual(set(target), {"source", "path"})
                        self.assertEqual(target["source"], "file")
                self.assertIsInstance(doc["execution"]["prompt"], str)
                self.assertEqual(doc["context"], {"scaffold_script": "scaffold.sh"})


class CiProbeWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.text = (P5 / "ci-probe.yml").read_text()

    def test_matrix_checkout_permissions_and_warnings(self):
        self.assertIn('python: ["3.11", "3.13"]', self.text)
        self.assertIn('warnings: ["off", "error"]', self.text)
        self.assertIn('path: "tollgate src"', self.text)
        self.assertIn("working-directory: tollgate src", self.text)
        self.assertRegex(self.text, r"(?m)^permissions:\n  contents: read$")
        self.assertIn("PYTHONWARNINGS=error::ResourceWarning", self.text)
        self.assertIn("PYTHONS=python tests/run", self.text)
        self.assertIn("unclosed database", self.text)
        self.assertIn('branches: ["p5-probe-*"]', self.text)

    def test_no_expression_inside_run_lines(self):
        lines = self.text.split("\n")
        i = 0
        while i < len(lines):
            m = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", lines[i])
            if not m:
                i += 1
                continue
            indent = len(m.group(1)) + (2 if lines[i].lstrip().startswith("-") else 0)
            block = [m.group(2)]
            i += 1
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
                block.append(lines[i])
                i += 1
            self.assertNotIn("${{", "\n".join(block))

    @unittest.skipUnless(yaml, "PyYAML assente")
    def test_it_parses_as_yaml(self):
        doc = yaml.safe_load(self.text)
        self.assertEqual(doc["jobs"]["suite"]["strategy"]["matrix"]["python"], ["3.11", "3.13"])
        self.assertEqual(doc["permissions"], {"contents": "read"})


GATE = ROOT / "spikes" / "run-p5-gate.sh"
GATE_CASES = ["pulita-fissata", "rifiuto-v4", "rivalutazione", "skip-ci"]


def gate_code(text):
    """Il codice dei modi del gate senza i commenti, il gh finto (heredoc) e il modo controlla con le sue prove negative, che
    nominano a posto loro i comandi vietati."""
    text = re.sub(r"(?s)<<'PY'\n.*?\nPY\n", "\n", text)
    for name in ("check_negativi", "check_git_negativi", "make_remote", "modo_controlla"):
        text = re.sub(r"(?s)\n%s\(\) \{.*?\n\}\n" % name, "\n", text)
    text = re.sub(r"(?m)^.*(\bforced=|nel registro|RIFIUTATO).*$", "", text)       # i controlli del registro nominano i comandi vietati
    return re.sub(r"(?m)^\s*#.*$", "", text)


class GateScriptShapeTest(unittest.TestCase):
    """Il Task 13: lo script della prova reale su detect. Si prova solo `bash -n` e `controlla` (mai gli altri modi)."""

    def setUp(self):
        self.text = GATE.read_text()
        self.code = gate_code(self.text)

    def test_syntax(self):
        r = subprocess.run(["bash", "-n", str(GATE)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_claude_no_destructive_command_no_forbidden_git(self):
        self.assertNotRegex(self.code, r"\bclaude\b")
        self.assertNotRegex(self.code, r"\brm\s+-[a-zA-Z]*[rR]")
        self.assertNotRegex(self.code, r"\b(pkill|killall)\b")
        self.assertNotRegex(self.code, r"\bkill\s")
        self.assertNotRegex(self.code, r"--force|push\s+(-f|--force)|--no-verify|reset --hard|git stash|--amend|--delete|--mirror")
        self.assertNotRegex(self.code, r"add\s+(-A|\.)(\s|$)")                       # mai `git add -A`
        self.assertNotRegex(self.code, r"\bgh\s+auth\s+(login|refresh|token)")

    def test_gh_is_only_called_through_the_guarded_helpers(self):
        text = re.sub(r"(?s)<<'PY'\n.*?\nPY\n", "\n", self.text)
        for number, line in enumerate(text.splitlines(), 1):
            code = line.split("#", 1)[0] if not line.lstrip().startswith(("echo", "printf", "gh_q()")) else ""
            with self.subTest(number):
                self.assertNotRegex(code, r"(?:^|[;&|(`]\s*|\$\(\s*|\bthen\s+|\bdo\s+)gh\s+\S",
                                    f"riga {number}: gh fuori da gh_call/gh_read/gh_q")

    def test_network_git_goes_only_through_git_net(self):
        for number, line in enumerate(self.code.splitlines(), 1):
            if not re.search(r"\bgit\b\s+(-C\s+\S+\s+)?(push|pull|fetch|ls-remote|clone)\b", line.split("#", 1)[0]):
                continue
            with self.subTest(number):
                self.assertIn("git_net", line, f"riga {number}: git con la rete fuori da git_net: {line.strip()}")

    def test_the_only_push_to_main_is_the_skip_ci_case(self):
        self.assertEqual(self.code.count("ALLOW_MAIN_PUSH=1"), 1)
        skip = re.search(r"(?s)\ncaso_skip_ci\(\) \{.*?\n\}\n", self.code).group(0)
        self.assertIn("ALLOW_MAIN_PUSH=1", skip)
        self.assertEqual(len(re.findall(r"net_push \S+ \"\$d\" main\b", self.code)), 2)
        self.assertEqual(len(re.findall(r"net_push \S+ \"\$d\" main\b", skip)), 2)
        self.assertIn('git_net "$1" "$2" push "$DET_URL" "$3"', self.code)         # il solo push: url di detect e ramo

    def test_only_the_allowed_operations_are_emitted(self):
        # decisione 21: niente `pr edit` (rotto con gh 2.46: PATCH REST), niente `issue create`, `issue close` lo fa il controller
        self.assertNotRegex(self.code, r"\bpr edit\b")
        self.assertNotRegex(self.code, r"\bissue (create|close|comment)\b")
        self.assertNotRegex(self.code, r"\bpr (comment|edit)\b")
        self.assertNotRegex(self.code, r"tollgate-p4-protected")
        self.assertEqual(self.code.count("--method PATCH"), 1)
        self.assertEqual(self.code.count("--method PUT"), 1)
        self.assertEqual(len(re.findall(r"pr merge", self.code)), 2)                # aggiorna e skip-ci
        self.assertEqual(len(re.findall(r"pr merge .*--squash", self.code)), 2)

    def test_branch_names_are_new_at_every_attempt(self):
        for name in re.findall(r'BR="([^"]+)"', self.code):
            self.assertRegex(name, r"\$TS|\$ISSUE|\$1|\$\(date", name)
        self.assertIn('fresh_branch "tollgate-config/$version"', self.code)
        self.assertIn('p5-gate-rifiuto-v4-$TS', self.code)
        self.assertIn('p5-gate-skip-ci-base-$TS', self.code)
        self.assertIn('tg/$ISSUE-p5-gate-$2-$TS', self.code)

    def test_exit_codes_and_state_file_rules(self):
        self.assertRegex(self.text, r"non so quale valore rimettere, mi rifiuto.*\n\s+exit 2|mi rifiuto\" >&2; exit 2")
        self.assertIn("exit 3", self.code)
        self.assertIn("exit 4", self.code)
        self.assertIn('[ ! -e "$STATE_FILE" ]', self.code)                          # pin-on non sovrascrive uno stato esistente
        self.assertNotIn("$HOME/.local/state", self.text)
        self.assertNotIn("$HOME/.claude", self.text)

    def test_the_cases_are_the_planned_ones(self):
        self.assertIn('CASES="pulita-fissata rifiuto-v4 rivalutazione skip-ci"', self.text)
        for fragment in ("Cache mode: read", "must be pinned to a full-length commit SHA", "pending (guard su edited) poi success", "[skip ci]",
                         "tollgate/sentinel", "SENTINEL_TITLE='tollgate: merge non verificato'"):
            self.assertIn(fragment, self.text)


class GateControllaTest(unittest.TestCase):
    """Il modo `controlla` del gate, una volta sola: tutti i modi su un nudo locale con un gh finto."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="tollgate-p5-gate-controlla-"))
        r = subprocess.run(["bash", str(GATE), "controlla"], capture_output=True, text=True,
                           env=clean_env(P5_CHECK_DIR=str(cls.tmp), GH_HOST="altro.example", GH_REPO="x/y"), timeout=900)
        cls.out, cls.err, cls.rc = r.stdout, r.stderr, r.returncode
        cls.log = (cls.tmp / "out" / "comandi.log").read_text() if (cls.tmp / "out" / "comandi.log").exists() else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def modes(self):
        """comandi.log diviso per modo: {nome del modo: [righe gh e git-net, senza ora]}."""
        out, current = {}, None
        for line in self.log.splitlines():
            body = line.split(" ", 1)[1] if " " in line else ""
            m = re.match(r"\(modo (.*)\)$", body)
            if m:
                current = m.group(1)
                out.setdefault(current, [])
            elif current and (body.startswith("gh ") or body.startswith("git-net ")):
                out[current].append(body)
        return out

    def test_it_passes_cleanly(self):
        self.assertEqual(self.rc, 0, self.out[-3000:] + self.err[-2000:])
        self.assertIn("CONTROLLA: ok", self.out)
        for bad in ("VIOLAZIONE", "FALLITO", "DOVEVA FALLIRE", "NON FERMATO", "MA RIFIUTATO", "manca ", "PR APERTE", "INATTES"):
            self.assertNotIn(bad, self.out)
        self.assertEqual(self.err, "")

    def test_the_case_list_and_every_mode(self):
        for name in GATE_CASES:
            self.assertIn(f"  {name}\tdetect", self.out)
        for mode in ("aggiorna", "pin-on", "caso-pulita-fissata", "caso-rifiuto-v4", "caso-rivalutazione", "caso-skip-ci", "pin-off", "raccogli"):
            self.assertIn(f"modo {mode}: ok", self.out)

    def test_net_push_is_really_refused_outside_skip_ci(self):
        self.assertIn("net_push: main e rami con :, + o - rifiutati fuori da skip-ci", self.out)
        self.assertNotIn("NET_PUSH NON RIFIUTATO", self.out)

    def test_refusals(self):
        self.assertIn("modo pin-off-senza-stato: fermato come previsto", self.out)
        self.assertIn("pin-off: senza stato si rifiuta", self.out)
        self.assertIn("pin-off: nessuna PUT senza stato", self.out)
        self.assertIn("modo caso-sconosciuto: fermato come previsto", self.out)
        self.assertIn("modo caso-senza-pin-on: fermato come previsto", self.out)
        self.assertIn("modo pin-on-due-volte: fermato come previsto", self.out)
        self.assertIn("pin-on: il secondo non sovrascrive il valore iniziale", self.out)
        self.assertIn("caso: con un'issue di sentinella aperta non parte", self.out)

    def test_pin_is_put_back_to_the_initial_value_and_the_state_is_archived_not_deleted(self):
        self.assertFalse(json.loads((self.tmp / "fake" / "perm.json").read_text())["sha_pinning_required"])
        self.assertIn("pin-off: valore iniziale rimesso (false)", self.out)
        self.assertIn("pin-off: stato archiviato, non cancellato", self.out)
        self.assertEqual(len(list((self.tmp / "stato").glob("pin-iniziale.env.rimesso-*"))), 1)
        self.assertFalse((self.tmp / "stato" / "pin-iniziale.env").exists())
        modes = self.modes()
        puts = {m: [line for line in modes[m] if "--method PUT" in line] for m in ("pin-on", "pin-off")}
        self.assertEqual([len(v) for v in puts.values()], [1, 1])      # il secondo pin-on e il pin-off senza stato si rifiutano prima di ogni PUT
        self.assertIn("sha_pinning_required=true", puts["pin-on"][0])
        self.assertIn("sha_pinning_required=false", puts["pin-off"][0])

    def test_each_mode_emits_only_its_own_commands(self):
        modes = self.modes()
        for name, lines in modes.items():
            for line in lines:
                with self.subTest(name, line=line[:90]):
                    self.assertNotRegex(line, r"^gh (pr edit|issue create|issue close|issue comment|pr comment|repo |auth )|--force|\s-f\s|--delete|--mirror|\s\+\S")
        # pin-on e pin-off: nessuna PR, nessun git, una sola PUT (true / valore iniziale)
        for name, want in (("pin-on", "sha_pinning_required=true"), ("pin-off", "sha_pinning_required=false")):
            lines = modes[name]
            self.assertTrue(all(l.startswith("gh api") for l in lines), lines)
            put = [l for l in lines if "--method PUT" in l]
            self.assertEqual(len(put), 1)
            self.assertIn(want, put[0])
            self.assertIn("repos/ginz0ls/tollgate-p4-detect/actions/permissions", put[0])
        # PATCH del corpo solo in rivalutazione; merge solo in aggiorna e skip-ci, sempre --squash
        for name, lines in modes.items():
            patch = [l for l in lines if "--method PATCH" in l]
            merge = [l for l in lines if l.startswith("gh pr merge")]
            self.assertEqual(len(patch), 1 if name == "caso rivalutazione" else 0, name)
            self.assertEqual(len(merge), 1 if name in ("aggiorna", "caso skip-ci") else 0, name)
            for m in merge:
                self.assertIn("--squash", m)
        # i push: solo verso detect, un ramo alla volta; su main solo i due del caso skip-ci
        pushes = {name: [l for l in lines if l.startswith("git-net") and " push " in l] for name, lines in modes.items()}
        for name, lines in pushes.items():
            for l in lines:
                self.assertRegex(l, r" push https://github\.com/ginz0ls/tollgate-p4-detect\.git [A-Za-z0-9._/-]+$", f"{name}: {l}")
            to_main = [l for l in lines if l.endswith(" main")]
            self.assertEqual(len(to_main), 2 if name == "caso skip-ci" else 0, name)
        self.assertEqual(len(pushes["aggiorna"]), 1)
        self.assertTrue(pushes["aggiorna"][0].endswith(" tollgate-config/0.2.0"))
        self.assertEqual(len(pushes["caso rifiuto-v4"]), 1)
        self.assertRegex(pushes["caso rifiuto-v4"][0], r" p5-gate-rifiuto-v4-[0-9-]+$")
        for name in ("pin-on", "pin-off", "raccogli"):
            self.assertEqual(pushes[name], [])
        # ogni git con la rete è un clone di detect o un push
        for name, lines in modes.items():
            for l in (x for x in lines if x.startswith("git-net")):
                self.assertRegex(l, r"git-net dir=\S+ (clone -q https://github\.com/ginz0ls/tollgate-p4-detect\.git \S+|push )", f"{name}: {l}")

    def test_aggiorna_stages_only_the_proposed_files(self):
        staging = (self.tmp / "out" / "gate-aggiorna-staging.txt").read_text().splitlines()
        self.assertGreater(len(staging), 100)
        files = [line.split("\t", 1)[1] for line in staging]
        self.assertFalse([f for f in files if f.startswith("docs/")])         # la cartella della proposta non entra mai
        self.assertTrue(all(f == "tollgate.toml" or f.startswith(".github/") for f in files), [f for f in files if not f.startswith(".github/")][:5])
        self.assertIn("git -C \"$d\" add -- \"$rel\"", GATE.read_text())

    def test_rows_of_the_report(self):
        rows = (self.tmp / "out" / "gate-casi-righe.md").read_text().splitlines()
        self.assertEqual([r.split("|")[1].strip() for r in rows], ["pulita-fissata", "pulita-fissata-cache", "rifiuto-v4", "rivalutazione", "skip-ci"])
        for row in rows:
            self.assertEqual(len(row.split("|")), 9, row)           # 7 colonne come il rapporto di P4
            self.assertIn("| riuscito |", row)
            self.assertRegex(row, r"\| \d+\.\d \(\d+ run\) \|$")
        self.assertIn("Cache mode: read", rows[1])
        self.assertIn("pending -> success", rows[3])
        self.assertIn("saltato failure, normale failure, partenza success", rows[4])

    def test_every_attempt_is_recorded_with_its_exit_code(self):
        ledger = [l.split("\t") for l in (self.tmp / "out" / "gate-tentativi.tsv").read_text().splitlines()]
        by = {}
        for _, mode, rc in ledger:
            by.setdefault(mode, []).append(rc)
        self.assertEqual(by["pin-off"], ["2", "0"])
        self.assertEqual(by["caso non-esiste"], ["2"])
        self.assertEqual(by["caso skip-ci"], ["0"])
        self.assertEqual(by["caso pulita-fissata"], ["1", "0", "6"])

    def test_no_pr_is_left_open_and_the_sentinel_issue_is_left_to_the_controller(self):
        prs = json.loads((self.tmp / "fake" / "prs.json").read_text())
        self.assertEqual([p for p in prs if p["state"] == "OPEN"], [])
        self.assertEqual(sorted(p["state"] for p in prs), ["CLOSED", "CLOSED", "MERGED", "MERGED"])
        self.assertFalse((self.tmp / "fake" / "closed-90").exists())
        self.assertIn("issue di sentinella: aperta, come previsto", self.out)

    def test_every_registered_command_passes_the_p5_guard_and_nothing_is_refused(self):
        self.assertIn("righe RIFIUTATO nel registro: 0", self.out)
        self.assertIn("push forzati o con --delete nel registro: 0", self.out)
        self.assertIn("gh pr edit nel registro: 0", self.out)
        self.assertIn("guard_args: 22 fermati su 22", self.out)
        self.assertIn("comandi legittimi ammessi: 23 su 23", self.out)
        self.assertIn("git: 14 fermati su 14", self.out)
        self.assertNotIn("RIFIUTATO gh", self.log)


class IssueCreateGuardTest(unittest.TestCase):
    """Profilo p5: `issue create` ammesso solo su detect, titolo «prova P5: …», al più due per prova."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "spikes" / "gh-p4"))
        import ghguard
        cls.g = ghguard

    DET = "ginz0ls/tollgate-p4-detect"

    def v(self, *args, lenient=False):
        return self.g.violation(list(args), lenient=lenient, profile="p5")

    def test_the_allowed_forms(self):
        self.assertIsNone(self.v("issue", "create", "-R", self.DET, "--title", "prova P5: pulita-fissata", "--body", "testo"))
        os.environ["P4_OUT"] = "/tmp/o"
        try:
            self.assertIsNone(self.v("issue", "create", "--repo", self.DET, "--title", "prova P5: x", "--body-file", "/tmp/o/b.md"))
        finally:
            del os.environ["P4_OUT"]
        # nel registro comandi.log gli spazi sono andati persi
        self.assertIsNone(self.v("issue", "create", "--repo", self.DET, "--title", "prova", "P5:", "caso", "--body", "a", "b", lenient=True))

    def test_other_repos_titles_and_options_are_refused(self):
        for args in (("--repo", "ginz0ls/tollgate", "--title", "prova P5: x", "--body", "t"),
                     ("--repo", "ginz0ls/tollgate-p4-protected", "--title", "prova P5: x", "--body", "t"),
                     ("--repo", self.DET, "--title", "altro titolo", "--body", "t"),
                     ("--repo", self.DET, "--title", "prova P5:", "--body", "t"),
                     ("--repo", self.DET, "--title", "prova P5: x"),
                     ("--repo", self.DET, "--title", "prova P5: x", "--body", "t", "--body-file", "/tmp/x"),
                     ("--repo", self.DET, "--title", "prova P5: x", "--body", "t", "--assignee", "me"),
                     ("--repo", self.DET, "--title", "prova P5: x", "--body", "t", "--label", "bug"),
                     ("--repo", self.DET, "--title", "prova P5: x", "--body", "t", "--project", "p"),
                     ("--repo", self.DET, "--title", "prova P5: x", "--body", "t", "--web"),
                     ("--title", "prova P5: x", "--body", "t")):
            with self.subTest(args):
                self.assertIsNotNone(self.v("issue", "create", *args))

    def test_at_most_two_per_prova_and_the_registry_is_required(self):
        import subprocess as sp
        with tempfile.TemporaryDirectory() as d:
            reg = os.path.join(d, "prs.txt")
            env = clean_env(P4_PROFILE="p5", P5_PR_REGISTRY=reg)
            cmd = [sys.executable, "-B", "-I", str(ROOT / "spikes" / "gh-p4" / "ghguard.py"), "check", "--", "issue", "create", "--repo", self.DET,
                   "--title", "prova P5: x", "--body", "t"]
            codes = [sp.run(cmd, env=env, capture_output=True).returncode for _ in range(3)]
            self.assertEqual(codes, [0, 0, 1])
            env.pop("P5_PR_REGISTRY")
            self.assertEqual(sp.run(cmd, env=env, capture_output=True).returncode, 1)
            # `check` non scrive niente per gli altri profili e il log non conta
            self.assertEqual(open(reg).read().split(), ["issue", "issue"])


if __name__ == "__main__":
    unittest.main()
