"""Generator for complete rikishi (wrestlers) with stats and background."""

import random
from typing import Literal

from pydantic import BaseModel, Field

from libs.constants import (
    MAX_POTENTIAL,
    MAX_STAT_VALUE,
    MEAN_POTENTIAL,
    MIN_POTENTIAL,
    MIN_STAT_VALUE,
    NUM_STATS,
    SIGMA_POTENTIAL,
)
from libs.generators.shikona import ShikonaGenerator, ShikonaInterpretation
from libs.generators.shusshin import Shusshin, ShusshinGenerator

# Type alias for stat names
StatName = Literal["strength", "technique", "balance", "endurance", "mental"]


class GeneratedRikishi(BaseModel):
    """
    A complete rikishi with name, origin, abilities, and individual stats.

    The relationship between current ability and individual stats:
    - current: Overall ability score (5-100) representing total capability
    - Individual stats: Specific attributes (1-20 each) that sum up to represent
      how the current ability is distributed across different areas
    - When current ability increases through training, individual stats improve
    - The starting distribution: all stats begin at 1, then (current - 5) points
      are randomly distributed among the five stats

    Attributes:
        shikona: Ring name with interpretation.
        shusshin: Place of origin.
        potential: Maximum ability the rikishi can reach (5-100).
        current: Current overall ability level (5-100).
        strength: Physical strength stat (1-20).
        technique: Technical skill stat (1-20).
        balance: Balance and stability stat (1-20).
        endurance: Stamina and endurance stat (1-20).
        mental: Mental fortitude stat (1-20).

    """

    shikona: ShikonaInterpretation
    shusshin: Shusshin
    potential: int = Field(..., ge=MIN_POTENTIAL, le=MAX_POTENTIAL)
    current: int = Field(..., ge=MIN_POTENTIAL, le=MAX_POTENTIAL)
    strength: int = Field(default=1, ge=MIN_STAT_VALUE, le=MAX_STAT_VALUE)
    technique: int = Field(default=1, ge=MIN_STAT_VALUE, le=MAX_STAT_VALUE)
    balance: int = Field(default=1, ge=MIN_STAT_VALUE, le=MAX_STAT_VALUE)
    endurance: int = Field(default=1, ge=MIN_STAT_VALUE, le=MAX_STAT_VALUE)
    mental: int = Field(default=1, ge=MIN_STAT_VALUE, le=MAX_STAT_VALUE)


class RikishiGenerator:
    """
    Generator for complete rikishi with realistic attributes.

    Generates rikishi with shikona, shusshin, abilities (potential and current),
    and individual stats distributed according to current ability.

    """

    def __init__(self, seed: int | None = None) -> None:
        """
        Initialize the rikishi generator.

        Args:
            seed: Optional seed for deterministic generation.

        """
        self.random = random.Random(seed)
        self.shikona_generator = ShikonaGenerator(seed=seed)
        self.shusshin_generator = ShusshinGenerator(seed=seed)

    def _get_potential_ability(self) -> int:
        """
        Generate a potential ability score using Gaussian distribution.

        Uses a normal distribution with mean=30 and sigma=20, clamped to
        [5, 100]. This creates a realistic talent pool where:
        - Most rikishi (68%) fall between 10-50 (lower to mid-tier)
        - Few reach elite levels (70+)
        - Reaching 100 potential is extremely rare (~1 in 4,300, or
          "once per generation")

        Returns:
            Potential ability score (5-100), centered around 30.

        """
        potential = self.random.gauss(MEAN_POTENTIAL, SIGMA_POTENTIAL)
        # Clamp to valid range
        potential = max(MIN_POTENTIAL, min(MAX_POTENTIAL, potential))
        return round(potential)

    def _get_current_ability(self, potential: int) -> int:
        """
        Generate current ability based on potential.

        All recruits start with low ability (5-12 base), with a visible hint
        of their potential (+/- ~6 points). This creates:
        - Meaningful differentiation between recruits
        - Talent is more visible but still requires development
        - Strong correlation with potential for better player feedback

        Args:
            potential: The rikishi's potential ability score.

        Returns:
            Current ability score (typically 5-18), always <= potential.

        """
        # Base ability: all recruits start relatively weak
        base = self.random.uniform(5, 12)

        # Moderate bonus/penalty based on deviation from mean potential
        # High potential (70): +6 bonus, Low potential (10): -3 penalty
        bonus = (potential - MEAN_POTENTIAL) * 0.15

        current = round(max(MIN_POTENTIAL, base + bonus))

        # Ensure current never exceeds potential
        return min(current, potential)

    def _distribute_stats(
        self, rikishi: GeneratedRikishi, points: int
    ) -> GeneratedRikishi:
        """
        Distribute points randomly across rikishi stats.

        Args:
            rikishi: The rikishi to modify.
            points: Total points to distribute.

        Returns:
            New rikishi instance with distributed stats (validated by Pydantic).

        Raises:
            ValueError: If points is negative.

        """
        if points < 0:
            msg = f"Points must be non-negative, got {points}"
            raise ValueError(msg)

        if points == 0:
            return rikishi

        stat_names: list[StatName] = [
            "strength",
            "technique",
            "balance",
            "endurance",
            "mental",
        ]

        # Track how many stats can still be increased
        max_allocation = NUM_STATS * (MAX_STAT_VALUE - MIN_STAT_VALUE)
        if points > max_allocation:
            points = max_allocation

        # Build a mutable dict of current stat values
        stats = {
            "strength": rikishi.strength,
            "technique": rikishi.technique,
            "balance": rikishi.balance,
            "endurance": rikishi.endurance,
            "mental": rikishi.mental,
        }

        remaining = points

        while remaining > 0:
            # Check if all stats are maxed out
            if all(stats[stat] >= MAX_STAT_VALUE for stat in stat_names):
                break

            stat = self.random.choice(stat_names)
            current_value = stats[stat]

            if current_value < MAX_STAT_VALUE:
                stats[stat] = current_value + 1
                remaining -= 1

        # Use model_copy to create a new validated instance
        return rikishi.model_copy(update=stats)

    def get(self) -> GeneratedRikishi:
        """
        Generate a complete rikishi with all attributes.

        Returns:
            GeneratedRikishi with shikona, shusshin, abilities, and stats.

        """
        shusshin = self.shusshin_generator.get()
        shikona = self.shikona_generator.generate_single(shusshin=str(shusshin))
        potential = self._get_potential_ability()
        current = self._get_current_ability(potential)
        rikishi = GeneratedRikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=potential,
            current=current,
        )
        points_to_distribute = current - (MIN_STAT_VALUE * NUM_STATS)
        return self._distribute_stats(rikishi, points_to_distribute)
