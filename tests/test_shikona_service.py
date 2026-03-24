"""Tests for ShikonaService pool management methods."""

from __future__ import annotations

from datetime import timedelta

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
    reserved_at: object = None,
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
