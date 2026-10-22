from __future__ import annotations

import pytest

from app.config import StoreConfig


def test_default_port_is_8001():
    config = StoreConfig()
    assert config.port == 8001


def test_port_overridden_by_env():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("PORT", "9000")
        config = StoreConfig()
        assert config.port == 9000


def test_database_path_overridden_by_env():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("DB_PATH", "/custom/path/tasks.db")
        config = StoreConfig()
        assert config.database_path == "/custom/path/tasks.db"


def test_writable_path_default():
    config = StoreConfig()
    assert config.writable_path == "/data"


def test_allowed_origins_default():
    config = StoreConfig()
    assert "http://localhost:5173" in config.allowed_origins
    assert "http://localhost:4173" in config.allowed_origins
