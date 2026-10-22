from __future__ import annotations


def test_preflight_without_origin_is_not_affected(client):
    response = client.options("/tasks")
    assert response.status_code in (200, 204)


def test_preflight_allows_content_type_header(client):
    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, authorization",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_no_wildcard_origins(client):
    from app.config import config

    assert "*" not in config.allowed_origins
    assert config.credentials is False
