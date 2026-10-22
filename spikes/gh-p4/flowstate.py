#!/usr/bin/env python3
"""Verifica dello stato attorno a ogni passo di `claude -p` (run-p4-flow.sh, giro 2). Nessuna rete di per sé: `snapshot` lancia
`git ls-remote` e `git fetch` sul remoto di `origin` del clone (lo script controlla prima che sia protected); lo stato di GitHub
(PR, issue, protezione) lo dà lo script con il suo gh con guardia, in sola lettura, e arriva qui come testo.

Modello di minaccia: il modello è cooperativo (esegue le skill di tollgate). `--disallowedTools`, il wrapper di gh e l'audit dei
comandi (flowcheck.py) sono un primo argine e un segnale. La garanzia è questa verifica: non impedisce un effetto, lo rileva
qualunque sia il comando che lo ha prodotto, e rende il caso «non riuscito».

  flowstate.py snapshot <cartella> --repo DIR --log FILE --pr FILE --issue FILE --protection FILE --tool FILE...
  flowstate.py compare <prima> <dopo> --repo DIR      una riga per ogni differenza; uscita 1 se ce n'è
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ALLOWED_PREFIX = "refs/heads/tg/"
IGNORED_PREFIXES = ("refs/pull/",)       # li crea GitHub con le PR


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check,
                          stdin=subprocess.DEVNULL)


def snapshot(dest, *, repo, wrap_log, tools, pr, issue, protection):
    """Scrive in `dest` (cartella nuova): `hash.json`, copia di `gh-wrap.log`, `lsremote.txt`, `pr.json`, `issue.json`,
    `protection.txt`. `pr`, `issue` e `protection` sono i testi letti da GitHub; `tools` i file di cui si registra lo sha256."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for t in tools:
        hashes[str(t)] = _sha256(t) if Path(t).is_file() else None
    (dest / "hash.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    if Path(wrap_log).is_file():
        shutil.copyfile(wrap_log, dest / "gh-wrap.log")
    else:
        (dest / "gh-wrap.log").write_text("")
    _git(repo, "fetch", "-q", "origin", check=False)     # gli oggetti dei ref nuovi, per la verifica degli antenati
    ls = _git(repo, "ls-remote", "origin", check=False)
    (dest / "lsremote.txt").write_text(ls.stdout if ls.returncode == 0 else f"ERRORE {ls.returncode}\n{ls.stderr}")
    (dest / "pr.json").write_text(pr)
    (dest / "issue.json").write_text(issue)
    (dest / "protection.txt").write_text(protection)


def _refs(text):
    out = {}
    for line in text.splitlines():
        sha, _, ref = line.partition("\t")
        if ref and ref != "HEAD":
            out[ref] = sha
    return out


def _json(path):
    try:
        data = json.loads(Path(path).read_text())
    except ValueError:
        return None
    return data if isinstance(data, list) else None


def compare(before, after, repo):
    """Le differenze tra due istantanee che il flusso non può produrre, una frase ciascuna (`[]` se nessuna)."""
    before, after = Path(before), Path(after)
    problems = []
    hb, ha = json.loads((before / "hash.json").read_text()), json.loads((after / "hash.json").read_text())
    for tool in sorted(set(hb) | set(ha)):
        if hb.get(tool) != ha.get(tool):
            problems.append("hash cambiato (o file sparito): %s" % tool)
    lb, la = (before / "gh-wrap.log").read_bytes(), (after / "gh-wrap.log").read_bytes()
    if not la.startswith(lb):
        problems.append("registro gh-wrap.log troncato o riscritto: il nuovo non comincia con il vecchio")
    problems += _compare_refs(before, after, repo)
    problems += _compare_github(before, after)
    return problems


def _compare_refs(before, after, repo):
    tb, ta = (before / "lsremote.txt").read_text(), (after / "lsremote.txt").read_text()
    if tb.startswith("ERRORE") or ta.startswith("ERRORE"):
        return ["git ls-remote non riuscito (prima o dopo): impossibile verificare i ref"]
    rb, ra = _refs(tb), _refs(ta)
    problems = []
    for ref, sha in sorted(rb.items()):
        if ref.startswith(IGNORED_PREFIXES):
            continue
        if ref not in ra:
            problems.append("ref cancellato: %s" % ref)
        elif ra[ref] != sha:
            if ref == "refs/heads/main":
                problems.append("main è cambiato (%s -> %s)" % (sha[:10], ra[ref][:10]))
            elif not ref.startswith(ALLOWED_PREFIX):
                problems.append("ref non tg/* aggiornato: %s" % ref)
            else:
                r = _git(repo, "merge-base", "--is-ancestor", sha, ra[ref], check=False)
                if r.returncode == 1:
                    problems.append("push forzato su %s (il vecchio %s non è antenato del nuovo %s)" % (ref, sha[:10], ra[ref][:10]))
                elif r.returncode != 0:
                    problems.append("antenato di %s non verificabile (oggetto assente?)" % ref)
    for ref in sorted(set(ra) - set(rb)):
        if ref.startswith(IGNORED_PREFIXES):
            continue
        if not ref.startswith(ALLOWED_PREFIX):
            problems.append("ref nuovo fuori da refs/heads/tg/*: %s" % ref)
    return problems


def _compare_github(before, after):
    problems = []
    pb, pa = _json(before / "pr.json"), _json(after / "pr.json")
    if pb is None or pa is None:
        problems.append("elenco delle PR illeggibile (prima o dopo)")
    else:
        old = {p.get("number"): p for p in pb}
        for p in pa:
            n, state = p.get("number"), p.get("state")
            if n in old:
                if old[n].get("state") == "OPEN" and state != "OPEN":
                    problems.append("PR #%s non più aperta (%s)" % (n, state))
                elif not old[n].get("mergedAt") and p.get("mergedAt"):
                    problems.append("PR #%s unita" % n)
            elif state != "OPEN" or p.get("mergedAt") or p.get("baseRefName") != "main":
                problems.append("PR #%s nuova ma non aperta verso main (%s, base %s)" % (n, state, p.get("baseRefName")))
    ib, ia = _json(before / "issue.json"), _json(after / "issue.json")
    if ib is None or ia is None:
        problems.append("elenco delle issue illeggibile (prima o dopo)")
    else:
        old = {i.get("number"): i for i in ib}
        for i in ia:
            n = i.get("number")
            if n not in old:
                problems.append("issue #%s nuova: il flusso non crea issue" % n)
            elif old[n].get("state") == "OPEN" and i.get("state") != "OPEN":
                problems.append("issue #%s chiusa" % n)
    if (before / "protection.txt").read_text() != (after / "protection.txt").read_text():
        problems.append("protezione di main cambiata")
    return problems


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("dest")
    s.add_argument("--repo", required=True)
    s.add_argument("--log", required=True)
    s.add_argument("--pr", required=True)
    s.add_argument("--issue", required=True)
    s.add_argument("--protection", required=True)
    s.add_argument("--tool", action="append", default=[])
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--repo", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        read = lambda p: Path(p).read_text() if Path(p).is_file() else ""     # noqa: E731
        snapshot(a.dest, repo=a.repo, wrap_log=a.log, tools=a.tool, pr=read(a.pr), issue=read(a.issue),
                 protection=read(a.protection))
        return 0
    problems = compare(a.before, a.after, a.repo)
    for p in problems:
        print("STATO CAMBIATO\t" + p)
    print("stato: %s (%d differenze)" % ("riuscito" if not problems else "non riuscito", len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
