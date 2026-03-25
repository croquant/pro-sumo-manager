"""Tests for the DraftPoolWrestler model."""

from django.test import TestCase

from game.enums.country_enum import Country
from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.models import DraftPoolShikona, DraftPoolWrestler, Shikona


def _make_draft_pool_shikona(
    transliteration: str = "Tsururyu",
) -> DraftPoolShikona:
    """Create and return a DraftPoolShikona instance."""
    shikona = Shikona.objects.create(
        name="鶴龍",
        transliteration=transliteration,
        interpretation="Crane Dragon",
    )
    return DraftPoolShikona.objects.create(shikona=shikona)


def _make_wrestler(
    draft_pool_shikona: DraftPoolShikona | None = None,
) -> DraftPoolWrestler:
    """Create and return a DraftPoolWrestler instance."""
    if draft_pool_shikona is None:
        draft_pool_shikona = _make_draft_pool_shikona()
    return DraftPoolWrestler.objects.create(
        draft_pool_shikona=draft_pool_shikona,
        country_code=Country.US,
        jp_prefecture="",
        potential=50,
        strength=10,
        technique=10,
        balance=10,
        endurance=10,
        mental=10,
        scout_report="A promising newcomer.",
    )


class DraftPoolWrestlerModelTests(TestCase):
    """Tests for the DraftPoolWrestler model."""

    def test_str_returns_shikona_and_status(self) -> None:
        """Should return shikona string and status."""
        wrestler = _make_wrestler()
        shikona = wrestler.draft_pool_shikona.shikona
        self.assertEqual(
            str(wrestler),
            f"{shikona} ({DraftPoolStatus.AVAILABLE})",
        )

    def test_default_status_is_available(self) -> None:
        """Should default to AVAILABLE status."""
        wrestler = _make_wrestler()
        self.assertEqual(wrestler.status, DraftPoolStatus.AVAILABLE)

    def test_reserved_by_optional(self) -> None:
        """Should allow creating entry without a reserved_by user."""
        wrestler = _make_wrestler()
        self.assertIsNone(wrestler.reserved_by)
        self.assertIsNone(wrestler.reserved_at)

    def test_one_to_one_with_draft_pool_shikona(self) -> None:
        """Should enforce one-to-one relationship with DraftPoolShikona."""
        draft_pool_shikona = _make_draft_pool_shikona("Hakuhou")
        wrestler = _make_wrestler(draft_pool_shikona)
        self.assertEqual(draft_pool_shikona.wrestler, wrestler)
