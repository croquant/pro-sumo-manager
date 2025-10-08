"""Tests for the ShikonaGenerator class."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from libs.generators.shikona import (
    ShikonaBatchResponse,
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


class ShikonaBatchResponseTests(unittest.TestCase):
    """Tests for the ShikonaBatchResponse Pydantic model."""

    def test_create_batch_response(self) -> None:
        """Should create a batch response with multiple shikona."""
        rikishi = [
            ShikonaInterpretation(
                shikona="豊昇龍",
                transliteration="hoshoryu",
                interpretation="rising dragon",
            ),
            ShikonaInterpretation(
                shikona="一山本",
                transliteration="ichiyamamoto",
                interpretation="one mountain base",
            ),
        ]
        batch = ShikonaBatchResponse(rikishi=rikishi)
        self.assertEqual(len(batch.rikishi), 2)
        self.assertEqual(batch.rikishi[0].shikona, "豊昇龍")
        self.assertEqual(batch.rikishi[1].shikona, "一山本")


class ShikonaGenerationErrorTests(unittest.TestCase):
    """Tests for the ShikonaGenerationError exception."""

    def test_raise_shikona_generation_error(self) -> None:
        """Should raise ShikonaGenerationError with a message."""
        with self.assertRaises(ShikonaGenerationError) as ctx:
            raise ShikonaGenerationError("Test error")
        self.assertEqual(str(ctx.exception), "Test error")


class ShikonaGeneratorInitTests(unittest.TestCase):
    """Tests for ShikonaGenerator initialization."""

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_init_with_api_key(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should initialize with provided API key."""
        generator = ShikonaGenerator(api_key="test-key", seed=42)
        mock_load_dotenv.assert_called_once()
        mock_openai.assert_called_once_with(api_key="test-key")
        self.assertEqual(generator.model, "gpt-5-nano")
        self.assertIsNotNone(generator.name_generator)

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"})
    def test_init_without_api_key(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should initialize with API key from environment."""
        generator = ShikonaGenerator(seed=42)
        mock_load_dotenv.assert_called_once()
        mock_openai.assert_called_once_with(api_key="env-key")
        self.assertIsNotNone(generator.name_generator)

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_init_with_custom_model(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should initialize with custom model."""
        generator = ShikonaGenerator(api_key="test-key", model="gpt-4")
        self.assertEqual(generator.model, "gpt-4")

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_load_prompt(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should load system prompt from shikona_prompt.md."""
        generator = ShikonaGenerator(api_key="test-key")
        self.assertIsNotNone(generator.system_prompt)
        self.assertIn("shikona", generator.system_prompt.lower())


class ShikonaGeneratorCallOpenAITests(unittest.TestCase):
    """Tests for ShikonaGenerator._call_openai method."""

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_call_openai_success(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should successfully call OpenAI API and return parsed response."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona="豊昇龍",
                    transliteration="hoshoryu",
                    interpretation="rising dragon",
                )
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key")
        result = generator._call_openai(["豊昇龍"])

        self.assertEqual(len(result.rikishi), 1)
        self.assertEqual(result.rikishi[0].shikona, "豊昇龍")
        mock_client.responses.parse.assert_called_once()

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_call_openai_failure(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should raise ShikonaGenerationError on API failure."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.parse.side_effect = Exception("API Error")

        generator = ShikonaGenerator(api_key="test-key")

        with self.assertRaises(ShikonaGenerationError) as ctx:
            generator._call_openai(["豊昇龍"])

        self.assertIn(
            "Failed to process shikona via OpenAI", str(ctx.exception)
        )

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_call_openai_none_response(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should raise ShikonaGenerationError when parsing returns None."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = None
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key")

        with self.assertRaises(ShikonaGenerationError) as ctx:
            generator._call_openai(["豊昇龍"])

        self.assertIn("parsing returned None", str(ctx.exception))


class ShikonaGeneratorGenerateBatchTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_batch method."""

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_generate_batch_single_batch(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should generate a single batch of shikona."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona="豊昇龍",
                    transliteration="hoshoryu",
                    interpretation="rising dragon",
                ),
                ShikonaInterpretation(
                    shikona="一山本",
                    transliteration="ichiyamamoto",
                    interpretation="one mountain base",
                ),
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key", seed=42)
        results = generator.generate_batch(count=2, batch_size=10)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].shikona, "豊昇龍")
        self.assertEqual(results[1].shikona, "一山本")
        mock_client.responses.parse.assert_called_once()

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_generate_batch_multiple_batches(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should handle multiple API calls for large batches."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # First batch
        mock_response_1 = MagicMock()
        mock_response_1.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona=f"名前{i}",
                    transliteration=f"name{i}",
                    interpretation=f"meaning {i}",
                )
                for i in range(3)
            ]
        )

        # Second batch
        mock_response_2 = MagicMock()
        mock_response_2.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona=f"名前{i}",
                    transliteration=f"name{i}",
                    interpretation=f"meaning {i}",
                )
                for i in range(3, 5)
            ]
        )

        mock_client.responses.parse.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        generator = ShikonaGenerator(api_key="test-key", seed=42)
        results = generator.generate_batch(count=5, batch_size=3)

        self.assertEqual(len(results), 5)
        self.assertEqual(mock_client.responses.parse.call_count, 2)

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    @patch("libs.generators.shikona.logger")
    def test_generate_batch_response_mismatch(
        self, mock_logger: Mock, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should log warning when response count doesn't match request."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona="豊昇龍",
                    transliteration="hoshoryu",
                    interpretation="rising dragon",
                )
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key", seed=42)
        results = generator.generate_batch(count=2, batch_size=10)

        # Should still return the results we got
        self.assertEqual(len(results), 1)
        # Should log a warning
        mock_logger.warning.assert_called()

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_generate_batch_ensures_exact_count(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should return exactly the requested count even if more results."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona=f"名前{i}",
                    transliteration=f"name{i}",
                    interpretation=f"meaning {i}",
                )
                for i in range(5)
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key", seed=42)
        results = generator.generate_batch(count=3, batch_size=10)

        # Should slice to exactly 3
        self.assertEqual(len(results), 3)


class ShikonaGeneratorGenerateSingleTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_single method."""

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_generate_single(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should generate a single shikona."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona="豊昇龍",
                    transliteration="hoshoryu",
                    interpretation="rising dragon",
                )
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key", seed=42)
        result = generator.generate_single()

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "豊昇龍")
        self.assertEqual(result.transliteration, "hoshoryu")
        self.assertEqual(result.interpretation, "rising dragon")


class ShikonaGeneratorGenerateDictTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_dict method."""

    @patch("libs.generators.shikona.OpenAI")
    @patch("libs.generators.shikona.load_dotenv")
    def test_generate_dict(
        self, mock_load_dotenv: Mock, mock_openai: Mock
    ) -> None:
        """Should generate shikona as dictionaries for database insertion."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaBatchResponse(
            rikishi=[
                ShikonaInterpretation(
                    shikona="豊昇龍",
                    transliteration="hoshoryu",
                    interpretation="rising dragon",
                ),
                ShikonaInterpretation(
                    shikona="一山本",
                    transliteration="ichiyamamoto",
                    interpretation="one mountain base",
                ),
            ]
        )
        mock_client.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(api_key="test-key", seed=42)
        results = generator.generate_dict(count=2, batch_size=10)

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]["name"], "豊昇龍")
        self.assertEqual(results[0]["transliteration"], "hoshoryu")
        self.assertEqual(results[0]["interpretation"], "rising dragon")
        self.assertEqual(results[1]["name"], "一山本")
        self.assertEqual(results[1]["transliteration"], "ichiyamamoto")
        self.assertEqual(results[1]["interpretation"], "one mountain base")
