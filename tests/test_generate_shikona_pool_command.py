"""Tests for the generate_shikona_pool management command."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from game.models import Shikona
from libs.types.shikona import Shikona as ShikonaType


def _make_shikona_type(
    shikona: str = "大翔",
    transliteration: str = "Daishō",
    interpretation: str = "Great soaring.",
) -> ShikonaType:
    """Create a ShikonaType instance for testing."""
    return ShikonaType(
        shikona=shikona,
        transliteration=transliteration,
        interpretation=interpretation,
    )


PATCH_PATH = "game.management.commands.generate_shikona_pool.ShikonaGenerator"


class GenerateShikonaPoolCommandTests(TestCase):
    """Tests for the generate_shikona_pool management command."""

    def test_creates_shikona_with_is_available_true(self) -> None:
        """Generated shikona should be saved with is_available=True."""
        mock_shikona = _make_shikona_type()

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.return_value = mock_shikona
            call_command(
                "generate_shikona_pool", "--count", "1", stdout=StringIO()
            )

        created = Shikona.objects.get(name=mock_shikona.shikona)
        self.assertTrue(created.is_available)

    def test_respects_count_parameter(self) -> None:
        """Command should generate exactly --count shikona."""
        shikona_list = [
            _make_shikona_type(
                shikona=f"力士{i}",
                transliteration=f"Rikishi{i}",
                interpretation=f"Meaning {i}.",
            )
            for i in range(3)
        ]

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.side_effect = shikona_list
            call_command(
                "generate_shikona_pool", "--count", "3", stdout=StringIO()
            )

        self.assertEqual(Shikona.objects.count(), 3)

    def test_skips_duplicate_names(self) -> None:
        """Command should skip shikona whose name already exists."""
        existing = Shikona.objects.create(
            name="大翔",
            transliteration="Daishō",
            interpretation="Existing.",
            is_available=True,
        )
        duplicate = _make_shikona_type(
            shikona=existing.name,
            transliteration=existing.transliteration,
        )
        unique = _make_shikona_type(
            shikona="白鵬",
            transliteration="Hakuhō",
            interpretation="White phoenix.",
        )

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.side_effect = [duplicate, unique]
            call_command(
                "generate_shikona_pool", "--count", "1", stdout=StringIO()
            )

        self.assertEqual(Shikona.objects.count(), 2)
        self.assertTrue(
            Shikona.objects.filter(name="白鵬", is_available=True).exists()
        )

    def test_handles_generation_failure(self) -> None:
        """Command should continue after ShikonaGenerationError and succeed."""
        from libs.generators.shikona import ShikonaGenerationError

        success_shikona = _make_shikona_type()

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.side_effect = [
                ShikonaGenerationError("API failure"),
                success_shikona,
            ]
            call_command(
                "generate_shikona_pool", "--count", "1", stdout=StringIO()
            )

        self.assertEqual(Shikona.objects.count(), 1)

    def test_reports_progress(self) -> None:
        """Command should output progress containing 'N/N'."""
        mock_shikona = _make_shikona_type()
        out = StringIO()

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.return_value = mock_shikona
            call_command("generate_shikona_pool", "--count", "1", stdout=out)

        output = out.getvalue()
        self.assertIn("1/1", output)

    def test_handles_integrity_error(self) -> None:
        """Command should treat IntegrityError as a duplicate and continue."""
        from django.db import IntegrityError

        success_shikona = _make_shikona_type(
            shikona="白鵬",
            transliteration="Hakuhō",
            interpretation="White phoenix.",
        )
        duplicate_shikona = _make_shikona_type()

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.side_effect = [
                duplicate_shikona,
                success_shikona,
            ]
            with patch(
                "game.management.commands.generate_shikona_pool"
                ".Shikona.objects.create"
            ) as mock_create:
                mock_create.side_effect = [IntegrityError(), None]
                call_command(
                    "generate_shikona_pool",
                    "--count",
                    "1",
                    stdout=StringIO(),
                )

        self.assertEqual(mock_create.call_count, 2)

    def test_rejects_non_positive_count(self) -> None:
        """Command should raise CommandError when --count is not positive."""
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command(
                "generate_shikona_pool", "--count", "0", stdout=StringIO()
            )

    def test_rejects_non_positive_batch_size(self) -> None:
        """Command should raise CommandError for non-positive --batch-size."""
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command(
                "generate_shikona_pool",
                "--count",
                "1",
                "--batch-size",
                "0",
                stdout=StringIO(),
            )

    def test_stops_after_max_attempts(self) -> None:
        """Command should stop when max_attempts is exhausted."""
        from libs.generators.shikona import ShikonaGenerationError

        with patch(PATCH_PATH) as mock_generator_cls:
            instance = mock_generator_cls.return_value
            instance.generate_single.side_effect = ShikonaGenerationError(
                "always fails"
            )
            out = StringIO()
            call_command("generate_shikona_pool", "--count", "1", stdout=out)

        self.assertEqual(Shikona.objects.count(), 0)
        self.assertIn("Success: 0", out.getvalue())
