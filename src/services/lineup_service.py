"""Business logic for managing a concert's supporting-act lineup entries."""

from sqlalchemy.orm import Session

from ..models import Concert, LineupEntry
from .concerts_service import ConcertNotFoundError


class LineupEntryNotFoundError(Exception):
    """Raised by `delete_lineup_entry` when no lineup entry with the given
    id exists for the given concert."""


def delete_lineup_entry(db: Session, concert_id: int, entry_id: int) -> None:
    """Remove a supporting act from a concert's lineup.

    Raises `ConcertNotFoundError` when no concert with `concert_id` exists.
    Raises `LineupEntryNotFoundError` when no lineup entry with `entry_id`
    exists, or when it exists but belongs to a different concert (checked
    via the real `LineupEntry.concert_id` foreign key) — both cases collapse
    onto the same error so a caller can never learn that an entry exists on
    another concert. On success, deletes the entry and commits.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    entry = (
        db.query(LineupEntry)
        .filter(LineupEntry.id == entry_id, LineupEntry.concert_id == concert_id)
        .first()
    )
    if entry is None:
        raise LineupEntryNotFoundError(
            f"Lineup entry {entry_id} not found for concert {concert_id}"
        )

    db.delete(entry)
    db.commit()
