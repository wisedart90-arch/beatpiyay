"""
BeatPiyay — Backend FastAPI
Sécurisé, structuré, prêt pour la production
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from routes import auth, beats, licenses, producers, payments

# ── Config ──────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    mongo_url: str
    db_name: str = "beatpiyay"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    app_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if settings.app_env == "production" else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("beatpiyay")

# ── DB client (partagé via app.state) ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connexion MongoDB...")
    app.state.mongo_client = AsyncIOMotorClient(settings.mongo_url)
    app.state.db = app.state.mongo_client[settings.db_name]
    # Index uniques essentiels
    await app.state.db.users.create_index("email", unique=True)
    await app.state.db.users.create_index("username", unique=True)
    await app.state.db.beats.create_index([("genre", 1), ("created_at", -1)])
    await app.state.db.beats.create_index("producer_id")
    logger.info("MongoDB connecté ✓")
    yield
    app.state.mongo_client.close()
    logger.info("MongoDB déconnecté.")

# ── App ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BeatPiyay API",
    version="1.0.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ── CORS (correctement configuré AVANT les routes) ───────────────────────
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Jamais "*" avec credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ── Routes ───────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth",      tags=["Auth"])
app.include_router(beats.router,     prefix="/api/beats",     tags=["Beats"])
app.include_router(licenses.router,  prefix="/api/licenses",  tags=["Licenses"])
app.include_router(producers.router, prefix="/api/producers", tags=["Producers"])
app.include_router(payments.router,  prefix="/api/payments",  tags=["Payments"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.app_env}
