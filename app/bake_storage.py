from supabase import create_client
import os

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

def save_bake(bake: Bake, user_id: str) -> None:
    """Save bake to Supabase, associating it with the user_id."""
    supabase.tables("bakes").upsert({
        "id": bake.id,
        "user_id": user_id,
        "data": bake_to_dict(bake)
    }).execute()

def load_bake(bake_id: str, user_id: str) -> dict:
    result = supabase.table("bakes")\
        .select("data")\
        .eq("id", bake_id)
        .eq("user_id", user_id)\
        .single()\
        .execute()
    return result.data["data"]