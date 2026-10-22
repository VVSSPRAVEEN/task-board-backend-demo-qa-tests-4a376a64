from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE_URL = os.getenv("P3_ACCEPTANCE_BASE_URL", "http://127.0.0.1:8001")


def _request(method, path, headers=None, body=None):
    url = BASE_URL + path
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode("utf-8")


def run_acceptance():
    results = []

    def check(name, fn):
        try:
            fn()
            results.append({"check": name, "passed": True, "status": "pass"})
        except AssertionError as e:
            results.append({"check": name, "passed": False, "status": "fail", "error": str(e)})

    def at1():
        status, _, body = _request("GET", "/health")
        assert status == 200, f"AT1: expected 200, got {status}"
        data = json.loads(body)
        assert data["status"] == "ok", f"AT1: expected status ok, got {data}"
        assert data["task_count"] == 0, f"AT1: expected task_count 0, got {data}"

    check("AT1_health_returns_200_with_empty_task_count", at1)

    def at2():
        resp = _request(
            "POST",
            "/tasks",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"title": "AT2 task"}),
        )
        status, _, body = resp
        assert status == 201, f"AT2: expected 201, got {status}"
        data = json.loads(body)
        assert "id" in data and len(data["id"]) == 36, f"AT2: expected UUID id, got {data}"
        assert data["title"] == "AT2 task"
        assert data["status"] == "todo"
        assert data["description"] == ""

    check("AT2_create_task_returns_201_with_UUID_and_defaults", at2)

    def at3():
        created = _request(
            "POST",
            "/tasks",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"title": "AT3 task", "description": "desc", "status": "in_progress"}),
        )
        status, _, _ = created
        assert status == 201
        tid = json.loads(created[2])["id"]
        patch_resp = _request(
            "PATCH",
            f"/tasks/{tid}",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"status": "done"}),
        )
        pstatus, _, pbody = patch_resp
        assert pstatus == 200, f"AT3: expected 200, got {pstatus}"
        pdata = json.loads(pbody)
        assert pdata["status"] == "done"
        assert pdata["title"] == "AT3 task"
        assert pdata["description"] == "desc"

    check("AT3_PATCH_updates_fields_and_keeps_unchanged", at3)

    def at4():
        created = _request(
            "POST",
            "/tasks",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"title": "AT4 task"}),
        )
        tid = json.loads(created[2])["id"]
        resp = _request(
            "PATCH",
            f"/tasks/{tid}",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"title": "new title", "status": "invalid"}),
        )
        status, _, body = resp
        assert status == 422, f"AT4: expected 422 on invalid status, got {status}"
        data = json.loads(body)
        assert data["code"] == "validation_error"
        get_resp = _request("GET", f"/tasks/{tid}")
        gstatus, _, gbody = get_resp
        assert gstatus == 200
        gdata = json.loads(gbody)
        assert gdata["title"] == "AT4 task", "AT4: data must be unchanged after failed PATCH"

    check("AT4_PATCH_is_atomic_no_partial_changes_on_failure", at4)

    def at5():
        created = _request(
            "POST",
            "/tasks",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"title": "AT5 task"}),
        )
        tid = json.loads(created[2])["id"]
        resp = _request("DELETE", f"/tasks/{tid}")
        status, _, body = resp
        assert status == 204, f"AT5: expected 204, got {status}"
        assert body == ""
        del_resp = _request("DELETE", f"/tasks/{tid}")
        dstatus, _, _ = del_resp
        assert dstatus == 404, f"AT5: expected 404 on delete of nonexistent task, got {dstatus}"

    check("AT5_DELETE_returns_204_and_404_for_missing", at5)

    def at6():
        for payload in [
            {"title": None},
            {"title": ""},
            {"title": "   "},
            {"title": "x" * 81},
            {"title": 42},
            {"title": "ok", "unknown": "x"},
            {"title": "ok", "id": "client-id"},
        ]:
            resp = _request(
                "POST",
                "/tasks",
                headers={"Content-Type": "application/json"},
                body=json.dumps(payload),
            )
            status, _, body = resp
            assert status == 422, f"AT6: expected 422 for {payload}, got {status}"
            assert json.loads(body)["code"] == "validation_error"

    check("AT6_validation_rejects_invalid_payloads_with_422", at6)

    def at7():
        resp = _request(
            "POST", "/tasks", headers={"Content-Type": "application/json"}, body="not json"
        )
        status, _, body = resp
        assert status == 400, f"AT7: expected 400 for malformed JSON, got {status}"
        assert json.loads(body)["code"] == "invalid_json"
        resp = _request("GET", "/tasks/nonexistent-id")
        status, _, body = resp
        assert status == 404
        assert json.loads(body)["code"] == "not_found"
        assert "traceback" not in body.lower()

    check("AT7_error_handling_returns_stable_codes_without_leaks", at7)

    def at8():
        resp = _request("GET", "/tasks", headers={"Origin": "http://localhost:5173"})
        status, headers, _ = resp
        assert status == 200
        assert headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "access-control-allow-credentials" not in headers
        resp = _request(
            "OPTIONS",
            "/tasks",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        ostatus, oheaders, _ = resp
        assert ostatus in (200, 204)
        assert oheaders["access-control-allow-methods"] == "GET, POST, PATCH, DELETE"

    check("AT8_CORS_restricts_to_allowed_origins_and_preflight", at8)

    return results
