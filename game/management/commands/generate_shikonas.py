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

    # Recommended batch sizes per model
    RECOMMENDED_BATCH_SIZES = {
        "gpt-5-nano": 3,
        "gpt-5-mini": 10,
        "gpt-5": 30,
    }

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
            default=None,
            help="Names per API call (auto-selected based on model)",
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
        batch_size: int | None = options["batch_size"]
        seed: int | None = options["seed"]
        model: str = options["model"]

        if count <= 0:
            raise CommandError("Count must be positive")

        # Auto-select batch size based on model if not specified
        if batch_size is None:
            batch_size = self.RECOMMENDED_BATCH_SIZES.get(model, 5)
            self.stdout.write(
                self.style.WARNING(
                    f"Auto-selected batch size {batch_size} for model {model}"
                )
            )
        elif batch_size <= 0:
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

        # Try to generate with automatic batch size reduction on failure
        shikona_data = None
        current_batch_size = batch_size
        min_batch_size = 1

        while current_batch_size >= min_batch_size:
            try:
                shikona_data = generator.generate_dict(
                    count=count, batch_size=current_batch_size
                )
                break
            except ShikonaGenerationError as e:
                if current_batch_size > min_batch_size:
                    current_batch_size = max(
                        min_batch_size, current_batch_size // 2
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"Generation failed, retrying with batch size "
                            f"{current_batch_size}..."
                        )
                    )
                else:
                    raise CommandError(
                        f"Failed to generate shikona: {e}"
                    ) from e

        if shikona_data is None:
            raise CommandError("Failed to generate shikona after retries")

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
