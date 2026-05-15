"""Technology update collection orchestration."""

from __future__ import annotations

import urllib.error
from collections.abc import Callable
from datetime import datetime

from learning_engine.dates import days_cutoff, format_datetime, within_window
from learning_engine.fetching import fetch_url
from learning_engine.models import (
    CollectionError,
    FeedUpdate,
    InterestsPayload,
    SourceType,
    TechnologyInterest,
    TechnologyUpdate,
    TechnologyUpdatesResponse,
)
from learning_engine.sources.feed import parse_feed_items
from learning_engine.sources.page import parse_page_items

FetchFn = Callable[[str], bytes]
ParseFn = Callable[[bytes, list[str], list[str]], list[FeedUpdate]]
__all__ = ["collect_technology_updates", "dedupe_updates", "parse_feed_items", "parse_page_items"]


def _dedupe_part(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.lower() or None


def _sort_key(update: TechnologyUpdate) -> tuple[bool, str | None]:
    published = update.published_at or update.published
    return published is not None, published


def dedupe_updates(updates: list[TechnologyUpdate]) -> list[TechnologyUpdate]:
    deduped: list[TechnologyUpdate] = []
    seen: set[tuple[str | None, str | None]] = set()
    for update in updates:
        key = (_dedupe_part(update.url), _dedupe_part(update.title))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(update)
    return deduped


def _source_for_interest(interest: TechnologyInterest) -> tuple[str, SourceType] | None:
    if interest.official_feed_url:
        return interest.official_feed_url, "feed"
    if interest.official_site_url:
        return interest.official_site_url, "page"
    return None


def _parser_for_source(source_type: SourceType, page_url: str | None) -> ParseFn:
    if source_type == "feed":
        return parse_feed_items

    def parse_page_source(page_bytes: bytes, watch_keywords: list[str], ignore_keywords: list[str]) -> list[FeedUpdate]:
        if page_url is None:
            return []
        return parse_page_items(page_bytes, page_url, watch_keywords, ignore_keywords)

    return parse_page_source


def _enrich_updates(
    interest: TechnologyInterest,
    source_url: str,
    source_type: SourceType,
    source_updates: list[FeedUpdate],
    cutoff: datetime | None,
) -> list[TechnologyUpdate]:
    return [
        TechnologyUpdate(
            interest_id=interest.id,
            interest_name=interest.name,
            feed_url=interest.official_feed_url,
            source_url=source_url,
            source_type=source_type,
            **source_update.model_dump(),
        )
        for source_update in source_updates
        if within_window(source_update.published_at or source_update.published, cutoff)
    ]


def _collect_from_interest(
    interest: TechnologyInterest,
    cutoff: datetime | None,
    fetch: FetchFn,
) -> tuple[list[TechnologyUpdate], CollectionError | None]:
    source = _source_for_interest(interest)
    if source is None:
        return [], None

    source_url, source_type = source
    try:
        fetched = fetch(source_url)
        parser = _parser_for_source(source_type, interest.official_site_url)
        source_updates = parser(fetched, interest.watch_keywords, interest.ignore_keywords)
    except (OSError, UnicodeError, urllib.error.URLError, ValueError) as exc:
        return [], CollectionError(interest_id=interest.id, interest_name=interest.name, error=str(exc))

    return _enrich_updates(interest, source_url, source_type, source_updates, cutoff), None


def collect_technology_updates(
    payload: InterestsPayload,
    days: int | None = None,
    now: datetime | None = None,
    fetch: FetchFn = fetch_url,
) -> TechnologyUpdatesResponse:
    updates: list[TechnologyUpdate] = []
    errors: list[CollectionError] = []
    checked = 0
    cutoff = days_cutoff(days, now)

    for interest in payload.interests:
        if not interest.enabled:
            continue

        if _source_for_interest(interest) is None:
            continue

        checked += 1
        source_updates, error = _collect_from_interest(interest, cutoff, fetch)
        updates.extend(source_updates)
        if error is not None:
            errors.append(error)

    updates = dedupe_updates(updates)
    updates.sort(key=_sort_key, reverse=True)
    return TechnologyUpdatesResponse(
        interests_checked=checked,
        days=days,
        since=format_datetime(cutoff),
        updates=updates,
        errors=errors,
    )
