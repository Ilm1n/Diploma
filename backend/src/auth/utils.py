from datetime import datetime, timezone, timedelta

import jwt
import uuid
from src.config import settings


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

def encode_jwt(
    payload: dict,
    private_key: str = settings.auth_jwt.private_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
):
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)

    expire = now + timedelta(minutes=expire_minutes)

    to_encode.update(exp=expire, iat=now, jti=str(uuid.uuid4()))
    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorithm,
    )
    return encoded


def decode_jwt(
    token: str,
    public_key: str = settings.auth_jwt.public_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
):
    try:
        decoded = jwt.decode(token, public_key, algorithms=[algorithm])
        return decoded
    except jwt.PyJWTError:
        return {}


def create_access_token(user_id: int, username: str, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "email": email,
        "type": ACCESS_TOKEN_TYPE
    }
    return encode_jwt(payload, expire_minutes=settings.auth_jwt.access_token_expire_minutes)

def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": REFRESH_TOKEN_TYPE
    }
    expire_minutes = settings.auth_jwt.refresh_token_expire_days * 24 * 60
    return encode_jwt(payload, expire_minutes=expire_minutes)