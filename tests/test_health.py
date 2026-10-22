from __future__ import annotations

from app.storage_guard import StorageProbeResult


def test_health_reports_ready_store_with_task_count(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "task_count": 0}
    assert response.headers.get("cache-control") == "no-store"


def test_health_counts_existing_tasks(client):
    created = client.post("/tasks", json={"title": "counted"})
    assert created.status_code == 201
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["task_count"] == 1


def test_health_reports_storage_failure_as_503(client, monkeypatch):
    from app import storage_guard

    original_probe = storage_guard.probe_store
    monkeypatch.setattr(
        storage_guard,
        "probe_store",
        lambda store: StorageProbeResult.unhealthy("storage_unreachable"),
    )
    try:
        response = client.get("/health")
    finally:
        storage_guard.probe_store = original_probe
    assert response.status_code == 503
    assert response.json()["code"] == "storage_unavailable"
