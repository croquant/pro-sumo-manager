"""Service for generating draft pool during onboarding."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from game.models import Heya, Rikishi, Shikona
from game.models import Shusshin as ShusshinModel
from libs.generators.rikishi import RikishiGenerator

logger = logging.getLogger(__name__)


@dataclass
class DraftPoolRikishi:
    """Serialization-friendly rikishi for session storage."""

    shikona_name: str
    shikona_transliteration: str
    shikona_interpretation: str
    shusshin_country_code: str
    shusshin_jp_prefecture: str
    shusshin_display: str
    potential: int
    potential_tier: str
    strength: int
    technique: int
    balance: int
    endurance: int
    mental: int


class DraftPoolService:
    """
    Service for generating and managing draft pool during onboarding.

    Provides business logic for generating a pool of wrestler candidates
    that new players can choose from during initial setup.
    """

    POTENTIAL_TIERS: list[tuple[int, str]] = [
        (20, "Limited"),
        (35, "Average"),
        (50, "Promising"),
        (70, "Talented"),
        (85, "Exceptional"),
        (100, "Generational"),
    ]

    @staticmethod
    def get_potential_tier(potential: int) -> str:
        """
        Get the tier label for a given potential value.

        Args:
        ----
            potential: The potential value (5-100).

        Returns:
        -------
            The tier label (e.g., "Promising", "Talented").

        """
        for threshold, tier in DraftPoolService.POTENTIAL_TIERS:
            if potential <= threshold:
                return tier
        return "Generational"

    @staticmethod
    def generate_draft_pool(count: int = 6) -> list[DraftPoolRikishi]:
        """
        Generate a pool of wrestler candidates for drafting.

        Uses the RikishiGenerator to create unique wrestlers with
        all their stats and attributes.

        Args:
        ----
            count: Number of wrestlers to generate (default: 6).

        Returns:
        -------
            List of DraftPoolRikishi instances ready for display.

        """
        pool: list[DraftPoolRikishi] = []
        generator = RikishiGenerator()

        # Get existing shikona names to avoid duplicates
        existing_names = set(Shikona.objects.values_list("name", flat=True))

        max_attempts = count * 3

        for _ in range(max_attempts):
            if len(pool) >= count:
                break

            try:
                rikishi = generator.get()

                # Check uniqueness against DB and current pool
                if (
                    rikishi.shikona.shikona not in existing_names
                    and rikishi.shikona.shikona
                    not in {r.shikona_name for r in pool}
                ):
                    pool.append(
                        DraftPoolRikishi(
                            shikona_name=rikishi.shikona.shikona,
                            shikona_transliteration=rikishi.shikona.transliteration,
                            shikona_interpretation=rikishi.shikona.interpretation,
                            shusshin_country_code=rikishi.shusshin.country_code,
                            shusshin_jp_prefecture=rikishi.shusshin.jp_prefecture,
                            shusshin_display=str(rikishi.shusshin),
                            potential=rikishi.potential,
                            potential_tier=DraftPoolService.get_potential_tier(
                                rikishi.potential
                            ),
                            strength=rikishi.strength,
                            technique=rikishi.technique,
                            balance=rikishi.balance,
                            endurance=rikishi.endurance,
                            mental=rikishi.mental,
                        )
                    )
                    logger.info(
                        "Generated draft candidate: %s (%s)",
                        rikishi.shikona.shikona,
                        rikishi.shikona.transliteration,
                    )
            except Exception as e:
                logger.warning("Failed to generate draft candidate: %s", e)
                continue

        if len(pool) < count:
            logger.warning(
                "Could only generate %d/%d draft candidates",
                len(pool),
                count,
            )

        return pool

    @staticmethod
    def serialize_for_session(
        pool: list[DraftPoolRikishi],
    ) -> list[dict[str, Any]]:
        """
        Serialize draft pool for session storage.

        Args:
        ----
            pool: List of DraftPoolRikishi instances.

        Returns:
        -------
            List of dictionaries suitable for JSON serialization.

        """
        return [
            {
                "shikona_name": r.shikona_name,
                "shikona_transliteration": r.shikona_transliteration,
                "shikona_interpretation": r.shikona_interpretation,
                "shusshin_country_code": r.shusshin_country_code,
                "shusshin_jp_prefecture": r.shusshin_jp_prefecture,
                "shusshin_display": r.shusshin_display,
                "potential": r.potential,
                "potential_tier": r.potential_tier,
                "strength": r.strength,
                "technique": r.technique,
                "balance": r.balance,
                "endurance": r.endurance,
                "mental": r.mental,
            }
            for r in pool
        ]

    @staticmethod
    def deserialize_from_session(
        data: list[dict[str, Any]],
    ) -> list[DraftPoolRikishi]:
        """
        Deserialize draft pool from session storage.

        Args:
        ----
            data: List of dictionaries from session.

        Returns:
        -------
            List of DraftPoolRikishi instances.

        """
        return [
            DraftPoolRikishi(
                shikona_name=d["shikona_name"],
                shikona_transliteration=d["shikona_transliteration"],
                shikona_interpretation=d["shikona_interpretation"],
                shusshin_country_code=d["shusshin_country_code"],
                shusshin_jp_prefecture=d["shusshin_jp_prefecture"],
                shusshin_display=d["shusshin_display"],
                potential=d["potential"],
                potential_tier=d["potential_tier"],
                strength=d["strength"],
                technique=d["technique"],
                balance=d["balance"],
                endurance=d["endurance"],
                mental=d["mental"],
            )
            for d in data
        ]

    @staticmethod
    def create_rikishi_from_selection(
        selection: dict[str, Any], heya: Heya
    ) -> Rikishi:
        """
        Create a Rikishi model from a draft pool selection.

        Args:
        ----
            selection: Dictionary with rikishi data from session.
            heya: The heya to assign the wrestler to.

        Returns:
        -------
            The newly created Rikishi instance.

        """
        # Create or get the Shikona
        shikona, _ = Shikona.objects.get_or_create(
            name=selection["shikona_name"],
            defaults={
                "transliteration": selection["shikona_transliteration"],
                "interpretation": selection["shikona_interpretation"],
            },
        )

        # Create or get the Shusshin
        shusshin, _ = ShusshinModel.objects.get_or_create(
            country_code=selection["shusshin_country_code"],
            jp_prefecture=selection["shusshin_jp_prefecture"],
        )

        # Create the Rikishi
        return Rikishi.objects.create(
            shikona=shikona,
            heya=heya,
            shusshin=shusshin,
            potential=selection["potential"],
            strength=selection["strength"],
            technique=selection["technique"],
            balance=selection["balance"],
            endurance=selection["endurance"],
            mental=selection["mental"],
        )
