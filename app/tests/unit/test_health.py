"""
MODULE 1 — Server Health
Tests: H-01 to H-03
"""
import pytest
import httpx
from app.tests.conftest import BASE_URL, THRESHOLD, timed

MODULE = "health"
REPORT_FILE = "module_01_health.json"

_results: list[dict] = []


def _rec(test_id, name, status, ms, code, assertions, error=None):
    entry = {
        "id": test_id, "name": name, "status": status,
        "response_time_ms": round(ms, 2), "status_code": code,
        "assertions": assertions,
    }
    if error:
        entry["error"] = error
    _results.append(entry)


@pytest.fixture(scope="module", autouse=True)
def write_report():
    yield
    import json, os
    from datetime import datetime
    from app.tests.conftest import REPORT_DIR
    os.makedirs(REPORT_DIR, exist_ok=True)
    passed = sum(1 for r in _results if r["status"] == "PASS")
    report = {
        "module": MODULE,
        "run_at": datetime.utcnow().isoformat(),
        "total": len(_results),
        "passed": passed,
        "failed": len(_results) - passed,
        "tests": _results,
    }
    with open(os.path.join(REPORT_DIR, REPORT_FILE), "w") as f:
        json.dump(report, f, indent=2)


# ── H-01 ──────────────────────────────────────────────────────────────────
def test_H01_health_check_returns_ok(client: httpx.Client):
    resp, ms = timed(client, "get", "/health")

    assertions = []
    status = "PASS"
    error = None

    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")

        body = resp.json()
        assert "status" in body
        assertions.append("'status' key present")

        assert body["status"] == "ok"
        assertions.append("status == 'ok'")

        assert ms < THRESHOLD["health"], f"Slow: {ms:.0f}ms > {THRESHOLD['health']}ms"
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['health']}ms")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("H-01", "Health check returns ok", status, ms, resp.status_code, assertions, error)


# ── H-02 ──────────────────────────────────────────────────────────────────
def test_H02_swagger_docs_load(client: httpx.Client):
    with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as raw:
        resp, ms = timed(raw, "get", "/docs")

    assertions = []
    status = "PASS"
    error = None

    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")

        assert "text/html" in resp.headers.get("content-type", "")
        assertions.append("content-type is text/html")

        assert ms < 2000
        assertions.append(f"response_time {ms:.0f}ms < 2000ms")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("H-02", "Swagger docs load", status, ms, resp.status_code, assertions, error)


# ── H-03 ──────────────────────────────────────────────────────────────────
def test_H03_unknown_route_returns_404(client: httpx.Client):
    resp, ms = timed(client, "get", "/nonexistent-route-xyz")

    assertions = []
    status = "PASS"
    error = None

    try:
        assert resp.status_code == 404
        assertions.append("status_code == 404")

        assert ms < THRESHOLD["health"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['health']}ms")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("H-03", "Unknown route returns 404", status, ms, resp.status_code, assertions, error)
