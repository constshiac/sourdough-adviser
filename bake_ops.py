"""
bake_ops.py — State mutation for Bake objects.

All functions accept a Bake and return the mutated Bake.
No file I/O here — this layer maps cleanly to FastAPI route logic in Phase 2.
"""

from typing import Optional, Literal
from dataclasses import asdict

from bake_utils import (
    Bake, Stage, BakeStage, Fold, Proof, Ingredient, BakeOutcome,
    group_ingredients_by_stage,
    get_timestamp, time_since
)

ROOM_TEMPERATURE = 22.0  # Default room temperature in °C if not specified in Bake
FRIDGE_TEMPERATURE = 4.0   # Default fridge temperature in °C for cold proofs

# ------------------------------------------------
# STAGE LOOKUPS

def get_stage(bake: Bake, stage_name: str) -> Optional[Stage]:
    """Return the first stage matching stage_name, or None."""
    return next((s for s in bake.stages if s.name == stage_name), None)


def get_current_stage(bake: Bake) -> Optional[Stage]:
    """Return the most recently started stage."""
    if not bake.stages:
        return None
    return max(bake.stages, key=lambda s: s.start_time)


def _require_stage(bake: Bake, stage_name: str) -> Stage:
    """Return stage or raise clearly."""
    stage = get_stage(bake, stage_name)
    if stage is None:
        raise ValueError(f"Stage '{stage_name}' not found. Have you called the right preceding step?")
    return stage


# ------------------------------------------------
# INGREDIENTS

def add_ingredients(bake: Bake, ingredients: list[Ingredient]) -> Bake:
    """
    Calculate baker's percentages, group ingredients into mixing stages,
    and attach everything to the bake.
    """
    bake.ingredients = ingredients
    bake.calculate_ingredient_percentages()
    bake.stages = group_ingredients_by_stage(ingredients)
    return bake


# ------------------------------------------------
# FOLDS

def add_fold(
    bake: Bake,
    fold_type: Literal["stretch-and-fold", "coil fold", "knead"],
    fold_time: Optional[str] = None,
    stage_name: str = "bulk fermentation"
) -> Bake:
    """
    Add a fold to the given stage.
    Previous timestamp is taken from: last fold > last ingredient > stage start.
    """
    stage = _require_stage(bake, stage_name)

    if stage.folds:
        previous_timestamp = stage.folds[-1].timestamp
    elif stage.ingredients:
        previous_timestamp = max(i.timestamp for i in stage.ingredients)
    else:
        previous_timestamp = stage.start_time

    fold = Fold(
        type=fold_type,
        timestamp=fold_time or get_timestamp(),
        previous_timestamp=previous_timestamp
    )
    stage.folds.append(fold)
    return bake


# ------------------------------------------------
# PROOFS

def add_proof(
    bake: Bake,
    proof_type: Literal["cold", "warm"],
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    temperature: Optional[float] = None
) -> Bake:
    """
    Add a proof to the 'final proof' stage.

    - The first proof always starts at the stage's own start_time.
    - Adding a subsequent proof automatically closes the previous open proof.
    - An explicit start_time on a subsequent proof is used as the close time
      for the previous proof.
    """
    stage = _require_stage(bake, "final proof")

    if not stage.proofs:
        # First proof anchors to stage start
        proof_start = stage.start_time
    else:
        prev = stage.proofs[-1]
        if prev.end_time is None:
            # Close the previous proof at the start of this one
            close_at = get_timestamp(override=start_time)
            if close_at < prev.start_time:
                raise ValueError("New proof start_time cannot be before the previous proof's start_time")
            prev.close(close_at)
        proof_start = get_timestamp(override=start_time)

    # Assume temperature
    if not temperature:
        if proof_type == "cold":
            temperature = FRIDGE_TEMPERATURE
        elif proof_type == "warm":
            temperature = bake.room_temperature or ROOM_TEMPERATURE

    proof = Proof(
        type=proof_type,
        start_time=proof_start,
        end_time=end_time,
        temperature=temperature
    )
    stage.proofs.append(proof)
    return bake


def close_proof(
    bake: Bake,
    end_time: Optional[str] = None
) -> Bake:
    """
    Close the currently open proof on the 'final proof' stage.
    Use this when ending the final proof before moving to the oven.
    """
    stage = _require_stage(bake, "final proof")
    if not stage.proofs:
        raise ValueError("No proofs found to close")
    last = stage.proofs[-1]
    if last.end_time is not None:
        raise ValueError("The most recent proof is already closed")
    last.close(end_time)
    return bake


# ------------------------------------------------
# HANDLING STAGES

def add_handling_stage(
    bake: Bake,
    stage_name: Literal["pre-shape", "final shape"],
    start_time: Optional[str] = None,
    notes: Optional[str] = None
) -> Bake:
    """
    Add a handling stage (pre-shape or final shape) and manage the
    lifecycle of adjacent stages automatically.

    pre-shape:
        - Closes bulk fermentation
        - Creates pre-shape stage
        - Opens bench rest

    final shape:
        - Closes bench rest (if present) or bulk fermentation
        - Creates final shape stage
        - Opens final proof
    """
    timestamp = get_timestamp(override=start_time)

    if stage_name == "pre-shape":
        bulk = get_stage(bake, "bulk fermentation")
        if bulk:
            bulk.close(timestamp)
        bake.stages.append(Stage(name="pre-shape", start_time=timestamp, notes=notes))
        bake.stages.append(Stage(name="bench rest", start_time=timestamp))

    elif stage_name == "final shape":
        # Close bench rest if it exists, otherwise close bulk fermentation
        bench = get_stage(bake, "bench rest")
        if bench:
            bench.close(timestamp)
        else:
            bulk = get_stage(bake, "bulk fermentation")
            if bulk and not bulk.end_time:
                bulk.close(timestamp)
        bake.stages.append(Stage(name="final shape", start_time=timestamp, notes=notes))
        bake.stages.append(Stage(name="final proof", start_time=timestamp))

    return bake


# ------------------------------------------------
# OVEN / BAKE STAGE

def add_bake_stage(
    bake: Bake,
    bake_stage: BakeStage
) -> Bake:
    """
    Attach a BakeStage (oven phase) to the bake.
    Also closes any open final proof at the bake stage's start_time.
    """
    # Close final proof if still open
    proof_stage = get_stage(bake, "final proof")
    if proof_stage:
        if proof_stage.end_time is None:
            proof_stage.close(bake_stage.start_time)
        if proof_stage.proofs and (proof_stage.proofs[-1].end_time is None or proof_stage.proofs[-1].end_time != bake_stage.start_time):
            proof_stage.proofs[-1].close(bake_stage.start_time)

    bake.bake_stage = bake_stage
    return bake


# ------------------------------------------------
# OUTCOME

def set_outcome(
    bake: Bake,
    oven_spring: int = 0,
    crumb: int = 0,
    crust: int = 0,
    flavour: int = 0,
    overall: int = 0,
    notes: Optional[str] = None
) -> Bake:
    """Record the scored outcome for a completed bake."""
    bake.outcome = BakeOutcome(
        oven_spring=oven_spring,
        crumb=crumb,
        crust=crust,
        flavour=flavour,
        overall=overall,
        notes=notes
    )
    bake.end_time = get_timestamp()
    return bake