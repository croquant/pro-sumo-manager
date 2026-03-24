"""Draft pool status choices."""

from django.db import models


class DraftPoolStatus(models.TextChoices):
    """Status choices for draft pool entries."""

    AVAILABLE = "available", "Available"
    RESERVED = "reserved", "Reserved"
    CONSUMED = "consumed", "Consumed"
