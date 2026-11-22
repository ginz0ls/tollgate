"""Sonda: cli_calls.decide con un comando `ruling add` (heredoc) da subagente e da sessione principale."""
import sys
from pathlib import Path
from types import SimpleNamespace

W = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(W / "bin"))
sys.dont_write_bytecode = True
from tollgate_checks import cli_calls
from tollgate_hooks.model import Event
from tollgate_core.paths import program_command

PLUGIN_BIN = str(W / "bin" / "tollgate")
prog = program_command(PLUGIN_BIN)
body = ("cosa: usa la copia dell'utente, perché $HOME `date` non c'è\n"
        "perché: il task review start non dice niente\n"
        "costo: nessuno")
def cmd(sub="ruling add --task 2 --by agent"):
    return f"{prog} {sub} <<'RULING_FINE'\n{body}\nRULING_FINE\n"

def ev(command, agent_id):
    return Event(kind="pre_bash", hook_event="PreToolUse", session="s", cwd=Path("/tmp"),
                 agent_id=agent_id, agent_type="tollgate:implementer" if agent_id else None,
                 tool_name="Bash", tool_input={"command": command}, tool_response=None, raw={})

ctx = SimpleNamespace(plugin_bin=PLUGIN_BIN, bound=False, work=None,
                      work_for_path=lambda p: None)
for label, command in (("ruling add", cmd()), ("sottocomando sconosciuto xyz", cmd("xyz add")),
                       ("task start (coordinatore)", cmd("task start 1"))):
    for who in ("a1", None):
        out = cli_calls.decide(ev(command, who), ctx)
        print(f"{label:34} agent_id={who!s:5} ->", [(d.kind, d.rule or d.op) for d in out])
# comando non analizzabile (variabile come programma) con parole task/review/start
cmd_var = f"$P ruling add --task 2 <<'RULING_FINE'\n{body}\nRULING_FINE\n"
for who in ("a1", None):
    out = cli_calls.decide(ev(cmd_var, who), ctx)
    print("programma = variabile".ljust(34), f"agent_id={who!s:5} ->", [(d.kind, d.rule or d.op) for d in out])
from tollgate_analysis import bash
try:
    print("parse:", [c.argv[:4] for c in bash.parse(cmd(), "/tmp")])
except bash.BashParseError as e:
    print("parse error", e)
