from __future__ import annotations

import pytest
from pydantic import ValidationError

from learning_engine.domain.models import CollectedUpdate, Interest, InterestSource, Update


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
        InterestSource.model_validate({"type": "Spotify Podcasts", "url": "spotify:show:abc"}).type == "spotify_podcast"
    )


def test_source_accepts_optional_image_url_with_camel_case_alias() -> None:
    source = InterestSource.model_validate(
        {
            "type": "feed",
            "url": "https://example.com/feed.xml",
            "imageUrl": " https://example.com/logo.png ",
        }
    )

    assert source.image_url == "https://example.com/logo.png"
    assert source.model_dump(mode="json", by_alias=True)["imageUrl"] == "https://example.com/logo.png"


def test_source_preserves_blank_image_url_as_empty_string() -> None:
    source = InterestSource.model_validate({"type": "feed", "url": "https://example.com/feed.xml", "imageUrl": "  "})

    assert source.image_url == ""


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
