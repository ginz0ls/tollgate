"""Le note del progetto di prova: ognuna ha un proprietario e sta in un archivio in memoria."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    id: int
    owner: str
    text: str


_NOTES: dict[int, Note] = {}


def add_note(note: Note) -> None:
    _NOTES[note.id] = note


def get_note(note_id: int) -> Note | None:
    return _NOTES.get(note_id)


def clear_notes() -> None:
    _NOTES.clear()
