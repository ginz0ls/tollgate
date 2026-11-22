#!/usr/bin/env python3
"""Verifica di «Finito quando» del brief corto di C2, solo sui file.

Uso, dalla radice del repo:

    python3 -B docs/superpowers/plans/2026-11-22-tollgate-c2-verifica-fine.py [--senza-rete]

Legge il ledger del workspace nel worktree `.claude/worktrees/c2` (o, se il worktree non c'è
più, la sua copia su `main` in `docs/sdd/2026-11-22-tollgate-c2-profilo-security/`), i file del
worktree e di `main`, la memoria del progetto, e stampa la situazione (A, B, C, D) con l'esito di
ogni condizione. Esce con 0 se il lavoro è finito (anche «finito per ora», in attesa dell'utente),
con 1 altrimenti. Non scrive niente. `--senza-rete` salta il confronto con GitHub; `--repo` e
`--home` servono alle prove a secco.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

WT_REL = ".claude/worktrees/c2"
WT_PARZIALE_REL = ".claude/worktrees/c2-parziale"
BRANCH, BRANCH_PARZIALE = "c2-profilo-security", "c2-parziale"
SDD_MAIN = "docs/sdd/2026-11-22-tollgate-c2-profilo-security"
SKILL = "skills/rules-security/SKILL.md"
PAGE = "docs/profili/security.md"
PROVA = "docs/verifiche/2026-11-22-c2-prova-flusso.md"
PIANO_PRINCIPALE = "docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md"
REMOTE = "https://github.com/ginz0ls/tollgate.git"
SECTIONS = ("Commit e test", "Regole approvate", "Modelli degli agenti",
            "Decisioni prese durante il lavoro", "Rilievi minori rinviati", "Prova reale",
            "Cosa cambia nei progetti")
ESITO = re.compile(r"^Esito: (riuscita|riuscita \(composita\)|non riuscita: .+)$", re.M)
FERMATA = re.compile(r"^Fermata (aperta|chiusa): (.+?)(?:\s+[—–-]\s+(.*))?\s*$", re.M)


class Check:
    def __init__(self) -> None:
        self.rows: list[tuple[bool, str]] = []

    def __call__(self, ok: bool, text: str) -> bool:
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


def ledger(repo: Path) -> tuple[str | None, Path | None, str]:
    """Il ledger, la cartella del workspace (se nel worktree) e da dove viene."""
    found = sorted((repo / WT_REL / ".superpowers" / "sdd").glob("*/progress.md"))
    if len(found) == 1:
        return read(found[0]), found[0].parent, "worktree"
    if len(found) > 1:
        return None, None, f"più di un workspace sotto {WT_REL}/.superpowers/sdd/"
    text = on_main(repo, f"{SDD_MAIN}/progress.md")
    return text, None, "copia su main" if text is not None else "nessun ledger"


def open_stops(text: str) -> list[str]:
    """I casi delle fermate aperte e non ancora chiuse, in ordine."""
    state: dict[str, bool] = {}
    for kind, case, _ in FERMATA.findall(text):
        state[case.strip().lower()] = kind == "aperta"
    return [c for c, is_open in state.items() if is_open]


def stop_answer(text: str, case: str) -> str | None:
    answers = [a for kind, c, a in FERMATA.findall(text)
               if kind == "chiusa" and c.strip().lower() == case]
    return answers[-1] if answers else None


def has_line(text: str, prefix: str) -> bool:
    return any(line.startswith(prefix) for line in text.splitlines())


def lines_before(text: str, prefix: str, marker: str) -> int | None:
    """Quante righe cominciano con `prefix` prima della riga che comincia con `marker`."""
    count = 0
    for line in text.splitlines():
        if line.startswith(marker):
            return count
        if line.startswith(prefix):
            count += 1
    return None


def section(text: str, title: str) -> str | None:
    m = re.search(r"^## %s\s*$(.*?)(?=^## |\Z)" % re.escape(title), text, re.M | re.S)
    return m.group(1) if m else None


def bullets(body: str) -> int:
    return sum(1 for line in body.splitlines() if line.startswith("- "))


def deferred_rows(review: str) -> int:
    """Le righe della tabella di triage la cui ultima cella (l'esito) comincia con «rinviato»."""
    count = 0
    for line in review.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[-1].lower().startswith("rinviato"):
            count += 1
    return count


def file_text(repo: Path, rel: str) -> str | None:
    """Il file nel worktree se c'è, altrimenti su `main`."""
    wt = repo / WT_REL / rel
    return read(wt) if wt.exists() else on_main(repo, rel)


def memory_text(repo: Path, home: Path) -> str | None:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(repo))
    return read(home / ".claude" / "projects" / slug / "memory" / "plugin-workflow-decisioni.md")


def worktree_listed(repo: Path, rel: str) -> bool:
    out = git(repo, "worktree", "list", "--porcelain") or ""
    target = str((repo / rel).resolve())
    return any(line == f"worktree {target}" for line in out.splitlines())


def check_report(c: Check, led: str, ws: Path | None, name: str, review_name: str,
                 parziale: bool) -> None:
    report = read(ws / name) if ws else None
    c(report is not None, f"il rapporto del merge esiste ({name} del workspace)")
    if report is None:
        return
    for title in SECTIONS:
        c(section(report, title) is not None, f"il rapporto ha la sezione «{title}»")
    c(report.rstrip().endswith("Posso unire su `main`?"),
      "il rapporto finisce con «Posso unire su `main`?»")
    marker = "Rapporto del merge c2-parziale: consegnato" if parziale \
        else "Rapporto del merge: consegnato"
    rulings = lines_before(led, "Ruling:", marker)
    c(rulings is not None, f"il ledger ha la riga «{marker}»")
    body = section(report, "Decisioni prese durante il lavoro") or ""
    if rulings is not None:
        c(bullets(body) == rulings, f"«Decisioni prese durante il lavoro» ha una riga per ognuna "
                                    f"delle {rulings} righe Ruling: prima del rapporto "
                                    f"(trovate {bullets(body)})")
    review = read(ws / review_name) if ws else None
    c(review is not None, f"{review_name} del workspace esiste")
    if review is not None:
        want = deferred_rows(review)
        body = section(report, "Rilievi minori rinviati") or ""
        got = bullets(body)
        c(got == want and (want > 0 or "Nessuno." in body),
          f"«Rilievi minori rinviati» ha una riga per ognuna delle {want} voci «rinviato» "
          f"(trovate {got}; con zero voci serve «Nessuno.»)")
    if parziale:
        c("rinviate dall'utente" in (section(report, "Regole approvate") or "")
          or "rifiutate dall'utente" in (section(report, "Regole approvate") or ""),
          "«Regole approvate» dice «rinviate dall'utente» o «rifiutate dall'utente»")
        c("non fatta: regole rinviate" in (section(report, "Prova reale") or ""),
          "«Prova reale» dice «non fatta: regole rinviate»")


def check_after_merge(c: Check, repo: Path, home: Path, led: str, *, subject: str, memory: str,
                      wt_rel: str, network: bool, parziale: bool) -> None:
    log = git(repo, "log", "main", "--format=%s") or ""
    c(any(s.startswith(subject) for s in log.splitlines()),
      f"git log main ha un commit «{subject}…»")
    c(on_main(repo, f"{SDD_MAIN}/README.md") is not None, f"{SDD_MAIN}/README.md è su main")
    plan = on_main(repo, PIANO_PRINCIPALE) or ""
    row = next((l for l in plan.splitlines() if l.startswith("| **C2")), "")
    c("unita" in row, "il piano principale su main ha «unita» nella riga C2")
    mem = memory_text(repo, home) or ""
    c(any(l.startswith(memory) for l in mem.splitlines()),
      f"plugin-workflow-decisioni.md ha una riga che comincia con «{memory}»")
    closing = "Chiusura di C2 parziale: consegnata" if parziale else "Chiusura di C2: consegnata"
    c(has_line(led, closing), f"il ledger ha «{closing}»")
    stop = "worktree c2-parziale" if parziale else "worktree"
    pending = stop in open_stops(led)
    answer = stop_answer(led, stop)
    listed = worktree_listed(repo, wt_rel)
    if pending and not listed:
        c(True, f"worktree {wt_rel} rimosso dopo la domanda")
    elif pending:
        c(True, "domanda sul worktree fatta, l'utente non ha ancora risposto")
    elif answer is not None:
        removed = answer.strip().lower().startswith("rimuovi")
        c(not removed or not listed,
          f"risposta sul worktree «{answer}»: {'rimosso' if not listed else 'ancora presente'}")
    else:
        c(False, f"nessuna domanda sul worktree nel ledger (Fermata aperta: {stop})")
    if network:
        local = (git(repo, "rev-parse", "main") or "").strip()
        remote = (git(repo, "ls-remote", REMOTE, "main") or "").split("\t")[0].strip()
        c(bool(local) and local == remote, f"GitHub ha lo stesso main ({remote[:12] or '?'} "
                                           f"contro {local[:12] or '?'})")


def branch_commits(repo: Path, branch: str) -> list[str] | None:
    """I commit del ramo dopo il punto in cui si è staccato da `main`; `None` se il ramo non c'è."""
    if git(repo, "rev-parse", "--verify", "--quiet", branch) is None:
        return None
    base = (git(repo, "merge-base", "main", branch) or "").strip()
    out = git(repo, "rev-list", f"{base}..{branch}") if base else None
    return out.split() if out else []


def situation_a(c: Check, repo: Path, home: Path, led: str, ws: Path | None,
                network: bool) -> bool:
    for n in range(1, 11):
        c(has_line(led, f"Task {n}: complete"), f"ledger: «Task {n}: complete»")
    skill = file_text(repo, SKILL) or ""
    m = re.search(r"^approved: (\d{4}-\d{2}-\d{2})$", skill, re.M)
    c(m is not None, f"{SKILL} ha «approved: <data>»")
    page = file_text(repo, PAGE) or ""
    if m:
        a, mo, d = m.group(1).split("-")
        c(f"Approvata dall'utente il {d}/{mo}/{a}." in page
          or f"Approvata dall'utente il {m.group(1)}." in page,
          f"{PAGE} ha «Approvata dall'utente il …» con la stessa data")
    prova = file_text(repo, PROVA) or ""
    c(ESITO.search(prova) is not None, f"{PROVA} ha la riga «Esito: …»")
    c(has_line(led, "Prova:"), "ledger: almeno una riga «Prova:»")
    c(has_line(led, "Revisione finale (Fable):"), "ledger: «Revisione finale (Fable): …»")
    c(has_line(led, "Revisione finale chiusa: 0 critical, 0 important aperti"),
      "ledger: «Revisione finale chiusa: 0 critical, 0 important aperti»")
    for n in (1, 2, 3):
        c(has_line(led, f"Suite finale corsa {n}: verde su python3.11 e python3"),
          f"ledger: «Suite finale corsa {n}: verde …»")
    return finish_merge(c, repo, home, led, ws, network, parziale=False)


def situation_b(c: Check, repo: Path, home: Path, led: str, ws: Path | None,
                network: bool) -> bool:
    for n in (1, 2, 3, 4, 5):
        c(has_line(led, f"Task {n}: complete"), f"ledger: «Task {n}: complete»")
    c(has_line(led, "Task 6: rinviato dall'utente"), "ledger: «Task 6: rinviato dall'utente»")
    c(has_line(led, "Task 10 ridotto: complete"), "ledger: «Task 10 ridotto: complete»")
    commits = [l for l in led.splitlines() if l.startswith("c2-parziale: ")]
    for subject in ("tollgate C2: revisori su Fable, implementatori su opus, mai sonnet",
                    "tollgate C2: sicurezza fin dal progetto per chi pianifica, implementa e "
                    "rivede",
                    "tollgate C2: keep_paths, un frammento che accende i suoi percorsi anche "
                    "per i file trovati da un altro"):
        c(any(subject in l for l in commits), f"ledger: «c2-parziale: …» con «{subject}»")
    shas = branch_commits(repo, BRANCH_PARZIALE)
    if shas is None:
        c(True, "ramo c2-parziale non più presente: i commit si controllano solo nel ledger")
    else:
        listed = " ".join(commits)
        missing = [x for x in shas if x[:7] not in listed]
        c(not missing, f"ledger: una riga «c2-parziale: …» per ognuno dei {len(shas)} commit "
                       f"del ramo (mancano {len(missing)})")
    c(any("tollgate C2 (parziale): spec rev 37 ridotta" in l for l in commits),
      "ledger: «c2-parziale: …» con «tollgate C2 (parziale): spec rev 37 ridotta»")
    c(has_line(led, "Revisione finale c2-parziale (Fable):"),
      "ledger: «Revisione finale c2-parziale (Fable): …»")
    c(has_line(led, "Revisione finale c2-parziale chiusa: 0 critical, 0 important aperti"),
      "ledger: «Revisione finale c2-parziale chiusa: 0 critical, 0 important aperti»")
    for n in (1, 2, 3):
        c(has_line(led, f"Suite finale c2-parziale corsa {n}: verde su python3.11 e python3"),
          f"ledger: «Suite finale c2-parziale corsa {n}: verde …»")
    return finish_merge(c, repo, home, led, ws, network, parziale=True)


def finish_merge(c: Check, repo: Path, home: Path, led: str, ws: Path | None, network: bool,
                 *, parziale: bool) -> bool:
    name = "rapporto-merge-c2-parziale.md" if parziale else "rapporto-merge.md"
    review = "final-review-c2-parziale.md" if parziale else "final-review.md"
    if ws is not None:
        check_report(c, led, ws, name, review, parziale)
    else:
        sdd = SDD_MAIN
        c(on_main(repo, f"{sdd}/{name}") is not None, f"{sdd}/{name} è su main")
    stop = "merge c2-parziale" if parziale else "merge"
    head = "Merge c2-parziale:" if parziale else "Merge:"
    if stop in open_stops(led):
        c(True, "rapporto consegnato, l'utente non ha ancora risposto sul merge: finito per ora")
        return True
    if has_line(led, f"{head} no dell'utente"):
        c(True, "l'utente ha detto no al merge: il lavoro è finito qui")
        return True
    if not c(has_line(led, f"{head} OK dell'utente"),
             f"ledger: «{head} OK dell'utente» (o la fermata «{stop}» aperta, o il no)"):
        return False
    check_after_merge(c, repo, home, led,
                      subject="tollgate C2 (parziale):" if parziale
                      else "tollgate C2: profilo security",
                      memory="- C2 parziale" if parziale else "- C2 eseguito",
                      wt_rel=WT_PARZIALE_REL if parziale else WT_REL, network=network,
                      parziale=parziale)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--home", type=Path, default=Path.home())
    ap.add_argument("--senza-rete", action="store_true")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    led, ws, origin = ledger(repo)
    c = Check()
    print(f"Ledger: {origin}")
    if led is None:
        c(False, "il ledger di C2 esiste (lavoro non cominciato?)")
        situation = "nessuna: lavoro non cominciato"
    else:
        stops = [s for s in open_stops(led)
                 if s not in ("merge", "worktree", "merge c2-parziale", "worktree c2-parziale")]
        approved = re.search(r"^approved: \d{4}-\d{2}-\d{2}$", file_text(repo, SKILL) or "",
                             re.M)
        if "regole" in stops:
            situation = "C: in attesa dell'utente sulle regole (finito per ora)"
            c(True, "fermata «regole» aperta nel ledger, l'utente non ha ancora risposto")
        elif stops:
            situation = f"D: fermata per un altro caso ({stops[-1]}; finito per ora)"
            c(True, f"fermata «{stops[-1]}» aperta nel ledger, l'utente non ha ancora risposto")
        elif approved:
            situation = "A: regole approvate"
            situation_a(c, repo, args.home, led, ws, not args.senza_rete)
        elif has_line(led, "Task 6: rinviato dall'utente"):
            situation = "B: regole rinviate"
            situation_b(c, repo, args.home, led, ws, not args.senza_rete)
        else:
            situation = "nessuna: lavoro in corso"
            c(False, "il lavoro è in una delle situazioni A, B, C o D")
    print(f"Situazione: {situation}")
    for ok, text in c.rows:
        print(f"[{'OK' if ok else 'NO'}] {text}")
    done = c.all_ok
    print(f"ESITO: {'finito' if done else 'non finito'}")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
