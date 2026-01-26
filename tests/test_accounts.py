"""Tests for the accounts app."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def test_create_user_with_email_and_username(self) -> None:
        """Should create a user with email and username."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_is_unique(self) -> None:
        """Should enforce unique emails."""
        User.objects.create_user(
            email="test@example.com",
            username="testuser1",
            password="testpass123",  # noqa: S106
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(
                email="test@example.com",
                username="testuser2",
                password="testpass123",  # noqa: S106
            )

    def test_username_is_unique(self) -> None:
        """Should enforce unique usernames."""
        User.objects.create_user(
            email="test1@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(
                email="test2@example.com",
                username="testuser",
                password="testpass123",  # noqa: S106
            )

    def test_str_returns_username(self) -> None:
        """Should return username for string representation."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )
        self.assertEqual(str(user), "testuser")

    def test_create_superuser(self) -> None:
        """Should create a superuser with correct permissions."""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123",  # noqa: S106
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthViewTests(TestCase):
    """Tests for authentication views."""

    def test_login_page_renders(self) -> None:
        """Login page should render successfully."""
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign In")

    def test_signup_page_renders(self) -> None:
        """Signup page should render successfully."""
        response = self.client.get(reverse("account_signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Account")

    def test_password_reset_page_renders(self) -> None:
        """Password reset page should render successfully."""
        response = self.client.get(reverse("account_reset_password"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset Password")

    def test_dashboard_requires_login(self) -> None:
        """Dashboard should redirect unauthenticated users to login."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_accessible_when_logged_in(self) -> None:
        """Dashboard should be accessible to authenticated users with heya."""
        from game.models import GameDate, Heya, Shikona

        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )
        # Create heya for the user (required to access dashboard)
        shikona = Shikona.objects.create(
            name="大海",
            transliteration="Ōumi",
            interpretation="Great Sea",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        Heya.objects.create(name=shikona, created_at=game_date, owner=user)

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome")

    def test_index_shows_login_link_when_unauthenticated(self) -> None:
        """Index page should show login link for unauthenticated users."""
        response = self.client.get(reverse("index"))
        self.assertContains(response, "Sign In")
        self.assertContains(response, "Get Started")

    def test_index_shows_dashboard_link_when_authenticated(self) -> None:
        """Index page should show dashboard link for authenticated users."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )
        self.client.force_login(user)
        response = self.client.get(reverse("index"))
        self.assertContains(response, "Go to Dashboard")


class SignupFlowTests(TestCase):
    """Tests for the signup flow."""

    def test_signup_creates_user(self) -> None:
        """Successful signup should create a user."""
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "securepass123!",
                "password2": "securepass123!",
            },
        )
        # Should redirect after successful signup
        self.assertEqual(response.status_code, 302)
        # User should exist
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists()
        )

    def test_signup_validates_password_match(self) -> None:
        """Signup should require matching passwords."""
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "securepass123!",
                "password2": "differentpass!",
            },
        )
        # Should stay on signup page
        self.assertEqual(response.status_code, 200)
        # User should not be created
        self.assertFalse(
            User.objects.filter(email="newuser@example.com").exists()
        )


class LoginFlowTests(TestCase):
    """Tests for the login flow."""

    def setUp(self) -> None:
        """Create a test user."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )

    def test_login_with_valid_credentials(self) -> None:
        """Login should succeed with valid credentials."""
        response = self.client.post(
            reverse("account_login"),
            {
                "login": "test@example.com",
                "password": "testpass123",
            },
        )
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/", response.url)

    def test_login_with_invalid_password(self) -> None:
        """Login should fail with wrong password."""
        response = self.client.post(
            reverse("account_login"),
            {
                "login": "test@example.com",
                "password": "wrongpass",
            },
        )
        # Should stay on login page
        self.assertEqual(response.status_code, 200)


class HeyaUserRelationshipTests(TestCase):
    """Tests for Heya-User ownership relationship."""

    def test_heya_without_owner_is_not_player_controlled(self) -> None:
        """Heya without owner should not be player controlled."""
        from game.models import GameDate, Heya, Shikona

        shikona = Shikona.objects.create(
            name="宮城野",
            transliteration="Miyagino",
            interpretation="Miyagi field",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        heya = Heya.objects.create(name=shikona, created_at=game_date)

        self.assertIsNone(heya.owner)
        self.assertFalse(heya.is_player_controlled)

    def test_heya_with_owner_is_player_controlled(self) -> None:
        """Heya with owner should be player controlled."""
        from game.models import GameDate, Heya, Shikona

        user = User.objects.create_user(
            email="player@example.com",
            username="player",
            password="testpass123",  # noqa: S106
        )
        shikona = Shikona.objects.create(
            name="境川",
            transliteration="Sakaigawa",
            interpretation="Border river",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=2)
        heya = Heya.objects.create(
            name=shikona,
            created_at=game_date,
            owner=user,
        )

        self.assertEqual(heya.owner, user)
        self.assertTrue(heya.is_player_controlled)


class HtmxAuthRedirectMiddlewareTests(TestCase):
    """Tests for HtmxAuthRedirectMiddleware."""

    def test_non_htmx_request_gets_normal_redirect(self) -> None:
        """Non-HTMX requests should get standard 302 redirect."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_htmx_request_gets_hx_redirect_header(self) -> None:
        """HTMX requests should get 200 with HX-Redirect header."""
        response = self.client.get(
            reverse("dashboard"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Redirect", response.headers)
        self.assertIn("/accounts/login/", response.headers["HX-Redirect"])

    def test_htmx_authenticated_request_no_redirect(self) -> None:
        """Authenticated HTMX requests should access dashboard normally."""
        from game.models import GameDate, Heya, Shikona

        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",  # noqa: S106
        )
        # Create heya for the user (required to access dashboard)
        shikona = Shikona.objects.create(
            name="白龍",
            transliteration="Hakuryū",
            interpretation="White Dragon",
        )
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        Heya.objects.create(name=shikona, created_at=game_date, owner=user)

        self.client.force_login(user)
        response = self.client.get(
            reverse("dashboard"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Redirect", response.headers)
