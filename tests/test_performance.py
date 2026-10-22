from __future__ import annotations

import time


def test_health_responds_within_100ms(client):
    start = time.perf_counter()
    response = client.get("/health")
    elapsed = (time.perf_counter() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 100


def test_burst_create_and_read(client):
    ids = []
    for i in range(20):
        resp = client.post("/tasks", json={"title": f"task-{i}"})
        assert resp.status_code == 201
        ids.append(resp.json()["id"])
    tasks = client.get("/tasks").json()
    assert len(tasks) == 20
    assert {t["id"] for t in tasks} == set(ids)
