"""Ring name model for a sumo wrestler."""

from __future__ import annotations

from django.db import models
from django.db.models import CheckConstraint, F, Q


class Shikona(models.Model):
    """Ring name for a sumo wrestler."""

    name = models.CharField(max_length=8, unique=True)
    transliteration = models.CharField(max_length=32, unique=True)
    interpretation = models.CharField(max_length=64)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        help_text=(
            "Optional parent shikona representing name lineage or evolution. "
            "In sumo tradition, wrestlers may adopt names honoring previous "
            "legendary wrestlers, or when a wrestler retires and becomes an "
            "oyakata (stable master), their former ring name may be inherited "
            "by a successor. This field tracks such historical relationships."
        ),
    )

    class Meta:
        """Model metadata."""

        ordering = ["transliteration"]
        verbose_name = "Shikona"
        verbose_name_plural = "Shikona"
        unique_together = ("name", "transliteration")
        constraints = [
            CheckConstraint(
                condition=Q(parent__isnull=True) | ~Q(parent=F("id")),
                name="shikona_parent_not_self",
                violation_error_message="A shikona cannot be its own parent.",
            ),
        ]

    def __str__(self) -> str:
        """Return the ring name."""
        return f"{self.transliteration} ({self.name})"
