"""Service for managing game date progression and time-based operations."""

from __future__ import annotations

from django.db import transaction

from game.models.gamedate import GameDate
from libs.constants import N_DAYS, N_MONTHS


class GameClockService:
    """
    Service for managing the game's internal calendar and time progression.

    This service provides thread-safe operations for advancing the game date
    and managing game time. All date modifications should go through this
    service to ensure consistency and proper transaction handling.
    """

    @staticmethod
    def get_current() -> GameDate | None:
        """
        Get the current game date for read-only access.

        This method does not acquire locks and is intended for read-only
        queries. If you need to access the current date within a transaction
        that will modify dates, use initialize() instead to ensure proper
        locking.

        Returns
        -------
            The current GameDate, or None if the game hasn't been initialized.

        """
        return GameDate.objects.first()

    @staticmethod
    def initialize() -> GameDate:
        """
        Initialize the game calendar with the first date.

        Creates the initial game date (Year 1, Month 1, Day 1) if no dates
        exist yet. If dates already exist, returns the current date.

        Returns
        -------
            The initial or current GameDate.

        Raises
        ------
            IntegrityError: If concurrent initialization attempts conflict.

        """
        with transaction.atomic():
            # Lock the table for updates
            current = GameDate.objects.select_for_update().first()
            if current is None:
                current = GameDate.objects.create(year=1, month=1, day=1)
            return current

    @staticmethod
    def tick() -> GameDate:
        """
        Advance the game calendar by one day.

        Creates a new GameDate record representing the next day in the game
        calendar. Handles day/month/year rollovers according to the game's
        calendar system (N_DAYS days per month, N_MONTHS months per year).

        If no dates exist yet, initializes the calendar first.

        Returns
        -------
            The newly created GameDate representing the next day.

        Raises
        ------
            IntegrityError: If a date already exists for the calculated day.

        """
        with transaction.atomic():
            # Lock the table for updates
            current_date = GameDate.objects.select_for_update().first()

            # Initialize if this is the first tick
            if current_date is None:
                return GameDate.objects.create(year=1, month=1, day=1)

            # Calculate next date
            year = current_date.year
            month = current_date.month
            day = current_date.day + 1

            # Handle day overflow
            if day > N_DAYS:
                day = 1
                month += 1

                # Handle month overflow
                if month > N_MONTHS:
                    month = 1
                    year += 1

            # Create and return new date
            return GameDate.objects.create(year=year, month=month, day=day)
