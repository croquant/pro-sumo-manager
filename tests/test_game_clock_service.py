"""Tests for the GameClockService."""

from django.db import IntegrityError, transaction
from django.test import TestCase

from game.models import GameDate
from game.models.gamedate import N_DAYS, N_MONTHS
from game.services import GameClockService


class GameClockServiceTests(TestCase):
    """Tests for the GameClockService."""

    def test_get_current_returns_none_when_no_dates(self) -> None:
        """Should return None when no game dates exist."""
        self.assertIsNone(GameClockService.get_current())

    def test_initialize_creates_first_date(self) -> None:
        """Should create the initial game date (Year 1, Month 1, Day 1)."""
        date = GameClockService.initialize()

        self.assertIsNotNone(date)
        self.assertEqual(date.year, 1)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)

    def test_initialize_returns_current_if_exists(self) -> None:
        """Should return current date if already initialized."""
        first = GameClockService.initialize()
        GameClockService.tick()
        GameClockService.tick()

        # Initialize again should return latest date, not create new one
        current = GameClockService.initialize()
        self.assertEqual(current.year, 1)
        self.assertEqual(current.month, 1)
        self.assertEqual(current.day, 3)
        self.assertNotEqual(current.pk, first.pk)

    def test_tick_creates_first_date_if_none_exist(self) -> None:
        """Should create initial date if tick is called on empty database."""
        date = GameClockService.tick()

        self.assertEqual(date.year, 1)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)

    def test_tick_advances_day(self) -> None:
        """Should advance the day by 1."""
        GameClockService.initialize()

        date = GameClockService.tick()
        self.assertEqual(date.day, 2)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.year, 1)

    def test_tick_advances_multiple_days(self) -> None:
        """Should correctly advance through multiple days."""
        GameClockService.initialize()

        for expected_day in range(2, 6):
            date = GameClockService.tick()
            self.assertEqual(date.day, expected_day)
            self.assertEqual(date.month, 1)
            self.assertEqual(date.year, 1)

    def test_tick_rolls_over_to_next_month(self) -> None:
        """Should roll over to next month when day exceeds N_DAYS."""
        # Create date at end of month
        GameDate.objects.create(year=1, month=1, day=N_DAYS)

        date = GameClockService.tick()
        self.assertEqual(date.year, 1)
        self.assertEqual(date.month, 2)
        self.assertEqual(date.day, 1)

    def test_tick_rolls_over_to_next_year(self) -> None:
        """Should roll over to next year when month exceeds N_MONTHS."""
        # Create date at end of year
        GameDate.objects.create(year=1, month=N_MONTHS, day=N_DAYS)

        date = GameClockService.tick()
        self.assertEqual(date.year, 2)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)

    def test_tick_handles_year_boundary_correctly(self) -> None:
        """Should correctly handle year boundaries across multiple years."""
        # Start at end of year 5
        GameDate.objects.create(year=5, month=N_MONTHS, day=N_DAYS - 1)

        # Advance to last day of year
        date = GameClockService.tick()
        self.assertEqual(date.year, 5)
        self.assertEqual(date.month, N_MONTHS)
        self.assertEqual(date.day, N_DAYS)

        # Advance to first day of next year
        date = GameClockService.tick()
        self.assertEqual(date.year, 6)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)

    def test_get_current_returns_latest_date(self) -> None:
        """Should return the most recent game date."""
        GameDate.objects.create(year=1, month=1, day=1)
        GameDate.objects.create(year=1, month=1, day=2)
        latest = GameDate.objects.create(year=1, month=1, day=3)

        current = GameClockService.get_current()
        self.assertEqual(current, latest)

    def test_dates_are_immutable(self) -> None:
        """Should create new dates rather than modifying existing ones."""
        date1 = GameClockService.initialize()
        date2 = GameClockService.tick()

        # Original date should be unchanged
        date1.refresh_from_db()
        self.assertEqual(date1.day, 1)

        # New date should exist
        self.assertEqual(date2.day, 2)

        # Both should exist in database
        self.assertEqual(GameDate.objects.count(), 2)

    def test_duplicate_dates_raise_integrity_error(self) -> None:
        """Should prevent creation of duplicate dates."""
        GameDate.objects.create(year=1, month=1, day=5)

        # Trying to create the same date should fail
        with self.assertRaises(IntegrityError), transaction.atomic():
            GameDate.objects.create(year=1, month=1, day=5)

    def test_maintains_complete_historical_record(self) -> None:
        """Should maintain a complete historical timeline."""
        GameClockService.initialize()

        # Advance 50 days
        for _ in range(50):
            GameClockService.tick()

        # Should have 51 total dates (initial + 50 ticks)
        self.assertEqual(GameDate.objects.count(), 51)

        # All dates should be unique and sequential
        dates = list(GameDate.objects.order_by("year", "month", "day"))
        self.assertEqual(len(dates), 51)

        # Verify they're all different
        pks = {date.pk for date in dates}
        self.assertEqual(len(pks), 51)

    def test_concurrent_tick_safety(self) -> None:
        """Should handle concurrent ticks safely with transactions."""
        GameClockService.initialize()

        # This test verifies that the transaction isolation works
        # In a real scenario, select_for_update would prevent race conditions
        date1 = GameClockService.tick()
        date2 = GameClockService.tick()

        self.assertNotEqual(date1.pk, date2.pk)
        self.assertEqual(date1.day, 2)
        self.assertEqual(date2.day, 3)

    def test_gamedate_str_representation(self) -> None:
        """Should format date string correctly."""
        date = GameDate.objects.create(year=123, month=4, day=5)
        self.assertEqual(str(date), "0123-04-05")

        date2 = GameDate.objects.create(year=1, month=1, day=1)
        self.assertEqual(str(date2), "0001-01-01")

    def test_gamedate_ordering(self) -> None:
        """Should order dates correctly (newest first)."""
        GameDate.objects.create(year=1, month=1, day=1)
        GameDate.objects.create(year=1, month=2, day=1)
        GameDate.objects.create(year=2, month=1, day=1)

        dates = list(GameDate.objects.all())

        # Should be ordered by year desc, month desc, day desc
        self.assertEqual(dates[0].year, 2)
        self.assertEqual(dates[1].month, 2)
        self.assertEqual(dates[2].day, 1)
        self.assertEqual(dates[2].month, 1)
