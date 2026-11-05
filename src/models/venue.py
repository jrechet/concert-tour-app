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

from ..database import Base


class Venue(Base):
    """Venue database model."""

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=True)
