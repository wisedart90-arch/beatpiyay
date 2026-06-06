"""
BeatPiyay — Routes licences & paiements (stubs prêts à brancher Stripe)
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from middleware.auth import get_current_user
from datetime import datetime, timezone
import uuid, os

# ── Licenses ─────────────────────────────────────────────────────────────
router = APIRouter()

TIERS = {
    "basic":     {"price": 29,  "streams_max": 50_000,  "wav": False, "stems": False, "exclusive": False},
    "premium":   {"price": 79,  "streams_max": 500_000, "wav": True,  "stems": False, "exclusive": False},
    "exclusive": {"price": 299, "streams_max": None,    "wav": True,  "stems": True,  "exclusive": True},
}

class LicensePurchaseIn(BaseModel):
    beat_id: str
    tier: str = Field(..., pattern="^(basic|premium|exclusive)$")

# Stub — à connecter à Stripe Checkout
@router.post("/purchase")
async def purchase_license(
    body: LicensePurchaseIn,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    beat = await db.beats.find_one({"_id": body.beat_id})
    if not beat:
        raise HTTPException(status_code=404, detail="Beat introuvable")
    if not beat.get("available") and body.tier == "exclusive":
        raise HTTPException(status_code=409, detail="Ce beat n'est plus disponible en exclusivité")

    tier_info = TIERS[body.tier]
    license_id = str(uuid.uuid4())

    # Si exclusive → retirer le beat de la vente
    if body.tier == "exclusive":
        await db.beats.update_one({"_id": body.beat_id}, {"$set": {"available": False}})

    license_doc = {
        "_id": license_id,
        "buyer_id": current_user["user_id"],
        "beat_id": body.beat_id,
        "tier": body.tier,
        "price_paid": tier_info["price"],
        "rights": tier_info,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "download_url": None,  # généré après paiement confirmé
    }
    await db.licenses.insert_one(license_doc)

    return {
        "license_id": license_id,
        "tier": body.tier,
        "price": tier_info["price"],
        "message": "Licence créée — intègre Stripe pour finaliser le paiement",
        "stripe_checkout_url": "TODO: créer session Stripe ici",
    }


@router.get("/my")
async def my_licenses(request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    licenses = await db.licenses.find(
        {"buyer_id": current_user["user_id"]}, {"_id": 0}
    ).to_list(200)
    return {"data": licenses, "total": len(licenses)}
