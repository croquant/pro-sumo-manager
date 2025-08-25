"""Origin model for sumo wrestlers."""

from django.db import models
from django.db.models import Q

from game.enums import Country, JPPrefecture


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
            models.UniqueConstraint(
                fields=["country_code"],
                condition=~Q(country_code=Country.JP),
                name="unique_shusshin_country_except_japan",
            ),
            models.UniqueConstraint(
                fields=["jp_prefecture"],
                condition=Q(country_code=Country.JP),
                name="unique_shusshin_jp_prefecture",
            ),
        ]

    def __str__(self) -> str:
        """Return a human-readable representation of the origin."""
        if self.country_code == Country.JP:
            return JPPrefecture(self.jp_prefecture).label
        return Country(self.country_code).label
