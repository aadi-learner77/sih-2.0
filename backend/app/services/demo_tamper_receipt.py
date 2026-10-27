"""
PRAMAAN-X Verification Receipts: Tamper-Evident Ledger Demonstration Script.

Demonstrates:
1. Appending 5 realistic verification receipts into the Postgres/SQLite ledger.
2. Generating canonical JSON and Ed25519 cryptographic signatures for each block.
3. Running verify_chain() on an intact ledger (100% Valid).
4. Demonstrating DB immutability controls blocking unauthorized UPDATE/DELETE.
5. Simulating a direct malicious modification on Row #3 (e.g. forging 'mismatch_detected' -> 'verified').
6. Running verify_chain() to pinpoint the exact broken link, tampered row ID, and invalid signature.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from sqlalchemy import text

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.models import VerificationReceipt, Application, Institution
from backend.app.services.verification_receipts import (
    append_verification_receipt,
    verify_chain,
    canonicalize_receipt_data,
    apply_db_immutability_triggers,
    default_key_manager,
    GENESIS_HASH
)


def run_receipt_tamper_demo() -> bool:
    print("\n" + "=" * 105)
    print("  PRAMAAN-X VERIFICATION RECEIPTS: APPEND-ONLY HASH-CHAINED LEDGER DEMO  ".center(105, "="))
    print("=" * 105)

    # 1. Initialize schema & DB triggers
    Base.metadata.create_all(bind=engine)
    apply_db_immutability_triggers(engine)
    db = SessionLocal()

    try:
        # Ensure institution exists
        inst = db.query(Institution).first()
        if not inst:
            inst = Institution(
                aicte_id="1-DEMO-001",
                name="Indian Institute of Technology & Science (Autonomous)",
                state="Maharashtra",
                city="Pune"
            )
            db.add(inst)
            db.commit()

        # Create fresh unique application to append append-only receipts
        timestamp_suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        app = Application(
            application_no=f"APP-DEMO-{timestamp_suffix}",
            institution_id=inst.id
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        print(f"\n[STEP 1] Generating fresh Ed25519 Keypair & Appending 5 Verification Receipts...")
        print(f"Active Application:      {app.application_no} (ID: {app.id})")
        print(f"System Ed25519 Public Key: {default_key_manager.public_key_hex}\n")

        demo_events = [
            {
                "source": "State Fire & Emergency Services Portal",
                "status": "verified",
                "response_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "rules": {"fire_safety_norms": "AICTE-2025.1", "water_capacity_litres": 25000}
            },
            {
                "source": "State Revenue & Land Records Portal (Bhoomi)",
                "status": "verified",
                "response_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
                "rules": {"minimum_land_acres": 5.0, "ownership_category": "FREEHOLD"}
            },
            {
                "source": "Town Planning Master Building Plan Registry",
                "status": "mismatch_detected",
                "response_hash": "c8a1e2f3d4b5a6c7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1",
                "rules": {"sanctioned_built_up_sqm": 12000.0, "detected_footprint_sqm": 8500.0}
            },
            {
                "source": "State Examining University Affiliation Gateway",
                "status": "verified",
                "response_hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                "rules": {"programmes_approved": ["Computer Science", "Mechanical Engineering"]}
            },
            {
                "source": "CBDT Income Tax 26AS / TDS Gateway",
                "status": "verified",
                "response_hash": "9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca7",
                "rules": {"cadre_ratio_professor": 1, "salary_mode": "DIRECT_BANK_TRANSFER"}
            }
        ]

        created_receipts: list[VerificationReceipt] = []
        for idx, evt in enumerate(demo_events, 1):
            r = append_verification_receipt(
                db=db,
                application_id=app.id,
                source=evt["source"],
                status=evt["status"],
                response_hash=evt["response_hash"],
                rule_version_set=evt["rules"]
            )
            created_receipts.append(r)
            print(f"  [+] Block #{idx} (id={r.id:<2}) | Prev: {r.previous_hash[:16]}... | Hash: {r.receipt_hash[:16]}... | Source: {r.source[:36]:<36} | Status: {r.status}")

        print("\n" + "-" * 105)
        print("[STEP 2] Running verify_chain() on Intact Ledger...")
        initial_check = verify_chain(db, application_id=app.id)

        print(f"  Result Status:        {initial_check['status']}")
        print(f"  Is Valid Chain:       {initial_check['is_valid']}")
        print(f"  Total Chain Blocks:   {initial_check['total_receipts']}")
        print(f"  Genesis Hash:         {str(initial_check.get('genesis_hash', 'N/A'))[:24]}...")
        print(f"  Chain Head Hash:      {str(initial_check.get('chain_head_hash', 'N/A'))[:24]}...")
        print(f"  First Broken Link:    {initial_check.get('first_broken_link')}")
        assert initial_check["is_valid"] is True, f"Initial verification failed: {initial_check}"
        print("  -> Cryptographic verification passed: All hashes and Ed25519 signatures are authentic!")

        # --------------------------------------------------------------------
        # STEP 3: Attempt regular ORM Update to demonstrate immutability block
        # --------------------------------------------------------------------
        print("\n" + "-" * 105)
        print("[STEP 3] Testing Immutability Protection: Attempting normal UPDATE on Receipt #3...")
        tamper_target = created_receipts[2]  # Receipt #3
        try:
            tamper_target.status = "verified"
            db.commit()
            print("  [FAILED] Immutability failed: Update was permitted!")
        except Exception as pe:
            db.rollback()
            print(f"  [BLOCKED] Immutability successfully protected ledger! Exception caught:")
            print(f"            {type(pe).__name__}: {pe}")

        # --------------------------------------------------------------------
        # STEP 4: Simulate Malicious Database Tampering Attack
        # --------------------------------------------------------------------
        print("\n" + "-" * 105)
        print(f"[STEP 4] Simulating Database Tampering Attack on Receipt #{tamper_target.id}...")
        print(f"  Target Row Details Before Tamper:")
        print(f"    - ID:     {tamper_target.id}")
        print(f"    - Source: {tamper_target.source}")
        print(f"    - Status: {tamper_target.status} (original: mismatch_detected)")
        print(f"    - Hash:   {tamper_target.receipt_hash[:24]}...")

        # Malicious actor with raw DB access bypasses application triggers
        # Changes status from 'mismatch_detected' to 'verified' to fraudulently approve the application
        is_postgres = "postgres" in str(engine.url).lower()
        if is_postgres:
            db.execute(text("ALTER TABLE verification_receipts DISABLE TRIGGER trg_block_verification_receipt_mutation;"))
            db.execute(text(f"UPDATE verification_receipts SET status = 'verified' WHERE id = {tamper_target.id};"))
            db.execute(text("ALTER TABLE verification_receipts ENABLE TRIGGER trg_block_verification_receipt_mutation;"))
            db.commit()
        else:
            db.execute(text("DROP TRIGGER IF EXISTS trg_block_receipts_update;"))
            db.execute(text(f"UPDATE verification_receipts SET status = 'verified' WHERE id = {tamper_target.id};"))
            db.commit()
            # Reapply trigger
            apply_db_immutability_triggers(engine)

        print(f"\n  [!] Malicious alteration executed directly in database:")
        print(f"    - Status fraudulently flipped to: 'verified'")
        print(f"    - Note: The attacker CANNOT forge the Ed25519 signature or recalculate downstream chain hashes!")

        # --------------------------------------------------------------------
        # STEP 5: Run verify_chain() to Detect Tampering
        # --------------------------------------------------------------------
        print("\n" + "-" * 105)
        print("[STEP 5] Running verify_chain() to Audit Ledger Authenticity...")
        tampered_check = verify_chain(db, application_id=app.id)

        print(f"\n  ================== TAMPER DETECTION AUDIT REPORT ==================")
        print(f"  Ledger Integrity:     {'COMPROMISED / TAMPERED' if not tampered_check['is_valid'] else 'VALID'}")
        print(f"  Audit Status:         {tampered_check['status']}")
        print(f"  Anomaly Type:         {tampered_check.get('tamper_type')}")
        print(f"  Broken Receipt ID:    #{tampered_check.get('broken_receipt_id')}")
        print(f"  Broken Link Index:    Index {tampered_check.get('broken_link_index')} in verification sequence")
        print(f"  Diagnostic Details:   {tampered_check.get('error_message')}")
        print(f"  First Broken Link Details:")
        for k, v in tampered_check.get("first_broken_link", {}).items():
            print(f"    - {k}: {v}")
        print("  ===================================================================")

        assert tampered_check["is_valid"] is False, "Expected tampering detection to fail validation!"
        assert tampered_check["broken_receipt_id"] == tamper_target.id, "Expected broken link to identify Receipt #3!"
        print(f"\n[SUCCESS] Tamper-evident ledger successfully identified the exact forged row (#{tamper_target.id}) and prevented regulatory fraud.\n")
        print("=" * 105 + "\n")
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_receipt_tamper_demo()
    sys.exit(0 if success else 1)
