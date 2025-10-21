"""Division model for sumo wrestling divisions."""

from __future__ import annotations

from django.db import models

from game.constants import DIVISION_NAMES, DIVISION_NAMES_SHORT


class Division(models.Model):
    """
    Represents a sumo wrestling division.

    Divisions are hierarchical levels in professional sumo wrestling,
    from Makuuchi (top) to Banzuke-gai (unranked). Each division
    has a unique level number for ordering.
    """

    level = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(
        max_length=12,
        choices=DIVISION_NAMES,
    )

    class Meta:
        """Model metadata."""

        ordering = ["level"]
        verbose_name = "Division"
        verbose_name_plural = "Divisions"

    def __str__(self) -> str:
        """Return human-readable representation."""
        return str(self.name)

    @property
    def short_name(self) -> str:
        """Return abbreviated division name."""
        return DIVISION_NAMES_SHORT[str(self.name)]
