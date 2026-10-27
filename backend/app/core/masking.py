"""
PRAMAAN-X PII Masking Utilities
Adheres to Indian regulatory guidelines for protecting sensitive personal identifiers (Aadhaar, PAN, contact info)
unless explicitly accessed with privileged audit clearance or viewed by the data-owning institution.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

PAN_REGEX = re.compile(r"\b([A-Z]{2})[A-Z]{3}[0-9]{4}([A-Z])\b", re.IGNORECASE)
AADHAAR_REGEX = re.compile(r"\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b")
PHONE_REGEX = re.compile(r"\b(\+?91[\-\s]?)?([6-9]\d{2})\d{4}(\d{3})\b")
EMAIL_REGEX = re.compile(r"\b([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b")


def mask_aadhaar(aadhaar: Optional[Union[str, int]]) -> str:
    """Masks Aadhaar number showing only the last 4 digits (e.g. XXXX-XXXX-1234)"""
    if not aadhaar:
        return ""
    clean = re.sub(r"[-\s]", "", str(aadhaar))
    if len(clean) >= 4:
        return f"XXXX-XXXX-{clean[-4:]}"
    return "XXXX-XXXX-XXXX"


def mask_pan(pan: Optional[str]) -> str:
    """Masks PAN card showing first 2 and last 2 characters (e.g. AB****34F)"""
    if not pan:
        return ""
    clean = str(pan).strip().upper()
    if len(clean) >= 5:
        return f"{clean[:2]}****{clean[-2:]}"
    return "******"


def mask_email(email: Optional[str]) -> str:
    """Masks email address (e.g. j***e@domain.edu)"""
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[Union[str, int]]) -> str:
    """Masks phone number showing only last 3 digits"""
    if not phone:
        return ""
    clean = re.sub(r"[^\d]", "", str(phone))
    if len(clean) >= 3:
        return f"{'*' * (len(clean) - 3)}{clean[-3:]}"
    return "******"


def mask_string_pii(text: str) -> str:
    """Detects and masks inline Aadhaar, PAN, phone numbers, and emails inside free-text."""
    if not isinstance(text, str):
        return text

    # Mask PAN
    text = PAN_REGEX.sub(r"\1****\2", text)
    # Mask Aadhaar
    text = AADHAAR_REGEX.sub(r"XXXX-XXXX-\3", text)
    # Mask Phone
    text = PHONE_REGEX.sub(r"*******\3", text)
    # Mask Email
    text = EMAIL_REGEX.sub(r"\1***@\2", text)
    return text


def mask_faculty_record(faculty: Dict[str, Any], is_privileged: bool = False) -> Dict[str, Any]:
    """Returns a copy of faculty dict with sensitive identifiers masked for scrutiny officers"""
    if is_privileged:
        return faculty
    masked = dict(faculty)
    if "aadhaar" in masked and masked["aadhaar"]:
        masked["aadhaar"] = mask_aadhaar(masked["aadhaar"])
    if "pan" in masked and masked["pan"]:
        masked["pan"] = mask_pan(masked["pan"])
    if "email" in masked and masked["email"]:
        masked["email"] = mask_email(masked["email"])
    if "phone" in masked and masked["phone"]:
        masked["phone"] = mask_phone(masked["phone"])
    return masked


PII_FIELD_KEYS = {
    "aadhaar", "aadhaar_no", "aadhaar_number",
    "pan", "pan_no", "pan_number", "faculty_pan",
    "phone", "mobile", "contact_no", "phone_number",
    "email", "email_id", "personal_email",
    "bank_account", "account_no", "bank_account_number", "tan"
}


def mask_pii_by_role(
    data: Any,
    user_role: str,
    is_owner: bool = False
) -> Any:
    """
    Role-based recursive PII masker:
    - Data owners (institution_user viewing their own institution) and admins see unmasked data.
    - Scrutiny Officers, Senior Officers, and Auditors see masked PAN, Aadhaar, phone, email, etc.
    """
    # Owners and Admins have unmasked visibility
    if is_owner or user_role == "admin":
        return data

    if isinstance(data, dict):
        masked_dict = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if k_lower in PII_FIELD_KEYS and v is not None:
                if "aadhaar" in k_lower:
                    masked_dict[k] = mask_aadhaar(v)
                elif "pan" in k_lower:
                    masked_dict[k] = mask_pan(v)
                elif "phone" in k_lower or "mobile" in k_lower or "contact" in k_lower:
                    masked_dict[k] = mask_phone(v)
                elif "email" in k_lower:
                    masked_dict[k] = mask_email(v)
                else:
                    masked_dict[k] = mask_string_pii(str(v))
            else:
                masked_dict[k] = mask_pii_by_role(v, user_role, is_owner=False)
        return masked_dict

    elif isinstance(data, list):
        return [mask_pii_by_role(item, user_role, is_owner=False) for item in data]

    elif isinstance(data, str):
        # Mask inline occurrences in string explanations or notes
        return mask_string_pii(data)

    return data
