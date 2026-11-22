"""Unit tests for the tour rename schema (`TourRename`) and the matching
`Tour` model-level name validation.
"""

import pytest
from pydantic import ValidationError

from src.models.tour import TOUR_NAME_MAX_LENGTH, Tour
from src.schemas.tour import TourRename


class TestTourRenameSchema:
    """Test cases for the `TourRename` schema."""

    def test_valid_name_accepted(self):
        rename = TourRename(name="Summer Tour")
        assert rename.name == "Summer Tour"

    def test_name_is_stripped(self):
        rename = TourRename(name="  Summer Tour  ")
        assert rename.name == "Summer Tour"

    def test_name_at_max_length_accepted(self):
        name = "A" * TOUR_NAME_MAX_LENGTH
        rename = TourRename(name=name)
        assert rename.name == name

    def test_name_over_max_length_rejected(self):
        with pytest.raises(ValidationError):
            TourRename(name="A" * (TOUR_NAME_MAX_LENGTH + 1))

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            TourRename(name="")

    def test_whitespace_only_name_rejected(self):
        with pytest.raises(ValidationError):
            TourRename(name="   ")

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError):
            TourRename()


class TestTourModelNameValidation:
    """Test cases for the `Tour` model's name validator."""

    def test_model_rejects_invalid_name_on_assignment(self):
        tour = Tour(
            name="Valid Tour",
            artist="The Beatles",
            start_date="2024-06-01",
            end_date="2024-12-31",
        )

        with pytest.raises(ValueError):
            tour.name = ""

        with pytest.raises(ValueError):
            tour.name = "   "

        with pytest.raises(ValueError):
            tour.name = "A" * (TOUR_NAME_MAX_LENGTH + 1)

        with pytest.raises(ValueError):
            Tour(
                name="",
                artist="The Beatles",
                start_date="2024-06-01",
                end_date="2024-12-31",
            )
