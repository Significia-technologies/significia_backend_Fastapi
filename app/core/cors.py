"""
Dynamic tenant-aware CORS middleware.

Tenants can bring either a Significia subdomain (<slug>.significia.com) or a
fully custom domain (see app/models/tenant.py: subdomain, custom_domain). A
static origin allow-list/regex can't express "any of N tenant-registered
domains," so instead of a blanket wildcard we validate the Origin header
against the tenant table, with a short-lived in-process cache to avoid a DB
hit on every request.
"""
import re
import time
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database.session import SessionLocal
from app.models.tenant import Tenant

FIXED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://significia.com",
    "https://www.significia.com",
    "https://app.significia.com",
}

VERCEL_ORIGIN_RE = re.compile(r"^https://[a-zA-Z0-9-]+\.vercel\.app$")

_CACHE_TTL_SECONDS = 60
_tenant_origin_cache: dict[str, tuple[bool, float]] = {}


def _is_known_tenant_origin(hostname: str) -> bool:
    cached = _tenant_origin_cache.get(hostname)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]

    db = SessionLocal()
    try:
        subdomain_slug = hostname.split(".")[0] if hostname.endswith(".significia.com") else None
        query = db.query(Tenant.id)
        if subdomain_slug:
            match = query.filter(
                (Tenant.subdomain == subdomain_slug) | (Tenant.custom_domain == hostname)
            ).first()
        else:
            match = query.filter(Tenant.custom_domain == hostname).first()
        is_known = match is not None
    finally:
        db.close()

    _tenant_origin_cache[hostname] = (is_known, time.monotonic() + _CACHE_TTL_SECONDS)
    return is_known


def _origin_allowed(origin: str) -> bool:
    if origin in FIXED_ORIGINS or VERCEL_ORIGIN_RE.match(origin):
        return True
    hostname = urlparse(origin).hostname
    if not hostname:
        return False
    return _is_known_tenant_origin(hostname)


class TenantCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        if origin and request.method == "OPTIONS" and "access-control-request-method" in request.headers:
            if not _origin_allowed(origin):
                return Response(status_code=400, content="CORS origin not allowed")
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "*"),
                "Vary": "Origin",
            }
            return Response(status_code=200, headers=headers)

        response: Response = await call_next(request)

        if origin and _origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"

        return response
