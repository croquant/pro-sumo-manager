"""Service for generating Shikona (ring names) for heya selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from game.models import Shikona as ShikonaModel
from libs.generators.shikona import ShikonaGenerationError, ShikonaGenerator

logger = logging.getLogger(__name__)


@dataclass
class ShikonaOption:
    """A generated shikona option for display."""

    name: str  # Japanese kanji
    transliteration: str  # Romaji
    interpretation: str  # Meaning


class ShikonaService:
    """
    Service for generating and managing Shikona (ring names).

    This service provides business logic for creating unique shikona
    options for stable name selection during onboarding.
    """

    @staticmethod
    def generate_shikona_options(count: int = 3) -> list[ShikonaOption]:
        """
        Generate unique shikona options for heya name selection.

        Uses the existing ShikonaGenerator which leverages OpenAI for
        authentic romanization and meaningful interpretations.

        Args:
        ----
            count: Number of unique options to generate (default: 3).

        Returns:
        -------
            List of ShikonaOption instances with unique names.
            May return fewer than requested if generation fails.

        """
        options: list[ShikonaOption] = []

        # Get existing shikona names to avoid duplicates
        existing_names = set(
            ShikonaModel.objects.values_list("name", flat=True)
        )
        existing_translit = set(
            ShikonaModel.objects.values_list("transliteration", flat=True)
        )

        generator = ShikonaGenerator()
        max_attempts = count * 3  # Allow some retries for duplicates

        for _ in range(max_attempts):
            if len(options) >= count:
                break

            try:
                shikona = generator.generate_single()

                # Check uniqueness
                if (
                    shikona.shikona not in existing_names
                    and shikona.transliteration not in existing_translit
                    and shikona.shikona not in {opt.name for opt in options}
                ):
                    options.append(
                        ShikonaOption(
                            name=shikona.shikona,
                            transliteration=shikona.transliteration,
                            interpretation=shikona.interpretation,
                        )
                    )
                    logger.info(
                        "Generated shikona option: %s (%s)",
                        shikona.shikona,
                        shikona.transliteration,
                    )
            except ShikonaGenerationError as e:
                logger.warning("Failed to generate shikona: %s", e)
                continue

        if len(options) < count:
            logger.warning(
                "Could only generate %d/%d shikona options",
                len(options),
                count,
            )

        return options

    @staticmethod
    def create_shikona_from_option(option: ShikonaOption) -> ShikonaModel:
        """
        Create a Shikona model instance from a ShikonaOption.

        Args:
        ----
            option: The ShikonaOption to persist.

        Returns:
        -------
            The newly created Shikona instance.

        """
        return ShikonaModel.objects.create(
            name=option.name,
            transliteration=option.transliteration,
            interpretation=option.interpretation,
        )
