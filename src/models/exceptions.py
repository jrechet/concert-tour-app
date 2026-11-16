"""Domain errors raised by model-level business rules (e.g. `Concert.uncancel`).

Kept separate from the SQLAlchemy models so callers (services, routers) can
import and catch them without importing the models themselves.
"""


class ConcertNotCancelledError(Exception):
    """Raised by `Concert.uncancel()` when the concert's `status` isn't
    `ConcertStatus.cancelled`. `detail` names the concert's current status.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ConcertDateInPastError(Exception):
    """Raised by `Concert.uncancel()` when the concert is cancelled but its
    `date_time` has already passed. `detail` names that date.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
