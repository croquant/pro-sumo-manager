"""Ring name model for a sumo wrestler."""

from django.db import models


class Shikona(models.Model):
    """Ring name for a sumo wrestler."""

    name = models.CharField(max_length=8, unique=True)
    transliteration = models.CharField(max_length=32, unique=True)
    interpretation = models.CharField(max_length=64)

    class Meta:
        """Model metadata."""

        ordering = ["transliteration"]
        verbose_name = "Shikona"
        verbose_name_plural = "Shikona"
        unique_together = ("name", "transliteration")

    def __str__(self) -> str:
        """Return the ring name."""
        return f"{self.transliteration} ({self.name})"
