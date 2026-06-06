"""
BeatPiyay — Routes beats
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from middleware.auth import get_current_user, require_producer
from datetime import datetime, timezone
import uuid

router = APIRouter()

GENRES = {"trap","afrobeats","drill","rb","pop","dancehall","reggaeton","gospel","hip-hop","electronic"}

class BeatIn(BaseModel):
    title: str       = Field(..., min_length=2, max_length=80)
    genre: str       = Field(..., min_length=2, max_length=30)
    bpm: int         = Field(..., ge=40, le=300)
    key: str         = Field(..., max_length=10)
    price_basic: float    = Field(..., ge=0, le=10000)
    price_premium: float  = Field(..., ge=0, le=10000)
    price_exclusive: float= Field(..., ge=0, le=100000)
    tags: list[str]  = Field(default_factory=list, max_length=10)
    description: str = Field("", max_length=500)


@router.get("")
async def list_beats(
    request: Request,
    genre: str | None = None,
    bpm_min: int = Query(40, ge=40),
    bpm_max: int = Query(300, le=300),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", pattern="^(created_at|plays|price_basic)$"),
):
    db = request.app.state.db
    query: dict = {"available": True}
    if genre:
        query["genre"] = genre.lower()
    query["bpm"] = {"$gte": bpm_min, "$lte": bpm_max}

    skip = (page - 1) * limit
    cursor = db.beats.find(query, {"_id": 0}).sort(sort, -1).skip(skip).limit(limit)
    beats = await cursor.to_list(limit)
    total = await db.beats.count_documents(query)
    return {"data": beats, "total": total, "page": page, "pages": -(-total // limit)}


@router.get("/{beat_id}")
async def get_beat(beat_id: str, request: Request):
    db = request.app.state.db
    beat = await db.beats.find_one({"_id": beat_id}, {"_id": 0})
    if not beat:
        raise HTTPException(status_code=404, detail="Beat introuvable")
    await db.beats.update_one({"_id": beat_id}, {"$inc": {"plays": 1}})
    return beat


@router.post("", status_code=201)
async def create_beat(
    body: BeatIn,
    request: Request,
    current_user: dict = Depends(require_producer),
):
    db = request.app.state.db
    if body.genre.lower() not in GENRES:
        raise HTTPException(status_code=422, detail=f"Genre invalide. Options: {sorted(GENRES)}")

    beat_id = str(uuid.uuid4())
    doc = {
        "_id": beat_id,
        **body.model_dump(),
        "genre": body.genre.lower(),
        "producer_id": current_user["user_id"],
        "plays": 0,
        "favorites": 0,
        "available": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "audio_url": None,
        "cover_url": None,
    }
    await db.beats.insert_one(doc)
    doc.pop("_id")
    doc["id"] = beat_id
    return doc


@router.delete("/{beat_id}", status_code=204)
async def delete_beat(
    beat_id: str,
    request: Request,
    current_user: dict = Depends(require_producer),
):
    db = request.app.state.db
    beat = await db.beats.find_one({"_id": beat_id})
    if not beat:
        raise HTTPException(status_code=404, detail="Beat introuvable")
    if beat["producer_id"] != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Pas ton beat")
    await db.beats.delete_one({"_id": beat_id})
