"""SQLAlchemy model for TicketTier entity."""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UniqueConstraint

from ..database import Base


class TicketTier(Base):
    """A priced ticket tier offered for a concert (e.g. General Admission,
    VIP, Premium).

    Currently populated only by `src.demo.seeder.seed_demo`: `Concert.
    ticket_price` still independently carries the single headline price
    shown elsewhere in the app.
    """

    __tablename__ = "ticket_tiers"
    __table_args__ = (
        UniqueConstraint("concert_id", "name", name="uq_ticket_tiers_concert_id_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, ForeignKey("concerts.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
