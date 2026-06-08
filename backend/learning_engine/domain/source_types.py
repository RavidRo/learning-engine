"""Supported source type values."""

from __future__ import annotations

from typing import Literal

SourceType = Literal["feed", "page", "youtube_channel", "twitter_account", "spotify_podcast"]
SOURCE_TYPES: tuple[SourceType, ...] = (
    "feed",
    "page",
    "youtube_channel",
    "twitter_account",
    "spotify_podcast",
)


def normalize_source_type(value: object) -> SourceType:
    source_type = str(value or "").strip().lower()
    if source_type in SOURCE_TYPES:
        return source_type
    raise ValueError(f"Source type must be one of: {', '.join(SOURCE_TYPES)}")
