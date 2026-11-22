"""Le domande dirette all'utente (`AskUserQuestion`) e le risposte (decisione 4 di C1).

Registra `stop_asked` e `stop_answered`; non nega e non inietta mai: una domanda non si ferma,
e un input di forma inattesa si tace. La fotografia ne ricava le attese dell'utente."""
from __future__ import annotations

from tollgate_hooks.model import record

from ._common import governing_work

CHECK = {"api": 1, "events": ["pre_question", "post_question"], "component": None, "order": 50}
STOP_TEXT_MAX = 300
MAX_QUESTIONS = 4
MAX_OPTIONS = 4


def _text(v) -> str:
    return v[:STOP_TEXT_MAX] if isinstance(v, str) else ""


def _questions(tool_input) -> list[dict]:
    raw = tool_input.get("questions") if isinstance(tool_input, dict) else None
    if not isinstance(raw, list):
        return []
    out = []
    for q in raw:
        if not isinstance(q, dict):
            continue
        opts = q.get("options")
        labels = []
        for o in (opts if isinstance(opts, list) else []):
            label = _text(o.get("label")) if isinstance(o, dict) else _text(o)
            if label:
                labels.append(label)
        out.append({"header": _text(q.get("header")), "question": _text(q.get("question")),
                    "options": labels[:MAX_OPTIONS]})
        if len(out) == MAX_QUESTIONS:
            break
    return out


def _answers(container) -> dict | None:
    found = container.get("answers") if isinstance(container, dict) else None
    if not isinstance(found, dict):
        return None
    out = {_text(k): _text(v) for k, v in found.items() if isinstance(k, str)}
    return out or None


def decide(event, ctx):
    raw = event.raw if isinstance(event.raw, dict) else {}
    use_id = raw.get("tool_use_id")
    use_id = _text(use_id) or None
    work = governing_work(ctx, event.cwd)
    work_id = work["id"] if work is not None else None
    if event.kind == "pre_question":
        questions = _questions(raw.get("tool_input"))
        if not questions:
            return []
        return [record("event", type="stop_asked", work=work_id,
                       data={"tool_use_id": use_id, "questions": questions})]
    if event.hook_event == "PostToolUseFailure":
        answers, source = None, "failure"
    else:
        answers, source = _answers(raw.get("tool_response")), "tool_response"
        if answers is None:
            answers, source = _answers(raw.get("tool_input")), "tool_input"
        if answers is None:
            source = "none"
    return [record("event", type="stop_answered", work=work_id,
                   data={"tool_use_id": use_id, "answers": answers, "source": source})]
