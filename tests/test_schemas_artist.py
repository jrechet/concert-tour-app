"""
Unit tests for the `ArtistUpdate` Pydantic schema.
"""

import pytest
from pydantic import ValidationError

from src.schemas.artist import ArtistUpdate


class TestArtistUpdate:
    """Test cases for the `ArtistUpdate` schema."""

    def test_valid_name_is_accepted_and_stripped(self):
        update = ArtistUpdate(name="  Daft Punk  ")
        assert update.name == "Daft Punk"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            ArtistUpdate(name="")

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValidationError):
            ArtistUpdate(name="   ")

    def test_omitted_name_validates_and_exclude_unset_is_empty(self):
        update = ArtistUpdate()
        assert update.model_dump(exclude_unset=True) == {}

    def test_extra_field_is_ignored(self):
        update = ArtistUpdate(name="Daft Punk", bogus="nope")
        assert not hasattr(update, "bogus")
        assert update.model_dump() == {"name": "Daft Punk"}
