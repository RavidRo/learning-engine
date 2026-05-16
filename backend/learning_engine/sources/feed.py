"""RSS and Atom feed parsing."""

from __future__ import annotations

from typing import Any, cast

import feedparser

from learning_engine.dates import format_datetime, parse_datetime
from learning_engine.models import FeedUpdate
from learning_engine.text import keyword_matches, searchable_text, strip_markup


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


def parse_feed_items(
    feed_bytes: bytes,
    watch_keywords: list[str],
    ignore_keywords: list[str],
) -> list[FeedUpdate]:
    """Parse RSS/Atom bytes into normalized feed updates."""

    parsed_feed = feedparser.parse(feed_bytes)
    entries = cast(list[Any], parsed_feed.get("entries", []))
    updates: list[FeedUpdate] = []

    for entry in entries:
        title = strip_markup(_entry_value(entry, "title"))
        url = _entry_value(entry, "link")
        summary = _entry_summary(entry)
        published = _entry_published(entry)
        matched = keyword_matches(searchable_text(title, summary, url), watch_keywords)
        ignored = keyword_matches(searchable_text(title, summary, url), ignore_keywords)
        if ignored or (watch_keywords and not matched):
            continue

        updates.append(
            FeedUpdate(
                title=title,
                url=url,
                summary=summary,
                published=published,
                published_at=format_datetime(parse_datetime(published)),
                matched_keywords=matched,
            )
        )

    return updates
