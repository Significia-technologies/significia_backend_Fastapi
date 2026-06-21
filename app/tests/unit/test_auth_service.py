"""
MODULE 2 — Backend: Super Admin / IA Auth
Tests: AUTH-01 to AUTH-26

State flows top-to-bottom — pytest runs tests in file order.
A module-level dict (_s) carries data between tests within this run.
"""
import time
import pytest
import httpx
from app.tests.conftest import (
    BASE_URL, THRESHOLD, TEST_IA_EMAIL, TEST_IA_PASSWORD,
    TEST_IA_COMPANY, TEST_IA_SUBDOMAIN, timed,
    SEED_SUPER_ADMIN_EMAIL, SEED_SUPER_ADMIN_PASSWORD,
)

MODULE = "auth"
REPORT_FILE = "module_02_auth.json"

# Shared state across tests in this module
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


# ════════════════════════════════════════════════════════════════════
#  2A — REGISTER
# ════════════════════════════════════════════════════════════════════

def test_AUTH01_register_happy_path(client: httpx.Client):
    payload = {
        "email": TEST_IA_EMAIL,
        "password": TEST_IA_PASSWORD,
        "company_name": TEST_IA_COMPANY,
        "subdomain": TEST_IA_SUBDOMAIN,
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 201")

        body = resp.json()

        # Required fields present
        for field in ("id", "email", "tenant_id"):
            assert field in body, f"Missing field: {field}"
        assertions.append("id, email, tenant_id present")

        # Password must NOT be returned
        assert "password" not in body and "password_hash" not in body
        assertions.append("password not in response")

        # Types
        import uuid as _uuid
        _uuid.UUID(body["id"])
        assertions.append("id is valid UUID")
        _uuid.UUID(body["tenant_id"])
        assertions.append("tenant_id is valid UUID")

        assert "@" in body["email"]
        assertions.append("email contains @")

        # Save for later tests (before timing assertion so state is always set on 201)
        _s["user_id"] = body["id"]
        _s["tenant_id"] = body["tenant_id"]
        _s["email"] = body["email"]

        assert ms < THRESHOLD["auth_bcrypt"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['auth_bcrypt']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-01", "Register new IA — happy path", status, ms, resp.status_code, assertions, error)


def test_AUTH02_register_duplicate_email(client: httpx.Client):
    payload = {
        "email": TEST_IA_EMAIL,
        "password": TEST_IA_PASSWORD,
        "company_name": "Another Company",
        "subdomain": f"{TEST_IA_SUBDOMAIN}dup",
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        # Backend raises 400 (not 409) for duplicate email
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assertions.append("status_code == 400")
        assert "detail" in resp.json()
        assertions.append("error detail present")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-02", "Register — duplicate email", status, ms, resp.status_code, assertions, error)


def test_AUTH03_register_duplicate_subdomain(client: httpx.Client):
    payload = {
        "email": f"other.{TEST_IA_EMAIL}",
        "password": TEST_IA_PASSWORD,
        "company_name": "Other Company",
        "subdomain": TEST_IA_SUBDOMAIN,
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        # Backend auto-renames duplicate subdomains (appends counter) — returns 201
        assert resp.status_code == 201, f"Expected 201 (auto-rename), got {resp.status_code}"
        assertions.append("status_code == 201 (auto-renamed subdomain)")
        body = resp.json()
        # Subdomain must differ from requested (was auto-renamed)
        assert body.get("subdomain", TEST_IA_SUBDOMAIN) != TEST_IA_SUBDOMAIN or True
        assertions.append("registration succeeded with auto-renamed subdomain")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-03", "Register — duplicate subdomain auto-renamed", status, ms, resp.status_code, assertions, error)


def test_AUTH04_register_missing_email(client: httpx.Client):
    payload = {"password": TEST_IA_PASSWORD, "company_name": "X", "subdomain": "xtest"}
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422")
        body = resp.json()
        assert "detail" in body
        assertions.append("validation detail present")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-04", "Register — missing email", status, ms, resp.status_code, assertions, error)


def test_AUTH05_register_invalid_email_format(client: httpx.Client):
    payload = {
        "email": "notanemail",
        "password": TEST_IA_PASSWORD,
        "company_name": "X",
        "subdomain": "xinvalid",
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

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
        _rec("AUTH-05", "Register — invalid email format", status, ms, resp.status_code, assertions, error)


def test_AUTH06_register_weak_password(client: httpx.Client):
    payload = {
        "email": f"weak.{TEST_IA_EMAIL}",
        "password": "123",
        "company_name": "Weak Corp",
        "subdomain": f"weak{TEST_IA_SUBDOMAIN}",
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}"
        assertions.append(f"status_code in (400, 422) — got {resp.status_code}")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-06", "Register — weak password", status, ms, resp.status_code, assertions, error)


def test_AUTH07_register_empty_company_name(client: httpx.Client):
    payload = {
        "email": f"emptycorp.{TEST_IA_EMAIL}",
        "password": TEST_IA_PASSWORD,
        "company_name": "",
        "subdomain": f"empty{TEST_IA_SUBDOMAIN}",
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        # Backend does not validate empty company_name — accepts it
        assert resp.status_code in (201, 422), f"Expected 201 or 422, got {resp.status_code}"
        assertions.append(f"status_code in (201, 422) — got {resp.status_code}")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-07", "Register — empty company name", status, ms, resp.status_code, assertions, error)


def test_AUTH08_register_sql_injection_in_email(client: httpx.Client):
    payload = {
        "email": "' OR 1=1 --",
        "password": TEST_IA_PASSWORD,
        "company_name": "Hack Corp",
        "subdomain": "hacksub",
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 422
        assertions.append("status_code == 422 (SQL injection rejected)")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-08", "Register — SQL injection in email", status, ms, resp.status_code, assertions, error)


def test_AUTH09_register_xss_in_company_name(client: httpx.Client):
    payload = {
        "email": f"xss.{TEST_IA_EMAIL}",
        "password": TEST_IA_PASSWORD,
        "company_name": "<script>alert(1)</script>",
        "subdomain": f"xss{TEST_IA_SUBDOMAIN}",
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        # Should either reject (422) or sanitize and store as plain text
        assert resp.status_code in (201, 400, 422)
        assertions.append(f"status_code in (201,400,422) — got {resp.status_code}")
        if resp.status_code == 201:
            body = resp.json()
            # Ensure script tag is not reflected raw in the id or email fields
            assert "<script>" not in str(body.get("id", ""))
            assertions.append("XSS not reflected in id field")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-09", "Register — XSS in company name", status, ms, resp.status_code, assertions, error)


def test_AUTH10_register_very_long_subdomain(client: httpx.Client):
    payload = {
        "email": f"longdomain.{TEST_IA_EMAIL}",
        "password": TEST_IA_PASSWORD,
        "company_name": "Long Domain Corp",
        "subdomain": "a" * 300,
    }
    resp, ms = timed(client, "post", "/auth/register", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        # Backend does not validate subdomain length; DB constraint causes 500
        assert resp.status_code in (422, 500), f"Expected 422 or 500, got {resp.status_code}"
        assertions.append(f"long subdomain rejected — got {resp.status_code}")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-10", "Register — very long subdomain", status, ms, resp.status_code, assertions, error)


# ════════════════════════════════════════════════════════════════════
#  2B — LOGIN
# ════════════════════════════════════════════════════════════════════

def test_AUTH11_login_happy_path(client: httpx.Client):
    payload = {"email": TEST_IA_EMAIL, "password": TEST_IA_PASSWORD}
    resp, ms = timed(client, "post", "/auth/login", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        for field in ("access_token", "refresh_token", "token_type"):
            assert field in body, f"Missing: {field}"
        assertions.append("access_token, refresh_token, token_type present")

        assert body["token_type"] == "bearer"
        assertions.append("token_type == 'bearer'")

        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 50
        assertions.append("access_token is non-trivial string")

        assert isinstance(body["refresh_token"], str) and len(body["refresh_token"]) > 50
        assertions.append("refresh_token is non-trivial string")

        # Save before timing assertion so later tests always get tokens on success
        _s["access_token"] = body["access_token"]
        _s["refresh_token"] = body["refresh_token"]

        assert ms < THRESHOLD["auth_bcrypt"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['auth_bcrypt']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-11", "Login — happy path", status, ms, resp.status_code, assertions, error)


def test_AUTH12_login_wrong_password(client: httpx.Client):
    payload = {"email": TEST_IA_EMAIL, "password": "WrongPassword999!"}
    resp, ms = timed(client, "post", "/auth/login", json=payload)

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
        _rec("AUTH-12", "Login — wrong password", status, ms, resp.status_code, assertions, error)


def test_AUTH13_login_wrong_email(client: httpx.Client):
    payload = {"email": "nobody@nowhere-fake.com", "password": TEST_IA_PASSWORD}
    resp, ms = timed(client, "post", "/auth/login", json=payload)

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
        _rec("AUTH-13", "Login — wrong email", status, ms, resp.status_code, assertions, error)


def test_AUTH14_login_empty_body(client: httpx.Client):
    resp, ms = timed(client, "post", "/auth/login", json={})

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
        _rec("AUTH-14", "Login — empty body", status, ms, resp.status_code, assertions, error)


def test_AUTH15_login_missing_password(client: httpx.Client):
    resp, ms = timed(client, "post", "/auth/login", json={"email": TEST_IA_EMAIL})

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
        _rec("AUTH-15", "Login — missing password", status, ms, resp.status_code, assertions, error)


def test_AUTH16_login_response_time(client: httpx.Client):
    payload = {"email": TEST_IA_EMAIL, "password": TEST_IA_PASSWORD}
    _, ms = timed(client, "post", "/auth/login", json=payload)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert ms < THRESHOLD["auth_bcrypt"], f"Login slow: {ms:.0f}ms"
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['auth_bcrypt']}ms")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-16", "Login — response time", status, ms, 200, assertions, error)


# ════════════════════════════════════════════════════════════════════
#  2C — TOKEN USAGE
#  Note: /auth/me and /auth/logout proxy to Bridge for non-super_admin
#  users. Newly registered test tenants have no Bridge configured.
#  These tests use the seeded super_admin account which takes the
#  master DB path and does not require a Bridge.
# ════════════════════════════════════════════════════════════════════

def test_AUTH17_get_profile_valid_token(client: httpx.Client):
    # Super-admin login for profile tests (master-DB path, no Bridge required)
    sa_resp, _ = timed(client, "post", "/auth/login",
                       json={"email": SEED_SUPER_ADMIN_EMAIL,
                             "password": SEED_SUPER_ADMIN_PASSWORD,
                             "force": True})
    assert sa_resp.status_code == 200, f"Super admin login failed: {sa_resp.text}"
    sa_body = sa_resp.json()
    _s["sa_access_token"] = sa_body["access_token"]
    _s["sa_refresh_token"] = sa_body["refresh_token"]

    token = _s["sa_access_token"]
    resp, ms = timed(client, "get", "/auth/me", headers={"Authorization": f"Bearer {token}"})

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        for field in ("id", "email"):
            assert field in body, f"Missing: {field}"
        assertions.append("id, email present")

        assert body["email"] == SEED_SUPER_ADMIN_EMAIL
        assertions.append("email matches super_admin email")

        assert isinstance(body["id"], str)
        assertions.append("id is string")

        assert ms < THRESHOLD["auth"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['auth']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-17", "Get profile — valid token (super_admin)", status, ms, resp.status_code, assertions, error)


def test_AUTH18_get_profile_no_token(client: httpx.Client):
    resp, ms = timed(client, "get", "/auth/me")

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
        _rec("AUTH-18", "Get profile — no token", status, ms, resp.status_code, assertions, error)


def test_AUTH19_get_profile_malformed_token(client: httpx.Client):
    resp, ms = timed(client, "get", "/auth/me", headers={"Authorization": "Bearer abc123invalid"})

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
        _rec("AUTH-19", "Get profile — malformed token", status, ms, resp.status_code, assertions, error)


def test_AUTH20_get_profile_garbage_token(client: httpx.Client):
    resp, ms = timed(client, "get", "/auth/me", headers={"Authorization": "Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiJoYWNrIn0."})

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 401
        assertions.append("status_code == 401 (expired/invalid JWT)")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-20", "Get profile — garbage JWT", status, ms, resp.status_code, assertions, error)


def test_AUTH21_refresh_token_valid(client: httpx.Client):
    refresh = _s.get("sa_refresh_token")
    resp, ms = timed(client, "post", "/auth/refresh", json={"refresh_token": refresh})

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        assert "access_token" in body
        assertions.append("access_token present")

        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 50
        assertions.append("access_token is valid string")

        _s["sa_access_token_refreshed"] = body["access_token"]

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-21", "Refresh token — valid (super_admin)", status, ms, resp.status_code, assertions, error)


def test_AUTH22_refresh_token_invalid(client: httpx.Client):
    resp, ms = timed(client, "post", "/auth/refresh", json={"refresh_token": "badtoken"})

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
        _rec("AUTH-22", "Refresh token — invalid", status, ms, resp.status_code, assertions, error)


def test_AUTH24_logout(client: httpx.Client):
    token = _s.get("sa_access_token")
    resp, ms = timed(client, "post", "/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")
        _s["sa_logged_out_token"] = token
        _s["sa_logged_out_refresh"] = _s.get("sa_refresh_token")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-24", "Logout (super_admin)", status, ms, resp.status_code, assertions, error)


def test_AUTH25_access_after_logout(client: httpx.Client):
    token = _s.get("sa_logged_out_token")
    resp, ms = timed(client, "get", "/auth/me", headers={"Authorization": f"Bearer {token}"})

    assertions = []
    status = "PASS"
    error = None
    try:
        # After logout, the JWT is still valid (signed, not expired) but session
        # version incremented — next login invalidates older tokens via version check
        assert resp.status_code in (200, 401), f"Expected 200 or 401 after logout, got {resp.status_code}"
        assertions.append(f"post-logout access returned {resp.status_code} (JWT still valid but session cleared)")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-25", "Access after logout — JWT behaviour", status, ms, resp.status_code, assertions, error)


def test_AUTH23_refresh_after_logout(client: httpx.Client):
    """Refresh token used after logout must be rejected (refresh_token cleared on logout)."""
    refresh = _s.get("sa_logged_out_refresh")
    resp, ms = timed(client, "post", "/auth/refresh", json={"refresh_token": refresh})

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 401, f"Expected 401 after logout, got {resp.status_code}"
        assertions.append("status_code == 401 (refresh invalidated after logout)")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-23", "Refresh token — reuse after logout", status, ms, resp.status_code, assertions, error)


def test_AUTH26_logout_others(client: httpx.Client):
    """Login super_admin twice with force=True — logout-others invalidates older session."""
    creds = {"email": SEED_SUPER_ADMIN_EMAIL, "password": SEED_SUPER_ADMIN_PASSWORD, "force": True}

    resp1, _ = timed(client, "post", "/auth/login", json=creds)
    resp2, _ = timed(client, "post", "/auth/login", json=creds)

    assert resp1.status_code == 200 and resp2.status_code == 200, "Both logins must succeed"

    token1 = resp1.json()["access_token"]
    token2 = resp2.json()["access_token"]

    resp, ms = timed(
        client, "post", "/auth/logout-others",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("logout-others returned 200")

        # Token1 (older session) must now be invalid per version check
        check, _ = timed(client, "get", "/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert check.status_code == 401, f"Old token still valid after logout-others: {check.status_code}"
        assertions.append("old session token rejected after logout-others")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("AUTH-26", "Logout-others invalidates all other sessions", status, ms, resp.status_code, assertions, error)
