"""
PRAMAAN-X Document Ingestion & Classification Pipeline (Prompt 5.1):
1. Ingestion: Accepts PDF/Image -> Converts pages to images (pdf2image with PyMuPDF fallback)
2. OCR: PaddleOCR -> Tesseract fallback -> PyMuPDF vector/layout block fallback
3. Classification:
   - Tier 1: Keyword & Regex pattern matching
   - Tier 2: TF-IDF + Logistic Regression ML classifier trained on synthetic regulatory documents
4. Structured Output: per-page text, confidence, bounding boxes, and document type.
"""
import os
import io
import re
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
from PIL import Image

# Import ML dependencies
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Optional PDF & OCR engines
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdf2image
except ImportError:
    pdf2image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from paddleocr import PaddleOCR
    _paddle_instance = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
except Exception:
    _paddle_instance = None

logger = logging.getLogger("ingestion_pipeline")

# ==============================================================================
# DOCUMENT CLASSIFICATION PATTERNS (Tier 1 Keyword/Regex)
# ==============================================================================

DOCUMENT_CLASSIFICATION_PATTERNS: Dict[str, List[str]] = {
    "Fire Safety Certificate": [
        r"fire\s*(?:and|&)?\s*emergency",
        r"fire\s*(?:safety|clearance|noc|certificate)",
        r"chief\s*fire\s*officer",
        r"fire\s*prevention\s*measures",
        r"fire\s*station\s*officer",
        r"national\s*building\s*code\s*part\s*iv"
    ],
    "Land Title Deed": [
        r"sale\s*deed",
        r"lease\s*deed",
        r"sub-registrar",
        r"revenue\s*department",
        r"schedule\s*property",
        r"khasra",
        r"survey\s*no",
        r"demarcation",
        r"bhoomi|mahabhulekh",
        r"encumbrance\s*certificate"
    ],
    "Building Plan Approval": [
        r"building\s*(?:plan|permission|permit)",
        r"occupancy\s*certificate",
        r"town\s*planning",
        r"municipal\s*corporation",
        r"bmrda|cidco|dda",
        r"built-up\s*(?:carpet)?\s*area",
        r"instructional\s*carpet\s*area",
        r"master\s*plan"
    ],
    "Faculty Roster": [
        r"faculty\s*(?:roster|list|details)",
        r"teaching\s*staff",
        r"cadre\s*ratio",
        r"ugc\s*7th\s*cpc",
        r"assistant\s*professor",
        r"associate\s*professor",
        r"pan\s*masked",
        r"form\s*16"
    ],
    "University Affiliation Order": [
        r"affiliation\s*order",
        r"affiliating\s*university",
        r"continuation\s*of\s*affiliation",
        r"academic\s*council",
        r"vtu|aktu|anna\s*univ",
        r"statutory\s*affiliation"
    ],
    "Accreditation": [
        r"national\s*board\s*of\s*accreditation",
        r"nba|naac",
        r"\bnba[_\-]",
        r"washington\s*accord",
        r"tier-?[12]",
        r"accreditation\s*status",
        r"evaluation\s*score"
    ],
    "NOC": [
        r"no\s*objection\s*certificate",
        r"state\s*government\s*noc",
        r"department\s*of\s*higher\s*(?:and|&)?\s*technical\s*education",
        r"noc\s*sanction",
        r"secretariat\s*order",
        r"\bnoc\b",
        r"\bnoc[_\-]"
    ],
    "Affidavit": [
        r"affidavit",
        r"\baff[_\-]",
        r"deponent",
        r"notary\s*public",
        r"solemnly\s*affirm",
        r"oath\s*commissioner",
        r"notarial\s*stamp",
        r"advocate\s*notary"
    ],
    "Audited Financial Statement": [
        r"audited\s*balance\s*sheet",
        r"income\s*(?:and|&)\s*expenditure",
        r"chartered\s*accountant",
        r"udin",
        r"auditor'?s\s*report",
        r"fixed\s*assets\s*schedule"
    ]
}

# ==============================================================================
# ML DOCUMENT CLASSIFIER (Tier 2 TF-IDF + Logistic Regression)
# ==============================================================================

class DocumentTypeClassifier:
    """
    Two-Tier Document Type Classifier:
    1. Keyword & regex pattern matching (high speed, deterministic)
    2. Small ML model (TF-IDF + Logistic Regression) trained on synthetic document catalog.
    """
    def __init__(self):
        self.ml_pipeline: Optional[Pipeline] = None
        self._init_ml_model()

    def _init_ml_model(self):
        """Initializes and trains TF-IDF Logistic Regression pipeline on synthetic document catalog."""
        training_corpus: List[str] = []
        training_labels: List[str] = []

        # 1. Attempt loading synthetic documents from generated_data
        workspace_root = Path(__file__).resolve().parent.parent.parent.parent
        catalog_path = workspace_root / "generated_data" / "documents_catalog.json"
        
        if catalog_path.exists():
            try:
                with open(catalog_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
                
                for item in catalog:
                    doc_type = item.get("document_type")
                    rel_path = item.get("file_path")
                    if doc_type and rel_path:
                        doc_file = workspace_root / rel_path
                        if doc_file.exists() and fitz:
                            try:
                                doc_pdf = fitz.open(str(doc_file))
                                text = " ".join(page.get_text() for page in doc_pdf)
                                if text.strip():
                                    training_corpus.append(text)
                                    training_labels.append(doc_type)
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"Could not load synthetic catalog for classifier: {e}")

        # 2. Add rich synthetic reference corpus for regulatory diversity
        seed_samples = [
            ("Fire Safety Certificate", "Government State Fire & Emergency Services Department Office of the Chief Fire Officer Fire Safety Clearance Certificate NOC sanctioned inspection under NBC educational premises building."),
            ("Fire Safety Certificate", "State Fire Command Fire Prevention Measures Certificate Inspection Report No FS 2024 educational occupancy compliant valid till June 2027."),
            ("Land Title Deed", "Government Department of Stamps & Registration Registered Sale Lease Deed Revenue Survey Number Sub-Registrar Khata Patta non-agricultural educational clear title unbroken 30 years possession."),
            ("Land Title Deed", "Conveyance Deed Freehold Title Deed Revenue Department Khasra Survey 42/1 Devanahalli Taluk extent acres educational trust lessor lessee."),
            ("Building Plan Approval", "Municipal Corporation Town Planning Authority Approved Master Building Plan Occupancy Certificate sanctioned built-up instructional carpet area sqm architectural drawings classrooms laboratories."),
            ("Building Plan Approval", "Development Authority BMRDA Approved Architectural Floor Plans Structural Stability Certificate built-up area carpet area norms educational building."),
            ("Faculty Roster", "Approved Teaching Faculty Roster Cadre Proportion Professor Associate Assistant Professor PAN Aadhaar masked 7th CPC scale regular full-time appointments student ratio."),
            ("Faculty Roster", "List of Faculty Members Teaching Staff Qualifications Ph.D. University scale cadre ratio 1:2:6 sanctioned intake appointments."),
            ("University Affiliation Order", "Visvesvaraya Technological University State Examining University Notification Continuation of Annual Affiliation Order Section 40 approved branches intake active valid academic year."),
            ("University Affiliation Order", "State Technical University Affiliation Cell Order grant of temporary affiliation B.Tech Engineering courses registrar academic council."),
            ("Accreditation", "National Board of Accreditation NBA Tier 1 Washington Accord accreditation score 768 accredited programmes valid till accreditation committee."),
            ("Accreditation", "NBA Evaluation Report Accreditation Certificate Tier-1 Washington Accord Computer Science Engineering status accredited."),
            ("NOC", "State Department of Higher and Technical Education No Objection Certificate NOC government order sanctioning technical institute establishment expansion."),
            ("NOC", "Government Order State Secretariat Higher Technical Education No Objection Certificate NOC issuance university affiliation AICTE approval."),
            ("Affidavit", "Standard Sworn Affidavit Deponent Oath Commissioner Registered Notary Public solemnly affirm declare governing council AICTE norms trust deed."),
            ("Affidavit", "Notarized Regulatory Affidavit Stamp Paper Notary Registration Number deponent legal declaration compliance handbook regulations.")
        ]

        for label, text in seed_samples:
            training_corpus.append(text)
            training_labels.append(label)

        # Train pipeline
        try:
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=1200, stop_words='english')),
                ('clf', LogisticRegression(C=1.0, max_iter=200, random_state=42))
            ])
            pipeline.fit(training_corpus, training_labels)
            self.ml_pipeline = pipeline
            logger.info(f"Initialized TF-IDF + Logistic Regression document classifier on {len(training_corpus)} samples.")
        except Exception as e:
            logger.error(f"Failed to train ML document classifier: {e}")
            self.ml_pipeline = None

    @property
    def is_trained(self) -> bool:
        return self.ml_pipeline is not None

    def train_ml_model(self, corpus: List[str], labels: List[str]):
        """Trains or re-trains the TF-IDF + Logistic Regression pipeline."""
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=1200, stop_words='english')),
            ('clf', LogisticRegression(C=1.0, max_iter=200, random_state=42))
        ])
        pipeline.fit(corpus, labels)
        self.ml_pipeline = pipeline
        return self.ml_pipeline

    def predict_ml(self, text: str) -> str:
        """Predicts document type using the trained ML model directly."""
        if not self.ml_pipeline or not text.strip():
            return "Supporting Document / Affidavit"
        return str(self.ml_pipeline.predict([text])[0])

    def classify(self, text: str, filename: str = "") -> Tuple[str, float, str]:
        """
        Classifies document text:
        Returns: (doc_type, confidence, method)
        """
        combined_text = (filename + " " + text).lower()

        # Step 1: Keyword & Regex evaluation
        best_regex_type = None
        max_matches = 0

        for doc_type, patterns in DOCUMENT_CLASSIFICATION_PATTERNS.items():
            matches = sum(1 for pat in patterns if re.search(pat, combined_text))
            if matches > max_matches:
                max_matches = matches
                best_regex_type = doc_type

        if best_regex_type and max_matches >= 1:
            confidence = min(0.99, 0.75 + (max_matches * 0.08))
            return best_regex_type, round(confidence, 2), "keyword_regex"

        # Step 2: Fall back to TF-IDF + Logistic Regression ML model
        if self.ml_pipeline is not None and text.strip():
            try:
                probs = self.ml_pipeline.predict_proba([text])[0]
                classes = self.ml_pipeline.classes_
                max_idx = probs.argmax()
                ml_type = str(classes[max_idx])
                ml_conf = float(probs[max_idx])
                
                # If regex had at least 1 match, synthesize confidence
                if best_regex_type and best_regex_type == ml_type:
                    ml_conf = min(0.98, ml_conf + 0.15)
                
                return ml_type, round(ml_conf, 2), "tfidf_logistic_regression"
            except Exception as e:
                logger.warning(f"ML classification failed: {e}")

        # Fallback heuristic if ML unavailable or empty text
        if best_regex_type:
            return best_regex_type, 0.72, "keyword_regex"

        return "Supporting Document / Affidavit", 0.50, "default_fallback"



# ==============================================================================
# OCR & INGESTION PIPELINE
# ==============================================================================

class IngestionPipeline:
    """
    Ingests PDF or image, renders pages, performs OCR (PaddleOCR -> Tesseract -> Vector blocks),
    and classifies document type.
    """
    def __init__(self):
        self.classifier = DocumentTypeClassifier()

    def convert_to_images(self, file_bytes: bytes, filename: str) -> List[Tuple[int, Image.Image, int, int]]:
        """
        Converts input file (PDF or image) to a list of (page_num, PIL_Image, width, height).
        Uses pdf2image when available, falling back to PyMuPDF (fitz) or direct PIL image opening.
        """
        lower_name = filename.lower()
        pages: List[Tuple[int, Image.Image, int, int]] = []

        # Case 1: PDF Document
        if lower_name.endswith(".pdf") or file_bytes[:4] == b"%PDF":
            # Try pdf2image first
            converted_with_pdf2image = False
            if pdf2image:
                try:
                    pil_images = pdf2image.convert_from_bytes(file_bytes, dpi=150)
                    for idx, img in enumerate(pil_images, start=1):
                        pages.append((idx, img, img.width, img.height))
                    converted_with_pdf2image = True
                except Exception as e:
                    logger.debug(f"pdf2image conversion skipped ({e}). Falling back to PyMuPDF.")

            # Fallback to PyMuPDF (fitz)
            if not converted_with_pdf2image and fitz:
                try:
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    for idx, page in enumerate(doc, start=1):
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                        pages.append((idx, img, int(page.rect.width), int(page.rect.height)))
                except Exception as e:
                    logger.error(f"PyMuPDF rendering error: {e}")

        # Case 2: Standard Image file (PNG, JPG, TIFF)
        if not pages:
            try:
                img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                pages.append((1, img, img.width, img.height))
            except Exception as e:
                logger.error(f"Failed to open image file: {e}")

        return pages

    def perform_ocr_on_page(self, page_img: Image.Image, page_num: int, pdf_page_fitz: Any = None) -> Dict[str, Any]:
        """
        Executes OCR:
        1. PaddleOCR if available
        2. Tesseract if available
        3. PyMuPDF vector text extraction with bounding boxes if available
        4. Synthetic heuristic fallback
        """
        lines: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        # 1. PaddleOCR
        if _paddle_instance is not None:
            try:
                img_byte_arr = io.BytesIO()
                page_img.save(img_byte_arr, format='PNG')
                ocr_res = _paddle_instance.ocr(img_byte_arr.getvalue(), cls=True)
                if ocr_res and ocr_res[0]:
                    for line_entry in ocr_res[0]:
                        bbox = line_entry[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                        text, conf = line_entry[1]
                        ymin = int(min(pt[1] for pt in bbox))
                        xmin = int(min(pt[0] for pt in bbox))
                        ymax = int(max(pt[1] for pt in bbox))
                        xmax = int(max(pt[0] for pt in bbox))
                        lines.append({
                            "text": text,
                            "confidence": round(float(conf), 2),
                            "bounding_box": [ymin, xmin, ymax, xmax]
                        })
                        full_text_parts.append(text)
            except Exception as e:
                logger.debug(f"PaddleOCR failed: {e}. Trying secondary OCR.")

        # 2. PyTesseract Fallback
        if not lines and pytesseract:
            try:
                data = pytesseract.image_to_data(page_img, output_type=pytesseract.Output.DICT)
                n_boxes = len(data['text'])
                current_line = []
                for i in range(n_boxes):
                    text = data['text'][i].strip()
                    conf = float(data['conf'][i])
                    if text and conf > 30:
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        lines.append({
                            "text": text,
                            "confidence": round(conf / 100.0, 2),
                            "bounding_box": [y, x, y + h, x + w]
                        })
                        full_text_parts.append(text)
            except Exception as e:
                logger.debug(f"Tesseract OCR failed: {e}")

        # 3. PyMuPDF Text Blocks Fallback (Fast, highly accurate for digital PDFs)
        if not lines and pdf_page_fitz is not None:
            try:
                blocks = pdf_page_fitz.get_text("blocks")
                for b in blocks:
                    # b: (x0, y0, x1, y1, "text", block_no, block_type)
                    if len(b) >= 5 and b[4].strip():
                        b_text = b[4].strip()
                        lines.append({
                            "text": b_text,
                            "confidence": 0.98,
                            "bounding_box": [int(b[1]), int(b[0]), int(b[3]), int(b[2])]
                        })
                        full_text_parts.append(b_text)
            except Exception as e:
                logger.debug(f"PyMuPDF block extraction failed: {e}")

        # Assemble full text
        full_text = "\n".join(full_text_parts) if full_text_parts else ""

        return {
            "page_number": page_num,
            "width": page_img.width,
            "height": page_img.height,
            "full_text": full_text,
            "lines": lines
        }

    def ingest_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Complete Ingestion Pipeline execution (Prompt 5.1):
        Converts file -> OCR per page -> Classifies Document Type -> Measures processing time.
        """
        start_time = time.perf_counter()

        # Step 1: Render pages
        rendered_pages = self.convert_to_images(file_bytes, filename)
        if not rendered_pages:
            # Create a fallback placeholder image
            placeholder = Image.new("RGB", (595, 842), color=(255, 255, 255))
            rendered_pages = [(1, placeholder, 595, 842)]

        # Open PyMuPDF doc if PDF for high-speed block extraction
        fitz_doc = None
        if fitz and (filename.lower().endswith(".pdf") or file_bytes[:4] == b"%PDF"):
            try:
                fitz_doc = fitz.open(stream=file_bytes, filetype="pdf")
            except Exception:
                pass

        # Step 2: Run OCR on each page
        pages_ocr: List[Dict[str, Any]] = []
        combined_full_text: List[str] = []

        for page_num, img, w, h in rendered_pages:
            pdf_page = fitz_doc[page_num - 1] if fitz_doc and len(fitz_doc) >= page_num else None
            page_data = self.perform_ocr_on_page(img, page_num, pdf_page)
            pages_ocr.append(page_data)
            if page_data["full_text"]:
                combined_full_text.append(page_data["full_text"])

        # Step 3: Classify Document
        aggregate_text = "\n".join(combined_full_text)
        doc_type, conf, method = self.classifier.classify(aggregate_text, filename)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "filename": filename,
            "doc_type": doc_type,
            "classifier_confidence": conf,
            "classifier_method": method,
            "total_pages": len(pages_ocr),
            "per_page_ocr": pages_ocr,
            "pages": pages_ocr,
            "full_extracted_text": aggregate_text,
            "processing_time_ms": max(12, duration_ms)
        }

# Global Singleton
ingestion_pipeline = IngestionPipeline()
