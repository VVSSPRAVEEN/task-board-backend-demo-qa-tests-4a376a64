"""Storage failures surface as 503 storage_unavailable, never as a 500."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import TaskStore


def _make_client(db_path: str) -> TestClient:
    store = TaskStore(db_path=db_path)
    app = create_app()
    app.state.store = store
    return TestClient(app)


@pytest.fixture()
def failing_store(tmp_path):
    store = TaskStore(db_path=str(tmp_path / "tasks.db"))
    store.list_tasks = lambda: (_ for _ in ()).throw(sqlite3.OperationalError("database is locked"))
    store.get_task = lambda tid: (_ for _ in ()).throw(
        sqlite3.OperationalError("database is locked")
    )
    store.add_task = lambda *a, **k: (_ for _ in ()).throw(
        sqlite3.OperationalError("database is locked")
    )
    store.update_task = lambda *a, **k: (_ for _ in ()).throw(
        sqlite3.OperationalError("database is locked")
    )
    store.delete_task = lambda *a, **k: (_ for _ in ()).throw(
        sqlite3.OperationalError("database is locked")
    )
    return store


@pytest.fixture()
def failing_client(failing_store, tmp_path):
    app = create_app()
    app.state.store = failing_store
    return TestClient(app)


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/tasks", None),
        ("GET", "/tasks/any-id", None),
        ("POST", "/tasks", {"title": "x"}),
        ("PATCH", "/tasks/any-id", {"title": "x"}),
        ("DELETE", "/tasks/any-id", None),
    ],
)
def test_store_failure_returns_503_envelope(failing_client, method, path, payload):
    response = failing_client.request(method, path, json=payload)

    assert response.status_code == 503
    assert response.json()["code"] == "storage_unavailable"
    assert "sqlite" not in response.text.lower()
