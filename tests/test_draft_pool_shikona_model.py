"""Tests for the DraftPoolShikona model."""

from django.test import TestCase

from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.models import DraftPoolShikona, Shikona


class DraftPoolShikonaModelTests(TestCase):
    """Tests for the DraftPoolShikona model."""

    def _make_shikona(self, transliteration: str = "Tsururyu") -> Shikona:
        """Create and return a Shikona instance."""
        return Shikona.objects.create(
            name="鶴龍",
            transliteration=transliteration,
            interpretation="Crane Dragon",
        )

    def test_str_returns_shikona_and_status(self) -> None:
        """Should return shikona string and status."""
        shikona = self._make_shikona()
        entry = DraftPoolShikona.objects.create(shikona=shikona)
        self.assertEqual(
            str(entry),
            f"{shikona} ({DraftPoolStatus.AVAILABLE})",
        )

    def test_default_status_is_available(self) -> None:
        """Should default to AVAILABLE status."""
        shikona = self._make_shikona()
        entry = DraftPoolShikona.objects.create(shikona=shikona)
        self.assertEqual(entry.status, DraftPoolStatus.AVAILABLE)

    def test_reserved_by_optional(self) -> None:
        """Should allow creating entry without a reserved_by user."""
        shikona = self._make_shikona()
        entry = DraftPoolShikona.objects.create(shikona=shikona)
        self.assertIsNone(entry.reserved_by)
        self.assertIsNone(entry.reserved_at)

    def test_one_to_one_with_shikona(self) -> None:
        """Should enforce one-to-one relationship with Shikona."""
        shikona = self._make_shikona()
        DraftPoolShikona.objects.create(shikona=shikona)
        self.assertEqual(
            shikona.draft_pool_entry.status, DraftPoolStatus.AVAILABLE
        )
