"""Tests for the pyproject.toml version-reader utility."""

from pathlib import Path

import pytest
import tomllib

from src.core.version import VersionNotFoundError, get_app_version

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_get_app_version_returns_string_matching_pyproject():
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    expected = data["project"]["version"]

    assert get_app_version() == expected
    assert isinstance(get_app_version(), str)


def test_get_app_version_raises_when_key_missing(tmp_path):
    bad_pyproject = tmp_path / "pyproject.toml"
    bad_pyproject.write_text('[project]\nname = "no-version-here"\n')

    with pytest.raises(VersionNotFoundError):
        get_app_version(bad_pyproject)


def test_get_app_version_raises_when_file_missing(tmp_path):
    missing_pyproject = tmp_path / "does-not-exist.toml"

    with pytest.raises(VersionNotFoundError):
        get_app_version(missing_pyproject)
