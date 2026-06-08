from __future__ import annotations

import pytest
from pydantic import ValidationError

from learning_engine.domain.interests import Interest, InterestSource
from learning_engine.domain.updates import SourceUpdate, Update


def test_update_enriches_generic_collected_update_without_feed_specific_base() -> None:
    assert issubclass(Update, SourceUpdate)
    assert Update.__bases__ == (SourceUpdate,)


def test_source_type_requires_canonical_values() -> None:
    assert InterestSource.model_validate({"type": "feed", "url": "https://example.com/feed.xml"}).type == "feed"

    with pytest.raises(ValidationError, match="Source type must be one of"):
        InterestSource.model_validate({"type": "RSS", "url": "https://example.com/feed.xml"})

    with pytest.raises(ValidationError, match="Source type must be one of"):
        InterestSource.model_validate({"type": "youtube-channel", "url": "@example"})


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
