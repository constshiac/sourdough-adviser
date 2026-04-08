"""
app/routes/bakes.py — All bake CRUD and logging endpoints.
 
Each route loads the bake, calls a service function, saves, and returns the result.
Auth uses Supabase JWT verification via get_current_user().
Falls back to _DEV_USER_ID locally when no token is present.
"""
 
from fastapi import APIRouter, HTTPException, Request
from dataclasses import asdict
 
from app.utils.auth import get_current_user
from app.utils.bake_utils import Bake, BakeStage, Ingredient
from app.services.bake_ops import (
    add_ingredients, add_fold, add_handling_stage,
    add_proof, close_proof, add_bake_stage, set_outcome
)
from app.services.bake_storage import save_bake, load_bake, list_bakes, delete_bake
from app.models.bake import (
    CreateBakeRequest, AddIngredientsRequest, AddFoldRequest,
    AddHandlingStageRequest, AddProofRequest, CloseProofRequest,
    BakeStageRequest, SetOutcomeRequest
) 
router = APIRouter()



def _load_or_404(bake_id: str, user_id: str) -> dict:
    """Load a bake dict or raise 404."""
    data = load_bake(bake_id, user_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Bake '{bake_id}' not found")
    return data
 
 
def _dict_to_bake(data: dict) -> Bake:
    """
    Reconstruct a Bake dataclass from a stored dict.
    Full Pydantic deserialisation comes in Phase 2 — for now we pass
    the raw dict fields into the constructor directly.
    """
    from app.utils.bake_utils import (
        Ingredient, Stage, Fold, Proof, BakeStage, BakeOutcome, Starter, Feeding
    )
    import dacite
    return dacite.from_dict(data_class=Bake, data=data)


# ------------------------------------------------
# BAKE LIFECYCLE
 
@router.post("", summary="Start a new bake")
def create_bake(body: CreateBakeRequest, request: Request):
    user_id = get_current_user(request)
    bake = Bake(recipe_label=body.recipe_label, room_temperature=body.room_temperature)
    save_bake(bake, user_id)
    return asdict(bake)
 
 
@router.get("", summary="List all bakes")
def get_bakes(request: Request):
    user_id = get_current_user(request)
    return list_bakes(user_id)
 
 
@router.get("/{bake_id}", summary="Get a single bake")
def get_bake(bake_id: str, request: Request):
    user_id = get_current_user(request)
    return _load_or_404(bake_id, user_id)
 
 
@router.delete("/{bake_id}", summary="Delete a bake")
def remove_bake(bake_id: str, request: Request):
    user_id = get_current_user(request)
    deleted = delete_bake(bake_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Bake '{bake_id}' not found")
    return {"deleted": bake_id}


# ------------------------------------------------
# INGREDIENTS
 
@router.post("/{bake_id}/ingredients", summary="Add ingredients to a bake")
def log_ingredients(bake_id: str, body: AddIngredientsRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
 
    ingredients = [
        Ingredient(
            name=i.name,
            type=i.type,
            grams=i.grams,
            **({"timestamp": i.timestamp} if i.timestamp else {})
        )
        for i in body.ingredients
    ]
 
    bake = add_ingredients(bake, ingredients)
    save_bake(bake, user_id)
    return asdict(bake)


# ------------------------------------------------
# FOLDS
 
@router.post("/{bake_id}/folds", summary="Log a fold")
def log_fold(bake_id: str, body: AddFoldRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
    bake = add_fold(bake, body.fold_type, body.fold_time, body.stage_name)
    save_bake(bake, user_id)
    return asdict(bake)


# ------------------------------------------------
# HANDLING STAGES
 
@router.post("/{bake_id}/stages", summary="Add a handling stage (pre-shape or final shape)")
def log_handling_stage(bake_id: str, body: AddHandlingStageRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
    bake = add_handling_stage(bake, body.stage_name, body.start_time, body.notes)
    save_bake(bake, user_id)
    return asdict(bake)
 
 
# ------------------------------------------------
# PROOFS
 
@router.post("/{bake_id}/proofs", summary="Add a proof")
def log_proof(bake_id: str, body: AddProofRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
    bake = add_proof(bake, body.proof_type, body.start_time, body.end_time, body.temperature)
    save_bake(bake, user_id)
    return asdict(bake)
 
 
@router.post("/{bake_id}/proofs/close", summary="Close the current open proof")
def log_close_proof(bake_id: str, body: CloseProofRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
    bake = close_proof(bake, body.end_time)
    save_bake(bake, user_id)
    return asdict(bake)
 
 
# ------------------------------------------------
# OVEN STAGE
 
@router.post("/{bake_id}/bake-stage", summary="Log the oven/bake stage")
def log_bake_stage(bake_id: str, body: BakeStageRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
 
    stage = BakeStage(
        name=body.name,
        type=body.type,
        start_time=body.start_time,
        end_time=body.end_time,
        score_time=body.score_time,
        duration=body.duration,
        notes=body.notes,
        preheat_time=body.preheat_time,
        preheat_duration=body.preheat_duration,
        preheat_temperature=body.preheat_temperature,
        steam_time=body.steam_time,
        steam_duration=body.steam_duration,
        steam_temperature=body.steam_temperature,
        open_time=body.open_time,
        open_duration=body.open_duration,
        open_temperature=body.open_temperature,
    )
 
    bake = add_bake_stage(bake, stage)
    save_bake(bake, user_id)
    return asdict(bake)
 
 
# ------------------------------------------------
# OUTCOME
 
@router.post("/{bake_id}/outcome", summary="Record bake outcome scores")
def log_outcome(bake_id: str, body: SetOutcomeRequest, request: Request):
    user_id = get_current_user(request)
    data = _load_or_404(bake_id, user_id)
    bake = _dict_to_bake(data)
    bake = set_outcome(
        bake,
        oven_spring=body.oven_spring,
        crumb=body.crumb,
        crust=body.crust,
        flavour=body.flavour,
        overall=body.overall,
        notes=body.notes
    )
    save_bake(bake, user_id)
    return asdict(bake)
 