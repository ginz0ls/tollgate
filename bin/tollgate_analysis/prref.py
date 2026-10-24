"""L'issue di una PR (spec 9.2, decisione 8): dal nome del ramo e dal corpo. Puro."""
from __future__ import annotations

import re

_BRANCH = re.compile(r"^tg/(\d+)-")
_CLOSES = re.compile(r"(?<![\w-])(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)[ \t]*:?[ \t]+#(\d+)\b",
                     re.IGNORECASE)
_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
CONFIG_PREFIX = "tollgate-config/"


def issue_from_branch(ref: str) -> int | None:
    """N di un ramo `tg/<N>-*`, altrimenti `None`."""
    m = _BRANCH.match(ref)
    return int(m.group(1)) if m else None


def _visible(body: str) -> list[str]:
    """Le righe del corpo senza i commenti HTML e senza le citazioni."""
    return [line for line in _COMMENT.sub(" ", body).splitlines()
            if not line.lstrip().startswith(">")]


def closes_issue(body: str) -> int | None:
    """N della prima riga del corpo con `Closes #N`, `Fixes #N` o `Resolves #N` (e varianti,
    senza distinzione di maiuscole); `None` se nessuna riga ha la parola chiave. Una riga citata
    (`> …`) o dentro un commento HTML (`<!-- … -->`, anche su più righe o mai chiuso) non conta."""
    for line in _visible(body):
        m = _CLOSES.search(line)
        if m:
            return int(m.group(1))
    return None


def is_tg_branch(ref: str) -> bool:
    """Un ramo `tg/<N>-*` di un lavoro di tollgate."""
    return issue_from_branch(ref) is not None


def is_config_branch(ref: str) -> bool:
    """Un ramo `tollgate-config/*`."""
    return ref.startswith(CONFIG_PREFIX)
