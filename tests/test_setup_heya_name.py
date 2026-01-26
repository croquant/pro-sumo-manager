"""Tests for the heya name selection setup flow."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from game.models import GameDate, Heya, Shikona
from game.services.shikona_service import ShikonaService

User = get_user_model()


class TestShikonaService(TestCase):
    """Tests for the ShikonaService."""

    def test_generate_shikona_options_returns_three_options(self):
        """Test that generate_shikona_options returns 3 unique options."""
        options = ShikonaService.generate_shikona_options(count=3)
        self.assertEqual(len(options), 3)

    def test_generate_shikona_options_are_unique(self):
        """Test that generated options have unique names."""
        options = ShikonaService.generate_shikona_options(count=3)
        names = [opt.name for opt in options]
        self.assertEqual(len(names), len(set(names)))

    def test_generate_shikona_options_have_all_fields(self):
        """Test that generated options have all required fields."""
        options = ShikonaService.generate_shikona_options(count=3)
        for opt in options:
            self.assertTrue(opt.name)
            self.assertTrue(opt.transliteration)
            self.assertTrue(opt.interpretation)

    def test_create_shikona_from_option(self):
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

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.client = Client()

    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_can_access_page(self):
        """Test that authenticated users without heya can access the page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("options", response.context)

    def test_page_shows_three_options(self):
        """Test that the page displays 3 shikona options."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_heya_name"))
        self.assertEqual(response.status_code, 200)
        options = response.context["options"]
        self.assertEqual(len(options), 3)

    def test_options_stored_in_session(self):
        """Test that options are stored in session for consistency."""
        self.client.force_login(self.user)
        self.client.get(reverse("setup_heya_name"))
        session = self.client.session
        self.assertIn("heya_options", session)
        self.assertEqual(len(session["heya_options"]), 3)

    def test_user_with_heya_redirected_to_dashboard(self):
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

    def test_post_creates_heya(self):
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

    def test_post_without_selection_shows_error(self):
        """Test that POST without selection shows error."""
        self.client.force_login(self.user)

        # First GET to generate options
        self.client.get(reverse("setup_heya_name"))

        # POST without selection
        response = self.client.post(reverse("setup_heya_name"), {})

        # Should redirect back to setup page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_post_with_invalid_selection_shows_error(self):
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


class TestDashboardRedirect(TestCase):
    """Tests for dashboard redirect behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.client = Client()

    def test_dashboard_redirects_user_without_heya(self):
        """Test that dashboard redirects users without heya to setup."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("setup_heya_name"))

    def test_dashboard_accessible_with_heya(self):
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
