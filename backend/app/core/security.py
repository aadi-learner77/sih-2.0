"""
PRAMAAN-X Core Security, Cryptography & Role-Based Access Control (RBAC)
Supported Roles:
- institution_user: Only permitted to view and submit data for their own institution.
- scrutiny_officer: Scrutiny committee member reviewing dossiers, running preflight/validation, executing officer actions.
- senior_officer: Senior / Regional regulatory officer with escalation review and determination permissions.
- admin: System administrator managing rules (CRUD + versioning), users, and platform configuration.
- auditor: Read-only access to all application dossiers, audit logs, and verification receipts.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Callable
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.models import User

# Standard RBAC Role Constants
ROLE_INSTITUTION_USER = "institution_user"
ROLE_SCRUTINY_OFFICER = "scrutiny_officer"
ROLE_SENIOR_OFFICER = "senior_officer"
ROLE_ADMIN = "admin"
ROLE_AUDITOR = "auditor"

ALL_ROLES = [
    ROLE_INSTITUTION_USER,
    ROLE_SCRUTINY_OFFICER,
    ROLE_SENIOR_OFFICER,
    ROLE_ADMIN,
    ROLE_AUDITOR
]

# Legacy role mapping for backwards compatibility
ROLE_ALIASES = {
    "regional_officer": ROLE_SENIOR_OFFICER,
    "super_admin": ROLE_ADMIN,
}

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def normalize_role(role: Optional[str]) -> str:
    """Normalizes role codes to standard 5 RBAC roles."""
    if not role:
        return ROLE_INSTITUTION_USER
    cleaned = str(role).strip().lower()
    return ROLE_ALIASES.get(cleaned, cleaned)


def hash_password(password: str) -> str:
    """Deterministic salt + SHA256 PBKDF2 hash for demo security."""
    salt = settings.SECRET_KEY[:16].encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored PBKDF2 hash."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates signed JWT access token containing subject, role, and custom claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decodes and validates JWT token signature and expiration."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """FastAPI Dependency resolving current authenticated user from JWT Bearer token."""
    if not token:
        # Fallback default user for unauthenticated requests in demo
        default_user = db.query(User).filter(User.role == ROLE_SCRUTINY_OFFICER).first()
        if default_user:
            return default_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    email: Optional[str] = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


def require_roles(*allowed_roles: str) -> Callable:
    """
    RBAC dependency factory that validates the current user's role.
    Admin is universally authorized unless explicitly excluded.
    """
    normalized_allowed = {normalize_role(r) for r in allowed_roles}
    # Always allow admin if not explicitly restricted
    normalized_allowed.add(ROLE_ADMIN)

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role = normalize_role(current_user.role)
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: User role '{user_role}' does not have permission. "
                    f"Required roles: {list(normalized_allowed)}"
                )
            )
        return current_user

    return role_dependency


def enforce_institution_isolation(user: User, institution_id: Optional[int]) -> None:
    """
    Enforces strict tenant isolation for institution_user.
    Institution users are prohibited from reading or mutating any data outside their institution.
    """
    user_role = normalize_role(user.role)
    if user_role == ROLE_INSTITUTION_USER:
        if institution_id is None or user.institution_id != institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: Institution users can only access their own institution's data "
                    f"(User institution ID: {user.institution_id}, requested: {institution_id})."
                )
            )
