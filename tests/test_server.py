import unittest
from datetime import UTC, datetime
from unittest.mock import patch

import server


class TestLearningEngineServer(unittest.TestCase):
    def test_normalize_technology_interest_keeps_official_source_fields(self):
        interest = server.normalize_interest({
            "id": "typescript",
            "name": "TypeScript",
            "type": "technology",
            "priority": "high",
            "sources": ["should", "not", "persist"],
            "official_site_url": "https://www.typescriptlang.org/",
            "official_feed_url": "https://devblogs.microsoft.com/typescript/feed/",
            "watch_keywords": ["release", "beta"],
            "ignore_keywords": ["webinar"],
            "notes": "Language/compiler updates only.",
            "enabled": True,
        })

        self.assertEqual(interest["type"], "technology")
        self.assertEqual(interest["official_site_url"], "https://www.typescriptlang.org/")
        self.assertEqual(interest["official_feed_url"], "https://devblogs.microsoft.com/typescript/feed/")
        self.assertEqual(interest["watch_keywords"], ["release", "beta"])
        self.assertEqual(interest["ignore_keywords"], ["webinar"])
        self.assertNotIn("sources", interest)

    def test_normalize_interest_only_allows_technology_for_now(self):
        interest = server.normalize_interest({
            "id": "architecture",
            "name": "Software Architecture",
            "type": "concept",
            "priority": "high",
        })

        self.assertEqual(interest["type"], "technology")

    def test_default_data_only_contains_typescript_technology_interest(self):
        interests = server.DEFAULT_DATA["interests"]

        self.assertEqual([item["id"] for item in interests], ["typescript"])
        self.assertTrue(all(item["type"] == "technology" for item in interests))
        self.assertTrue(all("sources" not in item for item in interests))

    def test_parse_rss_filters_by_watch_and_ignore_keywords(self):
        rss = b'''<?xml version="1.0"?>
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
        </channel></rss>'''

        updates = server.parse_feed_items(
            rss,
            watch_keywords=["release", "beta", "compiler"],
            ignore_keywords=["webinar"],
        )

        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["title"], "Announcing TypeScript 5.9 Beta")
        self.assertEqual(updates[0]["url"], "https://example.com/ts-59-beta")
        self.assertEqual(updates[0]["matched_keywords"], ["beta", "compiler"])

    def test_collect_technology_updates_fetches_enabled_technology_feeds_only(self):
        payload = {
            "interests": [
                {
                    "id": "typescript",
                    "name": "TypeScript",
                    "type": "technology",
                    "enabled": True,
                    "official_feed_url": "https://example.com/typescript.xml",
                    "watch_keywords": ["beta"],
                    "ignore_keywords": [],
                },
                {
                    "id": "python",
                    "name": "Python",
                    "type": "technology",
                    "enabled": False,
                    "official_feed_url": "https://example.com/python.xml",
                },
                {
                    "id": "person",
                    "name": "Someone",
                    "type": "person",
                    "enabled": True,
                    "official_feed_url": "https://example.com/person.xml",
                },
            ]
        }
        rss = b'''<rss><channel><item><title>TypeScript Beta</title><link>https://example.com/beta</link></item></channel></rss>'''

        with patch("server.fetch_url", return_value=rss) as fetch_url:
            result = server.collect_technology_updates(payload)

        fetch_url.assert_called_once_with("https://example.com/typescript.xml")
        self.assertEqual(result["interests_checked"], 1)
        self.assertEqual(result["updates"][0]["interest_name"], "TypeScript")
        self.assertEqual(result["updates"][0]["title"], "TypeScript Beta")

    def test_collect_technology_updates_can_filter_to_recent_days(self):
        payload = {
            "interests": [
                {
                    "id": "typescript",
                    "name": "TypeScript",
                    "type": "technology",
                    "enabled": True,
                    "official_feed_url": "https://example.com/typescript.xml",
                    "watch_keywords": ["typescript"],
                    "ignore_keywords": [],
                }
            ]
        }
        rss = b"""<rss><channel>
          <item><title>TypeScript fresh release</title><link>https://example.com/fresh</link>
          <pubDate>Fri, 15 May 2026 10:00:00 GMT</pubDate></item>
          <item><title>TypeScript old release</title><link>https://example.com/old</link>
          <pubDate>Mon, 20 Apr 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""

        with patch("server.fetch_url", return_value=rss):
            result = server.collect_technology_updates(
                payload,
                days=14,
                now=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
            )

        self.assertEqual(result["days"], 14)
        self.assertEqual([update["title"] for update in result["updates"]], ["TypeScript fresh release"])

    def test_collect_technology_updates_uses_official_page_fallback_without_feed(self):
        payload = {
            "interests": [
                {
                    "id": "anthropic-model-announcements",
                    "name": "Anthropic model announcements",
                    "type": "technology",
                    "enabled": True,
                    "official_site_url": "https://example.com/news",
                    "official_feed_url": "",
                    "watch_keywords": ["claude", "model"],
                    "ignore_keywords": [],
                }
            ]
        }
        html = b"""<html><body>
          <article><time>May 10, 2026</time><a href="/news/claude-model">Claude model update</a>
          <p>Launch details.</p></article>
        </body></html>"""

        with patch("server.fetch_url", return_value=html) as fetch_url:
            result = server.collect_technology_updates(
                payload,
                days=14,
                now=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
            )

        fetch_url.assert_called_once_with("https://example.com/news")
        self.assertEqual(result["updates"][0]["source_type"], "page")
        self.assertEqual(result["updates"][0]["url"], "https://example.com/news/claude-model")


if __name__ == "__main__":
    unittest.main()
