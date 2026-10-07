"""SQLAlchemy model for Venue entity.

The (name, city) uniqueness constraint lives only in the Alembic migration
(`migrations/versions/e6f0a9c3b4d7_add_venues_unique_name_city.py`), not in
`__table_args__` here: several existing fixtures/tests create venues via
`Base.metadata.create_all` (which does not run migrations) and rely on
being able to insert rows that share a (name, city) pair, so declaring the
constraint on the model would break them. Code paths that need the
constraint enforced (e.g. the `POST /api/v1/venues` 409 handling) pre-check
via a query instead of depending on the ORM to raise `IntegrityError`.
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
