"""Security, authentication, password hashing, and RBAC roles."""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ph = PasswordHasher()
security_bearer = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    OrgAdmin = "OrgAdmin"
    ProjectManager = "ProjectManager"
    FieldSurveyor = "FieldSurveyor"
    DataReviewer = "DataReviewer"
    CarbonAnalyst = "CarbonAnalyst"
    ClientViewer = "ClientViewer"
    ACVAAuditor = "ACVAAuditor"


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def create_access_token(
    subject: str,
    role: str,
    organization_id: str = "org_default",
    expires_delta: Optional[datetime.timedelta] = None,
) -> str:
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "org_id": organization_id,
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_roles(allowed_roles: List[UserRole]):
    def role_checker(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> Dict[str, Any]:
        user_role = payload.get("role")
        if not user_role or user_role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{user_role}'. Required one of: {[r.value for r in allowed_roles]}",
            )
        return payload

    return role_checker


__all__ = [
    "UserRole",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user_payload",
    "require_roles",
]
