"""Pattern nel dialetto di .gitignore (spec 3.2), su percorsi relativi alla radice del repo."""
from __future__ import annotations

import re
from functools import lru_cache

_GLOB_CHARS = set("*?[")


def is_pattern(s: str) -> bool:
    return any(c in _GLOB_CHARS for c in s)


def literal_segments(pattern: str) -> int:
    return sum(1 for seg in pattern.strip("/").split("/") if seg and not is_pattern(seg))


@lru_cache(maxsize=1024)
def compile(pattern: str) -> re.Pattern:  # noqa: A001 - nome voluto, come re.compile
    p = pattern
    dir_only = p.endswith("/")
    p = p.rstrip("/")
    anchored = p.startswith("/") or "/" in p
    p = p.lstrip("/")
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif p.startswith("/**", i) and i + 3 == len(p):
            out.append("/.*")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "[":
            j = p.find("]", i + 1)
            if j == -1:
                out.append(re.escape("["))
                i += 1
            else:
                body = p[i + 1:j]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append("[" + body.replace("\\", "\\\\") + "]")
                i = j + 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    prefix = "" if anchored else "(?:.*/)?"
    suffix = "/.*" if dir_only else "(?:/.*)?"
    return re.compile("^" + prefix + "".join(out) + suffix + "$")


def match(pattern: str, path: str) -> bool:
    return compile(pattern).match(path[2:] if path.startswith("./") else path) is not None


def match_any(patterns, path: str) -> bool:
    return any(match(p, path) for p in patterns)
