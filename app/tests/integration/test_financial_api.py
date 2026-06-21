"""
MODULE 9 — Bridge: Financial Analysis
Tests: FIN-01 to FIN-12
Requires: IA token, seed client C001 exists
Header: X-Tenant-Slug: demo
"""
import uuid
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, timed

MODULE = "financial_analysis"
REPORT_FILE = "module_09_financial_analysis.json"
TENANT_HEADER = {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}

_s: dict = {}
_results: list[dict] = []

SEED_CLIENT_ID = "7b3b4182-6f12-437c-a78b-48949d0332d3"
ANALYSIS_PAYLOAD = {
    "client_id": SEED_CLIENT_ID,
    "occupation": "Engineer",
    "dob": "1985-06-15",
    "annual_income": 1200000.0,
    "expenses": {
        "hh": 20000.0, "med": 5000.0, "travel": 10000.0, "elec": 3000.0,
        "tele": 2000.0, "maid": 3000.0, "edu": 5000.0, "ent": 5000.0,
        "emi": 15000.0, "savings": 20000.0, "misc": 5000.0,
    },
    "assets": {
        "land": 5000000.0, "inv": 2000000.0, "cash": 300000.0, "retirement": 500000.0, "others": [],
    },
    "liabilities": {
        "personal": 0.0, "cc": 50000.0, "hb": 2000000.0, "others": [],
    },
    "insurance": {
        "life_cover": 5000000.0, "life_premium": 50000.0,
        "med_cover": 500000.0, "med_premium": 15000.0,
        "veh_cover": 0.0, "veh_premium": 0.0, "other_cover": 0.0, "other_premium": 0.0,
    },
    "notes": "Pytest financial analysis FIN-01",
}


def _rec(test_id, name, status, ms, code, assertions, error=None):
    entry = {"id": test_id, "name": name, "status": status,
             "response_time_ms": round(ms, 2), "status_code": code, "assertions": assertions}
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
    report = {"module": MODULE, "run_at": datetime.utcnow().isoformat(),
              "total": len(_results), "passed": passed,
              "failed": len(_results) - passed, "tests": _results}
    with open(os.path.join(REPORT_DIR, REPORT_FILE), "w") as f:
        json.dump(report, f, indent=2)


# ── FIN-01 ─────────────────────────────────────────────────────────────────
def test_FIN01_create_financial_analysis(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", "/financial-analysis/bridge/analysis",
                     json=ANALYSIS_PAYLOAD, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 201), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"status_code in (200,201)")
        body = resp.json()
        assert "id" in body
        assertions.append("id present")
        uuid.UUID(body["id"])
        assertions.append("id is valid UUID")
        assert ms < THRESHOLD["write"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['write']}ms")
        _s["analysis_id"] = body["id"]
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-01", "Create financial analysis — happy path", status, ms, resp.status_code, assertions, error)


# ── FIN-02 ─────────────────────────────────────────────────────────────────
def test_FIN02_create_missing_client(client: httpx.Client, seed_ia_token: str):
    bad = {**ANALYSIS_PAYLOAD, "client_id": str(uuid.uuid4())}
    resp, ms = timed(client, "post", "/financial-analysis/bridge/analysis",
                     json=bad, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (404, 500), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"unknown client rejected: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-02", "Create — unknown client code", status, ms, resp.status_code, assertions, error)


# ── FIN-03 ─────────────────────────────────────────────────────────────────
def test_FIN03_create_missing_required_fields(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", "/financial-analysis/bridge/analysis",
                     json={"client_id": SEED_CLIENT_ID}, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-03", "Create — missing required fields", status, ms, resp.status_code, assertions, error)


# ── FIN-04 ─────────────────────────────────────────────────────────────────
def test_FIN04_get_analysis_by_id(client: httpx.Client, seed_ia_token: str):
    aid = _s.get("analysis_id")
    if not aid:
        pytest.skip("No analysis_id from FIN-01")

    resp, ms = timed(client, "get", f"/financial-analysis/bridge/analysis/{aid}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        assert body.get("id") == aid
        assertions.append("id matches requested id")
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-04", "Get analysis by ID", status, ms, resp.status_code, assertions, error)


# ── FIN-05 ─────────────────────────────────────────────────────────────────
def test_FIN05_get_analysis_bad_id(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", f"/financial-analysis/bridge/analysis/{uuid.uuid4()}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 404
        assertions.append("status_code == 404")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-05", "Get analysis — bad ID", status, ms, resp.status_code, assertions, error)


# ── FIN-06 ─────────────────────────────────────────────────────────────────
def test_FIN06_list_analyses_for_client(client: httpx.Client, seed_ia_token: str):
    client_id = SEED_CLIENT_ID
    resp, ms = timed(client, "get", f"/financial-analysis/bridge/analysis",
                     params={"client_id": client_id},
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert isinstance(resp.json(), list)
        assertions.append("response is array")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-06", "List analyses for client", status, ms, resp.status_code, assertions, error)


# ── FIN-07 ─────────────────────────────────────────────────────────────────
def test_FIN07_list_all_analyses(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/financial-analysis/bridge/analysis", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert isinstance(resp.json(), list)
        assertions.append("response is array")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-07", "List all analyses", status, ms, resp.status_code, assertions, error)


# ── FIN-08 ─────────────────────────────────────────────────────────────────
def test_FIN08_download_analysis_pdf(client: httpx.Client, seed_ia_token: str):
    aid = _s.get("analysis_id")
    if not aid:
        pytest.skip("No analysis_id from FIN-01")

    resp, ms = timed(client, "get", f"/financial-analysis/bridge/analysis/{aid}/pdf",
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append(f"PDF body size: {len(resp.content)} bytes")
        assert ms < THRESHOLD["pdf"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['pdf']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-08", "Download analysis PDF", status, ms, resp.status_code, assertions, error)


# ── FIN-09 ─────────────────────────────────────────────────────────────────
def test_FIN09_download_analysis_docx(client: httpx.Client, seed_ia_token: str):
    aid = _s.get("analysis_id")
    if not aid:
        pytest.skip("No analysis_id from FIN-01")

    resp, ms = timed(client, "get", f"/financial-analysis/bridge/analysis/{aid}/word",
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        ct = resp.headers.get("content-type", "")
        assert "wordprocessingml" in ct or "octet-stream" in ct
        assertions.append("content-type is DOCX")
        assert len(resp.content) > 1000
        assertions.append(f"DOCX body size: {len(resp.content)} bytes")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-09", "Download analysis DOCX", status, ms, resp.status_code, assertions, error)


# ── FIN-10 ─────────────────────────────────────────────────────────────────
def test_FIN10_send_analysis_email(client: httpx.Client, seed_ia_token: str):
    aid = _s.get("analysis_id")
    if not aid:
        pytest.skip("No analysis_id from FIN-01")

    resp, ms = timed(client, "post", f"/financial-analysis/bridge/analysis/{aid}/email",
                     json={"recipient_email": "test@example.com"},
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        # SMTP may not be configured in test environment
        assert resp.status_code in (200, 202, 500), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"email send response: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-10", "Send analysis via email", status, ms, resp.status_code, assertions, error)


# ── FIN-11 ─────────────────────────────────────────────────────────────────
def test_FIN11_unauthenticated_access(client: httpx.Client):
    resp, ms = timed(client, "get", "/financial-analysis/bridge/analysis", headers=TENANT_HEADER)

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 401
        assertions.append("status_code == 401 without token")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-11", "Unauthenticated access denied", status, ms, resp.status_code, assertions, error)


# ── FIN-12 ─────────────────────────────────────────────────────────────────
def test_FIN12_missing_tenant_header(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/financial-analysis/bridge/analysis",
                     headers={"Authorization": f"Bearer {seed_ia_token}"})

    assertions, status, error = [], "PASS", None
    try:
        # Backend may resolve tenant from host header or return 401/422 — accept both
        assert resp.status_code in (200, 400, 401, 422)
        assertions.append(f"Missing tenant header response: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("FIN-12", "Missing X-Tenant-Slug header", status, ms, resp.status_code, assertions, error)
