"""
bake_adviser.py — Anthropic API calls.

Accepts a Bake object and returns natural language advice.
"""

import json
import anthropic

from app.core.config import ANTHROPIC_API_KEY
from app.utils.bake_utils import Bake
from app.services.bake_storage import bake_to_dict

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an expert sourdough baker and coach.
You will be given a structured log of a sourdough bake in JSON format.
Analyse the ingredients, timings, hydration, fold schedule, proof durations, and outcome scores.
Give specific, actionable feedback — what went well, what to adjust next time.
Be concise. Use bullet points. Lead with the most impactful observations."""


def get_bake_advice(bake: Bake) -> str:
    """Send a bake log to Claude and return advice as a string."""
    bake_dict = bake_to_dict(bake)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Here is my bake log:\n\n{json.dumps(bake_dict, indent=2, default=str)}"
            }
        ]
    )
    return message.content[0].text