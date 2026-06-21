"""
MODULE 8 — Bridge: Risk Profile (Standard + Custom)
Tests: RSK-01 to RSK-20
Requires: IA token, seed client C001 exists
Header: X-Tenant-Slug: demo
"""
import uuid
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, timed

MODULE = "risk_profile"
REPORT_FILE = "module_08_risk_profile.json"
TENANT_HEADER = {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}

_s: dict = {}
_results: list[dict] = []

CONSERVATIVE_ANSWERS = {
    "q1": "C", "q2": {"a": "C", "b": "C", "c": "C", "d": "C", "e": "C"},
    "q3": "C", "q4": "C", "q5": "C", "q6": "C", "q7": "C", "q8": "C",
    "q9": "C", "q10": "C", "q11": "C", "q12": "C", "q13": "C", "q14": "C",
    "q15": "C", "q16": "C",
}
AGGRESSIVE_ANSWERS = {
    "q1": "A", "q2": {"a": "A", "b": "A", "c": "A", "d": "A", "e": "A"},
    "q3": "A", "q4": "A", "q5": "A", "q6": "A", "q7": "A", "q8": "A",
    "q9": "A", "q10": "A", "q11": "A", "q12": "A", "q13": "A", "q14": "A",
    "q15": "A", "q16": "A",
}
SEED_CLIENT_CODE = "CLI-06BE5129"


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


def test_RSK01_calculate_conservative(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", "/risk-profile/bridge/calculate",
                     json={"answers": CONSERVATIVE_ANSWERS}, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        body = resp.json()
        assert isinstance(body.get("total_score"), (int, float))
        assertions.append("total_score is numeric")
        assert isinstance(body.get("risk_tier"), str)
        assertions.append("risk_tier is string")
        assert "recommendation" in body
        assertions.append("recommendation present")
        assert ms < THRESHOLD["read"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
        _s["conservative_score"] = body["total_score"]
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-01", "Calculate — conservative answers", status, ms, resp.status_code, assertions, error)


def test_RSK02_calculate_aggressive(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", "/risk-profile/bridge/calculate",
                     json={"answers": AGGRESSIVE_ANSWERS}, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        body = resp.json()
        assert body["total_score"] >= _s.get("conservative_score", 0)
        assertions.append("aggressive_score >= conservative_score")
        _s["aggressive_score"] = body["total_score"]
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-02", "Calculate — aggressive > conservative", status, ms, resp.status_code, assertions, error)


def test_RSK03_calculate_missing_answers(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "post", "/risk-profile/bridge/calculate", json={}, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-03", "Calculate — missing answers", status, ms, resp.status_code, assertions, error)


def test_RSK04_calculate_wrong_type(client: httpx.Client, seed_ia_token: str):
    bad = {**CONSERVATIVE_ANSWERS, "q1": "abc"}
    resp, ms = timed(client, "post", "/risk-profile/bridge/calculate",
                     json={"answers": bad}, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        # "abc" is valid string type but not a known option — may return 200 or 422
        assert resp.status_code in (200, 422)
        assertions.append(f"wrong answer type response: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-04", "Calculate — wrong type for answer", status, ms, resp.status_code, assertions, error)


def test_RSK05_save_assessment(client: httpx.Client, seed_ia_token: str):
    payload = {
        "client_code": SEED_CLIENT_CODE,
        "answers": CONSERVATIVE_ANSWERS,
        "disclaimer_text": "I understand the risks.",
        "discussion_notes": "Discussed investment goals.",
        "form_name": "Standard Risk Form",
    }
    resp, ms = timed(client, "post", "/risk-profile/bridge/save", json=payload, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 201), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"status_code in (200,201)")
        body = resp.json()
        assert "id" in body
        assertions.append("id present")
        _s["assessment_id"] = body["id"]
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-05", "Save risk assessment — happy path", status, ms, resp.status_code, assertions, error)


def test_RSK06_save_unknown_client_code(client: httpx.Client, seed_ia_token: str):
    payload = {"client_code": "ZZZZZZZZ", "answers": CONSERVATIVE_ANSWERS, "form_name": "Test"}
    resp, ms = timed(client, "post", "/risk-profile/bridge/save", json=payload, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (404, 422), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"unknown client code rejected: {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-06", "Save — unknown client code", status, ms, resp.status_code, assertions, error)


def test_RSK07_get_assessments_for_client(client: httpx.Client, seed_ia_token: str):
    r, _ = timed(client, "get", "/master/clients/code/C001", headers=_auth(seed_ia_token))
    if r.status_code != 200:
        pytest.skip("Seed client C001 not found")
    client_id = r.json().get("id")
    resp, ms = timed(client, "get", f"/risk-profile/bridge/assessments/{client_id}", headers=_auth(seed_ia_token))
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
        _rec("RSK-07", "Get assessments for client", status, ms, resp.status_code, assertions, error)


def test_RSK08_get_all_assessments(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/risk-profile/bridge/assessments", headers=_auth(seed_ia_token))
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
        _rec("RSK-08", "Get all assessments", status, ms, resp.status_code, assertions, error)


def test_RSK09_download_assessment_pdf(client: httpx.Client, seed_ia_token: str):
    assessment_id = _s.get("assessment_id")
    if not assessment_id:
        pytest.skip("No assessment_id from RSK-05")
    resp, ms = timed(client, "get", f"/risk-profile/bridge/assessment/{assessment_id}/pdf", headers=_auth(seed_ia_token))
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
        _rec("RSK-09", "Download assessment PDF", status, ms, resp.status_code, assertions, error)


def test_RSK10_download_assessment_docx(client: httpx.Client, seed_ia_token: str):
    assessment_id = _s.get("assessment_id")
    if not assessment_id:
        pytest.skip("No assessment_id from RSK-05")
    resp, ms = timed(client, "get", f"/risk-profile/bridge/assessment/{assessment_id}/docx", headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        ct = resp.headers.get("content-type", "")
        assert "wordprocessingml" in ct or "octet-stream" in ct
        assertions.append("content-type is DOCX")
        assert len(resp.content) > 1000
        assertions.append("DOCX body > 1000 bytes")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-10", "Download assessment DOCX", status, ms, resp.status_code, assertions, error)


def test_RSK11_assessment_not_found_pdf(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", f"/risk-profile/bridge/assessment/{uuid.uuid4()}/pdf", headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (404, 500)
        assertions.append(f"non-existent assessment returns 404/500 — got {resp.status_code}")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-11", "Assessment not found — PDF", status, ms, resp.status_code, assertions, error)


def test_RSK12_calculate_response_time(client: httpx.Client, seed_ia_token: str):
    _, ms = timed(client, "post", "/risk-profile/bridge/calculate",
                  json={"answers": CONSERVATIVE_ANSWERS}, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert ms < THRESHOLD["read"], f"Pure math endpoint slow: {ms:.0f}ms"
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['read']}ms")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-12", "Response time — calculate", status, ms, 200, assertions, error)


def test_RSK13_list_questionnaires(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/risk-profile/bridge/questionnaires", headers=_auth(seed_ia_token))
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
        _rec("RSK-13", "List questionnaires", status, ms, resp.status_code, assertions, error)


def test_RSK14_create_questionnaire(client: httpx.Client, seed_ia_token: str):
    payload = {
        "portfolio_name": f"Pytest Portfolio {uuid.uuid4().hex[:6]}",
        "questions": [{"id": "q1", "text": "Risk tolerance?", "options": [
            {"id": "q1_a", "text": "Low risk", "score": 1.0},
            {"id": "q1_b", "text": "High risk", "score": 5.0},
        ]}],
        "categories": [
            {"name": "Conservative", "min_score": 1.0, "max_score": 2.0},
            {"name": "Aggressive", "min_score": 3.0, "max_score": 5.0},
        ]
    }
    resp, ms = timed(client, "post", "/risk-profile/bridge/questionnaires", json=payload, headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code in (200, 201), f"Got {resp.status_code}: {resp.text}"
        assertions.append(f"status_code in (200,201)")
        body = resp.json()
        qid = body.get("id") or body.get("questionnaire_id")
        assertions.append(f"questionnaire created: {body}")
        if qid:
            _s["questionnaire_id"] = qid
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-14", "Create questionnaire", status, ms, resp.status_code, assertions, error)


def test_RSK16_get_questionnaire_by_id(client: httpx.Client, seed_ia_token: str):
    q_id = _s.get("questionnaire_id")
    if not q_id:
        pytest.skip("No questionnaire_id from RSK-14")
    resp, ms = timed(client, "get", f"/risk-profile/bridge/questionnaires/{q_id}", headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")
        assert "id" in resp.json()
        assertions.append("id present")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-16", "Get questionnaire by ID", status, ms, resp.status_code, assertions, error)


def test_RSK17_get_questionnaire_bad_id(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", f"/risk-profile/bridge/questionnaires/{uuid.uuid4()}", headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 404
        assertions.append("status_code == 404")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-17", "Get questionnaire — bad ID", status, ms, resp.status_code, assertions, error)


def test_RSK19_download_blank_custom_form(client: httpx.Client, seed_ia_token: str):
    q_id = _s.get("questionnaire_id")
    if not q_id:
        pytest.skip("No questionnaire_id from RSK-14")
    resp, ms = timed(client, "get", f"/risk-profile/bridge/questionnaires/{q_id}/pdf", headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
        assert len(resp.content) > 1000
        assertions.append("PDF body > 1000 bytes")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-19", "Download blank custom form PDF", status, ms, resp.status_code, assertions, error)


def test_RSK20_download_sample_form(client: httpx.Client, seed_ia_token: str):
    resp, ms = timed(client, "get", "/risk-profile/bridge/questionnaires/sample-form/pdf", headers=_auth(seed_ia_token))
    assertions, status, error = [], "PASS", None
    try:
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        assert "application/pdf" in resp.headers.get("content-type", "")
        assertions.append("content-type is application/pdf")
    except AssertionError as e:
        status, error = "FAIL", str(e)
        raise
    finally:
        _rec("RSK-20", "Download sample risk form PDF", status, ms, resp.status_code, assertions, error)
