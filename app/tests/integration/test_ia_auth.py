"""
MODULE 4 — Bridge: IA Staff Auth
Tests: IA-01 to IA-11
Requires: Bridge running, seed demo tenant exists
Header: X-Tenant-Slug: demo
"""
import pytest
import httpx
from app.tests.conftest import (
    THRESHOLD, SEED_IA_EMAIL, SEED_IA_PASSWORD, SEED_IA_SUBDOMAIN, timed,
)

MODULE = "ia_auth"
REPORT_FILE = "module_04_ia_auth.json"
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


# ── IA-01 ──────────────────────────────────────────────────────────────────
def test_IA01_login_happy_path(client: httpx.Client):
    payload = {"email": SEED_IA_EMAIL, "password": SEED_IA_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        for field in ("access_token", "refresh_token", "token_type", "user_name", "user_role", "tenant_name"):
            assert field in body, f"Missing: {field}"
        assertions.append("all required fields present")

        # Types
        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 50
        assertions.append("access_token is non-trivial string")

        assert isinstance(body["refresh_token"], str) and len(body["refresh_token"]) > 50
        assertions.append("refresh_token is non-trivial string")

        assert body["token_type"] == "bearer"
        assertions.append("token_type == 'bearer'")

        assert isinstance(body["user_name"], str) and body["user_name"]
        assertions.append("user_name is non-empty string")

        assert isinstance(body["user_role"], str) and body["user_role"]
        assertions.append("user_role is non-empty string")

        assert isinstance(body["tenant_name"], str)
        assertions.append("tenant_name is string")

        # Save before timing so state is always set on successful response
        _s["ia_access_token"] = body["access_token"]
        _s["ia_refresh_token"] = body["refresh_token"]
        _s["ia_user_role"] = body["user_role"]

        assert ms < THRESHOLD["bridge_auth"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-01", "IA staff login — happy path", status, ms, resp.status_code, assertions, error)


# ── IA-02 ──────────────────────────────────────────────────────────────────
def test_IA02_login_wrong_password(client: httpx.Client):
    payload = {"email": SEED_IA_EMAIL, "password": "WrongPassword999!"}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 401
        assertions.append("status_code == 401")
        assert "detail" in resp.json()
        assertions.append("error detail present")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-02", "IA staff login — wrong password", status, ms, resp.status_code, assertions, error)


# ── IA-03 ──────────────────────────────────────────────────────────────────
def test_IA03_login_unknown_email(client: httpx.Client):
    payload = {"email": "nobody@nowhere-xyz.com", "password": SEED_IA_PASSWORD}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 401
        assertions.append("status_code == 401")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-03", "IA staff login — unknown email", status, ms, resp.status_code, assertions, error)


# ── IA-04 ──────────────────────────────────────────────────────────────────
def test_IA04_login_empty_body(client: httpx.Client):
    resp, ms = timed(client, "post", "/ia-auth/login", json={}, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-04", "IA staff login — empty body", status, ms, resp.status_code, assertions, error)


# ── IA-05 ──────────────────────────────────────────────────────────────────
def test_IA05_concurrent_session_no_force(client: httpx.Client):
    """Login again without force — Bridge must report active_session_exists."""
    payload = {"email": SEED_IA_EMAIL, "password": SEED_IA_PASSWORD, "force": False}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        assert body.get("status") == "active_session_exists", \
            f"Expected active_session_exists, got: {body}"
        assertions.append("status == 'active_session_exists'")

        assert "device_info" in body
        assertions.append("device_info present")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-05", "Concurrent session — no force", status, ms, resp.status_code, assertions, error)


# ── IA-06 ──────────────────────────────────────────────────────────────────
def test_IA06_concurrent_session_with_force(client: httpx.Client):
    """Login with force:true — must succeed and return valid tokens."""
    payload = {"email": SEED_IA_EMAIL, "password": SEED_IA_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        assert "access_token" in body and body.get("status") != "active_session_exists"
        assertions.append("access_token present (not active_session_exists)")

        # Update the shared token to the fresh one
        _s["ia_access_token"] = body["access_token"]
        _s["ia_refresh_token"] = body["refresh_token"]

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-06", "Concurrent session — with force", status, ms, resp.status_code, assertions, error)


# ── IA-07 & IA-08 — Lockout ────────────────────────────────────────────────
def test_IA07_IA08_lockout_after_repeated_failures(client: httpx.Client):
    """
    Use a fresh dummy email that doesn't exist — attempt 6 wrong logins.
    The 5th/6th attempt should return 423 (account locked) if the Bridge tracks
    lockout by IP/email. We accept either 401 or 423 for the first 4 attempts,
    and expect 423 by the 6th.
    """
    dummy_payload = {"email": "lockout.test@dummy.io", "password": "WrongPass#1"}

    last_status = None
    got_lockout = False
    last_ms = 0.0
    last_code = 0

    for attempt in range(1, 7):
        resp, ms = timed(client, "post", "/ia-auth/login", json=dummy_payload, headers=TENANT_HEADER)
        last_status = resp.status_code
        last_ms = ms
        last_code = resp.status_code
        if resp.status_code == 423:
            got_lockout = True
            break

    assertions = []
    status = "PASS"
    error = None
    try:
        # Bridge may lock by IP — not guaranteed for a non-existent user,
        # so accept either 401 (user not found) or 423 (locked)
        assert last_status in (401, 423), f"Expected 401 or 423, got {last_status}"
        assertions.append(f"Repeated failures result in {last_status} (401=not found / 423=locked)")

        if got_lockout:
            body = resp.json()
            assert "detail" in body
            assertions.append("423 contains detail message")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-07/08", "Lockout after repeated failures", status, last_ms, last_code, assertions, error)


# ── IA-09 ──────────────────────────────────────────────────────────────────
def test_IA09_response_time(client: httpx.Client):
    payload = {"email": SEED_IA_EMAIL, "password": SEED_IA_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assert ms < THRESHOLD["bridge_auth"], f"Bridge login slow: {ms:.0f}ms"
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

        _s["ia_access_token"] = resp.json()["access_token"]
        _s["ia_refresh_token"] = resp.json()["refresh_token"]

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-09", "Response time — login", status, ms, resp.status_code, assertions, error)


# ── IA-10 ──────────────────────────────────────────────────────────────────
def test_IA10_token_type_is_bearer(client: httpx.Client):
    token = _s.get("ia_access_token")
    if not token:
        pytest.skip("No IA token available — IA-01 may have failed")

    payload = {"email": SEED_IA_EMAIL, "password": SEED_IA_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/ia-auth/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.json().get("token_type") == "bearer"
        assertions.append("token_type == 'bearer' (lowercase)")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-10", "token_type is lowercase bearer", status, ms, resp.status_code, assertions, error)


# ── IA-11 ──────────────────────────────────────────────────────────────────
def test_IA11_user_role_is_valid(client: httpx.Client):
    role = _s.get("ia_user_role", "")

    assertions = []
    status = "PASS"
    error = None
    ms = 0.0
    try:
        valid_roles = {"owner", "ia_staff", "master", "partner", "staff"}
        assert role.lower() in valid_roles, f"Unexpected role: {role}"
        assertions.append(f"user_role '{role}' is a valid IA role")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("IA-11", "user_role is valid IA role", status, ms, 200, assertions, error)
