### Task 13: Wrapper `hooks/run`, `hooks.json`, `plugin.json`, skill `off` e `on`

**Files:**
- Create: `hooks/run` (eseguibile)
- Create: `hooks/hooks.json`
- Create: `.claude-plugin/plugin.json`
- Create: `skills/off/SKILL.md`, `skills/on/SKILL.md`
- Test: `tests/test_wrapper.py`, `tests/test_manifest.py`

**Interfaces:**
- Consumes: `bin/tollgate hook <evento>` (Task 12); esito D1 del Task 1 per `dependencies`.
- Produces: il wrapper con le uscite di 7.1 (criterio 14); `OFF` con `until=<epoch>`; `off.log` e `skipped.log` nella cartella di stato (decisione 5); il segnalino `bound/<sessione>` letto dal wrapper (decisione 22).

- [ ] **Step 1: Test del wrapper**

`tests/test_wrapper.py`:

```python
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.helpers import ROOT, TempState, make_origin_repo

FAKE_BIN = textwrap.dedent('''\
    #!/usr/bin/env python3
    import os, sys, time
    sys.stdin.read()
    m = os.environ.get("FAKE_MODE", "0")
    if m == "sleep":
        time.sleep(30)
    if m == "raise":
        raise RuntimeError("guasto")
    print("OUT")
    sys.stderr.write("ERR\\n")
    sys.exit(int(m))
''')
TOML = 'schema_version = 1\n[gate]\nmode = "protected"\n[hooks]\ntimeout_s = 1\n'
TOOLS = ["bash", "git", "sed", "tr", "head", "cat", "date", "mkdir", "rm", "mktemp", "sleep",
         "awk", "dirname", "kill", "env"]


class WrapperTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate wrapper "))
        self.plugin = self.tmp / "plugin"
        (self.plugin / "hooks").mkdir(parents=True)
        (self.plugin / "bin").mkdir()
        shutil.copy(ROOT / "hooks" / "run", self.plugin / "hooks" / "run")
        (self.plugin / "bin" / "tollgate").write_text(FAKE_BIN)
        (self.plugin / "bin" / "tollgate").chmod(0o755)
        self.repo, _, _ = make_origin_repo(self.tmp / "r", {"a.txt": "a\n"}, TOML)
        self.plain = self.tmp / "plain"
        self.plain.mkdir()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_wrapper(self, event, payload=None, *, cwd=None, mode="0", path=None):
        payload = payload or {"hook_event_name": event, "session_id": "s1",
                              "cwd": str(cwd or self.repo), "tool_name": "Bash",
                              "tool_input": {"command": "ls"}}
        env = self.ts.env()
        env["FAKE_MODE"] = mode
        if path is not None:
            env["PATH"] = path
        t0 = time.monotonic()
        r = subprocess.run([str(self.plugin / "hooks" / "run"), event],
                           input=json.dumps(payload), capture_output=True, text=True, env=env,
                           cwd=str(cwd or self.repo), timeout=30)
        return r, time.monotonic() - t0

    def test_control_errors_become_2(self):
        for mode in ("1", "127", "raise"):
            with self.subTest(mode=mode):
                r, _ = self.run_wrapper("PreToolUse", mode=mode)
                self.assertEqual(r.returncode, 2)
                self.assertIn(f"touch {self.ts.dir}/OFF", r.stderr)
                self.assertIn(str(self.plugin / "bin" / "tollgate"), r.stderr)

    def test_timeout_becomes_2(self):
        r, elapsed = self.run_wrapper("PreToolUse", mode="sleep")
        self.assertEqual(r.returncode, 2)
        self.assertLess(elapsed, 10)

    def test_informative_errors_become_0(self):
        for event in ("PostToolUse", "SubagentStop", "SessionStart", "UserPromptExpansion"):
            with self.subTest(event=event):
                self.assertEqual(self.run_wrapper(event, mode="1")[0].returncode, 0)

    def test_zero_and_two_pass_through(self):
        r, _ = self.run_wrapper("PreToolUse", mode="2")
        self.assertEqual((r.returncode, r.stdout.strip()), (2, "OUT"))
        self.assertEqual(self.run_wrapper("SubagentStop", mode="2")[0].returncode, 2)
        self.assertEqual(self.run_wrapper("PreToolUse", mode="0")[0].returncode, 0)

    def test_inactive_repo_exits_0_without_running(self):
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, mode="2")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_bound_marker_makes_any_dir_active(self):
        (self.ts.dir / "bound").mkdir()
        (self.ts.dir / "bound" / "s1").touch()
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, mode="2")
        self.assertEqual(r.returncode, 2)

    def _path_without_python(self):
        d = self.tmp / "nopy"
        d.mkdir(exist_ok=True)
        for t in TOOLS:
            src = shutil.which(t)
            if src and not (d / t).exists():
                os.symlink(src, d / t)
        return str(d)

    def test_without_python(self):
        path = self._path_without_python()
        self.assertEqual(self.run_wrapper("PreToolUse", path=path)[0].returncode, 2)
        self.assertEqual(self.run_wrapper("PostToolUse", path=path)[0].returncode, 0)
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, path=path)
        self.assertEqual(r.returncode, 0)

    def test_off_on_and_expiry(self):
        off = {"hook_event_name": "UserPromptExpansion", "session_id": "s1",
               "cwd": str(self.repo), "command_name": "tollgate:off", "command_args": "2",
               "expansion_type": "slash_command"}
        r, _ = self.run_wrapper("UserPromptExpansion", off, mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("until=", (self.ts.dir / "OFF").read_text())
        r, _ = self.run_wrapper("PreToolUse", mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("spento", r.stderr)
        self.assertIn("PreToolUse", (self.ts.dir / "skipped.log").read_text())
        on = dict(off, command_name="tollgate:on", command_args="")
        self.run_wrapper("UserPromptExpansion", on)
        self.assertFalse((self.ts.dir / "OFF").exists())
        log = (self.ts.dir / "off.log").read_text().splitlines()
        self.assertRegex(log[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.000000Z off \d+$")
        self.assertRegex(log[1], r"Z on$")
        (self.ts.dir / "OFF").write_text(f"until={int(time.time()) - 60}\n")
        self.assertEqual(self.run_wrapper("PreToolUse", mode="2")[0].returncode, 2)
        self.assertFalse((self.ts.dir / "OFF").exists())

    def test_off_without_hours(self):
        off = {"hook_event_name": "UserPromptExpansion", "session_id": "s1",
               "cwd": str(self.plain), "command_name": "tollgate:off", "command_args": ""}
        self.run_wrapper("UserPromptExpansion", off)
        self.assertEqual((self.ts.dir / "OFF").read_text(), "")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_manifest.py`:

```python
import json
import re
import unittest

from tests.helpers import ROOT


class ManifestTest(unittest.TestCase):
    def test_hooks_json(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptExpansion", "PreToolUse",
                                      "PostToolUse", "SubagentStart", "SubagentStop"})
        pre = hooks["PreToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "Agent", "SendMessage"):
            self.assertRegex(tool, f"^(?:{pre})$")
        self.assertRegex("mcp__srv__x", f"^(?:{pre})$")
        self.assertNotRegex("Read", f"^(?:{pre})$")
        post = hooks["PostToolUse"][0]["matcher"]
        for tool in ("Edit", "Write", "Bash", "Agent", "Skill", "SubagentHandback"):
            self.assertRegex(tool, f"^(?:{post})$")
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

    def test_off_on_skills_user_only(self):
        for name in ("off", "on"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
            self.assertRegex(text, rf"(?m)^name: {name}$")

    def test_wrapper_executable(self):
        import os
        self.assertTrue(os.access(ROOT / "hooks" / "run", os.X_OK))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_wrapper tests.test_manifest -v`
Expected: FAIL (file mancanti).

- [ ] **Step 3: `hooks/run`**

```bash
#!/usr/bin/env bash
# Wrapper degli hook di tollgate (spec 7.1). Uso: hooks/run <EventoDiClaudeCode>
# Solo l'uscita 2 blocca: qui ogni errore di un hook di controllo diventa 2,
# ogni errore di un hook informativo diventa 0 con un avviso.
set -u
EVENT="${1:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/bin/tollgate"
STATE="${HOME}/.local/state/tollgate"
if [ -n "${TOLLGATE_STATE:-}" ] && [ -f "${TOLLGATE_STATE}/.tollgate-test" ]; then
  STATE="$TOLLGATE_STATE"
fi
OFF="$STATE/OFF"
HINT="Per spegnere tollgate: /tollgate:off, oppure dal terminale: touch $STATE/OFF"
case "$EVENT" in PreToolUse) CONTROL=yes ;; *) CONTROL=no ;; esac
INPUT="$(cat)"

now_iso() { date -u +%Y-%m-%dT%H:%M:%S.000000Z; }
iso_of() { date -u -d "@$1" +%Y-%m-%dT%H:%M:%S.000000Z 2>/dev/null \
  || date -u -r "$1" +%Y-%m-%dT%H:%M:%S.000000Z; }
# Valore stringa di una chiave dell'input, senza jq (best effort: basta per cwd, sessione, comando).
json_str() {
  printf '%s' "$INPUT" | tr '\n' ' ' \
    | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -n 1
}

# 1. Interruttore senza Python né DB.
if [ "$EVENT" = "UserPromptExpansion" ]; then
  CMD="$(json_str command_name)"
  if [ "$CMD" = "tollgate:off" ]; then
    mkdir -p "$STATE"
    HOURS="$(json_str command_args | tr -cd '0-9')"
    UNTIL=""
    if [ -n "$HOURS" ]; then
      UNTIL=$(( $(date +%s) + HOURS * 3600 ))
      printf 'until=%s\n' "$UNTIL" > "$OFF"
    else
      : > "$OFF"
    fi
    printf '%s off %s\n' "$(now_iso)" "$UNTIL" | sed 's/ $//' >> "$STATE/off.log"
    echo "tollgate spento${HOURS:+ per $HOURS ore}. Per riaccenderlo: /tollgate:on" >&2
    exit 0
  fi
  if [ "$CMD" = "tollgate:on" ] && [ -e "$OFF" ]; then
    rm -f "$OFF"
    printf '%s on\n' "$(now_iso)" >> "$STATE/off.log"
    echo "tollgate acceso" >&2
  fi
fi

# 2. OFF attivo, salvo scadenza passata.
if [ -e "$OFF" ]; then
  UNTIL="$(sed -n 's/^until=\([0-9][0-9]*\)$/\1/p' "$OFF" 2>/dev/null | head -n 1)"
  if [ -n "$UNTIL" ] && [ "$(date +%s)" -ge "$UNTIL" ]; then
    rm -f "$OFF"
    printf '%s on\n' "$(iso_of "$UNTIL")" >> "$STATE/off.log"
  else
    printf '%s skip %s\n' "$(now_iso)" "$EVENT" >> "$STATE/skipped.log" 2>/dev/null
    echo "tollgate spento ($OFF): nessun controllo. Per riaccenderlo: /tollgate:on" >&2
    exit 0
  fi
fi

# 3. Repo attivo? tollgate.toml sul ramo predefinito di origin, senza rete.
CWD="$(json_str cwd)"
[ -n "$CWD" ] && [ -d "$CWD" ] || CWD="$PWD"
ACTIVE=no; FOUND=no; REF=""
B="$(git -C "$CWD" config --get tollgate.defaultBranch 2>/dev/null)"
for ref in ${B:+"origin/$B"} origin/HEAD origin/main origin/master; do
  if git -C "$CWD" rev-parse --verify -q "$ref^{commit}" >/dev/null 2>&1; then
    FOUND=yes; REF="$ref"
    git -C "$CWD" cat-file -e "$ref:tollgate.toml" 2>/dev/null && ACTIVE=yes
    break
  fi
done
SESSION="$(json_str session_id | tr -cd 'A-Za-z0-9_-')"
if [ "$ACTIVE" = no ] && [ -n "$SESSION" ] && [ -e "$STATE/bound/$SESSION" ]; then
  ACTIVE=yes   # sessione legata a un lavoro: le regole valgono in ogni cartella (6.6)
fi
if [ "$ACTIVE" = no ]; then
  if [ "$FOUND" = no ] && git -C "$CWD" rev-parse --git-dir >/dev/null 2>&1; then
    echo "tollgate: nessun riferimento remoto (origin/HEAD, main, master): repo trattato come non attivo" >&2
  fi
  exit 0
fi

# 4. Python >= 3.11.
PY=""
for c in python3 python3.13 python3.12 python3.11; do
  if command -v "$c" >/dev/null 2>&1 \
     && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "tollgate: serve Python >= 3.11 per i controlli. Programma: $BIN. $HINT" >&2
  [ "$CONTROL" = yes ] && exit 2
  exit 0
fi

# 5. Il controllo, con un cane da guardia oltre la scadenza interna di Python (decisione 4).
TIMEOUT=20
if [ -n "$REF" ]; then
  T="$(git -C "$CWD" show "$REF:tollgate.toml" 2>/dev/null | awk '
    /^\[hooks\]/ { s = 1; next } /^\[/ { s = 0 }
    s && /^[[:space:]]*timeout_s[[:space:]]*=/ { gsub(/[^0-9]/, "", $0); print; exit }')"
  [ -n "$T" ] && TIMEOUT="$T"
fi
TMPO="$(mktemp)"; TMPE="$(mktemp)"
trap 'rm -f "$TMPO" "$TMPE"' EXIT
printf '%s' "$INPUT" | "$PY" "$BIN" hook "$EVENT" >"$TMPO" 2>"$TMPE" &
PID=$!
( sleep $(( TIMEOUT + 2 )) && kill -TERM "$PID" ) >/dev/null 2>&1 </dev/null &
WD=$!
wait "$PID"; RC=$?
kill "$WD" >/dev/null 2>&1

# 6-7. Uscite.
if [ "$RC" -eq 0 ] || [ "$RC" -eq 2 ]; then
  cat "$TMPO"; cat "$TMPE" >&2
  exit "$RC"
fi
mkdir -p "$STATE"
{ printf '%s %s rc=%s\n' "$(now_iso)" "$EVENT" "$RC"; cat "$TMPE"; } >> "$STATE/hook-errors.log" 2>/dev/null
if [ "$CONTROL" = yes ]; then
  cat "$TMPE" >&2
  echo "tollgate: controllo non riuscito (uscita $RC): azione negata. Log: $STATE/hook-errors.log. Programma: $BIN. $HINT" >&2
  exit 2
fi
echo "tollgate: avviso, hook $EVENT non riuscito (uscita $RC) e ignorato. $HINT" >&2
exit 0
```

Poi `chmod +x hooks/run`.

- [ ] **Step 4: `hooks.json`, `plugin.json`, skill**

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" SessionStart", "timeout": 90}]}],
    "UserPromptExpansion": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" UserPromptExpansion", "timeout": 90}]}],
    "PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash|Agent|SendMessage|mcp__.*", "hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" PreToolUse", "timeout": 90}]}],
    "PostToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash|Agent|Skill|SubagentHandback", "hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" PostToolUse", "timeout": 90}]}],
    "SubagentStart": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" SubagentStart", "timeout": 90}]}],
    "SubagentStop": [{"hooks": [{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run\" SubagentStop", "timeout": 90}]}]
  }
}
```

`.claude-plugin/plugin.json` (il campo `version` della dipendenza secondo l'esito D1 del Task 1: con D1 «sì» `">=6.4.1 <7.0.0"`; con D1 «no» o «non determinato» la chiave `version` si toglie e il ledger registra la `Ruling:`; il controllo della versione passa a `start` in P3):

```json
{
  "name": "tollgate",
  "version": "0.1.0",
  "description": "Dall'issue GitHub alla PR verificata: guardrail locali per Claude Code e gate su GitHub.",
  "author": {"name": "ginz0ls"},
  "license": "MIT",
  "dependencies": [
    {"name": "superpowers", "version": ">=6.4.1 <7.0.0", "marketplace": "claude-plugins-official"}
  ]
}
```

`skills/off/SKILL.md`:

```markdown
---
name: off
description: Spegne tollgate su questa macchina, per sempre o per un numero di ore. Solo l'utente.
disable-model-invocation: true
argument-hint: "[ore]"
---

Il wrapper degli hook ha già spento tollgate quando hai digitato il comando, senza Python né DB.
Riferisci all'utente il messaggio dell'hook («tollgate spento…»). Ricordagli che con tollgate
spento non gira nessun guardrail locale, che il gate su GitHub resta attivo, e che si riaccende
con /tollgate:on. Non eseguire comandi.
```

`skills/on/SKILL.md`:

```markdown
---
name: on
description: Riaccende tollgate su questa macchina. Solo l'utente.
disable-model-invocation: true
---

Il wrapper degli hook ha già tolto l'interruttore quando hai digitato il comando.
Riferisci all'utente che tollgate è acceso. Non eseguire comandi.
```

- [ ] **Step 5: Verificare che passino**

Run: `tests/run`
Expected: OK. Se `claude` è installato, eseguire anche `claude plugin validate .` (se il comando esiste, esito D1) e riportare l'esito nel ledger; non installare il plugin.

- [ ] **Step 6: Commit**

```bash
git add hooks/run hooks/hooks.json .claude-plugin/plugin.json skills/off/SKILL.md skills/on/SKILL.md tests/test_wrapper.py tests/test_manifest.py
git commit -m "tollgate P2: wrapper hooks/run, hooks.json, plugin.json, interruttore off/on"
```

---
