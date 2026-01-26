"""Training session models for tracking rikishi stat development."""

from __future__ import annotations

from django.db import models

from game.models.rikishi import Rikishi


class TrainingSession(models.Model):
    """
    Represents a training session where a rikishi improves a stat.

    A training session records when a wrestler spent XP to improve
    one of their stats. It tracks the stat trained, the XP cost,
    and the stat values before and after training.
    """

    class Stat(models.TextChoices):
        """Available stats that can be trained."""

        STRENGTH = "strength", "Strength"
        TECHNIQUE = "technique", "Technique"
        BALANCE = "balance", "Balance"
        ENDURANCE = "endurance", "Endurance"
        MENTAL = "mental", "Mental"

    rikishi = models.ForeignKey(
        Rikishi,
        on_delete=models.CASCADE,
        related_name="training_sessions",
        help_text="The wrestler who trained",
    )

    stat = models.CharField(
        max_length=10,
        choices=Stat.choices,
        help_text="The stat that was trained",
    )

    xp_cost = models.PositiveIntegerField(
        help_text="XP spent on this training session",
    )

    stat_before = models.PositiveIntegerField(
        help_text="Stat value before training",
    )

    stat_after = models.PositiveIntegerField(
        help_text="Stat value after training",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the training occurred",
    )

    class Meta:
        """Model metadata."""

        ordering = ["-created_at"]
        verbose_name = "Training Session"
        verbose_name_plural = "Training Sessions"
        indexes = [
            models.Index(
                fields=["rikishi", "-created_at"],
                name="training_rikishi_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(xp_cost__gt=0),
                name="training_xp_cost_positive",
                violation_error_message="XP cost must be positive.",
            ),
            models.CheckConstraint(
                condition=models.Q(stat_after__gt=models.F("stat_before")),
                name="training_stat_increased",
                violation_error_message=(
                    "Stat after must be greater than stat before."
                ),
            ),
        ]

    def __str__(self) -> str:
        """Return a description of the training session."""
        return (
            f"{self.rikishi} trained {self.get_stat_display()} "
            f"({self.stat_before} -> {self.stat_after})"
        )
