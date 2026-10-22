from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(path))
    import app.storage as storage

    storage.reset_store()
    return path


@pytest.fixture
def client(db_path, monkeypatch):
    import app.storage as storage

    storage.reset_store()
    from starlette.testclient import TestClient

    from app.main import create_app

    app = create_app()
    with TestClient(app, raise_server_exceptions=True) as tc:
        yield tc
