"""Groq LLM Provider"""

import json
import logging
from typing import Optional

from groq import AsyncGroq

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq API LLM provider using llama models"""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 500,
    ):
        if not api_key:
            raise ValueError("Groq API key is required")

        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[dict] = None,
    ) -> str:
        """Generate response using Groq API"""

        # Build context string
        context_str = ""
        if context:
            if context.get("tracked_units"):
                units = context["tracked_units"]
                if units:
                    context_str += "\n\nCurrently tracked units:\n"
                    for unit in units:
                        context_str += f"- {unit['callsign']}: {unit['lat']:.6f}, {unit['lon']:.6f}\n"

            if context.get("agent_position"):
                pos = context["agent_position"]
                context_str += f"\nYour position: {pos['lat']:.6f}, {pos['lon']:.6f}\n"

        # Append action instructions
        action_instructions = """

When you want to place a waypoint on the map, include it in your response using this format:
[WAYPOINT: name, latitude, longitude]

When you want to create a route, use this format:
[ROUTE: route_name | waypoint1_name,lat,lon | waypoint2_name,lat,lon | ...]

Example waypoint: [WAYPOINT: Rally Point Alpha, 32.7767, -96.7970]
Example route: [ROUTE: MSR Tampa | SP,32.7800,-96.8000 | CP1,32.7850,-96.7900 | OBJ,32.7900,-96.7800]

Only include these markers when the user specifically asks you to create waypoints or routes.
Coordinates should be in decimal degrees format."""

        full_system = system_prompt + context_str + action_instructions

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result = response.choices[0].message.content
            logger.debug(f"LLM response: {result}")
            return result

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
