import importlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from time import perf_counter

import httpx
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
from learning_engine.domain.collections import (
    CollectionId,
    CollectionNotFoundError,
    Collections,
    SavedCollectionUpdate,
    SavedUpdateSnapshot,
    UpdateCollection,
)
from learning_engine.domain.interests import Interests, InterestSource
from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import SourceInterest, SourceUpdate, Update
from learning_engine.presentation.app import app, create_app

router_module = importlib.import_module("learning_engine.presentation.interests_router")

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
EXPECTED_EXPIRED_CALLS = 2
EXPECTED_RETRY_CALLS = 2
UPDATES_LOAD_BUDGET_SECONDS = 4
UPDATE_KEY_LENGTH = 64
MCP_HEADERS = {
    "Authorization": "Bearer mcp-secret",
    "Accept": "application/json, text/event-stream",
}


async def no_source_image(*_args: object) -> str | None:
    return None


class StubInterestRepository:
    def __init__(self, payload: Interests | None = None) -> None:
        self.saved_payloads: list[Interests] = []
        self._payload = payload or _payload()
        self.read_calls = 0

    def ensure_data_store(self) -> None:
        return None

    def read_interests(self) -> Interests:
        self.read_calls += 1
        return self.saved_payloads[-1] if self.saved_payloads else self._payload

    def write_interests(self, payload: Interests) -> None:
        self.saved_payloads.append(payload)


class StubCollectionRepository:
    def __init__(self) -> None:
        self.saved_updates: dict[tuple[CollectionId, str], SavedCollectionUpdate] = {}
        self.removed: list[tuple[CollectionId, str]] = []

    def ensure_data_store(self) -> None:
        return None

    def list_collections(self) -> Collections:
        saved_updates_by_collection = {
            "see-later": [
                saved_update
                for (
                    collection_id,
                    _update_key,
                ), saved_update in self.saved_updates.items()
                if collection_id == "see-later"
            ],
            "liked": [
                saved_update
                for (
                    collection_id,
                    _update_key,
                ), saved_update in self.saved_updates.items()
                if collection_id == "liked"
            ],
        }
        return Collections(
            collections=[
                UpdateCollection(
                    id="see-later",
                    name="See Later",
                    saved_updates=sorted(
                        saved_updates_by_collection["see-later"],
                        key=lambda saved_update: saved_update.saved_at,
                        reverse=True,
                    ),
                ),
                UpdateCollection(
                    id="liked",
                    name="Liked",
                    saved_updates=sorted(
                        saved_updates_by_collection["liked"],
                        key=lambda saved_update: saved_update.saved_at,
                        reverse=True,
                    ),
                ),
            ]
        )

    def save_update_to_collection(
        self,
        collection_id: CollectionId,
        update_key: str,
        update: SavedUpdateSnapshot,
        saved_at: datetime,
    ) -> SavedCollectionUpdate:
        if collection_id not in {"see-later", "liked"}:
            raise CollectionNotFoundError(f"Collection not found: {collection_id}")
        saved_update = self.saved_updates.get((collection_id, update_key))
        if saved_update is not None:
            return saved_update
        saved_update = SavedCollectionUpdate(update_key=update_key, saved_at=saved_at, update=update)
        self.saved_updates[(collection_id, update_key)] = saved_update
        return saved_update

    def remove_update_from_collection(self, collection_id: CollectionId, update_key: str) -> None:
        if collection_id not in {"see-later", "liked"}:
            raise CollectionNotFoundError(f"Collection not found: {collection_id}")
        self.removed.append((collection_id, update_key))
        self.saved_updates.pop((collection_id, update_key), None)


class StubSourceImageProvider:
    async def resolve_source_image(
        self,
        source_type: SourceType,
        source_url: str,
    ) -> str | None:
        return await no_source_image(source_type, source_url)


class StubSourceUpdateCollector:
    def __init__(
        self,
        collect_source_updates: Callable[[InterestSource], Awaitable[list[SourceUpdate]]],
    ) -> None:
        self._collect_source_updates = collect_source_updates

    async def collect_source_updates(self, source: InterestSource) -> list[SourceUpdate]:
        return await self._collect_source_updates(source)


def _create_test_app(
    *,
    repository: StubInterestRepository | None = None,
    collection_repository: StubCollectionRepository | None = None,
    source_update_collector: StubSourceUpdateCollector | None = None,
) -> FastAPI:
    api = create_app()
    api.state.interest_repository = repository or StubInterestRepository()
    api.state.collection_repository = collection_repository or StubCollectionRepository()
    api.state.source_image_provider_factory = lambda _fetcher: StubSourceImageProvider()
    if source_update_collector is not None:
        api.state.source_update_collector_factory = lambda _fetcher: source_update_collector
    return api


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


def test_source_image_endpoint_returns_resolved_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_source_image_endpoint_returns_null_on_resolver_miss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def resolve_source_image(*_args: object) -> str | None:
        return None

    monkeypatch.setattr(router_module, "resolve_source_image", resolve_source_image)

    with TestClient(_create_test_app()) as client:
        response = client.post(
            "/api/source-image",
            json={"type": "feed", "url": "https://example.com/feed.xml"},
        )

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
        response = client.post(
            "/api/source-image",
            json={"type": "spotify_podcast", "url": "spotify:show:show-one"},
        )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_source_image_endpoint_does_not_persist_resolved_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload()
    repository = StubInterestRepository(payload)

    async def resolve_source_image(*_args: object) -> str | None:
        return "https://example.com/dynamic.png"

    monkeypatch.setattr(router_module, "resolve_source_image", resolve_source_image)

    with TestClient(_create_test_app(repository=repository)) as client:
        assert client.post(
            "/api/source-image",
            json={"type": "feed", "url": "https://example.com/feed.xml"},
        ).json() == {"imageUrl": "https://example.com/dynamic.png"}
        saved = payload.model_dump(mode="json", by_alias=True)
        client.post("/api/interests", json=saved)

        assert client.get("/api/interests").json()["interests"][0]["sources"][0]["imageUrl"] is None


def test_export_interests_returns_versioned_envelope_with_all_stored_interests() -> None:
    repository = StubInterestRepository(_payload_with_archived_interest())

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.get("/api/interests/export")

    assert response.status_code == HTTP_OK
    payload = response.json()
    assert payload["schemaVersion"] == 1
    assert isinstance(payload["exportedAt"], str)
    assert [interest["id"] for interest in payload["interests"]] == [
        "typescript",
        "archived",
    ]
    assert payload["interests"][1]["deletedAt"] == "2026-06-12T10:00:00Z"
    assert payload["interests"][1]["enabled"] is False
    assert payload["interests"][1]["sources"][0]["deletedAt"] == "2026-06-12T10:00:00Z"


def test_import_interests_replaces_all_stored_interests() -> None:
    repository = StubInterestRepository(_payload())
    imported = {
        "schemaVersion": 1,
        "exportedAt": "2026-06-13T13:00:00Z",
        "interests": [
            {
                "id": "python",
                "name": "Python",
                "priority": "high",
                "sources": [
                    {
                        "id": "python-feed",
                        "type": "feed",
                        "url": "https://python.example/feed.xml",
                    }
                ],
            }
        ],
    }

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.post("/api/interests/import", json=imported)
        saved = client.get("/api/interests")

    assert response.status_code == HTTP_OK
    assert response.json()["saved"]["interests"][0]["id"] == "python"
    assert saved.json()["interests"][0]["id"] == "python"
    assert len(repository.saved_payloads) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"interests": []},
        {"schemaVersion": 2, "exportedAt": "2026-06-13T13:00:00Z", "interests": []},
        {
            "schemaVersion": 1,
            "exportedAt": "2026-06-13T13:00:00Z",
            "interests": [{"sources": [{"type": "feed"}]}],
        },
    ],
)
def test_import_interests_rejects_invalid_envelope_without_writing(
    payload: dict[str, object],
) -> None:
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.post("/api/interests/import", json=payload)

    assert response.status_code == HTTP_BAD_REQUEST
    assert response.json() == {"detail": "Invalid interest export file"}
    assert repository.saved_payloads == []


def test_import_interests_rejects_malformed_json_without_writing() -> None:
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.post(
            "/api/interests/import",
            content="{",
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == HTTP_BAD_REQUEST
    assert response.json() == {"detail": "Invalid interest export JSON"}
    assert repository.saved_payloads == []


def test_collections_endpoint_lists_fixed_collections() -> None:
    with TestClient(_create_test_app()) as client:
        response = client.get("/api/collections")

    assert response.status_code == HTTP_OK
    assert [(collection["id"], collection["name"]) for collection in response.json()["collections"]] == [
        ("see-later", "See Later"),
        ("liked", "Liked"),
    ]
    assert response.json()["collections"][0]["saved_updates"] == []


def test_save_collection_update_stores_snapshot_and_returns_key() -> None:
    collection_repository = StubCollectionRepository()

    with TestClient(_create_test_app(collection_repository=collection_repository)) as client:
        response = client.post(
            "/api/collections/see-later/updates",
            json={"update": _saved_update_payload()},
        )

    assert response.status_code == HTTP_OK
    payload = response.json()["saved_update"]
    assert isinstance(payload["saved_at"], str)
    assert len(payload["update_key"]) == UPDATE_KEY_LENGTH
    assert payload["update"]["title"] == "Saved update"
    assert payload["update"]["source_interest"]["source_id"] == "feed"
    assert len(collection_repository.saved_updates) == 1


def test_repeated_collection_save_preserves_original_saved_update() -> None:
    collection_repository = StubCollectionRepository()

    with TestClient(_create_test_app(collection_repository=collection_repository)) as client:
        first = client.post(
            "/api/collections/liked/updates",
            json={"update": _saved_update_payload(title="Original")},
        )
        second = client.post(
            "/api/collections/liked/updates",
            json={"update": _saved_update_payload(title="Changed")},
        )

    assert first.status_code == HTTP_OK
    assert second.status_code == HTTP_OK
    assert second.json() == first.json()
    assert len(collection_repository.saved_updates) == 1


def test_collections_endpoint_returns_saved_updates_ordered_by_save_time() -> None:
    collection_repository = StubCollectionRepository()

    with TestClient(_create_test_app(collection_repository=collection_repository)) as client:
        client.post(
            "/api/collections/see-later/updates",
            json={"update": _saved_update_payload(url="https://e.test/old")},
        )
        client.post(
            "/api/collections/see-later/updates",
            json={"update": _saved_update_payload(url="https://e.test/new")},
        )
        response = client.get("/api/collections")

    assert response.status_code == HTTP_OK
    saved_updates = response.json()["collections"][0]["saved_updates"]
    assert [saved_update["update"]["url"] for saved_update in saved_updates] == [
        "https://e.test/new",
        "https://e.test/old",
    ]


def test_remove_collection_update_removes_one_saved_update() -> None:
    collection_repository = StubCollectionRepository()

    with TestClient(_create_test_app(collection_repository=collection_repository)) as client:
        save_response = client.post("/api/collections/liked/updates", json={"update": _saved_update_payload()})
        update_key = save_response.json()["saved_update"]["update_key"]
        remove_response = client.delete(f"/api/collections/liked/updates/{update_key}")

    assert remove_response.status_code == HTTP_OK
    assert remove_response.json() == {"ok": True}
    assert collection_repository.removed == [("liked", update_key)]
    assert collection_repository.saved_updates == {}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/collections/unknown/updates"),
        ("delete", "/api/collections/unknown/updates/update-key"),
    ],
)
def test_collection_endpoints_reject_unknown_collections(method: str, path: str) -> None:
    with TestClient(_create_test_app()) as client:
        if method == "post":
            response = client.post(path, json={"update": _saved_update_payload()})
        else:
            response = client.delete(path)

    assert response.status_code == HTTP_NOT_FOUND
    assert response.json() == {"detail": "Collection not found: unknown"}


def test_updates_rejects_non_positive_days() -> None:
    client = TestClient(app)

    response = client.get("/api/updates?days=0")

    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY


def _payload(source_url: str = "https://example.com/feed.xml") -> Interests:
    return Interests.model_validate(
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


def _payload_with_archived_interest() -> Interests:
    return Interests.model_validate(
        {
            "interests": [
                {
                    "id": "typescript",
                    "name": "TypeScript",
                    "sources": [
                        {
                            "id": "feed",
                            "type": "feed",
                            "url": "https://example.com/feed.xml",
                        }
                    ],
                },
                {
                    "deletedAt": "2026-06-12T10:00:00Z",
                    "enabled": False,
                    "id": "archived",
                    "name": "Archived",
                    "sources": [
                        {
                            "deletedAt": "2026-06-12T10:00:00Z",
                            "id": "archived-feed",
                            "type": "feed",
                            "url": "https://example.com/archived.xml",
                        }
                    ],
                },
            ]
        }
    )


def _saved_update_payload(
    *,
    title: str = "Saved update",
    url: str = "https://e.test/update",
) -> dict[str, object]:
    return {
        "title": title,
        "url": url,
        "summary": "Snapshot",
        "image_url": "https://e.test/image.png",
        "published": "2026-06-12T10:00:00Z",
        "source_interest": {
            "interest_id": "typescript",
            "interest_name": "TypeScript",
            "source_id": "feed",
            "source_label": "TypeScript Feed",
            "source_image_url": "https://e.test/source.png",
            "source_url": "https://e.test/feed.xml",
            "source_type": "feed",
        },
    }


def _mcp_request(request_id: int, method: str, params: dict[str, object] | None = None) -> dict[str, object]:
    request: dict[str, object] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    return request


def _read_default_payload() -> Interests:
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
        errors=(
            []
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
            ]
        ),
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
    assert isinstance(api.state.source_fetch_cache, TTLCache)
    app_module = importlib.import_module("learning_engine.presentation.app")
    assert api.state.source_updates_cache.maxsize == app_module.SOURCE_UPDATES_CACHE_MAX_ENTRIES
    assert api.state.source_updates_cache.ttl == app_module.SOURCE_UPDATES_CACHE_TTL.total_seconds()
    assert api.state.source_fetch_cache.maxsize == app_module.SOURCE_FETCH_CACHE_MAX_ENTRIES
    assert api.state.source_fetch_cache.ttl == app_module.SOURCE_UPDATES_CACHE_TTL.total_seconds()


def test_updates_endpoint_reuses_source_document_for_image_enrichment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module = importlib.import_module("learning_engine.presentation.app")
    original_async_client = httpx.AsyncClient
    called_urls: list[str] = []

    def handle_request(request: httpx.Request) -> httpx.Response:
        called_urls.append(str(request.url))
        return httpx.Response(
            HTTP_OK,
            content=b"""<rss><channel>
            <image><url>https://example.com/source.png</url></image>
            <item><title>Fast update</title><link>https://example.com/update</link>
            <pubDate>Fri, 19 Jun 2026 10:00:00 GMT</pubDate></item>
            </channel></rss>""",
            request=request,
        )

    def async_client(*, timeout: float) -> httpx.AsyncClient:
        return original_async_client(
            timeout=timeout,
            transport=httpx.MockTransport(handle_request),
        )

    monkeypatch.setattr(app_module.httpx, "AsyncClient", async_client)
    api = create_app()
    api.state.interest_repository = StubInterestRepository(_read_default_payload())
    api.state.collection_repository = StubCollectionRepository()

    with TestClient(api) as client:
        started_at = perf_counter()
        response = client.get("/api/updates")
        elapsed = perf_counter() - started_at

    assert response.status_code == HTTP_OK
    assert response.json()["updates"][0]["source_interest"]["source_image_url"] == "https://example.com/source.png"
    assert called_urls == ["https://example.com/feed.xml"]
    assert elapsed < UPDATES_LOAD_BUDGET_SECONDS


def test_mcp_endpoint_lists_tools_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "mcp-secret")
    monkeypatch.delenv("MCP_ALLOWED_ORIGINS", raising=False)
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository), base_url="http://localhost") as client:
        response = client.post("/mcp", headers=MCP_HEADERS, json=_mcp_request(1, "tools/list"))

    assert response.status_code == HTTP_OK
    tool_names = {tool["name"] for tool in response.json()["result"]["tools"]}
    assert {
        "list_interests",
        "create_interest",
        "update_interest",
        "pause_interest",
        "resume_interest",
        "delete_interest",
        "add_source",
        "update_source",
        "pause_source",
        "resume_source",
        "delete_source",
    } <= tool_names


def test_mcp_tool_uses_app_interest_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "mcp-secret")
    monkeypatch.delenv("MCP_ALLOWED_ORIGINS", raising=False)
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository), base_url="http://localhost") as client:
        response = client.post(
            "/mcp",
            headers=MCP_HEADERS,
            json=_mcp_request(1, "tools/call", {"name": "list_interests", "arguments": {}}),
        )

    assert response.status_code == HTTP_OK
    assert response.json()["result"]["structuredContent"]["interests"][0]["id"] == "typescript"
    assert repository.read_calls == 1


def test_mcp_endpoint_returns_unavailable_when_token_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.post(
            "/mcp",
            headers=MCP_HEADERS,
            json=_mcp_request(1, "tools/call", {"name": "list_interests", "arguments": {}}),
        )

    assert response.status_code == HTTP_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "MCP is unavailable because MCP_AUTH_TOKEN is not configured"}
    assert repository.read_calls == 0


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {
            "Authorization": "Bearer wrong",
            "Accept": "application/json, text/event-stream",
        },
    ],
)
def test_mcp_endpoint_rejects_missing_or_invalid_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
    headers: dict[str, str],
) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "mcp-secret")
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.post(
            "/mcp",
            headers=headers,
            json=_mcp_request(1, "tools/call", {"name": "list_interests", "arguments": {}}),
        )

    assert response.status_code == HTTP_UNAUTHORIZED
    assert response.json() == {"detail": "Missing or invalid MCP bearer token"}
    assert repository.read_calls == 0


def test_mcp_endpoint_allows_configured_browser_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "mcp-secret")
    monkeypatch.setenv("MCP_ALLOWED_ORIGINS", "https://app.example.com")

    with TestClient(_create_test_app(), base_url="http://localhost") as client:
        response = client.post(
            "/mcp",
            headers={**MCP_HEADERS, "Origin": "https://app.example.com"},
            json=_mcp_request(1, "tools/list"),
        )

    assert response.status_code == HTTP_OK


@pytest.mark.parametrize("allowed_origins", ["https://app.example.com", ""])
def test_mcp_endpoint_rejects_disallowed_or_unset_browser_origin(
    monkeypatch: pytest.MonkeyPatch,
    allowed_origins: str,
) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "mcp-secret")
    monkeypatch.setenv("MCP_ALLOWED_ORIGINS", allowed_origins)
    repository = StubInterestRepository(_payload())

    with TestClient(_create_test_app(repository=repository)) as client:
        response = client.post(
            "/mcp",
            headers={**MCP_HEADERS, "Origin": "https://evil.example.com"},
            json=_mcp_request(1, "tools/call", {"name": "list_interests", "arguments": {}}),
        )

    assert response.status_code == HTTP_FORBIDDEN
    assert response.json() == {"detail": "MCP browser origin is not allowed"}
    assert repository.read_calls == 0


def test_mcp_endpoint_allows_non_browser_request_without_origin_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "mcp-secret")
    monkeypatch.delenv("MCP_ALLOWED_ORIGINS", raising=False)

    with TestClient(_create_test_app(), base_url="http://localhost") as client:
        response = client.post("/mcp", headers=MCP_HEADERS, json=_mcp_request(1, "tools/list"))

    assert response.status_code == HTTP_OK


def test_updates_endpoint_expires_cached_response_after_five_minutes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_updates_endpoint_cache_key_includes_selected_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_updates_endpoint_retries_source_errors_instead_of_caching_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        first_response = client.get("/api/updates")
        second_response = client.get("/api/updates")

    assert first_response.status_code == HTTP_OK
    assert second_response.status_code == HTTP_OK
    assert first_response.json()["updates"] == []
    assert second_response.json()["updates"] == []
    assert first_response.json()["errors"][0]["error"] == "network down"
    assert second_response.json()["errors"][0]["error"] == "network down"

    assert calls == EXPECTED_RETRY_CALLS
