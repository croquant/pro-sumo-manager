"""Banzuke and BanzukeEntry models."""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from game.models.gamedate import GameDate
from game.models.rank import Rank
from game.models.rikishi import Rikishi


class Banzuke(models.Model):
    """
    Represents a sumo tournament.

    There are typically 6 official tournaments per year (Hatsu, Haru, Natsu,
    Nagoya, Aki, Kyushu). Each lasts 15 days.
    """

    class Status(models.TextChoices):
        """Status of the tournament."""

        SCHEDULED = "SCHEDULED", "Scheduled"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    name = models.CharField(
        max_length=64,
        help_text="Name of the tournament (e.g., Hatsu Basho)",
    )
    location = models.CharField(
        max_length=64,
        help_text="Location of the tournament (e.g., Tokyo, Osaka)",
    )

    # We store the year/month explicitly to easily identify the "season"
    year = models.PositiveIntegerField(
        help_text="Year of the tournament",
    )
    month = models.PositiveIntegerField(
        help_text="Month of the tournament",
    )

    start_date = models.ForeignKey(
        GameDate,
        on_delete=models.PROTECT,
        related_name="banzuke_starts",
        help_text="First day of the tournament",
    )
    end_date = models.ForeignKey(
        GameDate,
        on_delete=models.PROTECT,
        related_name="banzuke_ends",
        help_text="Last day of the tournament (Senshuraku)",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        help_text="Current status of the tournament",
    )

    class Meta:
        """Model metadata."""

        ordering = ["-year", "-month"]
        verbose_name = "Banzuke"
        verbose_name_plural = "Banzuke"
        constraints = [
            models.UniqueConstraint(
                fields=["year", "month"],
                name="unique_banzuke_season",
            ),
            models.CheckConstraint(
                condition=Q(month__gte=1) & Q(month__lte=12),
                name="banzuke_valid_month",
                violation_error_message="Month must be between 1 and 12.",
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.year} {self.name}"


class BanzukeEntry(models.Model):
    """
    Represents a Rikishi's entry in a specific Banzuke.

    This links a Rikishi to a Rank for a specific tournament and tracks
    their performance (wins, losses, etc.).
    """

    banzuke = models.ForeignKey(
        Banzuke,
        on_delete=models.PROTECT,
        related_name="entries",
        help_text="Tournament this entry belongs to",
    )
    rikishi = models.ForeignKey(
        Rikishi,
        on_delete=models.PROTECT,
        related_name="banzuke_entries",
        help_text="Wrestler",
    )
    rank = models.ForeignKey(
        Rank,
        on_delete=models.PROTECT,
        related_name="banzuke_entries",
        help_text="Rank held during this tournament",
    )

    # Performance
    wins = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of wins",
    )
    losses = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of losses",
    )
    absences = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of absences (fusenpai/kyujo)",
    )

    class Meta:
        """Model metadata."""

        verbose_name = "Banzuke Entry"
        verbose_name_plural = "Banzuke Entries"
        ordering = ["banzuke", "rank"]
        constraints = [
            models.UniqueConstraint(
                fields=["banzuke", "rikishi"],
                name="unique_rikishi_per_banzuke",
                violation_error_message=(
                    "Rikishi can only appear once in a Banzuke."
                ),
            ),
            models.UniqueConstraint(
                fields=["banzuke", "rank"],
                name="unique_rank_per_banzuke",
                violation_error_message=(
                    "Rank can only be held by one Rikishi per Banzuke."
                ),
            ),
            models.CheckConstraint(
                condition=(
                    Q(wins__lte=15) & Q(losses__lte=15) & Q(absences__lte=15)
                ),
                name="banzukeentry_valid_match_counts",
                violation_error_message=(
                    "Wins, losses, and absences cannot exceed 15."
                ),
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.banzuke} - {self.rikishi} ({self.rank})"

    @property
    def total_matches(self) -> int:
        """Return total number of matches (wins + losses + absences)."""
        return self.wins + self.losses + self.absences

    @property
    def record(self) -> str:
        """Return formatted win-loss record (e.g., '8-7' or '8-5-2')."""
        if self.absences:
            return f"{self.wins}-{self.losses}-{self.absences}"
        return f"{self.wins}-{self.losses}"
