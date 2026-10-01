from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import LoginRequest, RegisterRequest
from ..security import COOKIE_NAME, create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _authenticated_response(message: str, user: User) -> JSONResponse:
    response = JSONResponse(
        {
            "message": message,
            "user": {"id": user.id, "name": user.name, "email": user.email},
        }
    )
    response.set_cookie(
        COOKIE_NAME,
        create_token(user),
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _authenticated_response("Registration successful", user)


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return _authenticated_response("Login successful", user)


@router.post("/logout")
def logout():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email}
