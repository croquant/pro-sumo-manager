"""Draft pool shikona model for pre-generated ring names."""

from django.conf import settings
from django.db import models

from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.models.shikona import Shikona


class DraftPoolShikona(models.Model):
    """
    Pre-generated ring name available in the draft pool.

    A thin wrapper around a Shikona record that tracks availability
    in the draft pool. Supports reservation to prevent concurrent
    users from seeing the same entry.
    """

    shikona = models.OneToOneField(
        Shikona,
        on_delete=models.PROTECT,
        related_name="draft_pool_entry",
        help_text="The pre-generated ring name",
    )
    status = models.CharField(
        max_length=10,
        choices=DraftPoolStatus.choices,
        default=DraftPoolStatus.AVAILABLE,
        help_text="Current availability status",
    )
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_draft_shikona",
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

        verbose_name = "Draft Pool Shikona"
        verbose_name_plural = "Draft Pool Shikona"

    def __str__(self) -> str:
        """Return the shikona and status."""
        return f"{self.shikona} ({self.status})"
