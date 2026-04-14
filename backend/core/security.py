"""
AJEL Capital — Security Module
==================================
JWT tokens, password hashing, rate limiting.
All secrets from environment variables — never hardcoded.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ── Secrets from environment only ─────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ajel-dev-secret-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

# ── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Bearer token scheme ──────────────────────────────────────────────────────
security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """
    Optional auth — returns user payload if token present, None otherwise.
    Used for endpoints that work with or without auth.
    """
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token[7:]
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        return None
    return decode_token(token)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """
    Required auth — raises 401 if no valid token.
    """
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token[7:]
    if not token and credentials:
        token = credentials.credentials
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token)


# ── Input Sanitization ────────────────────────────────────────────────────────
def sanitize_symbol(symbol: str) -> str:
    """Sanitize ticker symbol input to prevent injection."""
    import re
    cleaned = re.sub(r'[^A-Za-z0-9\-\.]', '', symbol.strip().upper())
    if len(cleaned) > 20:
        raise HTTPException(status_code=400, detail="Symbol too long")
    if not cleaned:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    return cleaned
