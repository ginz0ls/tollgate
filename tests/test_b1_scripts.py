"""Lo script delle verifiche reali di B1 (Task 1), la sonda dei suoi hook e le funzioni che raccolgono le evidenze, provati senza rete
e senza `claude` vero: `bash -n`, il modo `controlla`, un `claude` finto nel PATH che registra gli argomenti, prove dirette dei file
della sonda e della raccolta anonimizzata su un registro finto. Nessuna prova scrive in /tmp/tollgate-b1: le radici sono temporanee
(`B1_CHECK=1` con `B1_TMP`)."""
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
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
        self.assertEqual(sorted(data["series"]), ["post_bash_subagent", "post_read_no_agent", "post_read_subagent"])
        for series in data["series"].values():
            self.assertEqual(series["n"], 2)
            self.assertLessEqual(series["median_ms"], series["p95_ms"])
        # la serie del Read da subagente misura la registrazione vera, non un'uscita a vuoto
        import sqlite3
        conn = sqlite3.connect(str(tmp / "tollgate-b1" / "state" / "tollgate.db"))
        try:
            self.assertIn(("read", "src/app.py", 1), conn.execute(
                "SELECT kind, target, task FROM lookups").fetchall())
        finally:
            conn.close()
        v3 = json.loads((tmp / "out" / "b1v3-prova.json").read_text())
        self.assertEqual(v3["tool_name"], "mcp__plugin_context7_context7__query-docs")
        # dal Task 5 lo strumento di documentazione non è più un effetto esterno
        self.assertFalse(v3["denied"], v3)
        self.assertNotIn("effetto esterno", v3["stderr"])
        self.assertIn("mediana", r.stdout)
        self.assertFalse(list(tmp.rglob("__pycache__")))



FLOW_SCRIPT = ROOT / "spikes" / "run-b1-flow.sh"
FLOW_REG = B1 / "flowreg.py"
FLOW_EVIDENCE = ROOT / "docs" / "verifiche" / "evidenze" / "b1" / "flusso"
FLOW_TOOLS = "Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob,WebFetch,WebSearch"
FLOW_FAKE_CLAUDE = FAKE_CLAUDE.replace('case "$1" in', '[ "$1" = plugin ] && exit "${B1_FAKE_VALIDATE_RC:-0}"\n'
                                       '[ "$1" = -p ] && printf \'%s\\n%s\\n%s\\n\' "$PATH" "${TOLLGATE_GH-}" "${TOLLGATE_FAKEGH_DATA-}" >> "$B1_FAKE_LOG.env"\n'
                                       'case "$1" in', 1)


class FlowBench(Bench):
    """Radici temporanee per lo script della prova reale del Task 9, con un `claude` finto: nulla va in /tmp/tollgate-b1 né nelle evidenze del repo."""

    def __init__(self):
        super().__init__()
        (self.bin / "claude").write_text(FLOW_FAKE_CLAUDE)
        self.root = self.dir / "tollgate-b1"

    @property
    def flow(self):
        return self.root / "flow"

    @property
    def plugin(self):
        return self.root / "plugin"

    def env(self, **extra):
        base = dict(PATH=f"{self.bin}:{os.environ['PATH']}", B1_FAKE_LOG=str(self.log), B1_FLOW_CHECK="1", B1_FLOW_ROOT=str(self.root),
                    B1_FLOW_OUT=str(self.out), B1_FLOW_TIMEOUT="60", HOME=str(self.dir / "home"), GIT_CONFIG_GLOBAL="/dev/null",
                    GIT_CONFIG_NOSYSTEM="1")
        base.update(extra)
        return clean_env(**base)

    def run(self, *args, **extra):
        return subprocess.run(["bash", str(FLOW_SCRIPT), *args], capture_output=True, text=True, env=self.env(**extra), timeout=300)

    def prepara(self):
        r = self.run("prepara")
        if r.returncode != 0:
            raise AssertionError(r.stdout + r.stderr)
        return r

    def worktree(self):
        wt = self.flow / ".claude" / "worktrees" / "tg-1-prova"
        subprocess.run(["git", "-C", str(self.flow), "worktree", "add", "-q", "-b", "tg/1-prova", str(wt)], check=True,
                       capture_output=True, env=self.env())
        return wt

    def claude_p(self):
        return [c for c in self.calls() if c["args"][:1] == ["-p"]]

    def src_repo(self, *, approved=True, case="b1", ai_approved=True, infra_approved=True, backend_approved=True):
        """Un piccolo repo git che traccia `bin/` del repo e una `skills/rules-base/SKILL.md`: la radice sorgente (`B1_FLOW_SRC`).
        Con `case="ai"`, `case="infra"` o `case="backend"` copia invece i file veri (e tracciati) che servono a `init --propose`:
        `bin/`, `templates/`, `gate/`, `agents/`, `skills/rules-base/`, `skills/rules-ai/`, `skills/rules-infra/` e
        `skills/rules-backend/`; con `ai_approved=False`, `infra_approved=False` o `backend_approved=False` toglie `approved` dalla skill
        dell'area (solo quella del caso)."""
        src = self.dir / "src"
        (src / "skills" / "rules-base").mkdir(parents=True)
        parts = ("bin",) if case == "b1" else ("bin", "templates", "gate", "agents", "skills/rules-base", "skills/rules-ai",
                                               "skills/rules-infra", "skills/rules-backend", ".claude-plugin")
        tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--", *parts], capture_output=True, check=True).stdout
        for rel in filter(None, tracked.decode().split("\0")):
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, src / rel)
        if case in ("ai", "infra", "backend"):
            if not {"ai": ai_approved, "infra": infra_approved, "backend": backend_approved}[case]:
                skill = src / "skills" / f"rules-{case}" / "SKILL.md"
                skill.write_text(re.sub(r"(?m)^approved:.*\n", "", skill.read_text()))
        else:
            head = "---\nname: rules-base\ndescription: Regole di prova della sorgente finta.\nversion: 1\n"
            (src / "skills" / "rules-base" / "SKILL.md").write_text(
                head + ("approved: 2026-11-01\n" if approved else "") + "---\n# Regole di base (versione 1)\n\nUna regola di prova.\n")
        git = ["git", "-C", str(src), "-c", "user.name=prova", "-c", "user.email=prova@example.com", "-c", "commit.gpgsign=false"]
        subprocess.run([*git, "init", "-q", "-b", "main"], check=True, capture_output=True, env=self.env())
        subprocess.run([*git, "add", "-A"], check=True, capture_output=True, env=self.env())
        subprocess.run([*git, "commit", "-qm", "sorgente"], check=True, capture_output=True, env=self.env())
        return src


class FlowScriptTest(unittest.TestCase):
    def setUp(self):
        self.b = FlowBench()
        self.addCleanup(self.b.cleanup)
        self.evidence_before = sorted(p.name for p in FLOW_EVIDENCE.iterdir()) if FLOW_EVIDENCE.exists() else None

        def no_repo_evidence():
            after = sorted(p.name for p in FLOW_EVIDENCE.iterdir()) if FLOW_EVIDENCE.exists() else None
            self.assertEqual(after, self.evidence_before, "un test ha scritto nelle evidenze del repo")
        self.addCleanup(no_repo_evidence)

    def test_flow_syntax_and_static_rules(self):
        r = subprocess.run(["bash", "-n", str(FLOW_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        compile(FLOW_REG.read_text(), str(FLOW_REG), "exec")
        text = FLOW_SCRIPT.read_text()
        code = re.sub(r"(?m)^\s*#.*$", "", text)
        self.assertEqual(len(re.findall(r"=\(claude -p\b", code)), 1)
        self.assertEqual(len(re.findall(r'&& claude plugin validate --strict', code)), 1)
        self.assertRegex(code, r'timeout -k "\$KILL_AFTER" "\$STEP_TIMEOUT" "\$\{CMD\[@\]\}"')
        self.assertNotRegex(code, r"\brm\s+-[a-zA-Z]*[rR]")
        self.assertNotRegex(code, r"\b(pkill|killall)\b")
        self.assertNotRegex(code, r"\bkill\s")
        self.assertNotRegex(code, r"claude plugin (install|marketplace|enable|uninstall)|claude plugin eval")
        self.assertNotRegex(code, r"(?<!push )--force|--no-verify|reset --hard|git stash|--amend")
        self.assertIn("DEFAULT_TMP=/tmp/tollgate-b1", text)

    def test_flow_controlla_lists_steps(self):
        r = subprocess.run(["bash", str(FLOW_SCRIPT), "controlla"], capture_output=True, text=True, env=clean_env(), timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CONTROLLA: ok", r.stdout)
        for word in ("prepara", "passo1", "passo2", "registra", "/tmp/tollgate-b1/plugin", "approved: prova-b1", "plugin validate --strict",
                     "--plugin-dir", "--allowedTools", "--disallowedTools", "acceptEdits", "--model sonnet", "/tollgate:start #1 L1"):
            self.assertIn(word, r.stdout)
        self.assertEqual(r.stderr, "")

    def test_flow_refuses_outside_tmp(self):
        for root in ("/tmp/fuori-da-tollgate-b1", "/tmp/tollgate-b1x", "/tmp/tollgate-b1/../altro", str(Path.home() / "x"), "/tmp"):
            for mode in ("prepara", "passo1", "passo2", "registra"):
                with self.subTest(root=root, mode=mode):
                    r = self.b.run(mode, B1_FLOW_CHECK="0", B1_FLOW_ROOT=root, B1_FLOW_PLUGIN=str(self.b.dir / "p"))
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn("non è sotto /tmp/tollgate-b1/", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(Path("/tmp/fuori-da-tollgate-b1").exists())

    def test_flow_rules_base_only_in_copy(self):
        repo_skill = ROOT / "skills" / "rules-base" / "SKILL.md"
        repo_skill_before = repo_skill.read_bytes()
        r = self.b.prepara()
        self.assertIn("plan-check: ok", r.stdout)
        skill = self.b.plugin / "skills" / "rules-base" / "SKILL.md"
        text = skill.read_text()
        self.assertRegex(text, r"(?m)^name: rules-base$")
        self.assertRegex(text, r"(?m)^approved: prova-b1$")
        self.assertIn("Regole di prova della prova reale di B1: non sono le regole di B2", text)
        self.assertNotEqual(text.encode(), repo_skill_before, "la copia tiene la rules-base di prova")
        self.assertEqual(repo_skill.read_bytes(), repo_skill_before, "il repo non deve cambiare")
        self.assertFalse(list(self.b.plugin.rglob("APPROVED")))
        self.assertFalse(list(self.b.plugin.rglob("__pycache__")))
        # la copia è il plugin intero meno i dati di sviluppo; ogni percorso che plugin.json cita esiste
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertTrue((self.b.plugin / manifest["experimental"]["evals"]).is_dir())
        for part in ("evals", "LICENSES", "LICENSE", "gate", "templates", "statusline", "README.md"):
            self.assertTrue((self.b.plugin / part).exists(), part)
        for part in (".git", ".github", ".claude", ".superpowers", "docs", "spikes", "tests"):
            self.assertFalse((self.b.plugin / part).exists(), part)
        for part in (".claude-plugin/plugin.json", "bin/tollgate", "hooks/hooks.json", "agents/implementer.md", "skills/start/SKILL.md"):
            self.assertTrue((self.b.plugin / part).is_file(), part)
        # lo stato, il gh finto e il progetto
        self.assertTrue((self.b.root / "state" / ".tollgate-test").is_file())
        self.assertIn("fakegh.py", (self.b.root / "ghbin" / "gh").read_text())
        for part in ("tollgate.toml", "config.toml", "src/__init__.py", "tests/test_smoke.py", ".github/tollgate/VERSION"):
            self.assertTrue((self.b.flow / part).is_file(), part)
        self.assertFalse((self.b.flow / "piano-L1.md").exists())
        self.assertFalse((self.b.flow / "issue-1.md").exists())
        data = json.loads((self.b.root / "fakegh-data.json").read_text())
        self.assertIn("tomllib.load", data["issues"]["1"]["body"])
        self.assertIn("documentazione ufficiale di Python", data["issues"]["1"]["body"])
        remotes = subprocess.run(["git", "-C", str(self.b.flow), "config", "remote.origin.url"], capture_output=True, text=True).stdout.strip()
        self.assertEqual(remotes, "https://github.com/prova/flow.git")
        # un secondo prepara non cancella: rinomina
        self.b.prepara()
        self.assertEqual(len(list(self.b.root.glob("plugin.prev-*"))), 1)
        self.assertEqual(len(list(self.b.root.glob("flow.prev-*"))), 1)

    def test_flow_copy_is_made_of_tracked_files_only(self):
        """Un file non tracciato nella radice (per esempio un futuro `.env`) non entra nella copia."""
        stray = ROOT / "segreto-di-prova.local"
        stray.write_text("non deve finire nella copia\n")
        self.addCleanup(lambda: stray.unlink(missing_ok=True))
        self.b.prepara()
        self.assertFalse((self.b.plugin / stray.name).exists())
        self.assertTrue((self.b.plugin / "bin" / "tollgate").is_file())

    def test_flow_rules_vere_keeps_real_rules_base(self):
        src = self.b.src_repo()
        r = self.b.run("prepara", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        copy = self.b.plugin / "skills" / "rules-base" / "SKILL.md"
        self.assertEqual(copy.read_bytes(), (src / "skills" / "rules-base" / "SKILL.md").read_bytes())
        self.assertNotIn("prova-b1", copy.read_text())
        self.assertFalse(list(self.b.plugin.rglob("__pycache__")))

    def test_flow_rules_vere_refuses_unapproved(self):
        src = self.b.src_repo(approved=False)
        r = self.b.run("prepara", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("interruttore", r.stderr)
        self.assertFalse((self.b.flow / ".git").exists(), "ci si ferma prima di creare il progetto")
        self.assertEqual(self.b.calls(), [])

    def test_flow_rules_vere_out_dir(self):
        for rules, expected in (("vere", "docs/verifiche/evidenze/b2/flusso"), ("prova", "docs/verifiche/evidenze/b1/flusso"), (None, "docs/verifiche/evidenze/b1/flusso")):
            with self.subTest(rules=rules):
                extra = {} if rules is None else {"B1_FLOW_RULES": rules}
                r = subprocess.run(["bash", str(FLOW_SCRIPT), "controlla"], capture_output=True, text=True, env=clean_env(**extra), timeout=120)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("CONTROLLA: ok", r.stdout)
                self.assertIn(f"B1_FLOW_RULES: {rules or 'prova'}", r.stdout)
                self.assertIn(f"cartella delle uscite: {ROOT}/{expected}", r.stdout)
                self.assertIn(f"radice sorgente: {ROOT}", r.stdout)
                self.assertEqual(r.stderr, "")

    def test_flow_rules_unknown_value(self):
        for mode in ("controlla", "prepara", "passo1", "passo2", "registra"):
            with self.subTest(mode=mode):
                r = self.b.run(mode, B1_FLOW_RULES="altro")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("B1_FLOW_RULES", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(self.b.root.exists())

    def test_flow_src_only_in_check_mode(self):
        for mode in ("controlla", "prepara"):
            with self.subTest(mode=mode):
                r = self.b.run(mode, B1_FLOW_CHECK="0", B1_FLOW_SRC=str(self.b.dir / "src"))
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("B1_FLOW_SRC", r.stderr)
        self.assertFalse(self.b.root.exists())

    def test_flow_copy_fails_on_missing_tracked_file(self):
        src = self.b.src_repo()
        (src / "bin" / "tollgate").unlink()
        r = self.b.run("prepara", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("copia del plugin non riuscita", r.stderr)

    def test_flowreg_precarico(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b2-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        sub_ok = tmp / "agent-uno.jsonl"
        sub_ok.write_text(json.dumps({"message": {"content": "# Regole di base (versione 1)\n- R-BASE-01 ..."}}) + "\n")
        sub_no = tmp / "agent-due.jsonl"
        sub_no.write_text(json.dumps({"message": {"content": "niente"}}) + "\n")
        stream = tmp / "claude.jsonl"
        lines = [{"type": "system", "hook_event_name": "SubagentStop", "agent_transcript_path": str(p)} for p in (sub_ok, sub_no, tmp / "manca.jsonl")]
        lines.append({"type": "assistant", "message": {"content": [{"type": "text", "text": "ho letto R-BASE-03"}]}})
        stream.write_text("".join(json.dumps(x) + "\n" for x in lines))
        out = subprocess.run([sys.executable, "-B", str(FLOW_REG), "precarico", str(stream)], capture_output=True, text=True, check=True).stdout
        self.assertIn("metodo: trascrizioni", out)
        self.assertIn("titolo trovato in 1 di 2 trascrizioni", out)
        self.assertIn("agent-uno.jsonl: titolo trovato", out)
        self.assertIn("agent-due.jsonl: titolo assente", out)
        self.assertNotIn(str(tmp), out)
        # senza percorsi nelle uscite: solo l'indizio delle righe con R-BASE-
        bare = tmp / "bare.jsonl"
        bare.write_text(json.dumps({"type": "assistant", "message": {"content": "R-BASE-01"}}) + "\nnon json\n" + json.dumps({"x": "niente"}) + "\n")
        out = subprocess.run([sys.executable, "-B", str(FLOW_REG), "precarico", str(bare)], capture_output=True, text=True, check=True).stdout
        self.assertIn("metodo: indizio", out)
        self.assertIn("righe con R-BASE-: 1", out)

    def test_flow_requires_plugin_dir(self):
        self.b.prepara()
        r = self.b.run("passo1", B1_FLOW_PLUGIN="")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("senza --plugin-dir", r.stderr)
        r = self.b.run("passo1", B1_FLOW_PLUGIN=str(self.b.dir / "non-esiste"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("non esiste", r.stderr)
        self.assertEqual(self.b.calls(), [])

    def test_flow_passo1_validates_the_copy_first_and_stops_on_failure(self):
        self.b.prepara()
        r = self.b.run("passo1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        calls = self.b.calls()
        self.assertEqual(calls[0]["args"], ["plugin", "validate", "--strict", "."])
        self.assertEqual(os.path.realpath(calls[0]["cwd"]), os.path.realpath(self.b.plugin))
        self.assertEqual(calls[1]["args"][0], "-p")
        self.assertEqual(len(calls), 2)
        self.assertIn("uscita: 0", (self.b.out / "validate" / "validate-1.txt").read_text())
        # una validazione che fallisce ferma il passo: nessun claude -p, nessun tentativo consumato
        shutil.rmtree(self.b.out)
        self.b.log.unlink()
        r = self.b.run("passo1", B1_FAKE_VALIDATE_RC="3")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("plugin validate --strict ha fallito", r.stderr)
        self.assertEqual([c["args"][:2] for c in self.b.calls()], [["plugin", "validate"]])
        self.assertIn("uscita: 3", (self.b.out / "validate" / "validate-1.txt").read_text())
        self.assertFalse((self.b.out / "passo1").exists())

    def test_flow_allowed_tools(self):
        self.b.prepara()
        wt = self.b.worktree()
        for step in ("passo1", "passo2"):
            with self.subTest(step):
                r = self.b.run(step)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        first, second = self.b.claude_p()
        self.assertEqual(os.path.realpath(first["cwd"]), os.path.realpath(self.b.flow))
        self.assertEqual(os.path.realpath(second["cwd"]), os.path.realpath(wt))
        for call in (first, second):
            args = call["args"]
            self.assertEqual(Path(args[args.index("--plugin-dir") + 1]), self.b.plugin)
            self.assertEqual(args[args.index("--permission-mode") + 1], "acceptEdits")
            self.assertEqual(args[args.index("--model") + 1], "sonnet")
            self.assertEqual(args[args.index("--output-format") + 1], "stream-json")
            allowed = args[args.index("--allowedTools") + 1]
            self.assertEqual(allowed, FLOW_TOOLS)
            self.assertTrue({"WebFetch", "WebSearch"} <= set(allowed.split(",")))
            self.assertNotIn("context7", allowed)
            denied = args[args.index("--disallowedTools") + 1].split(",")
            for item in ("Bash(*/gh:*)", "Bash(git push https:*)", "Bash(git push ssh:*)", "Bash(git push git@:*)", "Bash(curl:*)", "Bash(wget:*)"):
                self.assertIn(item, denied)
            self.assertEqual(os.path.realpath(call["state"]), os.path.realpath(self.b.root / "state"))
        self.assertEqual(first["args"][-1], "/tollgate:start #1 L1")
        # i divieti di rete sono nel comando registrato
        self.assertIn("--disallowedTools", (self.b.out / "passo1" / "tentativo-1" / "argv.txt").read_text())

    def test_flow_claude_gets_the_fake_gh_first_in_path(self):
        self.b.prepara()
        r = self.b.run("passo1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        path, gh, data = Path(str(self.b.log) + ".env").read_text().splitlines()
        self.assertEqual(path.split(":")[0], str(self.b.root / "ghbin"))
        self.assertEqual(gh, str(ROOT / "tests" / "fakegh.py"))
        self.assertEqual(data, str(self.b.root / "fakegh-data.json"))
        self.assertTrue(os.access(self.b.root / "ghbin" / "gh", os.X_OK))

    def test_flow_passo2_writes_plan(self):
        self.b.prepara()
        self.b.worktree()
        r = self.b.run("passo2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        prompt = self.b.claude_p()[0]["args"][-1]
        i_write, i_commit, i_execute = prompt.index("Write"), prompt.index("committalo"), prompt.index("/tollgate:execute")
        self.assertLess(i_write, i_commit)
        self.assertLess(i_commit, i_execute)
        self.assertIn("docs/superpowers/plans/2026-10-27-prova-b1.md", prompt)
        self.assertIn("Non lanciare /tollgate:finish", prompt)
        plan = (B1 / "flow" / "piano-L1.md").read_text()
        self.assertIn(plan.strip(), prompt)
        self.assertIn("tests.test_conf.ConfTest::test_leggi_nome", prompt)

    def test_flow_passo2_needs_a_worktree_under_the_root(self):
        self.b.prepara()
        r = self.b.run("passo2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("worktree del lavoro non trovato", r.stderr)
        self.assertEqual(self.b.calls(), [])

    def test_flow_attempts_are_new_folders_and_capped_at_three(self):
        self.b.prepara()
        att1 = self.b.out / "passo1" / "tentativo-1"
        for n in (1, 2, 3):
            r = self.b.run("passo1")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            att = self.b.out / "passo1" / f"tentativo-{n}"
            for name in ("argv.txt", "claude.jsonl", "claude.err", "uscita.txt", "esito.txt"):
                self.assertTrue((att / name).is_file(), f"{att.name}/{name}")
            if n == 1:
                (att1 / "prova.txt").write_text("resta")
        self.assertEqual((att1 / "prova.txt").read_text(), "resta")
        esito = (self.b.out / "passo1" / "tentativo-2" / "esito.txt").read_text()
        self.assertIn("tentativo: 2", esito)
        self.assertIn("uscita: 0", esito)
        before = len(self.b.calls())
        r = self.b.run("passo1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("già 3 tentativi", r.stderr)
        self.assertEqual(len(self.b.calls()), before, "oltre il tetto non parte né validate né claude")
        self.assertFalse((self.b.out / "passo1" / "tentativo-4").exists())
        # un nuovo prepara rinomina i tentativi, non li cancella, e non azzera il tetto: vale per tutta la prova
        self.b.prepara()
        self.assertEqual(len(list(self.b.out.glob("passo1.prev-*"))), 1)
        self.assertTrue(list(self.b.out.glob("passo1.prev-*/tentativo-3")))
        before = len(self.b.calls())
        r = self.b.run("passo1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("già 3 tentativi in tutta la prova", r.stderr)
        self.assertEqual(len(self.b.calls()), before)
        self.assertFalse((self.b.out / "passo1").exists())

    def test_flow_attempt_cap_counts_moved_attempts_in_two_folders(self):
        self.b.prepara()
        for _ in range(2):
            self.assertEqual(self.b.run("passo1").returncode, 0)
        self.b.prepara()
        r = self.b.run("passo1")                      # il terzo della prova, il primo della nuova cartella
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.b.out / "passo1" / "tentativo-3").is_dir(), "la numerazione prosegue, non si ripete")
        r = self.b.run("passo1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("già 3 tentativi in tutta la prova", r.stderr)
        # l'altro passo ha il suo tetto
        self.b.worktree()
        self.assertEqual(self.b.run("passo2").returncode, 0)

    def test_flow_timeout_is_recorded(self):
        self.b.prepara()
        slow = self.b.bin / "claude"
        slow.write_text('#!/usr/bin/env bash\ncase "$1" in plugin) exit 0 ;; esac\nsleep 5\n')
        r = self.b.run("passo1", B1_FLOW_TIMEOUT="1")
        self.assertEqual(r.returncode, 124)
        self.assertIn("tetto di tempo superato", (self.b.out / "passo1" / "tentativo-1" / "esito.txt").read_text())

    def test_flow_registra_collects_the_evidence(self):
        self.b.prepara()
        wt = self.b.worktree()
        r = self.b.run("passo1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # un tentativo con un flusso finto: un Grep e un Bash del modello; una nota nel worktree
        att = self.b.out / "passo1" / "tentativo-1"
        stream = [{"type": "assistant", "parent_tool_use_id": None, "message": {"content": [
                      {"type": "tool_use", "name": "Bash", "input": {"command": "git push https://github.com/x/y main"}}]}},
                  {"type": "assistant", "parent_tool_use_id": "t1", "message": {"content": [
                      {"type": "tool_use", "name": "Grep", "input": {"pattern": "tomllib"}},
                      {"type": "tool_use", "name": "Read", "input": {"file_path": "config.toml"}}]}}]
        (att / "claude.jsonl").write_text("".join(json.dumps(x) + "\n" for x in stream) + "non json\n")
        (wt / ".tollgate-run" / "1").mkdir(parents=True)
        (wt / ".tollgate-run" / "1" / "research-1.md").write_text("nota\nesito: valida\n")
        r = self.b.run("registra")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = self.b.out / "registro-1"
        self.assertIn("9.9.9", (d / "versione-claude.txt").read_text())
        for name in ("events.jsonl", "stats.json", "status.json", "lookups.txt", "eventi-ricerca.jsonl", "comandi-modello.txt",
                     "grep-non-registrati.txt", "comandi-rischiosi.txt", "git-log-worktree.txt", "research-1.md"):
            self.assertTrue((d / name).is_file(), name)
        commands = (d / "comandi-modello.txt").read_text()
        self.assertIn("bash: git push https://github.com/x/y main", commands)
        self.assertIn("Grep: 1 (1)", commands)
        self.assertIn("Read: 1 (1)", commands)
        self.assertIn("git push https://github.com", (d / "comandi-rischiosi.txt").read_text())
        grep = (d / "grep-non-registrati.txt").read_text()
        self.assertIn("Grep del modello: 1; letture registrate (read): 0", grep)
        self.assertIn("non sono registrati", grep)
        self.assertIn("# lookups", (d / "lookups.txt").read_text())
        self.assertIn("Write ed Edit nudi", (d / "limiti.txt").read_text())
        self.assertIn("git -C x push", (d / "limiti.txt").read_text())
        self.assertEqual((d / "fallimenti.txt").read_text(), "")
        # un secondo registra non tocca il primo
        r = self.b.run("registra")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.b.out / "registro-2").is_dir())
        self.assertTrue((d / "research-1.md").is_file())

    def test_flow_registra_sums_greps_over_attempts_and_steps(self):
        self.b.prepara()
        wt = self.b.worktree()
        for step in ("passo1", "passo1", "passo2"):
            self.assertEqual(self.b.run(step).returncode, 0)

        def stream(greps, reads=0):
            blocks = [{"type": "tool_use", "name": "Grep", "input": {"pattern": f"p{i}"}} for i in range(greps)]
            blocks += [{"type": "tool_use", "name": "Read", "input": {"file_path": "x"}}] * reads
            return json.dumps({"type": "assistant", "parent_tool_use_id": None, "message": {"content": blocks}}) + "\n"
        (self.b.out / "passo1" / "tentativo-1" / "claude.jsonl").write_text(stream(2))
        (self.b.out / "passo1" / "tentativo-2" / "claude.jsonl").write_text(stream(0, 1))
        (self.b.out / "passo2" / "tentativo-1" / "claude.jsonl").write_text(stream(7))
        self.assertEqual(self.b.run("registra").returncode, 0)
        d = self.b.out / "registro-1"
        self.assertIn("Grep del modello: 9;", (d / "grep-non-registrati.txt").read_text())
        commands = (d / "comandi-modello.txt").read_text()
        self.assertEqual(commands.count("# strumenti del modello"), 1)
        self.assertIn("Grep: 9 (0)", commands)
        # anche il conteggio delle letture registrate somma le righe
        import sqlite3
        conn = sqlite3.connect(str(self.b.root / "state" / "tollgate.db"))
        try:
            conn.execute("INSERT INTO lookups (work, task, kind, target, at) VALUES (1, 1, 'read', 'a', 'x')")
            conn.execute("INSERT INTO lookups (work, task, kind, target, at) VALUES (1, 1, 'read', 'b', 'x')")
            conn.commit()
        except sqlite3.Error as e:
            self.skipTest(f"schema non pronto: {e}")
        finally:
            conn.close()
        self.assertEqual(self.b.run("registra").returncode, 0)
        self.assertIn("letture registrate (read): 2", (self.b.out / "registro-2" / "grep-non-registrati.txt").read_text())

    def web_stream(self, size):
        """Un flusso finto: un WebFetch con un risultato di `size` caratteri (testo di terzi) e un Bash con un risultato corto."""
        page = "P" * size
        use = {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "WebFetch", "input": {"url": "https://example.test/pagina", "prompt": "x"}},
            {"type": "tool_use", "id": "tu2", "name": "Bash", "input": {"command": "ls"}}]}}
        res = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu1", "content": page}]},
            "tool_use_result": {"bytes": size, "code": 200, "result": page, "url": "https://example.test/pagina"}}
        short = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu2", "content": "L" * 9000}]}}
        return [use, res, short]

    def test_flowreg_togli_pagine_replaces_long_web_results(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b3-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        stream = tmp / "claude.jsonl"
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.web_stream(22794)) + "non json\n")
        r = subprocess.run([sys.executable, "-B", str(FLOW_REG), "togli-pagine", str(stream)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = stream.read_text()
        self.assertNotIn("PPPPP", text)
        self.assertIn("[pagina di terzi tolta dalle evidenze: https://example.test/pagina, 22794 caratteri]", text)
        lines = text.splitlines()
        self.assertEqual(lines[-1], "non json")
        rows = [json.loads(x) for x in lines[:-1]]
        self.assertEqual(rows[1]["tool_use_result"]["result"], rows[1]["message"]["content"][0]["content"])
        self.assertEqual(rows[1]["tool_use_result"]["bytes"], 22794)
        self.assertEqual(rows[2]["message"]["content"][0]["content"], "L" * 9000, "un risultato di Bash non si tocca")

    def skill_stream(self, path, size):
        text = f"{'Base directory for this skill: ' + path}\n\n" + "S" * size
        return [{"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}]

    def test_flowreg_togli_pagine_replaces_external_skills_but_keeps_tollgate_ones(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b3-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        stream = tmp / "claude.jsonl"
        rows = (self.skill_stream("/tmp/bundled/claude-api", 109000) + self.skill_stream("/tmp/tollgate-b1/plugin/skills/rules-ai", 20000)
                + self.skill_stream("/tmp/x/piccola", 100))
        stream.write_text("".join(json.dumps(x) + "\n" for x in rows))
        for _ in range(2):
            subprocess.run([sys.executable, "-B", str(FLOW_REG), "togli-pagine", str(stream)], capture_output=True, text=True, check=True)
        out = [json.loads(x) for x in stream.read_text().splitlines()]
        self.assertRegex(out[0]["message"]["content"][0]["text"], r"^\[skill di terzi tolta dalle evidenze: claude-api, 109\d{3} caratteri\]$")
        self.assertIn("S" * 20000, out[1]["message"]["content"][0]["text"])
        self.assertIn("S" * 100, out[2]["message"]["content"][0]["text"])

    def test_flow_registra_strips_external_skills_from_the_streams(self):
        self.b.prepara()
        self.assertEqual(self.b.run("passo1").returncode, 0)
        stream = self.b.out / "passo1" / "tentativo-1" / "claude.jsonl"
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.skill_stream("/tmp/bundled/claude-api", 50000)))
        self.assertEqual(self.b.run("registra").returncode, 0)
        self.assertNotIn("SSSSS", stream.read_text())

    def test_flowreg_togli_pagine_keeps_short_results_and_is_idempotent(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b3-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        stream = tmp / "claude.jsonl"
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.web_stream(1500)))
        before = stream.read_text()
        for _ in range(2):
            subprocess.run([sys.executable, "-B", str(FLOW_REG), "togli-pagine", str(stream)], capture_output=True, text=True, check=True)
            self.assertEqual(stream.read_text(), before)
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.web_stream(30000)))
        for _ in range(2):
            subprocess.run([sys.executable, "-B", str(FLOW_REG), "togli-pagine", str(stream)], capture_output=True, text=True, check=True)
        self.assertNotIn("PPPPP", stream.read_text())

    def test_flow_registra_strips_third_party_pages_from_the_streams(self):
        self.b.prepara()
        self.assertEqual(self.b.run("passo1").returncode, 0)
        stream = self.b.out / "passo1" / "tentativo-1" / "claude.jsonl"
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.web_stream(22794)))
        r = self.b.run("registra")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("PPPPP", stream.read_text())
        self.assertIn("22794 caratteri", stream.read_text())
        self.assertEqual((self.b.out / "registro-1" / "fallimenti.txt").read_text(), "")

    @staticmethod
    def flowreg_module():
        sys.path.insert(0, str(B1))
        try:
            import flowreg
        finally:
            sys.path.remove(str(B1))
        return flowreg

    def test_tollgate_skill_by_folder_not_word(self):
        flowreg = self.flowreg_module()
        for path in ("/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/skills/execute",
                     "/home/USER/.claude/plugins/cache/x/tollgate/0.2.0/skills/start",
                     "/tmp/tollgate-b1/plugin/skills/start",
                     "/tmp/tollgate-eval-target/skills/init",
                     "/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p4/skills/execute",
                     "/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/skills/execute/"):
            self.assertTrue(flowreg.tollgate_skill(path), path)
        for path in ("/home/USER/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/writing-plans",
                     "/home/x/altro/skills/init",
                     "/home/USER/.claude/plugins/cache/x/altro/0.2.0/skills/start",
                     "/home/USER/tollgate/skills/start",
                     "/home/USER/MEGA/Plugin IT workflow/skills/writing-plans",
                     "/tmp/tollgate-b1/plugin/altro/start"):
            self.assertFalse(flowreg.tollgate_skill(path), path)

    def test_external_skill_keeps_tollgate_execute(self):
        flowreg = self.flowreg_module()
        text = f"{flowreg.SKILL_PREFIX} /home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/skills/execute\n\n" + "E" * 20000
        self.assertIsNone(flowreg.external_skill(text))
        other = text.replace("Plugin IT workflow/skills/execute", "x/superpowers/7.0.0/skills/writing-plans")
        self.assertEqual(flowreg.external_skill(other), "writing-plans")

    def hook_row(self, hook_name, text):
        return {"type": "system", "subtype": "hook_response", "hook_id": "h1", "hook_name": hook_name, "hook_event": "SessionStart",
                "output": text, "stdout": text, "stderr": "", "exit_code": 0, "outcome": "success"}

    def test_session_start_output_of_other_plugins_replaced(self):
        flowreg = self.flowreg_module()
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b3-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        stream = tmp / "claude.jsonl"
        other = json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "ALTRUI" * 1700}})
        short = json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "BREVE" * 200}}, indent=2)
        mine = json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "tollgate: " + "M" * 3000}})
        failed = json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                    "additionalContext": "(tollgate: controllo «x» in errore: " + "E" * 3000 + ")"}})
        rows = [self.hook_row("SessionStart:startup", other), self.hook_row("SessionStart:startup", short),
                self.hook_row("SessionStart:startup", mine), self.hook_row("SessionStart:startup", ""),
                self.hook_row("SessionStart:startup", failed),
                {"type": "system", "subtype": "hook_response", "hook_event": "PreToolUse", "output": "PRE" * 900, "stdout": "PRE" * 900}]
        stream.write_text("".join(json.dumps(x) + "\n" for x in rows))
        self.assertEqual([x.split(":")[1].split()[0] for x in flowreg.third_party_blocks(stream)], ["hook", "hook"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 2)
        text = stream.read_text()
        self.assertNotIn("ALTRUI", text)
        self.assertNotIn("BREVE", text)
        out = [json.loads(x) for x in text.splitlines()]
        self.assertEqual(out[0]["output"], f"[uscita di hook di terzi tolta dalle evidenze: SessionStart:startup, {len(other)} caratteri]")
        self.assertEqual(out[0]["stdout"], out[0]["output"])
        self.assertEqual(out[1]["stdout"], f"[uscita di hook di terzi tolta dalle evidenze: SessionStart:startup, {len(short)} caratteri]")
        self.assertEqual(out[2]["stdout"], mine, "l'uscita di tollgate resta")
        self.assertEqual(out[3]["stdout"], "")
        self.assertEqual(out[4]["stdout"], failed, "anche il messaggio d'errore del runner è di tollgate")
        self.assertEqual(out[5]["stdout"], "PRE" * 900, "solo gli hook SessionStart")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 0)
        self.assertEqual(flowreg.third_party_blocks(stream), [])

    def saved_copy_stream(self, copy_path):
        """Flusso finto: Grep e Read su una copia salvata (percorso dato) e un Read su un file normale, con risultati corti."""
        def use(i, name, **inp):
            return {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [{"type": "tool_use", "id": i, "name": name, "input": inp}]}}

        def res(i, text, tur):
            return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": i, "content": text}]},
                    "tool_use_result": tur}
        return [
            use("g1", "Grep", pattern="x", path=copy_path),
            res("g1", "TERZI-GREP riga", {"mode": "content", "numFiles": 0, "filenames": [], "content": "TERZI-GREP riga", "numLines": 1}),
            use("r1", "Read", file_path=copy_path),
            res("r1", "TERZI-READ riga", {"type": "text", "file": {"filePath": copy_path, "content": "TERZI-READ riga", "numLines": 1}}),
            use("r2", "Read", file_path="/work/progetto/README.md"),
            res("r2", "NORMALE riga", {"type": "text", "file": {"filePath": "/work/progetto/README.md", "content": "NORMALE riga"}}),
        ]

    def test_flowreg_togli_pagine_replaces_reads_and_greps_of_saved_copies(self):
        flowreg = self.flowreg_module()
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b4-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        stream = tmp / "claude.jsonl"
        copy = "/home/USER/.claude/projects/X/SESSIONE-1/tool-results/toolu_FAKE.txt"
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.saved_copy_stream(copy)))
        self.assertEqual([x.split(":")[0] for x in flowreg.third_party_blocks(stream)], ["2", "4"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 2)
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 0, "idempotente")
        text = stream.read_text()
        self.assertNotIn("TERZI", text)
        out = [json.loads(x) for x in text.splitlines()]
        marker = "[pagina di terzi tolta dalle evidenze: copia salvata da Claude Code (toolu_FAKE.txt), 15 caratteri]"
        self.assertEqual(out[1]["message"]["content"][0]["content"], marker)
        self.assertEqual(out[1]["tool_use_result"]["content"], marker)
        self.assertEqual(out[3]["message"]["content"][0]["content"], marker)
        self.assertEqual(out[3]["tool_use_result"]["file"]["content"], marker)
        self.assertEqual(out[5]["message"]["content"][0]["content"], "NORMALE riga", "un Read normale non si tocca")
        self.assertEqual(out[5]["tool_use_result"]["file"]["content"], "NORMALE riga")

    def test_committed_evidence_has_no_long_web_results(self):
        """Nelle evidenze pubbliche non c'è testo di terzi: né risultati di WebFetch/WebSearch oltre MAX_WEB_RESULT, né Read/Grep di copie
        salvate in tool-results/, né skill che non sono di
        tollgate, né uscite di hook SessionStart di altri plugin."""
        flowreg = self.flowreg_module()
        found = []
        for path in sorted((ROOT / "docs" / "verifiche" / "evidenze").rglob("*.jsonl")):
            found += [f"{path.relative_to(ROOT)}:{x}" for x in flowreg.third_party_blocks(path)]
        self.assertEqual(found, [], "testo di terzi nelle evidenze: lancia flowreg.py togli-pagine")

    def test_flow_registra_reports_collection_failures_but_collects_the_rest(self):
        self.b.prepara()
        self.assertEqual(self.b.run("passo1").returncode, 0)
        (self.b.root / "state" / "tollgate.db").write_text("non è un database")
        r = self.b.run("registra")
        self.assertNotEqual(r.returncode, 0)
        d = self.b.out / "registro-1"
        failures = (d / "fallimenti.txt").read_text()
        for name in ("events", "stats", "status"):
            self.assertIn(f"{name}: uscita", failures)
        self.assertIn("raccolta incompleta", r.stderr)
        for name in ("versione-claude.txt", "comandi-modello.txt", "grep-non-registrati.txt", "limiti.txt"):
            self.assertTrue((d / name).is_file(), name)

    def test_flowreg_lookups_events_and_commands(self):
        import sqlite3
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b1-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        db = tmp / "t.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""CREATE TABLE lookups (id INTEGER PRIMARY KEY, work INTEGER, task INTEGER, agent_id TEXT, session TEXT,
                                kind TEXT, target TEXT, at TEXT);
                              CREATE TABLE tasks (work INTEGER, number INTEGER, state TEXT, research_ok INTEGER, research_note TEXT);
                              INSERT INTO lookups VALUES (1, 1, 1, 'a1', 's', 'read', 'config.toml', '2026-10-28T10:00:00Z');
                              INSERT INTO lookups VALUES (2, 1, 1, 'a1', 's', 'fetch', 'https://docs.python.org/3/library/tomllib.html', '2026-10-28T10:01:00Z');
                              INSERT INTO tasks VALUES (1, 1, 'done', 1, 'Letto nel progetto\n- config.toml');""")
        conn.commit()
        conn.close()
        out = subprocess.run([sys.executable, "-B", str(FLOW_REG), "lookups", str(db)], capture_output=True, text=True, check=True).stdout
        self.assertIn("read\tconfig.toml", out)
        self.assertIn("fetch: 1", out)
        self.assertIn("read: 1", out)
        self.assertIn("# nota salvata, lavoro 1 task 1", out)
        self.assertIn("Letto nel progetto", out)
        events = tmp / "e.jsonl"
        events.write_text("".join(json.dumps({"seq": i, "type": t, "data": {}}) + "\n" for i, t in enumerate(["commit", "research_note", "veto", "research_reminder"])))
        out = subprocess.run([sys.executable, "-B", str(FLOW_REG), "eventi", str(events)], capture_output=True, text=True, check=True).stdout
        self.assertEqual([json.loads(x)["type"] for x in out.splitlines()], ["research_note", "veto", "research_reminder"])
        read_only = sqlite3.connect(str(db))
        try:
            self.assertEqual(read_only.execute("SELECT COUNT(*) FROM lookups").fetchone()[0], 2)
        finally:
            read_only.close()

    # ------------------------------------------------------------------ il caso `ai` (B3, Task 9)

    def ai_src(self, **kw):
        return self.b.src_repo(case="ai", **kw)

    def test_flow_case_ai_out_dir(self):
        r = self.b.run("controlla", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", B1_FLOW_OUT="")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CONTROLLA: ok", r.stdout)
        self.assertIn("B1_FLOW_CASE: ai", r.stdout)
        self.assertIn(f"cartella delle uscite: {ROOT}/docs/verifiche/evidenze/b3/flusso", r.stdout)
        self.assertEqual(r.stderr, "")
        for case in (None, "b1"):
            with self.subTest(case=case):
                extra = {} if case is None else {"B1_FLOW_CASE": case}
                r = self.b.run("controlla", B1_FLOW_OUT="", **extra)
                self.assertIn("B1_FLOW_CASE: b1", r.stdout)
                self.assertIn(f"cartella delle uscite: {ROOT}/docs/verifiche/evidenze/b1/flusso", r.stdout)

    def test_flow_case_ai_requires_real_rules(self):
        for rules in (None, "prova"):
            for mode in ("controlla", "prepara", "passo1", "passo2", "registra"):
                with self.subTest(rules=rules, mode=mode):
                    extra = {} if rules is None else {"B1_FLOW_RULES": rules}
                    r = self.b.run(mode, B1_FLOW_CASE="ai", **extra)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn("B1_FLOW_RULES", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(self.b.root.exists())

    def test_flow_case_unknown_value(self):
        for mode in ("controlla", "prepara", "passo1", "passo2", "registra"):
            with self.subTest(mode=mode):
                r = self.b.run(mode, B1_FLOW_CASE="altro")
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("B1_FLOW_CASE", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(self.b.root.exists())

    def test_real_flow_case_ai_prepara_proposes_profile(self):
        src = self.ai_src()
        r = self.b.run("prepara", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("plan-check: ok", r.stdout)
        text = (self.b.flow / "tollgate.toml").read_text()
        self.assertIn("[profiles.ai]", text)
        self.assertIn("services/notify.py", text)
        self.assertIn('mode = "detect"', text)
        for part in ("ai/summary.py", "services/notify.py", "tests/__init__.py", "tests/test_smoke.py"):
            self.assertTrue((self.b.flow / part).is_file(), part)
        self.assertFalse((self.b.flow / "docs" / "superpowers" / "tollgate-init").exists(), "la cartella della proposta si toglie")
        self.assertTrue(list(self.b.root.glob("tollgate-init.proposta-*")))
        git = ["git", "-C", str(self.b.flow)]
        log = subprocess.run([*git, "log", "--format=%s"], capture_output=True, text=True, check=True).stdout.split("\n")
        self.assertGreaterEqual(len([x for x in log if x]), 2)
        self.assertEqual(subprocess.run([*git, "status", "--porcelain"], capture_output=True, text=True).stdout, "")
        self.assertEqual(subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True).stdout,
                         subprocess.run([*git, "rev-parse", "origin/main"], capture_output=True, text=True).stdout)
        data = json.loads((self.b.root / "fakegh-data.json").read_text())
        self.assertIn("SUMMARY_MODEL", data["issues"]["1"]["body"])
        self.assertIn("repos/{owner}/{repo}/branches/main/protection", data["api_status"])
        sha = subprocess.run([*git, "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
        self.assertIn(sha, data["statuses"])
        self.assertEqual(self.b.calls(), [])

    def test_real_flow_case_ai_prepara_refuses_without_profile(self):
        src = self.ai_src(ai_approved=False)
        r = self.b.run("prepara", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("profiles.ai", r.stderr)

    def test_real_flow_case_ai_project_verifies(self):
        src = self.ai_src()
        r = self.b.run("prepara", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        verify = re.search(r'(?m)^verify = "(.*)"$', (self.b.flow / "tollgate.toml").read_text()).group(1)
        self.assertIn("unittest", verify)
        self.assertEqual((ROOT / "spikes" / "b3" / "flow" / "tollgate.toml").read_text(), (B1 / "flow" / "tollgate.toml").read_text())
        cmd = verify.replace("python3 ", "python3 -B ", 1)
        v = subprocess.run(cmd, shell=True, cwd=self.b.flow, capture_output=True, text=True, env=clean_env(PATH=os.environ["PATH"]))
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        self.assertFalse(list(self.b.flow.rglob("__pycache__")))

    def test_flowreg_project_dir_name(self):
        sys.path.insert(0, str(B1))
        self.addCleanup(sys.path.remove, str(B1))
        import flowreg
        self.assertEqual(flowreg.project_dir_name("/tmp/tollgate-b1/flow/.claude/worktrees/tg-1-x"),
                         "-tmp-tollgate-b1-flow--claude-worktrees-tg-1-x")
        self.assertEqual(flowreg.project_dir_name("/tmp/a b.c/x_y"), "-tmp-a-b-c-x-y")

    def _transcripts(self, home, cwd, session, agents):
        folder = Path(home) / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd) / session / "subagents"
        folder.mkdir(parents=True)
        for name, lines in agents.items():
            (folder / f"agent-{name}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))

    def test_real_registra_reads_only_matching_lines(self):
        src = self.ai_src()
        r = self.b.run("prepara", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.b.worktree()
        self.assertEqual(self.b.run("passo1", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere").returncode, 0)
        self.assertEqual(self.b.run("passo2", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere").returncode, 0)
        cwd1, cwd2 = "/tmp/prova.uno due/flow", "/tmp/prova.uno due/flow/.claude/worktrees/tg-1-x"
        for step, cwd, sid in (("passo1", cwd1, "sess-uno"), ("passo2", cwd2, "sess-due")):
            att = self.b.out / step / "tentativo-1"
            stream = [{"type": "system", "subtype": "init", "cwd": cwd, "session_id": sid},
                      {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}}]
            (att / "claude.jsonl").write_text("".join(json.dumps(x) + "\n" for x in stream))
        home = self.b.dir / "home"
        self._transcripts(home, cwd1, "sess-uno", {"a1": [
            {"isMeta": True, "message": {"role": "user", "content": "# Regole di base (versione 1)\n- R-BASE-01 ..."}},
            {"message": {"role": "user", "content": "SEGRETO-DEL-COMPITO nel brief"}}]})
        self._transcripts(home, cwd2, "sess-due", {"b2": [
            {"isMeta": True, "message": {"role": "user", "content": [{"type": "text", "text": "intro\n# Regole ai (versione 1)\n- R-AI-01"}]}},
            {"message": {"role": "assistant", "content": "SEGRETO-DEL-COMPITO risposta"}}]})
        # una sessione estranea, nella cartella giusta ma col session_id sbagliato, e una cartella estranea: non si leggono
        self._transcripts(home, cwd2, "sess-altra", {"c3": [{"isMeta": True, "message": {"content": "# Regole ai (versione 1)"}}]})
        self._transcripts(home, "/tmp/estranea", "sess-uno", {"d4": [{"isMeta": True, "message": {"content": "# Regole ai (versione 1)"}}]})
        r = self.b.run("registra", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = self.b.out / "registro-1"
        text = (d / "trascrizioni.txt").read_text()
        self.assertIn("agent-a1.jsonl", text)
        self.assertIn("agent-b2.jsonl", text)
        self.assertIn("# Regole di base (versione 1)", text)
        self.assertIn("# Regole ai (versione 1)", text)
        self.assertNotIn("SEGRETO", text)
        self.assertNotIn("R-AI-01", text)
        self.assertNotIn("agent-c3", text)
        self.assertNotIn("agent-d4", text)
        self.assertNotIn(str(home), text)
        self.assertIn("agent_type", (d / "tipi-task.txt").read_text())
        self.assertEqual((d / "fallimenti.txt").read_text(), "")
        self.assertNotIn("sess-uno", text)
        self.assertNotIn("sess-due", text)
        self.assertIn("sessione 1", text)
        self.assertIn("sessione 2", text)
        self.assertNotIn("prova", text, "i percorsi fuori da /tmp/tollgate-b1/ non si stampano")

    def test_flowreg_trascrizioni_skips_an_unsafe_session_id(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b3-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / "estranea" / "subagents").mkdir(parents=True)
        (tmp / "estranea" / "subagents" / "agent-x.jsonl").write_text("")
        stream = tmp / "claude.jsonl"
        stream.write_text(json.dumps({"type": "system", "cwd": "/tmp/tollgate-b1/flow", "session_id": "../../estranea"}) + "\n")
        r = subprocess.run([sys.executable, "-B", str(FLOW_REG), "trascrizioni", str(tmp), str(stream)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("session_id non valido", r.stdout)
        self.assertNotIn("estranea", r.stdout)
        self.assertNotIn("agent-x", r.stdout)

    def test_real_registra_ai_refuses_an_empty_home(self):
        src = self.ai_src()
        r = self.b.run("prepara", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(src))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.b.run("registra", B1_FLOW_CASE="ai", B1_FLOW_RULES="vere", HOME="")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("HOME", r.stderr)
        self.assertFalse((self.b.out / "registro-1").exists(), "si rifiuta prima di creare il registro")

    def test_registra_b1_does_not_look_at_transcripts(self):
        self.b.prepara()
        self.assertEqual(self.b.run("registra").returncode, 0)
        self.assertFalse((self.b.out / "registro-1" / "trascrizioni.txt").exists())


    # ------------------------------------------------------------------ il caso `infra` (B4, Task 8)

    def infra_src(self, **kw):
        return self.b.src_repo(case="infra", **kw)

    def infra_prepara(self, **kw):
        return self.b.run("prepara", B1_FLOW_CASE="infra", B1_FLOW_RULES="vere", B1_FLOW_SRC=str(self.infra_src(**kw)))

    def test_flow_case_infra_out_dir(self):
        r = self.b.run("controlla", B1_FLOW_CASE="infra", B1_FLOW_RULES="vere", B1_FLOW_OUT="")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CONTROLLA: ok", r.stdout)
        self.assertIn("B1_FLOW_CASE: infra", r.stdout)
        self.assertIn("[profiles.infra]", r.stdout)
        self.assertIn(f"cartella delle uscite: {ROOT}/docs/verifiche/evidenze/b4/flusso", r.stdout)
        self.assertEqual(r.stderr, "")

    def test_flow_case_infra_requires_real_rules(self):
        for rules in (None, "prova"):
            for mode in ("controlla", "prepara", "passo1", "passo2", "registra"):
                with self.subTest(rules=rules, mode=mode):
                    extra = {} if rules is None else {"B1_FLOW_RULES": rules}
                    r = self.b.run(mode, B1_FLOW_CASE="infra", **extra)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn("B1_FLOW_RULES", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(self.b.root.exists())

    def test_flow_case_unknown_value_names_infra(self):
        r = self.b.run("controlla", B1_FLOW_CASE="altro")
        self.assertNotEqual(r.returncode, 0)
        for value in ("b1", "ai", "infra"):
            self.assertIn(value, r.stderr)

    def test_real_flow_case_infra_prepara_proposes_profile(self):
        r = self.infra_prepara()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("plan-check: ok", r.stdout)
        text = (self.b.flow / "tollgate.toml").read_text()
        self.assertIn("[profiles.infra]", text)
        self.assertIn('"/vercel.json"', text)
        self.assertIn('"/Dockerfile"', text)
        self.assertIn('mode = "detect"', text)
        for part in ("vercel.json", "Dockerfile", "app/main.py", "tests/__init__.py", "tests/test_smoke.py"):
            self.assertTrue((self.b.flow / part).is_file(), part)
        self.assertFalse((self.b.flow / "docs" / "superpowers" / "tollgate-init").exists(), "la cartella della proposta si toglie")
        self.assertTrue(list(self.b.root.glob("tollgate-init.proposta-*")))
        git = ["git", "-C", str(self.b.flow)]
        self.assertEqual(subprocess.run([*git, "status", "--porcelain"], capture_output=True, text=True).stdout, "")
        self.assertEqual(subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True).stdout,
                         subprocess.run([*git, "rev-parse", "origin/main"], capture_output=True, text=True).stdout)
        data = json.loads((self.b.root / "fakegh-data.json").read_text())
        self.assertIn("vercel.json", data["issues"]["1"]["title"])
        self.assertIn("X-Content-Type-Options", data["issues"]["1"]["body"])
        self.assertIn("repos/{owner}/{repo}/branches/main/protection", data["api_status"])
        sha = subprocess.run([*git, "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
        self.assertIn(sha, data["statuses"])
        self.assertEqual(self.b.calls(), [])

    def test_real_flow_case_infra_prepara_refuses_without_profile(self):
        r = self.infra_prepara(infra_approved=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("profiles.infra", r.stderr)

    def test_real_flow_case_infra_project_verifies(self):
        r = self.infra_prepara()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        verify = re.search(r'(?m)^verify = "(.*)"$', (self.b.flow / "tollgate.toml").read_text()).group(1)
        self.assertIn("unittest", verify)
        self.assertEqual((ROOT / "spikes" / "b4" / "flow" / "tollgate.toml").read_text(), (B1 / "flow" / "tollgate.toml").read_text())
        cmd = verify.replace("python3 ", "python3 -B ", 1)
        v = subprocess.run(cmd, shell=True, cwd=self.b.flow, capture_output=True, text=True, env=clean_env(PATH=os.environ["PATH"]))
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        self.assertFalse(list(self.b.flow.rglob("__pycache__")))

    def disallowed(self, **extra):
        """La lista di `--disallowedTools` che `controlla` stampa per il passo 1 (`printf '%q'`)."""
        r = self.b.run("controlla", **extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        line = next(x for x in r.stdout.splitlines() if x.startswith("  passo1 (cwd"))
        argv = shlex.split(line.split("): ", 1)[1])
        return argv[argv.index("--disallowedTools") + 1].split(",")

    def test_flow_disallows_deploy_clis(self):
        denied = self.disallowed(B1_FLOW_CASE="infra", B1_FLOW_RULES="vere")
        for prog in ("vercel", "wrangler", "docker", "npx", "bunx", "pnpx", "bun", "npm", "pnpm", "yarn"):
            for form in (f"Bash({prog}:*)", f"Bash(*/{prog}:*)", f"Bash(command {prog}:*)", f"Bash(env {prog}:*)"):
                self.assertIn(form, denied)
        # `gh` non cambia: solo per percorso e dopo `command`
        self.assertIn("Bash(*/gh:*)", denied)
        self.assertIn("Bash(command gh:*)", denied)
        self.assertNotIn("Bash(env gh:*)", denied)
        for case, rules in (("b1", "prova"), ("ai", "vere")):
            with self.subTest(case=case):
                other = self.disallowed(B1_FLOW_CASE=case, B1_FLOW_RULES=rules)
                self.assertFalse([x for x in other if "vercel" in x or "npx" in x or "docker" in x])

    def test_real_flow_case_infra_project_has_no_credentials(self):
        project = ROOT / "spikes" / "b4" / "flow"
        found = [p.relative_to(project).as_posix() for p in project.rglob("*")
                 if p.name == ".vercel" or p.name.startswith((".env", ".dev.vars", "wrangler", ".wrangler"))]
        self.assertEqual(found, [])
        self.assertTrue((project / "vercel.json").is_file())

    def test_real_flow_case_infra_task_forbids_publishing(self):
        project = ROOT / "spikes" / "b4" / "flow"
        for name in ("issue-1.md", "piano-L1.md"):
            with self.subTest(name):
                text = " ".join((project / name).read_text().split())
                self.assertIn("non è collegato a nessun servizio", text)
                self.assertIn("prova senza pubblicazione non si fa", text)
                self.assertRegex(text, r"(?i)(nel )?report (scrivi|dice)")

    def _flow_stream(self, commands, **extra):
        """prepara, un passo 1 finto e un flusso con i `Bash` dati: ritorna la cartella del primo registro."""
        att = self.b.out / "passo1" / "tentativo-1"
        self.assertEqual(self.b.run("passo1", **extra).returncode, 0)
        stream = [{"type": "assistant", "parent_tool_use_id": None, "message": {"content": [
                      {"type": "tool_use", "name": "Bash", "input": {"command": c}} for c in commands]}}]
        (att / "claude.jsonl").write_text("".join(json.dumps(x) + "\n" for x in stream))
        r = self.b.run("registra", **extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.b.out / "registro-1"

    def test_real_registra_flags_deploy_clis(self):
        extra = dict(B1_FLOW_CASE="infra", B1_FLOW_RULES="vere")
        self.assertEqual(self.infra_prepara().returncode, 0)
        d = self._flow_stream(["npx vercel --prod", "bash -c 'npx vercel --prod'", "ls && docker build .", "/usr/local/bin/npm install",
                               "cat vercel.json", "git add vercel.json", "python3 -m unittest discover"], **extra)
        risky = (d / "comandi-rischiosi.txt").read_text()
        for cmd in ("npx vercel --prod", "bash -c 'npx vercel --prod'", "ls && docker build .", "/usr/local/bin/npm install"):
            self.assertIn(f"bash: {cmd}\n", risky)
        for cmd in ("cat vercel.json", "git add vercel.json", "python3 -m unittest"):
            self.assertNotIn(cmd, risky)
        self.assertIn("env VAR", (d / "limiti.txt").read_text())

    def test_registra_deploy_clis_only_for_infra(self):
        self.b.prepara()
        d = self._flow_stream(["npx vercel --prod", "git push https://github.com/x/y main"])
        risky = (d / "comandi-rischiosi.txt").read_text()
        self.assertIn("git push https://github.com", risky)
        self.assertNotIn("npx vercel", risky)
        self.assertNotIn("env VAR", (d / "limiti.txt").read_text())

    def test_real_registra_reads_infra_title(self):
        self.assertEqual(self.infra_prepara().returncode, 0)
        self.assertEqual(self.b.run("passo1", B1_FLOW_CASE="infra", B1_FLOW_RULES="vere").returncode, 0)
        cwd = "/tmp/prova.uno due/flow"
        stream = [{"type": "system", "subtype": "init", "cwd": cwd, "session_id": "sess-uno"}]
        (self.b.out / "passo1" / "tentativo-1" / "claude.jsonl").write_text("".join(json.dumps(x) + "\n" for x in stream))
        self._transcripts(self.b.dir / "home", cwd, "sess-uno", {"a1": [
            {"isMeta": True, "message": {"role": "user", "content": "# Regole di base (versione 1)\n- R-BASE-01 ..."}},
            {"isMeta": True, "message": {"role": "user", "content": "# Regole infra (versione 1)\n- R-INFRA-01 ..."}},
            {"message": {"role": "user", "content": "SEGRETO-DEL-COMPITO nel brief"}}]})
        r = self.b.run("registra", B1_FLOW_CASE="infra", B1_FLOW_RULES="vere")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = self.b.out / "registro-1"
        text = (d / "trascrizioni.txt").read_text()
        self.assertIn("agent-a1.jsonl: # Regole infra (versione 1) (isMeta: sì)", text)
        self.assertIn("# Regole di base (versione 1)", text)
        self.assertNotIn("SEGRETO", text)
        self.assertNotIn("R-INFRA-01", text)
        self.assertIn("agent_type", (d / "tipi-task.txt").read_text())
        self.assertEqual((d / "fallimenti.txt").read_text(), "")

    def test_real_registra_infra_refuses_an_empty_home(self):
        self.assertEqual(self.infra_prepara().returncode, 0)
        r = self.b.run("registra", B1_FLOW_CASE="infra", B1_FLOW_RULES="vere", HOME="")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("HOME", r.stderr)
        self.assertFalse((self.b.out / "registro-1").exists())


    # ------------------------------------------------------------------ il caso `backend` (B5, Task 7)

    BACKEND_EXTRA = dict(B1_FLOW_CASE="backend", B1_FLOW_RULES="vere")

    def backend_src(self, **kw):
        return self.b.src_repo(case="backend", **kw)

    def backend_prepara(self, **kw):
        return self.b.run("prepara", B1_FLOW_SRC=str(self.backend_src(**kw)), **self.BACKEND_EXTRA)

    def test_flow_case_backend_out_dir(self):
        r = self.b.run("controlla", B1_FLOW_OUT="", **self.BACKEND_EXTRA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CONTROLLA: ok", r.stdout)
        self.assertIn("B1_FLOW_CASE: backend", r.stdout)
        self.assertIn("[profiles.backend]", r.stdout)
        self.assertIn(f"cartella delle uscite: {ROOT}/docs/verifiche/evidenze/b5/flusso", r.stdout)
        self.assertEqual(r.stderr, "")

    def test_flow_case_backend_requires_real_rules(self):
        for rules in (None, "prova"):
            for mode in ("controlla", "prepara", "passo1", "passo2", "registra"):
                with self.subTest(rules=rules, mode=mode):
                    extra = {} if rules is None else {"B1_FLOW_RULES": rules}
                    r = self.b.run(mode, B1_FLOW_CASE="backend", **extra)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn("B1_FLOW_RULES", r.stderr)
        self.assertEqual(self.b.calls(), [])
        self.assertFalse(self.b.root.exists())

    def test_flow_case_unknown_value_names_backend(self):
        r = self.b.run("controlla", B1_FLOW_CASE="altro")
        self.assertNotEqual(r.returncode, 0)
        for value in ("b1", "ai", "infra", "backend"):
            self.assertIn(value, r.stderr)

    def test_real_flow_case_backend_prepara_proposes_profile(self):
        marker_file = ROOT / "spikes" / "b5" / "flow" / "edge" / "index.ts"
        fragment = tomllib.loads((ROOT / "templates" / "profiles" / "backend.toml").read_text())
        self.assertTrue([m for m in fragment["detect"]["content"] if m in marker_file.read_text()],
                        "edge/index.ts deve contenere un marcatore del frammento vero")
        r = self.backend_prepara()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("plan-check: ok", r.stdout)
        text = (self.b.flow / "tollgate.toml").read_text()
        profile = tomllib.loads(text)["profiles"]["backend"]
        self.assertIn("/server/**", profile["paths"])
        self.assertIn("edge/index.ts", profile["paths"])
        self.assertEqual([x for x in profile["paths"] if x.lstrip("/").startswith("supabase")], [])
        self.assertIn('mode = "detect"', text)
        for part in ("server/app.py", "edge/index.ts", "supabase/functions/hello/index.ts", "tests/__init__.py", "tests/test_smoke.py"):
            self.assertTrue((self.b.flow / part).is_file(), part)
        self.assertFalse((self.b.flow / "docs" / "superpowers" / "tollgate-init").exists(), "la cartella della proposta si toglie")
        self.assertTrue(list(self.b.root.glob("tollgate-init.proposta-*")))
        git = ["git", "-C", str(self.b.flow)]
        self.assertEqual(subprocess.run([*git, "status", "--porcelain"], capture_output=True, text=True).stdout, "")
        self.assertEqual(subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True).stdout,
                         subprocess.run([*git, "rev-parse", "origin/main"], capture_output=True, text=True).stdout)
        data = json.loads((self.b.root / "fakegh-data.json").read_text())
        self.assertIn("/health", data["issues"]["1"]["title"])
        self.assertIn("application/json", data["issues"]["1"]["body"])
        self.assertIn("repos/{owner}/{repo}/branches/main/protection", data["api_status"])
        sha = subprocess.run([*git, "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
        self.assertIn(sha, data["statuses"])
        self.assertEqual(self.b.calls(), [])

    def test_real_flow_case_backend_prepara_refuses_without_profile(self):
        r = self.backend_prepara(backend_approved=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("profiles.backend", r.stderr)

    def test_real_flow_case_backend_project_verifies(self):
        r = self.backend_prepara()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        verify = re.search(r'(?m)^verify = "(.*)"$', (self.b.flow / "tollgate.toml").read_text()).group(1)
        self.assertIn("unittest", verify)
        self.assertEqual((ROOT / "spikes" / "b5" / "flow" / "tollgate.toml").read_text(), (B1 / "flow" / "tollgate.toml").read_text())
        cmd = verify.replace("python3 ", "python3 -B ", 1)
        v = subprocess.run(cmd, shell=True, cwd=self.b.flow, capture_output=True, text=True, env=clean_env(PATH=os.environ["PATH"]))
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        self.assertFalse(list(self.b.flow.rglob("__pycache__")))

    def test_flow_disallows_service_clis_backend(self):
        denied = self.disallowed(**self.BACKEND_EXTRA)
        for prog in ("vercel", "wrangler", "docker", "npx", "bunx", "pnpx", "bun", "npm", "pnpm", "yarn", "supabase", "deno", "node"):
            for form in (f"Bash({prog}:*)", f"Bash(*/{prog}:*)", f"Bash(command {prog}:*)", f"Bash(env {prog}:*)"):
                self.assertIn(form, denied)
        self.assertIn("Bash(*/gh:*)", denied)
        infra = self.disallowed(B1_FLOW_CASE="infra", B1_FLOW_RULES="vere")
        self.assertFalse([x for x in infra if any(p in x for p in ("supabase", "deno", "node"))], "i tre programmi in più sono del solo caso backend")

    def test_real_flow_case_backend_project_has_no_credentials(self):
        project = ROOT / "spikes" / "b5" / "flow"
        found = [p.relative_to(project).as_posix() for p in project.rglob("*")
                 if p.name in (".vercel", ".wrangler") or p.name.startswith((".env", ".dev.vars", "wrangler", "vercel"))]
        self.assertEqual(found, [])
        for part in ("server/app.py", "edge/index.ts", "supabase/functions/hello/index.ts"):
            self.assertTrue((project / part).is_file(), part)
        ignore = (project / ".gitignore").read_text().split()
        for entry in (".env*", ".dev.vars*", ".wrangler/", ".vercel/", "__pycache__/", "reports/"):
            self.assertIn(entry, ignore)

    def test_real_flow_case_backend_task_does_not_list_report_lines(self):
        """Lezione di B4 (decisione 14): il lavoro chiede la rotta e il test, ma non elenca le righe del report che le regole chiedono,
        così compaiono solo se le regole sono state lette."""
        project = ROOT / "spikes" / "b5" / "flow"
        for name in ("issue-1.md", "piano-L1.md"):
            with self.subTest(name):
                text = " ".join((project / name).read_text().split())
                self.assertIn("GET /health", text)
                self.assertRegex(text, r"(?i)\btest\b")
                self.assertRegex(text, r"(?i)non (si )?avvi\w+ (un )?server su una porta")
                self.assertNotRegex(text, r"(?i)contratt|indirizzo|prova locale|pagina ufficiale|chi (li|le|lo) usa")

    def test_real_registra_reads_backend_title(self):
        self.assertEqual(self.backend_prepara().returncode, 0)
        self.assertEqual(self.b.run("passo1", **self.BACKEND_EXTRA).returncode, 0)
        cwd = "/tmp/prova.uno due/flow"
        stream = [{"type": "system", "subtype": "init", "cwd": cwd, "session_id": "sess-uno"}]
        (self.b.out / "passo1" / "tentativo-1" / "claude.jsonl").write_text("".join(json.dumps(x) + "\n" for x in stream))
        self._transcripts(self.b.dir / "home", cwd, "sess-uno", {"a1": [
            {"isMeta": True, "message": {"role": "user", "content": "# Regole di base (versione 1)\n- R-BASE-01 ..."}},
            {"isMeta": True, "message": {"role": "user", "content": "# Regole backend (versione 1)\n- R-BACKEND-01 ..."}},
            {"message": {"role": "user", "content": "SEGRETO-DEL-COMPITO nel brief"}}]})
        r = self.b.run("registra", **self.BACKEND_EXTRA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = self.b.out / "registro-1"
        text = (d / "trascrizioni.txt").read_text()
        self.assertIn("agent-a1.jsonl: # Regole backend (versione 1) (isMeta: sì)", text)
        self.assertIn("# Regole di base (versione 1)", text)
        self.assertNotIn("SEGRETO", text)
        self.assertNotIn("R-BACKEND-01", text)
        self.assertIn("agent_type", (d / "tipi-task.txt").read_text())
        self.assertEqual((d / "fallimenti.txt").read_text(), "")

    def test_real_registra_flags_service_clis_backend(self):
        self.assertEqual(self.backend_prepara().returncode, 0)
        d = self._flow_stream(["npx wrangler kv key put K V", "deno run x.ts", "ls && supabase functions deploy hello", "/usr/bin/node app.js",
                               "cat edge/index.ts", "git add supabase/functions/hello/index.ts", "python3 -m unittest discover"],
                              **self.BACKEND_EXTRA)
        risky = (d / "comandi-rischiosi.txt").read_text()
        for cmd in ("npx wrangler kv key put K V", "deno run x.ts", "ls && supabase functions deploy hello", "/usr/bin/node app.js"):
            self.assertIn(f"bash: {cmd}\n", risky)
        for cmd in ("cat edge/index.ts", "git add supabase", "python3 -m unittest"):
            self.assertNotIn(cmd, risky)
        limits = (d / "limiti.txt").read_text()
        self.assertIn("env VAR", limits)
        self.assertIn("supabase, deno e node", limits)

    def bash_saved_stream(self):
        """Flusso finto con quattro `Bash`: tre leggono una copia salvata (percorso in `tool-results/`), uno legge un file normale."""
        copy = "/home/USER/.claude/projects/X/SESSIONE-1/tool-results/toolu_FAKE.txt"
        commands = [f"cat {copy}", f"sed -n '1,40p' {copy}", f"grep -n x {copy} | head -5", "cat app.py"]
        out = []
        for i, cmd in enumerate(commands):
            text = "NORMALE riga" if cmd == "cat app.py" else "TERZI-BASH riga"
            out.append({"type": "assistant", "parent_tool_use_id": None, "message": {"content": [
                {"type": "tool_use", "id": f"b{i}", "name": "Bash", "input": {"command": cmd}}]}})
            out.append({"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"b{i}", "content": text}]},
                        "tool_use_result": {"stdout": text, "stderr": "", "interrupted": False}})
        return out

    def test_togli_pagine_bash_reading_saved_copy(self):
        flowreg = self.flowreg_module()
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b5-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        stream = tmp / "claude.jsonl"
        stream.write_text("".join(json.dumps(x) + "\n" for x in self.bash_saved_stream()))
        self.assertEqual([x.split(":")[0] for x in flowreg.third_party_blocks(stream)], ["2", "4", "6"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 3)
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 0, "idempotente")
        text = stream.read_text()
        self.assertNotIn("TERZI", text)
        out = [json.loads(x) for x in text.splitlines()]
        marker = "[pagina di terzi tolta dalle evidenze: copia salvata da Claude Code (toolu_FAKE.txt), 15 caratteri]"
        for i in (1, 3, 5):
            self.assertEqual(out[i]["message"]["content"][0]["content"], marker)
            self.assertEqual(out[i]["tool_use_result"], {"stdout": marker, "stderr": "", "interrupted": False})
        self.assertEqual(out[7]["message"]["content"][0]["content"], "NORMALE riga", "un Bash su un file normale non si tocca")
        self.assertEqual(out[7]["tool_use_result"]["stdout"], "NORMALE riga")

    def test_third_party_detects_bash_stdout(self):
        flowreg = self.flowreg_module()
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-b5-flowreg-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        marker = "[pagina di terzi tolta dalle evidenze: copia salvata da Claude Code (toolu_FAKE.txt), 15 caratteri]"
        lines = self.bash_saved_stream()[:2]
        lines[1]["message"]["content"][0]["content"] = marker  # il blocco è già il segnaposto, lo `stdout` ha ancora il testo
        stream = tmp / "claude.jsonl"
        stream.write_text("".join(json.dumps(x) + "\n" for x in lines))
        self.assertEqual(flowreg.third_party_blocks(stream), ["2: copia salvata (15)"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(flowreg.togli_pagine([str(stream)]), 1)
        self.assertNotIn("TERZI", stream.read_text())
        self.assertEqual(json.loads(stream.read_text().splitlines()[1])["tool_use_result"]["stdout"], marker)
        self.assertEqual(flowreg.third_party_blocks(stream), [])


if __name__ == "__main__":
    unittest.main()
