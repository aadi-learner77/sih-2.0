"""
ReportLab PDF Generator for Official Regulatory Compliance Documents:
Generates authentic Indian regulatory PDFs with dynamic QR codes:
1. Affidavit (Non-Judicial E-Stamp Paper)
2. State Government / University NOC
3. Accreditation Certificate (NBA / NAAC)
4. Fire-Safety Certificate (State Fire & Emergency Services)
5. Land-Ownership / 30-Year Leasehold Document
"""
import os
import io
import qrcode
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
)
from reportlab.lib.units import inch

VERIFICATION_PORTAL_BASE = "https://aicte-india.org/scrutiny/verify"

def generate_qr_code_rl_image(ref_no: str, doc_type: str, custom_url: Optional[str] = None) -> RLImage:
    """Generates an embedded ReportLab QR code image encoding verification portal URL."""
    url = custom_url or f"{VERIFICATION_PORTAL_BASE}?ref={ref_no}&type={doc_type}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    rl_img = RLImage(buffer, width=1.1 * inch, height=1.1 * inch)
    return rl_img

def build_pdf_document(filepath: str, elements: list):
    """Builds PDF document with standard A4 margins."""
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    doc.build(elements)

# ----------------------------------------------------------------------------
# 1. AFFIDAVIT
# ----------------------------------------------------------------------------
def generate_affidavit_pdf(filepath: str, data: Dict[str, Any]):
    styles = getSampleStyleSheet()
    elements = []
    
    ref_no = data.get("reference_number", "AFF/2025/10921")
    inst_name = data.get("institution_name", "Technical Institute")
    issue_date = data.get("issue_date", "2025-01-15")
    valid_date = data.get("validity_date", "2026-06-30")
    trust_name = data.get("trust_name", "Educational Trust")
    signatory = data.get("signatory_name", "Dr. Chairman")
    omit_sig = data.get("omit_signature", False)
    
    qr_img = generate_qr_code_rl_image(ref_no, "Affidavit", data.get("qr_verification_url"))

    # E-Stamp Header Table
    stamp_header = [
        [Paragraph("<font color='#8B0000'><b>GOVERNMENT OF NATIONAL CAPITAL TERRITORY OF DELHI / STATE</b><br/>e-Stamp Certificate No: " + ref_no + "</font>", styles['Normal']), qr_img],
    ]
    t_header = Table(stamp_header, colWidths=[400, 120])
    t_header.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#8B0000')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF8DC')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 16))

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'))
    elements.append(Paragraph("AFFIDAVIT ON NON-JUDICIAL STAMP PAPER", title_style))
    elements.append(Paragraph("(FORMAT FOR AICTE APPROVAL PROCESS HANDBOOK 2025-26)", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, fontSize=9, textColor=colors.gray)))
    elements.append(Spacer(1, 12))

    body_text = f"""
    I/We, <b>{signatory}</b>, in my capacity as Chairman/Secretary of <b>{trust_name}</b>, running the institution 
    <b>{inst_name}</b>, do hereby solemnly affirm and state as under:
    <br/><br/>
    1. That the applicant society/trust has applied for Extension of Approval (EoA) / Introduction of courses 
    for the Academic Year 2025-26 under Reference Number <b>{ref_no}</b>.<br/>
    2. That the institution possesses clear, undisputed title of land and total instructional carpet area 
    strictly conforming to the prescribed AICTE norms.<br/>
    3. That all teaching faculty members listed in the institutional roster are appointed on a full-time regular basis 
    with pay scales adhering to the 7th Central Pay Commission (CPC).<br/>
    4. That the statements made herein and supporting documents uploaded on the AICTE portal are true, genuine, 
    and authenticated against state records.<br/>
    """
    elements.append(Paragraph(body_text, ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)))
    elements.append(Spacer(1, 24))

    # Verification and Date Table
    meta_table = [
        [Paragraph(f"<b>Issue Date:</b> {issue_date}", styles['Normal']), Paragraph(f"<b>Valid Till:</b> {valid_date}", styles['Normal'])],
        [Paragraph(f"<b>Notary Registration No:</b> NOT/DL/{ref_no[-5:]}", styles['Normal']), Paragraph("<b>Jurisdiction:</b> District Magistrate Court", styles['Normal'])]
    ]
    t_meta = Table(meta_table, colWidths=[260, 260])
    elements.append(t_meta)
    elements.append(Spacer(1, 24))

    # Signatory Section (Simulated missing signature defect if flagged)
    if omit_sig:
        sig_data = [
            ["", Paragraph("<b>[SIGNATURE & NOTARY STAMP OMITTED - DEFECT]</b>", styles['Normal'])],
            ["", Paragraph(f"Deponent: {signatory}", styles['Normal'])],
        ]
    else:
        sig_data = [
            [Paragraph("<i>Signed & Affirmed before me:</i><br/><b>ADVOCATE & NOTARY PUBLIC</b><br/>Govt of India", styles['Normal']),
             Paragraph(f"<b>DEPONENT</b><br/>{signatory}<br/>Authorized Signatory, {trust_name}", styles['Normal'])],
        ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    elements.append(t_sig)

    build_pdf_document(filepath, elements)

# ----------------------------------------------------------------------------
# 2. STATE GOVT / UNIVERSITY NOC
# ----------------------------------------------------------------------------
def generate_noc_pdf(filepath: str, data: Dict[str, Any]):
    styles = getSampleStyleSheet()
    elements = []
    
    ref_no = data.get("reference_number", "NOC/2025/7712")
    inst_name = data.get("institution_name", "Technical Institute")
    issue_date = data.get("issue_date", "2024-06-10")
    valid_date = data.get("validity_date", "2026-06-30")
    issuer_name = data.get("issuer_name", "Department of Higher Education, Govt of Karnataka")
    omit_sig = data.get("omit_signature", False)
    
    qr_img = generate_qr_code_rl_image(ref_no, "NOC", data.get("qr_verification_url"))

    header_table = [
        [Paragraph(f"<b>{issuer_name.upper()}</b><br/><font size=8>SECRETARIAT - TECHNICAL EDUCATION WING</font>", styles['Heading2']), qr_img]
    ]
    t_head = Table(header_table, colWidths=[400, 120])
    elements.append(t_head)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F172A'), spaceAfter=12))

    elements.append(Paragraph(f"<b>NO OBJECTION CERTIFICATE (NOC)</b>", ParagraphStyle('H1', parent=styles['Heading1'], alignment=1, fontSize=13)))
    elements.append(Paragraph(f"Letter No: <b>{ref_no}</b> | Dated: <b>{issue_date}</b>", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, fontSize=9, textColor=colors.gray)))
    elements.append(Spacer(1, 14))

    body_text = f"""
    The State Government has scrutinized the application submitted by <b>{inst_name}</b> 
    for Extension of Approval and Continuation of Technical Courses for the Academic Year 2025-26.
    <br/><br/>
    The Competent Authority hereby conveys its <b>NO OBJECTION</b> for conducting technical degree programmes 
    with the sanctioned intake subject to strict adherence to AICTE Approval Process Handbook regulations 
    and affiliating university statutes.
    <br/><br/>
    <b>Validity:</b> This NOC is valid up to <b>{valid_date}</b> or completion of the academic year 2025-26, 
    whichever is earlier.
    """
    elements.append(Paragraph(body_text, ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=15)))
    elements.append(Spacer(1, 30))

    if omit_sig:
        sig_data = [["", Paragraph("<b>[MISSING COMPETENT AUTHORITY SIGNATURE]</b>", styles['Normal'])]]
    else:
        sig_data = [
            ["", Paragraph(f"<b>Principal Secretary to Government</b><br/>{issuer_name}<br/>Official Seal & Signature", styles['Normal'])]
        ]
    t_sig = Table(sig_data, colWidths=[300, 220])
    elements.append(t_sig)

    build_pdf_document(filepath, elements)

# ----------------------------------------------------------------------------
# 3. ACCREDITATION CERTIFICATE (NBA / NAAC)
# ----------------------------------------------------------------------------
def generate_accreditation_certificate_pdf(filepath: str, data: Dict[str, Any]):
    styles = getSampleStyleSheet()
    elements = []
    
    ref_no = data.get("reference_number", "NBA/ACCR/2024/9912")
    inst_name = data.get("institution_name", "Technical Institute")
    issue_date = data.get("issue_date", "2024-03-20")
    valid_date = data.get("validity_date", "2027-06-30")
    issuer_name = data.get("issuer_name", "National Board of Accreditation (NBA), New Delhi")
    score = data.get("accreditation_score", 712)
    omit_sig = data.get("omit_signature", False)

    qr_img = generate_qr_code_rl_image(ref_no, "Accreditation", data.get("qr_verification_url"))

    header_table = [
        [Paragraph(f"<b>NATIONAL BOARD OF ACCREDITATION</b><br/><font size=8>Pragati Vihar, New Delhi - 110003</font>", styles['Heading2']), qr_img]
    ]
    t_head = Table(header_table, colWidths=[400, 120])
    elements.append(t_head)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#046A38'), spaceAfter=14))

    elements.append(Paragraph("CERTIFICATE OF ACCREDITATION", ParagraphStyle('H1', parent=styles['Heading1'], alignment=1, fontSize=15, textColor=colors.HexColor('#046A38'))))
    elements.append(Paragraph(f"Accreditation Reference: <b>{ref_no}</b>", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, fontSize=9, textColor=colors.gray)))
    elements.append(Spacer(1, 14))

    body_text = f"""
    This is to certify that the undergraduate technical degree programmes offered by:
    <br/><br/>
    <font size=12><b>{inst_name}</b></font>
    <br/><br/>
    have been evaluated by the Expert Visiting Committee of the National Board of Accreditation. 
    Based on the accreditation criteria evaluated under Tier-II / Washington Accord standards, 
    the institution has achieved an evaluation score of <b>{score} / 1000</b>.
    <br/><br/>
    <b>Status:</b> ACCREDITED for 3 Years (Valid from {issue_date} up to {valid_date}).
    """
    elements.append(Paragraph(body_text, ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=15, alignment=1)))
    elements.append(Spacer(1, 30))

    if omit_sig:
        sig_data = [["", Paragraph("<b>[MEMBER SECRETARY SIGNATURE OMITTED]</b>", styles['Normal'])]]
    else:
        sig_data = [
            ["", Paragraph("<b>Member Secretary</b><br/>National Board of Accreditation<br/>New Delhi", styles['Normal'])]
        ]
    t_sig = Table(sig_data, colWidths=[320, 200])
    elements.append(t_sig)

    build_pdf_document(filepath, elements)

# ----------------------------------------------------------------------------
# 4. FIRE-SAFETY CERTIFICATE
# ----------------------------------------------------------------------------
def generate_fire_safety_certificate_pdf(filepath: str, data: Dict[str, Any]):
    styles = getSampleStyleSheet()
    elements = []
    
    ref_no = data.get("reference_number", "FS/2024/991/BFO")
    inst_name = data.get("institution_name", "Apex Institute of Technology")
    issue_date = data.get("issue_date", "2024-05-12")
    valid_date = data.get("validity_date", "2026-03-31")
    issuer_name = data.get("issuer_name", "Karnataka Fire & Emergency Services Department")
    built_up_area = data.get("built_up_area_sqm", 12500.0)
    survey_no = data.get("survey_number", "Sy. No. 42/1")
    omit_sig = data.get("omit_signature", False)

    qr_img = generate_qr_code_rl_image(ref_no, "FireNOC", data.get("qr_verification_url"))

    header_table = [
        [Paragraph(f"<b>{issuer_name.upper()}</b><br/><font size=8>OFFICE OF THE CHIEF FIRE OFFICER</font>", styles['Heading2']), qr_img]
    ]
    t_head = Table(header_table, colWidths=[400, 120])
    elements.append(t_head)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#DC2626'), spaceAfter=14))

    elements.append(Paragraph("FIRE SAFETY CLEARANCE CERTIFICATE / NOC", ParagraphStyle('H1', parent=styles['Heading1'], alignment=1, fontSize=13, textColor=colors.HexColor('#B91C1C'))))
    elements.append(Paragraph(f"NOC Sanction Number: <b>{ref_no}</b>", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, fontSize=9, textColor=colors.gray)))
    elements.append(Spacer(1, 14))

    body_text = f"""
    Certified that the educational building premises occupied by <b>{inst_name}</b>, situated at 
    <b>{survey_no}</b>, was inspected on <b>{issue_date}</b> by the Fire Station Officer in the presence of the applicant.
    <br/><br/>
    The institutional infrastructure comprises approved built-up carpet area of <b>{built_up_area:,.1f} sq. meters</b>, 
    categorized under Educational Occupancy (Group-B) under the National Building Code (NBC) 2016.
    <br/><br/>
    All mandatory fire prevention, fire hydrants, wet risers, and escape routes were tested and found satisfactory.
    <br/><br/>
    <b>Validity Period:</b> This Fire Safety Clearance Certificate is valid from <b>{issue_date}</b> up to <b>{valid_date}</b>, 
    subject to annual maintenance of all active equipment.
    """
    elements.append(Paragraph(body_text, ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=15)))
    elements.append(Spacer(1, 30))

    if omit_sig:
        sig_data = [["", Paragraph("<b>[MISSING CHIEF FIRE OFFICER SEAL & SIGNATURE]</b>", styles['Normal'])]]
    else:
        sig_data = [
            ["", Paragraph("<b>Chief Fire Officer (East Zone)</b><br/>Fire & Emergency Services<br/>Govt of Karnataka", styles['Normal'])]
        ]
    t_sig = Table(sig_data, colWidths=[300, 220])
    elements.append(t_sig)

    build_pdf_document(filepath, elements)

# ----------------------------------------------------------------------------
# 5. LAND-OWNERSHIP / 30-YEAR LEASEHOLD DOCUMENT
# ----------------------------------------------------------------------------
def generate_land_ownership_pdf(filepath: str, data: Dict[str, Any]):
    styles = getSampleStyleSheet()
    elements = []
    
    ref_no = data.get("reference_number", "REG/LEAS/2021/4892")
    inst_name = data.get("institution_name", "Technical Institute")
    issue_date = data.get("issue_date", "2021-06-01")
    valid_date = data.get("validity_date", "2051-05-31")
    issuer_name = data.get("issuer_name", "Department of Stamps & Registration, Sub-Registrar Office")
    land_acres = data.get("land_area_acres", 5.5)
    survey_no = data.get("survey_number", "Sy. No. 42/1 & 42/2")
    lease_years = data.get("lease_duration_years", 30)
    trust_name = data.get("trust_name", "Educational Trust")
    omit_sig = data.get("omit_signature", False)

    qr_img = generate_qr_code_rl_image(ref_no, "LandDeed", data.get("qr_verification_url"))

    header_table = [
        [Paragraph(f"<b>GOVERNMENT OF KARNATAKA - REVENUE DEPARTMENT</b><br/><font size=8>OFFICE OF THE SUB-REGISTRAR</font>", styles['Heading2']), qr_img]
    ]
    t_head = Table(header_table, colWidths=[400, 120])
    elements.append(t_head)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F172A'), spaceAfter=14))

    elements.append(Paragraph("REGISTERED PERMANENT LEASEHOLD / TITLE DEED", ParagraphStyle('H1', parent=styles['Heading1'], alignment=1, fontSize=13)))
    elements.append(Paragraph(f"Registration Document No: <b>{ref_no}</b> | Book 1 Volume 812", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, fontSize=9, textColor=colors.gray)))
    elements.append(Spacer(1, 14))

    body_text = f"""
    This Deed of Registered Lease is entered on <b>{issue_date}</b> between <b>{trust_name}</b> (Lessor) 
    and <b>{inst_name}</b> (Lessee).
    <br/><br/>
    <b>Schedule Property:</b> Revenue Survey Number(s) <b>{survey_no}</b>, measuring total land area of 
    <b>{land_acres} Acres</b>, with conversion order passed for Non-Agricultural Educational Use.
    <br/><br/>
    <b>Tenure:</b> The Lessor grants continuous, uninterrupted leasehold rights to the Lessee for a minimum 
    unbroken duration of <b>{lease_years} Years</b>, expiring on <b>{valid_date}</b>, in full compliance 
    with AICTE Land Ownership & Title continuity regulations.
    <br/><br/>
    <b>Encumbrance Status:</b> Certified free from any mortgage, lien, or court caveats on registration date.
    """
    elements.append(Paragraph(body_text, ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=15)))
    elements.append(Spacer(1, 30))

    if omit_sig:
        sig_data = [["", Paragraph("<b>[SUB-REGISTRAR ATTESTATION OMITTED]</b>", styles['Normal'])]]
    else:
        sig_data = [
            ["", Paragraph("<b>Senior Sub-Registrar</b><br/>Revenue Sub-District Office<br/>Official Registering Officer", styles['Normal'])]
        ]
    t_sig = Table(sig_data, colWidths=[300, 220])
    elements.append(t_sig)

    build_pdf_document(filepath, elements)
