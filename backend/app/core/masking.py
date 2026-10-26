"""
PRAMAAN-X PII Masking Utilities
Adheres to Indian regulatory guidelines for protecting sensitive personal identifiers (Aadhaar, PAN, contact info)
unless explicitly accessed with privileged audit clearance.
"""
import re

def mask_aadhaar(aadhaar: str | None) -> str:
    """Masks Aadhaar number showing only the last 4 digits (e.g. XXXX-XXXX-1234)"""
    if not aadhaar:
        return ""
    clean = re.sub(r"[-\s]", "", str(aadhaar))
    if len(clean) >= 4:
        return f"XXXX-XXXX-{clean[-4:]}"
    return "XXXX-XXXX-XXXX"

def mask_pan(pan: str | None) -> str:
    """Masks PAN card showing first 2 and last 2 characters (e.g. AB****34F)"""
    if not pan:
        return ""
    clean = str(pan).strip().upper()
    if len(clean) >= 5:
        return f"{clean[:2]}****{clean[-2:]}"
    return "******"

def mask_email(email: str | None) -> str:
    """Masks email address (e.g. j***e@domain.edu)"""
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"

def mask_phone(phone: str | None) -> str:
    """Masks phone number showing only last 3 digits"""
    if not phone:
        return ""
    clean = re.sub(r"[^\d]", "", str(phone))
    if len(clean) >= 3:
        return f"{'*' * (len(clean) - 3)}{clean[-3:]}"
    return "******"

def mask_faculty_record(faculty: dict, is_privileged: bool = False) -> dict:
    """Returns a copy of faculty dict with sensitive identifiers masked for scrutiny officers"""
    if is_privileged:
        return faculty
    masked = dict(faculty)
    if "aadhaar" in masked:
        masked["aadhaar"] = mask_aadhaar(masked["aadhaar"])
    if "pan" in masked:
        masked["pan"] = mask_pan(masked["pan"])
    if "email" in masked:
        masked["email"] = mask_email(masked["email"])
    if "phone" in masked:
        masked["phone"] = mask_phone(masked["phone"])
    return masked
