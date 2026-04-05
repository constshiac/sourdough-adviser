"""
app/routes/adviser.py — AI advice endpoint.
"""

from fastapi import APIRouter, HTTPException

from app.services.bake_storage import load_bake
from app.services.bake_adviser import get_bake_advice
from app.models.bake import AdviceResponse
from app.routes.bakes import _load_or_404, _dict_to_bake

router = APIRouter()

_DEV_USER_ID = "local"


@router.post("/{bake_id}", response_model=AdviceResponse, summary="Get AI advice for a bake")
def advise_bake(bake_id: str):
    data = _load_or_404(bake_id)
    bake = _dict_to_bake(data)
    advice = get_bake_advice(bake)
    return AdviceResponse(bake_id=bake_id, advice=advice)