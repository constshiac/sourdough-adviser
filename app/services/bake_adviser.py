import anthropic
import json
from dotenv import load_dotenv
from app.utils.bake_utils import Bake
from bake_storage import bake_to_dict

load_dotenv() # Pick up ANTHROPIC_API_KEY from .env
client = anthropic.Anthropic()

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