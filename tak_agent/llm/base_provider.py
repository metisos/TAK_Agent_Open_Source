"""Base LLM Provider interface"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: System/role instructions
            user_message: User's message
            context: Optional context dictionary (tracked units, etc.)

        Returns:
            Generated response text
        """
        pass
