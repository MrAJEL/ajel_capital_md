"""
AJEL Capital — Auth API Router
=========================================
Handles login and user management.
Passwords are never stored in plaintext — bcrypt only.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from database import get_db
from models.sql_models import User
from core.security import (
    hash_password, verify_password, create_access_token, get_current_user
)
from core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "viewer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, response: Response, req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=8 * 3600
    )
    return {"token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": user.role}}


@router.post("/auth/register")
@limiter.limit("5/minute")
async def register(request: Request, response: Response, req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. First user becomes admin."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # First user in the system is always admin
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else req.role

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    logger.info(f"New user registered: {user.email} (role: {role})")
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=8 * 3600
    )
    return {"token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": role}}

@router.post("/auth/logout")
async def logout(response: Response):
    """Logout user and clear cookie."""
    response.delete_cookie("access_token", httponly=True, secure=True, samesite="lax")
    return {"status": "success"}


@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current authenticated user info."""
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}
