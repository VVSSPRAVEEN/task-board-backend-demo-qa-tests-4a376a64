from __future__ import annotations

import uuid


def _create(client, **overrides):
    payload = {"title": "Write the report"}
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_generated_id_and_documented_defaults(client):
    task = _create(client)
    uuid.UUID(task["id"])
    assert task["title"] == "Write the report"
    assert task["description"] == ""
    assert task["status"] == "todo"
    assert task["created_at"]


def test_create_keeps_supplied_fields(client):
    task = _create(client, description="  details  ", status="in_progress")
    assert task["description"] == "details"
    assert task["status"] == "in_progress"


def test_title_is_trimmed(client):
    task = _create(client, title="   padded   ")
    assert task["title"] == "padded"


def test_list_returns_every_task(client):
    first = _create(client, title="first")
    second = _create(client, title="second")
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert {task["id"] for task in tasks} == {first["id"], second["id"]}
    assert [task["title"] for task in tasks] == ["first", "second"]


def test_get_returns_one_task(client):
    task = _create(client)
    response = client.get(f"/tasks/{task['id']}")
    assert response.status_code == 200
    assert response.json() == task


def test_patch_updates_only_supplied_fields(client):
    task = _create(client, description="keep me")
    updated = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["description"] == "keep me"


def test_patch_no_partial_changes_on_failure(client):
    task = _create(client, description="original")
    initial = client.get(f"/tasks/{task['id']}").json()
    response = client.patch(f"/tasks/{task['id']}", json={"title": None})
    assert response.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json() == initial


def test_delete_returns_204_with_no_body(client):
    task = _create(client)
    response = client.delete(f"/tasks/{task['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_delete_nonexistent_returns_404(client):
    response = client.delete("/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_nonexistent_returns_404(client):
    response = client.get("/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
