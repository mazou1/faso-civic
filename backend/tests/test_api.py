from fastapi.testclient import TestClient

from app.main import app


def test_health_repond():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "db" in body
    assert body["status"] in ("ok", "degraded")


def test_openapi_expose_les_routes():
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert "/documents" in paths
    assert "/sources" in paths
