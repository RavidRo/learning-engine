"""Pydantic models for interests and collected updates."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

InterestType = Literal["technology"]
Priority = Literal["low", "medium", "high"]
SourceType = Literal["feed", "page"]


def _clean_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


class TechnologyInterest(BaseModel):
    """A technology topic tracked from official sources."""

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = "Technology"
    type: InterestType = "technology"
    priority: Priority = "medium"
    official_site_url: str = ""
    official_feed_url: str = ""
    watch_keywords: list[str] = Field(default_factory=list)
    ignore_keywords: list[str] = Field(default_factory=list)
    notes: str = ""
    enabled: bool = True

    @field_validator("type", mode="before")
    @classmethod
    def coerce_interest_type(cls, _value: object) -> InterestType:
        return "technology"

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: object) -> Priority:
        priority = str(value or "medium").strip().lower()
        if priority in {"low", "medium", "high"}:
            return cast(Priority, priority)
        return "medium"

    @field_validator("id", "name", "official_site_url", "official_feed_url", "notes", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> str:
        return str(value or "").strip()

    @field_validator("watch_keywords", "ignore_keywords", mode="before")
    @classmethod
    def normalize_keywords(cls, value: object) -> list[str]:
        return _clean_string_list(value)


class InterestsPayload(BaseModel):
    interests: list[TechnologyInterest] = Field(default_factory=list)


class FeedUpdate(BaseModel):
    title: str = ""
    url: str = ""
    summary: str = ""
    published: str = ""
    published_at: str = ""
    matched_keywords: list[str] = Field(default_factory=list)


class TechnologyUpdate(FeedUpdate):
    interest_id: str = ""
    interest_name: str = "Technology"
    feed_url: str = ""
    source_url: str = ""
    source_type: SourceType = "feed"


class CollectionError(BaseModel):
    interest_id: str = ""
    interest_name: str = ""
    error: str


class TechnologyUpdatesResponse(BaseModel):
    interests_checked: int
    days: int | None = None
    since: str = ""
    updates: list[TechnologyUpdate] = Field(default_factory=list)
    errors: list[CollectionError] = Field(default_factory=list)
