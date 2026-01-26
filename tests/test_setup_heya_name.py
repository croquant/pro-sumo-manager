"""Tests for the heya name selection setup flow."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from game.models import GameDate, Heya, Shikona
from game.services.shikona_service import ShikonaService

User = get_user_model()


class TestShikonaService(TestCase):
    """Tests for the ShikonaService."""

    def test_generate_shikona_options_returns_three_options(self) -> None:
        """Test that generate_shikona_options returns 3 unique options."""
        options = ShikonaService.generate_shikona_options(count=3)
        self.assertEqual(len(options), 3)

    def test_generate_shikona_options_are_unique(self) -> None:
        """Test that generated options have unique names."""
        options = ShikonaService.generate_shikona_options(count=3)
        names = [opt.name for opt in options]
        self.assertEqual(len(names), len(set(names)))

    def test_generate_shikona_options_have_all_fields(self) -> None:
        """Test that generated options have all required fields."""
        options = ShikonaService.generate_shikona_options(count=3)
        for opt in options:
            self.assertTrue(opt.name)
            self.assertTrue(opt.transliteration)
            self.assertTrue(opt.interpretation)

    def test_create_shikona_from_option(self) -> None:
        """Test creating a Shikona model from an option."""
        options = ShikonaService.generate_shikona_options(count=1)
        option = options[0]
        shikona = ShikonaService.create_shikona_from_option(option)

        self.assertIsNotNone(shikona.pk)
        self.assertEqual(shikona.name, option.name)
        self.assertEqual(shikona.transliteration, option.transliteration)
        self.assertEqual(shikona.interpretation, option.interpretation)


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

    def test_authenticated_user_can_access_page(self) -> None:
        """Test that authenticated users without heya can access the page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("options", response.context)

    def test_page_shows_three_options(self) -> None:
        """Test that the page displays 3 shikona options."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 200)
        options = response.context["options"]
        self.assertEqual(len(options), 3)

    def test_options_stored_in_session(self) -> None:
        """Test that options are stored in session for consistency."""
        self.client.force_login(self.user)
        self.client.get(reverse("setup_heya_name"))
        session = self.client.session
        self.assertIn("heya_options", session)
        self.assertEqual(len(session["heya_options"]), 3)

    def test_options_persist_across_page_visits(self) -> None:
        """Test that options don't change when visiting page multiple times."""
        self.client.force_login(self.user)

        # First visit
        self.client.get(reverse("setup_heya_name"))
        first_options = list(self.client.session["heya_options"])

        # Second visit - should return same options
        self.client.get(reverse("setup_heya_name"))
        second_options = list(self.client.session["heya_options"])

        self.assertEqual(first_options, second_options)

    def test_user_with_heya_redirected_to_dashboard(self) -> None:
        """Test that users with heya are redirected away from setup."""
        # Create heya for user
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
        self.assertEqual(response.url, reverse("dashboard"))

    def test_post_creates_heya(self) -> None:
        """Test that POST creates a heya for the user."""
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

    def test_post_creates_heya_with_existing_game_date(self) -> None:
        """Test that POST uses existing game date when available."""
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

    def test_post_without_selection_shows_error(self) -> None:
        """Test that POST without selection shows error."""
        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST without selection
        response = self.client.post(reverse("setup_heya_name"), {})

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_post_with_invalid_selection_shows_error(self) -> None:
        """Test that POST with invalid selection shows error."""
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
        """Test that POST without session options triggers KeyError handling."""
        self.client.force_login(self.user)

        # POST directly without GET (no session options)
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "0"},
        )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_post_with_non_numeric_selection_shows_error(self) -> None:
        """Test that POST with non-numeric selection triggers ValueError."""
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

    def test_post_with_non_integer_selection_shows_error(self) -> None:
        """Test that POST with non-integer selection triggers ValueError."""
        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST with non-integer value (triggers ValueError)
        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "not_a_number"},
        )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_post_without_session_options_shows_error(self) -> None:
        """Test that POST without session options triggers KeyError."""
        self.client.force_login(self.user)

        # Skip GET - directly POST without session (triggers KeyError on index)
        # We need to manually set an empty session state
        session = self.client.session
        session["heya_options"] = []  # Empty list causes IndexError
        session.save()

        response = self.client.post(
            reverse("setup_heya_name"),
            {"selected_option": "0"},
        )

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_post_creates_game_date_if_none_exists(self) -> None:
        """Test that POST initializes GameDate if none exists."""
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


class TestShikonaServiceExhaustion(TestCase):
    """Tests for ShikonaService exhaustion edge case."""

    def test_generate_returns_fewer_when_combinations_exhausted(self) -> None:
        """Test that generation returns fewer options when names exhausted."""
        from game.services.shikona_service import (
            SHIKONA_PREFIXES,
            SHIKONA_SUFFIXES,
        )

        # Create all possible combinations in database
        # Track used transliterations since they must be unique
        used_translit: set[str] = set()
        for prefix in SHIKONA_PREFIXES:
            for suffix in SHIKONA_SUFFIXES:
                kanji = prefix[0] + suffix[0]
                romaji = prefix[1] + suffix[1]
                meaning = f"{prefix[2]} {suffix[2]}"
                # Skip if transliteration already used (some prefixes share)
                if romaji in used_translit:
                    continue
                used_translit.add(romaji)
                Shikona.objects.create(
                    name=kanji,
                    transliteration=romaji,
                    interpretation=meaning,
                )

        # Now try to generate - should return empty list
        options = ShikonaService.generate_shikona_options(count=3)
        self.assertEqual(len(options), 0)


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

    def test_dashboard_accessible_with_heya(self) -> None:
        """Test that users with heya can access dashboard."""
        # Create heya for user
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
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
