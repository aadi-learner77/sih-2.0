"""
PRAMAAN-X Database Schema:
PostgreSQL Production Models (Alembic-Ready) with SQLite Local Fallback.
Comprehensive 15-Table Architecture:
1.  roles
2.  users
3.  institutions
4.  application_categories
5.  applications
6.  documents
7.  extracted_fields
8.  rules
9.  rule_versions
10. findings
11. verifications
12. receipts (Hash-Chained)
13. alerts
14. officer_actions
15. audit_log
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, UniqueConstraint, Enum, JSON, event
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.core.database import Base

# Dialect-agnostic JSON type that compiles to JSONB on PostgreSQL and JSON on SQLite
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")

def utc_now():
    return datetime.now(timezone.utc)


# ============================================================================
# 1. ROLES & RBAC
# ============================================================================
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True) # scrutiny_officer, regional_officer, admin, institution_user
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON_TYPE, default=list) # ["view_dossier", "sign_action", "configure_rules"]
    created_at = Column(DateTime(timezone=True), default=utc_now)

    users = relationship("User", back_populates="role_rel")


# ============================================================================
# 2. USERS
# ============================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="scrutiny_officer") # legacy string identifier
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    role_rel = relationship("Role", back_populates="users")
    institution = relationship("Institution", back_populates="users")
    officer_actions = relationship("OfficerAction", back_populates="officer")
    audit_logs = relationship("AuditLog", back_populates="actor")


# ============================================================================
# 3. INSTITUTIONS
# ============================================================================
class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    aicte_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    state = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    category = Column(String(100), default="Engineering & Technology", index=True)
    approved_intake = Column(Integer, default=300)
    total_built_up_area_sqm = Column(Float, default=12000.0)
    land_area_acres = Column(Float, default=5.5)
    survey_numbers = Column(String(255), default="Survey 42/1, Khasra 108")
    address = Column(Text, nullable=True)
    trust_name = Column(String(255), default="Shri Vidya Educational Trust")
    status = Column(String(50), default="ACTIVE", index=True)
    geo_coordinates = Column(JSON_TYPE, nullable=True) # {"lat": 13.243, "lng": 77.712}
    created_at = Column(DateTime(timezone=True), default=utc_now)

    users = relationship("User", back_populates="institution")
    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")
    buildings = relationship("Building", back_populates="institution", cascade="all, delete-orphan")
    labs = relationship("Lab", back_populates="institution", cascade="all, delete-orphan")
    programmes = relationship("Programme", back_populates="institution", cascade="all, delete-orphan")
    employments = relationship("FacultyEmployment", back_populates="institution", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="institution", cascade="all, delete-orphan")
    held_documents = relationship("Document", back_populates="institution_rel", foreign_keys="Document.institution_id")


# ============================================================================
# 4. APPLICATION CATEGORIES (Taxonomy & Dynamic Checklists)
# ============================================================================
class ApplicationCategory(Base):
    __tablename__ = "application_categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False) # EOA, INCREASE_INTAKE, NEW_COURSE, CLOSURE
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_documents = Column(JSON_TYPE, default=list) # Checklist specification
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    applications = relationship("Application", back_populates="category_rel")


# ============================================================================
# 5. APPLICATIONS (Dossier Header)
# ============================================================================
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    application_no = Column(String(100), unique=True, index=True, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("application_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(100), default="Extension of Approval (EoA)", index=True)
    academic_year = Column(String(20), default="2025-26", index=True)
    status = Column(String(50), default="SUBMITTED", index=True) # SUBMITTED, UNDER_SCRUTINY, CLARIFICATION_REQUESTED, APPROVED_WITH_CONDITIONS
    
    # Pre-Flight Readiness & Scoring
    preflight_readiness_score = Column(Float, default=78.5)
    checklist_completion_pct = Column(Float, default=85.0)
    
    # Advisory Review Counters
    advisory_flags_count = Column(Integer, default=0)
    impossibility_flags_count = Column(Integer, default=0)
    forensic_flags_count = Column(Integer, default=0)
    issuer_discrepancy_count = Column(Integer, default=0)
    
    ai_advisory_summary = Column(Text, nullable=True)
    submission_date = Column(DateTime(timezone=True), default=utc_now)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_applications_inst_status", "institution_id", "status"),
        Index("idx_applications_year_cat", "academic_year", "category"),
    )

    institution = relationship("Institution", back_populates="applications")
    category_rel = relationship("ApplicationCategory", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="application", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="application", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="application", cascade="all, delete-orphan")
    verification_receipts = relationship("VerificationReceipt", back_populates="application", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="application", cascade="all, delete-orphan")
    officer_actions = relationship("OfficerAction", back_populates="application", cascade="all, delete-orphan")

    # Backwards-compatible alias for existing endpoints
    @property
    def rule_evaluations(self):
        return self.findings

    @property
    def audit_receipts(self):
        return self.receipts


# ============================================================================
# 6. DOCUMENTS
# ============================================================================
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False, index=True) # Fire Safety NOC, Land Deed, Building Plan, etc.
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True, default="")
    file_hash = Column(String(64), nullable=False, index=True) # SHA-256 for deduplication
    file_size_bytes = Column(Integer, default=0)
    mime_type = Column(String(100), default="application/pdf")
    
    # Classification & OCR
    classification_confidence = Column(Float, default=0.95)
    ocr_extracted_text = Column(Text, nullable=True)
    structured_fields = Column(JSON_TYPE, default=dict)
    
    # Forensics & Integrity
    metadata_forensics = Column(JSON_TYPE, default=dict) # Producer tool, EXIF, creation dates
    ela_score = Column(Float, default=0.0) # Error Level Analysis anomaly score
    phash = Column(String(64), nullable=True, index=True) # Perceptual hash for Photo Reuse Radar
    
    is_flagged_for_review = Column(Boolean, default=False, index=True)
    review_indicator_tag = Column(String(100), nullable=True)
    review_reason = Column(Text, nullable=True)
    
    uploaded_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_documents_app_type", "application_id", "document_type"),
        Index("idx_documents_hash", "file_hash"),
    )

    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    issuer_id = Column(Integer, ForeignKey("issuers.id", ondelete="SET NULL"), nullable=True, index=True)
    reference_number = Column(String(100), nullable=True, index=True)
    issue_date = Column(String(50), nullable=True, index=True)
    valid_till = Column(String(50), nullable=True, index=True)

    application = relationship("Application", back_populates="documents")
    extracted_fields_rel = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="document")
    institution_rel = relationship("Institution", back_populates="held_documents", foreign_keys=[institution_id])
    issuer_rel = relationship("Issuer", back_populates="documents")


# ============================================================================
# 7. EXTRACTED FIELDS (Structured Key-Values from OCR)
# ============================================================================
class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True) # valid_till, noc_number, carpet_area_sqm, survey_numbers
    field_value = Column(Text, nullable=False)
    normalized_value = Column(JSON_TYPE, nullable=True) # Structured/typed representation
    data_type = Column(String(50), default="STRING") # DATE, NUMERIC, STRING, BOOLEAN
    confidence = Column(Float, default=0.95)
    bounding_box = Column(JSON_TYPE, nullable=True) # {"x": 120, "y": 340, "w": 200, "h": 25}
    page_number = Column(Integer, default=1)
    is_verified = Column(Boolean, default=False, index=True)
    extracted_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_extracted_fields_doc_name", "document_id", "field_name"),
    )

    document = relationship("Document", back_populates="extracted_fields_rel")


# ============================================================================
# 8. RULES (Regulation-as-Code Declarative Catalog)
# ============================================================================
class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(100), unique=True, nullable=False, index=True) # RULE_FACULTY_STUDENT_RATIO
    clause_id = Column(String(100), nullable=False, index=True) # APH-2025-Cl-4.1.1
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True) # Faculty & Cadre, Infrastructure, Safety
    severity = Column(String(50), default="WARNING", index=True) # CRITICAL, WARNING, ADVISORY
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    versions = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="rule")


# ============================================================================
# 9. RULE VERSIONS (Handbook Editions & Configurable Parameters)
# ============================================================================
class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True)
    handbook_edition = Column(String(100), default="AICTE APH 2025-26", index=True)
    version_number = Column(String(50), default="1.0.0")
    parameters = Column(JSON_TYPE, default=dict) # {"target_fsr": 20, "tolerance_pct": 5}
    condition_expression = Column(Text, nullable=False)
    failure_message_template = Column(Text, nullable=False)
    effective_from = Column(DateTime(timezone=True), default=utc_now)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("rule_id", "handbook_edition", "version_number", name="uq_rule_edition_version"),
    )

    rule = relationship("Rule", back_populates="versions")
    findings = relationship("Finding", back_populates="rule_version")


# ============================================================================
# 10. FINDINGS (Discrepancies, Indicative Flags & Evidence Lens items)
# ============================================================================
class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Backwards compatibility fields for rules_engine
    rule_code_ref = Column(String(100), nullable=True, index=True)
    clause_id = Column(String(100), nullable=False, index=True)
    clause_title = Column(String(255), nullable=True)
    handbook_edition = Column(String(100), default="AICTE APH 2025-26")
    
    severity = Column(String(50), default="WARNING", index=True) # CRITICAL, WARNING, ADVISORY
    passed = Column(Boolean, default=True, index=True)
    status = Column(String(50), default="PENDING_REVIEW", index=True) # PENDING_REVIEW, ACCEPTED_WITH_NOTE, CLARIFICATION_ISSUED, WAIVED_WITH_REASON
    
    confidence = Column(Float, default=0.95) # 0.0 to 1.0 multi-modal confidence
    claim_summary = Column(Text, nullable=True)
    evidence_details = Column(JSON_TYPE, default=dict) # Evidence mapping dictionary
    evidence_refs = Column(JSON_TYPE, default=list) # Array of linked document IDs or field IDs
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    
    # Officer Review determination (Human in the Loop)
    officer_decision = Column(String(50), default="PENDING_REVIEW")
    officer_comment = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now)

    # Rectification & Superseding Lifecycle
    is_rectification_allowed = Column(Boolean, default=True, index=True)
    is_superseded = Column(Boolean, default=False, index=True)
    replacement_document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    superseded_by_finding_id = Column(Integer, ForeignKey("findings.id", ondelete="SET NULL"), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_findings_app_severity", "application_id", "severity"),
        Index("idx_findings_status", "status"),
        Index("idx_findings_clause", "clause_id"),
        Index("idx_findings_rectification", "is_rectification_allowed", "is_superseded"),
    )

    application = relationship("Application", back_populates="findings")
    rule = relationship("Rule", back_populates="findings")
    rule_version = relationship("RuleVersion", back_populates="findings")
    officer_actions = relationship("OfficerAction", back_populates="finding")
    replacement_document = relationship("Document", foreign_keys=[replacement_document_id])


# Alias for backwards compatibility
RuleEvaluation = Finding


# ============================================================================
# 11. VERIFICATIONS (External Mock Issuer Gateway Audit)
# ============================================================================
class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    issuer_type = Column(String(100), nullable=False, index=True) # fire_department, land_registry, university_affiliation, cbdt_income_tax
    issuer_name = Column(String(255), nullable=False)
    
    # Status: verified, mismatch_detected, expired, verification_pending, source_unavailable, manual_review_required
    status = Column(String(50), nullable=False, default="verification_pending", index=True)
    
    query_parameters = Column(JSON_TYPE, default=dict)
    issuer_response_data = Column(JSON_TYPE, default=dict)
    discrepancy_details = Column(JSON_TYPE, default=list) # List of mismatched fields
    latency_ms = Column(Integer, default=120)
    verified_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_verifications_app_status", "application_id", "status"),
    )

    application = relationship("Application", back_populates="verifications")
    document = relationship("Document", back_populates="verifications")


# Alias for backwards compatibility
VerificationCheck = Verification


# ============================================================================
# 12. RECEIPTS (Hash-Chained, Tamper-Evident Audit Ledger)
# ============================================================================
class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_index = Column(Integer, unique=True, nullable=False, index=True) # Monotonically increasing index 0, 1, 2...
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    event_type = Column(String(100), nullable=False, index=True) # APPLICATION_SUBMITTED, DOCUMENT_UPLOAD, EXTERNAL_VERIFY, OFFICER_DECISION
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(255), default="system@aicte-india.org")
    actor_role = Column(String(50), default="SYSTEM")
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    
    payload_hash = Column(String(64), nullable=False) # SHA-256 of canonical event payload
    previous_hash = Column(String(64), nullable=False, index=True) # Parent block hash
    receipt_hash = Column(String(64), unique=True, nullable=False, index=True) # SHA-256(index + timestamp + event + actor + payload + prev)
    signature_digest = Column(String(128), nullable=True) # HMAC-SHA256 signature
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_receipts_chain", "receipt_index", "receipt_hash"),
    )

    application = relationship("Application", back_populates="receipts")
    officer_action = relationship("OfficerAction", back_populates="receipt", uselist=False)


# Alias for backwards compatibility
AuditReceipt = Receipt


# ============================================================================
# 12B. VERIFICATION RECEIPTS (Append-Only Hash-Chained Log with Ed25519)
# ============================================================================
class VerificationReceipt(Base):
    """
    Append-only, hash-chained log for verification events in PostgreSQL.
    Contains: id, application_id, document_id, source, status, timestamp,
    response_hash, rule_version_set, previous_hash, and its own hash (SHA-256 over canonical JSON).
    Cryptographically signed with Ed25519 key.
    """
    __tablename__ = "verification_receipts"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    source = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    response_hash = Column(String(64), nullable=False, index=True)
    rule_version_set = Column(JSON_TYPE, default=dict, nullable=False)
    previous_hash = Column(String(64), nullable=False, index=True)
    receipt_hash = Column(String(64), unique=True, nullable=False, index=True)
    signature = Column(Text, nullable=False)
    public_key = Column(String(128), nullable=False)

    __table_args__ = (
        Index("idx_verif_receipts_chain", "id", "previous_hash", "receipt_hash"),
        Index("idx_verif_receipts_app", "application_id", "timestamp"),
    )

    application = relationship("Application", back_populates="verification_receipts")
    document = relationship("Document")


# ============================================================================
# 13. ALERTS (High-Priority Operational Warnings)

# ============================================================================
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False, index=True) # IMPOSSIBILITY_CONFLICT, FORENSIC_TAMPER, CERTIFICATE_EXPIRING, ISSUER_MISMATCH
    severity = Column(String(50), default="WARNING", index=True) # CRITICAL, WARNING, INFO
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    entity_refs = Column(JSON_TYPE, default=dict) # {"faculty_pan": "AB****89C", "survey_no": "42/1"}
    is_read = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_role = Column(String(100), default="scrutiny_officer", index=True)
    dedupe_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_alerts_app_severity", "application_id", "severity"),
        Index("idx_alerts_dedupe", "dedupe_key"),
        Index("idx_alerts_role", "assigned_role"),
    )

    application = relationship("Application", back_populates="alerts")


# ============================================================================
# 14. OFFICER ACTIONS (Human-in-the-Loop Signed Determinations)
# ============================================================================
class OfficerAction(Base):
    __tablename__ = "officer_actions"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="SET NULL"), nullable=True, index=True)
    officer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True) # CLARIFICATION_ISSUED, ACCEPTED_WITH_NOTE, WAIVED_WITH_REASON, PENDING_REVIEW
    justification_note = Column(Text, nullable=False)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="SET NULL"), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_officer_actions_app_type", "application_id", "action_type"),
    )

    application = relationship("Application", back_populates="officer_actions")
    finding = relationship("Finding", back_populates="officer_actions")
    officer = relationship("User", back_populates="officer_actions")
    receipt = relationship("Receipt", back_populates="officer_action")


# ============================================================================
# 15. AUDIT LOG (Immutable Activity Tracking)
# ============================================================================
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=False, index=True)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False, index=True) # USER_LOGIN, DOCUMENT_VIEW, FINDING_REVIEW, RULE_UPDATE
    resource = Column(String(255), nullable=False)
    ip_address = Column(String(50), default="127.0.0.1")
    status_code = Column(Integer, default=200)
    details = Column(JSON_TYPE, default=dict)

    __table_args__ = (
        Index("idx_audit_log_actor_time", "actor_id", "timestamp"),
        Index("idx_audit_log_action", "action"),
    )

    actor = relationship("User", back_populates="audit_logs")


# Alias for backwards compatibility
AccessLog = AuditLog


# ============================================================================
# 16. INSTITUTION TWIN KNOWLEDGE GRAPH MODELS
# ============================================================================
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    survey_numbers = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    institution = relationship("Institution", back_populates="locations")
    buildings = relationship("Building", back_populates="location")


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    building_code = Column(String(100), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    building_type = Column(String(100), default="Instructional") # Instructional, Administrative, Amenities
    built_up_area_sqm = Column(Float, default=0.0)
    floors = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    institution = relationship("Institution", back_populates="buildings")
    location = relationship("Location", back_populates="buildings")
    labs = relationship("Lab", back_populates="building")


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True, index=True)
    lab_code = Column(String(100), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    equipment = Column(JSON_TYPE, default=list) # List of equipment names
    capacity = Column(Integer, default=30)
    area_sqm = Column(Float, default=75.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    institution = relationship("Institution", back_populates="labs")
    building = relationship("Building", back_populates="labs")


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_code = Column(String(100), index=True, nullable=True)
    name = Column(String(255), nullable=False) # e.g. Mechanical Engineering, Civil Engineering
    degree_level = Column(String(50), default="UG") # UG, PG, Diploma
    approved_intake = Column(Integer, default=60)
    academic_year = Column(String(20), default="2025-26")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    institution = relationship("Institution", back_populates="programmes")


class Issuer(Base):
    __tablename__ = "issuers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    issuer_type = Column(String(100), nullable=False) # fire_department, land_registry, university_affiliation, accreditation_board
    creation_date = Column(String(50), nullable=False) # ISO YYYY-MM-DD
    state = Column(String(100), nullable=True)
    authority_level = Column(String(50), default="STATE")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    documents = relationship("Document", back_populates="issuer_rel")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    faculty_code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    pan_masked = Column(String(50), nullable=True, index=True)
    aadhaar_masked = Column(String(50), nullable=True, index=True)
    dob = Column(String(50), nullable=True, index=True) # ISO YYYY-MM-DD
    designation = Column(String(100), nullable=True)
    highest_degree = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    employments = relationship("FacultyEmployment", back_populates="faculty", cascade="all, delete-orphan")


class FacultyEmployment(Base):
    __tablename__ = "faculty_employments"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(100), nullable=False) # Professor, Associate Professor, Assistant Professor
    employment_type = Column(String(50), default="Full-Time") # Full-Time, Part-Time, Adjunct
    start_date = Column(String(50), nullable=False) # ISO YYYY-MM-DD
    end_date = Column(String(50), nullable=True) # ISO YYYY-MM-DD, None if currently employed
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    faculty = relationship("Faculty", back_populates="employments")
    institution = relationship("Institution", back_populates="employments")


# ============================================================================
# STATUTORY GOVERNANCE ENFORCEMENT: ADVERSE STATUS CONSTRAINTS
# ============================================================================

@event.listens_for(Session, "before_flush")
def validate_adverse_status_requires_officer_action(session, flush_context, instances):
    """
    Statutory Governance Constraint:
    Adverse statuses ('REJECTED') are strictly impossible without an authoritative,
    human-in-the-loop OfficerAction determination.
    Automated scanners, preflight checks, and background batch jobs can NEVER mutate
    an application to 'REJECTED'.
    """
    for obj in session.dirty.union(session.new):
        if isinstance(obj, Application) and getattr(obj, "status", None) == "REJECTED":
            # Check if an OfficerAction with REJECT or REJECTED is being recorded in the current session
            actions_in_session = [
                a for a in session.new.union(session.dirty)
                if isinstance(a, OfficerAction) and getattr(a, "application_id", None) == obj.id
                and getattr(a, "action_type", "").upper() in ["REJECT", "REJECTED"]
            ]
            if actions_in_session:
                continue

            # Or check if a committed OfficerAction already exists for this application
            if obj.id:
                has_committed_action = session.query(OfficerAction).filter(
                    OfficerAction.application_id == obj.id,
                    OfficerAction.action_type.in_(["REJECT", "REJECTED"])
                ).first()
                if has_committed_action:
                    continue

            raise ValueError(
                "Adverse status 'REJECTED' is impossible without an authoritative officer action. "
                "AI scanners and automated pipelines may only produce advisory indicators, never automated adverse verdicts."
            )

