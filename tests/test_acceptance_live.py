from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_ready(url: str, timeout_s: float = 30.0) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with opener.open(url + "/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"service did not become ready at {url}")


def test_acceptance_checks_run_against_live_service(tmp_path):
    import importlib.util

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DB_PATH"] = str(tmp_path / "acceptance.db")
    env["PORT"] = str(port)
    env["P3_ACCEPTANCE_BASE_URL"] = base_url
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        try:
            _wait_ready(base_url)
        except RuntimeError:
            process.terminate()
            try:
                process_output = process.communicate(timeout=5)[0]
            except Exception:
                process_output = ""
            raise RuntimeError(f"service did not start: {(process_output or '')[-2000:]}") from None
        os.environ["P3_ACCEPTANCE_BASE_URL"] = base_url

        spec = importlib.util.spec_from_file_location(
            "acceptance", str(Path(__file__).with_name("acceptance.py"))
        )
        acceptance = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(acceptance)
        acceptance.BASE_URL = base_url
        results = acceptance.run_acceptance()
        for result in results:
            print(f"{result['check']}: {result['status']}")
        assert all(result["passed"] for result in results), [
            result for result in results if not result["passed"]
        ]
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        os.environ.pop("P3_ACCEPTANCE_BASE_URL", None)
