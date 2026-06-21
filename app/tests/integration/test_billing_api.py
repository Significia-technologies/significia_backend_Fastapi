"""
MODULE 12 — Backend: Billing (Super Admin)
Tests: BIL-01 to BIL-02
Requires: Super admin credentials
"""
import pytest
import httpx
from app.tests.conftest import (
    THRESHOLD, SEED_SUPER_ADMIN_EMAIL, SEED_SUPER_ADMIN_PASSWORD, timed
)

MODULE = "billing"
REPORT_FILE = "module_12_billing.json"

_s: dict = {}
_results: list[dict] = []


def _rec(test_id, name, status, ms, code, assertions, error=None):
    entry = {"id": test_id, "name": name, "status": status,
             "response_time_ms": round(ms, 2), "status_code": code, "assertions": assertions}
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
    report = {"module": MODULE, "run_at": datetime.utcnow().isoformat(),
              "total": len(_results), "passed": passed,
              "failed": len(_results) - passed, "tests": _results}
    with open(os.path.join(REPORT_DIR, REPORT_FILE), "w") as f:
        json.dump(report, f, indent=2)


@pytest.fixture(scope="module")
def sa_token(client: httpx.Client) -> str:
    """Super admin token for billing endpoints."""
    resp = client.post(
        "/auth/login",
        json={"email": SEED_SUPER_ADMIN_EMAIL, "password": SEED_SUPER_ADMIN_PASSWORD, "force": True},
    )
    assert resp.status_code == 200, f"SA login failed: {resp.text}"
    return resp.json()["access_token"]


def _auth_sa(token):
    return {"Authorization": f"Bearer {token}"}


def test_BIL01_billing_overview(client: httpx.Client, sa_token: str):
    resp, ms = timed(client, "get", "/billing/overview", headers=_auth_sa(sa_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        assert isinstance(body, list)
        assertions.append("response is list of tenants")
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("BIL-01", "Billing overview — super admin", status, ms, resp.status_code, assertions, error)


def test_BIL02_billing_stats(client: httpx.Client, sa_token: str):
    resp, ms = timed(client, "get", "/billing/stats", headers=_auth_sa(sa_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        assert isinstance(body, dict)
        assertions.append("response is dict")
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("BIL-02", "Billing stats — super admin", status, ms, resp.status_code, assertions, error)
