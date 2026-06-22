"""
Shared fixtures, report writer, and HTTP client for all test modules.
All tests hit the live running server — no mocking.
"""
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any

import httpx
import pytest

# ── Constants ──────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8001/api/v1"
BRIDGE_BASE_URL = "http://localhost:9000"
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "test_reports")

# Unique suffix per test run so registrations never collide across runs
TEST_RUN_ID = uuid.uuid4().hex[:8]
TEST_IA_EMAIL = f"pytest.ia.{TEST_RUN_ID}@test.io"
TEST_IA_PASSWORD = "Test@Pytest#2026"
TEST_IA_COMPANY = f"PyTest Advisors {TEST_RUN_ID}"
TEST_IA_SUBDOMAIN = f"pytest{TEST_RUN_ID}"

# Super admin credentials (backend auth only)
SEED_SUPER_ADMIN_EMAIL = "alamtanbir@gmail.com"
SEED_SUPER_ADMIN_PASSWORD = "T@nbir#2026"

# Seed data (never delete these)
SEED_IA_EMAIL = "tanbir.official6@gmail.com"
SEED_IA_PASSWORD = "password"
SEED_IA_SUBDOMAIN = "acme"

# Response time thresholds (ms)
THRESHOLD = {
    "health": 500,
    "auth": 3000,
    "auth_bcrypt": 10000,  # bcrypt hash/verify is inherently slow
    "bridge_auth": 6000,
    "read": 3000,
    "write": 6000,
    "pdf": 15000,
    "export": 10000,
}


# ── Report Writer ──────────────────────────────────────────────────────────
class ReportWriter:
    """Accumulates test results and writes per-module JSON reports."""

    def __init__(self):
        self._modules: dict[str, list[dict]] = {}
        os.makedirs(REPORT_DIR, exist_ok=True)

    def record(
        self,
        module: str,
        test_id: str,
        name: str,
        status: str,
        response_time_ms: float,
        status_code: int,
        assertions: list[str],
        error: str | None = None,
    ):
        entry = {
            "id": test_id,
            "name": name,
            "status": status,
            "response_time_ms": round(response_time_ms, 2),
            "status_code": status_code,
            "assertions": assertions,
        }
        if error:
            entry["error"] = error
        self._modules.setdefault(module, []).append(entry)

    def write(self, module: str, filename: str):
        tests = self._modules.get(module, [])
        passed = sum(1 for t in tests if t["status"] == "PASS")
        failed = len(tests) - passed
        report = {
            "module": module,
            "run_at": datetime.utcnow().isoformat(),
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "tests": tests,
        }
        path = os.path.join(REPORT_DIR, filename)
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        return path


@pytest.fixture(scope="session")
def report() -> ReportWriter:
    return ReportWriter()


# ── HTTP Client ────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def client() -> httpx.Client:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


# ── Timed Request Helper ───────────────────────────────────────────────────
def timed(client: httpx.Client, method: str, url: str, **kwargs) -> tuple[httpx.Response, float]:
    """Make an HTTP request and return (response, elapsed_ms)."""
    start = time.perf_counter()
    response = getattr(client, method)(url, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    return response, elapsed


# ── Auth Token Fixtures ────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def seed_ia_token(client: httpx.Client) -> str:
    """Returns a valid IA bridge token using the seeded acme owner account.
    Module-scoped so each module gets a fresh token after prior modules may
    have incremented refresh_token_version via force logins."""
    resp = client.post(
        "/ia-auth/login",
        json={"email": SEED_IA_EMAIL, "password": SEED_IA_PASSWORD, "force": True},
        headers={"X-Tenant-Slug": SEED_IA_SUBDOMAIN},
    )
    assert resp.status_code == 200, f"Seed IA bridge login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def seed_tenant_headers() -> dict:
    """Headers needed for all Bridge-dependent routes."""
    return {"X-Tenant-Slug": SEED_IA_SUBDOMAIN}
