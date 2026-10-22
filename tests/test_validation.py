from __future__ import annotations

import pytest


@pytest.fixture()
def board(client):
    created = client.post("/tasks", json={"title": "existing", "description": "keep"})
    assert created.status_code == 201
    return created.json()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"title": 42},
        {"title": True},
        {"title": ["a"]},
        {"title": "   "},
        {"title": ""},
        {"title": "x" * 81},
        {"title": "ok", "description": None},
        {"title": "ok", "description": "x" * 281},
        {"title": "ok", "status": None},
        {"title": "ok", "status": "draft"},
        {"title": "ok", "status": "DONE"},
        {"title": "ok", "unknown": "field"},
        {"title": "ok", "id": "client-supplied"},
    ],
)
def test_invalid_create_is_rejected_without_writing(client, board, payload):
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "validation_error"
    tasks = client.get("/tasks").json()
    assert tasks == [board]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"title": "   "},
        {"title": "x" * 81},
        {"description": "x" * 281},
        {"status": "draft"},
        {"id": "client-supplied"},
        {"unknown": "field"},
    ],
)
def test_invalid_patch_is_rejected_without_writing(client, board, payload):
    response = client.patch(f"/tasks/{board['id']}", json=payload)
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "validation_error"
    assert client.get(f"/tasks/{board['id']}").json() == board


def test_boundary_lengths_are_accepted(client):
    sixty_five = client.post("/tasks", json={"title": "x" * 80})
    assert sixty_five.status_code == 201
    described = client.post("/tasks", json={"title": "ok", "description": "y" * 280})
    assert described.status_code == 201
    assert len(described.json()["description"]) == 280
