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


def make_wrapper(argv):
    """`make-wrapper <file> --real GH --repo SLUG --profile P --log FILE --tmp DIR`: scrive un `gh` che fissa profilo, repo,
    gh vero, registro e cartella dei file di ingresso al momento della generazione e scarta le variabili P4_*, TMPDIR e GH_REPO
    dell'ambiente: ciò che il modello imposta nella sua shell non cambia niente. Il file è di sola lettura."""
    import argparse
    import shlex
    ap = argparse.ArgumentParser(prog="ghwrap.py make-wrapper")
    ap.add_argument("dest")
    for opt in ("real", "repo", "profile", "log", "tmp"):
        ap.add_argument("--" + opt, required=True)
    a = ap.parse_args(argv)
    if a.repo not in ghguard.REPOS or a.profile not in ghguard.PROFILES or not os.path.isfile(a.real):
        print("make-wrapper: repo, profilo o gh vero non validi", file=sys.stderr)
        return 2
    here = os.path.dirname(os.path.abspath(__file__))
    text = (
        "#!/usr/bin/env bash\n"
        "# gh con guardia generato da ghwrap.py make-wrapper: valori fissati alla generazione (non letti dall'ambiente)\n"
        "unset P4_PROFILE P4_REPO P4_REAL_GH P4_LOG P4_OUT P4_WORK P4_TMP TMPDIR GH_REPO\n"
        "export P4_PROFILE=%s P4_REPO=%s P4_REAL_GH=%s P4_LOG=%s P4_TMP=%s\n"
        "exec python3 -B -I %s \"$@\"\n" % (
            shlex.quote(a.profile), shlex.quote(a.repo), shlex.quote(a.real), shlex.quote(a.log), shlex.quote(a.tmp),
            shlex.quote(os.path.join(here, "ghwrap.py"))))
    if os.path.lexists(a.dest):
        os.unlink(a.dest)
    with open(a.dest, "w") as fh:
        fh.write(text)
    os.chmod(a.dest, 0o555)
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["make-wrapper"]:
        sys.exit(make_wrapper(sys.argv[2:]))
    sys.exit(main(sys.argv[1:], os.environ))
