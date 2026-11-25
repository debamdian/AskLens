"""JWT Authentication & Verification for AskLens FastAPI Backend.

Uses HMAC-SHA256 (HS256) matching Auth.js / NextAuth JWT tokens signed with JWT_SECRET.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from app.core.config import settings


class AuthUser(BaseModel):
    """Authenticated user context extracted from JWT."""
    email: str
    role: str = "analyst"
    region_id: Optional[int] = None
    name: Optional[str] = None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(payload: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Create an HS256-signed JWT token."""
    exp_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = int(time.time())
    full_payload = {
        **payload,
        "iat": now,
        "exp": now + exp_minutes * 60,
    }
    header_b64 = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(full_payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify an HS256 JWT token and return its decoded payload."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format.")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid JWT signature.")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None and int(time.time()) > int(exp):
        raise ValueError("JWT token has expired.")
    return payload


async def get_optional_user(authorization: Optional[str] = Header(None)) -> AuthUser:
    """FastAPI dependency that verifies Bearer JWT if provided, or falls back in dev mode."""
    if not authorization:
        if settings.ENVIRONMENT == "development":
            return AuthUser(email="analyst@asklens.local", role="analyst", name="Local Analyst")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization scheme. Expected Bearer token.",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = verify_jwt_token(token)
        return AuthUser(
            email=payload.get("email", "user@asklens.local"),
            role=payload.get("role", "analyst"),
            region_id=payload.get("region_id"),
            name=payload.get("name"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
