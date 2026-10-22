#!/usr/bin/env python3
"""Controlli di run-p4-flow.sh sull'uscita `stream-json` di `claude -p` e sugli eventi di tollgate. Nessuna rete.

  flowcheck.py commands <passo.jsonl>               i comandi Bash del modello (uno per riga, in ordine)
  flowcheck.py gh <passo.jsonl>                     i comandi gh del modello con il giudizio di ghguard (profilo flow);
                                                    uscita 1 se uno è rifiutato o rivolto a un repo non ammesso
  flowcheck.py shim <passo.jsonl> <percorso shim>   l'uscita del tool per `command -v gh` e il confronto con lo shim
  flowcheck.py events <events.jsonl> <atteso>       veti ed effetti degli eventi, contro l'atteso (nessuno|open-pr)
  flowcheck.py sessions <cartella dei log>          id e cartella di ogni sessione (`system`/`init`)
  flowcheck.py shapes                               i gh che il flusso di tollgate fa davvero, ognuno passato da ghguard
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghguard  # noqa: E402
import ghwrap  # noqa: E402

SPLIT = re.compile(r"\|\||&&|[;|\n]")
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# I gh del flusso di tollgate (bin/tollgate_flow/gh.py, tollgate_gate/github.py): con `{owner}/{repo}` come li scrive la CLI.
SHAPES = [
    ["auth", "status"],
    ["api", "repos/{owner}/{repo}/issues/7"],
    ["api", "--paginate", "repos/{owner}/{repo}/pulls?state=all&per_page=100", "--jq",
     '.[] | {number, headRefName: .head.ref, state: (if .merged_at then "MERGED" else (.state | ascii_upcase) end), url: .html_url}'],
    ["pr", "list", "--head", "tg/7-prova", "--state", "all", "--limit", "100", "--json",
     "number,state,url,headRefOid,mergedAt,isCrossRepository"],
    ["pr", "view", "3", "--json", "number,state,url,mergedAt"],
    ["pr", "view", "3", "--json", "body"],
    ["pr", "view", "3", "--json", "comments"],
    ["pr", "create", "--head", "tg/7-prova", "--base", "main", "--title", "prova", "--body-file", "/tmp/tollgate-body/body.md"],
    ["pr", "edit", "3", "--body-file", "/tmp/tollgate-body/body.md"],
    ["api", "repos/{owner}/{repo}/commits/" + "a" * 40 + "/status"],
    ["api", "--include", "repos/{owner}/{repo}/branches/main/protection"],
    ["api", "repos/{owner}/{repo}/actions/permissions"],
]
# ciò che al flusso non è ammesso
FORBIDDEN_SHAPES = [
    ["issue", "create", "--title", "x"], ["repo", "clone", ghguard.PROT], ["repo", "delete", ghguard.PROT],
    ["pr", "merge", "3", "--squash"], ["pr", "close", "3"], ["auth", "login"], ["secret", "set", "X"],
    ["api", "--method", "POST", "repos/{owner}/{repo}/issues"],
    ["api", "--method", "PUT", "--input", "/tmp/x.json", "repos/{owner}/{repo}/branches/main/protection"],
    ["api", "user"], ["api", "repos/altro/x/issues"],
]


def events(path):
    """Gli oggetti JSON del file, uno per riga; le righe che non lo sono si ignorano."""
    out = []
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _blocks(event):
    msg = event.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    return content if isinstance(content, list) else []


def bash_uses(path):
    """`[(id, comando)]` degli usi dello strumento Bash, in ordine."""
    out = []
    for ev in events(path):
        for b in _blocks(ev):
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                cmd = (b.get("input") or {}).get("command")
                if isinstance(cmd, str):
                    out.append((b.get("id"), cmd))
    return out


def tool_results(path):
    """`{tool_use_id: testo}` delle uscite dei tool."""
    out = {}
    for ev in events(path):
        for b in _blocks(ev):
            if isinstance(b, dict) and b.get("type") == "tool_result":
                content = b.get("content")
                if isinstance(content, list):
                    content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
                out[b.get("tool_use_id")] = content if isinstance(content, str) else ""
    return out


def gh_invocations(command):
    """Gli argomenti di ogni `gh` che il comando Bash lancia (un `gh` all'inizio di un segmento, dopo eventuali
    assegnazioni di variabili). Un segmento che non si legge con shlex si salta."""
    found = []
    for segment in SPLIT.split(command):
        try:
            words = shlex.split(segment, comments=True)
        except ValueError:
            continue
        while words and ENV_ASSIGN.match(words[0]):
            words = words[1:]
        if words and words[0] == "gh":
            found.append(words[1:])
    return found


def foreign_repo(args):
    """Il primo repo `owner/nome` degli argomenti che non è ammesso (o `None`)."""
    for a in args:
        for m in re.finditer(r"%s/[\w.-]+" % ghguard.OWNER, a):
            if m.group(0) not in ghguard.REPOS:
                return m.group(0)
    return None


def judge_gh(args, slug=ghguard.PROT):
    """Il motivo per cui il gh del modello non va, `None` se è ammesso dal profilo flow sul repo `slug`."""
    other = foreign_repo(args)
    if other:
        return "repo non ammesso: %s" % other
    expanded = ghwrap.expand(args, slug) if args and args[0] in ("api", "pr", "issue", "run") else list(args)
    why = ghguard.violation(expanded, profile="flow")
    if why:
        return why
    repos = [a for a in expanded if re.fullmatch(r"%s/[\w.-]+" % ghguard.OWNER, a)]
    if any(r != slug for r in repos):
        return "repo diverso da %s" % slug
    return None


def cmd_gh(path):
    rc = 0
    for _id, command in bash_uses(path):
        for args in gh_invocations(command):
            why = judge_gh(args)
            print("%s\tgh %s%s" % ("ok" if why is None else "RIFIUTATO", " ".join(args), "" if why is None else "\t# " + why))
            if why:
                rc = 1
    return rc


def cmd_shim(path, shim):
    uses = bash_uses(path)
    results = tool_results(path)
    for uid, command in uses:
        if re.search(r"command\s+-v\s+gh\b", command):
            out = results.get(uid, "").strip()
            line = out.splitlines()[0].strip() if out else ""
            print("comando: %s" % command.replace("\n", " "))
            print("uscita del tool: %s" % (line or "(vuota)"))
            print("shim atteso: %s" % shim)
            print("uguali: %s" % ("sì" if line == shim else "no"))
            return 0 if line == shim else 1
    print("nessun comando `command -v gh` nei comandi Bash del modello")
    return 1


def cmd_events(path, expected):
    seen = {"veto": [], "effect_requested": [], "effect_executed": []}
    for ev in events(path):
        if ev.get("type") in seen:
            data = ev.get("data")
            seen[ev["type"]].append({"seq": ev.get("seq"), "work": ev.get("work"), "data": data})
    for kind, rows in seen.items():
        print("%s: %d" % (kind, len(rows)))
        for r in rows:
            print("  seq %s work %s %s" % (r["seq"], r["work"], json.dumps(r["data"], ensure_ascii=False)[:300]))
    allowed = {"nessuno": 0, "open-pr": 2}[expected]      # open-pr: la creazione della PR e al più un aggiornamento
    rc = 0
    for kind in ("effect_requested", "effect_executed"):
        if len(seen[kind]) > allowed:
            print("INATTESO: %d eventi %s, attesi al più %d" % (len(seen[kind]), kind, allowed))
            rc = 1
    return rc


def cmd_sessions(folder):
    for f in sorted(Path(folder).glob("*.jsonl")):
        if f.name.startswith("events"):
            continue
        sid = cwd = "?"
        for ev in events(f):
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                sid, cwd = ev.get("session_id", "?"), ev.get("cwd", "?")
                break
        print("%s\t%s\t%s" % (f.stem, sid, cwd))
    return 0


def cmd_shapes():
    rc = 0
    for args in SHAPES:
        why = judge_gh(args)
        print("%s\tgh %s%s" % ("ok" if why is None else "RIFIUTATO", " ".join(args)[:150], "" if why is None else "\t# " + why))
        rc |= 1 if why else 0
    for args in FORBIDDEN_SHAPES:
        why = judge_gh(args)
        print("%s\tgh %s\t# %s" % ("vietato" if why else "AMMESSO", " ".join(args)[:150], why or ""))
        rc |= 0 if why else 1
    return rc


def main(argv):
    if len(argv) == 3 and argv[1] == "commands":
        for _id, command in bash_uses(argv[2]):
            print(command.replace("\n", " ⏎ "))
        return 0
    if len(argv) == 3 and argv[1] == "gh":
        return cmd_gh(argv[2])
    if len(argv) == 4 and argv[1] == "shim":
        return cmd_shim(argv[2], argv[3])
    if len(argv) == 4 and argv[1] == "events" and argv[3] in ("nessuno", "open-pr"):
        return cmd_events(argv[2], argv[3])
    if len(argv) == 3 and argv[1] == "sessions":
        return cmd_sessions(argv[2])
    if len(argv) == 2 and argv[1] == "shapes":
        os.environ.setdefault("P4_TMP", "/tmp")
        return cmd_shapes()
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
