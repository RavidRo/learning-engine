from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime

import pytest

from learning_engine.application.collect_updates import (
    CollectUpdatesDependencies,
    SourceUpdatesCacheOptions,
    collect_updates,
    dedupe_updates,
)
from learning_engine.application.ports import HttpFetcher
from learning_engine.application.resolve_source_image import (
    SourceImageConfigurationError,
    SourceImageProviderUnavailableError,
)
from learning_engine.application.responses import UpdatesResponse
from learning_engine.common.timeframe import Timeframe
from learning_engine.domain.interests import InterestsPayload
from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import SourceInterest, Update
from learning_engine.infrastructure.source_collectors.registry import (
    SourceUpdateCollectorRegistry,
)

NOW = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)
ALL_TIMEFRAME = Timeframe(start=datetime.min.replace(tzinfo=UTC), end=NOW)
CONCURRENT_SOURCE_COUNT = 2


async def unused_fetch(url: str) -> bytes:
    raise AssertionError(f"Unexpected byte fetch: {url}")


async def unused_fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
    raise AssertionError(f"Unexpected JSON fetch: {url} {headers}")


async def no_source_image(*_args: object) -> str | None:
    return None


class StubSourceImageProvider:
    def __init__(
        self,
        resolve_source_image: Callable[..., Awaitable[str | None]] = no_source_image,
    ) -> None:
        self._resolve_source_image = resolve_source_image

    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
        http_fetcher: HttpFetcher,
    ) -> str | None:
        return await self._resolve_source_image(source_type, source_url, http_fetcher)


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
    http_fetcher: HttpFetcher,
    source_updates_cache: SourceUpdatesCacheOptions,
    source_image_provider: StubSourceImageProvider | None = None,
) -> UpdatesResponse:
    return await collect_updates(
        payload,
        timeframe=timeframe,
        dependencies=CollectUpdatesDependencies(
            http_fetcher=http_fetcher,
            source_update_collector=SourceUpdateCollectorRegistry(http_fetcher),
            source_image_provider=source_image_provider or StubSourceImageProvider(),
        ),
        source_updates_cache=source_updates_cache,
    )


def test_dedupe_keeps_distinct_updates_when_title_and_url_are_missing() -> None:
    updates = [
        Update(
            source_interest=SourceInterest(
                interest_id=None,
                interest_name="Interest",
                source_id=None,
                source_label="Source",
                source_url="https://example.com/a",
                source_type="feed",
            ),
            summary="first",
        ),
        Update(
            source_interest=SourceInterest(
                interest_id=None,
                interest_name="Interest",
                source_id=None,
                source_label="Source",
                source_url="https://example.com/b",
                source_type="feed",
            ),
            summary="second",
        ),
    ]

    assert dedupe_updates(updates) == updates


@pytest.mark.anyio
async def test_collect_updates_uses_youtube_channel_feed_for_channel_id() -> None:
    called_urls: list[str] = []

    async def fetch(url: str) -> bytes:
        called_urls.append(url)
        return b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>New lecture</title>
            <link href="https://www.youtube.com/watch?v=abc" />
            <updated>2026-05-15T10:00:00Z</updated>
          </entry>
        </feed>"""

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "id": "ml",
                    "name": "ML",
                    "sources": [
                        {
                            "id": "channel",
                            "type": "youtube_channel",
                            "url": "UCabcabcabcabcabcabcabc",
                        }
                    ],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert called_urls == ["https://www.youtube.com/feeds/videos.xml?channel_id=UCabcabcabcabcabcabcabc"]
    assert result.updates[0].source_interest.source_type == "youtube_channel"
    assert result.updates[0].title == "New lecture"


@pytest.mark.anyio
async def test_collect_updates_carries_source_interest_to_updates() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>Source update</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Images",
                    "sources": [
                        {
                            "id": "with-image",
                            "type": "feed",
                            "url": "https://example.com/feed.xml",
                            "imageUrl": "https://example.com/avatar.png",
                        }
                    ],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.updates[0].source_interest.interest_name == "Images"
    assert result.updates[0].source_interest.source_id == "with-image"
    assert result.updates[0].source_interest.source_image_url == "https://example.com/avatar.png"


@pytest.mark.anyio
async def test_collect_updates_uses_manual_source_image_before_resolver() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>Manual image</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    async def resolve_source_image(*_args: object) -> str | None:
        raise AssertionError("Manual source image should skip automatic resolution")

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Manual",
                    "sources": [
                        {
                            "type": "feed",
                            "url": "https://example.com/feed.xml",
                            "imageUrl": "https://example.com/manual.png",
                        }
                    ],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_image_provider=StubSourceImageProvider(resolve_source_image),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.updates[0].source_interest.source_image_url == "https://example.com/manual.png"


@pytest.mark.anyio
async def test_collect_updates_uses_automatic_source_image_when_manual_is_missing() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>Automatic image</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    async def resolve_source_image(*_args: object) -> str | None:
        return "https://example.com/auto.png"

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Automatic",
                    "sources": [{"type": "feed", "url": "https://example.com/feed.xml"}],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_image_provider=StubSourceImageProvider(resolve_source_image),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.updates[0].source_interest.source_image_url == "https://example.com/auto.png"
    assert payload.interests[0].sources[0].image_url is None


@pytest.mark.anyio
async def test_collect_updates_keeps_null_source_image_when_resolver_misses() -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>No image</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    async def resolve_source_image(*_args: object) -> str | None:
        return None

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Missing",
                    "sources": [{"type": "feed", "url": "https://example.com/feed.xml"}],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_image_provider=StubSourceImageProvider(resolve_source_image),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.updates[0].source_interest.source_image_url is None


@pytest.mark.anyio
async def test_collect_updates_logs_and_continues_when_source_image_provider_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>Provider unavailable</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    async def resolve_source_image(*_args: object) -> str | None:
        raise SourceImageProviderUnavailableError("Feed metadata provider is unavailable")

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Provider",
                    "sources": [{"type": "feed", "url": "https://example.com/feed.xml"}],
                }
            ]
        }
    )

    with caplog.at_level(logging.INFO, logger="learning_engine.application.collect_updates"):
        result = await _collect_updates(
            payload,
            timeframe=ALL_TIMEFRAME,
            http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
            source_image_provider=StubSourceImageProvider(resolve_source_image),
            source_updates_cache=SourceUpdatesCacheOptions(cache={}),
        )

    assert result.updates[0].source_interest.source_image_url is None
    assert "Source image provider is unavailable" in caplog.text


@pytest.mark.anyio
async def test_collect_updates_logs_and_continues_when_source_image_configuration_is_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>Configuration missing</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    async def resolve_source_image(*_args: object) -> str | None:
        raise SourceImageConfigurationError("Spotify bearer token is not configured")

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Configuration",
                    "sources": [{"type": "feed", "url": "https://example.com/feed.xml"}],
                }
            ]
        }
    )

    with caplog.at_level(logging.INFO, logger="learning_engine.application.collect_updates"):
        result = await _collect_updates(
            payload,
            timeframe=ALL_TIMEFRAME,
            http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
            source_image_provider=StubSourceImageProvider(resolve_source_image),
            source_updates_cache=SourceUpdatesCacheOptions(cache={}),
        )

    assert result.updates[0].source_interest.source_image_url is None
    assert "Source image configuration is unavailable" in caplog.text


@pytest.mark.anyio
async def test_collect_updates_logs_and_continues_when_source_image_resolver_crashes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def fetch(_url: str) -> bytes:
        return b"""<rss><channel><item><title>Resolver crash</title><link>https://example.com/update</link>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""

    async def resolve_source_image(*_args: object) -> str | None:
        raise RuntimeError("unexpected resolver failure")

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Internal",
                    "sources": [{"type": "feed", "url": "https://example.com/feed.xml"}],
                }
            ]
        }
    )

    with caplog.at_level(logging.ERROR, logger="learning_engine.application.collect_updates"):
        result = await _collect_updates(
            payload,
            timeframe=ALL_TIMEFRAME,
            http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
            source_image_provider=StubSourceImageProvider(resolve_source_image),
            source_updates_cache=SourceUpdatesCacheOptions(cache={}),
        )

    assert result.updates[0].source_interest.source_image_url is None
    assert "Source image resolver failed during update collection" in caplog.text


@pytest.mark.anyio
async def test_collect_updates_collects_sources_concurrently() -> None:
    rss = b"""<rss><channel><item><title>Source update</title><link>https://example.com/update</link>
    <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""
    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Parallel",
                    "sources": [
                        {
                            "id": "first",
                            "type": "feed",
                            "url": "https://example.com/first.xml",
                        },
                        {
                            "id": "second",
                            "type": "feed",
                            "url": "https://example.com/second.xml",
                        },
                    ],
                }
            ]
        }
    )
    active_fetches = 0
    max_active_fetches = 0

    async def fetch(_url: str) -> bytes:
        nonlocal active_fetches, max_active_fetches
        active_fetches += 1
        max_active_fetches = max(max_active_fetches, active_fetches)
        await asyncio.sleep(0.05)
        active_fetches -= 1
        return rss

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.sources_checked == CONCURRENT_SOURCE_COUNT
    assert max_active_fetches == CONCURRENT_SOURCE_COUNT


@pytest.mark.anyio
async def test_collect_updates_allows_equivalent_sources_to_fetch_concurrently() -> None:
    rss = b"""<rss><channel><item><title>Cached update</title><link>https://example.com/update</link>
    <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item></channel></rss>"""
    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Parallel cache",
                    "sources": [
                        {
                            "id": "first",
                            "type": "feed",
                            "url": "https://example.com/feed.xml",
                        },
                        {
                            "id": "second",
                            "type": "feed",
                            "url": "https://example.com/feed.xml",
                        },
                    ],
                }
            ]
        }
    )
    called_urls: list[str] = []

    async def fetch(url: str) -> bytes:
        called_urls.append(url)
        await asyncio.sleep(0.05)
        return rss

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.sources_checked == CONCURRENT_SOURCE_COUNT
    assert called_urls == [
        "https://example.com/feed.xml",
        "https://example.com/feed.xml",
    ]


@pytest.mark.anyio
async def test_collect_updates_resolves_youtube_handle_before_fetching_feed() -> None:
    called_urls: list[str] = []

    async def fetch(url: str) -> bytes:
        called_urls.append(url)
        if url == "https://www.youtube.com/@example":
            return b"""<html><meta itemprop="channelId" content="UCabcabcabcabcabcabcabc"></html>"""
        return b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Handle video</title>
            <link href="https://www.youtube.com/watch?v=abc" />
            <updated>2026-05-15T10:00:00Z</updated>
          </entry>
        </feed>"""

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Videos",
                    "sources": [{"type": "youtube_channel", "url": "@example"}],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(fetch, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert called_urls == [
        "https://www.youtube.com/@example",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCabcabcabcabcabcabcabc",
    ]
    assert result.updates[0].title == "Handle video"


@pytest.mark.anyio
async def test_collect_updates_uses_x_api_for_twitter_accounts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
    called: list[tuple[str, Mapping[str, str]]] = []

    async def fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
        called.append((url, headers))
        if url.endswith("/users/by/username/xdevelopers"):
            return {"data": {"id": "2244994945"}}
        return {
            "data": [
                {
                    "id": "1",
                    "text": "Learning engine update",
                    "created_at": "2026-05-15T10:00:00Z",
                }
            ]
        }

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "X",
                    "sources": [{"type": "twitter_account", "url": "https://x.com/xdevelopers"}],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(unused_fetch, fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert [url for url, _headers in called] == [
        "https://api.x.com/2/users/by/username/xdevelopers",
        "https://api.x.com/2/users/2244994945/tweets?max_results=20&tweet.fields=created_at&exclude=retweets,replies",
    ]
    assert called[0][1] == {"Authorization": "Bearer test-token"}
    assert result.updates[0].url == "https://x.com/xdevelopers/status/1"


@pytest.mark.anyio
async def test_collect_updates_reports_missing_twitter_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "X",
                    "sources": [{"id": "x", "type": "twitter_account", "url": "@xdevelopers"}],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(unused_fetch, unused_fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert result.updates == []
    assert result.errors[0].source_id == "x"
    assert result.errors[0].error == "Twitter bearer token is required for twitter_account sources"


@pytest.mark.anyio
async def test_collect_updates_uses_spotify_show_episodes_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPOTIFY_ACCESS_TOKEN", "spotify-token")
    called: list[tuple[str, Mapping[str, str]]] = []

    async def fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
        called.append((url, headers))
        return {
            "items": [
                {
                    "name": "Episode one",
                    "description": "A useful episode",
                    "release_date": "2026-05-15",
                    "external_urls": {"spotify": "https://open.spotify.com/episode/episode-one"},
                }
            ]
        }

    payload = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "Podcast",
                    "sources": [
                        {
                            "type": "spotify_podcast",
                            "url": "https://open.spotify.com/show/show-one",
                        }
                    ],
                }
            ]
        }
    )

    result = await _collect_updates(
        payload,
        timeframe=ALL_TIMEFRAME,
        http_fetcher=StubHttpFetcher(unused_fetch, fetch_json),
        source_updates_cache=SourceUpdatesCacheOptions(cache={}),
    )

    assert called == [
        (
            "https://api.spotify.com/v1/shows/show-one/episodes?limit=20&market=US",
            {"Authorization": "Bearer spotify-token"},
        )
    ]
    assert result.updates[0].title == "Episode one"
    assert result.updates[0].url == "https://open.spotify.com/episode/episode-one"
