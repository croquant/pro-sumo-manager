"""Tests for the draft pool setup flow."""

from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from game.models import GameDate, Heya, Rikishi, Shikona
from game.services.draft_pool_service import DraftPoolRikishi, DraftPoolService
from libs.types.rikishi import Rikishi as RikishiType
from libs.types.shikona import Shikona as ShikonaType
from libs.types.shusshin import Shusshin as ShusshinType

User = get_user_model()


def _mock_rikishi(
    name: str = "大海",
    translit: str = "Ōumi",
    interp: str = "Great Sea",
    country_code: str = "JP",
    jp_prefecture: str = "JP-13",
    potential: int = 45,
    strength: int = 3,
    technique: int = 2,
    balance: int = 2,
    endurance: int = 3,
    mental: int = 2,
) -> RikishiType:
    """Create a mock Rikishi type for testing."""
    return RikishiType(
        shikona=ShikonaType(
            shikona=name,
            transliteration=translit,
            interpretation=interp,
        ),
        shusshin=ShusshinType(
            country_code=country_code,
            jp_prefecture=jp_prefecture,
        ),
        potential=potential,
        current=12,
        strength=strength,
        technique=technique,
        balance=balance,
        endurance=endurance,
        mental=mental,
    )


class TestDraftPoolService(TestCase):
    """Tests for the DraftPoolService."""

    def test_get_potential_tier_limited(self) -> None:
        """Test potential tier mapping for Limited range."""
        self.assertEqual(DraftPoolService.get_potential_tier(5), "Limited")
        self.assertEqual(DraftPoolService.get_potential_tier(20), "Limited")

    def test_get_potential_tier_average(self) -> None:
        """Test potential tier mapping for Average range."""
        self.assertEqual(DraftPoolService.get_potential_tier(21), "Average")
        self.assertEqual(DraftPoolService.get_potential_tier(35), "Average")

    def test_get_potential_tier_promising(self) -> None:
        """Test potential tier mapping for Promising range."""
        self.assertEqual(DraftPoolService.get_potential_tier(36), "Promising")
        self.assertEqual(DraftPoolService.get_potential_tier(50), "Promising")

    def test_get_potential_tier_talented(self) -> None:
        """Test potential tier mapping for Talented range."""
        self.assertEqual(DraftPoolService.get_potential_tier(51), "Talented")
        self.assertEqual(DraftPoolService.get_potential_tier(70), "Talented")

    def test_get_potential_tier_exceptional(self) -> None:
        """Test potential tier mapping for Exceptional range."""
        self.assertEqual(DraftPoolService.get_potential_tier(71), "Exceptional")
        self.assertEqual(DraftPoolService.get_potential_tier(85), "Exceptional")

    def test_get_potential_tier_generational(self) -> None:
        """Test potential tier mapping for Generational range."""
        tier_86 = DraftPoolService.get_potential_tier(86)
        tier_100 = DraftPoolService.get_potential_tier(100)
        self.assertEqual(tier_86, "Generational")
        self.assertEqual(tier_100, "Generational")

    def test_get_potential_tier_above_max(self) -> None:
        """Test potential tier fallback for values above 100."""
        # Edge case: values > 100 should still return Generational
        self.assertEqual(
            DraftPoolService.get_potential_tier(101), "Generational"
        )

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_generate_draft_pool_returns_correct_count(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that generate_draft_pool returns correct count."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.side_effect = [
            _mock_rikishi("大海", "Ōumi", "Great Sea"),
            _mock_rikishi("若山", "Wakayama", "Young Mountain"),
            _mock_rikishi("琴風", "Kotokaze", "Harp Wind"),
            _mock_rikishi("朝日", "Asahi", "Morning Sun"),
            _mock_rikishi("雷電", "Raiden", "Thunder Lightning"),
            _mock_rikishi("北勝", "Hokushō", "Northern Victory"),
        ]

        pool = DraftPoolService.generate_draft_pool(count=6)
        self.assertEqual(len(pool), 6)

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_generate_draft_pool_wrestlers_are_unique(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that generated pool has unique wrestlers."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.side_effect = [
            _mock_rikishi("大海", "Ōumi", "Great Sea"),
            _mock_rikishi("若山", "Wakayama", "Young Mountain"),
            _mock_rikishi("琴風", "Kotokaze", "Harp Wind"),
        ]

        pool = DraftPoolService.generate_draft_pool(count=3)
        names = [r.shikona_name for r in pool]
        self.assertEqual(len(names), len(set(names)))

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_generate_draft_pool_skips_duplicates(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that duplicate names are skipped."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.side_effect = [
            _mock_rikishi("大海", "Ōumi", "Great Sea"),
            _mock_rikishi("大海", "Ōumi", "Great Sea"),  # Duplicate
            _mock_rikishi("若山", "Wakayama", "Young Mountain"),
            _mock_rikishi("琴風", "Kotokaze", "Harp Wind"),
        ]

        pool = DraftPoolService.generate_draft_pool(count=3)
        self.assertEqual(len(pool), 3)
        names = [r.shikona_name for r in pool]
        self.assertEqual(len(names), len(set(names)))

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_generate_draft_pool_logs_warning_when_exhausted(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that warning is logged when fewer wrestlers than requested."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.side_effect = [
            _mock_rikishi("大海", "Ōumi", "Great Sea"),
        ] + [_mock_rikishi("大海", "Ōumi", "Great Sea") for _ in range(20)]

        with self.assertLogs(
            "game.services.draft_pool_service", level="WARNING"
        ) as cm:
            pool = DraftPoolService.generate_draft_pool(count=3)

        self.assertEqual(len(pool), 1)
        self.assertTrue(any("Could only generate" in msg for msg in cm.output))

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_generate_draft_pool_handles_generation_errors(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that generation errors are caught and logged."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.side_effect = [
            _mock_rikishi("大海", "Ōumi", "Great Sea"),
            Exception("API error"),
            _mock_rikishi("若山", "Wakayama", "Young Mountain"),
            Exception("API error"),
            _mock_rikishi("琴風", "Kotokaze", "Harp Wind"),
        ]

        with self.assertLogs(
            "game.services.draft_pool_service", level="WARNING"
        ) as cm:
            pool = DraftPoolService.generate_draft_pool(count=3)

        self.assertEqual(len(pool), 3)
        self.assertTrue(any("Failed to generate" in msg for msg in cm.output))

    def test_serialize_for_session(self) -> None:
        """Test that pool is correctly serialized for session storage."""
        pool = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        serialized = DraftPoolService.serialize_for_session(pool)
        self.assertIsInstance(serialized, list)
        self.assertEqual(len(serialized), 1)
        self.assertEqual(serialized[0]["shikona_name"], "大海")
        self.assertEqual(serialized[0]["potential_tier"], "Promising")

    def test_deserialize_from_session(self) -> None:
        """Test that pool is correctly deserialized from session storage."""
        data: list[dict[str, Any]] = [
            {
                "shikona_name": "大海",
                "shikona_transliteration": "Ōumi",
                "shikona_interpretation": "Great Sea",
                "shusshin_country_code": "JP",
                "shusshin_jp_prefecture": "JP-13",
                "shusshin_display": "Tokyo, Japan",
                "potential": 45,
                "potential_tier": "Promising",
                "strength": 3,
                "technique": 2,
                "balance": 2,
                "endurance": 3,
                "mental": 2,
            }
        ]

        pool = DraftPoolService.deserialize_from_session(data)
        self.assertIsInstance(pool, list)
        self.assertEqual(len(pool), 1)
        self.assertIsInstance(pool[0], DraftPoolRikishi)
        self.assertEqual(pool[0].shikona_name, "大海")
        self.assertEqual(pool[0].potential_tier, "Promising")

    def test_serialize_deserialize_roundtrip(self) -> None:
        """Test that serialization/deserialization is lossless."""
        original = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        serialized = DraftPoolService.serialize_for_session(original)
        deserialized = DraftPoolService.deserialize_from_session(serialized)

        self.assertEqual(original[0].shikona_name, deserialized[0].shikona_name)
        self.assertEqual(original[0].potential, deserialized[0].potential)
        self.assertEqual(original[0].strength, deserialized[0].strength)

    def test_create_rikishi_from_selection(self) -> None:
        """Test creating a Rikishi model from selection."""
        # Create heya for test
        shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        heya = Heya.objects.create(
            name=shikona,
            created_at=game_date,
            owner=user,
        )

        selection: dict[str, Any] = {
            "shikona_name": "大海",
            "shikona_transliteration": "Ōumi",
            "shikona_interpretation": "Great Sea",
            "shusshin_country_code": "JP",
            "shusshin_jp_prefecture": "JP-13",
            "potential": 45,
            "strength": 3,
            "technique": 2,
            "balance": 2,
            "endurance": 3,
            "mental": 2,
        }

        rikishi = DraftPoolService.create_rikishi_from_selection(
            selection, heya
        )

        self.assertIsNotNone(rikishi.pk)
        self.assertEqual(rikishi.shikona.name, "大海")
        self.assertEqual(rikishi.heya, heya)
        self.assertEqual(rikishi.potential, 45)
        self.assertEqual(rikishi.strength, 3)


class TestSetupDraftPoolView(TestCase):
    """Tests for the setup_draft_pool view."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        self.game_date = GameDate.objects.create(year=1, month=1, day=1)
        self.heya = Heya.objects.create(
            name=self.shikona,
            created_at=self.game_date,
            owner=self.user,
        )
        self.client = Client()

    def test_unauthenticated_user_redirected_to_login(self) -> None:
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse("setup_draft_pool"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_authenticated_user_with_heya_can_access(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that users with heya but no rikishi can access the page."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("pool", response.context)

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_pool_stored_in_session(self, mock_gen: MagicMock) -> None:
        """Test that pool is stored in session for consistency."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))
        session = self.client.session
        self.assertIn("draft_pool", session)
        self.assertEqual(len(session["draft_pool"]), 1)

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_pool_persists_across_page_visits(
        self, mock_gen: MagicMock
    ) -> None:
        """Test pool consistency across page visits."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)

        # First visit
        self.client.get(reverse("setup_draft_pool"))
        first_pool = list(self.client.session["draft_pool"])

        # Second visit - should return same pool (from session)
        self.client.get(reverse("setup_draft_pool"))
        second_pool = list(self.client.session["draft_pool"])

        self.assertEqual(first_pool, second_pool)
        mock_gen.assert_called_once()

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_post_creates_rikishi(self, mock_gen: MagicMock) -> None:
        """Test that POST creates a rikishi for the heya."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)

        # First GET to generate pool
        self.client.get(reverse("setup_draft_pool"))

        # POST to select first wrestler
        response = self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "0"},
        )

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))

        # Heya should now have a rikishi
        self.assertTrue(self.heya.rikishi.exists())
        rikishi = self.heya.rikishi.first()
        self.assertIsNotNone(rikishi)
        self.assertEqual(rikishi.shikona.name, "大海")

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_post_without_selection_shows_error(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST without selection shows error."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        response = self.client.post(reverse("setup_draft_pool"), {})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_post_with_invalid_selection_shows_error(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST with invalid selection shows error."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        response = self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "99"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))

    def test_post_without_session_pool_shows_error(self) -> None:
        """Test that POST without session pool triggers error handling."""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "0"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_post_with_non_numeric_selection_shows_error(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST with non-numeric selection triggers ValueError."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        response = self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "abc"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))


class TestDecoratorHelperFunctions(TestCase):
    """Tests for decorator helper functions."""

    def test_user_has_rikishi_returns_false_for_user_without_heya(self) -> None:
        """Test _user_has_rikishi returns False when user has no heya."""
        from game.decorators import _user_has_rikishi

        # Create a user without a heya
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        # User has no heya, so accessing user.heya raises AttributeError
        self.assertFalse(_user_has_rikishi(user))


class TestDraftPoolDecoratorBehavior(TestCase):
    """Tests for decorator behavior on draft pool view."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    def test_user_without_heya_redirected_to_heya_name(self) -> None:
        """Test that users without heya are redirected to heya name setup."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_user_with_rikishi_redirected_to_dashboard(self) -> None:
        """Test that users with rikishi are redirected to dashboard."""
        # Create heya and rikishi
        heya_shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        rikishi_shikona = Shikona.objects.create(
            name="大海",
            transliteration="Ōumi",
            interpretation="Great Sea",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        heya = Heya.objects.create(
            name=heya_shikona,
            created_at=game_date,
            owner=self.user,
        )
        Rikishi.objects.create(
            shikona=rikishi_shikona,
            heya=heya,
            potential=45,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))


class TestSetupInProgressDecoratorUpdate(TestCase):
    """Tests for updated setup_in_progress decorator behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    def test_user_with_heya_no_rikishi_redirected_to_draft_pool(self) -> None:
        """Test that users with heya but no rikishi go to draft pool."""
        # Create heya without rikishi
        shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        Heya.objects.create(
            name=shikona,
            created_at=game_date,
            owner=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))

    def test_user_with_heya_and_rikishi_redirected_to_dashboard(self) -> None:
        """Test that users with heya and rikishi go to dashboard."""
        # Create heya and rikishi
        heya_shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        rikishi_shikona = Shikona.objects.create(
            name="大海",
            transliteration="Ōumi",
            interpretation="Great Sea",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        heya = Heya.objects.create(
            name=heya_shikona,
            created_at=game_date,
            owner=self.user,
        )
        Rikishi.objects.create(
            shikona=rikishi_shikona,
            heya=heya,
            potential=45,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))


class TestHeyaRequiredDecoratorUpdate(TestCase):
    """Tests for updated heya_required decorator behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    def test_user_with_heya_no_rikishi_redirected_to_draft_pool(self) -> None:
        """Test that dashboard redirects to draft pool if no rikishi."""
        # Create heya without rikishi
        shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        Heya.objects.create(
            name=shikona,
            created_at=game_date,
            owner=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))

    def test_user_with_heya_and_rikishi_can_access_dashboard(self) -> None:
        """Test that users with heya and rikishi can access dashboard."""
        # Create heya and rikishi
        heya_shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        rikishi_shikona = Shikona.objects.create(
            name="大海",
            transliteration="Ōumi",
            interpretation="Great Sea",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        heya = Heya.objects.create(
            name=heya_shikona,
            created_at=game_date,
            owner=self.user,
        )
        Rikishi.objects.create(
            shikona=rikishi_shikona,
            heya=heya,
            potential=45,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


class TestLimitedPoolWarning(TestCase):
    """Tests for warning when pool is limited."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        Heya.objects.create(
            name=shikona,
            created_at=game_date,
            owner=self.user,
        )
        self.client = Client()

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_warning_shown_when_fewer_wrestlers_generated(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that warning is shown when fewer than 3 wrestlers generated."""
        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            ),
            DraftPoolRikishi(
                shikona_name="若山",
                shikona_transliteration="Wakayama",
                shikona_interpretation="Young Mountain",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-27",
                shusshin_display="Osaka, Japan",
                potential=35,
                potential_tier="Average",
                strength=2,
                technique=3,
                balance=2,
                endurance=2,
                mental=3,
            ),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))

        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("limited" in str(m).lower() for m in messages))


class TestIntegrityErrorHandlingDraft(TestCase):
    """Tests for IntegrityError handling during rikishi creation."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.shikona = Shikona.objects.create(
            name="琴風",
            transliteration="Kotokaze",
            interpretation="Harp Wind",
        )
        self.game_date = GameDate.objects.create(year=1, month=1, day=1)
        self.heya = Heya.objects.create(
            name=self.shikona,
            created_at=self.game_date,
            owner=self.user,
        )
        self.client = Client()

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_integrity_error_handled_gracefully(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that IntegrityError from race condition is handled."""
        from django.db import IntegrityError

        mock_gen.return_value = [
            DraftPoolRikishi(
                shikona_name="大海",
                shikona_transliteration="Ōumi",
                shikona_interpretation="Great Sea",
                shusshin_country_code="JP",
                shusshin_jp_prefecture="JP-13",
                shusshin_display="Tokyo, Japan",
                potential=45,
                potential_tier="Promising",
                strength=3,
                technique=2,
                balance=2,
                endurance=3,
                mental=2,
            )
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        with patch(
            "game.views.DraftPoolService.create_rikishi_from_selection",
            side_effect=IntegrityError("duplicate key"),
        ):
            response = self.client.post(
                reverse("setup_draft_pool"),
                {"selected_wrestler": "0"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_draft_pool"))

        session = self.client.session
        self.assertNotIn("draft_pool", session)
