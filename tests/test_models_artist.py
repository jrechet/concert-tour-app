"""
Unit tests for model-level name validation on `Artist`.
"""

import pytest

from src.models import Artist


class TestArtistNameValidation:
    """Test cases for `Artist.name` validation."""

    def test_valid_name_is_accepted(self):
        artist = Artist(name="Daft Punk")
        assert artist.name == "Daft Punk"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Artist(name="")

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValueError):
            Artist(name="   ")

    def test_assigning_empty_name_after_construction_raises(self):
        artist = Artist(name="Daft Punk")
        with pytest.raises(ValueError):
            artist.name = ""
