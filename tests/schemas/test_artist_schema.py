"""
Unit tests for ArtistSummary Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.artist import ArtistSummary


class TestArtistSummary:
    """Test cases for ArtistSummary schema."""

    def test_valid_payload_serializes_to_same_fields_in_order(self):
        payload = {"name": "Daft Punk", "tour_count": 3}
        summary = ArtistSummary(**payload)
        assert summary.model_dump() == payload
        assert list(summary.model_dump().keys()) == ["name", "tour_count"]

    def test_tour_count_coerced_from_int_like_value(self):
        summary = ArtistSummary(name="Daft Punk", tour_count="3")
        assert summary.tour_count == 3

    @pytest.mark.parametrize("tour_count", [-1, -10])
    def test_negative_tour_count_raises(self, tour_count):
        with pytest.raises(ValidationError):
            ArtistSummary(name="Daft Punk", tour_count=tour_count)

    def test_non_numeric_tour_count_raises(self):
        with pytest.raises(ValidationError):
            ArtistSummary(name="Daft Punk", tour_count="not-a-number")

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ArtistSummary(tour_count=3)

    def test_builds_from_orm_like_object(self):
        class ArtistRow:
            def __init__(self, name, tour_count):
                self.name = name
                self.tour_count = tour_count

        row = ArtistRow(name="Daft Punk", tour_count=3)
        summary = ArtistSummary.model_validate(row)
        assert summary.model_dump() == {"name": "Daft Punk", "tour_count": 3}
