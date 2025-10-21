"""Rank model for sumo wrestling ranks."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from game.constants import (
    DIRECTION_NAMES,
    DIRECTION_NAMES_SHORT,
    RANK_NAMES,
    RANK_NAMES_SHORT,
    RANKING_LEVELS,
)
from game.models.division import Division


class Rank(models.Model):
    """
    Represents a specific rank within a sumo division.

    Ranks can be simple titles (e.g., "Yokozuna") or positional
    (e.g., "Maegashira 3 East"). The level field determines the
    hierarchical ordering across all ranks.
    """

    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        related_name="ranks",
    )
    title = models.CharField(
        max_length=12,
        choices=RANK_NAMES,
    )
    level = models.PositiveSmallIntegerField()
    order = models.PositiveSmallIntegerField(
        blank=True,
        default=0,
    )
    direction = models.CharField(
        max_length=4,
        choices=DIRECTION_NAMES,
        blank=True,
        default="",
    )

    class Meta:
        """Model metadata."""

        ordering = ["level", "order", "direction"]
        verbose_name = "Rank"
        verbose_name_plural = "Ranks"

    def __str__(self) -> str:
        """Return human-readable representation."""
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:  # type: ignore[override]
        """Save the rank, ensuring validation runs."""
        if not self.level:  # Only run clean if level not already set
            self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate rank data and set computed fields."""
        super().clean()

        # Validate title exists in RANKING_LEVELS
        if self.title not in RANKING_LEVELS:
            raise ValidationError(
                {"title": f"Invalid rank title: {self.title}"}
            )

        # Set level from RANKING_LEVELS
        self.level = RANKING_LEVELS[self.title]

        # Set division based on title if it exists as a division
        # Otherwise default to Makuuchi
        try:
            self.division = Division.objects.get(name=self.title)
        except Division.DoesNotExist:
            self.division = Division.objects.get(name="Makuuchi")

        # Validate direction is set if order is set
        if self.order and not self.direction:
            raise ValidationError(
                {"direction": "Direction required when order specified."}
            )

    @property
    def name(self) -> str:
        """Return formatted rank name with shorthand direction."""
        if self.order and self.direction:
            dir_shorthand = DIRECTION_NAMES_SHORT[str(self.direction)]
            return f"{self.title} {self.order}{dir_shorthand}"
        return str(self.title)

    @property
    def long_name(self) -> str:
        """Return formatted rank name with full direction."""
        if self.order and self.direction:
            return f"{self.title} {self.order} {self.direction}"
        return str(self.title)

    @property
    def short_name(self) -> str:
        """Return abbreviated rank name."""
        shorthand = RANK_NAMES_SHORT[str(self.title)]
        if self.order and self.direction:
            dir_shorthand = DIRECTION_NAMES_SHORT[str(self.direction)]
            return f"{shorthand}{self.order}{dir_shorthand}"
        return shorthand
