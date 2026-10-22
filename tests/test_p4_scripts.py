"""Gli script della prova reale (Task 1 e Task 16), provati senza rete: `bash -n` e il modo `controlla`, che gira su repo
nudi locali con un `gh` finto davanti nel PATH e passa ogni `gh` da `ghguard.py`. Nessun `claude`, nessun GitHub."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

SPIKES = ROOT / "spikes"
SCRIPTS = [SPIKES / "run-p4-gate.sh", SPIKES / "run-p4-flow.sh", SPIKES / "gh-p4" / "run-p4-checks.sh",
           SPIKES / "gh-p4" / "common.sh", SPIKES / "gh-p4" / "fakegh.sh", SPIKES / "gh-p4" / "bin" / "gh"]
# una scelta dei casi per il controllo del gate: ogni famiglia di operazioni (PR semplice, due push, due PR, ramo `other`,
# stato con il token personale, merge, push diretto) senza rifare i 37 casi
GATE_CASES = "verde-pulita verde-edit error-sha-superato error-due-pr non-applicabile token-personale detect-merge-rosso detect-push-diretto"


class ScriptsTest(unittest.TestCase):
    def test_syntax(self):
        for script in SCRIPTS:
            with self.subTest(script.name):
                r = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_claude_p_only_in_the_flow_script(self):
        for script in [SPIKES / "run-p4-gate.sh", SPIKES / "run-p4-flow.sh", *sorted((SPIKES / "gh-p4").glob("*.sh"))]:
            text = script.read_text()
            if script.name == "run-p4-flow.sh":
                self.assertEqual(len(re.findall(r"(?m)^\s*cmd=\(claude -p ", text)), 1)
                self.assertIn("--plugin-dir", text)
                continue
            with self.subTest(script.name):
                self.assertNotRegex(text, r"claude\s+-p\b")

    def test_no_script_deletes_the_evidence_folders(self):
        for name in ("run-p4-gate.sh", "run-p4-flow.sh"):
            text = re.sub(r'DISALLOWED="(?:[^"\\]|\\.)*"', "", (SPIKES / name).read_text(), flags=re.S)   # i divieti per il modello nominano push --force
            with self.subTest(name):
                self.assertNotRegex(text, r"\brm\s+-[a-zA-Z]*r")
                self.assertNotRegex(text, r"\b(pkill|killall)\b")
                self.assertNotRegex(text, r"--force|push\s+(-f|--force)|--no-verify|reset --hard")


class GiroUnoTest(unittest.TestCase):
    def test_public_confirmation_does_not_depend_on_p4_check(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-p4-conferma-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("P4_", "TOLLGATE_"))}
        env.update(P4_CHECK="1", P4_OUT=str(tmp / "out"), P4_WORK=str(tmp / "work"))
        r = subprocess.run(["bash", str(SPIKES / "run-p4-gate.sh"), "installa", "protected"], capture_output=True,
                           text=True, env=env, timeout=60)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("diventa pubblico", r.stderr)
        self.assertFalse((tmp / "work" / "protected").exists())

    def test_baseline_output_is_rotated(self):
        text = (SPIKES / "run-p4-gate.sh").read_text()
        self.assertRegex(text, r'rot "\$OUT/installa-\$n-baseline-file\.txt"\n\s+python3 -B "\$P4/make_case\.py" baseline')

    def test_flow_outputs_all_pass_through_rotation(self):
        text = (SPIKES / "run-p4-flow.sh").read_text()
        for name in ("events.jsonl", "events.err", "stats.err", "hooks.log", "skipped.log", "audit.txt"):
            self.assertIn(f'"$LOGS/{name}"', text.split("modo_registra()")[1].split("rot ")[1].split("\n\n")[0], name)

    def test_the_flow_forbids_forced_pushes_and_gh_by_path(self):
        text = (SPIKES / "run-p4-flow.sh").read_text()
        for rule in ("git push --force:", "git push -f:", "git push origin main:", "*/gh:", "command gh:", "env:", "P4_PROFILE=:"):
            self.assertIn(f"Bash({rule}*)", text)
        self.assertNotIn('P4_REPO="$PROT" P4_PROFILE', text)     # profilo e repo non passano dall'ambiente del passo


class StateVerificationTest(unittest.TestCase):
    def test_every_claude_step_is_wrapped_by_the_state_verification(self):
        text = (SPIKES / "run-p4-flow.sh").read_text()
        step = text.split("claude_step() {")[1].split("\n}\n")[0]
        self.assertLess(step.index('state_snapshot "$id" prima'), step.index("timeout "))
        self.assertLess(step.index("timeout "), step.index('state_snapshot "$id" dopo'))
        self.assertIn('state_compare "$id" || return 3', step)
        self.assertEqual(text.count("P4_CHECK_TAMPER"), 2)          # letta solo in check_canned, usata da controlla

    def test_tamper_switch_exists_only_inside_check_canned(self):
        text = (SPIKES / "run-p4-flow.sh").read_text()
        body = text.split("check_canned() {")[1].split("\nwrite_fake_gh")[0]
        self.assertIn('${P4_CHECK_TAMPER:-}', body)
        self.assertNotIn("P4_CHECK_TAMPER", text.split("check_canned() {")[0])


class ControllaTest(unittest.TestCase):
    def run_controlla(self, script: Path, **env) -> str:
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-p4-controlla-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        e = {k: v for k, v in os.environ.items() if not k.startswith(("P4_", "TOLLGATE_"))}
        e.update(P4_CHECK_DIR=str(tmp), **env)
        r = subprocess.run(["bash", str(script), "controlla"], capture_output=True, text=True, env=e, timeout=900)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-2000:])
        self.assertNotIn("VIOLAZIONE", r.stdout)
        self.assertNotIn("FALLITO", r.stdout)
        return r.stdout

    def test_task1_script_still_passes_after_the_common_library(self):
        out = self.run_controlla(SPIKES / "gh-p4" / "run-p4-checks.sh")
        self.assertIn("CONTROLLA: ok", out)

    def test_gate_script_controlla(self):
        out = self.run_controlla(SPIKES / "run-p4-gate.sh", P4_CHECK_CASES=GATE_CASES)
        self.assertIn("CONTROLLA: ok", out)
        self.assertIn("modo installa-protected: ok", out)
        self.assertIn("modo installa-detect: ok", out)
        self.assertIn("modo protezione: ok", out)
        for name in GATE_CASES.split():
            self.assertIn(f"modo caso-{name}: ok", out)
        self.assertIn("non riuscite: 0", out)
        self.assertIn("righe RIFIUTATO nel registro: 0", out)
        self.assertIn('{"app_ids":[15368,15368],"strict":true}', out)

    def test_flow_script_controlla(self):
        out = self.run_controlla(SPIKES / "run-p4-flow.sh")
        self.assertIn("CONTROLLA: ok", out)
        for mode in ("prepara", "shim", "passo1", "passo2", "passo3", "attendi", "passo4", "registra"):
            self.assertIn(f"modo {mode}: ok", out)
        self.assertIn("uguali: sì", out)
        self.assertIn("esito: riuscito", out)
        self.assertIn("vietato\tgh issue create", out)
        for kind in ("hash", "log", "main", "ref"):
            self.assertIn(f"manomissione {kind}: rilevata", out)


if __name__ == "__main__":
    unittest.main()
