"""Application response models for update collection use cases."""

from __future__ import annotations

from pydantic import BaseModel, Field

from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import Update


class CollectionError(BaseModel):
    interest_id: str | None
    interest_name: str
    source_id: str | None
    source_label: str
    source_url: str
    source_type: SourceType
    error: str


class UpdatesResponse(BaseModel):
    sources_checked: int
    since: str | None = None
    updates: list[Update] = Field(default_factory=list)
    errors: list[CollectionError] = Field(default_factory=list)
