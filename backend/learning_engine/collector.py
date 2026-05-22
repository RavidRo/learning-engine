"""Update collection orchestration across interest sources."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Mapping, MutableMapping
from dataclasses import dataclass

import httpx

from learning_engine.dates import format_datetime, parse_datetime
from learning_engine.fetching import fetch_json as default_fetch_json
from learning_engine.fetching import fetch_url
from learning_engine.models import (
    CollectedUpdate,
    CollectionError,
    Interest,
    InterestSource,
    InterestsPayload,
    Update,
    UpdatesResponse,
)
from learning_engine.sources.feed import parse_feed_items
from learning_engine.sources.page import parse_page_items
from learning_engine.sources.spotify import collect_spotify_podcast
from learning_engine.sources.twitter import collect_twitter_account
from learning_engine.sources.youtube import collect_youtube_channel
from learning_engine.text import keyword_matches, searchable_text
from learning_engine.timeframe import Timeframe

FetchFn = Callable[[str], Awaitable[bytes]]
JsonFetchFn = Callable[[str, Mapping[str, str]], Awaitable[dict[str, object]]]
SourceUpdatesCacheKey = tuple[str, str, tuple[str, ...]]
SourceUpdatesCacheValue = tuple[list[CollectedUpdate], str | None]
SourceUpdatesCache = MutableMapping[SourceUpdatesCacheKey, SourceUpdatesCacheValue]
__all__ = [
    "SourceUpdatesCache",
    "SourceUpdatesCacheKey",
    "SourceUpdatesCacheValue",
    "collect_updates",
    "dedupe_updates",
    "parse_feed_items",
    "parse_page_items",
]


@dataclass(frozen=True, slots=True)
class _SourceCollectionContext:
    timeframe: Timeframe
    fetch: FetchFn
    fetch_json: JsonFetchFn
    source_updates_cache: SourceUpdatesCache | None


def _dedupe_part(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.lower() or None


def _sort_key(update: Update) -> tuple[bool, str | None]:
    published = update.published_at or update.published
    return published is not None, published


def _within_timeframe(value: str | None, timeframe: Timeframe) -> bool:
    parsed = parse_datetime(value)
    return parsed is not None and parsed in timeframe


def dedupe_updates(updates: list[Update]) -> list[Update]:
    deduped: list[Update] = []
    seen: set[tuple[str | None, str | None]] = set()
    for update in updates:
        key = (_dedupe_part(update.url), _dedupe_part(update.title))
        if key == (None, None):
            deduped.append(update)
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(update)
    return deduped


async def _collect_source_updates(
    source: InterestSource,
    fetch: FetchFn,
    fetch_json: JsonFetchFn,
) -> list[CollectedUpdate]:
    if source.type == "feed":
        return parse_feed_items(await fetch(source.url), watch_keywords=[], ignore_keywords=source.ignore_keywords)

    if source.type == "page":
        return parse_page_items(
            await fetch(source.url),
            source.url,
            watch_keywords=[],
            ignore_keywords=source.ignore_keywords,
        )

    if source.type == "youtube_channel":
        return await collect_youtube_channel(source.url, fetch)

    if source.type == "twitter_account":
        return await collect_twitter_account(source.url, fetch_json)

    return await collect_spotify_podcast(source.url, fetch_json)


def _enrich_updates(
    interest: Interest,
    source: InterestSource,
    source_updates: list[CollectedUpdate],
    timeframe: Timeframe,
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
        if _within_timeframe(source_update.published_at or source_update.published, timeframe)
        and not keyword_matches(
            searchable_text(source_update.title, source_update.summary, source_update.url),
            source.ignore_keywords,
        )
    ]


def _source_updates_cache_key(source: InterestSource) -> SourceUpdatesCacheKey:
    return (source.type, source.url, tuple(source.ignore_keywords))


def _collection_error(interest: Interest, source: InterestSource, error: str) -> CollectionError:
    return CollectionError(
        interest_id=interest.id,
        interest_name=interest.name,
        source_id=source.id,
        source_label=source.label,
        source_url=source.url,
        source_type=source.type,
        error=error,
    )


async def _get_source_updates(
    interest: Interest,
    source: InterestSource,
    fetch: FetchFn,
    fetch_json: JsonFetchFn,
    source_updates_cache: SourceUpdatesCache | None,
) -> SourceUpdatesCacheValue:
    cache_key = _source_updates_cache_key(source)
    if source_updates_cache is not None and cache_key in source_updates_cache:
        updates, error = source_updates_cache[cache_key]
        return [update.model_copy(deep=True) for update in updates], error

    try:
        result: SourceUpdatesCacheValue = await _collect_source_updates(source, fetch, fetch_json), None
    except (
        OSError,
        UnicodeError,
        httpx.HTTPError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        result = [], str(exc)

    if source_updates_cache is not None:
        updates, error = result
        source_updates_cache[cache_key] = ([update.model_copy(deep=True) for update in updates], error)
    return result


async def _collect_from_source(
    interest: Interest,
    source: InterestSource,
    context: _SourceCollectionContext,
) -> tuple[list[Update], CollectionError | None]:
    source_updates, error = await _get_source_updates(
        interest,
        source,
        context.fetch,
        context.fetch_json,
        context.source_updates_cache,
    )
    collection_error = _collection_error(interest, source, error) if error is not None else None
    return _enrich_updates(interest, source, source_updates, context.timeframe), collection_error


def _enabled_sources(payload: InterestsPayload) -> Iterable[tuple[Interest, InterestSource]]:
    for interest in payload.interests:
        if interest.deleted_at is not None or not interest.enabled:
            continue

        for source in interest.sources:
            if source.deleted_at is not None or not source.enabled:
                continue

            yield interest, source


def _updates_response(
    source_results: list[tuple[list[Update], CollectionError | None]],
    checked: int,
    timeframe: Timeframe,
) -> UpdatesResponse:
    updates: list[Update] = []
    errors: list[CollectionError] = []

    for source_updates, error in source_results:
        updates.extend(source_updates)
        if error is not None:
            errors.append(error)

    updates = dedupe_updates(updates)
    updates.sort(key=_sort_key, reverse=True)
    return UpdatesResponse(
        sources_checked=checked,
        since=format_datetime(timeframe.start),
        updates=updates,
        errors=errors,
    )


async def collect_updates(
    payload: InterestsPayload,
    timeframe: Timeframe,
    fetch: FetchFn = fetch_url,
    fetch_json: JsonFetchFn = default_fetch_json,
    source_updates_cache: SourceUpdatesCache | None = None,
) -> UpdatesResponse:
    sources = list(_enabled_sources(payload))
    context = _SourceCollectionContext(
        timeframe=timeframe,
        fetch=fetch,
        fetch_json=fetch_json,
        source_updates_cache=source_updates_cache,
    )
    source_results: list[tuple[list[Update], CollectionError | None]] = list(
        await asyncio.gather(*(_collect_from_source(interest, source, context) for interest, source in sources))
    )
    return _updates_response(source_results, checked=len(sources), timeframe=timeframe)
