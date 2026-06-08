from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from learning_engine.domain.interests import InterestsPayload
from learning_engine.infrastructure.storage import InterestStore


def test_interest_store_reads_and_normalizes_interests(tmp_path: Path) -> None:
    path = tmp_path / "interests.json"
    path.write_text(
        json.dumps(
            {
                "interests": [
                    {
                        "id": " typescript ",
                        "name": " TypeScript ",
                        "sources": [
                            {
                                "type": "feed",
                                "url": " https://example.com/feed.xml ",
                                "ignoreKeywords": "nightly, beta",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    interests = InterestStore(path).read_interests()

    assert interests.interests[0].id == "typescript"
    assert interests.interests[0].name == "TypeScript"
    assert interests.interests[0].sources[0].url == "https://example.com/feed.xml"
    assert interests.interests[0].sources[0].ignore_keywords == ["nightly", "beta"]
    assert json.loads(path.read_text(encoding="utf-8")) == interests.model_dump(mode="json", by_alias=True)


def test_interest_store_writes_interests_with_json_aliases(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "interests.json"
    interests = InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "name": "TypeScript",
                    "sources": [
                        {
                            "type": "feed",
                            "url": "https://example.com/feed.xml",
                            "imageUrl": "https://example.com/image.png",
                        }
                    ],
                }
            ]
        }
    )

    InterestStore(path).write_interests(interests)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["interests"][0]["sources"][0]["imageUrl"] == "https://example.com/image.png"
    assert "image_url" not in saved["interests"][0]["sources"][0]


def test_interest_store_rejects_invalid_data(tmp_path: Path) -> None:
    path = tmp_path / "interests.json"
    path.write_text(json.dumps({"interests": [{"sources": [{"type": "rss", "url": ""}]}]}), encoding="utf-8")

    with pytest.raises(ValidationError):
        InterestStore(path).read_interests()
