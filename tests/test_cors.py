from __future__ import annotations

import pytest

ALLOWED = "http://localhost:5173"
OTHER_ALLOWED = "http://localhost:4173"
DISALLOWED = "http://evil.example.com"


def test_allowed_origin_is_echoed(client):
    response = client.get("/health", headers={"Origin": ALLOWED})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert "access-control-allow-credentials" not in response.headers


def test_second_allowed_origin_is_echoed(client):
    response = client.get("/tasks", headers={"Origin": OTHER_ALLOWED})
    assert response.headers["access-control-allow-origin"] == OTHER_ALLOWED


def test_disallowed_origin_is_not_allowed(client):
    response = client.get("/health", headers={"Origin": DISALLOWED})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
def test_preflight_is_answered_for_every_write_method(client, method):
    response = client.options(
        "/tasks",
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] == ALLOWED
    allowed = response.headers["access-control-allow-methods"]
    assert method in allowed
