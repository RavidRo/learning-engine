from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from learning_engine.collector import collect_updates, dedupe_updates
from learning_engine.models import CollectedUpdate, InterestSource, InterestsPayload, Update
from learning_engine.sources.spotify import spotify_show_id
from learning_engine.sources.twitter import twitter_username
from learning_engine.timeframe import Timeframe

NOW = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)
ALL_TIMEFRAME = Timeframe(start=datetime.min.replace(tzinfo=UTC), end=NOW)


def unused_fetch(url: str) -> bytes:
    raise AssertionError(f"Unexpected byte fetch: {url}")


def unused_fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
    raise AssertionError(f"Unexpected JSON fetch: {url} {headers}")


def test_update_enriches_generic_collected_update_without_feed_specific_base() -> None:
    assert issubclass(Update, CollectedUpdate)
    assert Update.__bases__ == (CollectedUpdate,)


def test_source_type_accepts_new_human_friendly_aliases() -> None:
    assert InterestSource.model_validate({"type": "RSS", "url": "https://example.com/feed.xml"}).type == "feed"
    assert InterestSource.model_validate({"type": "Webpage", "url": "https://example.com"}).type == "page"
    assert (
        InterestSource.model_validate(
            {"type": "Youtube Channels", "url": "https://youtube.com/channel/UCabcabcabcabcabcabcabc"}
        ).type
        == "youtube_channel"
    )
    assert InterestSource.model_validate({"type": "Twitter Accounts", "url": "@xdevelopers"}).type == "twitter_account"
    assert (
        InterestSource.model_validate({"type": "Spotify Podcasts", "url": "spotify:show:abc"}).type
        == "spotify_podcast"
    )


def test_dedupe_keeps_distinct_updates_when_title_and_url_are_missing() -> None:
    updates = [
        Update(source_url="https://example.com/a", source_type="feed", summary="first"),
        Update(source_url="https://example.com/b", source_type="feed", summary="second"),
    ]

    assert dedupe_updates(updates) == updates


def test_collect_updates_uses_youtube_channel_feed_for_channel_id() -> None:
    called_urls: list[str] = []

    def fetch(url: str) -> bytes:
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

    result = collect_updates(payload, timeframe=ALL_TIMEFRAME, fetch=fetch, fetch_json=unused_fetch_json)

    assert called_urls == ["https://www.youtube.com/feeds/videos.xml?channel_id=UCabcabcabcabcabcabcabc"]
    assert result.updates[0].source_type == "youtube_channel"
    assert result.updates[0].title == "New lecture"


def test_collect_updates_resolves_youtube_handle_before_fetching_feed() -> None:
    called_urls: list[str] = []

    def fetch(url: str) -> bytes:
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

    result = collect_updates(payload, timeframe=ALL_TIMEFRAME, fetch=fetch, fetch_json=unused_fetch_json)

    assert called_urls == [
        "https://www.youtube.com/@example",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCabcabcabcabcabcabcabc",
    ]
    assert result.updates[0].title == "Handle video"


def test_collect_updates_uses_x_api_for_twitter_accounts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TWITTER_BEARER_TOKEN", "test-token")
    called: list[tuple[str, Mapping[str, str]]] = []

    def fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
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

    result = collect_updates(payload, timeframe=ALL_TIMEFRAME, fetch=unused_fetch, fetch_json=fetch_json)

    assert [url for url, _headers in called] == [
        "https://api.x.com/2/users/by/username/xdevelopers",
        "https://api.x.com/2/users/2244994945/tweets?max_results=20&tweet.fields=created_at&exclude=retweets,replies",
    ]
    assert called[0][1] == {"Authorization": "Bearer test-token"}
    assert result.updates[0].url == "https://x.com/xdevelopers/status/1"


def test_collect_updates_reports_missing_twitter_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)
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

    result = collect_updates(payload, timeframe=ALL_TIMEFRAME, fetch=unused_fetch, fetch_json=unused_fetch_json)

    assert result.updates == []
    assert result.errors[0].source_id == "x"
    assert result.errors[0].error == "Twitter bearer token is required for twitter_account sources"


def test_collect_updates_uses_spotify_show_episodes_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPOTIFY_BEARER_TOKEN", "spotify-token")
    called: list[tuple[str, Mapping[str, str]]] = []

    def fetch_json(url: str, headers: Mapping[str, str]) -> dict[str, object]:
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
                    "sources": [{"type": "spotify_podcast", "url": "https://open.spotify.com/show/show-one"}],
                }
            ]
        }
    )

    result = collect_updates(payload, timeframe=ALL_TIMEFRAME, fetch=unused_fetch, fetch_json=fetch_json)

    assert called == [
        (
            "https://api.spotify.com/v1/shows/show-one/episodes?limit=20&market=US",
            {"Authorization": "Bearer spotify-token"},
        )
    ]
    assert result.updates[0].title == "Episode one"
    assert result.updates[0].url == "https://open.spotify.com/episode/episode-one"


def test_source_identifier_helpers_accept_common_forms() -> None:
    assert twitter_username("https://twitter.com/openai") == "openai"
    assert twitter_username("@openai") == "openai"
    assert spotify_show_id("spotify:show:show-id") == "show-id"
    assert spotify_show_id("https://open.spotify.com/show/show-id?si=abc") == "show-id"
