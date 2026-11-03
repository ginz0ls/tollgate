"""Scrittore TOML minimo: una tabella di stringhe, booleani, liste di stringhe e mappe di
stringhe (tabelle in linea). Un valore di altro tipo è un `TypeError`."""
from __future__ import annotations

import re

_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")
_ESCAPES = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f",
            "\r": "\\r"}


def _string(value: str) -> str:
    out = []
    for ch in value:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _key(key: object) -> str:
    if not isinstance(key, str):
        raise TypeError(f"chiave TOML non stringa: {key!r}")
    return key if _BARE_KEY.fullmatch(key) else _string(key)


def _value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list):
        if not all(isinstance(v, str) for v in value):
            raise TypeError(f"lista TOML ammessa solo di stringhe: {value!r}")
        return "[" + ", ".join(_string(v) for v in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(v, str) for v in value.values()):
            raise TypeError(f"mappa TOML ammessa solo di stringhe: {value!r}")
        if not value:
            return "{}"
        return "{ " + ", ".join(f"{_key(k)} = {_string(v)}" for k, v in value.items()) + " }"
    raise TypeError(f"tipo non scrivibile in TOML: {type(value).__name__}")


def table(name: str, values: dict) -> str:
    """`[name]` seguita da una riga `chiave = valore` per voce; `name` è un percorso con punti."""
    header = ".".join(_key(part) for part in name.split("."))
    lines = [f"[{header}]"]
    lines += [f"{_key(k)} = {_value(v)}" for k, v in values.items()]
    return "\n".join(lines) + "\n"
