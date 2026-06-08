from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime, timedelta

import pytest

from learning_engine.application.collect_updates import (
    CollectUpdatesDependencies,
    SourceUpdatesCache,
    SourceUpdatesCacheOptions,
    collect_updates,
)
from learning_engine.application.responses import UpdatesResponse
from learning_engine.common.timeframe import Timeframe
from learning_engine.domain.interests import InterestsPayload
from learning_engine.domain.source_types import SourceType
from learning_engine.infrastructure.fetching import Fetcher
from learning_engine.infrastructure.source_collectors.registry import SourceUpdateCollectorRegistry

RECENT_DAYS = 14
NOW = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)
ALL_TIMEFRAME = Timeframe(start=datetime.min.replace(tzinfo=UTC), end=NOW)
RECENT_TIMEFRAME = Timeframe.ending_at(NOW, timedelta(days=RECENT_DAYS))
EXPECTED_RETRY_CALLS = 2


async def unused_fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
    raise AssertionError(f"Unexpected JSON fetch: {url} {headers}")


async def no_source_image(*_args: object) -> str | None:
    return None


class StubSourceImageProvider:
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
    ) -> str | None:
        return await no_source_image(source_type, source_url)


class StubHttpFetcher:
    def __init__(
        self,
        fetch: Callable[[str], Awaitable[bytes]],
        fetch_json: Callable[[str, Mapping[str, str]], Awaitable[dict[str, object]]],
    ) -> None:
        self._fetch = fetch
        self._fetch_json = fetch_json

    async def fetch_url(self, url: str) -> bytes:
        return await self._fetch(url)

    async def fetch_json(self, url: str, headers: Mapping[str, str]) -> dict[str, object]:
        return await self._fetch_json(url, headers)


async def _collect_updates(
    payload: InterestsPayload,
    *,
    timeframe: Timeframe,
    http_fetcher: Fetcher,
    source_updates_cache: SourceUpdatesCacheOptions,
) -> UpdatesResponse:
    return await collect_updates(
        payload,
        timeframe=timeframe,
        dependencies=CollectUpdatesDependencies(
            source_update_collector=SourceUpdateCollectorRegistry(http_fetcher),
            source_image_provider=StubSourceImageProvider(),
        ),
        source_updates_cache=source_updates_cache,
    )


@pytest.mark.anyio
async def test_collect_updates_fetches_enabled_sources_only() -> None:
    payload = {
        "interests": [
            {
                "id": "typescript",
                "name": "TypeScript",
                "description": "TypeScript releases.",
                "enabled": True,
                "sources": [
                    {
                        "id": "typescript-feed",
                        "label": "TypeScript feed",
                        "type": "feed",
                        "url": "https://example.com/typescript.xml",
                        "enabled": True,
                    },
                    {
                        "id": "typescript-disabled",
                        "label": "Disabled feed",
                        "type": "feed",
                        "url": "https://example.com/disabled.xml",
                        "enabled": False,
                    },
                ],
            },
            {
                "id": "python",
                "name": "Python",
                "description": "Python releases.",
                "enabled": False,
                "sources": [
                    {
                        "id": "python-feed",
                        "label": "Python feed",
                        "type": "feed",
                        "url": "https://example.com/python.xml",
                    }
                ],
            },
            {
                "id": "deleted",
                "name": "Deleted",
                "description": "Deleted topic.",
                "enabled": True,
                "deletedAt": "2026-05-15T10:00:00.000Z",
                "sources": [
                    {
                        "id": "deleted-feed",
                        "label": "Deleted feed",
                        "type": "feed",
                        "url": "https://example.com/deleted.xml",
                    }
                ],
            },
        ]
    }
    rss = b"""<rss><channel><item><title>TypeScript Beta</title><link>https://example.com/beta</link>
    <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    fetched_urls: list[str] = []

    async def fetch_url(url: str) -> bytes:
        fetched_urls.append(url)
        return rss

    result = await _collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch_url, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert fetched_urls == ["https://example.com/typescript.xml"]
    assert result.sources_checked == 1
    assert result.updates[0].source_interest.interest_name == "TypeScript"
    assert result.updates[0].source_interest.source_id == "typescript-feed"
    assert result.updates[0].source_interest.source_label == "TypeScript feed"
    assert result.updates[0].title == "TypeScript Beta"


@pytest.mark.anyio
async def test_collect_updates_uses_source_ignore_keywords() -> None:
    payload = {
        "interests": [
            {
                "id": "t3code",
                "name": "T3 Code",
                "description": "Track T3 Code releases.",
                "enabled": True,
                "sources": [
                    {
                        "id": "t3code-feed",
                        "label": "T3 Code feed",
                        "type": "feed",
                        "url": "https://example.com/t3code.xml",
                        "ignoreKeywords": ["nightly"],
                    }
                ],
            }
        ]
    }
    rss = b"""<rss><channel>
      <item><title>T3 Code nightly build</title><link>https://example.com/nightly</link>
      <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item>
      <item><title>T3 Code stable release</title><link>https://example.com/stable</link>
      <pubDate>Fri, 15 May 2026 11:00:00 GMT</pubDate></item>
    </channel></rss>"""

    async def fetch_url(_url: str) -> bytes:
        return rss

    result = await _collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch_url, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert [update.title for update in result.updates] == ["T3 Code stable release"]


@pytest.mark.anyio
async def test_collect_updates_can_filter_to_recent_days() -> None:
    payload = {
        "interests": [
            {
                "id": "typescript",
                "name": "TypeScript",
                "description": "TypeScript releases.",
                "enabled": True,
                "sources": [
                    {
                        "id": "typescript-feed",
                        "label": "TypeScript feed",
                        "type": "feed",
                        "url": "https://example.com/typescript.xml",
                    }
                ],
            }
        ]
    }
    rss = b"""<rss><channel>
      <item><title>TypeScript fresh release</title><link>https://example.com/fresh</link>
      <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item>
      <item><title>TypeScript old release</title><link>https://example.com/old</link>
      <pubDate>Mon, 20 Apr 2026 10:00:00 GMT</pubDate></item>
    </channel></rss>"""

    async def fetch_url(_url: str) -> bytes:
        return rss

    result = await _collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=RECENT_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch_url, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.since == "2026-05-01T12:00:00Z"
    assert [update.title for update in result.updates] == ["TypeScript fresh release"]


@pytest.mark.anyio
async def test_collect_updates_uses_page_sources() -> None:
    payload = {
        "interests": [
            {
                "id": "anthropic-model-announcements",
                "name": "Anthropic model announcements",
                "description": "Track model launches.",
                "enabled": True,
                "sources": [
                    {
                        "id": "anthropic-news",
                        "label": "Anthropic news",
                        "type": "page",
                        "url": "https://example.com/news",
                    }
                ],
            }
        ]
    }
    html = b"""<html><body>
      <article><time>May 10, 2026</time><a href="/news/claude-model">Claude model update</a>
      <p>Launch details.</p></article>
    </body></html>"""

    fetched_urls: list[str] = []

    async def fetch_url(url: str) -> bytes:
        fetched_urls.append(url)
        return html

    result = await _collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=RECENT_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch_url, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert fetched_urls == ["https://example.com/news"]
    assert result.updates[0].source_interest.source_type == "page"
    assert result.updates[0].source_interest.source_url == "https://example.com/news"
    assert result.updates[0].url == "https://example.com/news/claude-model"


@pytest.mark.anyio
async def test_collect_updates_reports_source_errors_without_caching_them() -> None:
    payload = {
        "interests": [
            {
                "id": "typescript",
                "name": "TypeScript",
                "description": "TypeScript releases.",
                "sources": [
                    {
                        "id": "typescript-feed",
                        "label": "TypeScript feed",
                        "type": "feed",
                        "url": "https://example.com/typescript.xml",
                    }
                ],
            }
        ]
    }
    calls = 0

    async def fetch_url(_url: str) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("network down")
        return b"""<rss><channel><item><title>Recovered update</title><link>https://example.com/recovered</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    source_updates_cache: SourceUpdatesCache = {}
    interests = InterestsPayload.model_validate(payload)
    http_fetcher = StubHttpFetcher(fetch_url, unused_fetch_json)

    failed_result = await _collect_updates(
        interests,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=http_fetcher,
        source_updates_cache=SourceUpdatesCacheOptions(cache=source_updates_cache),
    )

    assert failed_result.updates == []
    assert len(failed_result.errors) == 1
    assert failed_result.errors[0].interest_id == "typescript"
    assert failed_result.errors[0].interest_name == "TypeScript"
    assert failed_result.errors[0].source_id == "typescript-feed"
    assert failed_result.errors[0].source_label == "TypeScript feed"
    assert failed_result.errors[0].source_url == "https://example.com/typescript.xml"
    assert failed_result.errors[0].source_type == "feed"
    assert failed_result.errors[0].error == "network down"

    result = await _collect_updates(
        interests,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=http_fetcher,
        source_updates_cache=SourceUpdatesCacheOptions(cache=source_updates_cache),
    )

    assert calls == EXPECTED_RETRY_CALLS
    assert result.updates[0].title == "Recovered update"
    assert result.errors == []
