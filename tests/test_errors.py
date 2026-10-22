from __future__ import annotations


def test_malformed_json_returns_400_invalid_json(client):
    response = client.post(
        "/tasks", content=b'{"title": "unterminated', headers={"content-type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_json"


def test_unknown_path_returns_404_envelope(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_write_without_json_content_type_returns_415(client):
    response = client.post("/tasks", content=b"title=plain", headers={"content-type": "text/plain"})
    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"


def test_oversized_body_returns_413(client):
    oversized = b'{"title": "' + (b"x" * 70_000) + b'"}'
    response = client.post(
        "/tasks", content=oversized, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["code"] == "payload_too_large"


def test_error_envelope_never_leaks_internals(client):
    response = client.get("/tasks/missing-id")
    body = response.text.lower()
    for forbidden in ("traceback", "sqlite3", "select ", "/generated", "site-packages"):
        assert forbidden not in body
