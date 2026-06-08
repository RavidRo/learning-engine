"""Presentation schemas for FastAPI-only payloads."""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from learning_engine.domain.interests import InterestSource
from learning_engine.domain.source_types import SourceType


class SourceImageRequest(BaseModel):
    """Source fields needed to resolve derived image metadata."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source_type: SourceType = Field(
        validation_alias=AliasChoices("sourceType", "source_type", "type"),
        serialization_alias="sourceType",
    )
    url: str

    @field_validator("source_type", mode="before")
    @classmethod
    def normalize_source_type(cls, value: object) -> SourceType:
        return InterestSource.normalize_source_type(value)

    @field_validator("url", mode="before")
    @classmethod
    def strip_url(cls, value: object) -> str:
        return InterestSource.strip_url(value)


class SourceImageResponse(BaseModel):
    """Dynamically resolved source image metadata."""

    image_url: str | None = Field(default=None, serialization_alias="imageUrl")
