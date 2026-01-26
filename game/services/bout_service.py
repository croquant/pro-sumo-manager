"""Service for managing bout operations and business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import transaction

from game.models import Banzuke, BanzukeEntry, Bout, Rikishi

if TYPE_CHECKING:
    from libs.types.bout import Bout as BoutOutput


class BoutService:
    """
    Service for managing bout-related operations.

    This service provides business logic for recording bout results,
    updating win/loss records, and awarding XP. All bout modifications
    should go through this service to ensure consistency and proper
    validation.
    """

    @staticmethod
    def _get_banzuke_entry(banzuke: Banzuke, rikishi: Rikishi) -> BanzukeEntry:
        """
        Get a BanzukeEntry with row-level locking for update.

        Args:
            banzuke: The tournament.
            rikishi: The wrestler.

        Returns:
            The BanzukeEntry for the wrestler in the tournament.

        Raises:
            ValidationError: If the wrestler is not entered in the tournament.

        """
        try:
            return BanzukeEntry.objects.select_for_update().get(
                banzuke=banzuke,
                rikishi=rikishi,
            )
        except BanzukeEntry.DoesNotExist:
            msg = (
                f"{rikishi} is not entered in {banzuke}. "
                "Cannot record bout result."
            )
            raise ValidationError(msg) from None

    @staticmethod
    @transaction.atomic
    def record_bout(
        banzuke: Banzuke,
        day: int,
        east_rikishi: Rikishi,
        west_rikishi: Rikishi,
        bout_result: BoutOutput,
    ) -> Bout:
        """
        Record a bout result from BoutGenerator output.

        This method:
        1. Creates a Bout record with the match details
        2. Updates the BanzukeEntry win/loss counts atomically
        3. Awards XP to both wrestlers

        Args:
            banzuke: The tournament this bout belongs to.
            day: The tournament day (1-15).
            east_rikishi: The wrestler on the east side.
            west_rikishi: The wrestler on the west side.
            bout_result: The generated bout result from BoutGenerator.

        Returns:
            The created Bout instance.

        Raises:
            ValidationError: If validation fails (e.g., missing BanzukeEntry,
                wrestler fighting themselves, duplicate bout).

        """
        # Validate wrestlers are different
        if east_rikishi.pk == west_rikishi.pk:
            raise ValidationError("A wrestler cannot fight themselves.")

        # Get BanzukeEntry records with locking
        east_entry = BoutService._get_banzuke_entry(banzuke, east_rikishi)
        west_entry = BoutService._get_banzuke_entry(banzuke, west_rikishi)

        # Convert commentary list to text
        commentary_text = "\n".join(bout_result.commentary)

        # Create the Bout record
        bout = Bout(
            banzuke=banzuke,
            day=day,
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            winner=bout_result.winner,
            kimarite=bout_result.kimarite,
            east_xp_gain=bout_result.east_xp_gain,
            west_xp_gain=bout_result.west_xp_gain,
            excitement_level=bout_result.excitement_level,
            commentary=commentary_text,
        )
        bout.full_clean()
        bout.save()

        # Update win/loss records
        if bout_result.winner == "east":
            east_entry.wins += 1
            west_entry.losses += 1
        else:
            west_entry.wins += 1
            east_entry.losses += 1

        east_entry.save()
        west_entry.save()

        # Award XP to both rikishi
        east_rikishi.xp += bout_result.east_xp_gain
        west_rikishi.xp += bout_result.west_xp_gain
        east_rikishi.save()
        west_rikishi.save()

        return bout

    @staticmethod
    def get_tournament_bouts(
        banzuke: Banzuke,
        day: int | None = None,
    ) -> list[Bout]:
        """
        Get all bouts for a tournament, optionally filtered by day.

        Args:
            banzuke: The tournament.
            day: Optional day filter (1-15).

        Returns:
            List of Bout instances.

        """
        queryset = Bout.objects.filter(banzuke=banzuke).select_related(
            "east_rikishi__shikona",
            "west_rikishi__shikona",
        )
        if day is not None:
            queryset = queryset.filter(day=day)
        return list(queryset.order_by("day"))

    @staticmethod
    def get_rikishi_bouts(
        rikishi: Rikishi,
        banzuke: Banzuke | None = None,
    ) -> list[Bout]:
        """
        Get all bouts for a rikishi, optionally filtered by tournament.

        Args:
            rikishi: The wrestler.
            banzuke: Optional tournament filter.

        Returns:
            List of Bout instances where the rikishi participated.

        """
        from django.db.models import Q

        queryset = Bout.objects.filter(
            Q(east_rikishi=rikishi) | Q(west_rikishi=rikishi)
        ).select_related(
            "banzuke",
            "east_rikishi__shikona",
            "west_rikishi__shikona",
        )
        if banzuke is not None:
            queryset = queryset.filter(banzuke=banzuke)
        return list(queryset.order_by("banzuke", "day"))
