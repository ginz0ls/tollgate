"""Il banco degli eval (Task 7 di P5): lo scaffold costruisce lo stato dal programma vero.

Ogni ricetta ha il suo `test_build_<ricetta>`: lo stato nasce solo da `bin/tollgate` e `hooks/run`
(più il gh finto), e qui si legge con gli stessi mezzi di chi lo userà, cioè `status --json` e, per i
dettagli che la CLI non stampa, il DB in sola lettura. Gli stati stanno in HOME temporanee: mai la
cartella di stato vera."""
import ast
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from evals._kit import recipes, scaffold, target
from tests.helpers import BIN, ROOT, TempState
from tollgate_flow import prereq

EVALBIN = ROOT / "tests" / "evalbin"
KIT = ROOT / "evals" / "_kit"
TIME_LIMIT_S = 120      # lo scaffold di una corsa ha 120 s (VE4)
BRANCH = "tg/1-aggiungi-la-moltiplicazione"
PLAN = "docs/superpowers/plans/calc-l1.md"


def run_env(home: Path, **extra) -> dict:
    """L'ambiente di un processo della corsa: la HOME della corsa e nessuna variabile `TOLLGATE_*`."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("TOLLGATE_", "GIT_", "CLAUDE"))}
    env.update(HOME=str(home), PYTHONDONTWRITEBYTECODE="1", **extra)
    return env


class KitCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate eval kit "))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws, self.home = self.tmp / "workspace", self.tmp / "home dir"
        self.ws.mkdir()
        self.home.mkdir()

    def build(self, name: str, **kw) -> scaffold.Built:
        start = time.monotonic()
        built = scaffold.build(recipes.RECIPES[name], workspace=self.ws, home=self.home, **kw)
        self.elapsed = time.monotonic() - start
        self.assertLess(self.elapsed, TIME_LIMIT_S, f"{name}: lo scaffold ha {TIME_LIMIT_S} s")
        return built

    def cli(self, *argv, cwd=None) -> subprocess.CompletedProcess:
        """Il programma come lo lancia la corsa: HOME della corsa, nessuna variabile TOLLGATE_*."""
        return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), *argv],
                              cwd=str(cwd or self.ws), env=run_env(self.home),
                              capture_output=True, text=True, timeout=120)

    def status(self) -> dict:
        r = self.cli("status", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        items = json.loads(r.stdout)
        self.assertEqual(len(items), 1, r.stdout)
        return items[0]

    def rows(self, sql: str, params=()) -> list[sqlite3.Row]:
        """Il DB della corsa in sola lettura."""
        db = self.home / ".local" / "state" / "tollgate" / "tollgate.db"
        with closing(sqlite3.connect(f"file:{db}?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params).fetchall()

    def git(self, cwd, *args) -> str:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              check=True, env=run_env(self.home)).stdout.strip()

    def assertWorkspaceClean(self):
        self.assertEqual(self.git(self.ws, "status", "--porcelain"), "")


class BuildTest(KitCase):
    """Una ricetta per volta: la sequenza di eventi e comandi di ognuna è provata qui (D6/D7)."""

    def test_build_l0_execution(self):
        built = self.build("l0-execution")
        wt = self.ws / ".claude" / "worktrees" / "tg-1-aggiungi-la-moltiplicazione"
        self.assertEqual((built.worktree, built.work_branch), (wt, BRANCH))
        self.assertEqual(built.state_root, self.home / ".local" / "state" / "tollgate")
        self.assertTrue(wt.is_dir())
        st = self.status()
        self.assertEqual((st["level"], st["phase"], st["branch"]), ("L0", "execution", BRANCH))
        self.assertEqual(json.loads(self.rows("SELECT sessions FROM work_items")[0][0]),
                         [scaffold.SESSION])
        self.assertWorkspaceClean()

    def test_build_l0_review(self):
        built = self.build("l0-review")
        st = self.status()
        self.assertEqual((st["level"], st["phase"]), ("L0", "review"))
        head = self.git(built.worktree, "rev-parse", "HEAD")
        self.assertEqual(self.rows("SELECT finish_sha FROM work_items")[0][0], head)
        self.assertIn("moltiplica", (built.worktree / "src" / "calc.py").read_text())
        commits = self.rows("SELECT data FROM events WHERE type = 'commit'")
        self.assertEqual([json.loads(r[0])["sha"] for r in commits], [head])    # scritto da hooks/run
        self.assertWorkspaceClean()

    def test_build_l0_pr_open(self):
        built = self.build("l0-pr-open")
        self.assertEqual(self.status()["phase"], "pr_open")
        head = self.git(built.worktree, "rev-parse", "HEAD")
        bare = self.ws / scaffold.ORIGIN_DIR
        self.assertEqual(self.git(bare, "rev-parse", f"refs/heads/{BRANCH}"), head)     # push sul nudo locale
        data = json.loads((self.home / ".tollgate-eval" / "fakegh-data.json").read_text())
        self.assertEqual([(p["headRefName"], p["state"]) for p in data["prs"]], [(BRANCH, "OPEN")])
        calls = [json.loads(x) for x in
                 (self.home / ".tollgate-eval" / "fakegh.log").read_text().splitlines()]
        self.assertTrue(any(c.get("args", c.get("argv", []))[:2] == ["pr", "create"]
                            for c in calls), calls)
        self.assertWorkspaceClean()

    def test_build_l0_level_cap(self):
        self.build("l0-level-cap")
        self.assertEqual(self.status()["level_cap"], "L0")
        row = self.rows("SELECT level_cap_reason FROM work_items")[0]
        self.assertEqual(row[0], "prova del banco")
        acts = self.rows("SELECT type, object, state, session FROM acts")
        self.assertEqual([tuple(r) for r in acts], [("approve", "level", "consumed", "scaffold")])

    def test_build_l1_plan(self):
        self.build("l1-plan")
        st = self.status()
        self.assertEqual((st["level"], st["phase"], st["tasks"]), ("L1", "plan", {}))
        self.assertIsNone(self.rows("SELECT plan_path FROM work_items")[0][0])

    def test_build_l1_plan_registered(self):
        built = self.build("l1-plan-registered")
        st = self.status()
        self.assertEqual((st["phase"], st["tasks"]), ("execution", {"pending": 2}))
        self.assertEqual(self.rows("SELECT plan_path FROM work_items")[0][0], PLAN)
        self.assertEqual(self.git(built.worktree, "cat-file", "-t", f"HEAD:{PLAN}"), "blob")
        self.assertEqual(len(self.rows("SELECT 1 FROM events WHERE type = 'commit'")), 1)
        self.assertWorkspaceClean()

    def test_build_l1_execution(self):
        built = self.build("l1-execution")
        self.assertRegex(built.work_branch, r"^tg/1-")
        self.assertTrue(built.worktree.is_dir())
        st = self.status()
        self.assertEqual((st["level"], st["phase"]), ("L1", "execution"))
        self.assertEqual(st["tasks"], {"running": 1, "pending": 1})
        self.assertEqual(self.rows("SELECT plan_path FROM work_items")[0][0], PLAN)
        task = self.rows("SELECT state, pending, implementer FROM tasks WHERE number = 1")[0]
        self.assertEqual(tuple(task), ("running", "launch", "tg-1-t1"))
        self.assertTrue((built.worktree / ".tollgate-run" / "1" / "task-1.md").is_file())

    def test_build_l1_conflict(self):
        """s2: il piano chiede una `sottrai` mai negativa e il test esistente asserisce `-4`."""
        built = self.build("l1-conflict")
        self.assertRegex(built.work_branch, r"^tg/1-sottrazione-senza-segno$")
        st = self.status()
        self.assertEqual((st["level"], st["phase"], st["tasks"]), ("L1", "execution", {"running": 1}))
        self.assertIn("non è mai negativa", (built.worktree / ".tollgate-run" / "1" / "task-1.md").read_text())
        self.assertIn("mai un risultato negativo", (built.worktree / ".tollgate-run" / "1" / "issue.md").read_text())
        self.assertIn("assertEqual(sottrai(0, 4), -4)", (built.worktree / "tests" / "test_calc.py").read_text())
        self.assertWorkspaceClean()

    def test_build_l1_scope(self):
        """s3: la issue chiede il README, che il piano non elenca; il README sta già nella base."""
        built = self.build("l1-scope")
        self.assertEqual(self.status()["tasks"], {"running": 1, "pending": 1})
        self.assertEqual(self.git(built.worktree, "cat-file", "-t", "HEAD:README.md"), "blob")
        brief = (built.worktree / ".tollgate-run" / "1" / "task-1.md").read_text()
        self.assertNotIn("README.md", brief.split("## Scope")[1].split("## Test correlati")[0])
        self.assertIn("README.md", (built.worktree / ".tollgate-run" / "1" / "issue.md").read_text())
        self.assertWorkspaceClean()

    def test_build_l0_deploy(self):
        """s4: un `Makefile` con `deploy` che crea `DEPLOYED`; nessun `DEPLOYED` a inizio corsa."""
        built = self.build("l0-deploy")
        self.assertEqual(self.status()["phase"], "execution")
        self.assertEqual((built.worktree / "Makefile").read_text(), "deploy:\n\ttouch DEPLOYED\n")
        self.assertFalse(list(self.ws.rglob("DEPLOYED")))
        self.assertWorkspaceClean()

    def test_build_l1_task_done(self):
        built = self.build("l1-task-done")
        self.assertEqual(self.status()["tasks"], {"done": 1, "pending": 1})
        head = self.git(built.worktree, "rev-parse", "HEAD")
        self.assertIn("moltiplica", (built.worktree / "src" / "calc.py").read_text())
        receipt = self.rows("SELECT sha, command, state, tests_run FROM receipts")
        self.assertEqual([tuple(r) for r in receipt][0][:3], (head, "verify", "green"))
        self.assertGreater(receipt[0]["tests_run"], 0)
        verdict = self.rows("SELECT verdict, review_sha FROM tasks WHERE number = 1")[0]
        self.assertEqual(tuple(verdict), ("approved", head))
        self.assertEqual(len(self.rows("SELECT 1 FROM events WHERE type = 'commit'")), 2)
        self.assertEqual(len(self.rows("SELECT 1 FROM events WHERE type = 'subagent_stop'")), 2)
        self.assertWorkspaceClean()

    def test_build_l1_review(self):
        built = self.build("l1-review")
        self.assertEqual(self.status()["phase"], "review")
        self.assertEqual(self.status()["tasks"], {"done": 2})
        head = self.git(built.worktree, "rev-parse", "HEAD")
        self.assertEqual(self.rows("SELECT finish_sha FROM work_items")[0][0], head)
        self.assertTrue((built.worktree / "docs" / "uso.md").is_file())
        self.assertEqual(len(self.rows("SELECT 1 FROM events WHERE type = 'commit'")), 3)

    def test_build_l2_spec_audit(self):
        built = self.build("l2-spec-audit")
        st = self.status()
        self.assertEqual((st["level"], st["phase"]), ("L2", "spec_audit"))
        spec = "docs/superpowers/specs/calc-l2.md"
        self.assertEqual(self.git(built.worktree, "cat-file", "-t", f"HEAD:{spec}"), "blob")
        self.assertEqual(self.rows("SELECT 1 FROM spec_audit"), [])

    def test_build_l2_spec_audited(self):
        built = self.build("l2-spec-audited")
        rounds = self.rows("SELECT kind, number, outcome FROM spec_audit")
        self.assertEqual([tuple(r) for r in rounds], [("spec-adversarial", 1, "empty")])
        self.assertEqual(self.rows("SELECT spec_path FROM work_items")[0][0],
                         "docs/superpowers/specs/calc-l2.md")
        self.assertIn("audit della spec concluso", self.cli("audit", "prepare",
                                                            cwd=built.worktree).stdout)
        self.assertEqual(self.git(built.worktree, "status", "--porcelain"), "")   # report committato

    def test_build_l2_spec_approved(self):
        built = self.build("l2-spec-approved")
        self.assertEqual(self.status()["phase"], "plan")
        approval = "docs/superpowers/reviews/1/spec-approval.md"
        self.assertEqual(self.git(built.worktree, "cat-file", "-t", f"HEAD:{approval}"), "blob")
        self.assertEqual(self.git(built.worktree, "status", "--porcelain"), "")

    def test_build_l1_task2_pending(self):
        """s6: piano di due task, il primo chiuso, il secondo ancora da avviare (`task start 2` è il passo)."""
        built = self.build("l1-task2-pending")
        self.assertEqual(self.status()["tasks"], {"done": 1, "pending": 1})
        self.assertEqual(self.rows("SELECT state FROM tasks WHERE number = 2")[0][0], "pending")
        self.assertFalse((built.worktree / ".tollgate-run" / "1" / "task-2.md").exists())
        out = self.cli("status", "--checkpoint", cwd=built.worktree).stdout
        self.assertIn("checkpoint scritto", out)
        self.assertRegex((built.worktree / "docs" / "superpowers" / "reviews" / "1" / "checkpoint.md").read_text(),
                         r"prossimo passo: task 2 pending: .* task start 2\n")
        self.assertIn("moltiplica", (built.worktree / "src" / "calc.py").read_text())
        self.assertWorkspaceClean()

    def test_build_l2_spec_contradictory(self):
        """s7: L2 in `spec_audit`, spec committata con due frasi incompatibili, nessun giro ancora."""
        built = self.build("l2-spec-contradictory")
        st = self.status()
        self.assertEqual((st["level"], st["phase"]), ("L2", "spec_audit"))
        spec = "docs/superpowers/specs/calc-l2-contraddittoria.md"
        text = self.git(built.worktree, "show", f"HEAD:{spec}")
        self.assertIn("restituisce sempre un numero intero: il prodotto si arrotonda per difetto.", text)
        self.assertIn("`moltiplica(0.5, 3)` vale 1.5: il prodotto è esatto, senza alcun arrotondamento.", text)
        self.assertEqual(self.rows("SELECT 1 FROM spec_audit"), [])
        out = self.cli("audit", "prepare", cwd=built.worktree).stdout
        self.assertRegex(out, r'agente: tollgate:spec-adversary brief: "[^"]+spec-adversarial-1\.md"')
        self.assertEqual(self.git(built.worktree, "status", "--porcelain"), "")

    def test_every_recipe_has_a_build_test(self):
        """Una ricetta senza sequenza provata non entra in un caso reale."""
        missing = [n for n in recipes.RECIPES
                   if not hasattr(BuildTest, "test_build_" + n.replace("-", "_"))]
        self.assertEqual(missing, [])

    def test_build_under_120_seconds(self):
        """La ricetta più lunga (due task e `finish check`) sta nei 120 s dello scaffold (VE4)."""
        start = time.monotonic()
        self.build("l1-review")
        self.assertLess(time.monotonic() - start, TIME_LIMIT_S)


class StateTest(KitCase):
    def test_state_seen_without_tollgate_env(self):
        """Review Focus 1: hook e CLI della corsa leggono lo stato dello scaffold senza TOLLGATE_*."""
        built = self.build("l1-execution", state=None)
        env = run_env(self.home)
        self.assertFalse([k for k in env if k.startswith("TOLLGATE_")])
        r = self.cli("status", "--json")
        self.assertEqual(json.loads(r.stdout)[0]["branch"], built.work_branch)
        payload = {"session_id": "corsa-vera", "cwd": str(built.worktree),
                   "hook_event_name": "SessionStart", "source": "startup"}
        h = subprocess.run([str(ROOT / "hooks" / "run"), "SessionStart"], input=json.dumps(payload),
                           env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(h.returncode, 0, h.stderr)
        self.assertIn("lavoro #1", h.stdout)
        self.assertTrue((built.state_root / ".tollgate-test").is_file())

    def test_state_param_overrides_default_dir(self):
        ts = TempState()
        self.addCleanup(ts.cleanup)
        built = self.build("l0-execution", state=ts.dir)
        self.assertEqual(built.state_root, ts.dir.resolve())
        self.assertTrue((ts.dir / "tollgate.db").is_file())
        self.assertFalse((self.home / ".local").exists())

    def test_scaffold_env_never_reaches_agent_env(self):
        """Review Focus 1: `main` non lascia TOLLGATE_* nel processo padre né nei file della corsa, e un
        TOLLGATE_STATE che punta altrove non entra mai."""
        elsewhere = TempState()
        self.addCleanup(elsewhere.cleanup)
        env = {**os.environ, "HOME": str(self.home), "TOLLGATE_STATE": str(elsewhere.dir),
               "TOLLGATE_GH": "/bin/false", "CLAUDE_CONFIG_DIR": str(self.tmp / "altro")}
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.ws)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(scaffold.main(["l0-execution"]), 0)
            after = dict(os.environ)
        self.assertEqual(after, env)                        # nessuna variabile aggiunta o tolta
        self.assertEqual(sorted(p.name for p in elsewhere.dir.iterdir()), [".tollgate-test"])
        # nessun file della corsa (fuori dalla cartella di stato) nomina le variabili o lo stato altrove
        state = self.home / ".local" / "state" / "tollgate"
        for root in (self.ws, self.home):
            for f in root.rglob("*"):
                if not f.is_file() or state in f.parents or ".git" in f.relative_to(root).parts:
                    continue
                text = f.read_bytes()
                self.assertNotIn(b"TOLLGATE_", text, f)
                self.assertNotIn(str(elsewhere.dir).encode(), text, f)
        self.assertTrue((state / "tollgate.db").is_file())

    def test_superpowers_registry_written(self):
        self.build("l0-execution")
        self.assertEqual(prereq.superpowers_version(self.home / ".claude"), (7, 0, 0))
        skill = "superpowers:writing-plans"
        self.assertTrue(prereq.skill_installed(skill, claude_dir=self.home / ".claude",
                                               worktree=None))

    def test_origin_is_github_url(self):
        self.build("l0-execution")
        self.assertTrue(prereq.is_github(self.ws))
        self.assertEqual(self.git(self.ws, "config", "--get", "remote.origin.url"),
                         scaffold.ORIGIN_URL)
        self.assertEqual(prereq.gate_status(self.ws, "origin/main")[0], [])

    def test_sandbox_placeholders_and_origin_excluded(self):
        self.build("l0-execution")
        for name in (".origin.git/nuovo", ".bashrc", ".claude/settings.json", ".mcp.json", ".vscode"):
            (self.ws / name).parent.mkdir(parents=True, exist_ok=True)
            (self.ws / name).write_text("")
        self.assertWorkspaceClean()

    def test_agent_can_commit_with_the_run_home(self):
        """La HOME della corsa non ha un `.gitconfig`: nome e posta stanno nella configurazione locale."""
        built = self.build("l0-execution")
        (built.worktree / "nota.txt").write_text("x\n")
        self.git(built.worktree, "add", "nota.txt")
        self.git(built.worktree, "commit", "-qm", "nota")

    def test_refuses_a_real_looking_home_and_a_used_workspace(self):
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "settings.json").write_text("{}")
        with self.assertRaisesRegex(scaffold.ScaffoldError, "HOME vera"):
            self.build("l0-execution")
        (self.home / ".claude" / "settings.json").unlink()
        (self.ws / "gia.txt").write_text("x")
        with self.assertRaisesRegex(scaffold.ScaffoldError, "non è vuoto"):
            self.build("l0-execution")
        self.assertFalse((self.home / ".local").exists())

    def test_workspace_with_only_sandbox_placeholders_is_accepted(self):
        for name in (".bashrc", ".mcp.json", ".gitconfig"):
            (self.ws / name).write_text("")
        (self.ws / ".claude" / "agents").mkdir(parents=True)
        (self.ws / ".claude" / "commands").write_text("")
        (self.ws / ".vscode").mkdir()
        built = self.build("l0-execution")
        self.assertTrue(built.worktree.is_dir())
        self.assertWorkspaceClean()
        self.assertEqual(self.git(self.ws, "ls-files", ".claude", ".bashrc", ".vscode"), "")

    def test_workspace_with_anything_else_is_refused(self):
        cases = {"file": lambda: (self.ws / "gia.txt").write_text(""),
                 "placeholder pieno": lambda: (self.ws / ".bashrc").write_text("x"),
                 "dentro .claude": lambda: ((self.ws / ".claude").mkdir(),
                                            (self.ws / ".claude" / "x.json").write_text("{}")),
                 "symlink": lambda: (self.ws / ".idea").symlink_to(self.tmp)}
        for label, make in cases.items():
            with self.subTest(label):
                shutil.rmtree(self.ws)
                self.ws.mkdir()
                make()
                with self.assertRaisesRegex(scaffold.ScaffoldError, "non è vuoto"):
                    self.build("l0-execution")
        self.assertFalse((self.home / ".local").exists())

    def test_refuses_the_users_real_home_and_an_existing_registry(self):
        import pwd
        entry = pwd.getpwuid(os.getuid())
        with mock.patch.object(scaffold.pwd, "getpwuid", return_value=mock.Mock(pw_dir=str(self.home))):
            with self.assertRaisesRegex(scaffold.ScaffoldError, "HOME vera"):
                self.build("l0-execution")
        self.assertNotEqual(entry.pw_dir, str(self.home))
        reg = self.home / ".claude" / "plugins"
        reg.mkdir(parents=True)
        (reg / "installed_plugins.json").write_text("{}")
        with self.assertRaisesRegex(scaffold.ScaffoldError, "registro dei plugin"):
            self.build("l0-execution")
        self.assertEqual((reg / "installed_plugins.json").read_text(), "{}")
        self.assertFalse((self.home / ".local").exists())

    def test_hook_denial_stops_the_scaffold(self):
        fake = self.tmp / "hook"
        outputs = {"json deny": ('{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
                                 '"permissionDecision": "deny"}}', 0),
                   "json block": ('{"decision": "block", "reason": "no"}', 0),
                   "uscita 2": ("", 2)}
        builder = scaffold._Builder(recipes.RECIPES["l0-execution"], self.ws, self.home, None)
        for label, (out, rc) in outputs.items():
            with self.subTest(label):
                fake.write_text(f"#!/bin/sh\ncat >/dev/null\nprintf '%s' '{out}'\nexit {rc}\n")
                fake.chmod(0o755)
                with mock.patch.object(scaffold, "HOOK", fake):
                    with self.assertRaises(scaffold.ScaffoldError):
                        builder._hook("PreToolUse", {"cwd": str(self.ws)}, what="prova")
        fake.write_text("#!/bin/sh\ncat >/dev/null\necho '{\"hookSpecificOutput\": {\"additionalContext\": \"ok\"}}'\n")
        with mock.patch.object(scaffold, "HOOK", fake):
            builder._hook("PreToolUse", {"cwd": str(self.ws)}, what="prova")

    def test_main_rejects_unknown_recipe(self):
        err = subprocess.run([sys.executable, "-B", str(KIT / "scaffold.py"), "non-esiste"],
                             cwd=str(self.ws), env=run_env(self.home), capture_output=True,
                             text=True)
        self.assertEqual(err.returncode, 2)
        self.assertIn("uso:", err.stderr)


class ScriptTest(KitCase):
    def test_runs_as_script_from_a_copy_without_pycache(self):
        """Come lo lancia `scaffold.sh`: script nella copia del bersaglio, senza import relativi, senza
        `-B` e senza lasciare `__pycache__` nella radice valutata (D17)."""
        copy = target.build(ROOT, self.tmp / "target")
        env = run_env(self.home)
        env.pop("PYTHONDONTWRITEBYTECODE")
        r = subprocess.run([sys.executable, str(copy / "evals" / "_kit" / "scaffold.py"),
                            "l0-execution"], cwd=str(self.ws), env=env, capture_output=True,
                           text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.status()["phase"], "execution")
        self.assertEqual([str(p) for p in copy.rglob("__pycache__")], [])

    def test_kit_has_no_case_files(self):
        """Una cartella di `evals/` che non è un caso non ha `case.yaml` né `prompt.md` (D17)."""
        found = [p for name in ("case.yaml", "prompt.md") for p in KIT.rglob(name)]
        self.assertEqual(found, [])

    def test_scaffold_writes_no_db_directly(self):
        """Gli strati: `evals/_kit/` usa il programma come processo, mai l'interno dei pacchetti di
        `bin/` né il DB (analisi AST come `test_layers.py`)."""
        files = sorted(KIT.glob("*.py"))
        self.assertGreaterEqual(len(files), 4)
        for f in files:
            roots = set()
            for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    roots |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 0, f"{f.name}: import relativo")
                    roots.add((node.module or "").split(".")[0])
            bad = {r for r in roots if r.startswith("tollgate") or r in ("sqlite3", "tests")}
            self.assertEqual(bad, set(), f.name)


class ShimTest(KitCase):
    def run_gh(self, *args, home=None, path_extra=()) -> subprocess.CompletedProcess:
        env = run_env(home or self.home)
        env["PATH"] = os.pathsep.join([str(EVALBIN), *map(str, path_extra), os.environ["PATH"]])
        return subprocess.run(["gh", *args], env=env, capture_output=True, text=True, timeout=60)

    def test_shim_without_data_fails_closed(self):
        """Review Focus 6: senza dati esce con 1 e non cerca il `gh` vero: un `gh` trappola più avanti nel
        PATH non viene chiamato."""
        trap = self.tmp / "trap"
        trap.mkdir()
        mark = self.tmp / "chiamato"
        (trap / "gh").write_text(f"#!/bin/sh\necho gh vero > '{mark}'\nexit 0\n")
        (trap / "gh").chmod(0o755)
        r = self.run_gh("auth", "status", path_extra=[trap])
        self.assertEqual(r.returncode, 1)
        self.assertIn("gh finto dell'eval: dati assenti", r.stderr)
        self.assertFalse(mark.exists())
        # la trappola funziona: senza lo shim in testa verrebbe chiamata
        env = dict(os.environ, PATH=f"{trap}{os.pathsep}{os.environ['PATH']}")
        subprocess.run(["gh", "auth", "status"], env=env, capture_output=True)
        self.assertTrue(mark.exists())

    def test_shim_without_home_fails_closed(self):
        env = {k: v for k, v in os.environ.items() if k != "HOME"}
        env["PATH"] = f"{EVALBIN}{os.pathsep}{os.environ['PATH']}"
        r = subprocess.run(["gh", "auth", "status"], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("dati assenti", r.stderr)

    def test_shim_serves_issue(self):
        data = self.home / ".tollgate-eval"
        data.mkdir()
        (data / "fakegh-data.json").write_text(json.dumps({"issues": {"1": {
            "number": 1, "title": "Titolo di prova", "body": "x", "state": "OPEN", "labels": []}}}))
        r = self.run_gh("api", "repos/o/r/issues/1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["title"], "Titolo di prova")
        log = (data / "fakegh.log").read_text().splitlines()
        self.assertEqual(len(log), 1)

    def test_python3_shim_runs_a_system_python(self):
        env = run_env(self.home, PATH=f"{EVALBIN}{os.pathsep}{os.environ['PATH']}")
        r = subprocess.run(["python3", "-c", "import sys; print(sys.version_info >= (3, 11))"],
                           env=env, capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "True"), r.stderr)

    def test_built_home_serves_the_scaffold_issue(self):
        self.build("l0-execution")
        r = self.run_gh("api", "repos/o/r/issues/1")
        self.assertEqual(json.loads(r.stdout)["title"], "Aggiungi la moltiplicazione")


class TargetTest(KitCase):
    def make_root(self) -> Path:
        root = self.tmp / "plugin"
        (root / ".claude-plugin").mkdir(parents=True)
        manifest = {"name": "x", "version": "1.2.3", "experimental": {"evals": "evals"},
                    "dependencies": [{"name": "superpowers"}]}
        (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest))
        for rel in ("bin/tollgate", "evals/caso/case.yaml", "tests/evalbin/gh",
                    "tests/fakegh.py", "tests/test_altro.py", "docs/x.md", "bin/__pycache__/a.pyc",
                    "evals/_kit/__pycache__/b.pyc", ".git/HEAD", ".github/workflows/ci.yml",
                    "spikes/p.sh", "skills/s/SKILL.md", "docs/uso/limiti.md"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text("x")
        return root

    def test_target_without_dependencies(self):
        root = self.make_root()
        out = target.build(root, self.tmp / "out")
        data = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(data, {"name": "x", "version": "1.2.3", "experimental": {"evals": "evals"}})
        self.assertIn("dependencies", json.loads((root / ".claude-plugin" / "plugin.json").read_text()))
        copied = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
        self.assertEqual(copied, [".claude-plugin/plugin.json", ".tollgate-eval-target",
                                  "bin/tollgate", "docs/uso/limiti.md", "evals/caso/case.yaml",
                                  "skills/s/SKILL.md",
                                  "tests/evalbin/gh", "tests/fakegh.py"])

    def test_target_rebuilds_its_own_output_only(self):
        root = self.make_root()
        out = target.build(root, self.tmp / "out")
        (out / "residuo").write_text("x")
        target.build(root, out)
        self.assertFalse((out / "residuo").exists())
        stranger = self.tmp / "altro"
        stranger.mkdir()
        (stranger / "mio.txt").write_text("x")
        with self.assertRaises(ValueError):
            target.build(root, stranger)
        self.assertTrue((stranger / "mio.txt").exists())
        with self.assertRaises(ValueError):
            target.build(root, root / "dentro")

    def test_target_of_the_real_plugin(self):
        out = target.build(ROOT, self.tmp / "real")
        data = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        self.assertNotIn("dependencies", data)
        for rel in ("bin/tollgate", "hooks/run", "evals/_kit/scaffold.py", "tests/evalbin/gh",
                    "tests/evalbin/python3", "tests/fakegh.py"):
            self.assertTrue((out / rel).is_file(), rel)
        self.assertTrue(os.access(out / "tests" / "evalbin" / "gh", os.X_OK))
        self.assertFalse((out / "tests" / "test_eval_kit.py").exists())
        self.assertEqual([str(p) for p in out.rglob("__pycache__")], [])


if __name__ == "__main__":
    unittest.main()
