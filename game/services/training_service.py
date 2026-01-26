"""Service for managing rikishi training operations."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from game.models import Rikishi, TrainingSession
from libs.constants import MAX_STAT_VALUE


class TrainingService:
    """
    Service for managing training-related operations.

    This service provides business logic for training rikishi stats,
    calculating XP costs, and recording training history.
    """

    @staticmethod
    def calculate_xp_cost(current_stat_level: int) -> int:
        """
        Calculate the XP cost to train a stat by 1 point.

        The cost formula is: current_stat_level * 10

        Args:
        ----
            current_stat_level: The current value of the stat.

        Returns:
        -------
            The XP cost to increase the stat by 1.

        """
        return current_stat_level * 10

    @staticmethod
    def validate_can_train(
        rikishi: Rikishi,
        stat: str,
    ) -> None:
        """
        Validate that a rikishi can train a specific stat.

        Args:
        ----
            rikishi: The rikishi to train.
            stat: The stat name to train.

        Raises:
        ------
            ValidationError: If training is not possible.

        """
        # Validate stat name
        valid_stats = [choice[0] for choice in TrainingSession.Stat.choices]
        if stat not in valid_stats:
            msg = f"Invalid stat '{stat}'. Must be one of: {valid_stats}"
            raise ValidationError(msg)

        current_stat_value = getattr(rikishi, stat)

        # Check if stat is already at max
        if current_stat_value >= MAX_STAT_VALUE:
            msg = (
                f"Stat '{stat}' is already at maximum value "
                f"({MAX_STAT_VALUE})."
            )
            raise ValidationError(msg)

        # Check if training would exceed potential
        if rikishi.current >= rikishi.potential:
            msg = (
                f"Rikishi has reached their potential ({rikishi.potential}). "
                "Cannot train further."
            )
            raise ValidationError(msg)

        # Calculate XP cost and check if rikishi has enough
        xp_cost = TrainingService.calculate_xp_cost(current_stat_value)
        if rikishi.xp < xp_cost:
            msg = (
                f"Insufficient XP. Training '{stat}' costs {xp_cost} XP, "
                f"but rikishi only has {rikishi.xp} XP."
            )
            raise ValidationError(msg)

    @staticmethod
    @transaction.atomic
    def train_stat(
        rikishi: Rikishi,
        stat: str,
    ) -> TrainingSession:
        """
        Train a specific stat for a rikishi.

        Deducts XP, increases the stat by 1, and creates a training
        session record.

        Args:
        ----
            rikishi: The rikishi to train.
            stat: The stat name to train (strength, technique, balance,
                  endurance, or mental).

        Returns:
        -------
            The created TrainingSession record.

        Raises:
        ------
            ValidationError: If training is not possible.

        """
        # Validate training is possible
        TrainingService.validate_can_train(rikishi, stat)

        # Get current values
        stat_before = getattr(rikishi, stat)
        xp_cost = TrainingService.calculate_xp_cost(stat_before)

        # Apply training
        rikishi.xp -= xp_cost
        setattr(rikishi, stat, stat_before + 1)
        rikishi.save()

        # Record training session
        training_session = TrainingSession.objects.create(
            rikishi=rikishi,
            stat=stat,
            xp_cost=xp_cost,
            stat_before=stat_before,
            stat_after=stat_before + 1,
        )

        return training_session
