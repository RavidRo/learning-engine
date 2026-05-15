"""Update collection orchestration across interest sources."""

from __future__ import annotations

import urllib.error
from collections.abc import Callable
from datetime import datetime

from learning_engine.dates import days_cutoff, format_datetime, within_window
from learning_engine.fetching import fetch_url
from learning_engine.models import (
    CollectionError,
    FeedUpdate,
    Interest,
    InterestSource,
    InterestsPayload,
    Update,
    UpdatesResponse,
)
from learning_engine.sources.feed import parse_feed_items
from learning_engine.sources.page import parse_page_items

FetchFn = Callable[[str], bytes]
ParseFn = Callable[[bytes, list[str], list[str]], list[FeedUpdate]]
__all__ = ["collect_updates", "dedupe_updates", "parse_feed_items", "parse_page_items"]


def _dedupe_part(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.lower() or None


def _sort_key(update: Update) -> tuple[bool, str | None]:
    published = update.published_at or update.published
    return published is not None, published


def dedupe_updates(updates: list[Update]) -> list[Update]:
    deduped: list[Update] = []
    seen: set[tuple[str | None, str | None]] = set()
    for update in updates:
        key = (_dedupe_part(update.url), _dedupe_part(update.title))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(update)
    return deduped


def _parser_for_source(source: InterestSource) -> ParseFn:
    if source.type == "feed":
        return parse_feed_items

    page_url = source.url

    def parse_page_source(page_bytes: bytes, watch_keywords: list[str], ignore_keywords: list[str]) -> list[FeedUpdate]:
        return parse_page_items(page_bytes, page_url, watch_keywords, ignore_keywords)

    return parse_page_source


def _enrich_updates(
    interest: Interest,
    source: InterestSource,
    source_updates: list[FeedUpdate],
    cutoff: datetime | None,
) -> list[Update]:
    return [
        Update(
            interest_id=interest.id,
            interest_name=interest.name,
            source_id=source.id,
            source_label=source.label,
            source_url=source.url,
            source_type=source.type,
            **source_update.model_dump(),
        )
        for source_update in source_updates
        if within_window(source_update.published_at or source_update.published, cutoff)
    ]


def _collect_from_source(
    interest: Interest,
    source: InterestSource,
    cutoff: datetime | None,
    fetch: FetchFn,
) -> tuple[list[Update], CollectionError | None]:
    parser = _parser_for_source(source)
    try:
        fetched = fetch(source.url)
        source_updates = parser(fetched, [], [])
    except (OSError, UnicodeError, urllib.error.URLError, ValueError) as exc:
        return [], CollectionError(
            interest_id=interest.id,
            interest_name=interest.name,
            source_id=source.id,
            source_label=source.label,
            source_url=source.url,
            source_type=source.type,
            error=str(exc),
        )

    return _enrich_updates(interest, source, source_updates, cutoff), None


def collect_updates(
    payload: InterestsPayload,
    days: int | None = None,
    now: datetime | None = None,
    fetch: FetchFn = fetch_url,
) -> UpdatesResponse:
    updates: list[Update] = []
    errors: list[CollectionError] = []
    checked = 0
    cutoff = days_cutoff(days, now)

    for interest in payload.interests:
        if interest.deleted_at is not None or not interest.enabled:
            continue

        for source in interest.sources:
            if source.deleted_at is not None or not source.enabled:
                continue

            checked += 1
            source_updates, error = _collect_from_source(interest, source, cutoff, fetch)
            updates.extend(source_updates)
            if error is not None:
                errors.append(error)

    updates = dedupe_updates(updates)
    updates.sort(key=_sort_key, reverse=True)
    return UpdatesResponse(
        sources_checked=checked,
        days=days,
        since=format_datetime(cutoff),
        updates=updates,
        errors=errors,
    )
