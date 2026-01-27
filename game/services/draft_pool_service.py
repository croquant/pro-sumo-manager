"""Service for managing draft pool operations during game setup."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from libs.generators.rikishi import RikishiGenerator

if TYPE_CHECKING:
    from libs.types.rikishi import Rikishi


@dataclass
class DraftCandidate:
    """A wrestler candidate in the draft pool with display-friendly data."""

    shikona_name: str
    shikona_transliteration: str
    shusshin_display: str
    strength: int
    technique: int
    balance: int
    endurance: int
    mental: int
    potential_tier: str
    # Store raw potential for internal use (not displayed)
    _potential: int

    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary for session storage."""
        return {
            "shikona_name": self.shikona_name,
            "shikona_transliteration": self.shikona_transliteration,
            "shusshin_display": self.shusshin_display,
            "strength": self.strength,
            "technique": self.technique,
            "balance": self.balance,
            "endurance": self.endurance,
            "mental": self.mental,
            "potential_tier": self.potential_tier,
            "_potential": self._potential,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> Self:
        """Create from dictionary (session storage)."""
        return cls(
            shikona_name=str(data["shikona_name"]),
            shikona_transliteration=str(data["shikona_transliteration"]),
            shusshin_display=str(data["shusshin_display"]),
            strength=int(data["strength"]),
            technique=int(data["technique"]),
            balance=int(data["balance"]),
            endurance=int(data["endurance"]),
            mental=int(data["mental"]),
            potential_tier=str(data["potential_tier"]),
            _potential=int(data["_potential"]),
        )


class DraftPoolService:
    """
    Service for generating and managing draft pools.

    The draft pool is a set of generated wrestlers that a new player
    can choose from to recruit for their stable.
    """

    # Potential tier mapping as specified in the issue
    POTENTIAL_TIERS: list[tuple[int, int, str]] = [
        (5, 20, "Limited"),
        (21, 35, "Average"),
        (36, 50, "Promising"),
        (51, 70, "Talented"),
        (71, 85, "Exceptional"),
        (86, 100, "Generational"),
    ]

    MIN_POOL_SIZE = 5
    MAX_POOL_SIZE = 8

    @staticmethod
    def get_potential_tier(potential: int) -> str:
        """
        Get the descriptive tier label for a potential value.

        Args:
            potential: The potential ability score (5-100).

        Returns:
            A descriptive tier label (e.g., "Promising", "Exceptional").

        """
        for min_val, max_val, label in DraftPoolService.POTENTIAL_TIERS:
            if min_val <= potential <= max_val:
                return label
        # Fallback for edge cases (shouldn't happen with valid potentials)
        return "Unknown"

    @staticmethod
    def generate_draft_pool(
        seed: int | None = None,
    ) -> list[DraftCandidate]:
        """
        Generate a pool of draft candidates.

        Creates 5-8 wrestlers with varied potentials and stats for the
        player to choose from during initial setup.

        Args:
            seed: Optional seed for deterministic generation (for testing).

        Returns:
            List of DraftCandidate objects representing available wrestlers.

        """
        rng = random.Random(seed)
        pool_size = rng.randint(
            DraftPoolService.MIN_POOL_SIZE,
            DraftPoolService.MAX_POOL_SIZE,
        )

        generator = RikishiGenerator(seed=seed)
        candidates: list[DraftCandidate] = []

        for _ in range(pool_size):
            rikishi = generator.get()
            candidate = DraftPoolService._rikishi_to_candidate(rikishi)
            candidates.append(candidate)

        return candidates

    @staticmethod
    def _rikishi_to_candidate(rikishi: Rikishi) -> DraftCandidate:
        """
        Convert a generated Rikishi to a DraftCandidate.

        Args:
            rikishi: The generated Rikishi from RikishiGenerator.

        Returns:
            A DraftCandidate with display-friendly data.

        """
        # Build shusshin display string
        shusshin = rikishi.shusshin
        if shusshin.country_code == "JP" and shusshin.jp_prefecture:
            # For Japanese wrestlers, show prefecture name
            shusshin_display = DraftPoolService._prefecture_to_name(
                shusshin.jp_prefecture
            )
        else:
            # For foreign wrestlers, show country name
            shusshin_display = DraftPoolService._country_to_name(
                shusshin.country_code
            )

        return DraftCandidate(
            shikona_name=rikishi.shikona.shikona,
            shikona_transliteration=rikishi.shikona.transliteration,
            shusshin_display=shusshin_display,
            strength=rikishi.strength,
            technique=rikishi.technique,
            balance=rikishi.balance,
            endurance=rikishi.endurance,
            mental=rikishi.mental,
            potential_tier=DraftPoolService.get_potential_tier(
                rikishi.potential
            ),
            _potential=rikishi.potential,
        )

    @staticmethod
    def _prefecture_to_name(prefecture_code: str) -> str:
        """
        Convert a JP prefecture code to a display name.

        Args:
            prefecture_code: ISO 3166-2 code like "JP-13" for Tokyo.

        Returns:
            Human-readable prefecture name.

        """
        # Import here to avoid circular dependencies
        from game.enums.jp_prefecture_enum import JPPrefecture

        try:
            return str(JPPrefecture(prefecture_code).label)
        except ValueError:
            return prefecture_code

    @staticmethod
    def _country_to_name(country_code: str) -> str:
        """
        Convert a country code to a display name.

        Args:
            country_code: ISO 3166-1 alpha-2 code like "MN" for Mongolia.

        Returns:
            Human-readable country name.

        """
        # Import here to avoid circular dependencies
        from game.enums.country_enum import Country

        try:
            return str(Country(country_code).label)
        except ValueError:
            return country_code

    @staticmethod
    def ensure_variety(candidates: list[DraftCandidate]) -> bool:
        """
        Check if the draft pool has sufficient variety in potentials.

        Args:
            candidates: List of draft candidates.

        Returns:
            True if the pool has at least 2 different potential tiers.

        """
        tiers = {c.potential_tier for c in candidates}
        return len(tiers) >= 2
