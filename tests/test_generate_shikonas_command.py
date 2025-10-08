"""Tests for the generate_shikonas management command."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from game.models.shikona import Shikona
from libs.generators.shikona import (
    ShikonaGenerationError,
)


class GenerateShikonasCommandTests(TestCase):
    """Tests for the generate_shikonas command."""

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_success(
        self, mock_generator_class: Mock
    ) -> None:
        """Should generate and save shikona to the database."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_generator.generate_dict.return_value = [
            {
                "name": "豊昇龍",
                "transliteration": "hoshoryu",
                "interpretation": "rising dragon",
            },
            {
                "name": "一山本",
                "transliteration": "ichiyamamoto",
                "interpretation": "one mountain base",
            },
        ]

        out = StringIO()
        call_command("generate_shikonas", "2", stdout=out)

        # Verify generator was initialized correctly
        mock_generator_class.assert_called_once_with(
            seed=None, model="gpt-5-nano"
        )

        # Verify generate_dict was called (with auto-selected batch size of 3)
        mock_generator.generate_dict.assert_called_once_with(
            count=2, batch_size=3
        )

        # Verify shikona were saved to database
        self.assertEqual(Shikona.objects.count(), 2)
        self.assertTrue(Shikona.objects.filter(name="豊昇龍").exists())
        self.assertTrue(Shikona.objects.filter(name="一山本").exists())

        # Verify output
        output = out.getvalue()
        self.assertIn("Successfully created 2 shikona", output)

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_with_custom_batch_size(
        self, mock_generator_class: Mock
    ) -> None:
        """Should use custom batch size when provided."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_dict.return_value = []

        out = StringIO()
        call_command("generate_shikonas", "5", "--batch-size", "3", stdout=out)

        mock_generator.generate_dict.assert_called_once_with(
            count=5, batch_size=3
        )

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_with_seed(
        self, mock_generator_class: Mock
    ) -> None:
        """Should use seed when provided."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_dict.return_value = []

        out = StringIO()
        call_command("generate_shikonas", "3", "--seed", "42", stdout=out)

        mock_generator_class.assert_called_once_with(
            seed=42, model="gpt-5-nano"
        )

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_with_custom_model(
        self, mock_generator_class: Mock
    ) -> None:
        """Should use custom model when provided."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_dict.return_value = []

        out = StringIO()
        call_command("generate_shikonas", "3", "--model", "gpt-4", stdout=out)

        mock_generator_class.assert_called_once_with(seed=None, model="gpt-4")

    def test_generate_shikonas_invalid_count(self) -> None:
        """Should raise error for non-positive count."""
        with self.assertRaises(CommandError) as ctx:
            call_command("generate_shikonas", "0")
        self.assertIn("Count must be positive", str(ctx.exception))

        with self.assertRaises(CommandError) as ctx:
            call_command("generate_shikonas", "-5")
        self.assertIn("Count must be positive", str(ctx.exception))

    def test_generate_shikonas_invalid_batch_size(self) -> None:
        """Should raise error for non-positive batch size."""
        with self.assertRaises(CommandError) as ctx:
            call_command("generate_shikonas", "5", "--batch-size", "0")
        self.assertIn("Batch size must be positive", str(ctx.exception))

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_auto_batch_size(
        self, mock_generator_class: Mock
    ) -> None:
        """Should auto-select batch size based on model."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_dict.return_value = []

        out = StringIO()
        call_command("generate_shikonas", "5", stdout=out)

        # Should use auto-selected batch size of 3 for gpt-5-nano
        mock_generator.generate_dict.assert_called_once_with(
            count=5, batch_size=3
        )
        output = out.getvalue()
        self.assertIn("Auto-selected batch size 3", output)

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_retry_on_failure(
        self, mock_generator_class: Mock
    ) -> None:
        """Should retry with smaller batch size on generation failure."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        # First call fails, second succeeds with smaller batch
        mock_generator.generate_dict.side_effect = [
            ShikonaGenerationError("API Error"),
            [
                {
                    "name": "豊昇龍",
                    "transliteration": "hoshoryu",
                    "interpretation": "rising dragon",
                }
            ],
        ]

        out = StringIO()
        call_command("generate_shikonas", "1", "--batch-size", "10", stdout=out)

        # Should have been called twice: first with 10, then with 5
        self.assertEqual(mock_generator.generate_dict.call_count, 2)
        output = out.getvalue()
        self.assertIn("retrying with batch size", output)

        # Verify shikona was created
        self.assertEqual(Shikona.objects.count(), 1)

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_generation_error_after_retries(
        self, mock_generator_class: Mock
    ) -> None:
        """Should raise CommandError when generation fails after all retries."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        # Fail repeatedly until batch size reaches 1, then still fail
        mock_generator.generate_dict.side_effect = ShikonaGenerationError(
            "API Error"
        )

        with self.assertRaises(CommandError) as ctx:
            call_command("generate_shikonas", "2", "--batch-size", "4")

        self.assertIn("Failed to generate shikona", str(ctx.exception))
        # Should have retried multiple times (4 -> 2 -> 1)
        self.assertGreaterEqual(mock_generator.generate_dict.call_count, 3)

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_initialization_error(
        self, mock_generator_class: Mock
    ) -> None:
        """Should raise CommandError when generator initialization fails."""
        mock_generator_class.side_effect = Exception("Initialization failed")

        with self.assertRaises(CommandError) as ctx:
            call_command("generate_shikonas", "2")

        self.assertIn(
            "Failed to initialize ShikonaGenerator", str(ctx.exception)
        )

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_handles_duplicates(
        self, mock_generator_class: Mock
    ) -> None:
        """Should skip duplicate shikona and report them."""
        # Create an existing shikona
        Shikona.objects.create(
            name="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        # Generator returns one duplicate and one new
        mock_generator.generate_dict.return_value = [
            {
                "name": "豊昇龍",
                "transliteration": "hoshoryu",
                "interpretation": "rising dragon",
            },
            {
                "name": "一山本",
                "transliteration": "ichiyamamoto",
                "interpretation": "one mountain base",
            },
        ]

        out = StringIO()
        call_command("generate_shikonas", "2", stdout=out)

        # Should still have 2 total (1 existing + 1 new)
        self.assertEqual(Shikona.objects.count(), 2)

        # Verify output mentions the duplicate
        output = out.getvalue()
        self.assertIn("Successfully created 1 shikona", output)
        self.assertIn("1 duplicates skipped", output)
        self.assertIn("Skipping duplicate: hoshoryu", output)

    @patch("game.management.commands.generate_shikonas.ShikonaGenerator")
    def test_generate_shikonas_shows_sample(
        self, mock_generator_class: Mock
    ) -> None:
        """Should display sample of created shikona."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        mock_generator.generate_dict.return_value = [
            {
                "name": "豊昇龍",
                "transliteration": "hoshoryu",
                "interpretation": "rising dragon",
            },
        ]

        out = StringIO()
        call_command("generate_shikonas", "1", stdout=out)

        output = out.getvalue()
        self.assertIn("Sample of created shikona:", output)
        self.assertIn("hoshoryu", output)
        self.assertIn("豊昇龍", output)
        self.assertIn("rising dragon", output)
