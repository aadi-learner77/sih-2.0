from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, EmailStr

# Auth & User
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    institution_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True

# Institution
class InstitutionOut(BaseModel):
    id: int
    aicte_id: str
    name: str
    state: str
    city: str
    category: str
    approved_intake: int
    total_built_up_area_sqm: float
    land_area_acres: float
    status: str

    class Config:
        from_attributes = True

# Document
class DocumentOut(BaseModel):
    id: int
    application_id: int
    document_type: str
    filename: str
    file_hash: str
    file_size_bytes: int
    mime_type: str
    classification_confidence: float
    ocr_extracted_text: Optional[str] = None
    structured_fields: Dict[str, Any] = {}
    metadata_forensics: Dict[str, Any] = {}
    ela_score: float = 0.0
    phash: Optional[str] = None
    is_flagged_for_review: bool = False
    review_indicator_tag: Optional[str] = None
    review_reason: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

# External Verification Check
class VerificationCheckOut(BaseModel):
    id: int
    application_id: int
    document_id: Optional[int] = None
    issuer_type: str
    issuer_name: str
    status: str # verified, mismatch_detected, expired, verification_pending, source_unavailable, manual_review_required
    query_parameters: Dict[str, Any] = {}
    issuer_response_data: Dict[str, Any] = {}
    discrepancy_details: List[Dict[str, Any]] = []
    latency_ms: int
    verified_at: datetime

    class Config:
        from_attributes = True

# Rule Evaluation (Regulation-as-Code)
class RuleEvaluationOut(BaseModel):
    id: int
    application_id: int
    rule_id: Optional[Union[str, int]] = None
    clause_id: str
    clause_title: Optional[str] = None
    handbook_edition: Optional[str] = "AICTE APH 2025-26"
    severity: str
    passed: bool
    claim_summary: Optional[str] = None
    evidence_details: Dict[str, Any] = {}
    explanation: str
    officer_decision: Optional[str] = "PENDING_REVIEW"
    officer_comment: Optional[str] = None
    evaluated_at: datetime

    class Config:
        from_attributes = True

class OfficerDecisionUpdate(BaseModel):
    decision: str # ACCEPTED_WITH_NOTE, CLARIFICATION_REQUESTED, WAIVED_WITH_REASON, PENDING_REVIEW
    comment: Optional[str] = None

# Audit Receipt
class AuditReceiptOut(BaseModel):
    id: int
    receipt_index: int
    timestamp: datetime
    event_type: str
    actor_email: str
    actor_role: str
    application_id: Optional[int] = None
    payload_hash: str
    previous_hash: str
    receipt_hash: str
    signature_digest: Optional[str] = None

    class Config:
        from_attributes = True

# Application Overview & Detail
class ApplicationOut(BaseModel):
    id: int
    application_no: str
    institution_id: int
    institution_name: Optional[str] = None
    academic_year: str
    category: str
    status: str
    preflight_readiness_score: float
    checklist_completion_pct: float
    advisory_flags_count: int
    impossibility_flags_count: int
    forensic_flags_count: int
    issuer_discrepancy_count: int
    submission_date: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationDetailOut(ApplicationOut):
    institution: InstitutionOut
    documents: List[DocumentOut] = []
    verifications: List[VerificationCheckOut] = []
    rule_evaluations: List[RuleEvaluationOut] = []
    ai_advisory_summary: Optional[str] = None

# Pre-flight readiness check
class PreflightScanRequest(BaseModel):
    institution_id: int
    application_category: str
    facts: Dict[str, Any] = {}

class PreflightScanResponse(BaseModel):
    readiness_score: float
    category: str
    checklist_summary: Dict[str, Any]
    rule_indicators: List[Dict[str, Any]]
    impossibility_indicators: List[Dict[str, Any]]
    recommendations: List[str]
    uploaded_documents: Optional[List[Dict[str, Any]]] = None

# Application Submission
class ApplicationSubmitRequest(BaseModel):
    institution_id: int
    category: Optional[str] = "Extension of Approval (EoA)"
    academic_year: Optional[str] = "2025-26"
    facts: Optional[Dict[str, Any]] = None

# Officer Action (Human in the loop - mandatory comment)
class OfficerActionRequest(BaseModel):
    action: str  # accept, dismiss, escalate, request_more_evidence, recommend_inspection, reject
    comment: str  # Mandatory comment!
    finding_id: Optional[int] = None
    target_status: Optional[str] = None

# Operational Alerts
class AlertOut(BaseModel):
    id: int
    application_id: int
    alert_type: str
    severity: str
    title: str
    message: str
    entity_refs: Dict[str, Any] = {}
    is_read: bool = False
    resolved_at: Optional[datetime] = None
    assigned_role: Optional[str] = "scrutiny_officer"
    dedupe_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Rules CRUD & Versioning
class RuleCreateRequest(BaseModel):
    rule_code: str
    clause_id: str
    title: str
    category: str
    severity: str = "WARNING"
    description: str
    condition_expression: str
    failure_message_template: str
    parameters: Dict[str, Any] = {}
    handbook_edition: str = "AICTE APH 2025-26"
    version_number: str = "1.0.0"

class RuleUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    condition_expression: Optional[str] = None
    failure_message_template: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    handbook_edition: Optional[str] = None
    version_number: Optional[str] = None
    is_active: Optional[bool] = None

class WhatIfDryRunRequest(BaseModel):
    rules: Optional[List[Dict[str, Any]]] = None
    applications: Optional[List[Dict[str, Any]]] = None
    parameters_override: Optional[Dict[str, Any]] = None

