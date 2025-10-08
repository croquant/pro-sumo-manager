"""Management command to generate shikona using AI."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from game.models.shikona import Shikona
from libs.generators.shikona import ShikonaGenerationError, ShikonaGenerator


class Command(BaseCommand):
    """Generate shikona using AI and save them to the database."""

    help = (
        "Generate shikona (ring names) using AI and save them to the database"
    )

    def add_arguments(self, parser: Any) -> None:  # noqa: ANN401
        """Add command arguments."""
        parser.add_argument(
            "count",
            type=int,
            help="Number of shikona to generate",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of names to process per API call (default: 10)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Random seed for deterministic generation (optional)",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="gpt-5-nano",
            help="OpenAI model to use (default: gpt-5-nano)",
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ANN401
        """Execute the command."""
        count: int = options["count"]
        batch_size: int = options["batch_size"]
        seed: int | None = options["seed"]
        model: str = options["model"]

        if count <= 0:
            raise CommandError("Count must be positive")

        if batch_size <= 0:
            raise CommandError("Batch size must be positive")

        self.stdout.write(
            self.style.SUCCESS(
                f"Generating {count} shikona (batch size: {batch_size}, "
                f"model: {model})"
            )
        )

        try:
            generator = ShikonaGenerator(seed=seed, model=model)
        except Exception as e:
            raise CommandError(
                f"Failed to initialize ShikonaGenerator: {e}"
            ) from e

        try:
            shikona_data = generator.generate_dict(
                count=count, batch_size=batch_size
            )
        except ShikonaGenerationError as e:
            raise CommandError(f"Failed to generate shikona: {e}") from e

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {len(shikona_data)} shikona, "
                f"saving to database..."
            )
        )

        # Create Shikona objects
        shikona_objects = [
            Shikona(
                name=data["name"],
                transliteration=data["transliteration"],
                interpretation=data["interpretation"],
            )
            for data in shikona_data
        ]

        # Save to database
        created_count = 0
        duplicate_count = 0

        for shikona in shikona_objects:
            try:
                with transaction.atomic():
                    shikona.save()
                    created_count += 1
            except IntegrityError:
                # Skip duplicates
                duplicate_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping duplicate: {shikona.transliteration} "
                        f"({shikona.name})"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully created {created_count} shikona "
                f"({duplicate_count} duplicates skipped)"
            )
        )

        if created_count > 0:
            self.stdout.write("\nSample of created shikona:")
            for shikona in Shikona.objects.order_by("-id")[:5]:
                self.stdout.write(
                    f"  - {shikona.transliteration} ({shikona.name}): "
                    f"{shikona.interpretation}"
                )
