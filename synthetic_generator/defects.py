"""
Defect Planting Engine & Ground Truth Logger:
Manages deliberate regulatory defects across documents, faculty, infrastructure, and institutions:
1. expired_document
2. missing_signature_field
3. wrong_institution_name
4. mismatched_reference_number
5. edited_amount
6. faculty_duplicate_across_institutions
7. area_too_small_for_intake
8. date_before_issuer_existed
9. reused_photo
"""
import os
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

GROUND_TRUTH_COLUMNS = [
    "institution_id",
    "institution_name",
    "document_id",
    "document_type",
    "defect_type",
    "details",
    "severity",
    "expected_regulatory_flag",
    "timestamp"
]

class GroundTruthLogger:
    def __init__(self, filepath: str = "ground_truth.csv"):
        self.filepath = filepath
        self.records: List[Dict[str, Any]] = []
        self._init_csv()

    def _init_csv(self):
        """Initializes ground_truth.csv with headers if file does not exist."""
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=GROUND_TRUTH_COLUMNS)
                writer.writeheader()

    def log_defect(
        self,
        institution_id: str,
        institution_name: str,
        document_id: str,
        document_type: str,
        defect_type: str,
        details: str,
        severity: str = "CRITICAL",
        expected_regulatory_flag: str = "INDICATOR_FOR_REVIEW"
    ):
        """Logs a planted defect record into ground truth registry and CSV."""
        record = {
            "institution_id": institution_id,
            "institution_name": institution_name,
            "document_id": document_id,
            "document_type": document_type,
            "defect_type": defect_type,
            "details": details,
            "severity": severity,
            "expected_regulatory_flag": expected_regulatory_flag,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.records.append(record)
        
        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=GROUND_TRUTH_COLUMNS)
            writer.writerow(record)

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistics on planted defects."""
        defect_counts = {}
        for r in self.records:
            d_type = r["defect_type"]
            defect_counts[d_type] = defect_counts.get(d_type, 0) + 1
        return {
            "total_defects_planted": len(self.records),
            "breakdown_by_defect_type": defect_counts
        }
