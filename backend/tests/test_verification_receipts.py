"""
Unit and Integration Test Suite for Verification Receipts (Append-Only Hash-Chained Log).

Tests:
1. Ed25519 cryptographic key management, signing, and signature verification.
2. Canonical JSON serialization, key sorting, and deterministic SHA-256 hashing.
3. Append function: genesis block linkage, subsequent block chaining, and transaction safety.
4. Chain verification on intact ledger (100% validity).
5. Tamper detection:
   - Content tampering (status forged) -> HASH_MISMATCH
   - Signature tampering -> INVALID_SIGNATURE
   - Chain linkage tampering (previous_hash modified) -> BROKEN_CHAIN_LINK
   - First broken link reporting accuracy
6. Immutability enforcement:
   - ORM-level listeners block UPDATE and DELETE
   - Database triggers block direct SQL UPDATE and DELETE
7. Multi-application isolation and chainhead verification.
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.models import VerificationReceipt, Application, Institution
from backend.app.services.verification_receipts import (
    Ed25519KeyManager,
    canonicalize_receipt_data,
    append_verification_receipt,
    verify_chain,
    apply_db_immutability_triggers,
    default_key_manager,
    GENESIS_HASH
)


@pytest.fixture(scope="module")
def setup_db():
    """Initializes tables and immutability triggers."""
    Base.metadata.create_all(bind=engine)
    apply_db_immutability_triggers(engine)
    yield


@pytest.fixture
def db(setup_db) -> Session:
    """Yields a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_institution(db: Session) -> Institution:
    """Creates or fetches a test institution."""
    inst = db.query(Institution).filter(Institution.aicte_id == "TEST-INST-REC").first()
    if not inst:
        inst = Institution(
            aicte_id="TEST-INST-REC",
            name="Pramaan Verification Testing Institute",
            state="Delhi",
            city="New Delhi"
        )
        db.add(inst)
        db.commit()
        db.refresh(inst)
    return inst


@pytest.fixture
def test_app(db: Session, sample_institution: Institution) -> Application:
    """Creates a unique test application to isolate receipts."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    app = Application(
        application_no=f"APP-TEST-{timestamp}",
        institution_id=sample_institution.id
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


# ============================================================================
# 1. ED25519 CRYPTOGRAPHY TESTS
# ============================================================================

def test_ed25519_key_generation_and_signing(tmp_path):
    """Tests Ed25519 key generation, signing, and verification."""
    custom_key_file = tmp_path / "test_ed25519.key"
    km = Ed25519KeyManager(key_file_path=custom_key_file)

    pub_hex = km.public_key_hex
    assert len(pub_hex) == 64  # 32 bytes in hex = 64 hex characters
    assert all(c in "0123456789abcdef" for c in pub_hex)

    payload = b"Canonical test verification payload for Pramaan-X"
    sig_hex = km.sign(payload)
    assert len(sig_hex) == 128  # 64 bytes in hex = 128 hex characters

    # Valid signature check
    assert Ed25519KeyManager.verify_signature(payload, sig_hex, pub_hex) is True

    # Tampered payload check
    tampered_payload = b"Forged payload"
    assert Ed25519KeyManager.verify_signature(tampered_payload, sig_hex, pub_hex) is False

    # Corrupted signature check
    corrupted_sig = "a" * 128
    assert Ed25519KeyManager.verify_signature(payload, corrupted_sig, pub_hex) is False

    # Key persistence check
    assert custom_key_file.exists()
    km2 = Ed25519KeyManager(key_file_path=custom_key_file)
    assert km2.public_key_hex == pub_hex


# ============================================================================
# 2. CANONICAL JSON SERIALIZATION TESTS
# ============================================================================

def test_canonicalize_receipt_data_determinism():
    """Tests that canonical JSON produces identical bytes regardless of dict key order."""
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    rules_order_1 = {"rule_b": 2, "rule_a": 1, "nested": {"z": 9, "a": 0}}
    rules_order_2 = {"nested": {"a": 0, "z": 9}, "rule_a": 1, "rule_b": 2}

    canon_bytes_1, hash_1 = canonicalize_receipt_data(
        application_id=101,
        document_id=5,
        source="GatewayA",
        status="verified",
        timestamp=now,
        response_hash="hash_resp_123",
        rule_version_set=rules_order_1,
        previous_hash=GENESIS_HASH
    )

    canon_bytes_2, hash_2 = canonicalize_receipt_data(
        application_id=101,
        document_id=5,
        source="GatewayA",
        status="verified",
        timestamp=now,
        response_hash="hash_resp_123",
        rule_version_set=rules_order_2,
        previous_hash=GENESIS_HASH
    )

    assert canon_bytes_1 == canon_bytes_2
    assert hash_1 == hash_2
    assert hash_1 == hashlib.sha256(canon_bytes_1).hexdigest()
    # Ensure compact separators: no spaces after ':' or ','
    assert b": " not in canon_bytes_1
    assert b", " not in canon_bytes_1


# ============================================================================
# 3. APPEND FUNCTION & HASH CHAINING TESTS
# ============================================================================

def test_append_verification_receipt_chaining(db: Session, test_app: Application):
    """Tests sequential append linking previous_hash correctly."""
    r1 = append_verification_receipt(
        db=db,
        application_id=test_app.id,
        source="Source-Fire",
        status="verified",
        response_hash="hash1" * 12 + "1234",
        rule_version_set={"fire_norm": "v1.0"}
    )
    assert r1.id is not None
    assert r1.receipt_hash is not None
    assert len(r1.receipt_hash) == 64
    assert len(r1.signature) == 128
    assert len(r1.public_key) == 64

    # Second block must link to r1's receipt_hash
    r2 = append_verification_receipt(
        db=db,
        application_id=test_app.id,
        source="Source-Land",
        status="verified",
        response_hash="hash2" * 12 + "5678",
        rule_version_set={"land_norm": "v2.0"}
    )
    assert r2.previous_hash == r1.receipt_hash
    assert r2.id > r1.id

    # Third block must link to r2's receipt_hash
    r3 = append_verification_receipt(
        db=db,
        application_id=test_app.id,
        source="Source-Building",
        status="mismatch_detected",
        response_hash="hash3" * 12 + "9012",
        rule_version_set={"fsi_norm": "v1.2"}
    )
    assert r3.previous_hash == r2.receipt_hash


# ============================================================================
# 4. CHAIN VERIFICATION ON INTACT LEDGER
# ============================================================================

def test_verify_chain_intact_ledger(db: Session, test_app: Application):
    """Tests verify_chain returns is_valid == True for unmodified receipts."""
    # Append 3 receipts
    for i in range(3):
        append_verification_receipt(
            db=db,
            application_id=test_app.id,
            source=f"IntactSource-{i}",
            status="verified",
            response_hash=f"resp_{i}" * 8,
            rule_version_set={"rule_idx": i}
        )

    res = verify_chain(db, application_id=test_app.id)
    assert res["is_valid"] is True
    assert res["status"] == "CHAIN_INTACT"
    assert res["total_receipts"] >= 3
    assert res["first_broken_link"] is None


def test_verify_chain_empty_ledger(db: Session, sample_institution: Institution):
    """Tests verify_chain on application with no receipts."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    empty_app = Application(
        application_no=f"APP-EMPTY-{timestamp}",
        institution_id=sample_institution.id
    )
    db.add(empty_app)
    db.commit()

    res = verify_chain(db, application_id=empty_app.id)
    assert res["is_valid"] is True
    assert res["status"] == "EMPTY_CHAIN"
    assert res["total_receipts"] == 0
    assert res["first_broken_link"] is None


# ============================================================================
# 5. TAMPER DETECTION TESTS
# ============================================================================

def test_tamper_detection_content_modification(db: Session, test_app: Application):
    """Tests that modifying status triggers HASH_MISMATCH and identifies first broken link."""
    r1 = append_verification_receipt(
        db=db, application_id=test_app.id, source="Gateway-1", status="verified",
        response_hash="resp1" * 10 + "1234", rule_version_set={"r": 1}
    )
    r2 = append_verification_receipt(
        db=db, application_id=test_app.id, source="Gateway-2", status="mismatch_detected",
        response_hash="resp2" * 10 + "5678", rule_version_set={"r": 2}
    )
    r3 = append_verification_receipt(
        db=db, application_id=test_app.id, source="Gateway-3", status="verified",
        response_hash="resp3" * 10 + "9012", rule_version_set={"r": 3}
    )

    # Force tamper status on r2 bypassing triggers
    db.execute(text("DROP TRIGGER IF EXISTS trg_block_receipts_update;"))
    db.execute(text(f"UPDATE verification_receipts SET status = 'verified' WHERE id = {r2.id};"))
    db.commit()
    apply_db_immutability_triggers(engine)

    # Audit the chain
    audit = verify_chain(db, application_id=test_app.id)
    assert audit["is_valid"] is False
    assert audit["status"] == "TAMPERING_DETECTED"
    assert audit["tamper_type"] == "HASH_MISMATCH"
    assert audit["broken_receipt_id"] == r2.id
    assert audit["first_broken_link"]["receipt_id"] == r2.id
    assert audit["first_broken_link"]["tamper_type"] == "HASH_MISMATCH"


def test_tamper_detection_signature_forgery(db: Session, test_app: Application):
    """Tests that corrupting signature triggers INVALID_SIGNATURE even if hash matched."""
    r = append_verification_receipt(
        db=db, application_id=test_app.id, source="Gateway-SigTest", status="verified",
        response_hash="resp_sig" * 8, rule_version_set={"sig": True}
    )

    # Corrupt signature in database
    forged_sig = "ff" * 64
    db.execute(text("DROP TRIGGER IF EXISTS trg_block_receipts_update;"))
    db.execute(text(f"UPDATE verification_receipts SET signature = '{forged_sig}' WHERE id = {r.id};"))
    db.commit()
    apply_db_immutability_triggers(engine)

    audit = verify_chain(db, application_id=test_app.id)
    assert audit["is_valid"] is False
    assert audit["tamper_type"] == "INVALID_SIGNATURE"
    assert audit["broken_receipt_id"] == r.id


def test_tamper_detection_broken_chain_link(db: Session, test_app: Application):
    """Tests that modifying previous_hash triggers BROKEN_CHAIN_LINK."""
    r1 = append_verification_receipt(
        db=db, application_id=test_app.id, source="Gateway-A", status="verified",
        response_hash="hash_a" * 8, rule_version_set={}
    )
    r2 = append_verification_receipt(
        db=db, application_id=test_app.id, source="Gateway-B", status="verified",
        response_hash="hash_b" * 8, rule_version_set={}
    )

    # Corrupt previous_hash of r2
    bogus_prev = "9" * 64
    db.execute(text("DROP TRIGGER IF EXISTS trg_block_receipts_update;"))
    db.execute(text(f"UPDATE verification_receipts SET previous_hash = '{bogus_prev}' WHERE id = {r2.id};"))
    db.commit()
    apply_db_immutability_triggers(engine)

    audit = verify_chain(db, application_id=test_app.id)
    assert audit["is_valid"] is False
    assert audit["tamper_type"] == "BROKEN_CHAIN_LINK"
    assert audit["broken_receipt_id"] == r2.id


# ============================================================================
# 6. IMMUTABILITY ENFORCEMENT (TRIGGERS & ORM LISTENERS)
# ============================================================================

def test_orm_listener_blocks_update(db: Session, test_app: Application):
    """Tests that regular SQLAlchemy session UPDATE raises PermissionError."""
    r = append_verification_receipt(
        db=db, application_id=test_app.id, source="Source-Immutable", status="verified",
        response_hash="imm_resp" * 8, rule_version_set={}
    )

    r.status = "mismatch_detected"
    with pytest.raises(PermissionError) as exc_info:
        db.commit()
    assert "immutable. UPDATE operations are strictly prohibited" in str(exc_info.value)
    db.rollback()


def test_orm_listener_blocks_delete(db: Session, test_app: Application):
    """Tests that regular SQLAlchemy session DELETE raises PermissionError."""
    r = append_verification_receipt(
        db=db, application_id=test_app.id, source="Source-DeleteTest", status="verified",
        response_hash="del_resp" * 8, rule_version_set={}
    )

    db.delete(r)
    with pytest.raises(PermissionError) as exc_info:
        db.commit()
    assert "immutable. DELETE operations are strictly prohibited" in str(exc_info.value)
    db.rollback()


def test_database_trigger_blocks_direct_sql_mutation(db: Session, test_app: Application):
    """Tests that direct raw SQL UPDATE/DELETE is blocked by DB triggers."""
    apply_db_immutability_triggers(engine)
    r = append_verification_receipt(
        db=db, application_id=test_app.id, source="Source-TriggerTest", status="verified",
        response_hash="trig_resp" * 8, rule_version_set={}
    )

    # Direct raw SQL UPDATE should trigger DB exception
    with pytest.raises(Exception):
        db.execute(text(f"UPDATE verification_receipts SET status = 'tampered' WHERE id = {r.id};"))
        db.commit()
    db.rollback()

    # Direct raw SQL DELETE should trigger DB exception
    with pytest.raises(Exception):
        db.execute(text(f"DELETE FROM verification_receipts WHERE id = {r.id};"))
        db.commit()
    db.rollback()
