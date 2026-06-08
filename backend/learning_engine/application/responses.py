"""Application response models for update collection use cases."""

from __future__ import annotations

from pydantic import BaseModel, Field

from learning_engine.domain.interests import Interest, InterestSource
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

    @classmethod
    def from_source(cls, interest: Interest, source: InterestSource, error: str) -> CollectionError:
        return cls(
            interest_id=interest.id,
            interest_name=interest.name,
            source_id=source.id,
            source_label=source.label,
            source_url=source.url,
            source_type=source.type,
            error=error,
        )


class UpdatesResponse(BaseModel):
    sources_checked: int
    since: str | None = None
    updates: list[Update] = Field(default_factory=list)
    errors: list[CollectionError] = Field(default_factory=list)
