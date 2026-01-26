"""Bout model for recording individual match results."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Final, Literal, get_args

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

if TYPE_CHECKING:
    from game.models.banzuke import Banzuke
    from game.models.rikishi import Rikishi

# Valid kimarite (winning techniques) - extracted from libs/types/bout.py
KimariteType = Literal[
    "yorikiri",
    "oshidashi",
    "hatakikomi",
    "uwatenage",
    "shitatenage",
    "tsuppari",
    "kotenage",
    "yori-taoshi",
    "oshitaoshi",
    "hikiotoshi",
    "uwatedashinage",
    "shitatedashinage",
    "tsukiotoshi",
    "sukuinage",
    "tottari",
    "ketaguri",
    "utchari",
    "katasukashi",
]

VALID_KIMARITE: Final[tuple[str, ...]] = get_args(KimariteType)


class Bout(models.Model):
    """
    Represents a single bout between two rikishi in a tournament.

    Records the complete result of a match including winner, winning
    technique (kimarite), XP gains for both wrestlers, and commentary.
    """

    class Winner(models.TextChoices):
        """Winner position in the bout."""

        EAST = "east", "East"
        WEST = "west", "West"

    banzuke = models.ForeignKey(
        "game.Banzuke",
        on_delete=models.PROTECT,
        related_name="bouts",
        help_text="Tournament this bout belongs to",
    )
    east_rikishi = models.ForeignKey(
        "game.Rikishi",
        on_delete=models.PROTECT,
        related_name="bouts_as_east",
        help_text="Wrestler on the east side",
    )
    west_rikishi = models.ForeignKey(
        "game.Rikishi",
        on_delete=models.PROTECT,
        related_name="bouts_as_west",
        help_text="Wrestler on the west side",
    )

    day = models.PositiveSmallIntegerField(
        help_text="Tournament day (1-15)",
    )
    winner = models.CharField(
        max_length=4,
        choices=Winner.choices,
        help_text="Winner position (east or west)",
    )
    kimarite = models.CharField(
        max_length=32,
        help_text="Winning technique used",
    )

    east_xp_gain = models.PositiveIntegerField(
        help_text="XP gained by east rikishi",
    )
    west_xp_gain = models.PositiveIntegerField(
        help_text="XP gained by west rikishi",
    )

    excitement_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="Excitement level from 1.0 to 10.0",
    )
    commentary = models.TextField(
        help_text="Match commentary/description",
    )

    class Meta:
        """Model metadata."""

        ordering = ["banzuke", "day"]
        verbose_name = "Bout"
        verbose_name_plural = "Bouts"
        indexes = [
            models.Index(
                fields=["banzuke", "day"],
                name="bout_banzuke_day_idx",
            ),
        ]
        constraints = [
            # Each wrestler pair can only fight once per tournament
            # Use a canonical ordering (smaller id first) to catch both directions
            models.UniqueConstraint(
                fields=["banzuke", "east_rikishi", "west_rikishi"],
                name="unique_bout_per_tournament",
                violation_error_message=(
                    "These wrestlers have already fought in this tournament."
                ),
            ),
            # Day must be between 1 and 15
            models.CheckConstraint(
                condition=Q(day__gte=1) & Q(day__lte=15),
                name="bout_valid_day",
                violation_error_message="Day must be between 1 and 15.",
            ),
            # Excitement level must be between 1.0 and 10.0
            models.CheckConstraint(
                condition=(
                    Q(excitement_level__gte=Decimal("1.0"))
                    & Q(excitement_level__lte=Decimal("10.0"))
                ),
                name="bout_valid_excitement_level",
                violation_error_message=(
                    "Excitement level must be between 1.0 and 10.0."
                ),
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return (
            f"{self.banzuke} Day {self.day}: "
            f"{self.east_rikishi} vs {self.west_rikishi}"
        )

    def clean(self) -> None:
        """Validate model data."""
        errors: dict[str, list[str]] = {}

        # Validate wrestler cannot fight themselves
        east = getattr(self, "east_rikishi_id", None)
        west = getattr(self, "west_rikishi_id", None)
        if east is not None and west is not None and east == west:
            errors.setdefault("west_rikishi", []).append(
                "A wrestler cannot fight themselves."
            )

        # Validate kimarite is from valid list
        if self.kimarite and self.kimarite not in VALID_KIMARITE:
            errors.setdefault("kimarite", []).append(
                f"Invalid kimarite. Must be one of: {', '.join(VALID_KIMARITE)}"
            )

        if errors:
            raise ValidationError(errors)

    @property
    def winner_rikishi(self) -> Rikishi:
        """Return the winning rikishi."""
        if self.winner == self.Winner.EAST:
            return self.east_rikishi
        return self.west_rikishi

    @property
    def loser_rikishi(self) -> Rikishi:
        """Return the losing rikishi."""
        if self.winner == self.Winner.EAST:
            return self.west_rikishi
        return self.east_rikishi
