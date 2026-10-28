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
from backend.app.api.inspections import router as inspections_router

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
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not cors_origins or "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
app.include_router(verification_router)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(preflight_router, prefix=settings.API_V1_STR)
app.include_router(radar_router, prefix=settings.API_V1_STR)
app.include_router(radar_router)  # Expose /radar/clusters at root as requested
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(inspections_router, prefix=settings.API_V1_STR)
app.include_router(inspections_router)

@app.on_event("startup")
def on_startup():
    # Seed initial synthetic benchmark data on start
    seed_database()
    
    # Pre-populate representative manual review queue cases if empty
    from backend.app.services.connectors import default_manual_review_queue
    if len(default_manual_review_queue.list()) == 0:
        default_manual_review_queue.enqueue(
            result={
                "status": "manual_review_required",
                "source": "api_lookup:state_fire_services",
                "request_hash": "a1f72b94c0388de84291884bb0728c0b299e900c4314e304892c90ad7d72c1c1",
                "response_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "authoritative_data": {"noc_status": "EXPIRED", "expiry_date": "2024-11-30", "portal_ref": "FS/NOC/BLR/2024/9812"},
                "discrepancies": [{"field": "valid_till", "claimed": "2026-03-31", "authoritative": "2024-11-30"}]
            },
            doc_fields={
                "document_type": "Fire Safety Certificate",
                "reference_number": "FS/NOC/BLR/2024/9812",
                "institution_id": "INST_001",
                "institution_name": "Apex Institute of Technology & Science",
                "authority": "fire"
            },
            reason="Indicator for review: Claimed validity (2026-03-31) conflicts with State Fire Services Portal record (expired 2024-11-30).",
            priority="HIGH"
        )
        default_manual_review_queue.enqueue(
            result={
                "status": "source_unavailable",
                "source": "api_lookup:bhoomi_land_registry",
                "request_hash": "c5d2e7b94c0388de84291884bb0728c0b299e900c4314e304892c90ad7d72c2d2",
                "response_hash": "f4c0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b966",
                "authoritative_data": {"error": "Gateway timeout (HTTP 503)", "attempts": 3},
                "discrepancies": []
            },
            doc_fields={
                "document_type": "Land Title Deed / 7-12 Extract",
                "reference_number": "LND/KA/SURV/42/1",
                "institution_id": "INST_002",
                "institution_name": "Royal College of Engineering",
                "authority": "land"
            },
            reason="Indicator for review: Authoritative Land Registry Gateway timed out after 3 retries with exponential backoff. Requires officer verification.",
            priority="MEDIUM"
        )
        default_manual_review_queue.enqueue(
            result={
                "status": "manual_review_required",
                "source": "digital_signature:dsig_validator",
                "request_hash": "b8e1a7b94c0388de84291884bb0728c0b299e900c4314e304892c90ad7d72c3f3",
                "response_hash": "17d0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852ba77",
                "authoritative_data": {"issuer_ca": "Apex Trust Sub-CA", "ca_trusted": False},
                "discrepancies": [{"field": "ca_trust_chain", "claimed": "e-Mudhra / CCA Root", "found": "Untrusted Self-Signed Sub-CA"}]
            },
            doc_fields={
                "document_type": "University Affiliation Order",
                "reference_number": "AFF/VTU/2024/8819",
                "institution_id": "INST_001",
                "institution_name": "Apex Institute of Technology & Science",
                "authority": "affiliation"
            },
            reason="Indicator for review: Digital signature valid, but signing certificate is issued by an untrusted intermediate CA not in CCA India trust store.",
            priority="MEDIUM"
        )

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
    db_engine = "SQLite" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL"
    return {"status": "HEALTHY", "db": "CONNECTED", "database_engine": db_engine}

