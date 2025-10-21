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

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_init_with_seed(self, mock_singleton: MagicMock) -> None:
        """Should initialize with provided seed."""
        generator = ShikonaGenerator(seed=42)
        self.assertIsNotNone(generator.name_generator)
        self.assertEqual(generator.client, mock_singleton.return_value)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_init_without_seed(self, mock_singleton: MagicMock) -> None:
        """Should initialize without seed (random generation)."""
        generator = ShikonaGenerator()
        self.assertIsNotNone(generator.name_generator)
        self.assertEqual(generator.client, mock_singleton.return_value)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_load_system_prompt(self, mock_singleton: MagicMock) -> None:
        """Should load system prompt from shikona_prompt.md."""
        generator = ShikonaGenerator()
        self.assertIsNotNone(generator._system_prompt)
        self.assertIn("shikona", generator._system_prompt.lower())


class ShikonaGeneratorCallOpenAITests(unittest.TestCase):
    """Tests for ShikonaGenerator._call_openai method."""

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_call_openai_success(self, mock_singleton: MagicMock) -> None:
        """Should successfully call OpenAI API and return parsed response."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator._call_openai("豊昇龍")

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "豊昇龍")
        self.assertEqual(result.transliteration, "hoshoryu")
        self.assertEqual(result.interpretation, "rising dragon")
        mock_singleton.return_value.responses.parse.assert_called_once()

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_call_openai_with_parent(self, mock_singleton: MagicMock) -> None:
        """Should call OpenAI with formatted parent message."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="太昇龍",
            transliteration="taishoryu",
            interpretation="great rising dragon",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator._call_openai("太郎山", parent_shikona="豊昇龍")

        self.assertIsInstance(result, ShikonaInterpretation)
        # Verify the user message was formatted correctly
        call_args = mock_singleton.return_value.responses.parse.call_args
        user_message = call_args[1]["input"][1]["content"]
        self.assertIn("GENERATED: 太郎山", user_message)
        self.assertIn("PARENT: 豊昇龍", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_call_openai_with_shusshin(self, mock_singleton: MagicMock) -> None:
        """Should call OpenAI with formatted shusshin message."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="蒼鷹山",
            transliteration="sotakayama",
            interpretation="blue hawk mountain",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator._call_openai("太郎山", shusshin="Mongolia")

        self.assertIsInstance(result, ShikonaInterpretation)
        # Verify the user message was formatted correctly
        call_args = mock_singleton.return_value.responses.parse.call_args
        user_message = call_args[1]["input"][1]["content"]
        self.assertIn("GENERATED: 太郎山", user_message)
        self.assertIn("SHUSSHIN: Mongolia", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_call_openai_with_parent_and_shusshin(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should call OpenAI with both parent and shusshin."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="白桜",
            transliteration="hakuo",
            interpretation="white cherry",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator._call_openai(
            "力山", parent_shikona="白鵬", shusshin="Tokyo"
        )

        self.assertIsInstance(result, ShikonaInterpretation)
        # Verify the user message was formatted correctly
        call_args = mock_singleton.return_value.responses.parse.call_args
        user_message = call_args[1]["input"][1]["content"]
        self.assertIn("GENERATED: 力山", user_message)
        self.assertIn("PARENT: 白鵬", user_message)
        self.assertIn("SHUSSHIN: Tokyo", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_call_openai_failure(self, mock_singleton: MagicMock) -> None:
        """Should raise ShikonaGenerationError on API failure."""
        mock_singleton.return_value.responses.parse.side_effect = Exception(
            "API Error"
        )

        generator = ShikonaGenerator(seed=42)

        with self.assertRaises(ShikonaGenerationError) as ctx:
            generator._call_openai("豊昇龍")

        self.assertIn(
            "Failed to process shikona via OpenAI", str(ctx.exception)
        )

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_call_openai_none_response(self, mock_singleton: MagicMock) -> None:
        """Should raise ShikonaGenerationError when parsing returns None."""
        mock_response = MagicMock()
        mock_response.output_parsed = None
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)

        with self.assertRaises(ShikonaGenerationError) as ctx:
            generator._call_openai("豊昇龍")

        self.assertIn("parsing returned None", str(ctx.exception))


class ShikonaGeneratorGenerateSingleTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_single method."""

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_single(self, mock_singleton: MagicMock) -> None:
        """Should generate a single shikona."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator.generate_single()

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "豊昇龍")
        self.assertEqual(result.transliteration, "hoshoryu")
        self.assertEqual(result.interpretation, "rising dragon")

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_single_with_parent(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate a single shikona related to parent."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="太昇龍",
            transliteration="taishoryu",
            interpretation="great rising dragon",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator.generate_single(parent_shikona="豊昇龍")

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "太昇龍")
        # Verify parent was passed to API
        call_args = mock_singleton.return_value.responses.parse.call_args
        user_message = call_args[1]["input"][1]["content"]
        self.assertIn("PARENT: 豊昇龍", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_single_with_shusshin(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate a single shikona with origin themes."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="蒼鷹",
            transliteration="sotaka",
            interpretation="blue hawk",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator.generate_single(shusshin="Mongolia")

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "蒼鷹")
        # Verify shusshin was passed to API
        call_args = mock_singleton.return_value.responses.parse.call_args
        user_message = call_args[1]["input"][1]["content"]
        self.assertIn("SHUSSHIN: Mongolia", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_single_with_parent_and_shusshin(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate a shikona with both parent and origin."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="白桜",
            transliteration="hakuo",
            interpretation="white cherry",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        result = generator.generate_single(
            parent_shikona="白鵬", shusshin="Tokyo"
        )

        self.assertIsInstance(result, ShikonaInterpretation)
        self.assertEqual(result.shikona, "白桜")
        # Verify both were passed to API
        call_args = mock_singleton.return_value.responses.parse.call_args
        user_message = call_args[1]["input"][1]["content"]
        self.assertIn("PARENT: 白鵬", user_message)
        self.assertIn("SHUSSHIN: Tokyo", user_message)


class ShikonaGeneratorGenerateBatchTests(unittest.TestCase):
    """Tests for ShikonaGenerator.generate_batch method."""

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_batch_multiple(self, mock_singleton: MagicMock) -> None:
        """Should generate multiple shikona one by one."""
        # Create 3 individual responses
        mock_responses = []
        for interp_data in [
            ("豊昇龍", "hoshoryu", "rising dragon"),
            ("一山本", "ichiyamamoto", "one mountain base"),
            ("都留樹富士", "tsurugifuji", "rooted fuji strength"),
        ]:
            mock_resp = MagicMock()
            mock_resp.output_parsed = ShikonaInterpretation(
                shikona=interp_data[0],
                transliteration=interp_data[1],
                interpretation=interp_data[2],
            )
            mock_resp.usage = MagicMock()
            mock_responses.append(mock_resp)
        mock_singleton.return_value.responses.parse.side_effect = mock_responses

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(count=3)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].shikona, "豊昇龍")
        self.assertEqual(results[1].shikona, "一山本")
        self.assertEqual(results[2].shikona, "都留樹富士")
        # Should make 3 individual API calls
        self.assertEqual(
            mock_singleton.return_value.responses.parse.call_count, 3
        )

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_batch_with_parent(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate multiple shikona related to parent."""
        # Create 2 individual responses with parent-related names
        mock_responses = []
        for interp_data in [
            ("豊山", "toyoyama", "abundant mountain"),
            ("太昇龍", "taishoryu", "great rising dragon"),
        ]:
            mock_resp = MagicMock()
            mock_resp.output_parsed = ShikonaInterpretation(
                shikona=interp_data[0],
                transliteration=interp_data[1],
                interpretation=interp_data[2],
            )
            mock_resp.usage = MagicMock()
            mock_responses.append(mock_resp)
        mock_singleton.return_value.responses.parse.side_effect = mock_responses

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(count=2, parent_shikona="豊昇龍")

        self.assertEqual(len(results), 2)
        # Verify parent was passed to all API calls
        self.assertEqual(
            mock_singleton.return_value.responses.parse.call_count, 2
        )
        for call in mock_singleton.return_value.responses.parse.call_args_list:
            user_message = call[1]["input"][1]["content"]
            self.assertIn("PARENT: 豊昇龍", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_batch_with_shusshin(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate multiple shikona with origin themes."""
        # Create 2 individual responses with Mongolia-themed names
        mock_responses = []
        for interp_data in [
            ("蒼鷹", "sotaka", "blue hawk"),
            ("翔馬", "shoma", "soaring horse"),
        ]:
            mock_resp = MagicMock()
            mock_resp.output_parsed = ShikonaInterpretation(
                shikona=interp_data[0],
                transliteration=interp_data[1],
                interpretation=interp_data[2],
            )
            mock_resp.usage = MagicMock()
            mock_responses.append(mock_resp)
        mock_singleton.return_value.responses.parse.side_effect = mock_responses

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(count=2, shusshin="Mongolia")

        self.assertEqual(len(results), 2)
        # Verify shusshin was passed to all API calls
        self.assertEqual(
            mock_singleton.return_value.responses.parse.call_count, 2
        )
        for call in mock_singleton.return_value.responses.parse.call_args_list:
            user_message = call[1]["input"][1]["content"]
            self.assertIn("SHUSSHIN: Mongolia", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_batch_with_parent_and_shusshin(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate multiple shikona with both parent and origin."""
        # Create 2 individual responses
        mock_responses = []
        for interp_data in [
            ("白桜", "hakuo", "white cherry"),
            ("白都", "hakuto", "white capital"),
        ]:
            mock_resp = MagicMock()
            mock_resp.output_parsed = ShikonaInterpretation(
                shikona=interp_data[0],
                transliteration=interp_data[1],
                interpretation=interp_data[2],
            )
            mock_resp.usage = MagicMock()
            mock_responses.append(mock_resp)
        mock_singleton.return_value.responses.parse.side_effect = mock_responses

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(
            count=2, parent_shikona="白鵬", shusshin="Tokyo"
        )

        self.assertEqual(len(results), 2)
        # Verify both parent and shusshin were passed to all API calls
        self.assertEqual(
            mock_singleton.return_value.responses.parse.call_count, 2
        )
        for call in mock_singleton.return_value.responses.parse.call_args_list:
            user_message = call[1]["input"][1]["content"]
            self.assertIn("PARENT: 白鵬", user_message)
            self.assertIn("SHUSSHIN: Tokyo", user_message)

    @patch("libs.generators.shikona.get_openai_singleton")
    def test_generate_batch_single(self, mock_singleton: MagicMock) -> None:
        """Should generate a single shikona when count=1."""
        mock_response = MagicMock()
        mock_response.output_parsed = ShikonaInterpretation(
            shikona="豊昇龍",
            transliteration="hoshoryu",
            interpretation="rising dragon",
        )
        mock_response.usage = MagicMock()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        generator = ShikonaGenerator(seed=42)
        results = generator.generate_batch(count=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].shikona, "豊昇龍")
        self.assertEqual(
            mock_singleton.return_value.responses.parse.call_count, 1
        )

    @patch("libs.generators.shikona.get_openai_singleton")
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
