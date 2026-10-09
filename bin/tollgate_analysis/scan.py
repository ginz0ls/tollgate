"""Lettura di codice senza commenti e stringhe (JS/TS e simili, Python)."""
from __future__ import annotations

import io
import tokenize


def js_tokens(text: str):
    """Token di linguaggi con la sintassi del C: ('str', valore), ('id', nome), ('p', carattere)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "'\"`":
            j, buf = i + 1, []
            while j < n and text[j] != c:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                buf.append(text[j])
                j += 1
            yield ("str", "".join(buf))
            i = j + 1
            continue
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (text[j].isalnum() or text[j] in "_$"):
                j += 1
            yield ("id", text[i:j])
            i = j
            continue
        if not c.isspace():
            yield ("p", c)
        i += 1


def js_code(text: str) -> str:
    return " ".join("S" if k == "str" else v for k, v in js_tokens(text))


def py_code(text: str) -> str | None:
    """Codice Python senza commenti né stringhe; None se il file non si legge."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            name = tokenize.tok_name[tok.type]
            if name == "ERRORTOKEN" and not tok.string.isspace():
                return None   # Python 3.11 non solleva su una stringa non chiusa
            if "STRING" in name or name in ("COMMENT", "NL", "NEWLINE", "INDENT", "DEDENT",
                                            "ENDMARKER"):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return " ".join(out)
