import anthropic
import json
from app.utils.bake_utils import Bake
from app.services.bake_storage import bake_to_dict
from fastapi import APIRouter

from app.core.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic()

router = APIRouter()

def get_bake_advice(bake: Bake) -> str:
    bake_dict = bake_to_dict(bake)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="""You are an expert sourdough baker and coach. 
You will be given a structured log of a sourdough bake in JSON format.
Analyse the ingredients, timings, hydration, fold schedule, proof durations, and outcome scores.
Give specific, actionable feedback — what went well, what to adjust next time.""",
        messages=[
            {
                "role": "user",
                "content": f"Here is my bake log:\n\n{json.dumps(bake_dict, indent=2, default=str)}"
            }
        ]
    )
    return message.content[0].text


@router.get("/bakes/{bake_id}/advice")
def get_advice(bake_id: str):
    bake = load_bake(bake_id)
    advice = get_bake_advice(bake)
    return {"bake_id": bake_id, "advice": advice}