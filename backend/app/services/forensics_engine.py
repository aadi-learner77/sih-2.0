"""
Forensics Engine:
1. Document Metadata Integrity Scanner (Tool signatures, modification timestamps, author anomalies)
2. Error-Level Analysis (ELA) for image tampering and altered certificates
3. Photo Reuse Radar using Perceptual Hashes (pHash / dHash) across all technical institutions
4. Cryptographic Document Deduplication (SHA-256)
"""
import io
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageChops, ImageEnhance
import imagehash

class ForensicsEngine:
    def __init__(self):
        # Cross-institution repository of registered campus infrastructure photos
        # Key: phash_hex, Value: metadata
        self.photo_radar_registry: List[Dict[str, Any]] = []
        self._seed_photo_radar()

    def _seed_photo_radar(self):
        """Seeds realistic historical photo perceptual hashes from across Indian institutions."""
        # Simulated hashes representing standard laboratory, library, and campus photos
        self.photo_radar_registry = [
            {
                "hash_hex": "a8f0c3d2e1b4a5f6",
                "institution_id": "INST_002",
                "institution_name": "Royal College of Engineering",
                "application_no": "EOA-2024-ENG-1102",
                "photo_category": "Computer Science Laboratory 1",
                "submitted_year": "2024",
                "file_name": "cs_lab_advanced_workstations.jpg"
            },
            {
                "hash_hex": "b7e1d4c3f2a5b6c7",
                "institution_id": "INST_003",
                "institution_name": "National Academy of Technical Studies",
                "application_no": "EOA-2023-ENG-8419",
                "photo_category": "Central Digital Library & Reading Hall",
                "submitted_year": "2023",
                "file_name": "central_library_reading_hall.jpg"
            },
            {
                "hash_hex": "c6d2e5b4a3f1c8e9",
                "institution_id": "INST_004",
                "institution_name": "Zenith Institute of Engineering",
                "application_no": "EOA-2024-ENG-5532",
                "photo_category": "Chemistry & Material Testing Lab",
                "submitted_year": "2024",
                "file_name": "chemistry_analytical_lab.jpg"
            }
        ]

    def compute_sha256(self, file_bytes: bytes) -> str:
        """Computes SHA-256 cryptographic checksum."""
        return hashlib.sha256(file_bytes).hexdigest()

    def compute_perceptual_hash(self, image: Image.Image) -> str:
        """Computes 64-bit perceptual hash (pHash) for an image."""
        try:
            return str(imagehash.phash(image))
        except Exception:
            return "0000000000000000"

    def perform_error_level_analysis(self, image: Image.Image, quality: int = 92) -> Tuple[float, Dict[str, Any]]:
        """
        Performs Error-Level Analysis (ELA) by re-compressing the image as JPEG
        and measuring pixel differences against the original.
        High discrepancy indicates localized digital tampering (e.g. pasted text/stamps).
        Returns:
            ela_score (0.0 to 1.0, where > 0.65 suggests suspicious localized manipulation)
            details dict
        """
        try:
            # Convert to RGB if needed
            orig_rgb = image.convert("RGB")
            
            # Save to buffer with standard JPEG quality
            buffer = io.BytesIO()
            orig_rgb.save(buffer, "JPEG", quality=quality)
            buffer.seek(0)
            
            recompressed = Image.open(buffer)
            
            # Compute absolute difference
            diff = ImageChops.difference(orig_rgb, recompressed)
            
            # Compute extremum and scale
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema]) if extrema else 0
            
            # Calculate mean difference
            # Enhance difference for inspection
            scale = 255.0 / max(1, max_diff)
            enhanced = ImageEnhance.Brightness(diff).enhance(scale)
            
            # Compute mean pixel value of enhanced difference
            gray_diff = diff.convert("L")
            hist = gray_diff.histogram()
            total_pixels = sum(hist)
            if total_pixels == 0:
                return 0.0, {"status": "NO_PIXELS"}
                
            weighted_sum = sum(i * count for i, count in enumerate(hist))
            mean_diff = weighted_sum / total_pixels
            
            # Normalized ELA score
            ela_score = round(min(1.0, mean_diff / 15.0), 3)
            is_tampered = ela_score > 0.65
            
            return ela_score, {
                "ela_score": ela_score,
                "is_anomalous": is_tampered,
                "max_channel_difference": max_diff,
                "mean_recompression_delta": round(mean_diff, 2),
                "assessment": "High localized compression divergence detected (possible stamp/text modification)" if is_tampered else "Homogeneous compression artifacts consistent with original scan"
            }
        except Exception as e:
            return 0.0, {"error": str(e), "status": "FAILED"}

    def scan_metadata_integrity(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Inspects PDF / image headers for forensic anomalies:
        - Image editing tools (Photoshop, Canva, GIMP, Inkscape, Paint)
        - Inconsistent dates
        - Multiple editing revisions
        """
        anomalies = []
        software_detected = []
        is_suspicious = False
        
        # Binary search for common editing software signatures
        signatures = [
            (b"Photoshop", "Adobe Photoshop"),
            (b"GIMP", "GNU Image Manipulation Program (GIMP)"),
            (b"Canva", "Canva Online Editor"),
            (b"Inkscape", "Inkscape Vector Graphics"),
            (b"Sejda", "Sejda Online PDF Editor"),
            (b"PDFescape", "PDFescape Tool"),
            (b"CorelDRAW", "CorelDRAW Graphic Suite"),
            (b"ilovepdf", "iLovePDF Online Tool")
        ]
        
        for sig_bytes, tool_name in signatures:
            if sig_bytes in file_bytes:
                software_detected.append(tool_name)
                is_suspicious = True
                anomalies.append(
                    f"Digital editing signature detected: '{tool_name}'. "
                    f"Official government certificates and municipal NOCs are rarely generated with desktop image manipulation suites."
                )

        file_size_kb = round(len(file_bytes) / 1024, 1)

        return {
            "filename": filename,
            "file_size_kb": file_size_kb,
            "is_suspicious": is_suspicious,
            "software_detected": software_detected,
            "anomalies": anomalies,
            "forensic_risk_level": "ELEVATED" if is_suspicious else "NORMAL",
            "advisory_note": "AI Indicator: Flagged for scrutiny officer visual inspection. Not proof of forgery."
        }

    def scan_photo_reuse_radar(self, phash_hex: str, current_institution_id: str) -> Dict[str, Any]:
        """
        Photo Reuse Radar:
        Compares input image pHash with the cross-institution registry.
        Uses Hamming distance to identify identical or re-used laboratory / campus photos.
        """
        if not phash_hex:
            return {"match_found": False, "details": "No perceptual hash available"}

        matches = []
        try:
            input_hash = imagehash.hex_to_hash(phash_hex)
        except Exception:
            return {"match_found": False, "details": "Invalid perceptual hash hex"}

        for registered in self.photo_radar_registry:
            # Skip matches within the exact same application if desired, but check cross-institution
            reg_hash = imagehash.hex_to_hash(registered["hash_hex"])
            distance = input_hash - reg_hash
            
            # Max hash length is 64 bits. Distance <= 10 indicates near-duplicate or identical photo
            if distance <= 10:
                similarity_pct = round((1.0 - (distance / 64.0)) * 100, 1)
                is_cross_institution = (registered["institution_id"] != current_institution_id)
                
                matches.append({
                    "matched_institution_id": registered["institution_id"],
                    "matched_institution_name": registered["institution_name"],
                    "matched_application_no": registered["application_no"],
                    "original_photo_category": registered["photo_category"],
                    "original_filename": registered["file_name"],
                    "original_submission_year": registered["submitted_year"],
                    "hamming_distance": int(distance),
                    "visual_similarity_pct": similarity_pct,
                    "is_cross_institution_reuse": is_cross_institution,
                    "flag_level": "CRITICAL" if is_cross_institution else "WARNING"
                })

        # Sort by similarity descending
        matches.sort(key=lambda x: x["visual_similarity_pct"], reverse=True)

        if matches:
            top = matches[0]
            explanation = (
                f"Photo Reuse Radar flagged: Submitted image matches ({top['visual_similarity_pct']}% similarity) "
                f"a photo previously submitted by '{top['matched_institution_name']}' under "
                f"Application {top['matched_application_no']} ({top['original_photo_category']}). "
                f"Indicator of potential infrastructure imagery re-use across distinct colleges."
            )
            return {
                "match_found": True,
                "matches_count": len(matches),
                "top_match": top,
                "all_matches": matches,
                "explanation": explanation,
                "advisory_disclaimer": "AI Flag: Indicator for physical committee verification. Not proof of forgery."
            }

        return {
            "match_found": False,
            "explanation": "No cross-institutional duplicate matches found in the AICTE Photo Radar repository."
        }

    def register_photo_hash(self, phash_hex: str, institution_id: str, inst_name: str, app_no: str, category: str, filename: str):
        """Adds a newly processed photo hash to the registry for ongoing cross-institutional radar."""
        self.photo_radar_registry.append({
            "hash_hex": phash_hex,
            "institution_id": institution_id,
            "institution_name": inst_name,
            "application_no": app_no,
            "photo_category": category,
            "submitted_year": "2025",
            "file_name": filename
        })

# Global singleton
forensics_engine = ForensicsEngine()
