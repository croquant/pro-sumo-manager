"""Game date model for tracking in-game time progression."""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from game.constants import N_DAYS, N_MONTHS


class GameDate(models.Model):
    """
    Represents a single day in the game's internal calendar.

    The game uses a simplified calendar system with 12 months
    and 24 days per month. Each tick of the game clock creates
    a new GameDate record, providing a complete historical timeline.

    This model should not be created directly. Use GameClockService
    to advance the game date.
    """

    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    day = models.PositiveIntegerField()

    class Meta:
        """Model metadata."""

        ordering = ["-year", "-month", "-day"]
        verbose_name = "Game Date"
        verbose_name_plural = "Game Dates"
        indexes = [
            models.Index(
                fields=["-year", "-month", "-day"],
                name="gamedate_current_date_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(month__gte=1) & Q(month__lte=N_MONTHS),
                name="gamedate_month_valid_range",
                violation_error_message=(
                    f"Month must be between 1 and {N_MONTHS}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(day__gte=1) & Q(day__lte=N_DAYS),
                name="gamedate_day_valid_range",
                violation_error_message=f"Day must be between 1 and {N_DAYS}.",
            ),
            models.UniqueConstraint(
                fields=["year", "month", "day"],
                name="unique_game_date",
                violation_error_message="This game date already exists.",
            ),
        ]

    def __str__(self) -> str:
        """Return formatted date string."""
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
