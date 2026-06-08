import importlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from cachetools import TTLCache
from fastapi import FastAPI
from fastapi.testclient import TestClient

from learning_engine.application.resolve_source_image import (
    SourceImageConfigurationError,
    SourceImageProviderError,
    SourceImageProviderUnavailableError,
)
from learning_engine.application.responses import CollectionError, UpdatesResponse
from learning_engine.domain.interests import InterestSource, InterestsPayload
from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import SourceInterest, SourceUpdate, Update
from learning_engine.presentation.app import app, create_app

router_module = importlib.import_module("learning_engine.presentation.interests_router")

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_UNPROCESSABLE_ENTITY = 422
EXPECTED_EXPIRED_CALLS = 2
EXPECTED_RETRY_CALLS = 2


async def no_source_image(*_args: object) -> str | None:
    return None


class StubInterestRepository:
    def __init__(self, payload: InterestsPayload | None = None) -> None:
        self.saved_payloads: list[InterestsPayload] = []
        self._payload = payload or _payload()

    def ensure_data_file(self) -> None:
        return None

    def read_interests(self) -> InterestsPayload:
        return self.saved_payloads[-1] if self.saved_payloads else self._payload

    def write_interests(self, payload: InterestsPayload) -> None:
        self.saved_payloads.append(payload)


class StubSourceImageProvider:
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
    ) -> str | None:
        return await no_source_image(source_type, source_url)


class StubSourceUpdateCollector:
    def __init__(self, collect_source_updates: Callable[[InterestSource], Awaitable[list[SourceUpdate]]]) -> None:
        self._collect_source_updates = collect_source_updates

    async def collect_source_updates(self, source: InterestSource) -> list[SourceUpdate]:
        return await self._collect_source_updates(source)


def _create_test_app(
    *,
    repository: StubInterestRepository | None = None,
    source_update_collector: StubSourceUpdateCollector | None = None,
) -> FastAPI:
    api = create_app()
    api.state.interest_repository = repository or StubInterestRepository()
    api.state.source_image_provider_factory = lambda _fetcher: StubSourceImageProvider()
    if source_update_collector is not None:
        api.state.source_update_collector_factory = lambda _fetcher: source_update_collector
    return api


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


def test_source_image_endpoint_returns_resolved_image(monkeypatch: pytest.MonkeyPatch) -> None:
    async def resolve_source_image(
        source_type: str,
        source_url: str,
        *_args: object,
    ) -> str | None:
        assert source_type == "youtube_channel"
        assert source_url == "@example"
        return "https://yt.example/avatar.jpg"

    monkeypatch.setattr(router_module, "resolve_source_image", resolve_source_image)

    with TestClient(_create_test_app()) as client:
        response = client.post("/api/source-image", json={"type": "youtube_channel", "url": " @example "})

    assert response.status_code == HTTP_OK
    assert response.json() == {"imageUrl": "https://yt.example/avatar.jpg"}


def test_source_image_endpoint_returns_null_on_resolver_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    async def resolve_source_image(*_args: object) -> str | None:
        return None

    monkeypatch.setattr(router_module, "resolve_source_image", resolve_source_image)

    with TestClient(_create_test_app()) as client:
        response = client.post("/api/source-image", json={"type": "feed", "url": "https://example.com/feed.xml"})

    assert response.status_code == HTTP_OK
    assert response.json() == {"imageUrl": None}


@pytest.mark.parametrize(
    ("resolver_error", "expected_status", "expected_detail"),
    [
        (
            SourceImageConfigurationError("Spotify bearer token is not configured"),
            HTTP_BAD_REQUEST,
            "Spotify bearer token is not configured",
        ),
        (
            SourceImageProviderUnavailableError("Spotify metadata provider is unavailable"),
            HTTP_SERVICE_UNAVAILABLE,
            "Spotify metadata provider is unavailable",
        ),
        (
            SourceImageProviderError("Spotify show metadata did not include an images list"),
            HTTP_BAD_GATEWAY,
            "Spotify show metadata did not include an images list",
        ),
        (
            RuntimeError("unexpected resolver failure"),
            HTTP_INTERNAL_SERVER_ERROR,
            "Could not resolve source image",
        ),
    ],
)
def test_source_image_endpoint_returns_matching_error_for_resolver_failures(
    monkeypatch: pytest.MonkeyPatch,
    resolver_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    async def resolve_source_image(*_args: object) -> str | None:
        raise resolver_error

    monkeypatch.setattr(router_module, "resolve_source_image", resolve_source_image)

    with TestClient(_create_test_app()) as client:
        response = client.post("/api/source-image", json={"type": "spotify_podcast", "url": "spotify:show:show-one"})

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_source_image_endpoint_does_not_persist_resolved_image(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload()
    repository = StubInterestRepository(payload)

    async def resolve_source_image(*_args: object) -> str | None:
        return "https://example.com/dynamic.png"

    monkeypatch.setattr(router_module, "resolve_source_image", resolve_source_image)

    with TestClient(_create_test_app(repository=repository)) as client:
        assert client.post(
            "/api/source-image", json={"type": "feed", "url": "https://example.com/feed.xml"}
        ).json() == {"imageUrl": "https://example.com/dynamic.png"}
        saved = payload.model_dump(mode="json", by_alias=True)
        client.post("/api/interests", json=saved)

        assert client.get("/api/interests").json()["interests"][0]["sources"][0]["imageUrl"] is None


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
                source_interest=SourceInterest(
                    interest_id="typescript",
                    interest_name="TypeScript",
                    source_id="feed",
                    source_label="Source",
                    source_url="https://example.com/feed.xml",
                    source_type="feed",
                ),
                title=title,
                url=f"https://example.com/{title}",
                published_at=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
            )
        ],
        errors=[]
        if error is None
        else [
            CollectionError(
                interest_id="typescript",
                interest_name="TypeScript",
                source_id="feed",
                source_label="Source",
                source_url="https://example.com/feed.xml",
                source_type="feed",
                error=error,
            )
        ],
    )


def _collected_update(title: str) -> SourceUpdate:
    return SourceUpdate(
        title=title,
        url=f"https://example.com/{title}",
        published_at=datetime.now(UTC) - timedelta(seconds=1),
    )


@pytest.mark.parametrize(("query", "expected_path"), [(None, "/api/updates"), (7, "/api/updates?days=7")])
def test_updates_endpoint_reuses_cached_response_for_five_minutes(
    monkeypatch: pytest.MonkeyPatch,
    query: int | None,
    expected_path: str,
) -> None:
    calls: list[str] = []

    async def collect_source_updates(source: InterestSource, *_args: object) -> list[SourceUpdate]:
        calls.append(source.url)
        return [_collected_update(f"call-{len(calls)}")]

    path = "/api/updates" if query is None else f"/api/updates?days={query}"
    api = _create_test_app(
        repository=StubInterestRepository(_read_default_payload()),
        source_update_collector=StubSourceUpdateCollector(collect_source_updates),
    )
    with TestClient(api) as client:
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
    app_module = importlib.import_module("learning_engine.presentation.app")
    assert api.state.source_updates_cache.maxsize == app_module.SOURCE_UPDATES_CACHE_MAX_ENTRIES
    assert api.state.source_updates_cache.ttl == app_module.SOURCE_UPDATES_CACHE_TTL.total_seconds()


def test_updates_endpoint_expires_cached_response_after_five_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    current_time = 1000.0
    calls = 0

    def monotonic() -> float:
        return current_time

    async def collect_source_updates(_source: object, *_args: object) -> list[SourceUpdate]:
        nonlocal calls
        calls += 1
        return [_collected_update(f"call-{calls}")]

    api = _create_test_app(
        repository=StubInterestRepository(_read_default_payload()),
        source_update_collector=StubSourceUpdateCollector(collect_source_updates),
    )
    api.state.source_updates_cache = TTLCache(maxsize=128, ttl=300, timer=monotonic)

    with TestClient(api) as client:
        assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
        current_time += 301
        assert client.get("/api/updates").json()["updates"][0]["title"] == "call-2"
    assert calls == EXPECTED_EXPIRED_CALLS


def test_updates_endpoint_cache_key_includes_selected_days(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def collect_source_updates(source: InterestSource, *_args: object) -> list[SourceUpdate]:
        calls.append(source.url)
        return [_collected_update(f"call-{len(calls)}")]

    api = _create_test_app(
        repository=StubInterestRepository(_read_default_payload()),
        source_update_collector=StubSourceUpdateCollector(collect_source_updates),
    )
    with TestClient(api) as client:
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
    repository = StubInterestRepository(_payload())
    calls: list[str] = []

    async def collect_source_updates(source: InterestSource, *_args: object) -> list[SourceUpdate]:
        calls.append(source.url)
        return [_collected_update(f"call-{len(calls)}")]

    api = _create_test_app(
        repository=repository,
        source_update_collector=StubSourceUpdateCollector(collect_source_updates),
    )
    with TestClient(api) as client:
        assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
        saved = _payload().model_dump(mode="json", by_alias=True)
        client.post("/api/interests", json=saved)
        assert client.get("/api/updates").json()["updates"][0]["title"] == "call-1"
    assert calls == ["https://example.com/feed.xml"]


def test_updates_endpoint_retries_source_errors_instead_of_caching_them(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def collect_source_updates(_source: object, *_args: object) -> list[SourceUpdate]:
        nonlocal calls
        calls += 1
        raise ValueError("network down")

    api = _create_test_app(
        repository=StubInterestRepository(_read_default_payload()),
        source_update_collector=StubSourceUpdateCollector(collect_source_updates),
    )
    with TestClient(api) as client:
        with pytest.raises(ValueError, match="network down"):
            client.get("/api/updates")
        with pytest.raises(ValueError, match="network down"):
            client.get("/api/updates")

    assert calls == EXPECTED_RETRY_CALLS
