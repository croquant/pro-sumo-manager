"""Tests for draft pool models."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, models, transaction
from django.test import TestCase
from django.utils import timezone

from game.enums.country_enum import Country
from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.enums.jp_prefecture_enum import JPPrefecture
from game.models import DraftPoolShikona, DraftPoolWrestler, Shikona

User = get_user_model()


class DraftPoolShikonaModelTests(TestCase):
    """Tests for the DraftPoolShikona model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.shikona = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )

    def test_create_with_defaults(self) -> None:
        """Should create with available status and no reservation."""
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        self.assertEqual(entry.status, DraftPoolStatus.AVAILABLE)
        self.assertIsNone(entry.reserved_by)
        self.assertIsNone(entry.reserved_at)
        self.assertIsNotNone(entry.created_at)

    def test_str_includes_shikona_and_status(self) -> None:
        """Should include shikona and status in string."""
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        result = str(entry)
        self.assertIn("Tsururyu", result)
        self.assertIn("available", result)

    def test_reserve_entry(self) -> None:
        """Should allow reserving with user and timestamp."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        entry.status = DraftPoolStatus.RESERVED
        entry.reserved_by = user
        entry.reserved_at = timezone.now()
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.status, DraftPoolStatus.RESERVED)
        self.assertEqual(entry.reserved_by, user)
        self.assertIsNotNone(entry.reserved_at)

    def test_consume_entry(self) -> None:
        """Should allow consuming an entry."""
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        entry.status = DraftPoolStatus.CONSUMED
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.status, DraftPoolStatus.CONSUMED)

    def test_fail_duplicate_shikona(self) -> None:
        """Should prevent two pool entries for the same shikona."""
        DraftPoolShikona.objects.create(shikona=self.shikona)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolShikona.objects.create(shikona=self.shikona)

    def test_shikona_protected_on_delete(self) -> None:
        """Should prevent deleting a shikona that has a pool entry."""
        DraftPoolShikona.objects.create(shikona=self.shikona)
        with self.assertRaises(models.ProtectedError), transaction.atomic():
            self.shikona.delete()

    def test_user_deletion_nullifies_reservation(self) -> None:
        """Should set reserved_by to null when user is deleted."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
            status=DraftPoolStatus.RESERVED,
            reserved_by=user,
            reserved_at=timezone.now(),
        )
        user.delete()

        entry.refresh_from_db()
        self.assertIsNone(entry.reserved_by)


class DraftPoolWrestlerModelTests(TestCase):
    """Tests for the DraftPoolWrestler model."""

    def _create_pool_shikona(
        self, name: str, transliteration: str, interpretation: str
    ) -> DraftPoolShikona:
        """Create a Shikona and DraftPoolShikona pair."""
        shikona = Shikona.objects.create(
            name=name,
            transliteration=transliteration,
            interpretation=interpretation,
        )
        return DraftPoolShikona.objects.create(shikona=shikona)

    def setUp(self) -> None:
        """Set up test data."""
        self.pool_shikona = self._create_pool_shikona(
            "鶴龍", "Tsururyu", "Crane Dragon"
        )
        self.valid_kwargs: dict[str, object] = {
            "draft_pool_shikona": self.pool_shikona,
            "country_code": Country.JP,
            "jp_prefecture": JPPrefecture.TOKYO,
            "potential": 50,
            "strength": 10,
            "technique": 8,
            "balance": 7,
            "endurance": 6,
            "mental": 5,
            "scout_report": "A promising wrestler from Tokyo.",
        }

    def test_create_with_valid_data(self) -> None:
        """Should create a wrestler with all required fields."""
        wrestler = DraftPoolWrestler.objects.create(**self.valid_kwargs)
        self.assertEqual(wrestler.status, DraftPoolStatus.AVAILABLE)
        self.assertIsNone(wrestler.reserved_by)
        self.assertIsNone(wrestler.reserved_at)
        self.assertIsNotNone(wrestler.created_at)
        self.assertEqual(wrestler.potential, 50)
        self.assertEqual(wrestler.strength, 10)
        self.assertEqual(
            wrestler.scout_report,
            "A promising wrestler from Tokyo.",
        )

    def test_str_includes_shikona_and_status(self) -> None:
        """Should include shikona and status in string."""
        wrestler = DraftPoolWrestler.objects.create(**self.valid_kwargs)
        result = str(wrestler)
        self.assertIn("Tsururyu", result)
        self.assertIn("available", result)

    def test_non_jp_country_with_empty_prefecture(self) -> None:
        """Should allow non-JP country with empty prefecture."""
        pool_shikona = self._create_pool_shikona(
            "白鳳", "Hakuhou", "White Phoenix"
        )
        wrestler = DraftPoolWrestler.objects.create(
            draft_pool_shikona=pool_shikona,
            country_code=Country.US,
            jp_prefecture="",
            potential=40,
            strength=5,
            technique=5,
            balance=5,
            endurance=5,
            mental=5,
            scout_report="An American wrestler.",
        )
        self.assertEqual(wrestler.country_code, Country.US)

    def test_fail_jp_without_prefecture(self) -> None:
        """Should fail for JP country without prefecture."""
        pool_shikona = self._create_pool_shikona(
            "白鳳", "Hakuhou", "White Phoenix"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(
                draft_pool_shikona=pool_shikona,
                country_code=Country.JP,
                jp_prefecture="",
                potential=40,
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                scout_report="Missing prefecture.",
            )

    def test_fail_non_jp_with_prefecture(self) -> None:
        """Should fail for non-JP country with prefecture."""
        pool_shikona = self._create_pool_shikona(
            "白鳳", "Hakuhou", "White Phoenix"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(
                draft_pool_shikona=pool_shikona,
                country_code=Country.US,
                jp_prefecture=JPPrefecture.TOKYO,
                potential=40,
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                scout_report="Invalid prefecture.",
            )

    def test_fail_strength_below_min(self) -> None:
        """Should fail if strength is below minimum."""
        self.valid_kwargs["strength"] = 0
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_strength_above_max(self) -> None:
        """Should fail if strength exceeds maximum."""
        self.valid_kwargs["strength"] = 21
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_potential_below_min(self) -> None:
        """Should fail if potential is below 5."""
        self.valid_kwargs["potential"] = 4
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_potential_above_max(self) -> None:
        """Should fail if potential exceeds 100."""
        self.valid_kwargs["potential"] = 101
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_duplicate_pool_shikona(self) -> None:
        """Should prevent two wrestlers for the same pool shikona."""
        DraftPoolWrestler.objects.create(**self.valid_kwargs)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_reserve_wrestler(self) -> None:
        """Should allow reserving with user and timestamp."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        wrestler = DraftPoolWrestler.objects.create(**self.valid_kwargs)
        wrestler.status = DraftPoolStatus.RESERVED
        wrestler.reserved_by = user
        wrestler.reserved_at = timezone.now()
        wrestler.save()

        wrestler.refresh_from_db()
        self.assertEqual(wrestler.status, DraftPoolStatus.RESERVED)
        self.assertEqual(wrestler.reserved_by, user)
        self.assertIsNotNone(wrestler.reserved_at)

    def test_pool_shikona_protected_on_delete(self) -> None:
        """Should prevent deleting a pool shikona that has a wrestler."""
        DraftPoolWrestler.objects.create(**self.valid_kwargs)
        with self.assertRaises(models.ProtectedError), transaction.atomic():
            self.pool_shikona.delete()
