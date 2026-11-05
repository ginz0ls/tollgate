"""Lo script della prova vera di B3-bis (Task 7) e il suo progetto di prova, provati senza rete: `bash -n`, i modi `controlla` e
`prepara`, e `prova` con un `tollgate` finto (`B3BIS_TOLLGATE`) che scrive un file segnale. Eccezione approvata per questi test
(global-constraints): il figlio parte da `os.environ` senza le variabili delle chiavi, con al più una chiave finta. Nessun socket,
nessun `claude`, nessuna chiave vera. Le cartelle di lavoro stanno in `/tmp/tollgate-b3bis-test-*` e si tolgono alla fine."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import MODEL_KEY_VARS, ROOT

B3BIS = ROOT / "spikes" / "b3bis"
SCRIPT = B3BIS / "models-prova.sh"
PROJECT = B3BIS / "progetto"
FAKE_KEY = "sk-PROVA-123"
FAKE_TOLLGATE = """import json, os, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
with open(here / "segnale", "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "state": os.environ.get("TOLLGATE_STATE")}) + "\\n")
var = os.environ.get("B3BIS_FAKE_PRINT")
if var:
    print("chiave: " + os.environ.get(var, ""))
print("modelli: nessun avviso")
"""


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in MODEL_KEY_VARS and not k.startswith(("B3BIS_", "TOLLGATE_", "GIT_"))}
    env.update(extra)
    return env


class Bench(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="tollgate-b3bis-test-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.work = self.dir / "w"
        self.fake = self.dir / "tollgate-finto.py"
        self.fake.write_text(FAKE_TOLLGATE)

    def env(self, **extra):
        base = dict(B3BIS_DIR=str(self.work), B3BIS_PY=sys.executable, B3BIS_TOLLGATE=str(self.fake),
                    HOME=str(self.dir / "home"))
        base.update(extra)
        return clean_env(**base)

    def run_script(self, *args, env=None):
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, timeout=120,
                              env=env if env is not None else self.env(), cwd=str(self.dir))

    def signals(self):
        path = self.dir / "segnale"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]


class ScriptTest(Bench):
    def test_script_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_progetto_toml_is_valid(self):
        from tollgate_core import config
        cfg = config.load_config_text((PROJECT / "tollgate.toml").read_text())
        self.assertEqual(cfg.get("models.files"), ["ai/models.py"])
        self.assertEqual(cfg.get("gate.mode"), "detect")
        self.assertEqual(cfg.warnings, [])
        self.assertTrue((PROJECT / "ai" / "models.py").is_file())

    def test_controlla_mode_no_network(self):
        r = self.run_script("controlla", env=self.env(ANTHROPIC_API_KEY=FAKE_KEY, GEMINI_API_KEY=""))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CONTROLLA: ok", r.stdout)
        self.assertNotIn(FAKE_KEY, r.stdout + r.stderr)
        for name in MODEL_KEY_VARS:
            self.assertIn(f"  chiave {name}", r.stdout)
        self.assertRegex(r.stdout, r"chiave ANTHROPIC_API_KEY: impostata")
        self.assertRegex(r.stdout, r"chiave GEMINI_API_KEY: non impostata")
        self.assertRegex(r.stdout, r"chiave OPENAI_API_KEY: non impostata")
        self.assertFalse(self.work.exists(), "controlla non scrive")
        self.assertEqual(self.signals(), [])

    def test_controlla_fails_without_interpreter(self):
        r = self.run_script("controlla", env=self.env(B3BIS_PY="python-che-non-esiste-3.99"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("CONTROLLA: FALLITO", r.stdout)

    def test_prepara_builds_repo_with_origin(self):
        r = self.run_script("prepara")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        repo, bare = self.work / "repo", self.work / "origin.git"
        self.assertTrue((self.work / "state" / ".tollgate-test").is_file())

        def git(*a, cwd=repo):
            return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True, check=True,
                                  env=clean_env(HOME=str(self.dir / "home"))).stdout.strip()

        self.assertEqual(git("remote", "get-url", "origin"), str(bare))
        tree = git("ls-tree", "-r", "--name-only", "origin/main").splitlines()
        self.assertIn("tollgate.toml", tree)
        self.assertIn("ai/models.py", tree)
        self.assertEqual(git("rev-parse", "HEAD"), git("rev-parse", "origin/main"))
        self.assertEqual(git("rev-parse", "main", cwd=bare), git("rev-parse", "HEAD"))
        self.assertEqual(git("status", "--porcelain"), "")
        self.assertEqual(git("config", "user.name"), "prova")
        self.assertEqual((repo / "ai" / "models.py").read_text(), (PROJECT / "ai" / "models.py").read_text())
        self.assertEqual(self.signals(), [])

    def test_prepara_keeps_previous_work(self):
        self.assertEqual(self.run_script("prepara").returncode, 0)
        (self.work / "repo" / "nota.txt").write_text("x")
        r = self.run_script("prepara")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.work / "repo" / "nota.txt").exists())
        moved = [p for p in self.work.glob("repo.prev-*") if (p / "nota.txt").exists()]
        self.assertEqual(len(moved), 1)

    def test_dir_must_be_under_allowed_roots(self):
        tag = self.dir.name
        bad = ["/var/tmp/" + tag, "/tmp/altro-" + tag, str(self.dir) + "/../y-" + tag, "relativa/" + tag,
               "/tmp/tollgate-b3bis-test-", "/tmp/tollgate-b3bisx"]
        for d in bad:
            for mode in ("controlla", "prepara", "prova"):
                with self.subTest(dir=d, mode=mode):
                    r = self.run_script(mode, env=self.env(B3BIS_DIR=d))
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn("B3BIS_DIR", r.stderr)
        for d in ("/var/tmp/" + tag, "/tmp/altro-" + tag, "/tmp/y-" + tag, "/tmp/tollgate-b3bisx"):
            self.assertFalse(Path(d).exists(), d)
        self.assertEqual(self.signals(), [])
        self.assertFalse(Path("relativa").exists() or (self.dir / "relativa").exists())

    def test_dir_rejects_symlinks_and_deep_paths(self):
        target = self.dir / "altro"
        target.mkdir()
        (self.dir / "lnk").symlink_to(target)
        top = Path(tempfile.mkdtemp(prefix="tollgate-b3bis-test-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, top, True)
        toplink = Path("/tmp") / (top.name + "-lnk")
        toplink.symlink_to(top)
        self.addCleanup(toplink.unlink)
        (top / "w").mkdir()
        (top / "alias").symlink_to(top / "w")
        bad = [self.dir / "lnk", self.dir / "lnk" / "x", toplink / "w", top / "alias", self.dir / "a" / "b"]
        for d in bad:
            for mode in ("controlla", "prepara", "prova"):
                with self.subTest(dir=str(d), mode=mode):
                    r = self.run_script(mode, env=self.env(B3BIS_DIR=str(d)))
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn("B3BIS_DIR", r.stderr)
        self.assertEqual(list(target.iterdir()), [])
        self.assertEqual(list((top / "w").iterdir()), [])
        self.assertFalse((self.dir / "a").exists())

    def test_out_and_state_are_private(self):
        self.assertEqual(self.run_script("prepara").returncode, 0)
        self.assertEqual(self.run_script("prova").returncode, 0)
        for name in ("state", "out"):
            self.assertEqual((self.work / name).stat().st_mode & 0o077, 0, name)
        for f in (self.work / "out").iterdir():
            self.assertEqual(f.stat().st_mode & 0o077, 0, f.name)

    def test_prova_in_test_dir_needs_fake_tollgate(self):
        self.assertEqual(self.run_script("prepara").returncode, 0)
        env = self.env()
        del env["B3BIS_TOLLGATE"]
        r = self.run_script("prova", env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("B3BIS_TOLLGATE", r.stderr)
        self.assertFalse((self.work / "out").exists())
        r = self.run_script("prova", env=self.env(B3BIS_TOLLGATE=str(self.dir / "non-esiste.py")))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.work / "out").exists())
        self.assertEqual(self.signals(), [])

    def test_prova_needs_prepara(self):
        r = self.run_script("prova")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.signals(), [])

    def test_prova_runs_twice_refresh_first(self):
        self.assertEqual(self.run_script("prepara").returncode, 0)
        r = self.run_script("prova")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sig = self.signals()
        self.assertEqual([s["argv"] for s in sig], [["models", "check", "--refresh"], ["models", "check"]])
        for s in sig:
            self.assertEqual(Path(s["cwd"]).resolve(), (self.work / "repo").resolve())
            self.assertEqual(s["state"], str(self.work / "state"))
        outs = sorted(p.name for p in (self.work / "out").iterdir())
        self.assertEqual(len(outs), 2, outs)
        for p in (self.work / "out").iterdir():
            self.assertIn("modelli: nessun avviso", p.read_text())

    def test_prova_output_checked_for_keys(self):
        self.assertEqual(self.run_script("prepara").returncode, 0)
        env = self.env(ANTHROPIC_API_KEY=FAKE_KEY, B3BIS_FAKE_PRINT="ANTHROPIC_API_KEY")
        r = self.run_script("prova", env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(len(self.signals()), 1, "il finto è girato e lo script si è fermato")
        self.assertNotIn(FAKE_KEY, r.stdout + r.stderr)
        self.assertIn("ERRORE: l'uscita contiene il valore di una variabile di chiave (ANTHROPIC_API_KEY): non salvata",
                      r.stderr)
        for f in self.work.rglob("*"):
            if f.is_file() and not f.is_relative_to(self.work / "repo" / ".git"):
                self.assertNotIn(FAKE_KEY.encode(), f.read_bytes(), str(f))
        saved = list((self.work / "out").glob("*")) if (self.work / "out").exists() else []
        self.assertEqual(saved, [])
        # una variabile impostata ma vuota si salta, come in api_key
        env = self.env(ANTHROPIC_API_KEY="", B3BIS_FAKE_PRINT="ANTHROPIC_API_KEY")
        r = self.run_script("prova", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(list((self.work / "out").iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
