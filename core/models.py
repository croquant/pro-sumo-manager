"""Database models for the core app."""

from django.db import models
from django.db.models import Q

from core.enums.country_enum import Country
from core.enums.jp_prefecture_enum import JPPrefecture


class Shusshin(models.Model):
    country_code = models.CharField(max_length=2, choices=Country.choices)
    jp_prefecture = models.CharField(
        max_length=5, choices=JPPrefecture.choices, blank=True, default=""
    )

    class Meta:
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
