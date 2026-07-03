from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

from app.core.config import settings
from app.api.router import api_router
from app.core.domain_guard import DomainGuardMiddleware
from app.core.cors import TenantCORSMiddleware
from app.core.rate_limiter import limiter

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Trust proxy headers (X-Forwarded-Proto, etc.) to correctly handle HTTPS redirects
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Create uploads directory if it doesn't exist
os.makedirs("uploads/ia_documents", exist_ok=True)

# CORS: validated dynamically against registered tenant domains
# (fixed Significia domains + *.vercel.app + any tenant subdomain/custom_domain
# in the DB) — see app/core/cors.py for why a static allow-list can't work here.
app.add_middleware(TenantCORSMiddleware)

# Domain-based access guard (restricts Super Admin routes to Significia domains)
app.add_middleware(DomainGuardMiddleware)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check route for load balancers
@app.get("/health")
def health_check():
    return {"status": "ok"}
