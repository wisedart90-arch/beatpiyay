"""BeatPiyay — Payments (stub Stripe prêt à brancher)"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/config")
async def payments_config():
    return {"message": "Ajoute ta clé Stripe dans .env et intègre stripe.checkout.Session.create() ici"}
