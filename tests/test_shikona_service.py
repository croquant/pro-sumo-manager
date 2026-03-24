"""Tests for ShikonaService pool management methods."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from game.models import Shikona
from game.services.shikona_service import ShikonaService
from libs.constants import SHIKONA_RESERVATION_TTL_MINUTES


def _create_user(
    username: str = "testuser", email: str = "test@example.com"
) -> User:
    """Create a test user."""
    return User.objects.create_user(
        username=username,
        email=email,
        password="password",  # noqa: S106
    )


def _create_pool_shikona(
    name: str,
    transliteration: str,
    interpretation: str = "Test meaning",
    is_available: bool = True,
    reserved_at: datetime | None = None,
    reserved_by: User | None = None,
) -> Shikona:
    """Create a Shikona for pool testing."""
    return Shikona.objects.create(
        name=name,
        transliteration=transliteration,
        interpretation=interpretation,
        is_available=is_available,
        reserved_at=reserved_at,
        reserved_by=reserved_by,
    )


class ReleaseExpiredReservationsTests(TestCase):
    """Tests for ShikonaService.release_expired_reservations."""

    def test_releases_expired_reservations(self) -> None:
        """Reservation older than TTL should be cleared."""
        user = _create_user()
        expired_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=expired_time,
            reserved_by=user,
        )

        released = ShikonaService.release_expired_reservations()

        shikona.refresh_from_db()
        self.assertEqual(released, 1)
        self.assertIsNone(shikona.reserved_at)
        self.assertIsNone(shikona.reserved_by)

    def test_does_not_release_fresh_reservations(self) -> None:
        """Reservation within TTL should not be cleared."""
        user = _create_user()
        fresh_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES - 1
        )
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=fresh_time,
            reserved_by=user,
        )

        released = ShikonaService.release_expired_reservations()

        shikona.refresh_from_db()
        self.assertEqual(released, 0)
        self.assertIsNotNone(shikona.reserved_at)
        self.assertIsNotNone(shikona.reserved_by)

    def test_does_not_touch_consumed_shikona(self) -> None:
        """Consumed shikona with old reserved_at should not be touched."""
        user = _create_user()
        expired_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            is_available=False,
            reserved_at=expired_time,
            reserved_by=user,
        )

        released = ShikonaService.release_expired_reservations()

        shikona.refresh_from_db()
        self.assertEqual(released, 0)
        # Consumed shikona fields should be unchanged
        self.assertIsNotNone(shikona.reserved_at)


class GetAvailableShikonaTests(TestCase):
    """Tests for ShikonaService.get_available_shikona."""

    def test_returns_available_unreserved_shikona(self) -> None:
        """Should return available shikona with no reservation."""
        shikona = _create_pool_shikona(name="鶴龍", transliteration="Tsururyu")

        result = ShikonaService.get_available_shikona(count=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pk, shikona.pk)

    def test_excludes_consumed_shikona(self) -> None:
        """Consumed shikona (is_available=False) should be excluded."""
        _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            is_available=False,
        )

        result = ShikonaService.get_available_shikona(count=1)

        self.assertEqual(len(result), 0)

    def test_excludes_freshly_reserved_shikona(self) -> None:
        """Shikona with active reservation should be excluded."""
        user = _create_user()
        fresh_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES - 1
        )
        _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=fresh_time,
            reserved_by=user,
        )

        result = ShikonaService.get_available_shikona(count=1)

        self.assertEqual(len(result), 0)

    def test_includes_expired_reservations(self) -> None:
        """Shikona with expired reservation should be treated as available."""
        user = _create_user()
        expired_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=expired_time,
            reserved_by=user,
        )

        result = ShikonaService.get_available_shikona(count=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pk, shikona.pk)

    def test_returns_fewer_if_pool_insufficient(self) -> None:
        """Should return fewer than requested if pool is too small."""
        _create_pool_shikona(name="鶴龍", transliteration="Tsururyu")

        result = ShikonaService.get_available_shikona(count=5)

        self.assertEqual(len(result), 1)

    def test_returns_empty_when_pool_empty(self) -> None:
        """Should return empty list when no shikona are available."""
        result = ShikonaService.get_available_shikona(count=3)

        self.assertEqual(result, [])


class ReserveShikonaTests(TestCase):
    """Tests for ShikonaService.reserve_shikona."""

    def test_reserves_available_shikona(self) -> None:
        """Should set reserved_at and reserved_by for available shikona."""
        user = _create_user()
        shikona = _create_pool_shikona(name="鶴龍", transliteration="Tsururyu")

        result = ShikonaService.reserve_shikona([shikona.pk], user)

        self.assertEqual(len(result), 1)
        shikona.refresh_from_db()
        self.assertIsNotNone(shikona.reserved_at)
        self.assertEqual(shikona.reserved_by, user)

    def test_skips_already_consumed_shikona(self) -> None:
        """Should not reserve consumed shikona (is_available=False)."""
        user = _create_user()
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            is_available=False,
        )

        result = ShikonaService.reserve_shikona([shikona.pk], user)

        self.assertEqual(len(result), 0)

    def test_skips_already_reserved_shikona(self) -> None:
        """Should not reserve shikona with an active reservation."""
        user1 = _create_user(username="user1", email="user1@example.com")
        user2 = _create_user(username="user2", email="user2@example.com")
        fresh_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES - 1
        )
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=fresh_time,
            reserved_by=user1,
        )

        result = ShikonaService.reserve_shikona([shikona.pk], user2)

        self.assertEqual(len(result), 0)
        shikona.refresh_from_db()
        # Reservation should still belong to user1
        self.assertEqual(shikona.reserved_by, user1)


class ReleaseReservationTests(TestCase):
    """Tests for ShikonaService.release_reservation."""

    def test_releases_user_reservations(self) -> None:
        """Should clear reservation fields for all shikona reserved by user."""
        user = _create_user()
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=timezone.now(),
            reserved_by=user,
        )

        ShikonaService.release_reservation(user)

        shikona.refresh_from_db()
        self.assertIsNone(shikona.reserved_at)
        self.assertIsNone(shikona.reserved_by)

    def test_does_not_release_other_user_reservations(self) -> None:
        """Should not affect reservations belonging to other users."""
        user1 = _create_user(username="user1", email="user1@example.com")
        user2 = _create_user(username="user2", email="user2@example.com")
        reserved_time = timezone.now()
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=reserved_time,
            reserved_by=user1,
        )

        ShikonaService.release_reservation(user2)

        shikona.refresh_from_db()
        self.assertIsNotNone(shikona.reserved_at)
        self.assertEqual(shikona.reserved_by, user1)


class ConsumeShikonaTests(TestCase):
    """Tests for ShikonaService.consume_shikona."""

    def test_marks_shikona_unavailable(self) -> None:
        """Should set is_available=False and clear reservation fields."""
        user = _create_user()
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=timezone.now(),
            reserved_by=user,
        )

        ShikonaService.consume_shikona(shikona)

        shikona.refresh_from_db()
        self.assertFalse(shikona.is_available)
        self.assertIsNone(shikona.reserved_at)
        self.assertIsNone(shikona.reserved_by)

    def test_works_on_unreserved_shikona(self) -> None:
        """Should mark as unavailable even if shikona was not reserved."""
        shikona = _create_pool_shikona(name="鶴龍", transliteration="Tsururyu")

        ShikonaService.consume_shikona(shikona)

        shikona.refresh_from_db()
        self.assertFalse(shikona.is_available)
        self.assertIsNone(shikona.reserved_at)
        self.assertIsNone(shikona.reserved_by)


class GenerateShikonaOptionsPoolTests(TestCase):
    """Tests for generate_shikona_options pool integration."""

    def test_uses_pool_when_available(self) -> None:
        """
        Create pool shikona, call with user, verify returned and reserved.

        Creates 3 pool shikona, calls with user, verifies 3 options returned
        and all reserved.
        """
        user = _create_user()
        _create_pool_shikona(name="龍虎", transliteration="Ryuko")
        _create_pool_shikona(name="雷電", transliteration="Raiden")
        _create_pool_shikona(name="白鵬", transliteration="Hakuho")

        options = ShikonaService.generate_shikona_options(count=3, user=user)

        self.assertEqual(len(options), 3)
        # All returned shikona should be reserved by user
        reserved = Shikona.objects.filter(is_available=True, reserved_by=user)
        self.assertEqual(reserved.count(), 3)

    def test_falls_back_to_openai_when_pool_empty(self) -> None:
        """When pool is empty, falls back to OpenAI generation."""
        from unittest.mock import MagicMock, patch

        from libs.types.shikona import Shikona as ShikonaType

        user = _create_user()
        mock_shikona = ShikonaType(
            shikona="霧島",
            transliteration="Kirishima",
            interpretation="Fog island",
        )
        with patch(
            "game.services.shikona_service.ShikonaGenerator"
        ) as mock_gen_cls:
            instance = MagicMock()
            instance.generate_single.return_value = mock_shikona
            mock_gen_cls.return_value = instance

            options = ShikonaService.generate_shikona_options(
                count=1, user=user
            )

        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].name, "霧島")
        self.assertEqual(options[0].transliteration, "Kirishima")

    def test_uses_pool_without_user(self) -> None:
        """Pool shikona returned without reserving when user is None."""
        _create_pool_shikona(name="龍虎", transliteration="Ryuko")

        options = ShikonaService.generate_shikona_options(count=1)

        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].name, "龍虎")
        # No reservation should be set
        shikona = Shikona.objects.get(name="龍虎")
        self.assertIsNone(shikona.reserved_by)

    def test_releases_expired_before_fetching(self) -> None:
        """Expired reservation by user1 is released so user2 can get it."""
        user1 = _create_user(username="user1", email="user1@example.com")
        user2 = _create_user(username="user2", email="user2@example.com")
        expired_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        shikona = _create_pool_shikona(
            name="鶴龍",
            transliteration="Tsururyu",
            reserved_at=expired_time,
            reserved_by=user1,
        )

        options = ShikonaService.generate_shikona_options(count=1, user=user2)

        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].name, shikona.name)


class CreateShikonaFromOptionPoolTests(TestCase):
    """Tests for create_shikona_from_option pool integration."""

    def test_consumes_pregenerated_shikona(self) -> None:
        """Matching pool shikona is consumed and other reservation released."""
        user = _create_user()
        now = timezone.now()
        s1 = _create_pool_shikona(
            name="龍虎",
            transliteration="Ryuko",
            reserved_at=now,
            reserved_by=user,
        )
        s2 = _create_pool_shikona(
            name="雷電",
            transliteration="Raiden",
            reserved_at=now,
            reserved_by=user,
        )

        from game.services.shikona_service import ShikonaOption

        option = ShikonaOption(
            name="龍虎",
            transliteration="Ryuko",
            interpretation="Test meaning",
        )
        result = ShikonaService.create_shikona_from_option(option, user=user)

        self.assertEqual(result.pk, s1.pk)
        s1.refresh_from_db()
        self.assertFalse(s1.is_available)
        # Other reservation should be released
        s2.refresh_from_db()
        self.assertIsNone(s2.reserved_by)

    def test_creates_new_shikona_when_not_in_pool(self) -> None:
        """When option is not in pool, a new shikona is created."""
        from game.services.shikona_service import ShikonaOption

        option = ShikonaOption(
            name="霧島",
            transliteration="Kirishima",
            interpretation="Fog island",
        )
        result = ShikonaService.create_shikona_from_option(option)

        self.assertIsNotNone(result.pk)
        self.assertEqual(result.name, "霧島")
        self.assertFalse(result.is_available)

    def test_consumes_pregenerated_shikona_without_user(self) -> None:
        """Matching pool shikona is consumed even when user is None."""
        from game.services.shikona_service import ShikonaOption

        s = _create_pool_shikona(name="龍虎", transliteration="Ryuko")

        option = ShikonaOption(
            name="龍虎",
            transliteration="Ryuko",
            interpretation="Test meaning",
        )
        result = ShikonaService.create_shikona_from_option(option)

        self.assertEqual(result.pk, s.pk)
        s.refresh_from_db()
        self.assertFalse(s.is_available)
