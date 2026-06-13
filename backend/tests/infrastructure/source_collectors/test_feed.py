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


def test_parse_rss_extracts_update_specific_image_url() -> None:
    rss = b"""<?xml version="1.0"?>
    <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>
      <item>
        <title>Release with thumbnail</title>
        <link>https://example.com/posts/release</link>
        <media:thumbnail url="/images/release.png" />
        <enclosure url="https://example.com/fallback.jpg" type="image/jpeg" />
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate>
      </item>
    </channel></rss>"""

    updates = parse_feed_items(rss, watch_keywords=[], ignore_keywords=[])

    assert len(updates) == 1
    assert updates[0].image_url == "https://example.com/images/release.png"


def test_parse_rss_uses_image_enclosure_when_media_thumbnail_is_missing() -> None:
    rss = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>Release with enclosure</title>
        <link>https://example.com/posts/release</link>
        <enclosure url="//cdn.example.com/release.jpg" type="image/jpeg" />
        <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate>
      </item>
    </channel></rss>"""

    updates = parse_feed_items(rss, watch_keywords=[], ignore_keywords=[])

    assert len(updates) == 1
    assert updates[0].image_url == "https://cdn.example.com/release.jpg"


def test_parse_rss_extracts_update_image_from_description_img() -> None:
    rss = (
        b"""<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>WebMCP Standard Proposal for Agentic Web Actuation Now Available in Chrome</title>
            <link>https://www.infoq.com/news/2026/06/webmcp-web-agent-standard-chrome/</link>
            <description><img src="https://res.infoq.com/news/2026/06/webmcp-web-agent-standard-chrome/en/headerimage/"""
        b"""generatedHeaderImage-1781307482428.jpg"/><p>Google recently announced that WebMCP is entering origin """
        b"""trials in Chrome 149.</p> <i>By Bruno Couriol</i></description>
            <pubDate>Sat, 13 Jun 2026 03:32:00 GMT</pubDate>
          </item>
        </channel></rss>"""
    )

    updates = parse_feed_items(rss, watch_keywords=[], ignore_keywords=[])

    assert len(updates) == 1
    assert (
        updates[0].image_url
        == "https://res.infoq.com/news/2026/06/webmcp-web-agent-standard-chrome/en/headerimage/generatedHeaderImage-1781307482428.jpg"
    )
    assert (
        updates[0].summary
        == "Google recently announced that WebMCP is entering origin trials in Chrome 149. By Bruno Couriol"
    )
