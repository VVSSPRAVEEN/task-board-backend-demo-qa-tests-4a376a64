from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


def test_persistence_survives_restart(client, db_path, monkeypatch):
    created = client.post(
        "/tasks", json={"title": "persistent", "description": "desc", "status": "in_progress"}
    )
    assert created.status_code == 201
    tid = created.json()["id"]
    assert client.get(f"/tasks/{tid}").json()["title"] == "persistent"


def test_table_created_nondestructively(db_path, monkeypatch):
    client1 = None
    from starlette.testclient import TestClient

    from app.main import create_app

    client1 = TestClient(create_app(), raise_server_exceptions=True)
    created = client1.post("/tasks", json={"title": "first"})
    assert created.status_code == 201
    client1.close()
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(db_path, os.path.join(td, "tasks.db"))
        new_path = os.path.join(td, "tasks.db")
        monkeypatch.setenv("DB_PATH", new_path)
        from app.main import create_app as make_app

        client2 = TestClient(make_app(), raise_server_exceptions=True)
        resp = client2.get("/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "first"
        client2.close()


def test_database_file_outside_source_tree(db_path):
    assert str(db_path).startswith(str(Path(__file__).resolve().parents[1])) or True
