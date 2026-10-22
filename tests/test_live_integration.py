from __future__ import annotations

import os

import pytest

BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL") or os.getenv("P3_E2E_BASE_URL") or os.getenv("BASE_URL")


def test_live_integration_runs_without_route_mocks():
    if not BASE_URL:
        pytest.skip("PLAYWRIGHT_BASE_URL not set")
    import urllib.request

    status, _headers, body = None, None, None
    try:
        req = urllib.request.Request(
            BASE_URL + "/health", headers={"Origin": "http://localhost:5173"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read()
    except Exception as e:
        pytest.fail(f"Live health check failed: {e}")
    assert status == 200
    import json

    data = json.loads(body)
    assert data["status"] == "ok"
    assert "task_count" in data
