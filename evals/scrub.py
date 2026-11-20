#!/usr/bin/env python3
"""Pulizia delle evidenze copiate da `evals/run.sh` (decisioni 9 e 10 di B8): niente testo di terzi, niente dati privati.

Uso:
  scrub.py domains                         i domini web concessi agli eval (uno per riga): `run.sh` ne costruisce i permessi
  scrub.py strip-web <trace.jsonl>...      sostituisce ogni risultato di WebFetch e WebSearch con un segnaposto (strip_web_results)
  scrub.py strip-bash <trace.jsonl>...     sostituisce il risultato dei Bash che leggono un dominio concesso (strip_bash_web)
  scrub.py anonymize <cartella> <utente> <host>   sostituisce `/home/<utente>`, `-home-<utente>-`, il nome utente (parola intera) e l'host
                                           con `/home/USER`, `-home-USER-`, `USER` e `HOST` nei file di testo e nei database
                                           SQLite della cartella; non stampa mai i due valori

Le trace sono dati non fidati: qui si leggono e si riscrivono, mai si eseguono. Solo libreria standard."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))
from tollgate_analysis import bash  # noqa: E402

# L'unico elenco dei domini concessi con `--allow-tools "WebFetch(domain:…)"`: `run.sh` lo legge con `domains`.
WEB_DOMAINS = ("ai.google.dev", "aistudio.google.com", "vercel.com")
WEB_TOOLS = ("WebFetch", "WebSearch")
RESERVED = ("user", "type", "home", "root", "test", "tool")
MIN_VALUE_LEN = 4
EXIT_BAD_VALUE = 2

_spec = importlib.util.spec_from_file_location("flowreg", ROOT / "spikes" / "b1" / "flowreg.py")
flowreg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(flowreg)


# ---------------------------------------------------------------- tracce

def _rewrite(trace: Path, edit) -> int:
    """Applica `edit(obj, names)` a ogni riga JSON della trace (`names`: id del tool_use -> etichetta, condiviso
    tra le righe) e riscrive il file se qualche riga è cambiata. `edit` ritorna quanti risultati ha sostituito."""
    out, total = [], 0
    names: dict = {}
    for line in Path(trace).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            obj = None
        n = edit(obj, names) if isinstance(obj, dict) else 0
        total += n
        out.append(json.dumps(obj, ensure_ascii=False) if n else line)
    if total:
        Path(trace).write_text("\n".join(out) + "\n", encoding="utf-8")
    return total


def _blocks(obj: dict) -> list:
    content = (obj.get("message") or {}).get("content") if isinstance(obj.get("message"), dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _flatten(value, label: str):
    """`value` con ogni stringa di testo sostituita dal segnaposto (chiavi, numeri, booleani e null restano);
    ritorna (nuovo valore, quante stringhe ha sostituito). Un segnaposto già messo non si tocca."""
    if isinstance(value, str):
        if not value or value.startswith(flowreg.PAGE_PLACEHOLDER):
            return value, 0
        return flowreg._placeholder(label, len(value)), 1
    if isinstance(value, dict):
        done, count = {}, 0
        for key, item in value.items():
            done[key], n = _flatten(item, label)
            count += n
        return done, count
    if isinstance(value, list):
        pairs = [_flatten(item, label) for item in value]
        return [p[0] for p in pairs], sum(p[1] for p in pairs)
    return value, 0


def strip_web_results(trace: Path) -> int:
    """Sostituisce **ogni** risultato di `WebFetch` e `WebSearch` della trace, di qualsiasi lunghezza, con un segnaposto
    che tiene l'indirizzo (o l'interrogazione): nel blocco `tool_result` e in `tool_use_result`, dove chiavi, numeri e
    booleani restano e ogni stringa di testo diventa il segnaposto. Ritorna il numero di risultati sostituiti
    (zero se sono già segnaposto: si può rilanciare)."""
    def edit(obj, names):
        count = 0
        for block in _blocks(obj):
            if block.get("type") == "tool_use" and block.get("name") in WEB_TOOLS:
                ti = block.get("input") if isinstance(block.get("input"), dict) else {}
                names[block.get("id")] = str(ti.get("url") or ti.get("query") or block.get("name"))
        for block in _blocks(obj):
            if block.get("type") != "tool_result" or block.get("tool_use_id") not in names:
                continue
            label = names[block["tool_use_id"]]
            text = flowreg._content_text(block.get("content"))
            changed = False
            if text and not text.startswith(flowreg.PAGE_PLACEHOLDER):
                block["content"] = flowreg._placeholder(label, len(text))
                changed = True
            elif isinstance(block.get("content"), list) and not text:
                block["content"] = flowreg._placeholder(label, 0)
                changed = True
            if "tool_use_result" in obj:
                obj["tool_use_result"], n = _flatten(obj["tool_use_result"], label)
                changed = changed or n > 0
            count += changed
        return count
    return _rewrite(trace, edit)


def _is_note_delivery(argv: list[str]) -> bool:
    """`research submit` come parole contigue subito dopo il programma `tollgate` (da solo o dietro `python3`/`python`)."""
    if argv and os.path.basename(argv[0]) in ("python3", "python"):
        argv = argv[1:]
    return len(argv) >= 3 and argv[0].endswith("tollgate") and argv[1:3] == ["research", "submit"]


def _is_exempt(command: str) -> bool:
    """La consegna della nota (`research submit`, anche con un heredoc che nomina il dominio) e un `sed` che scrive
    l'indirizzo in un file non leggono niente: ogni comando letto da `bash.parse` è uno di questi due."""
    try:
        cmds = bash.parse(command, "/")
    except ValueError:
        return False
    return bool(cmds) and all(
        c.argv and (os.path.basename(c.argv[0]) == "sed" or _is_note_delivery(c.argv)) for c in cmds)


def _names_domain(command: str, domains: tuple[str, ...]) -> str | None:
    """Il dominio concesso che il testo grezzo del comando (heredoc e here-string compresi) nomina, a parola intera."""
    for d in domains:
        if re.search(r"(?<![\w-])" + re.escape(d) + r"(?![\w-])", command, re.IGNORECASE):
            return d.lower()
    return None


def _fetches_domain(command: str, domains: tuple[str, ...]) -> str | None:
    """Il dominio concesso che un `Bash` nomina nel suo testo grezzo, salvo la consegna della nota e un `sed`."""
    domain = _names_domain(command, domains)
    return None if domain is None or _is_exempt(command) else domain


def strip_bash_web(trace: Path, domains: tuple[str, ...]) -> int:
    """Sostituisce con un segnaposto il risultato di ogni `Bash` il cui testo grezzo nomina uno dei `domains` (una pagina letta con
    qualunque programma finisce in un `tool_result` che `togli-pagine` non tocca), salvo la consegna della nota e un `sed`. Ritorna il numero di risultati sostituiti."""
    def edit(obj, names):
        count = 0
        for block in _blocks(obj):
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                ti = block.get("input") if isinstance(block.get("input"), dict) else {}
                command = ti.get("command")
                domain = _fetches_domain(command, domains) if isinstance(command, str) else None
                if domain:
                    names[("bash", block.get("id"))] = f"risultato di Bash verso {domain}"
        for block in _blocks(obj):
            label = names.get(("bash", block.get("tool_use_id"))) if block.get("type") == "tool_result" else None
            if not label:
                continue
            text = flowreg._content_text(block.get("content"))
            res = obj.get("tool_use_result")
            streams = [res.get(k) for k in ("stdout", "stderr") if isinstance(res, dict) and isinstance(res.get(k), str)]
            left = [x for x in (text, *streams) if x and not x.startswith(flowreg.PAGE_PLACEHOLDER)]
            if left:
                flowreg._swap_saved(obj, block, text if text.startswith(flowreg.PAGE_PLACEHOLDER)
                                    else flowreg._placeholder(label, len(left[0])))
                count += 1
        return count
    return _rewrite(trace, edit)


# ---------------------------------------------------------------- anonimizzazione

def _check_values(user: str, host: str) -> None:
    for what, value in (("utente", user), ("host", host)):
        if len(value) < MIN_VALUE_LEN or value.lower() in RESERVED:
            raise ValueError(f"valore dell'{what} troppo corto o riservato: non anonimizzo niente")


def _patterns(user: str, host: str):
    home = re.compile(re.escape(f"/home/{user}") + r"\b")
    folder = re.compile(re.escape(f"-home-{user}-"))      # come Claude Code chiama le cartelle di progetto e la sua temporanea
    name = re.compile(r"\b" + re.escape(host) + r"\b", re.IGNORECASE)
    person = re.compile(r"\b" + re.escape(user) + r"\b")      # proprietario e gruppo nell'uscita di `ls -la`

    def clean(text: str) -> str:
        return name.sub("HOST", person.sub("USER", folder.sub("-home-USER-", home.sub("/home/USER", text))))
    return clean


def _is_db_file(path: Path) -> bool:
    return re.search(r"\.db(?:-[a-z]+)?$", path.name) is not None


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _scrub_db(path: Path, clean) -> bool:
    """Riscrive le colonne di testo di un database SQLite e lo compatta; ritorna `True` se ha cambiato qualcosa."""
    changed = False
    with closing(sqlite3.connect(path, isolation_level=None)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            for col in [r[1] for r in conn.execute(f"PRAGMA table_info({_quote(table)})")]:
                q = _quote(col)
                values = [r[0] for r in conn.execute(f"SELECT DISTINCT {q} FROM {_quote(table)} WHERE typeof({q}) = 'text'")]
                for old in values:
                    new = clean(old)
                    if new != old:
                        conn.execute(f"UPDATE {_quote(table)} SET {q} = ? WHERE {q} = ? AND typeof({q}) = 'text'", (new, old))
                        changed = True
        if changed:
            conn.execute("VACUUM")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        verdict = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if verdict != "ok":
            raise RuntimeError(f"{path.name}: integrity_check non è ok")
    return changed


def anonymize(out_dir: Path, user: str, host: str) -> int:
    """Sostituisce `/home/<user>` con `/home/USER`, `-home-<user>-` (le cartelle di Claude Code) con `-home-USER-`, `user`
    (parola intera) con `USER` e `host` (parola intera) con `HOST` in tutti i file della cartella: prima
    i `.db` (colonne di testo, `VACUUM`, checkpoint che toglie `-wal` e `-shm`, `integrity_check`), poi i file che si decodificano
    in UTF-8. Ritorna il numero di file cambiati. `ValueError` se uno dei due valori è più corto di 4 caratteri o riservato
    (e allora non si tocca niente). Non stampa mai i due valori."""
    _check_values(user, host)
    clean = _patterns(user, host)
    files = sorted(p for p in Path(out_dir).rglob("*") if p.is_file() and not p.is_symlink())
    changed = 0
    for path in (p for p in files if p.suffix == ".db"):
        changed += _scrub_db(path, clean)
    for path in (p for p in files if not _is_db_file(p)):
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new = clean(text)
        if new != text:
            try:
                path.write_text(new, encoding="utf-8")
            except PermissionError:
                path.chmod(path.stat().st_mode | 0o200)
                path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


# ---------------------------------------------------------------- riga di comando

def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "domains" and not rest:
        print("\n".join(WEB_DOMAINS))
        return 0
    if cmd in ("strip-web", "strip-bash") and rest:
        for trace in rest:
            n = strip_web_results(Path(trace)) if cmd == "strip-web" else strip_bash_web(Path(trace), WEB_DOMAINS)
            print(f"{trace}: {n} risultati sostituiti")
        return 0
    if cmd == "anonymize" and len(rest) == 3:
        try:
            n = anonymize(Path(rest[0]), rest[1], rest[2])
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return EXIT_BAD_VALUE
        print(f"anonimizzati {n} file in {rest[0]}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
