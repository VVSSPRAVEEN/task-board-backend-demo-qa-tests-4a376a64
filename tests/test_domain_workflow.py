from __future__ import annotations


def test_full_task_lifecycle(client):
    created = client.post(
        "/tasks", json={"title": "Learn pytest", "description": "Write tests", "status": "todo"}
    )
    assert created.status_code == 201
    tid = created.json()["id"]
    resp = client.get(f"/tasks/{tid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Learn pytest"
    patch = client.patch(f"/tasks/{tid}", json={"status": "in_progress"})
    assert patch.status_code == 200
    assert patch.json()["status"] == "in_progress"
    patch2 = client.patch(
        f"/tasks/{tid}", json={"status": "done", "description": "Done writing tests"}
    )
    assert patch2.status_code == 200
    assert patch2.json()["status"] == "done"
    assert patch2.json()["description"] == "Done writing tests"
    delete = client.delete(f"/tasks/{tid}")
    assert delete.status_code == 204
    final = client.get(f"/tasks/{tid}")
    assert final.status_code == 404
