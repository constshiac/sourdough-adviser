from fastapi import APIRouter
from app.bake_ops import add_ingredients, add_fold
from app.bake_utils import Bake, Ingredient

router = APIRouter()

@router.post("/")
def create_bake(recipe_label: str = None):
    bake = Bake(recipe_label=recipe_label)
    save_bake(bake)
    return bake_to_dict(bake)

@router.post("/{bake_id}/folds")
def log_fold(bake_id: str, fold_type: str, fold_time: str = None):
    bake = load_bake(bake_id)
    bake = add_fold(bake, fold_type, fold_time)
    save_bake(bake)
    return bake_to_dict(bake)
    
