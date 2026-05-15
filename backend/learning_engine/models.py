"""Pydantic models for interests, sources, and collected updates."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

Priority = Literal["low", "medium", "high"]
SourceType = Literal["feed", "page"]


class InterestSource(BaseModel):
    """A feed or page attached to a broader learning interest."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str | None = None
    label: str = "Source"
    type: SourceType
    url: str
    enabled: bool = True
    deleted_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("deletedAt", "deleted_at"),
        serialization_alias="deletedAt",
    )

    @field_validator("type", mode="before")
    @classmethod
    def normalize_source_type(cls, value: object) -> SourceType:
        source_type = str(value or "").strip().lower()
        if source_type in {"feed", "page"}:
            return cast(SourceType, source_type)
        raise ValueError("Source type must be feed or page")

    @field_validator("id", "deleted_at", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("label", mode="before")
    @classmethod
    def strip_label(cls, value: object) -> str:
        return str(value or "Source").strip() or "Source"

    @field_validator("url", mode="before")
    @classmethod
    def strip_url(cls, value: object) -> str:
        url = str(value or "").strip()
        if not url:
            raise ValueError("Source URL is required")
        return url


class Interest(BaseModel):
    """A general topic tracked by the Learning Engine."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str | None = None
    name: str = "Interest"
    description: str = ""
    priority: Priority = "medium"
    sources: list[InterestSource] = Field(default_factory=list)
    enabled: bool = True
    deleted_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("deletedAt", "deleted_at"),
        serialization_alias="deletedAt",
    )

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: object) -> Priority:
        priority = str(value or "medium").strip().lower()
        if priority in {"low", "medium", "high"}:
            return cast(Priority, priority)
        return "medium"

    @field_validator("id", "deleted_at", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("name", mode="before")
    @classmethod
    def strip_required_name(cls, value: object) -> str:
        return str(value or "Interest").strip() or "Interest"

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: object) -> str:
        return str(value or "").strip()


class InterestsPayload(BaseModel):
    interests: list[Interest] = Field(default_factory=list)


class FeedUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    summary: str | None = None
    published: str | None = None
    published_at: str | None = None
    matched_keywords: list[str] = Field(default_factory=list)


class Update(FeedUpdate):
    interest_id: str | None = None
    interest_name: str = "Interest"
    source_id: str | None = None
    source_label: str = "Source"
    source_url: str
    source_type: SourceType = "feed"


class CollectionError(BaseModel):
    interest_id: str | None = None
    interest_name: str = "Interest"
    source_id: str | None = None
    source_label: str = "Source"
    source_url: str
    source_type: SourceType
    error: str


class UpdatesResponse(BaseModel):
    sources_checked: int
    days: int | None = None
    since: str | None = None
    updates: list[Update] = Field(default_factory=list)
    errors: list[CollectionError] = Field(default_factory=list)
