"""
Unit tests for the TourStatus enum.
"""

from src.models.tour import Tour
from src.schemas.tour import TourStatus
from src.schemas import TourStatus as ExportedTourStatus


class TestTourStatus:
    """Test cases for the TourStatus enum."""

    def test_values_match_model_default(self):
        assert Tour.status.default.arg == TourStatus.PLANNED.value

    def test_is_str_enum_with_expected_members(self):
        assert set(TourStatus) == {
            TourStatus.PLANNED,
            TourStatus.ACTIVE,
            TourStatus.COMPLETED,
        }
        assert TourStatus.PLANNED.value == "planned"
        assert TourStatus.ACTIVE.value == "active"
        assert TourStatus.COMPLETED.value == "completed"
        assert isinstance(TourStatus.PLANNED, str)

    def test_importable_from_schemas_package(self):
        assert ExportedTourStatus is TourStatus
