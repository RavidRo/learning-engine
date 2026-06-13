"""Update collection orchestration across interest sources."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, MutableMapping
from dataclasses import dataclass
from datetime import datetime

from learning_engine.application.ports import SourceImageProvider, SourceUpdateCollector
from learning_engine.application.resolve_source_image import (
    SourceImageConfigurationError,
    SourceImageProviderError,
    SourceImageProviderUnavailableError,
    resolve_source_image,
)
from learning_engine.application.responses import CollectionError, UpdatesResponse
from learning_engine.common.dates import format_datetime
from learning_engine.common.text import keyword_matches, searchable_text
from learning_engine.common.timeframe import Timeframe
from learning_engine.domain.interests import Interest, Interests, InterestSource
from learning_engine.domain.updates import SourceInterest, SourceUpdate, Update

SourceUpdatesCacheKey = tuple[str, str, tuple[str, ...], str | None]
SourceUpdatesCacheValue = list[SourceUpdate]
SourceUpdatesCache = MutableMapping[SourceUpdatesCacheKey, SourceUpdatesCacheValue]
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SourceUpdatesCacheOptions:
    cache: SourceUpdatesCache
    scope: str | None = None


@dataclass(frozen=True, slots=True)
class CollectUpdatesDependencies:
    source_update_collector: SourceUpdateCollector
    source_image_provider: SourceImageProvider


__all__ = [
    "CollectUpdatesDependencies",
    "SourceUpdatesCache",
    "SourceUpdatesCacheKey",
    "SourceUpdatesCacheOptions",
    "SourceUpdatesCacheValue",
    "collect_updates",
    "dedupe_updates",
]


@dataclass(frozen=True, slots=True)
class _SourceCollectionContext:
    timeframe: Timeframe
    source_update_collector: SourceUpdateCollector
    source_image_provider: SourceImageProvider
    source_updates_cache: SourceUpdatesCache
    source_updates_cache_scope: str | None


async def _source_image_url(source: InterestSource, context: _SourceCollectionContext) -> str | None:
    if source.image_url:
        return source.image_url
    try:
        image_url = await resolve_source_image(
            source.type,
            source.url,
            context.source_image_provider,
        )
    except SourceImageConfigurationError as exc:
        logger.info(
            "Source image configuration is unavailable",
            extra={
                "source_type": source.type,
                "source_url": source.url,
                "reason": str(exc),
            },
        )
        return None
    except SourceImageProviderError as exc:
        log_message = (
            "Source image provider is unavailable"
            if isinstance(exc, SourceImageProviderUnavailableError)
            else "Source image provider metadata is unavailable"
        )
        logger.info(
            log_message,
            extra={
                "source_type": source.type,
                "source_url": source.url,
                "reason": str(exc),
            },
        )
        return None
    except Exception:
        logger.exception(
            "Source image resolver failed during update collection",
            extra={"source_type": source.type, "source_url": source.url},
        )
        return None

    if image_url is None:
        logger.debug(
            "Source image provider metadata did not include an image",
            extra={"source_type": source.type, "source_url": source.url},
        )
    return image_url


def _dedupe_part(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.lower() or None


def _sort_key(update: Update) -> tuple[bool, str | None]:
    published = update.published_at or update.published
    return published is not None, format_datetime(published)


def _within_timeframe(value: datetime | None, timeframe: Timeframe) -> bool:
    return value is not None and value in timeframe


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


def _enrich_updates(
    interest: Interest,
    source: InterestSource,
    source_updates: list[SourceUpdate],
    timeframe: Timeframe,
    source_image_url: str | None,
) -> list[Update]:
    return [
        Update(
            source_interest=SourceInterest(
                interest_id=interest.id,
                interest_name=interest.name,
                source_id=source.id,
                source_label=source.label,
                source_image_url=source_image_url,
                source_url=source.url,
                source_type=source.type,
            ),
            **source_update.model_dump(),
        )
        for source_update in source_updates
        if _within_timeframe(source_update.published_at or source_update.published, timeframe)
        and not keyword_matches(
            searchable_text(source_update.title, source_update.summary, source_update.url),
            source.ignore_keywords,
        )
    ]


def _source_updates_cache_key(source: InterestSource, cache_scope: str | None) -> SourceUpdatesCacheKey:
    return (source.type, source.url, tuple(source.ignore_keywords), cache_scope)


def _copy_source_updates_cache_value(
    value: SourceUpdatesCacheValue,
) -> SourceUpdatesCacheValue:
    return [update.model_copy(deep=True) for update in value]


async def _get_source_updates(
    source: InterestSource,
    context: _SourceCollectionContext,
) -> SourceUpdatesCacheValue:
    source_updates_cache = context.source_updates_cache
    cache_key = _source_updates_cache_key(source, context.source_updates_cache_scope)

    if cache_key in source_updates_cache:
        return _copy_source_updates_cache_value(source_updates_cache[cache_key])

    source_updates = await context.source_update_collector.collect_source_updates(source)
    source_updates_cache[cache_key] = _copy_source_updates_cache_value(source_updates)
    return source_updates


async def _collect_from_source(
    interest: Interest,
    source: InterestSource,
    context: _SourceCollectionContext,
) -> list[Update]:
    source_updates = await _get_source_updates(source, context)
    source_image_url = await _source_image_url(source, context) if source_updates else source.image_url
    return _enrich_updates(interest, source, source_updates, context.timeframe, source_image_url)


def _enabled_sources(
    interests: Interests,
) -> Iterable[tuple[Interest, InterestSource]]:
    for interest in interests.interests:
        if interest.deleted_at is not None or not interest.enabled:
            continue

        for source in interest.sources:
            if source.deleted_at is not None or not source.enabled:
                continue

            yield interest, source


def _updates_response(
    source_results: list[list[Update]],
    errors: list[CollectionError],
    checked: int,
    timeframe: Timeframe,
) -> UpdatesResponse:
    updates: list[Update] = []

    for source_updates in source_results:
        updates.extend(source_updates)

    updates = dedupe_updates(updates)
    updates.sort(key=_sort_key, reverse=True)
    return UpdatesResponse(
        sources_checked=checked,
        since=format_datetime(timeframe.start),
        updates=updates,
        errors=errors,
    )


def _collection_error(
    interest: Interest,
    source: InterestSource,
    exc: Exception,
) -> CollectionError:
    return CollectionError(
        interest_id=interest.id,
        interest_name=interest.name,
        source_id=source.id,
        source_label=source.label,
        source_url=source.url,
        source_type=source.type,
        error=str(exc) or exc.__class__.__name__,
    )


async def collect_updates(
    interests: Interests,
    timeframe: Timeframe,
    dependencies: CollectUpdatesDependencies,
    source_updates_cache: SourceUpdatesCacheOptions,
) -> UpdatesResponse:
    sources = list(_enabled_sources(interests))
    context = _SourceCollectionContext(
        timeframe=timeframe,
        source_update_collector=dependencies.source_update_collector,
        source_image_provider=dependencies.source_image_provider,
        source_updates_cache=source_updates_cache.cache,
        source_updates_cache_scope=source_updates_cache.scope,
    )
    collected_results = await asyncio.gather(
        *(_collect_from_source(interest, source, context) for interest, source in sources),
        return_exceptions=True,
    )
    source_results: list[list[Update]] = []
    errors: list[CollectionError] = []
    for (interest, source), result in zip(sources, collected_results, strict=True):
        if isinstance(result, Exception):
            errors.append(_collection_error(interest, source, result))
            continue
        if isinstance(result, BaseException):
            raise result
        source_results.append(result)

    return _updates_response(
        source_results,
        errors=errors,
        checked=len(sources),
        timeframe=timeframe,
    )
