"""
Unit tests for the venue search query and response schemas.
"""

import pytest
from pydantic import ValidationError

from src.schemas.venue import VenueSearchQuery


class TestVenueSearchQuery:
    """Test cases for VenueSearchQuery schema."""

    def test_minimum_length_query_is_accepted(self):
        query = VenueSearchQuery(q="ar")
        assert query.q == "ar"

    def test_valid_query_is_stripped(self):
        query = VenueSearchQuery(q="  arena ")
        assert query.q == "arena"

    def test_single_character_query_raises(self):
        with pytest.raises(ValidationError):
            VenueSearchQuery(q="a")

    def test_empty_query_raises(self):
        with pytest.raises(ValidationError):
            VenueSearchQuery(q="")

    def test_whitespace_only_query_raises(self):
        with pytest.raises(ValidationError):
            VenueSearchQuery(q="  ")
