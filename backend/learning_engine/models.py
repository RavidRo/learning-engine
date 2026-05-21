"""Pydantic models for interests, sources, and collected updates."""

from __future__ import annotations

from typing import Literal, TypeAlias, cast

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

Priority = Literal["low", "medium", "high"]
SourceType = Literal["feed", "page", "youtube_channel", "twitter_account", "spotify_podcast"]
SOURCE_TYPES: tuple[SourceType, ...] = (
    "feed",
    "page",
    "youtube_channel",
    "twitter_account",
    "spotify_podcast",
)
_SOURCE_TYPE_ALIASES: dict[str, SourceType] = {
    "feed": "feed",
    "rss": "feed",
    "rss_feed": "feed",
    "page": "page",
    "webpage": "page",
    "web_page": "page",
    "youtube": "youtube_channel",
    "youtube_channel": "youtube_channel",
    "youtube_channels": "youtube_channel",
    "twitter": "twitter_account",
    "twitter_account": "twitter_account",
    "twitter_accounts": "twitter_account",
    "x": "twitter_account",
    "x_account": "twitter_account",
    "spotify": "spotify_podcast",
    "spotify_podcast": "spotify_podcast",
    "spotify_podcasts": "spotify_podcast",
}


class InterestSource(BaseModel):
    """A feed or page attached to a broader learning interest."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str | None = None
    label: str = "Source"
    type: SourceType
    url: str
    image_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("imageUrl", "image_url"),
        serialization_alias="imageUrl",
    )
    ignore_keywords: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ignoreKeywords", "ignore_keywords"),
        serialization_alias="ignoreKeywords",
    )
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
        normalized = source_type.replace("-", "_").replace(" ", "_")
        if normalized in _SOURCE_TYPE_ALIASES:
            return _SOURCE_TYPE_ALIASES[normalized]
        raise ValueError(f"Source type must be one of: {', '.join(SOURCE_TYPES)}")

    @field_validator("id", "deleted_at", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_image_url(cls, value: object) -> str | None:
        if value is None:
            return None
        return str(value).strip()

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

    @field_validator("ignore_keywords", mode="before")
    @classmethod
    def normalize_ignore_keywords(cls, value: object) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            candidates = value.split(",")
        elif isinstance(value, list):
            candidates = value
        else:
            return []

        return [keyword for item in candidates if (keyword := str(item).strip())]


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


class CollectedUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    summary: str | None = None
    published: str | None = None
    published_at: str | None = None
    matched_keywords: list[str] = Field(default_factory=list)


FeedUpdate: TypeAlias = CollectedUpdate


class Update(CollectedUpdate):
    interest_id: str | None = None
    interest_name: str = "Interest"
    source_id: str | None = None
    source_label: str = "Source"
    source_image_url: str | None = None
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
