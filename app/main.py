from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.router import api_router
from app.core.domain_guard import DomainGuardMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

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
