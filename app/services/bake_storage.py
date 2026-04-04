from supabase import create_client
from app.utils.bake_utils import Bake, bake_to_dict
import os

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

def save_bake(bake: Bake, user_id: str) -> None:
    supabase.table("bakes").upsert({
        "id": bake.id,
        "user_id": user_id,
        "data": bake_to_dict(bake),
        "updated_at": "now()"
    }).execute()

def load_bake(bake_id: str, user_id: str) -> dict | None:
    result = supabase.table("bakes")\
        .select("data")\
        .eq("id", bake_id)\
        .eq("user_id", user_id)\
        .maybe_single()\
        .execute()
    return result.data["data"] if result.data else None

def list_bakes(user_id: str) -> list[dict]:
    result = supabase.table("bakes")\
        .select("id, created_at, data->recipe_label")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    return result.data