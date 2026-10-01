from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from passlib.context import CryptContext

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User


settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

ALGORITHM = "HS256"

COOKIE_NAME = "pocketsmart_token"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        password,
        hashed_password,
    )


def create_token(user: User) -> str:
    expiration = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expiration,
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    return token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:

    token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required",
        )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload["sub"])

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user