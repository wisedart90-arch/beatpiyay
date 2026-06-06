"""
BeatPiyay — Routes authentification
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
import uuid, os

router = APIRouter()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET  = os.environ["JWT_SECRET_KEY"]
ALGO    = os.environ.get("JWT_ALGORITHM", "HS256")
EXP_MIN = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", 60))
EXP_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRE_DAYS", 30))


# ── Schemas ──────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("user", pattern="^(user|producer)$")

class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ── Helpers ──────────────────────────────────────────────────────────────
def make_token(user_id: str, role: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


# ── Endpoints ────────────────────────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, request: Request):
    db = request.app.state.db
    existing = await db.users.find_one({"email": body.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user_id = str(uuid.uuid4())
    await db.users.insert_one({
        "_id": user_id,
        "username": body.username,
        "email": body.email,
        "password_hash": pwd_ctx.hash(body.password),
        "role": body.role,
        "avatar_url": None,
        "bio": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verified": False,
    })

    access  = make_token(user_id, body.role, timedelta(minutes=EXP_MIN))
    refresh = make_token(user_id, body.role, timedelta(days=EXP_DAYS))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/login")
async def login(body: LoginIn, request: Request):
    db = request.app.state.db
    user = await db.users.find_one({"email": body.email})
    if not user or not pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    access  = make_token(user["_id"], user["role"], timedelta(minutes=EXP_MIN))
    refresh = make_token(user["_id"], user["role"], timedelta(days=EXP_DAYS))
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "id": user["_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        }
    }


@router.get("/me")
async def me(request: Request):
    from middleware.auth import verify_token
    return {"message": "Utilise le middleware verify_token comme dépendance"}
