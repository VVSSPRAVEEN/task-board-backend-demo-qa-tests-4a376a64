from __future__ import annotations

import os

import pytest

from app.store import TaskStore


@pytest.fixture()
def store(tmp_path):
    return TaskStore(db_path=str(tmp_path / "tasks.db"))


def test_init_store_creates_table(tmp_path):
    db_path = str(tmp_path / "tasks.db")
    TaskStore(db_path=db_path)
    assert os.path.exists(db_path)


def test_create_and_list(store):
    task = store.add_task("title", "desc", "todo")
    assert task["title"] == "title"
    tasks = store.list_tasks()
    assert len(tasks) == 1


def test_get_missing_returns_none(store):
    assert store.get_task("missing") is None


def test_patch_missing_returns_none(store):
    assert store.update_task("missing", {"status": "done"}) is None


def test_delete_missing_returns_false(store):
    assert store.delete_task("missing") is False


def test_patch_atomic_on_missing(store):
    store.add_task("keep", "desc", "todo")
    store.update_task("missing", {"title": "changed"})
    tasks = store.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "keep"
