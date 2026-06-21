"""
MODULE 6 — Bridge: IA Master Profile
Tests: IAM-01 to IAM-17
Requires: IA token from Module 4 (seed_ia_token fixture)
Header: X-Tenant-Slug: demo
"""
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, timed

MODULE = "ia_master"
REPORT_FILE = "module_06_ia_master.json"
TENANT_HEADER = {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}

_s: dict = {}
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


def _auth(token):
    return {**TENANT_HEADER, "Authorization": f"Bearer {token}"}


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


# ── IAM-01 ─────────────────────────────────────────────────────────────────
def test_IAM01_get_latest_ia(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/latest", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        assert "id" in body
        assertions.append("id present")

        assert "ia_registration_number" in body
        assertions.append("ia_registration_number present")

        assert ms < THRESHOLD["bridge_auth"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

        _s["ia_id"] = body.get("id")
        _s["ia_reg_number"] = body.get("ia_registration_number")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-01", "Get IA Master — existing profile", status, ms, resp.status_code, assertions, error)


# ── IAM-03 ─────────────────────────────────────────────────────────────────
def test_IAM03_validate_ia_number_valid(client: httpx.Client, seed_ia_token: str):
    reg = _s.get("ia_reg_number", "INA0000000000")
    resp, ms = timed(client, "get", f"/ia-master/validate/{reg}", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        # API returns {"exists": bool} not {"valid": bool}
        key = "exists" if "exists" in body else "valid"
        assert key in body
        assertions.append(f"'{key}' field present")
        assert isinstance(body[key], bool)
        assertions.append(f"{key} is bool")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-03", "Validate IA number — valid", status, ms, resp.status_code, assertions, error)


# ── IAM-04 ─────────────────────────────────────────────────────────────────
def test_IAM04_validate_ia_number_invalid(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/validate/XXXXX-INVALID", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (200, 400)
        assertions.append(f"status_code in (200,400) — got {resp.status_code}")
        if resp.status_code == 200:
            body = resp.json()
            # API returns {"exists": bool} or {"valid": bool}
            result = body.get("valid") or body.get("exists")
            assert result is False or result is None
            assertions.append("IA number marked as invalid/non-existent")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-04", "Validate IA number — invalid format", status, ms, resp.status_code, assertions, error)


# ── IAM-05 ─────────────────────────────────────────────────────────────────
def test_IAM05_list_employees(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/employees", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert isinstance(resp.json(), list)
        assertions.append("response is array")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-05", "List IA employees", status, ms, resp.status_code, assertions, error)


# ── IAM-06 ─────────────────────────────────────────────────────────────────
def test_IAM06_list_departments(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/departments", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert isinstance(resp.json(), list)
        assertions.append("response is array")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-06", "List departments", status, ms, resp.status_code, assertions, error)


# ── IAM-07 ─────────────────────────────────────────────────────────────────
def test_IAM07_create_department(client: httpx.Client, seed_ia_token: str):
    import uuid
    dept_name = f"Test Dept {uuid.uuid4().hex[:6]}"
    resp, ms = timed(
        client, "post", "/ia-master/departments",
        data={"name": dept_name},
        headers=_auth(seed_ia_token)
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text}"
        assertions.append(f"status_code in (200,201) — got {resp.status_code}")
        body = resp.json()
        assert "id" in body or "name" in body
        assertions.append("id or name present in response")
        _s["dept_id"] = body.get("id")
        _s["dept_name"] = dept_name
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-07", "Create department", status, ms, resp.status_code, assertions, error)


# ── IAM-08 ─────────────────────────────────────────────────────────────────
def test_IAM08_create_duplicate_department(client: httpx.Client, seed_ia_token: str):
    dept_name = _s.get("dept_name")
    if not dept_name:
        pytest.skip("No dept_name from IAM-07")

    resp, ms = timed(
        client, "post", "/ia-master/departments",
        data={"name": dept_name},
        headers=_auth(seed_ia_token)
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (400, 409), f"Expected 400/409, got {resp.status_code}"
        assertions.append(f"status_code in (400,409) — got {resp.status_code}")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-08", "Create duplicate department", status, ms, resp.status_code, assertions, error)


# ── IAM-09 ─────────────────────────────────────────────────────────────────
def test_IAM09_delete_department(client: httpx.Client, seed_ia_token: str):
    dept_id = _s.get("dept_id")
    if not dept_id:
        pytest.skip("No dept_id from IAM-07")

    resp, ms = timed(client, "delete", f"/ia-master/departments/{dept_id}", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (200, 204), f"Expected 200/204, got {resp.status_code}"
        assertions.append(f"status_code in (200,204) — got {resp.status_code}")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-09", "Delete department", status, ms, resp.status_code, assertions, error)


# ── IAM-10 ─────────────────────────────────────────────────────────────────
def test_IAM10_get_sebi_audit_trail(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/sebi/audit-trail", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        assert isinstance(body, (list, dict))
        assertions.append("response is list or dict")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-10", "Get SEBI audit trail", status, ms, resp.status_code, assertions, error)


# ── IAM-11 ─────────────────────────────────────────────────────────────────
def test_IAM11_get_ia_version_history(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/sebi/ia-master/versions", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert isinstance(resp.json(), (list, dict))
        assertions.append("response is list or dict")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-11", "Get IA version history", status, ms, resp.status_code, assertions, error)


# ── IAM-12 ─────────────────────────────────────────────────────────────────
def test_IAM12_export_audit_trail_csv(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(
        client, "get", "/ia-master/sebi/audit-trail/export?format=csv",
        headers=_auth(seed_ia_token)
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        ct = resp.headers.get("content-type", "")
        assert "text/csv" in ct or "application/octet-stream" in ct
        assertions.append(f"content-type contains csv — got {ct}")
        assert len(resp.content) > 0
        assertions.append("response body non-empty")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-12", "Export audit trail — CSV", status, ms, resp.status_code, assertions, error)


# ── IAM-13 ─────────────────────────────────────────────────────────────────
def test_IAM13_export_audit_trail_json(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(
        client, "get", "/ia-master/sebi/audit-trail/export?format=json",
        headers=_auth(seed_ia_token)
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        ct = resp.headers.get("content-type", "")
        assert "application/json" in ct or "application/octet-stream" in ct
        assertions.append(f"content-type contains json — got {ct}")
        assert len(resp.content) > 0
        assertions.append("response body non-empty")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-13", "Export audit trail — JSON", status, ms, resp.status_code, assertions, error)


# ── IAM-14 ─────────────────────────────────────────────────────────────────
def test_IAM14_download_ia_pdf(client: httpx.Client, seed_ia_token: str):
    ia_id = _s.get("ia_id")
    if not ia_id:
        pytest.skip("No ia_id from IAM-01")

    resp, ms = timed(client, "get", f"/ia-master/{ia_id}/pdf", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append("PDF body > 1000 bytes")
        assert ms < THRESHOLD["pdf"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['pdf']}ms")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-14", "Download IA PDF report", status, ms, resp.status_code, assertions, error)


# ── IAM-15 ─────────────────────────────────────────────────────────────────
def test_IAM15_download_letterhead(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/letterhead", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append("PDF body > 1000 bytes")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-15", "Download letterhead PDF", status, ms, resp.status_code, assertions, error)


# ── IAM-16 ─────────────────────────────────────────────────────────────────
def test_IAM16_get_report_history(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/ia-master/sebi/report-history", headers=_auth(seed_ia_token))

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert isinstance(resp.json(), (list, dict))
        assertions.append("response is list or dict")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-16", "Get report history", status, ms, resp.status_code, assertions, error)


# ── IAM-17 ─────────────────────────────────────────────────────────────────
def test_IAM17_export_report_history_csv(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(
        client, "get", "/ia-master/sebi/report-history/export?format=csv",
        headers=_auth(seed_ia_token)
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        ct = resp.headers.get("content-type", "")
        assert "text/csv" in ct or "application/octet-stream" in ct
        assertions.append("content-type is csv")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IAM-17", "Export report history — CSV", status, ms, resp.status_code, assertions, error)
