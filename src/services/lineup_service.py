"""Business logic for managing a concert's supporting-act lineup entries."""

from sqlalchemy.orm import Session

from ..models import Concert, LineupEntry
from .concerts_service import ConcertNotFoundError


class LineupEntryNotFoundError(Exception):
    """Raised by `delete_lineup_entry`/`reorder_lineup_entry` when no lineup
    entry with the given id exists for the given concert."""


class InvalidSetOrderError(Exception):
    """Raised by `reorder_lineup_entry` when `new_set_order` is not a
    positive integer."""


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


def clear_lineup(db: Session, concert_id: int) -> None:
    """Remove every supporting-act lineup entry from a concert.

    Raises `ConcertNotFoundError` when no concert with `concert_id` exists.
    Leaves the `Concert` row itself untouched, and is idempotent: calling
    this on a concert whose lineup is already empty succeeds without error.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    db.query(LineupEntry).filter(LineupEntry.concert_id == concert_id).delete()
    db.commit()


def reorder_lineup_entry(db: Session, concert_id: int, entry_id: int, new_set_order: int) -> LineupEntry:
    """Move a lineup entry to `new_set_order`, shifting siblings to keep
    `set_order` values contiguous within the concert.

    Raises `ConcertNotFoundError` when no concert with `concert_id` exists.
    Raises `LineupEntryNotFoundError` when no lineup entry with `entry_id`
    exists, or when it exists but belongs to a different concert (checked
    via the real `LineupEntry.concert_id` foreign key), mirroring
    `delete_lineup_entry`. Raises `InvalidSetOrderError` when
    `new_set_order` is zero or negative.

    Moving to a later position shifts every entry strictly between the old
    and new position down by one; moving to an earlier position shifts
    every entry strictly between the new and old position up by one. The
    moved entry is parked at an unused sentinel `set_order` while siblings
    are shifted (and each shift is flushed immediately), since `LineupEntry`
    enforces a `(concert_id, set_order)` uniqueness rule on every flush and
    shifting in place would otherwise momentarily collide with either the
    entry's own old slot or a sibling's not-yet-shifted slot. On success,
    commits and returns the updated entry.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise ConcertNotFoundError(f"Concert {concert_id} not found")

    if new_set_order <= 0:
        raise InvalidSetOrderError("new_set_order must be a positive integer")

    entry = (
        db.query(LineupEntry)
        .filter(LineupEntry.id == entry_id, LineupEntry.concert_id == concert_id)
        .first()
    )
    if entry is None:
        raise LineupEntryNotFoundError(
            f"Lineup entry {entry_id} not found for concert {concert_id}"
        )

    old_set_order = entry.set_order
    if new_set_order == old_set_order:
        return entry

    siblings = (
        db.query(LineupEntry)
        .filter(LineupEntry.concert_id == concert_id, LineupEntry.id != entry.id)
        .all()
    )

    sentinel = max([s.set_order for s in siblings] + [old_set_order, new_set_order]) + 1
    entry.set_order = sentinel
    db.flush()

    if new_set_order > old_set_order:
        shifted = sorted(
            (s for s in siblings if old_set_order < s.set_order <= new_set_order),
            key=lambda s: s.set_order,
        )
        for sibling in shifted:
            sibling.set_order -= 1
            db.flush()
    else:
        shifted = sorted(
            (s for s in siblings if new_set_order <= s.set_order < old_set_order),
            key=lambda s: s.set_order,
            reverse=True,
        )
        for sibling in shifted:
            sibling.set_order += 1
            db.flush()

    entry.set_order = new_set_order
    db.commit()
    db.refresh(entry)
    return entry
