"""Service for managing rikishi operations and business logic."""

from __future__ import annotations

import random

from django.core.exceptions import ValidationError
from django.db import transaction

from game.constants import MAX_STAT_VALUE
from game.models import (
    GameDate,
    Rank,
    Rikishi,
    RikishiStats,
    Shikona,
    Shusshin,
)


class RikishiService:
    """
    Service for managing rikishi-related operations.

    This service provides business logic for creating, updating, and
    managing rikishi and their statistics. All rikishi modifications
    should go through this service to ensure consistency and proper
    validation.
    """

    @staticmethod
    def validate_debut_intai_dates(
        debut: GameDate | None,
        intai: GameDate | None,
    ) -> None:
        """
        Validate that debut date is before or equal to retirement date.

        Args:
        ----
            debut: The debut date.
            intai: The retirement date.

        Raises:
        ------
            ValidationError: If debut is after retirement.

        """
        if debut and intai:
            # Compare dates by converting to tuples (year, month, day)
            debut_tuple = (debut.year, debut.month, debut.day)
            intai_tuple = (intai.year, intai.month, intai.day)
            if debut_tuple > intai_tuple:
                msg = "Debut date must be before or equal to retirement date."
                raise ValidationError(msg)

    @staticmethod
    def validate_stats_within_potential(stats: RikishiStats) -> None:
        """
        Validate that current stats don't exceed potential.

        Args:
        ----
            stats: The RikishiStats instance to validate.

        Raises:
        ------
            ValidationError: If current stats exceed potential.

        """
        if stats.current > stats.potential:
            msg = (
                f"Current stats ({stats.current}) cannot exceed "
                f"potential ({stats.potential})."
            )
            raise ValidationError(msg)

    @staticmethod
    @transaction.atomic
    def create_rikishi(
        shikona: Shikona,
        shusshin: Shusshin | None = None,
        rank: Rank | None = None,
        debut: GameDate | None = None,
        intai: GameDate | None = None,
    ) -> Rikishi:
        """
        Create a new rikishi with validation.

        Args:
        ----
            shikona: The wrestler's ring name.
            shusshin: The wrestler's place of origin (optional).
            rank: The wrestler's current rank (optional).
            debut: The debut date (optional).
            intai: The retirement date (optional).

        Returns:
        -------
            The newly created Rikishi instance.

        Raises:
        ------
            ValidationError: If debut is after retirement.

        """
        # Validate dates
        RikishiService.validate_debut_intai_dates(debut, intai)

        # Create and return rikishi
        return Rikishi.objects.create(
            shikona=shikona,
            shusshin=shusshin,
            rank=rank,
            debut=debut,
            intai=intai,
        )

    @staticmethod
    @transaction.atomic
    def update_rikishi(
        rikishi: Rikishi,
        shikona: Shikona | None = None,
        shusshin: Shusshin | None = None,
        rank: Rank | None = None,
        debut: GameDate | None = None,
        intai: GameDate | None = None,
    ) -> Rikishi:
        """
        Update a rikishi with validation.

        Args:
        ----
            rikishi: The rikishi to update.
            shikona: New ring name (optional).
            shusshin: New place of origin (optional).
            rank: New rank (optional).
            debut: New debut date (optional).
            intai: New retirement date (optional).

        Returns:
        -------
            The updated Rikishi instance.

        Raises:
        ------
            ValidationError: If debut is after retirement.

        """
        if shikona is not None:
            rikishi.shikona = shikona
        if shusshin is not None:
            rikishi.shusshin = shusshin
        if rank is not None:
            rikishi.rank = rank
        if debut is not None:
            rikishi.debut = debut
        if intai is not None:
            rikishi.intai = intai

        # Validate dates
        RikishiService.validate_debut_intai_dates(rikishi.debut, rikishi.intai)

        rikishi.save()
        return rikishi

    @staticmethod
    @transaction.atomic
    def create_rikishi_stats(
        rikishi: Rikishi,
        potential: int,
        xp: int = 0,
        strength: int = 1,
        technique: int = 1,
        balance: int = 1,
        endurance: int = 1,
        mental: int = 1,
    ) -> RikishiStats:
        """
        Create stats for a rikishi with validation.

        Args:
        ----
            rikishi: The rikishi these stats belong to.
            potential: Maximum total stat points achievable.
            xp: Initial experience points (default: 0).
            strength: Initial strength stat (default: 1).
            technique: Initial technique stat (default: 1).
            balance: Initial balance stat (default: 1).
            endurance: Initial endurance stat (default: 1).
            mental: Initial mental stat (default: 1).

        Returns:
        -------
            The newly created RikishiStats instance.

        Raises:
        ------
            ValidationError: If current stats exceed potential.

        """
        stats = RikishiStats(
            rikishi=rikishi,
            potential=potential,
            xp=xp,
            strength=strength,
            technique=technique,
            balance=balance,
            endurance=endurance,
            mental=mental,
        )

        # Validate before saving
        RikishiService.validate_stats_within_potential(stats)
        stats.save()
        return stats

    @staticmethod
    @transaction.atomic
    def increase_random_stats(stats: RikishiStats, amount: int = 1) -> None:
        """
        Increase random stats up to potential limit.

        Distributes the specified number of stat points randomly among
        available attributes that haven't yet reached their maximum
        value. Respects both the per-stat maximum (MAX_STAT_VALUE) and
        the wrestler's total potential.

        Args:
        ----
            stats: The RikishiStats instance to modify.
            amount: Number of stat points to distribute randomly.

        Note:
        ----
            Changes are automatically saved to the database within a
            transaction. If any error occurs, all changes are rolled back.

        """
        stat_names = [
            "strength",
            "technique",
            "balance",
            "endurance",
            "mental",
        ]

        points_to_distribute = amount

        while points_to_distribute > 0 and stats.current < stats.potential:
            # Find stats that can still be increased
            available_stats = [
                stat
                for stat in stat_names
                if getattr(stats, stat) < MAX_STAT_VALUE
            ]

            if not available_stats:
                # All stats are maxed out, can't increase further
                break

            # Increase a random available stat
            random_stat = random.choice(available_stats)
            current_value = getattr(stats, random_stat)
            setattr(stats, random_stat, current_value + 1)
            points_to_distribute -= 1

        # Validate before saving
        RikishiService.validate_stats_within_potential(stats)
        stats.save()
