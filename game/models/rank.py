"""Rank model for sumo wrestling ranks."""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from game.enums import Direction as DirectionEnum
from game.enums import RankTitle
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
        on_delete=models.PROTECT,
        related_name="ranks",
        help_text="Division this rank belongs to",
    )
    title = models.CharField(
        max_length=2,
        choices=RankTitle.choices,
        help_text="Rank title short code (e.g., Y=Yokozuna, O=Ozeki)",
    )
    level = models.PositiveSmallIntegerField(
        help_text=(
            "Hierarchical level (1=highest/Yokozuna, 12=lowest/Banzuke-gai)"
        ),
    )
    order = models.PositiveSmallIntegerField(
        blank=True,
        default=0,
        help_text="Positional number within rank (e.g., Maegashira 1, 2, 3...)",
    )
    direction = models.CharField(
        max_length=1,
        choices=DirectionEnum.choices,
        blank=True,
        default="",
        help_text="Side of banzuke (E=East, W=West)",
    )

    class Meta:
        """Model metadata."""

        ordering = ["level", "order", "direction"]
        verbose_name = "Rank"
        verbose_name_plural = "Ranks"
        constraints = [
            models.CheckConstraint(
                condition=Q(level__gte=1) & Q(level__lte=12),
                name="rank_level_valid_range",
                violation_error_message=(
                    "Rank level must be between 1 and 12."
                ),
            ),
            models.CheckConstraint(
                condition=Q(order__gte=0),
                name="rank_order_non_negative",
                violation_error_message="Rank order must be non-negative.",
            ),
            models.CheckConstraint(
                condition=(
                    Q(order=0, direction="") | Q(order__gt=0) & ~Q(direction="")
                ),
                name="rank_direction_required_with_order",
                violation_error_message=(
                    "Direction required when order is greater than 0."
                ),
            ),
            models.UniqueConstraint(
                fields=["division", "title", "order", "direction"],
                name="unique_rank_position",
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return self.name

    @property
    def name(self) -> str:
        """Return formatted rank name with shorthand direction."""
        if self.order and self.direction:
            # direction is already the short code (E or W)
            title_display = self.get_title_display()
            return f"{title_display} {self.order}{self.direction}"
        return self.get_title_display()

    @property
    def long_name(self) -> str:
        """Return formatted rank name with full direction."""
        if self.order and self.direction:
            title_display = self.get_title_display()
            direction_display = self.get_direction_display()
            return f"{title_display} {self.order} {direction_display}"
        return self.get_title_display()

    @property
    def short_name(self) -> str:
        """Return abbreviated rank name."""
        # title is already the short code
        if self.order and self.direction:
            return f"{self.title}{self.order}{self.direction}"
        return self.title
