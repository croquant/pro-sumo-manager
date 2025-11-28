"""Generator for complete rikishi (wrestlers) with stats and background."""

import random

from libs.constants import (
    MAX_POTENTIAL,
    MAX_STAT_VALUE,
    MEAN_POTENTIAL,
    MIN_POTENTIAL,
    MIN_STAT_VALUE,
    NUM_STATS,
    SIGMA_POTENTIAL,
)
from libs.generators.shikona import ShikonaGenerator
from libs.generators.shusshin import ShusshinGenerator
from libs.types.rikishi import Rikishi, StatName


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

    def _distribute_stats(self, rikishi: Rikishi, points: int) -> Rikishi:
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

    def get(self) -> Rikishi:
        """
        Generate a complete rikishi with all attributes.

        Returns:
            Rikishi with shikona, shusshin, abilities, and stats.

        """
        shusshin = self.shusshin_generator.get()
        shikona = self.shikona_generator.generate_single(shusshin=str(shusshin))
        potential = self._get_potential_ability()
        current = self._get_current_ability(potential)
        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=potential,
            current=current,
        )
        points_to_distribute = current - (MIN_STAT_VALUE * NUM_STATS)
        return self._distribute_stats(rikishi, points_to_distribute)
