"""Service for generating complete shikona (ring names) with interpretations."""

from __future__ import annotations

import logging
import os
from typing import Final

from pydantic import BaseModel

from libs.generators.name import RikishiNameGenerator
from libs.singletons.openai import openai_singleton

logger = logging.getLogger(__name__)

DIRNAME: Final[str] = os.path.dirname(__file__)


class ShikonaInterpretation(BaseModel):
    """Structured response for a single shikona interpretation from OpenAI."""

    shikona: str
    transliteration: str
    interpretation: str


class ShikonaGenerationError(Exception):
    """Raised when shikona generation fails."""


def _load_system_prompt() -> str:
    """Load the system prompt from the shikona_prompt.md file."""
    prompt_path = os.path.join(DIRNAME, "data", "shikona_prompt.md")
    with open(prompt_path, encoding="utf-8") as f:
        return f.read()


class ShikonaGenerator:
    """
    Generator for complete shikona with AI-enhanced romanization.

    Combines the RikishiNameGenerator for authentic kanji names with OpenAI
    for proper romanization and meaningful interpretations.
    """

    # Load system prompt once at class level
    _system_prompt: Final[str] = _load_system_prompt()

    def __init__(
        self,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the shikona generator.

        Args:
            seed: Optional seed for deterministic name generation.

        """
        self.name_generator = RikishiNameGenerator(seed=seed)
        self.client = openai_singleton

    def _call_openai(self, kanji_name: str) -> ShikonaInterpretation:
        """
        Call OpenAI API to get romanization and interpretation for a kanji name.

        Args:
            kanji_name: Kanji shikona to process.

        Returns:
            ShikonaInterpretation with romanization and interpretation.

        Raises:
            ShikonaGenerationError: If the API call fails.

        """
        try:
            response = self.client.responses.parse(
                model="gpt-5-nano",
                reasoning_effort="low",
                temperature=0,
                input=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": kanji_name},
                ],
                text_format=ShikonaInterpretation,
            )
            result: ShikonaInterpretation | None = response.output_parsed
            if result is None:
                raise ShikonaGenerationError(
                    "OpenAI response parsing returned None"
                )
            return result
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise ShikonaGenerationError(
                f"Failed to process shikona via OpenAI: {e}"
            ) from e

    def generate_single(self) -> ShikonaInterpretation:
        """
        Generate a single complete shikona with interpretation.

        Returns:
            ShikonaInterpretation object.

        Raises:
            ShikonaGenerationError: If generation fails.

        """
        kanji_name = self.name_generator.get()[0]
        logger.debug(
            f"Generated kanji name {kanji_name}, "
            "sending to OpenAI for processing"
        )

        interpretation = self._call_openai(kanji_name)
        logger.debug(f"Received interpretation: {interpretation}")

        return interpretation

    def generate_batch(self, count: int) -> list[ShikonaInterpretation]:
        """
        Generate multiple complete shikona with interpretations.

        Args:
            count: Number of shikona to generate. Must be positive.

        Returns:
            List of ShikonaInterpretation objects.

        Raises:
            ValueError: If count is not positive.
            ShikonaGenerationError: If generation fails.

        """
        if count <= 0:
            raise ValueError(f"count must be positive, got {count}")

        all_results: list[ShikonaInterpretation] = []
        for i in range(count):
            interpretation = self.generate_single()

            all_results.append(interpretation)

            logger.info(f"Processed {i + 1}/{count} shikona successfully")

        return all_results
