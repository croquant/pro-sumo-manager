"""Tests for the heya name selection setup flow."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from game.models import GameDate, Heya, Rikishi, Shikona
from game.services.shikona_service import ShikonaOption, ShikonaService
from libs.generators.shikona import ShikonaGenerationError
from libs.types.shikona import Shikona as ShikonaType

User = get_user_model()


def _mock_shikona(name: str, translit: str, interp: str) -> ShikonaType:
    """Create a mock Shikona type for testing."""
    return ShikonaType(
        shikona=name,
        transliteration=translit,
        interpretation=interp,
    )


class TestShikonaService(TestCase):
    """Tests for the ShikonaService."""

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_generate_shikona_options_returns_three_options(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that generate_shikona_options returns 3 unique options."""
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_single.side_effect = [
            _mock_shikona("大海", "Ōumi", "Great Sea"),
            _mock_shikona("若山", "Wakayama", "Young Mountain"),
            _mock_shikona("琴風", "Kotokaze", "Harp Wind"),
        ]

        options = ShikonaService.generate_shikona_options(count=3)
        self.assertEqual(len(options), 3)

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_generate_shikona_options_are_unique(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that generated options have unique names."""
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_single.side_effect = [
            _mock_shikona("大海", "Ōumi", "Great Sea"),
            _mock_shikona("若山", "Wakayama", "Young Mountain"),
            _mock_shikona("琴風", "Kotokaze", "Harp Wind"),
        ]

        options = ShikonaService.generate_shikona_options(count=3)
        names = [opt.name for opt in options]
        self.assertEqual(len(names), len(set(names)))

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_generate_shikona_options_have_all_fields(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that generated options have all required fields."""
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_single.side_effect = [
            _mock_shikona("大海", "Ōumi", "Great Sea"),
            _mock_shikona("若山", "Wakayama", "Young Mountain"),
            _mock_shikona("琴風", "Kotokaze", "Harp Wind"),
        ]

        options = ShikonaService.generate_shikona_options(count=3)
        for opt in options:
            self.assertTrue(opt.name)
            self.assertTrue(opt.transliteration)
            self.assertTrue(opt.interpretation)

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_create_shikona_from_option(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test creating a Shikona model from an option."""
        mock_gen = mock_gen_class.return_value
        mock_gen.generate_single.return_value = _mock_shikona(
            "大海", "Ōumi", "Great Sea"
        )

        options = ShikonaService.generate_shikona_options(count=1)
        option = options[0]
        shikona = ShikonaService.create_shikona_from_option(option)

        self.assertIsNotNone(shikona.pk)
        self.assertEqual(shikona.name, option.name)
        self.assertEqual(shikona.transliteration, option.transliteration)
        self.assertEqual(shikona.interpretation, option.interpretation)

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_generate_skips_duplicates(self, mock_gen_class: MagicMock) -> None:
        """Test that duplicate names are skipped."""
        mock_gen = mock_gen_class.return_value
        # First call returns duplicate, should be skipped
        mock_gen.generate_single.side_effect = [
            _mock_shikona("大海", "Ōumi", "Great Sea"),
            _mock_shikona("大海", "Ōumi", "Great Sea"),  # Duplicate
            _mock_shikona("若山", "Wakayama", "Young Mountain"),
            _mock_shikona("琴風", "Kotokaze", "Harp Wind"),
        ]

        options = ShikonaService.generate_shikona_options(count=3)
        self.assertEqual(len(options), 3)
        names = [opt.name for opt in options]
        self.assertEqual(len(names), len(set(names)))

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_generate_logs_warning_when_exhausted(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that warning is logged when fewer options than requested."""
        mock_gen = mock_gen_class.return_value
        # Return only duplicates after first option - exhausts max_attempts
        mock_gen.generate_single.side_effect = [
            _mock_shikona("大海", "Ōumi", "Great Sea"),
        ] + [
            _mock_shikona("大海", "Ōumi", "Great Sea")  # Duplicates
            for _ in range(20)
        ]

        with self.assertLogs(
            "game.services.shikona_service", level="WARNING"
        ) as cm:
            options = ShikonaService.generate_shikona_options(count=3)

        # Should only get 1 option due to duplicates exhausting attempts
        self.assertEqual(len(options), 1)
        # Should have logged warning about limited options
        self.assertTrue(any("Could only generate" in msg for msg in cm.output))

    @patch("game.services.shikona_service.ShikonaGenerator")
    def test_generate_handles_generation_errors(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Test that ShikonaGenerationError is caught and logged."""
        mock_gen = mock_gen_class.return_value
        # Mix of successful generations and errors
        mock_gen.generate_single.side_effect = [
            _mock_shikona("大海", "Ōumi", "Great Sea"),
            ShikonaGenerationError("API error"),
            _mock_shikona("若山", "Wakayama", "Young Mountain"),
            ShikonaGenerationError("API error"),
            _mock_shikona("琴風", "Kotokaze", "Harp Wind"),
        ]

        with self.assertLogs(
            "game.services.shikona_service", level="WARNING"
        ) as cm:
            options = ShikonaService.generate_shikona_options(count=3)

        # Should get 3 options despite errors
        self.assertEqual(len(options), 3)
        # Should have logged warnings about failed generations
        self.assertTrue(any("Failed to generate" in msg for msg in cm.output))


class TestSetupHeyaNameView(TestCase):
    """Tests for the setup_heya_name view."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    def test_unauthenticated_user_redirected_to_login(self) -> None:
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_authenticated_user_can_access_page(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that authenticated users without heya can access the page."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("options", response.context)

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_page_shows_three_options(self, mock_gen: MagicMock) -> None:
        """Test that the page displays 3 shikona options."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 200)
        options = response.context["options"]
        self.assertEqual(len(options), 3)

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_options_stored_in_session(self, mock_gen: MagicMock) -> None:
        """Test that options are stored in session for consistency."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_heya_name"))
        session = self.client.session
        self.assertIn("heya_options", session)
        self.assertEqual(len(session["heya_options"]), 3)

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_options_persist_across_page_visits(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that options don't change when visiting page multiple times."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # First visit
        self.client.get(reverse("setup_heya_name"))
        first_options = list(self.client.session["heya_options"])

        # Second visit - should return same options (from session)
        self.client.get(reverse("setup_heya_name"))
        second_options = list(self.client.session["heya_options"])

        self.assertEqual(first_options, second_options)
        # Generator should only be called once
        mock_gen.assert_called_once()

    def test_user_with_heya_redirected_to_draft_pool(self) -> None:
        """Test that users with heya but no rikishi go to draft pool."""
        # Create heya for user (no rikishi yet)
        shikona = Shikona.objects.create(
            name="大海",
            transliteration="Ōumi",
            interpretation="Great Sea",
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

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_post_creates_heya(self, mock_gen: MagicMock) -> None:
        """Test that POST creates a heya for the user."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST to select first option
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "0"},
        )

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)

        # User should now have a heya
        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, "heya"))
        self.assertIsNotNone(self.user.heya)

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_post_creates_heya_with_existing_game_date(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST uses existing game date when available."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        # Pre-create a game date
        game_date = GameDate.objects.create(year=5, month=3, day=15)

        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST to select second option
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "1"},
        )

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)

        # User should now have a heya with the existing game date
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.heya)
        self.assertEqual(self.user.heya.created_at, game_date)

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_post_without_selection_shows_error(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST without selection shows error."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST without selection
        response = self.client.post(reverse("setup_heya_name"), {})

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_post_with_invalid_selection_shows_error(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST with invalid selection shows error."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST with invalid selection
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "99"},
        )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_post_without_session_options_shows_error(self) -> None:
        """Test that POST without session options triggers error handling."""
        self.client.force_login(self.user)

        # POST directly without GET (no session options)
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "0"},
        )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_post_with_non_numeric_selection_shows_error(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST with non-numeric selection triggers ValueError."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST with non-numeric selection
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "abc"},
        )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))


class TestSetupHeyaNameEdgeCases(TestCase):
    """Tests for edge cases in heya name selection."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_post_creates_game_date_if_none_exists(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that POST initializes GameDate if none exists."""
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # Ensure no GameDate exists
        GameDate.objects.all().delete()
        self.assertEqual(GameDate.objects.count(), 0)

        # GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST to select first option
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "0"},
        )

        # Should succeed and create GameDate
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GameDate.objects.count(), 1)

        # User should have heya
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.heya)


class TestLimitedOptionsWarning(TestCase):
    """Tests for warning when options are limited."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_warning_shown_when_fewer_options_generated(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that warning is shown when fewer than 3 options generated."""
        # Mock the service to return only 2 options
        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))

        self.assertEqual(response.status_code, 200)
        # Check that warning message is shown
        messages = list(response.context["messages"])
        self.assertTrue(any("limited" in str(m).lower() for m in messages))


class TestIntegrityErrorHandling(TestCase):
    """Tests for IntegrityError handling during heya creation."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    @patch("game.views.ShikonaService.generate_shikona_options")
    def test_integrity_error_handled_gracefully(
        self, mock_gen: MagicMock
    ) -> None:
        """Test that IntegrityError from race condition is handled."""
        from django.db import IntegrityError

        mock_gen.return_value = [
            ShikonaOption("大海", "Ōumi", "Great Sea"),
            ShikonaOption("若山", "Wakayama", "Young Mountain"),
            ShikonaOption("琴風", "Kotokaze", "Harp Wind"),
        ]

        self.client.force_login(self.user)

        # GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # Mock Heya.objects.create to raise IntegrityError (simulating race)
        with patch(
            "game.views.Heya.objects.create",
            side_effect=IntegrityError("duplicate key"),
        ):
            response = self.client.post(
                reverse("setup_heya_name"),
                {"selected_option": "0"},
            )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

        # Session should be cleared to force regeneration
        session = self.client.session
        self.assertNotIn("heya_options", session)


class TestDashboardRedirect(TestCase):
    """Tests for dashboard redirect behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",  # noqa: S106
        )
        self.client = Client()

    def test_dashboard_redirects_user_without_heya(self) -> None:
        """Test that dashboard redirects users without heya to setup."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_dashboard_accessible_with_heya_and_rikishi(self) -> None:
        """Test that users with heya and rikishi can access dashboard."""
        # Create heya and rikishi for user
        heya_shikona = Shikona.objects.create(
            name="大海",
            transliteration="Ōumi",
            interpretation="Great Sea",
        )
        rikishi_shikona = Shikona.objects.create(
            name="若山",
            transliteration="Wakayama",
            interpretation="Young Mountain",
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
