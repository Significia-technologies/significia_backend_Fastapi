from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os

from app.core.config import settings
from app.api.router import api_router
from app.core.domain_guard import DomainGuardMiddleware


def _run_schema_patches():
    from sqlalchemy import text
    from app.database.session import engine
    # Use pg_attribute to find the table regardless of schema, then ALTER using its schema
    patch = """
    DO $$ DECLARE
        v_schema TEXT;
    BEGIN
        SELECT n.nspname INTO v_schema
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'ia_master' AND c.relkind = 'r'
        LIMIT 1;

        IF v_schema IS NOT NULL THEN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = v_schema
                  AND table_name   = 'ia_master'
                  AND column_name  = 'website'
            ) THEN
                EXECUTE format('ALTER TABLE %I.ia_master ADD COLUMN website VARCHAR(255)', v_schema);
            END IF;
        END IF;
    END $$;
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(patch))
            conn.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Schema patch failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_schema_patches()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Trust proxy headers (X-Forwarded-Proto, etc.) to correctly handle HTTPS redirects
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Create uploads directory if it doesn't exist
os.makedirs("uploads/ia_documents", exist_ok=True)

# Define allowed origins for CORS (no wildcard when credentials=True)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://significia.com",
    "https://www.significia.com",
    "https://app.significia.com",
]

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Allow any IA custom domain + Vercel preview deployments
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:3000|https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Domain-based access guard (restricts Super Admin routes to Significia domains)
app.add_middleware(DomainGuardMiddleware)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check route for load balancers
@app.get("/health")
def health_check():
    return {"status": "ok"}
