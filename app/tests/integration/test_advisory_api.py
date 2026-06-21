"""
MODULE 10 — Bridge: Investment Advice Notes (IANs)
Tests: IAN-01 to IAN-07
Requires: IA token, seed client C001 exists
Header: X-Tenant-Slug: demo
"""
import uuid
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, TEST_RUN_ID, timed

MODULE = "investment_advice_notes"
REPORT_FILE = "module_10_advisory.json"
TENANT_HEADER = {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}

_s: dict = {}
_results: list[dict] = []

SEED_CLIENT_ID = "7b3b4182-6f12-437c-a78b-48949d0332d3"
IAN_PAYLOAD = {
    "advice_date": "2024-01-20",
    "advice_type": "Portfolio Rebalancing",
    "recommendation": f"Pytest advice note {TEST_RUN_ID}. Increase equity allocation to 70%.",
    "rationale": "Market conditions favor equity for long-term growth.",
    "risk_level": "Moderate",
    "disclaimer": "This advice is based on current market conditions.",
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


# ── IAN-01 ─────────────────────────────────────────────────────────────────
def test_IAN01_list_advice_notes(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/advisory/investment-advice-notes",
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        items = body.get("items", body.get("notes", body)) if isinstance(body, dict) else body
        assert isinstance(items, list)
        assertions.append("response is array")
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-01", "List investment advice notes", status, ms, resp.status_code, assertions, error)


# ── IAN-02 ─────────────────────────────────────────────────────────────────
def test_IAN02_create_advice_note(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", f"/advisory/investment-advice-notes/{SEED_CLIENT_ID}",
                     json=IAN_PAYLOAD, headers=_auth(seed_ia_token))

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
        _s["ian_id"] = body["id"]
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-02", "Create advice note — happy path", status, ms, resp.status_code, assertions, error)


# ── IAN-03 ─────────────────────────────────────────────────────────────────
def test_IAN03_create_unknown_client(client: httpx.Client, seed_ia_token: str):
    fake_client_id = str(uuid.uuid4())
    resp, ms = timed(client, "post", f"/advisory/investment-advice-notes/{fake_client_id}",
                     json=IAN_PAYLOAD, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (400, 404, 500), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"unknown client rejected: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-03", "Create — unknown client code", status, ms, resp.status_code, assertions, error)


# ── IAN-04 ─────────────────────────────────────────────────────────────────
def test_IAN04_get_advice_note_by_id(client: httpx.Client, seed_ia_token: str):
    ian_id = _s.get("ian_id")
    if not ian_id:
        pytest.skip("No ian_id from IAN-02")

    resp, ms = timed(client, "get", f"/advisory/investment-advice-note/{ian_id}",
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        assert body.get("id") == ian_id
        assertions.append("id matches requested ian_id")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-04", "Get advice note by ID", status, ms, resp.status_code, assertions, error)


# ── IAN-05 ─────────────────────────────────────────────────────────────────
def test_IAN05_get_advice_note_bad_id(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", f"/advisory/investment-advice-note/{uuid.uuid4()}",
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (400, 404, 500), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"bad note ID rejected: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-05", "Get advice note — bad ID", status, ms, resp.status_code, assertions, error)


# ── IAN-06 ─────────────────────────────────────────────────────────────────
def test_IAN06_list_notes_for_client(client: httpx.Client, seed_ia_token: str):
    r, _ = timed(client, "get", "/master/clients/code/C001", headers=_auth(seed_ia_token))
    if r.status_code != 200:
        pytest.skip("Seed client C001 not found")
    client_id = r.json().get("id")

    resp, ms = timed(client, "get",
                     f"/advisory/investment-advice-notes/client/{client_id}",
                     headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        items = body.get("items", body.get("notes", body)) if isinstance(body, dict) else body
        assert isinstance(items, list)
        assertions.append("response is array")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-06", "List notes for client", status, ms, resp.status_code, assertions, error)


# ── IAN-07 ─────────────────────────────────────────────────────────────────
def test_IAN07_unauthenticated_access(client: httpx.Client):
    resp, ms = timed(client, "get", "/advisory/investment-advice-notes",
                     headers=TENANT_HEADER)

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 401
        assertions.append("status_code == 401 without token")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("IAN-07", "Unauthenticated access denied", status, ms, resp.status_code, assertions, error)
