from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import get_settings
from .models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()
ALGORITHM = "HS256"
COOKIE_NAME = "pocketsmart_token"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user.id), "email": user.email, "exp": expires_at},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
