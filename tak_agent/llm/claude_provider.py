"""Claude/Anthropic LLM Provider"""

import logging
from typing import Optional

import anthropic

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        if not api_key:
            raise ValueError("Anthropic API key is required")

        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[dict] = None,
    ) -> str:
        """Generate response using Claude API"""

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

        # Append TAK action instructions
        action_instructions = """

TAK MAP ACTIONS:
You can create and delete map objects by including special markers in your response.

MARKER (tactical icon - USE THIS FOR ALL POINTS):
[MARKER: name, latitude, longitude, type, remarks]
Types: friendly (blue icon), hostile (red icon), neutral (green icon), unknown (yellow icon)
Examples:
[MARKER: HQ Alpha, 32.7800, -96.7950, friendly, Command post]
[MARKER: Enemy OP, 32.7850, -96.7900, hostile, Observation post]
[MARKER: Gas Station, 32.7900, -96.7800, neutral, Resupply point]

ROUTE (connected line with checkpoints):
[ROUTE: route_name | cp1_name,lat,lon | cp2_name,lat,lon | cp3_name,lat,lon]
Example: [ROUTE: MSR Tampa | SP,32.7800,-96.8000 | CP1,32.7850,-96.7900 | OBJ,32.7900,-96.7800]
Routes display as connected lines on the map with labeled checkpoints.

DELETE ALL (remove all items created by this agent):
[DELETE_ALL]
Use this when the user asks to clear, remove, or delete all markers/points/routes you created.

IMPORTANT:
- ALWAYS use MARKER for placing single points - it shows proper tactical icons
- Use ROUTE only when creating connected paths between multiple locations
- Use DELETE_ALL when user wants to clear/remove/delete markers or data
- Use real coordinates based on the location context or user request
- Coordinates must be in decimal degrees format (e.g., 32.7767, -96.7970)
- Choose appropriate marker type: friendly for allied assets, hostile for threats, neutral for infrastructure/landmarks"""

        full_system = system_prompt + context_str + action_instructions

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=full_system,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )

            result = response.content[0].text
            logger.debug(f"Claude response: {result}")
            return result

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
