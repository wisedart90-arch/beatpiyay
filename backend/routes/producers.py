"""BeatPiyay — Routes producers"""
from fastapi import APIRouter, HTTPException, Request, Query
router = APIRouter()

@router.get("")
async def list_producers(request: Request, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    db = request.app.state.db
    producers = await db.users.find(
        {"role": "producer"}, {"password_hash": 0}
    ).skip((page-1)*limit).limit(limit).to_list(limit)
    for p in producers:
        p["id"] = str(p.pop("_id"))
    return {"data": producers}

@router.get("/{producer_id}")
async def get_producer(producer_id: str, request: Request):
    db = request.app.state.db
    user = await db.users.find_one({"_id": producer_id, "role": "producer"}, {"password_hash": 0})
    if not user:
        raise HTTPException(404, "Producteur introuvable")
    user["id"] = str(user.pop("_id"))
    beats_count = await db.beats.count_documents({"producer_id": producer_id})
    user["beats_count"] = beats_count
    return user
