"""Management command to generate a pool of pre-generated shikona."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandParser
from django.db import IntegrityError

from game.models import Shikona
from libs.generators.shikona import ShikonaGenerationError, ShikonaGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Generate a pool of shikona for instant selection."""

    help = "Pre-generate a pool of shikona ring names via OpenAI."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--count",
            type=int,
            default=600,
            help="Number of shikona to generate (default: 600).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Progress report interval (default: 50).",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Execute the command."""
        count: int = options["count"]  # type: ignore[assignment]
        batch_size: int = options["batch_size"]  # type: ignore[assignment]

        generator = ShikonaGenerator()
        existing_names = set(Shikona.objects.values_list("name", flat=True))
        existing_translit = set(
            Shikona.objects.values_list("transliteration", flat=True)
        )

        success = 0
        failures = 0
        duplicates = 0
        max_attempts = count * 3

        for attempt in range(max_attempts):
            if success >= count:
                break

            try:
                shikona = generator.generate_single()

                if (
                    shikona.shikona in existing_names
                    or shikona.transliteration in existing_translit
                ):
                    duplicates += 1
                    continue

                Shikona.objects.create(
                    name=shikona.shikona,
                    transliteration=shikona.transliteration,
                    interpretation=shikona.interpretation,
                    is_available=True,
                )
                existing_names.add(shikona.shikona)
                existing_translit.add(shikona.transliteration)
                success += 1

                if success % batch_size == 0 or success == count:
                    self.stdout.write(f"Generated {success}/{count}...")

            except ShikonaGenerationError as e:
                failures += 1
                logger.warning("Failed (attempt %d): %s", attempt + 1, e)
                continue
            except IntegrityError:
                duplicates += 1
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Success: {success}, "
                f"Failures: {failures}, "
                f"Duplicates skipped: {duplicates}"
            )
        )
