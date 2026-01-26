"""Heya (stable) model for the game."""

from django.conf import settings
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
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="heya",
        null=True,
        blank=True,
        help_text="Player who owns this stable (null for AI-controlled)",
    )

    class Meta:
        """Model metadata."""

        ordering = ["name"]
        verbose_name = "Heya"
        verbose_name_plural = "Heya"

    def __str__(self) -> str:
        """Return the stable name."""
        return self.name.transliteration

    @property
    def is_player_controlled(self) -> bool:
        """Return whether this stable is controlled by a player."""
        return self.owner is not None
