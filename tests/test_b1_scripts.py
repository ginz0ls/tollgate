"""Lo script delle verifiche reali di B1 (Task 1), la sonda dei suoi hook e le funzioni che raccolgono le evidenze, provati senza rete
e senza `claude` vero: `bash -n`, il modo `controlla`, un `claude` finto nel PATH che registra gli argomenti, prove dirette dei file
della sonda e della raccolta anonimizzata su un registro finto. Nessuna prova scrive in /tmp/tollgate-b1: le radici sono temporanee
(`B1_CHECK=1` con `B1_TMP`)."""
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

B1 = ROOT / "spikes" / "b1"
SCRIPT = B1 / "run-b1-checks.sh"
PLUGIN = B1 / "probe-plugin"
SKILL = PLUGIN / "skills" / "leggi" / "SKILL.md"
REDIRECT = "https://docs.python.org/library/json.html"
FAKE_CLAUDE = """#!/usr/bin/env bash
{ printf 'CWD\\0%s\\0ENV\\0%s\\0' "$PWD" "${TOLLGATE_STATE-}"; for a in "$@"; do printf 'ARG\\0%s\\0' "$a"; done; printf 'END\\0'; } >> "$B1_FAKE_LOG"
case "$1" in --version) echo "9.9.9 (Claude Code finto)" ;; -p) echo '{"result":"ok"}' ;; esac
exit 0
"""


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("B1_", "P4_", "P5_", "TOLLGATE_", "GIT_"))}
    env.update(extra)
    return env


def read_calls(log):
    """Le chiamate al claude finto: lista di dict {cwd, args}."""
    calls, cur = [], None
    if not Path(log).exists():
        return calls
    parts = Path(log).read_bytes().decode().split("\0")
    i = 0
    while i < len(parts) - 1:
        if parts[i] == "CWD":
            cur = {"cwd": parts[i + 1], "args": [], "state": parts[i + 3]}
            i += 4
        elif parts[i] == "ARG":
            cur["args"].append(parts[i + 1])
            i += 2
        elif parts[i] == "END":
            calls.append(cur)
            i += 1
        else:
            i += 1
    return calls


class Bench:
    """Radici temporanee e `claude` finto per un test."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="tollgate-b1-test-"))
        self.tmp = self.dir / "tollgate-b1"
        self.out = self.dir / "out"
        self.samples = self.dir / "samples-b1.json"
        self.bin = self.dir / "bin"
        self.bin.mkdir()
        self.log = self.dir / "fake-claude.log"
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(0o755)

    def env(self, **extra):
        base = dict(PATH=f"{self.bin}:{os.environ['PATH']}", B1_FAKE_LOG=str(self.log), B1_CHECK="1", B1_TMP=str(self.tmp),
                    B1_OUT=str(self.out), B1_SAMPLES=str(self.samples), B1_TIMEOUT="60", HOME=str(self.dir / "home"))
        base.update(extra)
        return clean_env(**base)

    def run(self, *args, **extra):
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=self.env(**extra), timeout=300)

    def calls(self):
        return read_calls(self.log)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class ScriptShapeTest(unittest.TestCase):
    def test_syntax(self):
        r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        for py in [B1 / "latenza.py", B1 / "raccogli.py", PLUGIN / "bin" / "eco", PLUGIN / "hooks" / "record.py"]:
            with self.subTest(py.name):
                compile(py.read_text(), str(py), "exec")

    def test_the_script_has_one_claude_p_and_no_destructive_commands(self):
        text = SCRIPT.read_text()
        code = re.sub(r"(?m)^\s*#.*$", "", text)
        self.assertEqual(len(re.findall(r"=\(claude -p\b", code)), 1)       # il solo comando; il resto sono messaggi
        self.assertNotRegex(code, r"\brm\s+-[a-zA-Z]*[rR]")
        self.assertNotRegex(code, r"\b(pkill|killall)\b")
        self.assertNotRegex(code, r"\bkill\s")
        self.assertNotRegex(code, r"claude plugin (install|marketplace|enable|uninstall)|claude plugin eval")
        self.assertNotRegex(code, r"--force|--no-verify|reset --hard|git stash|--amend")
        self.assertIn("DEFAULT_TMP=/tmp/tollgate-b1", text)

    def test_the_hooks_never_touch_the_user_state_or_settings(self):
        for path in [SCRIPT, B1 / "latenza.py", B1 / "raccogli.py", *PLUGIN.rglob("*.py"), PLUGIN / "bin" / "eco"]:
            with self.subTest(path.name):
                code = re.sub(r"(?m)^\s*#.*$", "", path.read_text())
                self.assertNotIn(".local/state/tollgate", code)
                self.assertNotIn("settings.json", code)
                self.assertNotIn("installed_plugins", code)


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.b = Bench()
        self.addCleanup(self.b.cleanup)

    def test_checks_controlla_lists_steps(self):
        r = subprocess.run(["bash", str(SCRIPT), "controlla"], capture_output=True, text=True, env=clean_env(), timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CONTROLLA: ok", r.stdout)
        for word in ("sonda", "latenza", "valida", "raccogli", "B1-V1", "B1-V6", "B1-V7", "/tmp/tollgate-b1/probe", "--plugin-dir",
                     "--allowedTools", "--disallowedTools", "--output-format json", "acceptEdits"):
            self.assertIn(word, r.stdout)
        self.assertEqual(r.stderr, "")

    def test_checks_refuses_outside_tmp(self):
        for work in ("/tmp/fuori-da-tollgate-b1", "/tmp/tollgate-b1", "/tmp/tollgate-b1/../altro", str(Path.home() / "x")):
            with self.subTest(work):
                r = self.b.run("sonda", "--redirect-url", REDIRECT, B1_WORK=work, B1_CHECK="0", B1_TMP="")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("non è sotto /tmp/tollgate-b1/", r.stderr)
        r = self.b.run("sonda", "--redirect-url", REDIRECT, B1_WORK="/tmp/fuori-da-tollgate-b1")      # anche con la radice temporanea
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("non è sotto", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(self.b.tmp.exists())

    def test_checks_requires_plugin_dir(self):
        r = self.b.run("sonda", "--redirect-url", REDIRECT, B1_PLUGIN_DIR="")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("senza --plugin-dir", r.stderr)
        r = self.b.run("sonda", "--redirect-url", REDIRECT, B1_PLUGIN_DIR=str(self.b.dir / "non-esiste"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("non esiste", r.stderr)
        self.assertEqual(self.b.calls(), [])

    def test_checks_requires_redirect_url(self):
        for args in (["sonda"], ["sonda", "--redirect-url"], ["sonda", "--redirect-url", "http://x.example/a"]):
            with self.subTest(args):
                r = self.b.run(*args)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(self.b.calls(), [])

    def test_checks_valida_uses_tmp_copy(self):
        r = self.b.run("valida")
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = self.b.calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["args"], ["plugin", "validate", "--strict", "."])
        self.assertNotIn("-p", calls[0]["args"])
        self.assertEqual(os.path.realpath(calls[0]["cwd"]), os.path.realpath(self.b.tmp / "valida"))
        skill = (self.b.tmp / "valida" / "skills" / "rules-base" / "SKILL.md").read_text()
        self.assertRegex(skill, r"(?m)^approved: prova$")
        self.assertTrue((self.b.tmp / "valida" / ".claude-plugin" / "plugin.json").exists())
        self.assertFalse((PLUGIN / "skills" / "rules-base").exists(), "la sonda nel repo non deve cambiare")
        self.assertIn("uscita: 0", (self.b.out / "valida-esito.txt").read_text())
        r = self.b.run("valida")                       # una seconda volta: la copia precedente si rinomina, non si cancella
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(list(self.b.tmp.glob("valida.prev-*"))), 1)
        self.assertEqual(len(list(self.b.out.glob("valida-esito.txt.prev-*"))), 1)

    def test_checks_allowed_tools(self):
        r = self.b.run("sonda", "--redirect-url", REDIRECT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        calls = [c for c in self.b.calls() if c["args"][:1] == ["-p"]]
        self.assertEqual(len(calls), 1)
        args = calls[0]["args"]
        self.assertEqual(os.path.realpath(calls[0]["cwd"]), os.path.realpath(self.b.tmp / "probe"))
        self.assertIn("--plugin-dir", args)
        self.assertEqual(Path(args[args.index("--plugin-dir") + 1]), PLUGIN)
        self.assertEqual(args[args.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(args[args.index("--model") + 1], "sonnet")
        self.assertEqual(args[args.index("--output-format") + 1], "json")
        allowed = args[args.index("--allowedTools") + 1].split(",")
        for tool in ("Read", "Grep", "Glob", "Bash", "Agent", "Skill", "Write", "Edit", "WebFetch", "WebSearch",
                     "mcp__context7__*", "mcp__plugin_context7_context7__*"):
            self.assertIn(tool, allowed)
        denied = args[args.index("--disallowedTools") + 1].split(",")
        self.assertEqual(denied, ["Bash(curl:*)", "Bash(wget:*)", "Bash(gh:*)", "Bash(git push:*)"])
        prompt = args[-1]
        self.assertIn(REDIRECT, prompt)
        self.assertIn("Dopo i dodici passi", prompt)
        self.assertIn("path src/app.py, senza output_mode (non passare il parametro)", prompt)
        self.assertIn("path src/app.py (un file), con output_mode content", prompt)
        for word in ("src/app.py", "src/assente.py", "content", "files_with_matches", "Glob", "pyproject.toml",
                     "https://docs.python.org/3/library/tomllib.html", "WebSearch", "context7", "probe:leggi"):
            self.assertIn(word, prompt)
        state = Path(calls[0]["state"])
        self.assertEqual(os.path.realpath(state), os.path.realpath(self.b.tmp / "state"))
        self.assertTrue((state / ".tollgate-test").is_file())
        # il repo di prova
        probe = self.b.tmp / "probe"
        self.assertTrue((probe / "src" / "app.py").exists() and (probe / "pyproject.toml").exists())
        self.assertEqual(subprocess.run(["git", "-C", str(probe), "log", "--oneline"], capture_output=True, text=True).returncode, 0)
        att = self.b.tmp / "tentativo-1"
        self.assertEqual((att / "redirect-url.txt").read_text().strip(), REDIRECT)
        self.assertIn("9.9.9", (att / "versione.txt").read_text())
        self.assertEqual((att / "claude.json").read_text().strip(), '{"result":"ok"}')
        # un secondo tentativo non tocca il primo e ricrea il repo di prova
        (att / "prova.txt").write_text("resta")
        r = self.b.run("sonda", "--redirect-url", REDIRECT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((att / "prova.txt").read_text(), "resta")
        self.assertTrue((self.b.tmp / "tentativo-2" / "claude.json").exists())
        self.assertEqual(len(list(self.b.tmp.glob("probe.prev-*"))), 1)

    def _fake_attempt(self, eco=None, extra_events=()):
        att = self.b.tmp / "tentativo-1"
        att.mkdir(parents=True)
        home = str(self.b.dir / "home")
        sid, agent = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb", "agent-xyz"
        base = {"session_id": sid, "transcript_path": f"{home}/.claude/projects/p/{sid}.jsonl", "cwd": "/tmp/tollgate-b1/probe",
                "permission_mode": "acceptEdits"}

        def ev(name, tool, ti, tr=None, agent_id=agent, tuid=None, **kw):
            e = dict(base, hook_event_name=name, tool_name=tool, tool_input=ti, tool_use_id=tuid)
            if agent_id:
                e.update(agent_id=agent_id, agent_type="probe:lettore")
            if tr is not None:
                e["tool_response"] = tr
            e.update(kw)
            return e

        events = [dict(base, hook_event_name="SubagentStart", agent_id=agent, agent_type="probe:lettore")]
        pairs = [
            ("t1", "Read", {"file_path": "/tmp/tollgate-b1/probe/src/app.py"}, {"type": "text", "file": {"content": f"x {home}"}}),
            ("t2", "Grep", {"pattern": "somma", "path": "src", "output_mode": "content"}, {"mode": "content", "content": "src/app.py:1:def somma"}),
            ("t2f", "Grep", {"pattern": "somma", "path": "src/app.py", "output_mode": "content"}, {"mode": "content", "content": "1:def somma"}),
            ("t3d", "Grep", {"pattern": "somma", "path": "src/app.py"}, {"mode": "files_with_matches", "filenames": ["src/app.py"]}),
            ("t3", "Grep", {"pattern": "somma", "output_mode": "files_with_matches"}, {"mode": "files_with_matches", "filenames": ["src/app.py"]}),
            ("t4", "Glob", {"pattern": "**/*.py"}, {"filenames": ["src/app.py"]}),
            ("t5", "Bash", {"command": "cat pyproject.toml"}, {"stdout": "[project]", "stderr": ""}),
            ("t6", "WebFetch", {"url": "https://docs.python.org/3/library/tomllib.html", "prompt": "x"}, {"result": "A" * 9000, "url": "u"}),
            ("t7", "WebFetch", {"url": REDIRECT, "prompt": "x"}, {"result": "ok", "url": "https://docs.python.org/3/library/json.html"}),
            ("t8", "WebSearch", {"query": "python tomllib"}, {"query": "python tomllib", "results": []}),
            ("t9", "Bash", {"command": "python3 /x/bin/eco <<'NOTA_DI_RICERCA_FINE'\nx\nNOTA_DI_RICERCA_FINE"}, {"stdout": "eco: 1 byte"}),
        ]
        for tuid, tool, ti, tr in pairs:
            events.append(ev("PreToolUse", tool, ti, tuid=tuid))
            events.append(ev("PostToolUse", tool, ti, tr, tuid=tuid))
        events.append(ev("PreToolUse", "Read", {"file_path": "/x/y.py"}, tuid="t10"))             # senza agent_id: la sessione principale
        events[-1].pop("agent_id"), events[-1].pop("agent_type")
        events.append(ev("PreToolUse", "Read", {"file_path": "/tmp/tollgate-b1/probe/src/assente.py"}, tuid="t11"))
        events.append(ev("PostToolUseFailure", "Read", {"file_path": "/tmp/tollgate-b1/probe/src/assente.py"}, tuid="t11", error="no"))
        events.extend(extra_events)
        (att / "hooks.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events) + "riga rotta\n")
        (att / "redirect-url.txt").write_text(REDIRECT + "\n")
        (att / "claude.json").write_text(json.dumps({"result": f"fatto in {home}/x", "session_id": sid}))
        (att / "argv.txt").write_text(f"cwd: /tmp/tollgate-b1/probe\nclaude -p --plugin-dir {home}/p\n")
        if eco is not None:
            (att / "eco.txt").write_text(eco)
        return home, sid, agent

    def _expected_eco(self):
        return subprocess.run([sys.executable, "-B", str(B1 / "raccogli.py"), "atteso", "--skill", str(SKILL)],
                              capture_output=True, text=True, check=True).stdout

    def test_checks_raccogli_anonymizes(self):
        home, sid, agent = self._fake_attempt(eco=self._expected_eco())
        r = self.b.run("raccogli", HOME=home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        samples = json.loads(self.b.samples.read_text())
        self.assertEqual(list(samples), ["read", "grep_content", "grep_content_dir", "grep_default", "grep_files", "glob", "bash_cat", "webfetch", "webfetch_redirect",
                                         "websearch"], "mcp_docs resta assente senza campione")
        for key, entry in samples.items():
            with self.subTest(key):
                self.assertEqual(sorted(entry), ["post", "pre"])
                self.assertEqual(entry["pre"]["hook_event_name"], "PreToolUse")
                self.assertEqual(entry["post"]["hook_event_name"], "PostToolUse")
                self.assertEqual(entry["pre"]["tool_use_id"], entry["post"]["tool_use_id"])
                self.assertEqual(entry["pre"]["agent_id"], agent)
        self.assertEqual(samples["read"]["pre"]["session_id"], "SESSION-ID")
        self.assertEqual(samples["read"]["pre"]["transcript_path"], "/home/USER/.claude/projects/TRANSCRIPT.jsonl")
        self.assertEqual(samples["read"]["post"]["tool_response"]["file"]["content"], "x /home/USER")
        self.assertEqual(samples["webfetch_redirect"]["pre"]["tool_input"]["url"], REDIRECT)
        self.assertEqual(samples["webfetch"]["pre"]["tool_input"]["url"], "https://docs.python.org/3/library/tomllib.html")
        self.assertTrue(samples["webfetch"]["post"]["tool_response"]["result"].endswith("[troncato, 9000 caratteri]"))
        self.assertEqual(samples["grep_content"]["pre"]["tool_input"]["path"], "src/app.py")
        self.assertEqual(samples["grep_content_dir"]["pre"]["tool_input"]["path"], "src")
        self.assertNotIn("output_mode", samples["grep_default"]["pre"]["tool_input"])
        self.assertEqual(samples["grep_files"]["pre"]["tool_input"]["output_mode"], "files_with_matches")
        self.assertEqual(samples["bash_cat"]["pre"]["tool_input"]["command"], "cat pyproject.toml")
        # nulla di personale in tutto ciò che si è scritto
        written = [self.b.samples, *[p for p in self.b.out.rglob("*") if p.is_file()]]
        self.assertTrue(any(p.name == "hooks.jsonl" for p in written))
        for path in written:
            text = path.read_text()
            with self.subTest(path.name):
                self.assertNotIn(home, text)
                self.assertNotIn(sid, text)
                self.assertNotIn("PATH", text)
        out = self.b.out / "tentativo-1"
        self.assertEqual((out / "eco-esito.txt").read_text().splitlines()[0], "integro")
        summary = (out / "riepilogo.txt").read_text()
        self.assertIn("PostToolUseFailure: Read", summary)
        self.assertIn("righe non valide: 1", summary)
        self.assertIn("senza campione: mcp_docs", summary)
        self.assertIn("probe:lettore", summary)

    def test_checks_raccogli_refuses_an_empty_home(self):
        self._fake_attempt(eco="")
        for home in ("", "/"):
            with self.subTest(home):
                r = self.b.run("raccogli", HOME=home)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("--home vuoto", r.stderr)
                self.assertFalse(self.b.samples.exists())
                self.assertFalse(self.b.out.exists())

    def test_checks_raccogli_flags_a_changed_heredoc_and_a_missing_one(self):
        home, _, _ = self._fake_attempt(eco=self._expected_eco().replace("`backtick`", "backtick"))
        r = self.b.run("raccogli", HOME=home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = (self.b.out / "tentativo-1" / "eco-esito.txt").read_text()
        self.assertEqual(text.splitlines()[0], "diverso")
        self.assertIn("prima differenza alla riga 1", text)
        shutil.rmtree(self.b.tmp)
        shutil.rmtree(self.b.out)
        home, _, _ = self._fake_attempt(eco=None)
        r = self.b.run("raccogli", HOME=home)
        self.assertEqual((self.b.out / "tentativo-1" / "eco-esito.txt").read_text().splitlines()[0], "assente")

    def test_checks_raccogli_picks_a_mcp_docs_sample_and_prefers_the_subagent(self):
        tool = "mcp__plugin_context7_context7__query-docs"
        ti = {"libraryId": "/python/cpython", "query": "tomllib"}
        main = {"hook_event_name": "PreToolUse", "tool_name": "Glob", "tool_input": {"pattern": "*"}, "tool_use_id": "m1"}
        extra = [main, dict(main, hook_event_name="PostToolUse", tool_response={"filenames": []}),
                 {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti, "tool_use_id": "c1", "agent_id": "agent-xyz"},
                 {"hook_event_name": "PostToolUse", "tool_name": tool, "tool_input": ti, "tool_use_id": "c1", "agent_id": "agent-xyz",
                  "tool_response": {"content": [{"type": "text", "text": "doc"}]}}]
        home, _, _ = self._fake_attempt(eco="", extra_events=extra)
        r = self.b.run("raccogli", HOME=home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        samples = json.loads(self.b.samples.read_text())
        self.assertEqual(samples["mcp_docs"]["post"]["tool_response"]["content"][0]["text"], "doc")
        self.assertEqual(samples["glob"]["pre"]["agent_id"], "agent-xyz", "tra due Glob vince quello del subagente")


class ProbePluginTest(unittest.TestCase):
    def test_hooks_json_registers_the_wanted_events(self):
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(sorted(hooks), ["PostToolUse", "PostToolUseFailure", "PreToolUse", "SubagentStart", "SubagentStop"])
        for event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
            self.assertEqual(hooks[event][0]["matcher"], ".*")
        for event, groups in hooks.items():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertIn("hooks/record.py", hook["command"])

    def test_plugin_files(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "probe")
        agent = (PLUGIN / "agents" / "lettore.md").read_text()
        self.assertIn("\nname: lettore\n", agent)
        self.assertIn("\ntools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__context7__*, mcp__plugin_context7_context7__*\n", agent)
        self.assertIn("probe:lettore", SKILL.read_text())

    def test_record_logs_only_the_stdin_json(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b1-record-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        log = tmp / "sub" / "hooks.jsonl"
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Read", "agent_id": "a1", "tool_input": {"file_path": "/x"}}
        env = clean_env(B1_PROBE_LOG=str(log), SEGRETO_DI_PROVA="zz-segreto", HOME=str(tmp / "home"))
        for text in (json.dumps(payload), "non json", "[1]"):
            r = subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "record.py")], input=text, text=True, capture_output=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
        lines = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual(lines[0], payload)
        self.assertEqual(lines[1], {"_non_json": "non json"})
        self.assertEqual(lines[2], {"_non_oggetto": True})
        self.assertNotIn("zz-segreto", log.read_text())
        # sotto la HOME non scrive
        home_log = tmp / "home" / "x" / "hooks.jsonl"
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "hooks" / "record.py")], input=json.dumps(payload), text=True,
                           capture_output=True, env=clean_env(B1_PROBE_LOG=str(home_log), HOME=str(tmp / "home")))
        self.assertEqual(r.returncode, 0)
        self.assertFalse(home_log.exists())

    def test_the_skill_heredoc_reaches_eco_intact(self):
        """Il comando del passo finale della skill, eseguito da bash com'è (con ${CLAUDE_PLUGIN_ROOT} risolto)."""
        text = SKILL.read_text()
        command = re.search(r"~~~~\n(.*?)\n~~~~", text, re.S).group(1).replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN))
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b1-eco-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        out = tmp / "eco.txt"
        env = clean_env(B1_ECO_OUT=str(out), HOME=str(tmp / "home"), PATH=os.environ["PATH"])
        r = subprocess.run(["bash", "-c", command], capture_output=True, text=True, env=env, cwd=str(tmp))
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = subprocess.run([sys.executable, "-B", str(B1 / "raccogli.py"), "atteso", "--skill", str(SKILL)],
                                  capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.read_text(), expected)
        for piece in ("`backtick`", "\nEOF\n", "$HOME", "$(echo no)"):
            self.assertIn(piece, expected)
        self.assertIn("<<'NOTA_DI_RICERCA_FINE'", command)

    def test_eco_refuses_the_home(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b1-eco-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        r = subprocess.run([sys.executable, "-B", str(PLUGIN / "bin" / "eco")], input="x", text=True, capture_output=True,
                           env=clean_env(B1_ECO_OUT=str(tmp / "home" / "e.txt"), HOME=str(tmp / "home")))
        self.assertEqual(r.returncode, 1)
        self.assertFalse((tmp / "home").exists())


class LatencyTest(unittest.TestCase):
    def test_latenza_builds_the_active_repo_and_measures_both_series(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b1-latenza-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        r = subprocess.run([sys.executable, "-B", str(B1 / "latenza.py"), "--root", str(tmp / "tollgate-b1"), "--out", str(tmp / "out"),
                            "--runs", "2"], capture_output=True, text=True, env=clean_env(), timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((tmp / "tollgate-b1" / "state" / ".tollgate-test").exists())
        data = json.loads((tmp / "out" / "latenza.json").read_text())
        self.assertEqual(sorted(data["series"]), ["post_bash_subagent", "post_read_no_agent"])
        for series in data["series"].values():
            self.assertEqual(series["n"], 2)
            self.assertLessEqual(series["median_ms"], series["p95_ms"])
        v3 = json.loads((tmp / "out" / "b1v3-prova.json").read_text())
        self.assertEqual(v3["tool_name"], "mcp__plugin_context7_context7__query-docs")
        self.assertTrue(v3["denied"], v3)
        self.assertIn("effetto esterno", v3["stderr"])
        self.assertIn("mediana", r.stdout)
        self.assertFalse(list(tmp.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
