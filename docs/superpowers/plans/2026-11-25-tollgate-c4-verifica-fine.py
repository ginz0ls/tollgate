#!/usr/bin/env python3
"""Verifica di «Finito quando» del brief corto di C4a, solo sui file.

Uso, dalla radice del repo:

    python3 -B docs/superpowers/plans/2026-11-25-tollgate-c4-verifica-fine.py [--senza-rete]

Legge il ledger del workspace nel worktree `.claude/worktrees/c4` (una sola cartella sotto
`.superpowers/sdd/`; se il worktree non c'è più, la copia su `main` in
`docs/sdd/2026-11-25-tollgate-c4-ponte-github/`), il rapporto della sonda, `rapporto-merge.md` e
`final-review.md`, il piano principale di C su `main` e la memoria del progetto, e stampa la
situazione (A, B, C, oppure lavoro non cominciato o in corso) con l'esito di ogni condizione.
Esce con 0 se il lavoro è finito (anche «finito per ora», in attesa dell'utente), con 1
altrimenti. Non scrive niente. `--senza-rete` salta il confronto con GitHub; `--repo`, `--home` e
`--remote` (per esempio un repo nudo locale al posto di GitHub) servono alle prove a secco.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

WT_REL = ".claude/worktrees/c4"
BRANCH = "c4-ponte-github"
SDD_MAIN = "docs/sdd/2026-11-25-tollgate-c4-ponte-github"
SONDA = "docs/verifiche/2026-11-25-c4-sonda.md"
PIANO_PRINCIPALE = "docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md"
REMOTE = "https://github.com/ginz0ls/tollgate.git"
MERGE_SUBJECT = "tollgate C4a:"
MEMORY_LINE = "- C4a eseguito"
MERGE_MARKER = "Rapporto del merge: consegnato"
CLOSING = "Chiusura di C4a: consegnata"
CI_PREFIX = "CI di main: verde su "
SECTIONS = ("Commit e test", "La sonda", "Il token delle bacheche",
            "Decisioni prese durante il lavoro", "Rilievi minori rinviati",
            "Cosa cambia nei progetti")
ESITI_A = ("riuscita", "riuscita con differenze")
ESITO_B = "rinviata a C4b"
WORKTREE_ANSWERS = ("rimuovi worktree e ramo", "rimuovi solo il worktree", "tieni tutto")
ESITO = re.compile(r"^Esito:[ \t]*(.*?)[ \t]*$", re.M)
SEP = r"[ \t]+[—–-][ \t]+"
FERMATA = re.compile(r"^Fermata (aperta|chiusa): (.+?)(?:%s(.*?))?[ \t]*$" % SEP)
S13 = re.compile(r"^Sonda: S13 notifica%s\S" % SEP)
LOGIN = REMOTE.split("/")[-2]
# Ciò che il rapporto della sonda non deve contenere. Lo script dice solo CHE c'è, mai il testo.
# La forma di token è costruita a pezzi perché la scansione dei segreti non scatti su questo file.
FORBIDDEN = (
    ("il login dell'account", re.compile(re.escape(LOGIN), re.I)),
    ("il nome del repo di prova", re.compile(re.escape("tollgate-c4-" + "probe"), re.I)),
    ("un percorso sotto /home/", re.compile(re.escape("/home/"))),
    ("una forma di token", re.compile("gh[pousr]" + "_[A-Za-z0-9_]{20,}|"
                                      + re.escape("github" + "_pat_"))),
)


class Check:
    def __init__(self) -> None:
        self.rows: list[tuple[bool, str]] = []

    def __call__(self, ok: object, text: str) -> bool:
        self.rows.append((bool(ok), text))
        return bool(ok)

    @property
    def all_ok(self) -> bool:
        return all(ok for ok, _ in self.rows)


def git(repo: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                             timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout if out.returncode == 0 else None


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def on_main(repo: Path, rel: str) -> str | None:
    return git(repo, "show", f"main:{rel}")


class Workspace:
    """La cartella del workspace nel worktree, o la copia del registro su `main`."""

    def __init__(self, repo: Path, path: Path | None) -> None:
        self.repo, self.path = repo, path
        self.where = "del workspace" if path else f"della copia su main ({SDD_MAIN}/)"

    def read(self, name: str) -> str | None:
        if self.path is not None:
            return read(self.path / name)
        return on_main(self.repo, f"{SDD_MAIN}/{name}")


def ledger(repo: Path) -> tuple[str | None, Path | None, str]:
    """Il ledger, la cartella del workspace (se nel worktree) e da dove viene."""
    sdd = repo / WT_REL / ".superpowers" / "sdd"
    dirs = sorted(p for p in sdd.iterdir() if p.is_dir()) if sdd.is_dir() else []
    if len(dirs) > 1:
        return None, None, f"più di un workspace sotto {WT_REL}/.superpowers/sdd/"
    if dirs and (dirs[0] / "progress.md").is_file():
        return read(dirs[0] / "progress.md"), dirs[0], "worktree"
    text = on_main(repo, f"{SDD_MAIN}/progress.md")
    return text, None, "copia su main" if text is not None else "nessun ledger"


def stops(lines: list[str]) -> list[tuple[int, str, str, str | None]]:
    """Le righe delle fermate: indice, «aperta» o «chiusa», caso, risposta."""
    out = []
    for i, line in enumerate(lines):
        m = FERMATA.match(line)
        if m:
            out.append((i, m.group(1), m.group(2).strip().lower(), m.group(3)))
    return out


def open_stops(lines: list[str]) -> list[str]:
    """I casi delle fermate aperte e non ancora chiuse, in ordine."""
    state: dict[str, bool] = {}
    for _, kind, case, _ in stops(lines):
        state.pop(case, None)
        state[case] = kind == "aperta"
    return [c for c, is_open in state.items() if is_open]


def answers(lines: list[str], case: str) -> list[str]:
    return [a.strip() for _, kind, c, a in stops(lines) if kind == "chiusa" and c == case and a]


def index_of(lines: list[str], prefix: str) -> int | None:
    return next((i for i, line in enumerate(lines) if line.startswith(prefix)), None)


def has_line(lines: list[str], prefix: str, after: int = -1) -> bool:
    return any(line.startswith(prefix) for line in lines[after + 1:])


def section(text: str, title: str) -> str | None:
    m = re.search(r"^## %s[ \t]*$(.*?)(?=^## |\Z)" % re.escape(title), text, re.M | re.S)
    return m.group(1) if m else None


def bullets(body: str) -> int:
    return sum(1 for line in body.splitlines() if line.startswith("- "))


def deferred_rows(review: str) -> int:
    """Le righe della tabella di triage la cui ultima cella (l'esito) comincia con «rinviato»."""
    count = 0
    for line in review.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[-1].lower().startswith("rinviato"):
            count += 1
    return count


def file_text(repo: Path, rel: str) -> tuple[str | None, str]:
    """Il file nel worktree se c'è, altrimenti su `main`, e da dove viene."""
    wt = repo / WT_REL / rel
    if wt.is_file():
        return read(wt), "nel worktree"
    text = on_main(repo, rel)
    return text, "su main" if text is not None else "assente"


def memory_text(repo: Path, home: Path) -> str | None:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(repo))
    return read(home / ".claude" / "projects" / slug / "memory" / "plugin-workflow-decisioni.md")


def worktree_listed(repo: Path) -> bool:
    out = git(repo, "worktree", "list", "--porcelain") or ""
    target = (repo / WT_REL).resolve()
    return any(line.startswith("worktree ") and Path(line[9:]).resolve() == target
               for line in out.splitlines())


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", older, newer) is not None


def check_tasks(c: Check, lines: list[str]) -> None:
    for n in range(1, 12):
        c(has_line(lines, f"Task {n}: complete"), f"ledger: «Task {n}: complete»")


def check_forbidden(c: Check, report: str) -> None:
    for label, pattern in FORBIDDEN:
        c(pattern.search(report) is None, f"il rapporto della sonda non contiene {label}")


def check_probe_a(c: Check, lines: list[str], report: str) -> None:
    c(answers(lines, "sonda"), "ledger: «Fermata chiusa: sonda — <risposta>»")
    for prefix in ("Sonda: controlla", "Sonda: esegui", "Sonda: pulisci"):
        c(has_line(lines, prefix), f"ledger: «{prefix} …»")
    c(any(S13.match(line) for line in lines), "ledger: «Sonda: S13 notifica — <risposta>»")
    missing = [n for n in range(1, 23)
               if not re.search(r"^\|[ \t]*S%d[ \t]*\|" % n, report, re.M)]
    c(not missing, "il rapporto della sonda ha una riga «| S<n> |» per ognuno dei fatti S1-S22"
                   + (f" (mancano: {', '.join(f'S{n}' for n in missing)})" if missing else ""))
    check_forbidden(c, report)


def check_probe_b(c: Check, lines: list[str], report: str) -> None:
    c(any(a.startswith("Non ora") for a in answers(lines, "sonda")),
      "ledger: «Fermata chiusa: sonda — Non ora…»")
    c(has_line(lines, "Sonda: rinviata a C4b"), "ledger: «Sonda: rinviata a C4b …»")
    check_forbidden(c, report)


def check_review_and_suite(c: Check, lines: list[str]) -> None:
    first = index_of(lines, "Revisione finale (Fable):")
    c(first is not None, "ledger: «Revisione finale (Fable): …»")
    c(first is not None and has_line(lines, "Revisione finale chiusa: 0 critical, "
                                            "0 important aperti", first),
      "ledger: «Revisione finale chiusa: 0 critical, 0 important aperti» dopo la revisione")
    for n in (1, 2, 3):
        c(has_line(lines, f"Suite finale corsa {n}: verde su python3.11 e python3"),
          f"ledger: «Suite finale corsa {n}: verde su python3.11 e python3 …»")


def check_merge_report(c: Check, lines: list[str], ws: Workspace, probe_words: str) -> None:
    report = ws.read("rapporto-merge.md")
    c(report is not None, f"rapporto-merge.md {ws.where} esiste")
    c(has_line(lines, MERGE_MARKER), f"ledger: «{MERGE_MARKER}»")
    if report is None:
        return
    for title in SECTIONS:
        c(section(report, title) is not None, f"il rapporto del merge ha la sezione «## {title}»")
    c(probe_words in (section(report, "La sonda") or ""),
      f"la sezione «La sonda» del rapporto del merge dice «{probe_words}»")
    marker = index_of(lines, MERGE_MARKER)
    if marker is not None:
        rulings = sum(1 for line in lines[:marker] if line.startswith("Ruling:"))
        got = bullets(section(report, "Decisioni prese durante il lavoro") or "")
        c(got == rulings, f"«Decisioni prese durante il lavoro» ha un elemento per ognuna delle "
                          f"{rulings} righe «Ruling:» prima del rapporto (trovati {got})")
    review = ws.read("final-review.md")
    c(review is not None, f"final-review.md {ws.where} esiste")
    if review is not None:
        want = deferred_rows(review)
        body = section(report, "Rilievi minori rinviati") or ""
        got = bullets(body)
        c(got == want and (want > 0 or "Nessuno." in body),
          f"«Rilievi minori rinviati» ha un elemento per ognuna delle {want} righe di triage "
          f"«rinviato» (trovati {got}; con zero righe serve «Nessuno.»)")
    c(report.rstrip().endswith("Posso unire su `main`?"),
      "il rapporto del merge finisce con «Posso unire su `main`?»")


def check_ci(c: Check, repo: Path, lines: list[str], merge: str | None) -> None:
    ci = [line for line in lines if line.startswith(CI_PREFIX)]
    if not ci:
        c(False, f"6.6 ledger: «{CI_PREFIX}<sha>»")
        return
    words = ci[-1][len(CI_PREFIX):].split()
    given = words[0] if words else ""
    full = None
    if re.fullmatch(r"[0-9a-f]{7,40}", given):
        full = (git(repo, "rev-parse", "--verify", "--quiet", f"{given}^{{commit}}") or "").strip()
    c(full, f"6.6 lo SHA dell'ultima riga «{CI_PREFIX}…» ({given[:12] or '?'}) esiste")
    if not full:
        return
    c(merge is not None and is_ancestor(repo, merge, full),
      f"6.6 il commit del merge è un antenato di {full[:12]} (o è lui)")
    c(is_ancestor(repo, full, "main"), f"6.6 {full[:12]} è un antenato di main (o è main)")
    out = git(repo, "log", "-m", "--first-parent", "--no-renames", "--format=", "--name-only",
              f"{full}..main")
    outside = [f for f in (out or "").splitlines()
               if f.strip() and not f.startswith(SDD_MAIN + "/")]
    c(out is not None and not outside,
      f"6.6 i commit dopo {full[:12]} su main toccano solo {SDD_MAIN}/ "
      f"({len(outside)} file fuori)")


def check_worktree(c: Check, repo: Path, lines: list[str], from_main: bool) -> None:
    listed = worktree_listed(repo)
    branch = git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{BRANCH}") is not None
    if not from_main and "worktree" in open_stops(lines):
        c(listed, "6.9 domanda sul worktree fatta e senza risposta, worktree presente: "
                  "finito per ora")
        return
    given = answers(lines, "worktree")
    if not given:
        c(False, "6.9 ledger: «Fermata chiusa: worktree — <risposta>»"
                 + (" (la copia su main non ha la copia finale del ledger)" if from_main else ""))
        return
    answer = given[-1].lower()
    choice = next((a for a in WORKTREE_ANSWERS if answer.startswith(a)), None)
    where = "presente" if listed else "rimosso"
    if choice == "tieni tutto":
        c(listed, f"6.9 risposta «tieni tutto»: worktree {where}")
    elif choice == "rimuovi solo il worktree":
        c(not listed and branch, f"6.9 risposta «rimuovi solo il worktree»: worktree {where}, "
                                 f"ramo {BRANCH} {'presente' if branch else 'assente'}")
    elif choice == "rimuovi worktree e ramo":
        c(not listed and not branch, f"6.9 risposta «rimuovi worktree e ramo»: worktree {where}, "
                                     f"ramo {BRANCH} {'presente' if branch else 'assente'}")
    else:
        c(False, "6.9 la risposta sul worktree non è una delle tre ammesse")


def check_after_merge(c: Check, repo: Path, home: Path, lines: list[str], from_main: bool,
                      remote: str, network: bool) -> None:
    log = git(repo, "log", "--first-parent", "main", "--format=%H %s") or ""
    merges = [sha for sha, _, subject in (l.partition(" ") for l in log.splitlines())
              if subject.startswith(MERGE_SUBJECT)]
    merge = merges[-1] if merges else None
    c(merge, f"6.1 git log --first-parent main ha un commit «{MERGE_SUBJECT} …»"
             + (f" (il merge: {merge[:12]})" if merge else ""))
    plan = on_main(repo, PIANO_PRINCIPALE) or ""
    row = next((l for l in plan.splitlines() if l.startswith("| **C4a")), "")
    c("unita su" in row, "6.2 il piano principale su main ha «unita su» nella riga «| **C4a»")
    mem = memory_text(repo, home) or ""
    c(any(l.startswith(MEMORY_LINE) for l in mem.splitlines()),
      f"6.3 plugin-workflow-decisioni.md della memoria ha una riga «{MEMORY_LINE} …»")
    closing = index_of(lines, CLOSING)
    c(closing is not None, f"6.4 ledger: «{CLOSING}»")
    c(closing is not None and any(i > closing and kind == "aperta" and case == "worktree"
                                  for i, kind, case, _ in stops(lines)),
      f"6.4 ledger: «Fermata aperta: worktree» dopo «{CLOSING}»")
    c(on_main(repo, f"{SDD_MAIN}/README.md") is not None, f"6.5 {SDD_MAIN}/README.md è su main")
    tree = git(repo, "ls-tree", "-r", "--name-only", "main", "--", SDD_MAIN) or ""
    c(not any("sonda-c4" in Path(p).parts for p in tree.splitlines()),
      f"6.5 {SDD_MAIN}/ su main non contiene file di sonda-c4/")
    check_ci(c, repo, lines, merge)
    c(closing is not None and has_line(lines, "Subagenti: nessuno in corso", closing),
      f"6.7 ledger: «Subagenti: nessuno in corso» dopo «{CLOSING}»")
    if network:
        local = (git(repo, "rev-parse", "main") or "").strip()
        out = git(repo, "ls-remote", remote, "main") or ""
        far = next((l.split("\t")[0] for l in out.splitlines()
                    if l.endswith("\trefs/heads/main")), "")
        c(local and local == far, f"6.8 il remoto ha lo stesso main ({far[:12] or '?'} contro "
                                  f"{local[:12] or '?'})")
    else:
        c(True, "6.8 confronto con GitHub saltato (--senza-rete)")
    check_worktree(c, repo, lines, from_main)


def check_merge(c: Check, repo: Path, home: Path, lines: list[str], from_main: bool,
                remote: str, network: bool) -> None:
    merge_lines = [line for line in lines if line.startswith("Merge:")]
    if not merge_lines:
        c("merge" in open_stops(lines),
          "6 rapporto consegnato, fermata «merge» aperta e nessuna riga «Merge:»: finito per ora")
        return
    last = merge_lines[-1]
    if last.startswith("Merge: no dell'utente"):
        c(True, "6 ultima riga «Merge: no dell'utente»: il lavoro è finito qui")
    elif last.startswith("Merge: OK dell'utente"):
        c(True, "6 ultima riga «Merge: OK dell'utente»: valgono i passi dopo il merge")
        check_after_merge(c, repo, home, lines, from_main, remote, network)
    else:
        c(False, "6 l'ultima riga «Merge:» non è «Merge: OK dell'utente» né «Merge: no dell'utente»")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--home", type=Path, default=Path.home())
    ap.add_argument("--remote", default=REMOTE)
    ap.add_argument("--senza-rete", action="store_true")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    network = not args.senza_rete
    text, ws_path, origin = ledger(repo)
    c = Check()
    print(f"Ledger: {origin}")
    if text is None:
        if origin.startswith("più di un"):
            situation = "nessuna: più di un workspace, ledger non verificabile"
            c(False, f"una sola cartella sotto {WT_REL}/.superpowers/sdd/")
        else:
            situation = "nessuna: lavoro non cominciato"
            c(False, "il ledger di C4a esiste (nel worktree o su main)")
    else:
        lines = [line.rstrip() for line in text.splitlines()]
        pending = [s for s in open_stops(lines) if s not in ("merge", "worktree")]
        report, where = file_text(repo, SONDA)
        esiti = ESITO.findall(report or "")
        if pending:
            situation = f"C: fermata aperta ({pending[-1]}; finito per ora)"
            c(True, f"fermata «{pending[-1]}» aperta nel ledger, l'utente non ha ancora risposto")
        elif report is None or not esiti:
            situation = "nessuna: lavoro in corso"
            c(False, f"{SONDA} ha una riga «Esito: …» ({where})")
        elif esiti[-1] in ESITI_A or esiti[-1] == ESITO_B:
            probe_a = esiti[-1] in ESITI_A
            situation = ("A: lavoro completo con la sonda fatta" if probe_a
                         else "B: lavoro completo con la sonda rinviata a C4b")
            c(True, f"{SONDA} ({where}): «Esito: {esiti[-1]}»")
            check_tasks(c, lines)
            if probe_a:
                check_probe_a(c, lines, report)
            else:
                check_probe_b(c, lines, report)
            check_review_and_suite(c, lines)
            ws = Workspace(repo, ws_path)
            check_merge_report(c, lines, ws, "riuscita" if probe_a else ESITO_B)
            check_merge(c, repo, args.home, lines, ws_path is None, args.remote, network)
        else:
            situation = "nessuna: «Esito:» della sonda non riconosciuto"
            c(False, f"{SONDA} ({where}) ha «Esito: riuscita», «Esito: riuscita con differenze» "
                     f"o «Esito: {ESITO_B}» (la riga trovata è un'altra)")
    print(f"Situazione: {situation}")
    for ok, row in c.rows:
        print(f"[{'OK' if ok else 'NO'}] {row}")
    done = c.all_ok
    print(f"ESITO: {'finito' if done else 'non finito'}")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
