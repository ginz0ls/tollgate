#!/usr/bin/env python3
"""gh con guardia: controlla gli argomenti con ghguard.py, li registra e passa il comando al gh vero.

Ambiente: P4_REAL_GH (gh vero, obbligatorio), P4_PROFILE (script|flow, predefinito script),
P4_LOG (registro `<ora> gh <argomenti>`, predefinito $P4_OUT/comandi.log), P4_REPO (il repo del
comando, `owner/nome`; senza, lo si legge da `git remote get-url --push origin` della cartella corrente).

Prima di controllare, i segnaposto `{owner}` e `{repo}` (che il gh vero espanderebbe da solo) si
sostituiscono con il repo, e a `pr`, `issue` e `run` senza --repo si aggiunge `--repo <repo>`: la
lista degli ammessi vede sempre il repo vero. Un repo che non è uno dei due ammessi ferma il comando.
Uscita 126 con il motivo su stderr se il comando è rifiutato (e un «RIFIUTATO» nel registro)."""
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghguard  # noqa: E402

URL = re.compile(r"^(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?$")


def repo_slug(env):
    if env.get("P4_REPO"):
        return env["P4_REPO"]
    try:
        out = subprocess.run(["git", "remote", "get-url", "--push", "origin"], capture_output=True, text=True,
                             timeout=20, stdin=subprocess.DEVNULL).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    m = URL.match(out)
    return m.group(1) if m else None


def expand(args, slug):
    out = [a.replace("{owner}", slug.split("/")[0]).replace("{repo}", slug.split("/")[1]) for a in args]
    has_repo = any(a in ("--repo", "-R") or a.startswith(("--repo=", "-R")) for a in out)
    if out and out[0] in ("pr", "issue", "run") and not has_repo:
        out += ["--repo", slug]
    return out


def log(env, line):
    path = env.get("P4_LOG") or (os.path.join(env["P4_OUT"], "comandi.log") if env.get("P4_OUT") else None)
    if path:
        with open(path, "a") as fh:
            fh.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), line))


def main(argv, env):
    real = env.get("P4_REAL_GH")
    if not real or not os.path.isfile(real):
        print("ghwrap: P4_REAL_GH non impostato o non è un file", file=sys.stderr)
        return 126
    args = list(argv)
    needs_repo = bool(args) and args[0] in ("api", "pr", "issue", "run", "repo")
    slug = repo_slug(env)
    if needs_repo and args[0] != "repo":
        if slug is None or slug not in ghguard.REPOS:
            print("ghwrap: il repo di origin (%s) non è uno dei due ammessi" % slug, file=sys.stderr)
            log(env, "RIFIUTATO gh %s (repo %s)" % (" ".join(args), slug))
            return 126
        args = expand(args, slug)
    why = ghguard.violation(args, profile=env.get("P4_PROFILE", "script"))
    if why:
        print("ghwrap: gh %s: %s" % (" ".join(args), why), file=sys.stderr)
        log(env, "RIFIUTATO gh %s" % " ".join(args))
        return 126
    log(env, "gh %s" % " ".join(args))
    os.execv(real, [real, *args])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], os.environ))
