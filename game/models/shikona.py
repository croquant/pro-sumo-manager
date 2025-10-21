"""Ring name model for a sumo wrestler."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


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

    def __str__(self) -> str:
        """Return the ring name."""
        return f"{self.transliteration} ({self.name})"

    def clean(self) -> None:
        """
        Validate the Shikona instance.

        Raises:
            ValidationError: If the parent relationship creates a circular
                reference.

        """
        super().clean()
        self._validate_no_circular_parent()

    def _validate_no_circular_parent(self) -> None:
        """
        Ensure that setting a parent does not create a circular reference.

        A circular reference occurs when:
        1. A shikona is set as its own parent
        2. A shikona's parent chain eventually leads back to itself

        Raises:
            ValidationError: If a circular reference is detected.

        """
        if self.parent is None:
            return

        # Check direct self-reference
        if self.parent.pk == self.pk:
            raise ValidationError(
                {"parent": "A shikona cannot be its own parent."}
            )

        # Check for cycles in the parent chain
        visited = {self.pk}
        current = self.parent

        while current is not None:
            if current.pk in visited:
                raise ValidationError(
                    {
                        "parent": (
                            f"Setting {self.parent} as parent would create a "
                            "circular reference in the parent chain."
                        )
                    }
                )
            visited.add(current.pk)
            current = current.parent
