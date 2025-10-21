"""Service for generating complete shikona (ring names) with interpretations."""

from __future__ import annotations

import logging
import os
from typing import Final

from pydantic import BaseModel

from libs.generators.name import RikishiNameGenerator
from libs.singletons.openai import get_openai_singleton

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
        self.client = get_openai_singleton()

    def _call_openai(
        self,
        kanji_name: str,
        parent_shikona: str | None = None,
        shusshin: str | None = None,
    ) -> ShikonaInterpretation:
        """
        Call OpenAI API to get romanization and interpretation for a kanji name.

        Args:
            kanji_name: Kanji shikona to process.
            parent_shikona: Optional parent shikona to create a related name.
            shusshin: Optional origin/birthplace to incorporate themes.

        Returns:
            ShikonaInterpretation with romanization and interpretation.

        Raises:
            ShikonaGenerationError: If the API call fails.

        """
        # Format the user message based on context provided
        if parent_shikona or shusshin:
            parts = [f"GENERATED: {kanji_name}"]
            if parent_shikona:
                parts.append(f"PARENT: {parent_shikona}")
            if shusshin:
                parts.append(f"SHUSSHIN: {shusshin}")
            user_message = "\n".join(parts)
        else:
            user_message = kanji_name

        try:
            response = self.client.responses.parse(
                model="gpt-5-mini",
                reasoning={"effort": "low"},
                input=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_message},
                ],
                text_format=ShikonaInterpretation,
            )
            logger.info("OpenAI API Usage: %s", response.usage)
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

    def generate_single(
        self,
        parent_shikona: str | None = None,
        shusshin: str | None = None,
    ) -> ShikonaInterpretation:
        """
        Generate a single complete shikona with interpretation.

        Args:
            parent_shikona: Optional parent shikona to create a related name.
            shusshin: Optional origin/birthplace to incorporate themes.

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

        interpretation = self._call_openai(kanji_name, parent_shikona, shusshin)
        logger.debug(f"Received interpretation: {interpretation}")

        return interpretation

    def generate_batch(
        self,
        count: int,
        parent_shikona: str | None = None,
        shusshin: str | None = None,
    ) -> list[ShikonaInterpretation]:
        """
        Generate multiple complete shikona with interpretations.

        Args:
            count: Number of shikona to generate. Must be positive.
            parent_shikona: Optional parent shikona to create related names.
            shusshin: Optional origin/birthplace to incorporate themes.

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
            interpretation = self.generate_single(parent_shikona, shusshin)

            all_results.append(interpretation)

            logger.info(f"Processed {i + 1}/{count} shikona successfully")

        return all_results
