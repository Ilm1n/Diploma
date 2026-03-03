import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from src.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

PRIVATE_KEY = settings.auth_jwt.private_key_path.read_text()
PUBLIC_KEY = settings.auth_jwt.public_key_path.read_text()
ALGORITHM = settings.auth_jwt.algorithm

password_hash = PasswordHash.recommended()


def encode_jwt(
    payload: dict[str, Any],
    expire_minutes: int,
) -> str:
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)

    to_encode.update(
        exp=expire,
        iat=now,
        jti=str(uuid.uuid4()),
    )

    return jwt.encode(
        to_encode,
        PRIVATE_KEY,
        algorithm=ALGORITHM,
    )


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(
    user_data: dict[str, Any],
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
) -> str:
    payload = user_data.copy()
    payload.update({"type": ACCESS_TOKEN_TYPE})
    return encode_jwt(
        payload,
        expire_minutes=expire_minutes,
    )


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": REFRESH_TOKEN_TYPE,
    }
    expire_minutes = settings.auth_jwt.refresh_token_expire_days * 24 * 60
    return encode_jwt(
        payload,
        expire_minutes=expire_minutes,
    )


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def validate_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)