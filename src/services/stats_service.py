"""Query logic backing the stats endpoints.

Cities and venue names are derived from `Venue` rows joined to `Concert` on
its `venue_id` foreign key, so only venues that actually host at least one
concert are included (a venue with no concerts is excluded, rather than
listing every venue in the table).
"""

from typing import List

from sqlalchemy.orm import Session

from ..models import Concert, Venue


def get_distinct_cities(db: Session) -> List[str]:
    """Return the distinct, alphabetically sorted cities of venues hosting
    at least one concert."""
    rows = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Venue.city.isnot(None), Venue.city != "")
        .distinct()
        .order_by(Venue.city)
        .all()
    )
    return [row[0] for row in rows]


def get_distinct_venue_names(db: Session) -> List[str]:
    """Return the distinct, alphabetically sorted names of venues hosting
    at least one concert."""
    rows = (
        db.query(Venue.name)
        .join(Concert, Concert.venue_id == Venue.id)
        .filter(Venue.name.isnot(None), Venue.name != "")
        .distinct()
        .order_by(Venue.name)
        .all()
    )
    return [row[0] for row in rows]
