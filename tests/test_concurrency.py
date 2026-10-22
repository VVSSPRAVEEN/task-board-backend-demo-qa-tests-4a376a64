from __future__ import annotations

import threading


def test_concurrent_create_does_not_corrupt(client):
    results = []
    barrier = threading.Barrier(10)

    def create_task(i):
        barrier.wait()
        resp = client.post("/tasks", json={"title": f"concurrent-{i}"})
        results.append((i, resp.status_code, resp.json().get("id")))

    threads = [threading.Thread(target=create_task, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    statuses = [r[1] for r in results]
    assert all(s == 201 for s in statuses), statuses
    ids = [r[2] for r in results]
    assert len(set(ids)) == 10
    tasks = client.get("/tasks").json()
    assert len(tasks) == 10
