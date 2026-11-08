from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def hash_password(value):
    return password_hash.hash(value)


def verify_password(value, hashed):
    return password_hash.verify(value, hashed)


def create_token(username):
    return jwt.encode(
        {"sub": username, "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)},
        settings.jwt_secret,
        algorithm="HS256",
    )


async def current_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Требуется авторизация")
    try:
        data = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = data.get("sub")
    except JWTError:
        user = None
    if user != settings.admin_username:
        raise HTTPException(401, "Недействительный токен")
    return user
