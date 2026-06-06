"""
BeatPiyay — Middleware d'authentification JWT
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timezone
import os

security = HTTPBearer()

SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM  = os.environ.get("JWT_ALGORITHM", "HS256")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expiré")
    return payload


def get_current_user(payload: dict = Depends(verify_token)) -> dict:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    return {"user_id": user_id, "role": payload.get("role", "user")}


def require_producer(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in ("producer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé aux producteurs")
    return current_user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès admin requis")
    return current_user
