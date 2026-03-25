"""Draft pool wrestler model for pre-generated wrestlers."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from game.enums.country_enum import Country
from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.enums.jp_prefecture_enum import JPPrefecture
from game.models.draft_pool_shikona import DraftPoolShikona
from libs.constants import (
    MAX_POTENTIAL,
    MAX_STAT_VALUE,
    MIN_POTENTIAL,
    MIN_STAT_VALUE,
)


class DraftPoolWrestler(models.Model):
    """
    Pre-generated wrestler available in the draft pool.

    A flat staging record containing all data needed to create a
    Rikishi when a player drafts this wrestler. Stats and potential
    are hidden from the player; only the scout report is shown.
    """

    # Identity
    draft_pool_shikona = models.OneToOneField(
        DraftPoolShikona,
        on_delete=models.PROTECT,
        related_name="wrestler",
        help_text="Ring name for this wrestler",
    )

    # Origin (resolved to Shusshin via get_or_create at draft time)
    country_code = models.CharField(
        max_length=2,
        choices=Country.choices,
        help_text="Country of origin (ISO 3166-1 alpha-2)",
    )
    jp_prefecture = models.CharField(
        max_length=5,
        choices=JPPrefecture.choices,
        blank=True,
        default="",
        help_text="Japanese prefecture (required if country is JP)",
    )

    # Stats (hidden from player)
    potential = models.PositiveIntegerField(
        help_text="Maximum total stat points",
    )
    strength = models.PositiveIntegerField(
        help_text="Physical power and pushing ability",
    )
    technique = models.PositiveIntegerField(
        help_text="Technical skill",
    )
    balance = models.PositiveIntegerField(
        help_text="Stability and footing",
    )
    endurance = models.PositiveIntegerField(
        help_text="Stamina",
    )
    mental = models.PositiveIntegerField(
        help_text="Mental fortitude",
    )

    # Player-facing
    scout_report = models.TextField(
        help_text="LLM-generated narrative about this wrestler",
    )

    # Lifecycle
    status = models.CharField(
        max_length=10,
        choices=DraftPoolStatus.choices,
        default=DraftPoolStatus.AVAILABLE,
        db_index=True,
        help_text="Current availability status",
    )
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_draft_wrestlers",
        help_text="User who has reserved this entry",
    )
    reserved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this entry was reserved",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata."""

        verbose_name = "Draft Pool Wrestler"
        verbose_name_plural = "Draft Pool Wrestlers"
        constraints = [
            # Stat range constraints
            models.CheckConstraint(
                condition=Q(strength__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_strength_min",
                violation_error_message=(
                    f"Strength must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(strength__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_strength_max",
                violation_error_message=(
                    f"Strength cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(technique__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_technique_min",
                violation_error_message=(
                    f"Technique must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(technique__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_technique_max",
                violation_error_message=(
                    f"Technique cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(balance__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_balance_min",
                violation_error_message=(
                    f"Balance must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(balance__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_balance_max",
                violation_error_message=(
                    f"Balance cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(endurance__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_endurance_min",
                violation_error_message=(
                    f"Endurance must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(endurance__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_endurance_max",
                violation_error_message=(
                    f"Endurance cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(mental__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_mental_min",
                violation_error_message=(
                    f"Mental must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(mental__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_mental_max",
                violation_error_message=(
                    f"Mental cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            # Potential range constraint
            models.CheckConstraint(
                condition=(
                    Q(potential__gte=MIN_POTENTIAL)
                    & Q(potential__lte=MAX_POTENTIAL)
                ),
                name="draft_pool_wrestler_potential_range",
                violation_error_message=(
                    f"Potential must be between {MIN_POTENTIAL}"
                    f" and {MAX_POTENTIAL}."
                ),
            ),
            # Shusshin constraint (mirroring Shusshin model)
            models.CheckConstraint(
                name="draft_pool_wrestler_jp_prefecture",
                condition=(
                    (Q(country_code=Country.JP) & ~Q(jp_prefecture=""))
                    | (~Q(country_code=Country.JP) & Q(jp_prefecture=""))
                ),
                violation_error_message=(
                    "Japanese wrestlers require a prefecture;"
                    " non-Japanese wrestlers must not have one."
                ),
            ),
        ]

    def __str__(self) -> str:
        """Return the wrestler's ring name and status."""
        return f"{self.draft_pool_shikona.shikona} ({self.status})"
