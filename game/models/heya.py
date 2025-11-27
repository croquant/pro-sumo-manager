"""Heya (stable) model for the game."""

from django.db import models

from game.models.gamedate import GameDate
from game.models.shikona import Shikona


class Heya(models.Model):
    """
    Represents a sumo stable (heya).

    A heya is an organization of sumo wrestlers where they live and train.
    It is managed by a stable master (oyakata).
    """

    name = models.ForeignKey(
        Shikona,
        on_delete=models.PROTECT,
        related_name="heya_name",
        help_text="Name of the stable (e.g., 'Miyagino')",
        verbose_name="Name",
    )
    created_at = models.ForeignKey(
        GameDate,
        on_delete=models.PROTECT,
        related_name="heya_created_at",
        help_text="Date the stable was founded",
        verbose_name="Founded Date",
    )

    class Meta:
        """Model metadata."""

        ordering = ["name"]
        verbose_name = "Heya"
        verbose_name_plural = "Heya"

    def __str__(self) -> str:
        """Return the stable name."""
        return self.name.transliteration
