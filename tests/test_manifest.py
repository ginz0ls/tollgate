import ast
import json
import os
import re
import unittest

from tests.helpers import ROOT

ATTRIBUTION = ("Derivato da superpowers/skills/subagent-driven-development (MIT, © 2025 Jesse "
               "Vincent); vedi LICENSES/superpowers-MIT.txt")

FINAL_ATTRIBUTION = ("Derivato da superpowers/skills/requesting-code-review (MIT, © 2025 Jesse "
                     "Vincent); vedi LICENSES/superpowers-MIT.txt")


def frontmatter(path) -> dict[str, str]:
    """Parser minimo del frontmatter: solo righe `chiave: valore`."""
    lines = path.read_text().split("\n")
    assert lines[0] == "---", f"{path}: frontmatter assente"
    out = {}
    for line in lines[1:]:
        if line == "---":
            return out
        key, _, value = line.partition(": ")
        out[key] = value.strip().strip('"')
    raise AssertionError(f"{path}: frontmatter non chiuso")


class ManifestTest(unittest.TestCase):
    def test_hooks_json(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptExpansion", "UserPromptSubmit",
                                      "PreToolUse", "PostToolUse", "PostToolUseFailure",
                                      "SubagentStart", "SubagentStop"})
        pre = hooks["PreToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "Agent", "SendMessage"):
            self.assertRegex(tool, f"^(?:{pre})$")
        self.assertRegex("mcp__srv__x", f"^(?:{pre})$")
        self.assertNotRegex("Read", f"^(?:{pre})$")
        post = hooks["PostToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "Bash", "Agent", "Skill", "SubagentHandback"):
            self.assertRegex(tool, f"^(?:{post})$")
        fail = hooks["PostToolUseFailure"][0]["matcher"]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash"):
            self.assertRegex(tool, f"^(?:{fail})$")
        for tool in ("Read", "Agent", "Skill"):
            self.assertNotRegex(tool, f"^(?:{fail})$")
        self.assertNotIn("matcher", hooks["UserPromptSubmit"][0])
        for event, groups in hooks.items():
            for h in groups[0]["hooks"]:
                self.assertEqual(h["command"], f'"${{CLAUDE_PLUGIN_ROOT}}/hooks/run" {event}')
                self.assertEqual(h["timeout"], 90)

    def test_plugin_json(self):
        p = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(p["name"], "tollgate")
        from tollgate_core import VERSION
        self.assertEqual(p["version"], VERSION)
        dep = p["dependencies"][0]
        self.assertEqual((dep["name"], dep["marketplace"]),
                         ("superpowers", "claude-plugins-official"))
        self.assertNotIn("version", dep)

    def test_off_on_skills_user_only(self):
        for name in ("off", "on"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
            self.assertRegex(text, rf"(?m)^name: {name}$")

    def test_agents_frontmatter(self):
        impl = ROOT / "agents" / "implementer.md"
        fm = frontmatter(impl)
        self.assertEqual(fm["name"], "implementer")
        self.assertEqual(fm["model"], "inherit")
        self.assertEqual(fm["maxTurns"], "60")
        self.assertEqual([t.strip() for t in fm["tools"].split(",")],
                         ["Read", "Edit", "Write", "Bash", "Grep", "Glob", "Skill"])
        self.assertTrue(fm["description"])
        rev = ROOT / "agents" / "task-reviewer.md"
        fm = frontmatter(rev)
        self.assertEqual(fm["name"], "task-reviewer")
        self.assertEqual(fm["model"], "sonnet")
        tools = [t.strip() for t in fm["tools"].split(",")]
        self.assertEqual(tools, ["Read", "Grep", "Glob", "Bash"])
        self.assertNotIn("Edit", tools)
        self.assertNotIn("Write", tools)
        for path in (impl, rev):
            self.assertIn(ATTRIBUTION, path.read_text())

    def test_user_only_skills(self):
        for name in ("approve", "resolve", "setup", "off", "on"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^disable-model-invocation: true$", name)
            self.assertRegex(text, rf"(?m)^name: {name}$")
        for name in ("start", "execute", "status"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertNotIn("disable-model-invocation", text, name)
            self.assertRegex(text, rf"(?m)^name: {name}$")
            self.assertRegex(text, r"(?m)^description: \S")

    def test_skills_use_quoted_program(self):
        for name in ("start", "execute", "status", "approve", "resolve", "setup"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"', text, name)
            self.assertNotIn('"<programma>"', text, name)
            self.assertIn("python3.11", text, name)
            self.assertNotIn("indica questo percorso", text, name)
            if name != "setup":
                self.assertIn("indica il comando intero", text, name)
            self.assertIn("tollgate: programma", text, name)

    def test_execute_forbids_sdd_as_executor(self):
        text = (ROOT / "skills" / "execute" / "SKILL.md").read_text()
        self.assertIn("/tollgate:finish", text)
        self.assertIn("mai subagent-driven-development", text)
        self.assertIn(ATTRIBUTION, text)
        start = (ROOT / "skills" / "start" / "SKILL.md").read_text()
        self.assertIn("/tollgate:execute", start)

    def test_start_skill_covers_exit_codes_and_levels(self):
        text = (ROOT / "skills" / "start" / "SKILL.md").read_text()
        for needle in ("--confirm", "EnterWorktree", "cd <percorso> && claude",
                       "status --checkpoint", "writing-plans", "brainstorming"):
            self.assertIn(needle, text)
        self.assertRegex(text, r"(?m)^argument-hint: \"#N \[L1\|L2\]\"$")

    def test_setup_skill_does_not_write_settings(self):
        text = (ROOT / "skills" / "setup" / "SKILL.md").read_text()
        self.assertIn("statusLine.command", text)
        self.assertIn("statusline/ctx", text)
        self.assertIn("non modificare", text)

    def test_plugin_and_marketplace_json(self):
        p = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(p["author"], {"name": "sAInapse"})
        self.assertEqual(p["license"], "MIT")
        for dep in p["dependencies"]:
            self.assertNotIn("version", dep)
        m = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        self.assertEqual(m["name"], "sainapse")
        self.assertEqual(m["owner"], {"name": "sAInapse"})
        self.assertTrue(m["description"])
        self.assertEqual(m["allowCrossMarketplaceDependenciesOn"], ["claude-plugins-official"])
        (entry,) = m["plugins"]
        self.assertEqual((entry["name"], entry["source"]), ("tollgate", "./"))
        self.assertTrue(entry["description"])
        self.assertEqual(entry["author"], {"name": "sAInapse"})

    def test_license_files(self):
        own = (ROOT / "LICENSE").read_text()
        self.assertTrue(own.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026 sAInapse", own)
        theirs = (ROOT / "LICENSES" / "superpowers-MIT.txt").read_text()
        self.assertIn("MIT License", theirs)
        self.assertIn("Copyright (c) 2025 Jesse Vincent", theirs)

    def test_brief_fields_match_agent_text(self):
        from tollgate_analysis.report import REQUIRED
        impl = (ROOT / "agents" / "implementer.md").read_text()
        for field in (*REQUIRED, "must_have", "size_reason"):
            self.assertRegex(impl, rf'"{field}"', field)
        rev = (ROOT / "agents" / "task-reviewer.md").read_text()
        for field in ("v", "task", "sha", "code", "outcome", "spec_compliance", "findings",
                      "severity", "file", "line", "rule", "text"):
            self.assertRegex(rev, rf'"{field}"', field)
        blocks = re.findall(r"```json\n(.*?)\n```", rev, re.S)
        outcomes = {json.loads(b)["outcome"] for b in blocks}
        self.assertEqual(outcomes, {"approved", "changes"})
        for b in re.findall(r"```json\n(.*?)\n```", impl, re.S):
            self.assertEqual(json.loads(b)["status"], "DONE")

    def test_agents_and_skills_never_write_a_bare_program_name(self):
        """`tollgate` non è nel PATH: ai subagenti serve la forma del brief (decisione 3)."""
        bare = re.compile(r"(?<![\w/:.\"'-])tollgate (?:verify|block|task|status|act|start|"
                          r"waiver|approve|finish|init)\b")
        for path in (*(ROOT / "agents").glob("*.md"), *(ROOT / "skills").glob("*/SKILL.md")):
            with self.subTest(path=path.name):
                self.assertEqual(bare.findall(path.read_text()), [])

    def test_execute_follows_registered_verdict_and_checkpoint(self):
        text = (ROOT / "skills" / "execute" / "SKILL.md").read_text()
        self.assertIn("revisore: <tipo>", text)
        self.assertIn("mai un tipo fisso", text)
        self.assertLess(text.index("task done k`:"), text.index("task start k --fix`, che"))
        self.assertIn("conta quello registrato", text)
        self.assertIn("status --checkpoint", text)
        self.assertIn("prossimo passo", text)
        for state in ("pending", "running", "review", "blocked"):
            self.assertIn(f"| `{state}`", text)
        self.assertIn("/tollgate:resolve", text)

    def test_start_l1_is_reentrant(self):
        text = (ROOT / "skills" / "start" / "SKILL.md").read_text()
        self.assertIn("rientrante", text)
        self.assertIn("Non chiedere un secondo `/clear`", text)

    def test_final_agents_frontmatter(self):
        rev = ROOT / "agents" / "final-reviewer.md"
        ver = ROOT / "agents" / "finding-verifier.md"
        for path, name, model in ((rev, "final-reviewer", "inherit"),
                                  (ver, "finding-verifier", "sonnet")):
            fm = frontmatter(path)
            self.assertEqual(fm["name"], name)
            self.assertEqual(fm["model"], model)
            self.assertTrue(fm["description"])
            tools = [t.strip() for t in fm["tools"].split(",")]
            self.assertEqual(tools, ["Read", "Grep", "Glob", "Bash"])
            self.assertNotIn("Edit", tools)
            self.assertNotIn("Write", tools)
        self.assertIn(FINAL_ATTRIBUTION, rev.read_text())

    def test_closing_skills_user_only(self):
        for name in ("sync", "adopt", "abandon", "cleanup"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^disable-model-invocation: true$", name)
            self.assertRegex(text, rf"(?m)^name: {name}$")
        text = (ROOT / "skills" / "finish" / "SKILL.md").read_text()
        self.assertNotIn("disable-model-invocation", text)
        self.assertRegex(text, r"(?m)^name: finish$")
        self.assertRegex(text, r"(?m)^description: \S")

    def test_skills_use_program_command_form(self):
        """Ogni testo che nomina `bin/tollgate` lo fa nella forma `python3 "…/bin/tollgate"`."""
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skills), 13)
        bare = re.compile(r'(?<!python3 "\$\{CLAUDE_PLUGIN_ROOT\}/)(?<!python3 "…/)'
                          r'bin/tollgate(?![\w])')
        for path in skills:
            text = path.read_text()
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertEqual(bare.findall(text), [])
                if "bin/tollgate" in text:
                    self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"', text)
                    self.assertIn("tollgate: programma", text)

    def test_finish_skill_never_pushes(self):
        text = (ROOT / "skills" / "finish" / "SKILL.md").read_text()
        self.assertIn("mai `git push`", text)
        self.assertIn("gh pr create", text)

    def test_finish_skill_keeps_worktree_clean(self):
        text = (ROOT / "skills" / "finish" / "SKILL.md").read_text()
        self.assertIn("committa", text)
        self.assertLess(text.index("committa"), text.index("finish check"))
        self.assertIn("di' all'utente di digitare di nuovo `/tollgate:finish` e **fermati**", text)
        self.assertLess(text.index("digitare di nuovo `/tollgate:finish` e **fermati**"),
                        text.index("<programma> finish check"))
        for needle in ("review prepare", "finish open-pr", "--from-findings", "agente:",
                       "prossimo passo", "/tollgate:resolve", "/tollgate:approve finding",
                       "/tollgate:approve rounds"):
            self.assertIn(needle, text)

    def test_final_verdict_fields_in_agent_text(self):
        rev = (ROOT / "agents" / "final-reviewer.md").read_text()
        for field in ("v", "sha", "code", "outcome", "findings", "severity", "confidence",
                      "file", "line", "rule", "text"):
            self.assertRegex(rev, rf'"{field}"', field)
        blocks = re.findall(r"```json\n(.*?)\n```", rev, re.S)
        self.assertEqual({json.loads(b)["outcome"] for b in blocks},
                         {"ok", "needs_fix", "needs_you"})
        ver = (ROOT / "agents" / "finding-verifier.md").read_text()
        for field in ("v", "sha", "code", "results", "id", "verification", "reason"):
            self.assertRegex(ver, rf'"{field}"', field)
        for word in ("confirmed", "rejected", "unverified"):
            self.assertIn(word, ver)
        for b in re.findall(r"```json\n(.*?)\n```", ver, re.S):
            self.assertEqual(json.loads(b)["v"], 1)
        for b in blocks:
            self.assertEqual(json.loads(b)["v"], 1)

    def test_updated_skills_describe_closing(self):
        approve = (ROOT / "skills" / "approve" / "SKILL.md").read_text()
        for needle in ("finding", "rounds", "unverified-review", "rebase", "act apply",
                       "unverified-tests", "waiver", "effect"):
            self.assertIn(needle, approve)
        self.assertNotIn("arriva con /tollgate:finish (P3b)", approve)
        execute = (ROOT / "skills" / "execute" / "SKILL.md").read_text()
        self.assertIn("digitare `/tollgate:finish`", execute)
        self.assertNotIn("arriva con P3b", execute)
        start = (ROOT / "skills" / "start" / "SKILL.md").read_text()
        self.assertIn("/tollgate:adopt #N", start)
        self.assertNotIn("arriva con P3b", start)
        self.assertIn("/tollgate:abandon #N", start)
        resolve = (ROOT / "skills" / "resolve" / "SKILL.md").read_text()
        self.assertIn("concede **un** ciclo", resolve)

    def test_wrapper_executable(self):
        self.assertTrue(os.access(ROOT / "hooks" / "run", os.X_OK))


class BareProgramInMessagesTest(unittest.TestCase):
    """I testi che il modello legge come istruzione non scrivono `tollgate <sottocomando>` nudo:
    `tollgate` non è nel PATH e un percorso con spazi non regge come nome di comando. Si usa
    `paths.program_command`. Le docstring e le etichette di errore («tollgate verify: …») non
    contano."""
    # Sottocomandi del parser della CLI, più quelli dei piani a venire; `hook` resta fuori:
    # compare in testi che non sono istruzioni («tollgate hook lo lancia solo hooks/run»).
    FUTURE = ("open-pr", "gate", "finish", "init", "setup", "sync", "adopt", "cleanup",
              "abandon", "resolve", "approve")

    @classmethod
    def bare(cls):
        from tollgate_core import cli
        parser = cli.build_parser()
        action = next(a for a in parser._actions if a.dest == "cmd")
        names = {*action.choices, *cls.FUTURE} - {"hook"}
        alt = "|".join(re.escape(n) for n in sorted(names))
        return re.compile(rf"(?<![\w/:.\-])tollgate (?:{alt})\b(?!:)")

    @staticmethod
    def docstrings(tree):
        out = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    out.add(id(first.value))
        return out

    def test_no_bare_program_in_string_literals(self):
        bare = self.bare()
        hits = []
        for path in sorted((ROOT / "bin").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            skip = self.docstrings(tree)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and id(node) not in skip):
                    for m in bare.finditer(node.value):
                        hits.append(f"{path.relative_to(ROOT)}:{node.lineno}: {m.group(0)}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
