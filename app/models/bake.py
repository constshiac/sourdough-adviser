"""
app/models/bake.py — Pydantic models for API request/response validation.
 
These are the shapes of data that come IN to and go OUT of the API.
They are separate from the internal dataclasses in bake_utils.py.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.utils.bake_utils import OUTCOME_MIN, OUTCOME_MAX, TEMP_MIN, TEMP_MAX


# ------------------------------------------------
# REQUEST MODELS (what the API receives)
 

class CreateBakeRequest(BaseModel):
    recipe_label: Optional[str] = None
    room_temperature: Optional[float] = Field(None, ge=TEMP_MIN, le=TEMP_MAX)

class IngredientRequest(BaseModel):
    name: str
    type: Literal["flour", "liquid", "starter", "salt", "other"]
    grams: float
    timestamp: Optional[str] = None


class AddIngredientsRequest(BaseModel):
    ingredients: list[IngredientRequest]


class AddFoldRequest(BaseModel):
    fold_type: Literal["stretch-and-fold", "coil fold", "knead"]
    fold_time: Optional[str] = None
    stage_name: str = "bulk fermentation"


class AddHandlingStageRequest(BaseModel):
    stage_name: Literal["pre-shape", "final shape"]
    start_time: Optional[str] = None
    notes: Optional[str] = None
 
 
class AddProofRequest(BaseModel):
    proof_type: Literal["cold", "warm"]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=TEMP_MIN, le=TEMP_MAX)
 
 
class CloseProofRequest(BaseModel):
    end_time: Optional[str] = None
 
 
class BakeStageRequest(BaseModel):
    name: str
    type: Optional[Literal["open bake", "dutch oven"]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    score_time: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    preheat_time: Optional[str] = None
    preheat_duration: Optional[str] = None
    preheat_temperature: Optional[float] = Field(None, ge=TEMP_MIN, le=TEMP_MAX)
    steam_time: Optional[str] = None
    steam_duration: Optional[str] = None
    steam_temperature: Optional[str] = Field(None, ge=TEMP_MIN, le=TEMP_MAX)
    open_time: Optional[str] = None
    open_duration: Optional[str] = None
    open_temperature: Optional[float] = Field(None, ge=TEMP_MIN, le=TEMP_MAX)
 

class SetOutcomeRequest(BaseModel):
    oven_spring: Optional[float] = Field(None, ge=OUTCOME_MIN, le=OUTCOME_MAX)
    crumb: Optional[float] = Field(None, ge=OUTCOME_MIN, le=OUTCOME_MAX)
    crust: Optional[float] = Field(None, ge=OUTCOME_MIN, le=OUTCOME_MAX)
    flavour: Optional[float] = Field(None, ge=OUTCOME_MIN, le=OUTCOME_MAX)
    overall: Optional[float] = Field(None, ge=OUTCOME_MIN, le=OUTCOME_MAX)
    notes: Optional[str] = None
 
 
# ------------------------------------------------
# RESPONSE MODELS (what the API returns)
 
class BakeListItem(BaseModel):
    id: str
    recipe_label: Optional[str]
    created_at: Optional[str] = None
 
 
class AdviceResponse(BaseModel):
    bake_id: str
    advice: str
 