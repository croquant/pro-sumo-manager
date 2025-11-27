"""Rikishi (sumo wrestler) models for the game."""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from game.constants import MAX_STAT_VALUE
from game.models.gamedate import GameDate
from game.models.heya import Heya
from game.models.rank import Rank
from game.models.shikona import Shikona
from game.models.shusshin import Shusshin


class Rikishi(models.Model):
    """
    Represents a professional sumo wrestler.

    A rikishi is a professional sumo wrestler who competes in official
    tournaments. Each rikishi has a ring name (shikona), place of
    origin (shusshin), current rank, and dates tracking their career
    debut and retirement.
    """

    shikona = models.ForeignKey(
        Shikona,
        on_delete=models.PROTECT,
        related_name="rikishi",
        help_text="Ring name of the wrestler",
        verbose_name="Shikona",
    )

    heya = models.ForeignKey(
        Heya,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="rikishi",
        help_text="Stable the wrestler belongs to",
        verbose_name="Heya",
    )

    shusshin = models.ForeignKey(
        Shusshin,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rikishi",
        help_text="Place of origin for the wrestler",
        verbose_name="Shusshin",
    )

    rank = models.ForeignKey(
        Rank,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rikishi",
        help_text="Current rank in the banzuke (ranking system)",
        verbose_name="Rank",
    )

    debut = models.ForeignKey(
        GameDate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="debut_rikishi",
        help_text="Date of first professional match",
        verbose_name="Debut date",
    )

    intai = models.ForeignKey(
        GameDate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="retired_rikishi",
        help_text="Date of retirement from professional sumo",
        verbose_name="Retirement date",
    )

    # Stats
    potential = models.PositiveIntegerField(
        help_text="Maximum total stat points this wrestler can achieve"
    )
    xp = models.PositiveIntegerField(
        default=0,
        help_text=("Experience points earned through training and competition"),
    )

    strength = models.PositiveIntegerField(
        default=1, help_text="Physical power and pushing ability"
    )
    technique = models.PositiveIntegerField(
        default=1, help_text="Technical skill and knowledge of techniques"
    )
    balance = models.PositiveIntegerField(
        default=1, help_text="Stability and ability to maintain footing"
    )
    endurance = models.PositiveIntegerField(
        default=1, help_text="Stamina and ability to sustain effort"
    )
    mental = models.PositiveIntegerField(
        default=1, help_text="Mental fortitude and fighting spirit"
    )

    class Meta:
        """Model metadata."""

        ordering = ["shikona__transliteration"]
        verbose_name = "Rikishi"
        verbose_name_plural = "Rikishi"
        indexes = [
            models.Index(fields=["shikona"], name="rikishi_shikona_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(strength__gte=1),
                name="rikishi_strength_min",
                violation_error_message="Strength must be at least 1.",
            ),
            models.CheckConstraint(
                condition=Q(strength__lte=MAX_STAT_VALUE),
                name="rikishi_strength_max",
                violation_error_message=(
                    f"Strength cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(technique__gte=1),
                name="rikishi_technique_min",
                violation_error_message="Technique must be at least 1.",
            ),
            models.CheckConstraint(
                condition=Q(technique__lte=MAX_STAT_VALUE),
                name="rikishi_technique_max",
                violation_error_message=(
                    f"Technique cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(balance__gte=1),
                name="rikishi_balance_min",
                violation_error_message="Balance must be at least 1.",
            ),
            models.CheckConstraint(
                condition=Q(balance__lte=MAX_STAT_VALUE),
                name="rikishi_balance_max",
                violation_error_message=(
                    f"Balance cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(endurance__gte=1),
                name="rikishi_endurance_min",
                violation_error_message="Endurance must be at least 1.",
            ),
            models.CheckConstraint(
                condition=Q(endurance__lte=MAX_STAT_VALUE),
                name="rikishi_endurance_max",
                violation_error_message=(
                    f"Endurance cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(mental__gte=1),
                name="rikishi_mental_min",
                violation_error_message="Mental must be at least 1.",
            ),
            models.CheckConstraint(
                condition=Q(mental__lte=MAX_STAT_VALUE),
                name="rikishi_mental_max",
                violation_error_message=(
                    f"Mental cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(potential__gte=5) & Q(potential__lte=100),
                name="rikishi_potential_range",
                violation_error_message=(
                    "Potential must be between 5 and 100."
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    potential__gte=models.F("strength")
                    + models.F("technique")
                    + models.F("balance")
                    + models.F("endurance")
                    + models.F("mental")
                ),
                name="rikishi_current_within_potential",
                violation_error_message="Total stats cannot exceed potential.",
            ),
        ]

    def __str__(self) -> str:
        """Return the wrestler's ring name."""
        return self.shikona.transliteration

    @property
    def current(self) -> int:
        """Calculate total current stat points."""
        return (
            self.strength
            + self.technique
            + self.balance
            + self.endurance
            + self.mental
        )
