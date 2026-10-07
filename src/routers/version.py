"""App version endpoint."""

from fastapi import APIRouter, HTTPException

from ..core.version import VersionNotFoundError, get_app_version

router = APIRouter(prefix="/api/v1", tags=["version"])


@router.get("/version")
def get_version():
    """Retrieve the app version declared in pyproject.toml."""
    try:
        version = get_app_version()
    except VersionNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"version": version}
