"""RSS and Atom feed parsing."""

from __future__ import annotations

from typing import Any, cast

import feedparser

from learning_engine.common.dates import parse_datetime
from learning_engine.common.text import keyword_matches, searchable_text, strip_markup
from learning_engine.domain.updates import SourceUpdate
from learning_engine.infrastructure.source_collectors.image_metadata import (
    FetchFn,
    fetch_provider_bytes,
    first_feed_image,
    html_image_url,
    normalized_image_url,
)


def _entry_value(entry: Any, key: str) -> str | None:
    raw_value = entry.get(key)
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    return value or None


def _entry_summary(entry: Any) -> str | None:
    summary = _entry_value(entry, "summary") or _entry_value(entry, "description")
    if summary:
        return strip_markup(summary)

    content_items = entry.get("content", [])
    if isinstance(content_items, list) and content_items:
        first_content = content_items[0]
        if isinstance(first_content, dict):
            content = strip_markup(first_content.get("value"))
            return content or None
    return None


def _entry_published(entry: Any) -> str | None:
    return _entry_value(entry, "published") or _entry_value(entry, "updated") or _entry_value(entry, "created")


def _image_url_from_mapping(value: Any, base_url: str) -> str | None:
    if not isinstance(value, dict):
        return None
    return normalized_image_url(cast(str | None, value.get("url") or value.get("href")), base_url)


def _is_image_media(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    medium = str(value.get("medium") or "").lower()
    media_type = str(value.get("type") or "").lower()
    return medium == "image" or media_type.startswith("image/")


def _first_image_url(values: Any, base_url: str) -> str | None:
    if not isinstance(values, list):
        return None
    for value in values:
        resolved = _image_url_from_mapping(value, base_url)
        if resolved is not None:
            return resolved
    return None


def _first_typed_image_url(values: Any, base_url: str) -> str | None:
    if not isinstance(values, list):
        return None
    return _first_image_url([value for value in values if _is_image_media(value)], base_url)


def _entry_image_url(entry: Any, base_url: str) -> str | None:
    return (
        _first_image_url(entry.get("media_thumbnail", []), base_url)
        or _first_typed_image_url(entry.get("media_content", []), base_url)
        or _first_typed_image_url(entry.get("links", []), base_url)
    )


def parse_feed_items(
    feed_bytes: bytes,
    watch_keywords: list[str],
    ignore_keywords: list[str],
) -> list[SourceUpdate]:
    """Parse RSS/Atom bytes into normalized feed updates."""

    parsed_feed = feedparser.parse(feed_bytes)
    entries = cast(list[Any], parsed_feed.get("entries", []))
    updates: list[SourceUpdate] = []

    for entry in entries:
        title = strip_markup(_entry_value(entry, "title"))
        url = _entry_value(entry, "link")
        summary = _entry_summary(entry)
        image_url = _entry_image_url(entry, url or "")
        published = _entry_published(entry)
        matched = keyword_matches(searchable_text(title, summary, url), watch_keywords)
        ignored = keyword_matches(searchable_text(title, summary, url), ignore_keywords)
        if ignored or (watch_keywords and not matched):
            continue

        updates.append(
            SourceUpdate(
                title=title,
                url=url,
                summary=summary,
                image_url=image_url,
                published=parse_datetime(published),
                published_at=parse_datetime(published),
                matched_keywords=matched,
            )
        )

    return updates


async def resolve_feed_image(source_url: str, fetch: FetchFn) -> str | None:
    feed_bytes = await fetch_provider_bytes(source_url, fetch, "Feed")
    parsed = feedparser.parse(feed_bytes)
    feed = parsed.get("feed", {})
    if isinstance(feed, dict):
        resolved = first_feed_image(cast(dict[str, Any], feed), source_url)
        if resolved is not None:
            return resolved
    return html_image_url(feed_bytes, source_url)
