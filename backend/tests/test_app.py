import importlib
from datetime import UTC, datetime, timedelta

import pytest
from cachetools import TTLCache
from fastapi.testclient import TestClient

from learning_engine.app import app, create_app
from learning_engine.models import (
    CollectedUpdate,
    CollectionError,
    InterestSource,
    InterestsPayload,
    Update,
    UpdatesResponse,
)

app_module = importlib.import_module("learning_engine.app")
collector_module = importlib.import_module("learning_engine.collector")

HTTP_OK = 200
HTTP_UNPROCESSABLE_ENTITY = 422
EXPECTED_EXPIRED_CALLS = 2


def _published_now() -> str:
    return (datetime.now(UTC) - timedelta(seconds=1)).isoformat()


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


def test_updates_rejects_non_positive_days() -> None:
    client = TestClient(app)

    response = client.get("/api/updates?days=0")

    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY


def _payload(source_url: str = "https://example.com/feed.xml") -> InterestsPayload:
    return InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "id": "typescript",
                    "name": "TypeScript",
                    "sources": [
                        {"id": "feed", "type": "feed", "url": source_url},
                    ],
                }
            ]
        }
    )


def _read_default_payload() -> InterestsPayload:
    return _payload()


def _response(title: str, *, error: str | None = None) -> UpdatesResponse:
    return UpdatesResponse(
        sources_checked=1,
        since="2026-05-15T12:00:00Z",
        updates=[
            Update(
                interest_id="typescript",
                interest_name="TypeScript",
                source_id="feed",
                source_url="https://example.com/feed.xml",
                source_type="feed",
                title=title,
                url=f"https://example.com/{title}",
                published_at="2026-05-15T12:00:00Z",
            )
        ],
        errors=[]
        if error is None
        else [
            CollectionError(
                interest_id="typescript",
                interest_name="TypeScript",
                source_id="feed",
                source_url="https://example.com/feed.xml",
                source_type="feed",
                error=error,
            )
        ],
    )


def _collected_update(title: str) -> CollectedUpdate:
    return CollectedUpdate(
        title=title,
        url=f"https://example.com/{title}",
        published_at=_published_now(),
    )


@pytest.mark.parametrize(("query", "expected_path"), [(None, "/api/updates"), (7, "/api/updates?days=7")])
def test_updates_endpoint_reuses_cached_response_for_five_minutes(
    monkeypatch: pytest.MonkeyPatch,
    query: int | None,
    expected_path: str,
) -> None:
    calls: list[str] = []

    async def collect_source_updates(source: InterestSource, *_args: object) -> list[CollectedUpdate]:
        calls.append(source.url)
        return [_collected_update(f"call-{len(calls)}")]

    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(collector_module, "_collect_source_updates", collect_source_updates)
    client = TestClient(create_app())

    path = "/api/updates" if query is None else f"/api/updates?days={query}"
    first = client.get(path)
    second = client.get(path)

    assert first.status_code == HTTP_OK
    assert second.status_code == HTTP_OK
    assert path == expected_path
    assert calls == ["https://example.com/feed.xml"]
    assert first.json()["updates"] == second.json()["updates"]
    assert second.json()["updates"][0]["title"] == "call-1"


def test_create_app_uses_cachetools_ttl_cache() -> None:
    api = create_app()

    assert isinstance(api.state.source_updates_cache, TTLCache)
    assert api.state.source_updates_cache.maxsize == app_module.SOURCE_UPDATES_CACHE_MAX_ENTRIES
    assert api.state.source_updates_cache.ttl == app_module.SOURCE_UPDATES_CACHE_TTL.total_seconds()


def test_updates_endpoint_expires_cached_response_after_five_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 1000.0
    calls = 0

    def monotonic() -> float:
        return current_time

    async def collect_source_updates(_source: object, *_args: object) -> list[CollectedUpdate]:
        nonlocal calls
        calls += 1
        return [_collected_update(f"call-{calls}")]

    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(collector_module, "_collect_source_updates", collect_source_updates)
    api = create_app()
    api.state.source_updates_cache = TTLCache(maxsize=128, ttl=300, timer=monotonic)
    client = TestClient(api)

    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
    current_time += 301
    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-2"
    assert calls == EXPECTED_EXPIRED_CALLS


def test_updates_endpoint_cache_key_includes_selected_days(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def collect_source_updates(source: InterestSource, *_args: object) -> list[CollectedUpdate]:
        calls.append(source.url)
        return [_collected_update(f"call-{len(calls)}")]

    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(collector_module, "_collect_source_updates", collect_source_updates)
    client = TestClient(create_app())

    first = client.get("/api/updates?days=7")
    second = client.get("/api/updates?days=30")
    repeated_first = client.get("/api/updates?days=7")

    assert calls == ["https://example.com/feed.xml", "https://example.com/feed.xml"]
    assert first.json()["updates"][0]["title"] == "call-1"
    assert second.json()["updates"][0]["title"] == "call-2"
    assert repeated_first.json()["updates"][0]["title"] == "call-1"


def test_saving_interests_keeps_source_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_payloads: list[InterestsPayload] = []
    current_payload = _payload()
    calls: list[str] = []

    def read_interests() -> InterestsPayload:
        return saved_payloads[-1] if saved_payloads else current_payload

    def write_interests(payload: InterestsPayload) -> None:
        saved_payloads.append(payload)

    async def collect_source_updates(source: InterestSource, *_args: object) -> list[CollectedUpdate]:
        calls.append(source.url)
        return [_collected_update(f"call-{len(calls)}")]

    monkeypatch.setattr(app_module, "read_interests", read_interests)
    monkeypatch.setattr(app_module, "write_interests", write_interests)
    monkeypatch.setattr(collector_module, "_collect_source_updates", collect_source_updates)
    client = TestClient(create_app())

    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
    saved = _payload().model_dump(mode="json", by_alias=True)
    client.post("/api/interests", json=saved)
    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
    assert calls == ["https://example.com/feed.xml"]


def test_updates_endpoint_caches_partial_results_with_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def collect_source_updates(_source: object, *_args: object) -> list[CollectedUpdate]:
        nonlocal calls
        calls += 1
        raise ValueError("network down")

    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(collector_module, "_collect_source_updates", collect_source_updates)
    client = TestClient(create_app())

    first = client.get("/api/updates")
    second = client.get("/api/updates")

    assert calls == 1
    assert first.json() == second.json()
    assert second.json()["errors"][0]["error"] == "network down"
