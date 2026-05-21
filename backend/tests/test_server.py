from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from learning_engine.collector import collect_updates
from learning_engine.models import Interest, InterestsPayload
from learning_engine.sources.feed import parse_feed_items
from learning_engine.storage import DEFAULT_DATA
from learning_engine.timeframe import Timeframe

RECENT_DAYS = 14
NOW = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)
ALL_TIMEFRAME = Timeframe(start=datetime.min.replace(tzinfo=UTC), end=NOW)
RECENT_TIMEFRAME = Timeframe.ending_at(NOW, timedelta(days=RECENT_DAYS))


async def unused_fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
    raise AssertionError(f"Unexpected JSON fetch: {url} {headers}")


def test_normalize_interest_keeps_general_topic_and_sources() -> None:
    interest = Interest.model_validate(
        {
            "id": "typescript",
            "name": "TypeScript",
            "description": "Language/compiler updates only.",
            "priority": "high",
            "sources": [
                {
                    "id": "typescript-dev-blog",
                    "label": "TypeScript dev blog",
                    "type": "feed",
                    "url": "https://devblogs.microsoft.com/typescript/feed/",
                    "ignoreKeywords": ["nightly"],
                    "enabled": True,
                    "deletedAt": "2026-05-15T10:00:00.000Z",
                }
            ],
            "enabled": True,
        }
    ).model_dump(mode="json", by_alias=True)

    assert interest["name"] == "TypeScript"
    assert interest["description"] == "Language/compiler updates only."
    assert interest["sources"][0]["label"] == "TypeScript dev blog"
    assert interest["sources"][0]["type"] == "feed"
    assert interest["sources"][0]["ignoreKeywords"] == ["nightly"]
    assert interest["sources"][0]["deletedAt"] == "2026-05-15T10:00:00.000Z"


def test_normalize_interest_rejects_old_schema_fields() -> None:
    with pytest.raises(ValidationError):
        Interest.model_validate(
            {
                "id": "typescript",
                "name": "TypeScript",
                "type": "technology",
                "official_feed_url": "https://devblogs.microsoft.com/typescript/feed/",
                "watch_keywords": ["release"],
                "ignore_keywords": ["webinar"],
                "notes": "Language/compiler updates only.",
            }
        )


def test_default_data_contains_typescript_sources() -> None:
    interests = DEFAULT_DATA.model_dump(mode="json", by_alias=True)["interests"]

    assert [item["id"] for item in interests] == ["typescript"]
    assert interests[0]["description"]
    assert [source["type"] for source in interests[0]["sources"]] == ["page", "feed"]
    assert "type" not in interests[0]
    assert "official_feed_url" not in interests[0]


def test_parse_rss_filters_by_watch_and_ignore_keywords() -> None:
    rss = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>Announcing TypeScript 5.9 Beta</title>
        <link>https://example.com/ts-59-beta</link>
        <description>Compiler and language changes.</description>
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate>
      </item>
      <item>
        <title>TypeScript webinar recording</title>
        <link>https://example.com/webinar</link>
        <description>Community session.</description>
      </item>
      <item>
        <title>Unrelated blog post</title>
        <link>https://example.com/other</link>
        <description>Nothing relevant here.</description>
      </item>
    </channel></rss>"""

    updates = parse_feed_items(
        rss,
        watch_keywords=["release", "beta", "compiler"],
        ignore_keywords=["webinar"],
    )

    assert len(updates) == 1
    assert updates[0].title == "Announcing TypeScript 5.9 Beta"
    assert updates[0].url == "https://example.com/ts-59-beta"
    assert updates[0].matched_keywords == ["beta", "compiler"]


def test_parse_atom_feed_uses_feedparser_normalization() -> None:
    atom = b"""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>TypeScript compiler release candidate</title>
        <link href="https://example.com/atom-release" />
        <summary>RC details for the compiler.</summary>
        <updated>2026-05-15T10:00:00Z</updated>
      </entry>
    </feed>"""

    updates = parse_feed_items(atom, watch_keywords=["compiler", "rc"], ignore_keywords=[])

    assert len(updates) == 1
    assert updates[0].url == "https://example.com/atom-release"
    assert updates[0].published_at == "2026-05-15T10:00:00Z"
    assert updates[0].matched_keywords == ["compiler", "rc"]


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

    result = await collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=ALL_TIMEFRAME,
        fetch=fetch_url,
        fetch_json=unused_fetch_json,
    )

    assert fetched_urls == ["https://example.com/typescript.xml"]
    assert result.sources_checked == 1
    assert result.updates[0].interest_name == "TypeScript"
    assert result.updates[0].source_id == "typescript-feed"
    assert result.updates[0].source_label == "TypeScript feed"
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

    result = await collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=ALL_TIMEFRAME,
        fetch=fetch_url,
        fetch_json=unused_fetch_json,
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

    result = await collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=RECENT_TIMEFRAME,
        fetch=fetch_url,
        fetch_json=unused_fetch_json,
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

    result = await collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=RECENT_TIMEFRAME,
        fetch=fetch_url,
        fetch_json=unused_fetch_json,
    )

    assert fetched_urls == ["https://example.com/news"]
    assert result.updates[0].source_type == "page"
    assert result.updates[0].source_url == "https://example.com/news"
    assert result.updates[0].url == "https://example.com/news/claude-model"


@pytest.mark.anyio
async def test_collect_updates_reports_source_errors() -> None:
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

    async def fetch_url(_url: str) -> bytes:
        raise OSError("network down")

    result = await collect_updates(
        InterestsPayload.model_validate(payload),
        timeframe=ALL_TIMEFRAME,
        fetch=fetch_url,
        fetch_json=unused_fetch_json,
    )

    assert result.sources_checked == 1
    assert result.updates == []
    assert result.errors[0].interest_id == "typescript"
    assert result.errors[0].source_id == "typescript-feed"
    assert result.errors[0].source_url == "https://example.com/typescript.xml"
    assert result.errors[0].error == "network down"
