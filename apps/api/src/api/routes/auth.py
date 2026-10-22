"""Authentication and user management endpoints."""
from typing import Any, Dict

from core.security import (
    create_access_token,
    get_current_user_payload,
    hash_password,
    verify_password,
)
from db.base import get_db
from db.models import Organization, User
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "CarbonAnalyst"
    organization_name: str = "Carbon Consultancy India"


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    token = create_access_token(
        subject=user.email,
        role=user.role,
        organization_id=user.organization_id,
    )
    return LoginResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": user.organization_id,
        },
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: UserCreate, db: Session = Depends(get_db)):
    email_clean = req.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    org = db.query(Organization).first()
    if not org:
        org = Organization(name=req.organization_name)
        db.add(org)
        db.commit()
        db.refresh(org)

    user = User(
        organization_id=org.id,
        email=email_clean,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "user_id": user.id}


@router.get("/me")
def get_current_user(payload: Dict[str, Any] = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization_id": user.organization_id,
    }
