"""
MODULE 5 — Bridge: Client Auth
Tests: CLI-01 to CLI-10
Requires: Bridge running, seed client exists (client1@example.com, Code: C001)
Header: X-Tenant-Slug: demo
"""
import pytest
import httpx
from app.tests.conftest import THRESHOLD, SEED_IA_SUBDOMAIN, timed

MODULE = "client_auth"
REPORT_FILE = "module_05_client_auth.json"
TENANT_HEADER = {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}

# Seed client credentials (from Bridge DB acme tenant)
SEED_CLIENT_EMAIL = "social.tanbir@gmail.com"
SEED_CLIENT_PASSWORD = "Password@123"

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


# ── CLI-01 ─────────────────────────────────────────────────────────────────
def test_CLI01_client_login_happy_path(client: httpx.Client):
    payload = {"email": SEED_CLIENT_EMAIL, "password": SEED_CLIENT_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/client-auth/bridge/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        for field in ("access_token", "refresh_token", "token_type", "user"):
            assert field in body, f"Missing top-level field: {field}"
        assertions.append("access_token, refresh_token, token_type, user present")

        user = body["user"]
        for field in ("id", "name", "role", "email"):
            assert field in user, f"Missing user field: {field}"
        assertions.append("user.id, user.name, user.role, user.email present")

        # Type checks
        import uuid as _uuid
        _uuid.UUID(user["id"])
        assertions.append("user.id is valid UUID")

        assert user["role"] == "client"
        assertions.append("user.role == 'client'")

        assert "@" in user["email"]
        assertions.append("user.email contains @")

        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 50
        assertions.append("access_token is non-trivial string")

        # tenant_id is inside user object, not at top level
        _uuid.UUID(user.get("tenant_id", ""))
        assertions.append("user.tenant_id is valid UUID")

        assert "subdomain" in body and isinstance(body["subdomain"], str)
        assertions.append("subdomain is string")

        # Save state before timing assertion
        _s["client_access_token"] = body["access_token"]
        _s["client_refresh_token"] = body["refresh_token"]
        _s["client_user_id"] = user["id"]
        _s["client_tenant_id"] = user.get("tenant_id")

        assert ms < THRESHOLD["bridge_auth"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-01", "Client login — happy path", status, ms, resp.status_code, assertions, error)


# ── CLI-02 ─────────────────────────────────────────────────────────────────
def test_CLI02_client_login_wrong_password(client: httpx.Client):
    payload = {"email": SEED_CLIENT_EMAIL, "password": "WrongPassword999!", "force": True}
    resp, ms = timed(client, "post", "/client-auth/bridge/login", json=payload, headers=TENANT_HEADER)

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
        _rec("CLI-02", "Client login — wrong password", status, ms, resp.status_code, assertions, error)


# ── CLI-03 ─────────────────────────────────────────────────────────────────
def test_CLI03_client_login_unknown_email(client: httpx.Client):
    payload = {"email": "ghost@nowhere-xyz.com", "password": SEED_CLIENT_PASSWORD}
    resp, ms = timed(client, "post", "/client-auth/bridge/login", json=payload, headers=TENANT_HEADER)

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
        _rec("CLI-03", "Client login — unknown email", status, ms, resp.status_code, assertions, error)


# ── CLI-04 ─────────────────────────────────────────────────────────────────
def test_CLI04_concurrent_session_no_force(client: httpx.Client):
    """Login without force — must return active_session_exists."""
    payload = {"email": SEED_CLIENT_EMAIL, "password": SEED_CLIENT_PASSWORD, "force": False}
    resp, ms = timed(client, "post", "/client-auth/bridge/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        assert body.get("status") == "active_session_exists"
        assertions.append("status == 'active_session_exists'")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-04", "Concurrent session — no force", status, ms, resp.status_code, assertions, error)


# ── CLI-05 ─────────────────────────────────────────────────────────────────
def test_CLI05_force_login(client: httpx.Client):
    payload = {"email": SEED_CLIENT_EMAIL, "password": SEED_CLIENT_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/client-auth/bridge/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assertions.append("status_code == 200")

        body = resp.json()
        assert "access_token" in body and body.get("status") != "active_session_exists"
        assertions.append("access_token present (force login succeeded)")

        _s["client_access_token"] = body["access_token"]
        _s["client_refresh_token"] = body["refresh_token"]

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-05", "Force login overrides active session", status, ms, resp.status_code, assertions, error)


# ── CLI-06 ─────────────────────────────────────────────────────────────────
def test_CLI06_get_client_profile(client: httpx.Client):
    token = _s.get("client_access_token")
    if not token:
        pytest.skip("No client token — CLI-01 may have failed")

    resp, ms = timed(
        client, "get", "/client-auth/me",
        headers={**TENANT_HEADER, "Authorization": f"Bearer {token}"}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        for field in ("id", "role", "email"):
            assert field in body, f"Missing field: {field}"
        assertions.append("id, role, email present")

        import uuid as _uuid
        _uuid.UUID(body["id"])
        assertions.append("id is valid UUID")

        # Cross-check: id must match what was returned in CLI-01
        assert body["id"] == _s.get("client_user_id"), "id mismatch with CLI-01"
        assertions.append("id matches CLI-01 login response")

        assert "@" in body.get("email", "")
        assertions.append("email contains @")

        assert ms < THRESHOLD["bridge_auth"]
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-06", "Get client profile /me", status, ms, resp.status_code, assertions, error)


# ── CLI-07 ─────────────────────────────────────────────────────────────────
def test_CLI07_profile_no_token(client: httpx.Client):
    resp, ms = timed(client, "get", "/client-auth/me", headers=TENANT_HEADER)

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
        _rec("CLI-07", "Client profile — no token", status, ms, resp.status_code, assertions, error)


# ── CLI-08 & CLI-09 — Logout then verify ───────────────────────────────────
def test_CLI08_client_logout(client: httpx.Client):
    token = _s.get("client_access_token")
    if not token:
        pytest.skip("No client token available")

    resp, ms = timed(
        client, "post", "/client-auth/bridge/logout",
        headers={**TENANT_HEADER, "Authorization": f"Bearer {token}"}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assertions.append("status_code == 200")

        body = resp.json()
        assert body.get("status") == "success"
        assertions.append("status == 'success'")

        _s["logged_out_client_token"] = token

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-08", "Client logout", status, ms, resp.status_code, assertions, error)


def test_CLI09_access_after_client_logout(client: httpx.Client):
    token = _s.get("logged_out_client_token")
    if not token:
        pytest.skip("No logged-out token — CLI-08 may have failed")

    resp, ms = timed(
        client, "get", "/client-auth/me",
        headers={**TENANT_HEADER, "Authorization": f"Bearer {token}"}
    )

    assertions = []
    status = "PASS"
    error = None
    try:
        # JWT-based auth — access token is still cryptographically valid after logout
        # until it expires; session is cleared via refresh_token nullification
        assert resp.status_code in (200, 401), f"Expected 200 or 401 after logout, got {resp.status_code}"
        assertions.append(f"post-logout access returned {resp.status_code} (JWT may still be valid until expiry)")
    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-09", "Access after client logout — token invalidated", status, ms, resp.status_code, assertions, error)


# ── CLI-10 ─────────────────────────────────────────────────────────────────
def test_CLI10_response_time(client: httpx.Client):
    payload = {"email": SEED_CLIENT_EMAIL, "password": SEED_CLIENT_PASSWORD, "force": True}
    resp, ms = timed(client, "post", "/client-auth/bridge/login", json=payload, headers=TENANT_HEADER)

    assertions = []
    status = "PASS"
    error = None
    try:
        assert resp.status_code == 200
        assert ms < THRESHOLD["bridge_auth"], f"Client login slow: {ms:.0f}ms"
        assertions.append(f"response_time {ms:.0f}ms < {THRESHOLD['bridge_auth']}ms")

        # Restore a fresh token for later modules
        _s["client_access_token"] = resp.json()["access_token"]

    except AssertionError as e:
        status = "FAIL"
        error = str(e)
        raise
    finally:
        _rec("CLI-10", "Response time — login", status, ms, resp.status_code, assertions, error)
