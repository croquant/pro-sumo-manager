"""Tests for the ShikonaGenerator class."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from libs.generators.shikona import (
    ShikonaGenerationError,
    ShikonaGenerator,
    ShikonaInterpretation,
)


class ShikonaInterpretationTests(unittest.TestCase):
    """Tests for the ShikonaInterpretation Pydantic model."""

    def test_create_shikona_interpretation(self) -> None:
        """Should create a ShikonaInterpretation with all fields."""
        interp = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        self.assertEqual(interp.shikona, "豊昇龍")
        self.assertEqual(interp.transliteration, "hoshoryu")
        self.assertEqual(interp.interpretation, "rising dragon")


class ShikonaGenerationErrorTests(unittest.TestCase):
    """Tests for the ShikonaGenerationError exception."""

    def test_raise_shikona_generation_error(self) -> None:
        """Should raise ShikonaGenerationError with a message."""
        with self.assertRaises(ShikonaGenerationError) as ctx:
            raise ShikonaGenerationError("Test error")
        self.assertEqual(str(ctx.exception), "Test error")


class ShikonaGeneratorInitTests(unittest.TestCase):
    """Tests for ShikonaGenerator initialization."""

    @patch("libs.generators.shikona.openai_singleton")
    def test_init_with_seed(self, mock_singleton: MagicMock) -> None:
        """Should initialize with provided seed."""
        generator = ShikonaGenerator(seed=42)
        self.assertIsNotNone(generator.name_generator)
        self.assertEqual(generator.client, mock_singleton)

    @patch("libs.generators.shikona.openai_singleton")
    def test_init_without_seed(self, mock_singleton: MagicMock) -> None:
        """Should initialize without seed (random generation)."""
        generator = ShikonaGenerator()
        self.assertIsNotNone(generator.name_generator)
        self.assertEqual(generator.client, mock_singleton)

    @patch("libs.generators.shikona.openai_singleton")
    def test_load_system_prompt(self, mock_singleton: MagicMock) -> None:
        """Should load system prompt from shikona_prompt.md."""
        generator = ShikonaGenerator()
        self.assertIsNotNone(generator._system_prompt)
        self.assertIn("shikona", generator._system_prompt.lower())


class ShikonaGeneratorCallOpenAITests(unittest.TestCase):
    """Tests for ShikonaGenerator._call_openai method."""

    @patch("libs.generators.shikona.openai_singleton")
    def test_call_openai_success(self, mock_singleton: MagicMock) -> None:
        """Should successfully call OpenAI API and return parsed response."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        mock_singleton.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator._call_openai("豊昇龍")

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "豊昇龍")
        self.assertEqual(result.transliteration, "hoshoryu")
        self.assertEqual(result.interpretation, "rising dragon")
        mock_singleton.responses.parse.assert_called_once()

    @patch("libs.generators.shikona.openai_singleton")
    def test_call_openai_failure(self, mock_singleton: MagicMock) -> None:
        """Should raise ShikonaGenerationError on API failure."""
        mock_singleton.responses.parse.side_effect = Exception("API Error")

        generator = ShikonaGenerator(seed=42)

        with self.assertRaises(ShikonaGenerationError) as ctx:
            generator._call_openai("豊昇龍")

        self.assertIn(
            "Failed to process shikona via OpenAI", str(ctx.exception)
        )

    @patch("libs.generators.shikona.openai_singleton")
    def test_call_openai_none_response(self, mock_singleton: MagicMock) -> None:
        """Should raise ShikonaGenerationError when parsing returns None."""
        mock_response = MagicMock()
        mock_response.output_parsed = None
        mock_singleton.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)

        with self.assertRaises(ShikonaGenerationError) as ctx:
            generator._call_openai("豊昇龍")

        self.assertIn("parsing returned None", str(ctx.exception))


class ShikonaGeneratorGenerateSingleTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_single method."""

    @patch("libs.generators.shikona.openai_singleton")
    def test_generate_single(self, mock_singleton: MagicMock) -> None:
        """Should generate a single shikona."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        mock_singleton.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator.generate_single()

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "豊昇龍")
        self.assertEqual(result.transliteration, "hoshoryu")
        self.assertEqual(result.interpretation, "rising dragon")


class ShikonaGeneratorGenerateBatchTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_batch method."""

    @patch("libs.generators.shikona.openai_singleton")
    def test_generate_batch_multiple(self, mock_singleton: MagicMock) -> None:
        """Should generate multiple shikona one by one."""
        # Create 3 individual responses
        mock_responses = [
            MagicMock(
                output_parsed=ShikonaInterpretation(
                    shikona="豊昇龍",
                    transliteration="hoshoryu",
                    interpretation="rising dragon",
                )
            ),
            MagicMock(
                output_parsed=ShikonaInterpretation(
                    shikona="一山本",
                    transliteration="ichiyamamoto",
                    interpretation="one mountain base",
                )
            ),
            MagicMock(
                output_parsed=ShikonaInterpretation(
                    shikona="都留樹富士",
                    transliteration="tsurugifuji",
                    interpretation="rooted fuji strength",
                )
            ),
        ]
        mock_singleton.responses.parse.side_effect = mock_responses

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(count=3)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].shikona, "豊昇龍")
        self.assertEqual(results[1].shikona, "一山本")
        self.assertEqual(results[2].shikona, "都留樹富士")
        # Should make 3 individual API calls
        self.assertEqual(mock_singleton.responses.parse.call_count, 3)

    @patch("libs.generators.shikona.openai_singleton")
    def test_generate_batch_single(self, mock_singleton: MagicMock) -> None:
        """Should generate a single shikona when count=1."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        mock_singleton.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(count=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].shikona, "豊昇龍")
        self.assertEqual(mock_singleton.responses.parse.call_count, 1)

    @patch("libs.generators.shikona.openai_singleton")
    def test_generate_batch_invalid_count(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should raise ValueError when count is not positive."""
        generator = ShikonaGenerator(seed=42)

        with self.assertRaises(ValueError) as ctx:
            generator.generate_batch(count=0)

        self.assertIn("must be positive", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            generator.generate_batch(count=-5)

        self.assertIn("must be positive", str(ctx.exception))
