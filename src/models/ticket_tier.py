"""SQLAlchemy model for TicketTier entity."""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship, validates

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
    concert_id = Column(
        Integer, ForeignKey("concerts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    concert = relationship("Concert", back_populates="tiers")

    @validates("price")
    def validate_price(self, key, value):
        """Reject a negative price; prices are data, not something this
        model defaults or clamps."""
        if value is not None and value < 0:
            raise ValueError("price cannot be negative")
        return value

    @validates("name")
    def validate_name(self, key, value):
        """Reject a blank/whitespace-only name."""
        if value is None or not value.strip():
            raise ValueError("name cannot be blank")
        return value
