"""Service for generating complete shikona (ring names) with interpretations."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from libs.generators.name import RikishiNameGenerator

logger = logging.getLogger(__name__)

DIRNAME = os.path.dirname(__file__)


class ShikonaInterpretation(BaseModel):
    """Structured response for a single shikona from OpenAI."""

    shikona: str
    transliteration: str
    interpretation: str


class ShikonaBatchResponse(BaseModel):
    """Batch response containing multiple shikona interpretations."""

    rikishi: list[ShikonaInterpretation]


class ShikonaGenerationError(Exception):
    """Raised when shikona generation fails."""

    pass


class ShikonaGenerator:
    """
    Generator for complete shikona with AI-enhanced romanization.

    Combines the RikishiNameGenerator for authentic kanji names with OpenAI
    for proper romanization and meaningful interpretations.
    """

    def __init__(
        self,
        api_key: str | None = None,
        seed: int | None = None,
        model: str = "gpt-5-nano",
    ) -> None:
        """
        Initialize the shikona generator.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            seed: Optional seed for deterministic name generation.
            model: OpenAI model to use (default: gpt-5-nano).

        """
        load_dotenv()
        self.name_generator = RikishiNameGenerator(seed=seed)
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self._load_prompt()

    def _load_prompt(self) -> None:
        """Load the system prompt from the shikona_prompt.md file."""
        prompt_path = os.path.join(DIRNAME, "data", "shikona_prompt.md")
        with open(prompt_path, encoding="utf-8") as f:
            self.system_prompt = f.read()

    def _call_openai(self, kanji_names: list[str]) -> ShikonaBatchResponse:
        """
        Call OpenAI API to get romanization and interpretation for kanji names.

        Args:
            kanji_names: List of kanji shikona to process.

        Returns:
            ShikonaBatchResponse with processed shikona data.

        Raises:
            ShikonaGenerationError: If the API call fails.

        """
        user_prompt = json.dumps(kanji_names, ensure_ascii=False)

        try:
            response = self.client.responses.parse(
                model=self.model,
                reasoning={"effort": "low"},
                input=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=ShikonaBatchResponse,
            )
            result: ShikonaBatchResponse | None = response.output_parsed
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

    def generate_batch(
        self, count: int, batch_size: int = 10
    ) -> list[ShikonaInterpretation]:
        """
        Generate multiple complete shikona with interpretations.

        Args:
            count: Number of shikona to generate.
            batch_size: Number of names to process per API call (default: 10).

        Returns:
            List of ShikonaInterpretation objects.

        Raises:
            ShikonaGenerationError: If generation fails.

        """
        all_results: list[ShikonaInterpretation] = []
        remaining = count

        while remaining > 0:
            current_batch_size = min(batch_size, remaining)

            # Generate kanji names using the name generator
            kanji_names = [
                self.name_generator.get()[0] for _ in range(current_batch_size)
            ]

            logger.info(
                f"Generated {current_batch_size} kanji names, "
                f"sending to OpenAI for processing"
            )

            # Get interpretations from OpenAI
            batch_response = self._call_openai(kanji_names)

            # Validate response
            if len(batch_response.rikishi) != current_batch_size:
                logger.warning(
                    f"Expected {current_batch_size} results but got "
                    f"{len(batch_response.rikishi)}"
                )

            all_results.extend(batch_response.rikishi)
            remaining -= current_batch_size

            logger.info(
                f"Processed {len(all_results)}/{count} shikona successfully"
            )

        return all_results[:count]  # Ensure we return exactly count results

    def generate_single(self) -> ShikonaInterpretation:
        """
        Generate a single complete shikona with interpretation.

        Returns:
            ShikonaInterpretation object.

        Raises:
            ShikonaGenerationError: If generation fails.

        """
        results = self.generate_batch(count=1, batch_size=1)
        return results[0]

    def generate_dict(
        self, count: int, batch_size: int = 10
    ) -> list[dict[str, Any]]:
        """
        Generate shikona as dictionaries for database insertion.

        Args:
            count: Number of shikona to generate.
            batch_size: Number of names to process per API call (default: 10).

        Returns:
            List of dicts with keys: name, transliteration, interpretation.

        """
        results = self.generate_batch(count=count, batch_size=batch_size)
        return [
            {
                "name": r.shikona,
                "transliteration": r.transliteration,
                "interpretation": r.interpretation,
            }
            for r in results
        ]
