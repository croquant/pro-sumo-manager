"""Database models for the core app."""

from django.db import models
from django.db.models import Q

from core.enums.country_enum import Country
from core.enums.jp_prefecture_enum import JPPrefecture


class Shusshin(models.Model):
    """Origin information for a sumo wrestler."""

    country_code = models.CharField(max_length=2, choices=Country.choices)
    jp_prefecture = models.CharField(
        max_length=5,
        choices=JPPrefecture.choices,
        blank=True,
        default="",
    )

    class Meta:
        """Model metadata."""

        ordering = ["country_code", "jp_prefecture"]
        verbose_name = "Shusshin"
        verbose_name_plural = "Shusshin"
        constraints = [
            models.CheckConstraint(
                name="jp_prefecture_required_only_for_jp",
                condition=(
                    (Q(country_code=Country.JP) & ~Q(jp_prefecture=""))
                    | (~Q(country_code=Country.JP) & Q(jp_prefecture=""))
                ),
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - simple string representation
        """Return a human-readable representation of the origin."""
        if self.jp_prefecture:
            return f"{self.country_code}-{self.jp_prefecture}"
        return self.country_code
