from __future__ import annotations

from datetime import UTC, datetime

from learning_engine.infrastructure.source_collectors.feed import parse_feed_items


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
    assert updates[0].published_at == datetime(2026, 5, 15, 10, 0, tzinfo=UTC)
    assert updates[0].matched_keywords == ["compiler", "rc"]
