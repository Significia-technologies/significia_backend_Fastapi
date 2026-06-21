"""
MODULE 3 — Backend: Tenant Resolution
Tests: TEN-01 to TEN-04
Requires: Module 2 passed (seed IA tenant exists)
"""
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, timed

MODULE = "tenant"
REPORT_FILE = "module_03_tenant.json"

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


# ── TEN-01 ─────────────────────────────────────────────────────────────────
def test_TEN01_get_tenant_info_valid_subdomain(client: httpx.Client):
    resp, ms = timed(
        client, "get", "/ia-auth/tenant-info",
        headers={"X-Tenant-Slug": SEED_IA_SUBDOMAIN}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        for field in ("tenant_id", "tenant_name", "subdomain", "bridge_status"):
            assert field in body, f"Missing field: {field}"
        assertions.append("tenant_id, tenant_name, subdomain, bridge_status present")

        # Type checks
        import uuid as _uuid
        _uuid.UUID(body["tenant_id"])
        assertions.append("tenant_id is valid UUID")

        assert isinstance(body["tenant_name"], str) and body["tenant_name"]
        assertions.append("tenant_name is non-empty string")

        assert body["subdomain"] == SEED_IA_SUBDOMAIN
        assertions.append(f"subdomain == '{SEED_IA_SUBDOMAIN}'")

        assert isinstance(body["bridge_status"], str)
        assertions.append("bridge_status is string")

        assert ms < THRESHOLD["bridge_auth"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("TEN-01", "Get tenant info — valid subdomain", status, ms, resp.status_code, assertions, error)


# ── TEN-02 ─────────────────────────────────────────────────────────────────
def test_TEN02_get_tenant_info_invalid_subdomain(client: httpx.Client):
    resp, ms = timed(
        client, "get", "/ia-auth/tenant-info",
        headers={"X-Tenant-Slug": "zzz-this-does-not-exist-xyz"}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (401, 404), f"Expected 401/404, got {resp.status_code}"
        assertions.append(f"status_code in (401,404) — got {resp.status_code}")
        assert "detail" in resp.json()
        assertions.append("error detail present")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("TEN-02", "Get tenant info — invalid subdomain", status, ms, resp.status_code, assertions, error)


# ── TEN-03 ─────────────────────────────────────────────────────────────────
def test_TEN03_get_tenant_info_no_header(client: httpx.Client):
    resp, ms = timed(client, "get", "/ia-auth/tenant-info")

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (401, 422), f"Expected 401/422, got {resp.status_code}"
        assertions.append(f"status_code in (401,422) — got {resp.status_code}")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("TEN-03", "Get tenant info — no header", status, ms, resp.status_code, assertions, error)


# ── TEN-04 ─────────────────────────────────────────────────────────────────
def test_TEN04_tenant_info_field_types(client: httpx.Client):
    resp, ms = timed(
        client, "get", "/ia-auth/tenant-info",
        headers={"X-Tenant-Slug": SEED_IA_SUBDOMAIN}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        body = resp.json()

        assert isinstance(body.get("tenant_id"), str)
        assertions.append("tenant_id is str")

        assert isinstance(body.get("tenant_name"), str)
        assertions.append("tenant_name is str")

        assert isinstance(body.get("subdomain"), str)
        assertions.append("subdomain is str")

        assert isinstance(body.get("bridge_status"), str)
        assertions.append("bridge_status is str")

        # custom_domain may be null — just check it's not an unexpected type
        cd = body.get("custom_domain")
        assert cd is None or isinstance(cd, str)
        assertions.append("custom_domain is str or null")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("TEN-04", "Tenant info field types", status, ms, resp.status_code, assertions, error)
