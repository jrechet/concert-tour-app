"""
Pydantic schema for the concert headliner lookup response.
"""

from pydantic import BaseModel, ConfigDict, Field


class HeadlinerResponse(BaseModel):
    """Schema for a concert's headlining act: the lineup entry with the
    greatest `set_order`.

    `name`/`set_position` are this response's own stable field names,
    distinct from the underlying `LineupEntry.artist_name`/`set_order`
    columns they are sourced from via `validation_alias`.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"name": "The Headliners", "set_position": 3}},
    )

    name: str = Field(..., validation_alias="artist_name", description="Headlining act's name")
    set_position: int = Field(
        ..., validation_alias="set_order", description="Headliner's running-order position"
    )
