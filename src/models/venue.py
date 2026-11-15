"""SQLAlchemy model for Venue entity.

The (name, city) uniqueness constraint lives only in the Alembic migration
(`migrations/versions/e6f0a9c3b4d7_add_venues_unique_name_city.py`, named
`uq_venues_name_city`), not in `__table_args__` here: several existing
fixtures/tests create venues via `Base.metadata.create_all` (which does not
run migrations) and rely on being able to insert rows that share a (name,
city) pair across different helper calls within one test (see
`tests/fixtures/dashboard_fixtures.create_venues`), so declaring the
constraint on the model would break them. `tests/models/test_venue_model.py`
and `tests/migrations/test_venue_unique_constraint.py` exercise the
constraint against a real, migrated database instead. Code paths that need
the constraint enforced (e.g. the `POST /api/v1/venues` 409 handling)
pre-check via a query rather than depending on the ORM to raise
`IntegrityError`.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import validates

from ..database import Base


class Venue(Base):
    """Venue database model."""

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=True)

    @validates("name")
    def validate_name(self, key, value):
        """Reject an empty or whitespace-only name, mirroring `VenueCreate`/`VenueUpdate`."""
        if value is None or not value.strip():
            raise ValueError("name must not be empty or whitespace")
        return value

    @validates("capacity")
    def validate_capacity(self, key, value):
        """Reject a negative capacity.

        `VenueCreate`/`VenueUpdate` require `capacity > 0` for anything
        coming through the API, but `0` is kept valid here at the model
        level: it's an established edge case elsewhere in the codebase
        (e.g. sold-out/occupancy calculations guard against a zero-capacity
        venue rather than treating it as invalid data - see
        `tests/services/test_occupancy.py::test_zero_total_capacity_returns_zero_percentage`).
        `None` is also allowed through since the column is nullable.
        """
        if value is not None and value < 0:
            raise ValueError("capacity must not be negative")
        return value
