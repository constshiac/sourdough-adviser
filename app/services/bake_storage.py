"""
bake_storage.py — Persistence layer.

Uses Supabase when credentials are present, otherwise falls back to a local
bake_history.json file. This means local dev works without any Supabase setup.
In Phase 3 the local fallback can be dropped.
"""

import json
import os
from dataclasses import asdict
from typing import Optional

from app.utils.bake_utils import Bake

LOCAL_FILE = "bake_history.json"
_USE_LOCAL = not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


# ------------------------------------------------
# SERIALISATION

def bake_to_dict(bake: Bake) -> dict:
    """Convert a Bake dataclass to a JSON-serialisable dict."""
    return asdict(bake)


# ------------------------------------------------
# SUPABASE CLIENT — lazy so missing env vars don't crash on import

def _get_supabase():
    from supabase import create_client
    from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ------------------------------------------------
# LOCAL FALLBACK

def _load_local() -> list[dict]:
    if not os.path.exists(LOCAL_FILE):
        return []
    with open(LOCAL_FILE, "r") as f:
        return json.load(f)


def _save_local(history: list[dict]) -> None:
    with open(LOCAL_FILE, "w") as f:
        json.dump(history, f, indent=2, default=str)


# ------------------------------------------------
# PUBLIC API

def save_bake(bake: Bake, user_id: str = "local") -> None:
    """Upsert a bake by ID."""
    bake_dict = bake_to_dict(bake)

    if _USE_LOCAL:
        history = _load_local()
        for i, existing in enumerate(history):
            if existing.get("id") == bake.id:
                history[i] = bake_dict
                _save_local(history)
                return
        history.append(bake_dict)
        _save_local(history)
    else:
        _get_supabase().table("bakes").upsert({
            "id": bake.id,
            "user_id": user_id,
            "data": bake_dict,
        }).execute()


def load_bake(bake_id: str, user_id: str = "local") -> Optional[dict]:
    """Load a single bake by ID. Returns None if not found."""
    if _USE_LOCAL:
        return next((b for b in _load_local() if b.get("id") == bake_id), None)
    else:
        result = _get_supabase().table("bakes") \
            .select("data") \
            .eq("id", bake_id) \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        return result.data["data"] if result.data else None


def list_bakes(user_id: str = "local") -> list[dict]:
    """Return all bakes, most recent first."""
    if _USE_LOCAL:
        return list(reversed(_load_local()))
    else:
        result = _get_supabase().table("bakes") \
            .select("id, created_at, data->>recipe_label") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        return result.data


def delete_bake(bake_id: str, user_id: str = "local") -> bool:
    """Delete a bake by ID. Returns True if deleted, False if not found."""
    if _USE_LOCAL:
        history = _load_local()
        updated = [b for b in history if b.get("id") != bake_id]
        if len(updated) == len(history):
            return False
        _save_local(updated)
        return True
    else:
        _get_supabase().table("bakes") \
            .delete() \
            .eq("id", bake_id) \
            .eq("user_id", user_id) \
            .execute()
        return True