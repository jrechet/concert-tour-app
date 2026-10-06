"""
Unit tests for ArtistSummary Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.artist import ArtistSummary


class TestArtistSummary:
    """Test cases for ArtistSummary schema."""

    def test_serializes_to_expected_shape(self):
        payload = {"name": "The Openers", "tour_count": 3}
        summary = ArtistSummary(**payload)
        assert summary.model_dump() == payload

    @pytest.mark.parametrize("tour_count", [0, -1])
    def test_non_positive_tour_count_raises(self, tour_count):
        with pytest.raises(ValidationError):
            ArtistSummary(name="The Openers", tour_count=tour_count)

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ArtistSummary(tour_count=3)
