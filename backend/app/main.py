import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.data.seed_data import seed_database

# API Routers
from backend.app.api.auth import router as auth_router
from backend.app.api.applications import router as applications_router
from backend.app.api.documents import router as documents_router
from backend.app.api.rules import router as rules_router
from backend.app.api.graph import router as graph_router
from backend.app.api.forensics import router as forensics_router
from backend.app.api.verification import router as verification_router
from backend.app.api.audit import router as audit_router
from backend.app.api.preflight import router as preflight_router
from backend.app.api.radar import router as radar_router
from backend.app.api.alerts import router as alerts_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

TAGS_METADATA = [
    {
        "name": "Authentication & RBAC",
        "description": "JWT-based authentication and role-based access control with roles: institution_user, scrutiny_officer, senior_officer, admin, auditor."
    },
    {
        "name": "Applications & Scrutiny",
        "description": "Statutory application dossiers, validation reports, advisory findings, and officer determinations with mandatory comments. Enforces no automatic rejection."
    },
    {
        "name": "Documents & OCR Intelligence",
        "description": "Document ingestion, OCR text extraction, cryptographic deduplication, and forensic integrity checking with tenant isolation."
    },
    {
        "name": "Regulation-as-Code",
        "description": "Handbook rule catalog, multi-versioning, parameter configuration, and What-If dry run cohort impact simulation."
    },
    {
        "name": "Operational Alerts & Warnings",
        "description": "Real-time institutional risk flags, forensic alerts, and show-cause resolution tracking."
    },
    {
        "name": "National Photo Reuse Radar",
        "description": "Cross-institutional computer vision duplicate detection using perceptual hashing and vector embeddings."
    },
    {
        "name": "Tamper-Evident Audit Ledger",
        "description": "Append-only hash-chained verification receipts with Ed25519 digital signatures and mathematical tamper detection."
    }
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "PRAMAAN-X: AI Decision-Support Platform for AICTE Extension of Approval (EoA) "
        "and Regulatory Document Scrutiny. Built for AICTE India.\n\n"
        "Security & Governance:\n"
        "- Role-Based Access Control (RBAC): institution_user, scrutiny_officer, senior_officer, admin, auditor\n"
        "- Tenant Isolation: Institution users can only view their own institution's data\n"
        "- Immutable Access Logging: Every read of sensitive data is logged with actor, timestamp, and resource\n"
        "- Role-Based PII Masking: Personal identifiers (Aadhaar, PAN, contact) masked for committee review\n"
        "- No Automatic Rejection: Adverse determinations strictly require an authorized Officer Action with a mandatory comment\n"
    ),
    openapi_tags=TAGS_METADATA,
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for document preview
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Routers under /api/v1
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(applications_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(documents_router)  # Also expose /documents/ingest at root as requested by Prompt 5.1
app.include_router(rules_router, prefix=settings.API_V1_STR)
app.include_router(graph_router, prefix=settings.API_V1_STR)
app.include_router(forensics_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(preflight_router, prefix=settings.API_V1_STR)
app.include_router(radar_router, prefix=settings.API_V1_STR)
app.include_router(radar_router)  # Expose /radar/clusters at root as requested
app.include_router(alerts_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    # Seed initial synthetic benchmark data on start
    seed_database()

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "purpose": "AICTE EoA AI Decision-Support & Document Scrutiny Platform",
        "version": settings.PROJECT_VERSION,
        "status": "OPERATIONAL",
        "advisory_disclaimer": "AI indicators are decision-support aids for scrutiny committees, not proofs of forgery.",
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "db": "CONNECTED"}
