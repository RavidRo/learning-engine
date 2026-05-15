from fastapi.testclient import TestClient

from learning_engine.app import app

HTTP_OK = 200
HTTP_UNPROCESSABLE_ENTITY = 422


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


def test_updates_rejects_non_positive_days() -> None:
    client = TestClient(app)

    response = client.get("/api/updates?days=0")

    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY
