import importlib

import pytest
from fastapi.testclient import TestClient

from learning_engine.app import UpdatesCache, app, create_app
from learning_engine.models import CollectionError, InterestsPayload, Update, UpdatesResponse
from learning_engine.timeframe import Timeframe

app_module = importlib.import_module("learning_engine.app")

HTTP_OK = 200
HTTP_UNPROCESSABLE_ENTITY = 422
EXPECTED_EXPIRED_CALLS = 2


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


@pytest.mark.parametrize(("query", "expected_path"), [(None, "/api/updates"), (7, "/api/updates?days=7")])
def test_updates_endpoint_reuses_cached_response_for_five_minutes(
    monkeypatch: pytest.MonkeyPatch,
    query: int | None,
    expected_path: str,
) -> None:
    current_time = 1000.0
    calls: list[str] = []

    def monotonic() -> float:
        return current_time

    async def collect_updates(
        payload: InterestsPayload,
        **_kwargs: object,
    ) -> UpdatesResponse:
        calls.append(payload.interests[0].sources[0].url)
        return _response(f"call-{len(calls)}")

    monkeypatch.setattr(app_module, "monotonic", monotonic)
    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(app_module, "collect_updates", collect_updates)
    client = TestClient(create_app())

    path = "/api/updates" if query is None else f"/api/updates?days={query}"
    first = client.get(path)
    second = client.get(path)

    assert first.status_code == HTTP_OK
    assert second.status_code == HTTP_OK
    assert path == expected_path
    assert calls == ["https://example.com/feed.xml"]
    assert first.json() == second.json()
    assert second.json()["updates"][0]["title"] == "call-1"


def test_updates_cache_prunes_expired_entries_before_storing(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 1000.0

    def monotonic() -> float:
        return current_time

    monkeypatch.setattr(app_module, "monotonic", monotonic)
    cache = UpdatesCache(ttl_seconds=300)

    cache.set((7,), _response("old"))
    current_time += 301
    cache.set((30,), _response("new"))

    assert cache.get((7,)) is None
    assert cache.get((30,)) == _response("new")


def test_updates_cache_evicts_earliest_expiring_entry_when_full(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 1000.0

    def monotonic() -> float:
        return current_time

    monkeypatch.setattr(app_module, "monotonic", monotonic)
    cache = UpdatesCache(ttl_seconds=300, max_entries=2)

    cache.set((7,), _response("oldest"))
    current_time += 1
    cache.set((14,), _response("middle"))
    current_time += 1
    cache.set((30,), _response("newest"))

    assert cache.get((7,)) is None
    assert cache.get((14,)) == _response("middle")
    assert cache.get((30,)) == _response("newest")


def test_updates_endpoint_expires_cached_response_after_five_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 1000.0
    calls = 0

    def monotonic() -> float:
        return current_time

    async def collect_updates(
        _payload: InterestsPayload,
        **_kwargs: object,
    ) -> UpdatesResponse:
        nonlocal calls
        calls += 1
        return _response(f"call-{calls}")

    monkeypatch.setattr(app_module, "monotonic", monotonic)
    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(app_module, "collect_updates", collect_updates)
    client = TestClient(create_app())

    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
    current_time += 301
    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-2"
    assert calls == EXPECTED_EXPIRED_CALLS


def test_updates_endpoint_cache_key_includes_selected_days(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def collect_updates(
        _payload: InterestsPayload,
        **kwargs: object,
    ) -> UpdatesResponse:
        timeframe = kwargs["timeframe"]
        assert isinstance(timeframe, Timeframe)
        calls.append(str(timeframe.length.days))
        return _response(f"call-{len(calls)}")

    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(app_module, "collect_updates", collect_updates)
    client = TestClient(create_app())

    first = client.get("/api/updates?days=7")
    second = client.get("/api/updates?days=30")
    repeated_first = client.get("/api/updates?days=7")

    assert calls == ["7", "30"]
    assert first.json()["updates"][0]["title"] == "call-1"
    assert second.json()["updates"][0]["title"] == "call-2"
    assert repeated_first.json()["updates"][0]["title"] == "call-1"


def test_saving_interests_invalidates_updates_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    saved_payloads: list[InterestsPayload] = []
    current_payload = _payload("https://example.com/first.xml")
    calls: list[str] = []

    def read_interests() -> InterestsPayload:
        return saved_payloads[-1] if saved_payloads else current_payload

    def write_interests(payload: InterestsPayload) -> None:
        saved_payloads.append(payload)

    async def collect_updates(payload: InterestsPayload, **_kwargs: object) -> UpdatesResponse:
        calls.append(payload.interests[0].sources[0].url)
        return _response(f"call-{len(calls)}")

    monkeypatch.setattr(app_module, "read_interests", read_interests)
    monkeypatch.setattr(app_module, "write_interests", write_interests)
    monkeypatch.setattr(app_module, "collect_updates", collect_updates)
    client = TestClient(create_app())

    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
    saved = _payload("https://example.com/second.xml").model_dump(mode="json", by_alias=True)
    client.post("/api/interests", json=saved)
    assert client.get("/api/updates").json()["updates"][0]["title"] == "call-2"
    assert calls == ["https://example.com/first.xml", "https://example.com/second.xml"]


def test_updates_endpoint_caches_partial_results_with_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def collect_updates(
        _payload: InterestsPayload,
        **_kwargs: object,
    ) -> UpdatesResponse:
        nonlocal calls
        calls += 1
        return _response(f"call-{calls}", error="network down")

    monkeypatch.setattr(app_module, "read_interests", _read_default_payload)
    monkeypatch.setattr(app_module, "collect_updates", collect_updates)
    client = TestClient(create_app())

    first = client.get("/api/updates")
    second = client.get("/api/updates")

    assert calls == 1
    assert first.json() == second.json()
    assert second.json()["errors"][0]["error"] == "network down"
