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

from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, _DEV_USER_ID
from app.utils.bake_utils import Bake

LOCAL_FILE = "bake_history.json"
_USE_LOCAL = not (SUPABASE_URL and SUPABASE_SERVICE_KEY)


# ------------------------------------------------
# SERIALISATION

def bake_to_dict(bake: Bake) -> dict:
    """Convert a Bake dataclass to a JSON-serialisable dict, including properties."""
    bake_dict = asdict(bake)
    # Add calculated properties
    bake_dict['total_flour'] = bake.total_flour
    bake_dict['hydration'] = bake.hydration
    bake_dict['inoculation'] = bake.inoculation
    bake_dict['salt_percentage'] = bake.salt_percentage
    return bake_dict


# ------------------------------------------------
# SUPABASE CLIENT — lazy so missing env vars don't crash on import

def _get_supabase():
    from supabase import create_client
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

def save_bake(bake: Bake, user_id: str = _DEV_USER_ID) -> None:
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


def load_bake(bake_id: str, user_id: str = _DEV_USER_ID) -> Optional[dict]:
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


def _get_bake_status(row: dict) -> str:
    import json
    from datetime import datetime

    stages = row.get("stages")
    if isinstance(stages, str):
        stages = json.loads(stages)
    
    def _get_stage_by_name(stages: list[dict], stage_name: str) -> dict:
        return next((s for s in stages if s.get('name') == stage_name), None)

    if not stages:
        return "not started"

    bake_stage = row.get("bake_stage")
    if isinstance(bake_stage, str):
        bake_stage = json.loads(bake_stage)
    if bake_stage:
        bake_end = bake_stage.get('end_time')
        bake_completed = bake_end is not None and datetime.fromisoformat(bake_end) < datetime.now()
        if bake_completed:
            return "completed"
        else:
            return "baking"
        
    final_proof = _get_stage_by_name(stages, "final proof")
    if final_proof:
        if final_proof.get('proofs'):
            proofs = final_proof.get('proofs',[])
            if proofs:
                proof_type = proofs[-1].get('type')
        else:
            proof_type = "proof"
        
        if proof_type:
            return proof_type + " proofing"

    bulk_fermentation = _get_stage_by_name(stages, "bulk fermentation")
    if bulk_fermentation:
        return "bulk fermentation"

    return stages[-1].get('name')


def _summarise_bake(row: dict) -> dict:
    row['status'] = _get_bake_status(row)
    del row['stages']
    del row['bake_stage']
    return row


def list_bakes(user_id: str = _DEV_USER_ID) -> list[dict]:
    """Return all bakes, most recent first."""
    if _USE_LOCAL:
        return list(reversed(_load_local()))
    else:
        result = _get_supabase().table("bakes") \
            .select("id, created_at, data->>recipe_label, data->>hydration, data->>total_flour, data->>inoculation, data->>salt_percentage, data->'outcome'->>'overall', data->>stages, data->>bake_stage") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        return [_summarise_bake(row) for row in result.data]


def delete_bake(bake_id: str, user_id: str = _DEV_USER_ID) -> bool:
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