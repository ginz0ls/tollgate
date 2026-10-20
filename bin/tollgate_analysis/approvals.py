"""File di approvazione `spec-approval.md` e `plan-approval.md` (spec 18.3)."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

KINDS = ("spec-approval", "plan-approval")
REQUIRED = ("kind", "path", "sha")
REVIEWS_DIR = "docs/superpowers/reviews"
_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)$")
_INT = re.compile(r"^-?\d{1,6}$")


def approval_paths(issue: int) -> tuple[str, str]:
    """Percorsi (relativi al worktree) di `spec-approval.md` e `plan-approval.md`."""
    base = f"{REVIEWS_DIR}/{issue}"
    return f"{base}/spec-approval.md", f"{base}/plan-approval.md"


_MAP = re.compile(r"^\{(.*)\}$")
_PAIR = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(-?\d{1,6})$")
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
REPORT_KINDS = ("spec-adversarial", "spec-lens", "plan-adversarial")
SEVERITIES = ("blocker", "major", "moderate", "minor")
_REPORT_NAME = re.compile(r"^(spec-adversarial|spec-lens|plan-adversarial)-(\d+)\.md$")
_APPROVAL_PATH = re.compile(rf"^{re.escape(REVIEWS_DIR)}/(\d+)/spec-approval\.md$")


def _value(raw: str):
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        end = raw.find(raw[0], 1)
        if end > 0 and (not raw[end + 1:].strip() or raw[end + 1:].lstrip().startswith("#")):
            return raw[1:end]
    raw = re.sub(r"\s+#.*$", "", raw)
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if raw in ("null", "~", ""):
        return None
    m = _MAP.match(raw)
    if m:
        pairs = [_PAIR.match(x.strip()) for x in m.group(1).split(",")]
        if all(pairs):
            return {p.group(1): int(p.group(2)) for p in pairs}
        return raw
    return int(raw) if _INT.match(raw) else raw


def parse_header(text: str) -> dict | None:
    """L'intestazione tra le due righe `---` come dizionario, oppure `None` se manca, non si
    chiude o ha una riga che non è `chiave: valore`. Valori tra virgolette (con un eventuale
    commento dopo) o nudi; `null` è `None`; `{chiave: intero, ...}` è un dizionario."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    header: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return header
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if m is None:
            return None
        header[m.group(1)] = _value(m.group(2))
    return None


def parse_approval(text: str) -> dict | None:
    """L'intestazione di un file di approvazione, oppure `None` se `parse_header` non la legge,
    non è di un `kind` di approvazione o le manca `path` o `sha`."""
    header = parse_header(text)
    if header is None or header.get("kind") not in KINDS \
            or any(not header.get(k) for k in REQUIRED):
        return None
    return header


def parse_report_header(text: str) -> dict | None:
    """L'intestazione di un report di giro, oppure `None` se `kind` non è in `REPORT_KINDS`,
    `number` non è un intero >= 1 o `counts` non ha esattamente le quattro gravità, intere >= 0."""
    header = parse_header(text)
    if header is None or header.get("kind") not in REPORT_KINDS:
        return None
    number, counts = header.get("number"), header.get("counts")
    if not isinstance(number, int) or number < 1 or not isinstance(counts, dict) \
            or set(counts) != set(SEVERITIES) or any(v < 0 for v in counts.values()):
        return None
    return header


def _render_value(key: str, value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        raise ValueError(f"{key}: valore booleano non ammesso")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, dict):
        for k, v in value.items():
            if not _KEY.match(str(k)) or isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"{key}: voce non ammessa: {k!r}")
        return "{" + ", ".join(f"{k}: {v}" for k, v in value.items()) + "}"
    if isinstance(value, str):
        if any(unicodedata.category(c) in ("Cc", "Zl", "Zp") or c == '"' for c in value):
            raise ValueError(f"{key}: a capo, virgolette o caratteri di controllo non ammessi")
        return f'"{value}"'
    raise ValueError(f"{key}: tipo non ammesso: {type(value).__name__}")


def _render_header(fields: dict) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if not _KEY.match(str(key)):
            raise ValueError(f"nome di campo non ammesso: {key!r}")
        lines.append(f"{key}: {_render_value(key, value)}")
    return "\n".join(lines + ["---", ""])


def render_approval(fields: dict) -> str:
    """Un file di approvazione: l'intestazione dei `fields` (stringhe tra virgolette doppie,
    interi nudi, `None` come `null`). `ValueError` se un valore stringa ha un a capo, `"` o un
    carattere di controllo. `parse_approval(render_approval(f))` restituisce `f`."""
    return _render_header(fields)


def render_report(fields: dict, body: str) -> str:
    """Un report di giro: l'intestazione dei `fields` (`counts` come `{blocker: 0, ...}`) e il
    corpo. Stesse regole e stesso `ValueError` di `render_approval`."""
    return _render_header(fields) + body


def approval_listing(paths) -> list[str]:
    """I percorsi `docs/superpowers/reviews/<n>/spec-approval.md` di un elenco, nell'ordine dato."""
    return [p for p in paths if _APPROVAL_PATH.match(p)]


def report_listing(paths, folders) -> list[str]:
    """I percorsi di report di giro (nome `<tipo>-<n>.md`) direttamente dentro una delle
    `folders`, senza barra finale, nell'ordine dato."""
    wanted = set(folders)
    return [p for p in paths if p.rpartition("/")[0] in wanted
            and _REPORT_NAME.match(p.rpartition("/")[2])]


def locate_spec_approval(files: Mapping[str, str], *, issue: int, spec_path: str,
                         spec_blob: str | None) -> tuple[str, dict] | None:
    """L'approvazione della spec `spec_path`, come (percorso, intestazione), oppure `None`.
    Prima quella del lavoro (`reviews/<issue>/`) se ha `path == spec_path`, qualunque `sha`
    (chi chiama controlla `is_current`); poi, per una fetta successiva, quella di un'altra
    issue con `path == spec_path` e `sha == spec_blob` (con `spec_blob = None` basta il
    `path`); con più candidati vince il numero di issue più basso.

    Pura: `files` (percorso -> testo) lo sceglie il chiamante, cioè HEAD, la punta del ramo
    predefinito o il disco; qui non si legge nulla."""
    own = approval_paths(issue)[0]
    candidates = [own] + sorted((p for p in approval_listing(files) if p != own),
                                key=lambda p: int(_APPROVAL_PATH.match(p).group(1)))
    for path in candidates:
        if path not in files:
            continue
        header = parse_approval(files[path])
        if header is None or header["kind"] != "spec-approval" or header["path"] != spec_path:
            continue
        if path == own or spec_blob is None or header["sha"] == spec_blob:
            return path, header
    return None


def _reports(files: Mapping[str, str], folder: str, kind: str) -> int:
    """Quanti report di `kind` con intestazione valida ci sono in `folder`."""
    n = 0
    for path, text in files.items():
        head, _, name = path.rpartition("/")
        m = _REPORT_NAME.match(name)
        if head == folder and m and m.group(1) == kind:
            header = parse_report_header(text)
            n += header is not None and header["kind"] == kind
    return n


def check_l2(files: Mapping[str, str], *, issue: int, spec_path: str | None,
             spec_blob: str | None, plan_path: str | None, plan_blob: str | None) -> list[str]:
    """La voce `approvals` della DoD in L2 (spec 8.7): i problemi, o `[]` se spec e piano sono
    approvati e i report richiesti ci sono. `files` è `{percorso: testo}` di tutti i file sotto
    `docs/superpowers/reviews/` dell'albero scelto dal chiamante. Ogni messaggio nomina il file
    o il report che manca."""
    problems: list[str] = []
    if not spec_path or spec_blob is None:
        problems.append("spec non registrata o assente dall'albero: manca l'approvazione della "
                        "spec (spec-approval.md)")
    else:
        found = locate_spec_approval(files, issue=issue, spec_path=spec_path, spec_blob=spec_blob)
        if found is None:
            problems.append(f"manca il file di approvazione della spec {spec_path} con lo sha "
                            f"attuale ({approval_paths(issue)[0]})")
        elif not is_current(found[1], spec_blob):
            problems.append(f"{found[0]}: la spec {spec_path} è cambiata dopo l'approvazione "
                            f"(rifai approve spec)")
        else:
            path, header = found
            folder = path.rpartition("/")[0]
            if header.get("adversarial") != "off" \
                    and not _reports(files, folder, "spec-adversarial"):
                problems.append(f"manca il report spec-adversarial-<n>.md valido in {folder}/")
            slices = header.get("slices")
            if isinstance(slices, int) and slices > 1 and header.get("lens") == "closed" \
                    and not _reports(files, folder, "spec-lens"):
                problems.append(f"manca il report spec-lens-<n>.md valido in {folder}/")
    plan_approval = approval_paths(issue)[1]
    if not plan_path or plan_blob is None:
        problems.append(f"piano non registrato o assente dall'albero: manca l'approvazione del "
                        f"piano ({plan_approval})")
        return problems
    header = parse_approval(files.get(plan_approval, ""))
    if header is None or header["kind"] != "plan-approval":
        problems.append(f"manca il file di approvazione del piano {plan_approval}")
        return problems
    if not is_current(header, plan_blob):
        problems.append(f"{plan_approval}: il piano {plan_path} è cambiato dopo l'approvazione "
                        f"(rifai approve plan)")
    if spec_blob is not None and header.get("spec_sha") != spec_blob:
        problems.append(f"{plan_approval}: approvato su una spec diversa da quella attuale "
                        f"(rifai approve plan)")
    folder = plan_approval.rpartition("/")[0]
    if header.get("adversarial") != "off" and not _reports(files, folder, "plan-adversarial"):
        problems.append(f"manca il report plan-adversarial-<n>.md valido in {folder}/")
    return problems


def is_current(header: dict, blob_sha: str | None) -> bool:
    """L'approvazione vale se `sha` è il blob attuale del documento; un documento assente o
    modificato dopo l'approvazione la rende superata."""
    return blob_sha is not None and header.get("sha") == blob_sha
