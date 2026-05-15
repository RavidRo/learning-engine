from fastapi.testclient import TestClient

from learning_engine.app import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_technology_updates_rejects_non_positive_days() -> None:
    client = TestClient(app)

    response = client.get("/api/technology-updates?days=0")

    assert response.status_code == 422
