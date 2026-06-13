"""Update domain models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from learning_engine.common.dates import parse_datetime
from learning_engine.domain.source_types import SourceType


class SourceUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    summary: str | None = None
    image_url: str | None = None
    published: datetime | None = None
    published_at: datetime | None = None
    matched_keywords: list[str] = Field(default_factory=list)

    @field_validator("published", "published_at", mode="before")
    @classmethod
    def parse_update_datetime(cls, value: object) -> datetime | None:
        if value is None or isinstance(value, datetime):
            return value
        return parse_datetime(str(value))


class SourceInterest(BaseModel):
    interest_id: str | None
    interest_name: str
    source_id: str | None
    source_label: str
    source_image_url: str | None = None
    source_url: str
    source_type: SourceType


class Update(SourceUpdate):
    source_interest: SourceInterest
