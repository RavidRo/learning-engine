from __future__ import annotations

from learning_engine.infrastructure.storage import DEFAULT_DATA


def test_default_data_contains_typescript_sources() -> None:
    interests = DEFAULT_DATA.model_dump(mode="json", by_alias=True)["interests"]

    assert [item["id"] for item in interests] == ["typescript"]
    assert interests[0]["description"]
    assert [source["type"] for source in interests[0]["sources"]] == ["page", "feed"]
    assert "type" not in interests[0]
    assert "official_feed_url" not in interests[0]
