"""
bake_storage.py — Persistence layer for bake history.

Reads and writes bake_history.json.

NOTE: Only used with log_bake.py script.
"""

import json
import os
from dataclasses import asdict
from typing import Optional

from bake_utils import Bake


BAKE_HISTORY_FILE = "bake_history.json"


# ------------------------------------------------
# SERIALISATION

def bake_to_dict(bake: Bake) -> dict:
    """Convert a Bake dataclass to a JSON-serialisable dict, including computed properties."""
    data = asdict(bake)
    # Include computed properties
    data['total_flour'] = bake.total_flour
    data['hydration'] = bake.hydration
    data['inoculation'] = bake.inoculation
    data['salt_percentage'] = bake.salt_percentage
    return data


def bake_from_dict(data: dict) -> dict:
    """
    Return raw dict for now — full deserialisation to Bake dataclass
    is added in Phase 2 when Pydantic validation is introduced.
    """
    return data


# ------------------------------------------------
# FILE I/O

def load_bake_history() -> list[dict]:
    """Load all bakes from local JSON store. Returns empty list if file absent."""
    if not os.path.exists(BAKE_HISTORY_FILE):
        return []
    with open(BAKE_HISTORY_FILE, "r") as f:
        return json.load(f)


def save_bake_history(history: list[dict]) -> None:
    """Write the full bake history list to disk."""
    with open(BAKE_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2, default=str)


# ------------------------------------------------
# CRUD OPERATIONS

def save_bake(bake: Bake) -> None:
    """
    Append or update a bake in history.
    Matches on bake.id — updates in place if found, appends if new.
    """
    history = load_bake_history()
    bake_dict = bake_to_dict(bake)

    for i, existing in enumerate(history):
        if existing.get("id") == bake.id:
            history[i] = bake_dict
            save_bake_history(history)
            return

    history.append(bake_dict)
    save_bake_history(history)


def load_bake(bake_id: str) -> Optional[dict]:
    """Load a single bake by ID. Returns None if not found."""
    history = load_bake_history()
    return next((b for b in history if b.get("id") == bake_id), None)


def delete_bake(bake_id: str) -> bool:
    """
    Delete a bake by ID.
    Returns True if deleted, False if not found.
    """
    history = load_bake_history()
    updated = [b for b in history if b.get("id") != bake_id]
    if len(updated) == len(history):
        return False
    save_bake_history(updated)
    return True


def list_bake_ids() -> list[str]:
    """Return all bake IDs in history, most recent first."""
    history = load_bake_history()
    return [b["id"] for b in reversed(history) if "id" in b]