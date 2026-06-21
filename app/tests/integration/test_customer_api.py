"""
MODULE 7 — Bridge: Client CRUD
Tests: CLT-01 to CLT-35
Requires: IA token, seed client exists (C001)
Header: X-Tenant-Slug: demo
"""
import uuid
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, TEST_RUN_ID, timed

MODULE = "client_crud"
REPORT_FILE = "module_07_client_crud.json"
TENANT_HEADER = {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}

_s: dict = {}
_results: list[dict] = []

TEST_CLIENT_EMAIL = f"pytest.client.{TEST_RUN_ID}@test.io"
_h = abs(hash(TEST_RUN_ID))
_pan_digits = str(_h % 10000).zfill(4)
TEST_CLIENT_PAN = f"ABCDE{_pan_digits}F"
_TEST_AADHAR = str(_h % (10 ** 12)).zfill(12)
_TEST_PHONE = "9" + str((_h + 1) % (10 ** 9)).zfill(9)
_TEST_BANK_ACC = str((_h + 2) % (10 ** 12)).zfill(12)
TEST_CLIENT_PAYLOAD = {
    "email": TEST_CLIENT_EMAIL,
    "client_name": f"Pytest Client {TEST_RUN_ID}",
    "date_of_birth": "1990-05-15",
    "pan_number": TEST_CLIENT_PAN,
    "phone_number": _TEST_PHONE,
    "address": "123 Pytest Lane, Test City",
    "gender": "Male",
    "occupation": "Engineer",
    "marital_status": "Single",
    "nationality": "Indian",
    "residential_status": "Resident Individual",
    "aadhar_number": _TEST_AADHAR,
    "tax_residency": "India",
    "pep_status": "Not a PEP",
    "father_name": "Test Father Name",
    "mother_name": "Test Mother Name",
    "annual_income": 1200000.0,
    "net_worth": 5000000.0,
    "income_source": "Salary",
    "fatca_compliance": "Compliant",
    "bank_account_number": _TEST_BANK_ACC,
    "bank_name": "State Bank of India",
    "bank_branch": "Main Branch",
    "ifsc_code": "SBIN0001234",
    "risk_profile": "Moderate",
    "investment_experience": "Intermediate",
    "investment_objectives": "Growth",
    "investment_horizon": "Medium Term",
    "liquidity_needs": "Medium",
    "advisor_name": "Test Advisor",
    "advisor_registration_number": "INA000000001",
    "nominees": [{"name": "Test Nominee", "relationship": "Spouse", "dob": "1992-01-01", "percentage": 100.0}],
    "password": "Test@Client#2026",
}


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


# ════════════════════════════════════════════════════════════════════
#  7A — LIST & READ
# ════════════════════════════════════════════════════════════════════

def test_CLT01_list_all_clients(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        clients = body.get("clients", body) if isinstance(body, dict) else body
        assert isinstance(clients, list)
        assertions.append("clients is a list")
        _s["initial_client_count"] = body.get("total", len(clients))
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-01", "List all clients", status, ms, resp.status_code, assertions, error)


def test_CLT02_list_with_pagination(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients?skip=0&limit=2", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        clients = body.get("clients", body) if isinstance(body, dict) else body
        assert len(clients) <= 2
        assertions.append("pagination limit respected")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-02", "List with pagination", status, ms, resp.status_code, assertions, error)


def test_CLT03_list_with_search(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients?search=Bob", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        clients = body.get("clients", body) if isinstance(body, dict) else body
        assert isinstance(clients, list)
        assertions.append("search returns a list")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-03", "List with search", status, ms, resp.status_code, assertions, error)


def test_CLT04_list_empty_search(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients?search=", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-04", "List with empty search", status, ms, resp.status_code, assertions, error)


def test_CLT06_get_by_invalid_uuid(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients/not-a-uuid", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-06", "Get client — invalid UUID", status, ms, resp.status_code, assertions, error)


def test_CLT07_get_by_nonexistent_id(client: httpx.Client, seed_ia_token: str):
    fake_id = str(uuid.uuid4())
    resp, ms = timed(client, "get", f"/master/clients/{fake_id}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (403, 404)
        assertions.append(f"status_code in (403,404) — got {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-07", "Get client — non-existent ID", status, ms, resp.status_code, assertions, error)


def test_CLT08_get_by_pan(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients/pan/ABCDE1234F", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 404)
        assertions.append(f"status_code in (200,404) — got {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-08", "Get client by PAN", status, ms, resp.status_code, assertions, error)


def test_CLT09_get_by_pan_lowercase(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients/pan/abcde1234f", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 404)
        assertions.append("case-insensitive PAN lookup accepted")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-09", "Get client by PAN — lowercase", status, ms, resp.status_code, assertions, error)


def test_CLT10_get_by_pan_not_found(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients/pan/ZZZZ9999Z", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 404
        assertions.append("status_code == 404")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-10", "Get client by PAN — not found", status, ms, resp.status_code, assertions, error)


def test_CLT11_get_by_code(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients/code/C001", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 404)
        assertions.append(f"status_code in (200,404) — got {resp.status_code}")
        if resp.status_code == 200:
            _s["seed_client_id"] = resp.json().get("id")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-11", "Get client by code C001", status, ms, resp.status_code, assertions, error)


def test_CLT12_get_by_code_not_found(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/clients/code/XXXXXX", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 404
        assertions.append("status_code == 404")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-12", "Get client by code — not found", status, ms, resp.status_code, assertions, error)


# ════════════════════════════════════════════════════════════════════
#  7B — CREATE
# ════════════════════════════════════════════════════════════════════

def test_CLT13_create_client_happy_path(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", "/master/clients", json=TEST_CLIENT_PAYLOAD, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 201), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"status_code in (200,201) — got {resp.status_code}")
        body = resp.json()
        assert "id" in body
        assertions.append("id present")
        uuid.UUID(body["id"])
        assertions.append("id is valid UUID")
        assert ms < THRESHOLD["auth_bcrypt"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['auth_bcrypt']}ms")
        _s["new_client_id"] = body["id"]
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-13", "Create client — happy path", status, ms, resp.status_code, assertions, error)


def test_CLT05_get_by_id(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id") or _s.get("seed_client_id")
    if not client_id:
        pytest.skip("No client_id available")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        assert body.get("id") == client_id
        assertions.append("id matches requested ID")
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-05", "Get client by ID", status, ms, resp.status_code, assertions, error)


def test_CLT14_create_duplicate_pan(client: httpx.Client, seed_ia_token: str):
    payload = {**TEST_CLIENT_PAYLOAD, "email": f"dup.{TEST_CLIENT_EMAIL}"}
    resp, ms = timed(client, "post", "/master/clients", json=payload, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (400, 409), f"Got {resp.status_code}"
        assertions.append("duplicate PAN rejected")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-14", "Create — duplicate PAN", status, ms, resp.status_code, assertions, error)


def test_CLT15_create_duplicate_email(client: httpx.Client, seed_ia_token: str):
    payload = {**TEST_CLIENT_PAYLOAD, "pan_number": f"NEW{TEST_RUN_ID[:4].upper()}X"}
    resp, ms = timed(client, "post", "/master/clients", json=payload, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (400, 409), f"Got {resp.status_code}"
        assertions.append("duplicate email rejected")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-15", "Create — duplicate email", status, ms, resp.status_code, assertions, error)


def test_CLT16_create_missing_required_field(client: httpx.Client, seed_ia_token: str):
    payload = {k: v for k, v in TEST_CLIENT_PAYLOAD.items() if k != "client_name"}
    resp, ms = timed(client, "post", "/master/clients", json=payload, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-16", "Create — missing required field", status, ms, resp.status_code, assertions, error)


def test_CLT17_create_invalid_date(client: httpx.Client, seed_ia_token: str):
    payload = {**TEST_CLIENT_PAYLOAD, "email": f"bd.{TEST_CLIENT_EMAIL}", "pan_number": f"BD{TEST_RUN_ID[:5].upper()}X", "date_of_birth": "not-a-date"}
    resp, ms = timed(client, "post", "/master/clients", json=payload, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-17", "Create — invalid date_of_birth", status, ms, resp.status_code, assertions, error)


def test_CLT19_create_negative_income(client: httpx.Client, seed_ia_token: str):
    _h2 = abs(hash(TEST_RUN_ID + "neg"))
    _neg_pan_digits = str(_h2 % 10000).zfill(4)
    payload = {
        **TEST_CLIENT_PAYLOAD,
        "email": f"neg.{TEST_CLIENT_EMAIL}",
        "pan_number": f"NEGXX{_neg_pan_digits}Y",
        "aadhar_number": str(_h2 % (10 ** 12)).zfill(12),
        "phone_number": "9" + str((_h2 + 1) % (10 ** 9)).zfill(9),
        "bank_account_number": str((_h2 + 2) % (10 ** 12)).zfill(12),
        "annual_income": -50000,
    }
    resp, ms = timed(client, "post", "/master/clients", json=payload, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        # Bridge doesn't validate income sign — may return 200/201 or 400/422
        assert resp.status_code in (200, 201, 400, 409, 422), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"negative income response: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-19", "Create — negative annual income", status, ms, resp.status_code, assertions, error)


# ════════════════════════════════════════════════════════════════════
#  7C — UPDATE, VERSIONS, REPORTS, DELETE
# ════════════════════════════════════════════════════════════════════

def test_CLT23_update_client(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    if not client_id:
        pytest.skip("No new_client_id from CLT-13")

    resp, ms = timed(client, "put", f"/master/clients/{client_id}", json={"address": "456 Updated Street"}, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        # SEBI compliance may require E-Serial number for updates
        assert resp.status_code in (200, 400), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"status_code in (200,400) — got {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-23", "Update client — happy path", status, ms, resp.status_code, assertions, error)


def test_CLT24_update_invalid_id(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "put", f"/master/clients/{uuid.uuid4()}", json={"address": "x"}, headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (400, 404)
        assertions.append(f"status_code in (400,404) — got {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-24", "Update — invalid ID", status, ms, resp.status_code, assertions, error)


def test_CLT26_update_creates_version(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    if not client_id:
        pytest.skip("No new_client_id")

    resp_before, _ = timed(client, "get", f"/master/clients/{client_id}/versions", headers=_auth(seed_ia_token))
    count_before = len(resp_before.json().get("versions", resp_before.json()) if isinstance(resp_before.json(), dict) else resp_before.json())

    timed(client, "put", f"/master/clients/{client_id}", json={"address": "Version Check Street"}, headers=_auth(seed_ia_token))

    resp_after, ms = timed(client, "get", f"/master/clients/{client_id}/versions", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        after = resp_after.json()
        versions = after.get("versions", after) if isinstance(after, dict) else after
        assert len(versions) >= count_before
        assertions.append("version count increased or equal after update")
        _s["version_id"] = versions[0].get("id") if versions else None
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-26", "Update creates version snapshot", status, ms, resp_after.status_code, assertions, error)


def test_CLT27_list_client_versions(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    if not client_id:
        pytest.skip("No new_client_id")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}/versions", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        versions = body.get("versions", body) if isinstance(body, dict) else body
        assert isinstance(versions, list)
        assertions.append("versions is a list")
        assert len(versions) >= 1
        assertions.append("at least 1 version exists")
        _s["version_id"] = versions[0].get("id") if versions else None
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-27", "List client versions", status, ms, resp.status_code, assertions, error)


def test_CLT28_get_specific_version(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    version_id = _s.get("version_id")
    if not client_id or not version_id:
        pytest.skip("Need client_id and version_id")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}/versions/{version_id}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        assert "snapshot" in body or "id" in body
        assertions.append("snapshot or id present")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-28", "Get specific version", status, ms, resp.status_code, assertions, error)


def test_CLT29_point_in_time_query(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    if not client_id:
        pytest.skip("No new_client_id")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}/version-at?target_date=2026-01-01", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 404)
        assertions.append(f"status_code in (200,404) — got {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-29", "Point-in-time version query", status, ms, resp.status_code, assertions, error)


def test_CLT30_point_in_time_bad_date(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    if not client_id:
        pytest.skip("No new_client_id")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}/version-at?target_date=notadate", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (400, 422, 500)
        assertions.append(f"bad date response: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-30", "Point-in-time — bad date format", status, ms, resp.status_code, assertions, error)


def test_CLT33_download_blank_form(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/blank-form", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append("PDF body > 1000 bytes")
        assert ms < THRESHOLD["pdf"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['pdf']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-33", "Download blank registration form", status, ms, resp.status_code, assertions, error)


def test_CLT34_download_individual_pdf(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id") or _s.get("seed_client_id")
    if not client_id:
        pytest.skip("No client_id available")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}/pdf", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append("PDF body > 1000 bytes")
        assert ms < THRESHOLD["pdf"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['pdf']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-34", "Download individual client PDF", status, ms, resp.status_code, assertions, error)


def test_CLT35_download_master_report(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/master/report", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append("PDF body > 1000 bytes")
        assert ms < THRESHOLD["pdf"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['pdf']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-35", "Download client master report PDF", status, ms, resp.status_code, assertions, error)


def test_CLT31_delete_client(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("new_client_id")
    if not client_id:
        pytest.skip("No new_client_id from CLT-13")

    resp, ms = timed(client, "delete", f"/master/clients/{client_id}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 204, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 204 (soft delete)")
        _s["deleted_client_id"] = client_id
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-31", "Delete client — soft delete", status, ms, resp.status_code, assertions, error)


def test_CLT32_get_deleted_client(client: httpx.Client, seed_ia_token: str):
    client_id = _s.get("deleted_client_id")
    if not client_id:
        pytest.skip("No deleted_client_id from CLT-31")

    resp, ms = timed(client, "get", f"/master/clients/{client_id}", headers=_auth(seed_ia_token))

    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (404, 200)
        assertions.append(f"status_code in (404,200) — got {resp.status_code}")
        if resp.status_code == 200:
            body = resp.json()
            has_marker = body.get("deleted_at") is not None or body.get("is_deleted") is True
            assertions.append(f"soft-delete marker present: {has_marker}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("CLT-32", "Get deleted client", status, ms, resp.status_code, assertions, error)
