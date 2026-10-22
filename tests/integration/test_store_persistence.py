"""Persistence across reopens and a genuine process restart (AT1/AT8 support)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.store import SCHEMA_VERSION, TaskStore

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]

_CHILD_ADD = """
import os
from app.store import TaskStore

store = TaskStore()
created = store.add_task("from child", status="in_progress")
store.close()
print(created["id"])
"""

_CHILD_COUNT = """
from app.store import TaskStore

store = TaskStore()
print(store.count_tasks())
store.close()
"""


def _child_env(db_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(REPO_ROOT) if not existing else os.pathsep.join([str(REPO_ROOT), existing])
    )
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run(script: str, db_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        env=_child_env(db_path),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_rows_survive_a_reopen(tmp_path: Path):
    db_file = tmp_path / "tasks.db"

    first = TaskStore(str(db_file))
    created = first.add_task("persisted", description="detail", status="done")
    first.close()

    second = TaskStore(str(db_file))
    try:
        assert second.count_tasks() == 1
        assert second.get_task(created["id"]) == created
    finally:
        second.close()


def test_empty_board_survives_a_reopen(tmp_path: Path):
    db_file = tmp_path / "tasks.db"

    TaskStore(str(db_file)).close()

    reopened = TaskStore(str(db_file))
    try:
        assert reopened.init_schema() == SCHEMA_VERSION
        assert reopened.list_tasks() == []
    finally:
        reopened.close()


def test_rows_survive_a_real_process_restart(tmp_path: Path):
    db_file = tmp_path / "tasks.db"

    parent = TaskStore(str(db_file))
    parent.add_task("before restart")
    parent.close()

    result = _run(_CHILD_COUNT, db_file)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "1"

    added = _run(_CHILD_ADD, db_file)
    assert added.returncode == 0, added.stderr
    assert added.stdout.strip()

    reopened = TaskStore(str(db_file))
    try:
        assert reopened.count_tasks() == 2
    finally:
        reopened.close()


def test_legacy_schema_is_migrated_without_losing_rows(tmp_path: Path):
    import sqlite3

    db_file = tmp_path / "legacy.db"
    connection = sqlite3.connect(db_file)
    connection.execute(
        "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, "
        "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    connection.execute("INSERT INTO tasks (title, done) VALUES ('legacy done', 1)")
    connection.execute("INSERT INTO tasks (title, done) VALUES ('legacy todo', 0)")
    connection.commit()
    connection.close()

    store = TaskStore(str(db_file))
    try:
        tasks = store.list_tasks()
        assert {task["title"]: task["status"] for task in tasks} == {
            "legacy done": "done",
            "legacy todo": "todo",
        }
        assert all(isinstance(task["id"], str) for task in tasks)
    finally:
        store.close()
