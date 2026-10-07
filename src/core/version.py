"""Reads the application version from pyproject.toml.

Single source of truth for the app version, so routers/services (and the
FastAPI app itself) don't hardcode a version string that can drift from
pyproject.toml.
"""

import tomllib
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"


class VersionNotFoundError(Exception):
    """Raised when pyproject.toml is missing, or has no version declared."""


def get_app_version(pyproject_path: Path = PYPROJECT_PATH) -> str:
    """Return the version declared in pyproject.toml.

    Looks under [project].version first, falling back to
    [tool.poetry].version. Raises VersionNotFoundError if the file is
    missing or neither location declares a version.
    """
    if not pyproject_path.is_file():
        raise VersionNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    version = data.get("project", {}).get("version") or data.get("tool", {}).get(
        "poetry", {}
    ).get("version")

    if not version:
        raise VersionNotFoundError(
            f"No version found under [project] or [tool.poetry] in {pyproject_path}"
        )

    return version
