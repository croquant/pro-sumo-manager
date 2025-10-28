"""Division model for sumo wrestling divisions."""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from game.enums import Division as DivisionEnum


class Division(models.Model):
    """
    Represents a sumo wrestling division.

    Divisions are hierarchical levels in professional sumo wrestling,
    from Makuuchi (top) to Banzuke-gai (unranked). Each division
    has a unique level number for ordering.
    """

    level = models.PositiveSmallIntegerField(
        primary_key=True,
        help_text="Division level (1=Makuuchi/highest, 8=Banzuke-gai/lowest)",
    )
    name = models.CharField(
        max_length=2,
        choices=DivisionEnum.choices,
        help_text="Division short code (e.g., M=Makuuchi, J=Juryo)",
    )

    class Meta:
        """Model metadata."""

        ordering = ["level"]
        verbose_name = "Division"
        verbose_name_plural = "Divisions"
        constraints = [
            models.CheckConstraint(
                condition=Q(level__gte=1) & Q(level__lte=8),
                name="division_level_valid_range",
                violation_error_message=(
                    "Division level must be between 1 and 8."
                ),
            ),
            models.UniqueConstraint(
                fields=["name"],
                name="unique_division_name",
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return self.get_name_display()
