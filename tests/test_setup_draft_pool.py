"""Tests for the draft pool setup flow."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from game.models import GameDate, Heya, Rikishi, Shikona
from game.services import DraftCandidate

User = get_user_model()


class SetupDraftPoolViewTests(TestCase):
    """Tests for the setup_draft_pool view."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )

        # Create a heya for the user
        self.game_date = GameDate.objects.create(year=1, month=1, day=1)
        self.heya_name = Shikona.objects.create(
            name="虎龍",
            transliteration="Koryu",
            interpretation="Tiger Dragon",
        )
        self.heya = Heya.objects.create(
            name=self.heya_name,
            created_at=self.game_date,
            owner=self.user,
        )

    def test_draft_pool_requires_login(self) -> None:
        """Draft pool page should redirect unauthenticated users."""
        response = self.client.get(reverse("setup_draft_pool"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_draft_pool_requires_heya(self) -> None:
        """Draft pool page should redirect users without a heya."""
        # Use a fresh client to avoid session contamination from other tests
        client = Client()

        # Create user without heya
        user_no_heya = User.objects.create_user(
            email="noheya@example.com",
            username="noheya",
            password="testpass123",  # noqa: S106
        )
        client.force_login(user_no_heya)

        response = client.get(reverse("setup_draft_pool"))
        # fetch_redirect_response=False to avoid following to setup_heya_name
        # which would trigger ShikonaGenerator with mocked OpenAI
        self.assertRedirects(
            response,
            reverse("setup_heya_name"),
            fetch_redirect_response=False,
        )

    def test_draft_pool_redirects_if_already_drafted(self) -> None:
        """Draft pool page should redirect users who already have a wrestler."""
        # Create a wrestler for the heya
        wrestler_shikona = Shikona.objects.create(
            name="大海",
            transliteration="Oumi",
            interpretation="Great Sea",
        )
        Rikishi.objects.create(
            shikona=wrestler_shikona,
            heya=self.heya,
            potential=50,
            strength=5,
            technique=5,
            balance=5,
            endurance=3,
            mental=2,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))
        self.assertRedirects(response, reverse("dashboard"))

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_pool_page_renders(self, mock_generate: MagicMock) -> None:
        """Draft pool page should render successfully."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft Your First Wrestler")
        self.assertContains(response, "Hoshoryu")
        self.assertContains(response, "Mongolia")
        self.assertContains(response, "Promising")

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_pool_stored_in_session(
        self, mock_generate: MagicMock
    ) -> None:
        """Draft pool should be stored in session for consistency."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        # Second request should not regenerate
        mock_generate.reset_mock()
        self.client.get(reverse("setup_draft_pool"))
        mock_generate.assert_not_called()

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_pool_persists_across_reloads(
        self, mock_generate: MagicMock
    ) -> None:
        """Draft pool should persist in session across page reloads."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)

        # First request
        response1 = self.client.get(reverse("setup_draft_pool"))
        self.assertContains(response1, "Hoshoryu")

        # Second request (reload)
        response2 = self.client.get(reverse("setup_draft_pool"))
        self.assertContains(response2, "Hoshoryu")

        # generate_draft_pool should only be called once
        mock_generate.assert_called_once()

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_selection_creates_wrestler(
        self, mock_generate: MagicMock
    ) -> None:
        """Selecting a wrestler should create a Rikishi record."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)

        # Load the page to populate session
        self.client.get(reverse("setup_draft_pool"))

        # Submit selection
        response = self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "0"},
        )

        # Should redirect to dashboard
        self.assertRedirects(response, reverse("dashboard"))

        # Rikishi should be created
        self.assertTrue(Rikishi.objects.filter(shikona__name="豊昇龍").exists())

        # Rikishi should belong to user's heya
        rikishi = Rikishi.objects.get(shikona__name="豊昇龍")
        self.assertEqual(rikishi.heya, self.heya)
        self.assertEqual(rikishi.potential, 45)
        self.assertEqual(rikishi.strength, 5)
        self.assertEqual(rikishi.technique, 6)

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_selection_without_selection_shows_error(
        self, mock_generate: MagicMock
    ) -> None:
        """Submitting without selection should show error."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        response = self.client.post(reverse("setup_draft_pool"), {})
        self.assertRedirects(response, reverse("setup_draft_pool"))

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_selection_invalid_index_shows_error(
        self, mock_generate: MagicMock
    ) -> None:
        """Invalid selection index should show error."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        response = self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "99"},  # Invalid index
        )
        self.assertRedirects(response, reverse("setup_draft_pool"))

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_clears_session_on_success(
        self, mock_generate: MagicMock
    ) -> None:
        """Session should be cleared after successful draft."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Promising",
                _potential=45,
            ),
        ]

        self.client.force_login(self.user)
        self.client.get(reverse("setup_draft_pool"))

        # Verify session has data
        session = self.client.session
        self.assertIn("draft_pool", session)

        # Submit selection
        self.client.post(
            reverse("setup_draft_pool"),
            {"selected_wrestler": "0"},
        )

        # Session should be cleared (need fresh session object)
        session = self.client.session
        self.assertNotIn("draft_pool", session)

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_pool_displays_all_stats(
        self, mock_generate: MagicMock
    ) -> None:
        """Draft pool should display all 5 stats for each wrestler."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=8,
                technique=7,
                balance=6,
                endurance=5,
                mental=4,
                potential_tier="Talented",
                _potential=55,
            ),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))

        self.assertContains(response, "Strength")
        self.assertContains(response, "Technique")
        self.assertContains(response, "Balance")
        self.assertContains(response, "Endurance")
        self.assertContains(response, "Mental")

    @patch("game.views.DraftPoolService.generate_draft_pool")
    def test_draft_pool_shows_potential_tier_not_number(
        self, mock_generate: MagicMock
    ) -> None:
        """Draft pool should show tier label, not the potential number."""
        mock_generate.return_value = [
            DraftCandidate(
                shikona_name="豊昇龍",
                shikona_transliteration="Hoshoryu",
                shusshin_display="Mongolia",
                strength=5,
                technique=6,
                balance=4,
                endurance=3,
                mental=2,
                potential_tier="Exceptional",
                _potential=75,
            ),
        ]

        self.client.force_login(self.user)
        response = self.client.get(reverse("setup_draft_pool"))

        # Should show tier label
        self.assertContains(response, "Exceptional")

        # Should NOT show the actual potential number
        content = response.content.decode()
        # Check that "75" doesn't appear as a standalone value
        # (it might appear in other contexts like CSS values)
        self.assertNotIn(">75<", content)
