"""Service for generating Shikona (ring names) for heya selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from game.models import Shikona as ShikonaModel
from libs.constants import SHIKONA_RESERVATION_TTL_MINUTES
from libs.generators.shikona import ShikonaGenerationError, ShikonaGenerator

logger = logging.getLogger(__name__)


@dataclass
class ShikonaOption:
    """A generated shikona option for display."""

    name: str  # Japanese kanji
    transliteration: str  # Romaji
    interpretation: str  # Meaning


class ShikonaService:
    """
    Service for generating and managing Shikona (ring names).

    This service provides business logic for creating unique shikona
    options for stable name selection during onboarding.
    """

    @staticmethod
    def generate_shikona_options(count: int = 3) -> list[ShikonaOption]:
        """
        Generate unique shikona options for heya name selection.

        Uses the existing ShikonaGenerator which leverages OpenAI for
        authentic romanization and meaningful interpretations.

        Args:
        ----
            count: Number of unique options to generate (default: 3).

        Returns:
        -------
            List of ShikonaOption instances with unique names.
            May return fewer than requested if generation fails.

        """
        options: list[ShikonaOption] = []

        # Get existing shikona names to avoid duplicates
        existing_names = set(
            ShikonaModel.objects.values_list("name", flat=True)
        )
        existing_translit = set(
            ShikonaModel.objects.values_list("transliteration", flat=True)
        )

        generator = ShikonaGenerator()
        max_attempts = count * 3  # Allow some retries for duplicates

        for _ in range(max_attempts):
            if len(options) >= count:
                break

            try:
                shikona = generator.generate_single()

                # Check uniqueness
                if (
                    shikona.shikona not in existing_names
                    and shikona.transliteration not in existing_translit
                    and shikona.shikona not in {opt.name for opt in options}
                ):
                    options.append(
                        ShikonaOption(
                            name=shikona.shikona,
                            transliteration=shikona.transliteration,
                            interpretation=shikona.interpretation,
                        )
                    )
                    logger.info(
                        "Generated shikona option: %s (%s)",
                        shikona.shikona,
                        shikona.transliteration,
                    )
            except ShikonaGenerationError as e:
                logger.warning("Failed to generate shikona: %s", e)
                continue

        if len(options) < count:
            logger.warning(
                "Could only generate %d/%d shikona options",
                len(options),
                count,
            )

        return options

    @staticmethod
    def create_shikona_from_option(option: ShikonaOption) -> ShikonaModel:
        """
        Create a Shikona model instance from a ShikonaOption.

        Args:
        ----
            option: The ShikonaOption to persist.

        Returns:
        -------
            The newly created Shikona instance.

        """
        return ShikonaModel.objects.create(
            name=option.name,
            transliteration=option.transliteration,
            interpretation=option.interpretation,
        )

    @staticmethod
    def release_expired_reservations() -> int:
        """
        Clear reservations older than the TTL on available shikona.

        Only affects shikona where is_available=True. Clears reserved_at
        and reserved_by for any shikona whose reservation has expired.

        Returns
        -------
            The number of shikona reservations released.

        """
        cutoff = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES
        )
        updated = ShikonaModel.objects.filter(
            is_available=True,
            reserved_at__lt=cutoff,
        ).update(reserved_at=None, reserved_by=None)
        return updated

    @staticmethod
    def get_available_shikona(count: int = 1) -> list[ShikonaModel]:
        """
        Return random available, non-reserved shikona from the pool.

        Filters to shikona that are available (is_available=True) and
        either have no reservation or have an expired reservation.

        Args:
        ----
            count: Number of shikona to return (default: 1).

        Returns:
        -------
            List of ShikonaModel instances selected randomly.
            May be fewer than requested if the pool is insufficient.

        """
        cutoff = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES
        )

        return list(
            ShikonaModel.objects.filter(
                is_available=True,
            )
            .filter(Q(reserved_at__isnull=True) | Q(reserved_at__lt=cutoff))
            .order_by("?")[:count]
        )

    @staticmethod
    def reserve_shikona(
        shikona_ids: list[int], user: User
    ) -> list[ShikonaModel]:
        """
        Reserve shikona for a user within an atomic transaction.

        Only reserves shikona that are available and not freshly reserved
        by another session. Uses select_for_update() to prevent races.

        Args:
        ----
            shikona_ids: List of primary keys of shikona to reserve.
            user: The user reserving the shikona.

        Returns:
        -------
            List of ShikonaModel instances that were successfully reserved.

        """
        now = timezone.now()
        cutoff = now - timedelta(minutes=SHIKONA_RESERVATION_TTL_MINUTES)

        with transaction.atomic():
            candidates = (
                ShikonaModel.objects.select_for_update()
                .filter(
                    pk__in=shikona_ids,
                    is_available=True,
                )
                .filter(Q(reserved_at__isnull=True) | Q(reserved_at__lt=cutoff))
            )
            reserved = []
            for shikona in candidates:
                shikona.reserved_at = now
                shikona.reserved_by = user
                shikona.save(update_fields=["reserved_at", "reserved_by"])
                reserved.append(shikona)
        return reserved

    @staticmethod
    def release_reservation(user: User) -> None:
        """
        Clear reservation fields for all shikona reserved by a user.

        Only affects available shikona (is_available=True).

        Args:
        ----
            user: The user whose reservations should be released.

        """
        ShikonaModel.objects.filter(
            is_available=True,
            reserved_by=user,
        ).update(reserved_at=None, reserved_by=None)

    @staticmethod
    def consume_shikona(shikona: ShikonaModel) -> None:
        """
        Mark a shikona as consumed, making it unavailable in the pool.

        Sets is_available=False and clears any reservation fields.

        Args:
        ----
            shikona: The ShikonaModel instance to consume.

        """
        shikona.is_available = False
        shikona.reserved_at = None
        shikona.reserved_by = None
        shikona.save(
            update_fields=["is_available", "reserved_at", "reserved_by"]
        )
