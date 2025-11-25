"""Tests for the bout generator."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from libs.generators.bout import (
    BoutGenerator,
    BoutGeneratorInput,
    BoutGeneratorOutput,
)
from libs.generators.rikishi import GeneratedRikishi
from libs.generators.shikona import ShikonaInterpretation
from libs.generators.shusshin import Shusshin


class TestBoutGeneratorInput(unittest.TestCase):
    """Tests for the BoutGeneratorInput Pydantic model."""

    def test_can_create_input_with_valid_data(self) -> None:
        """Should create BoutGeneratorInput with all required fields."""
        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Abundant Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=60,
            current=40,
            strength=10,
            technique=8,
            balance=9,
            endurance=7,
            mental=6,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="若元春",
                transliteration="Wakamotoharu",
                interpretation="Young Origin Spring",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-47"),
            potential=55,
            current=35,
            strength=8,
            technique=7,
            balance=8,
            endurance=6,
            mental=6,
        )
        fortune = [5, 10, 8, 12, 3]

        input_data = BoutGeneratorInput(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=fortune,
        )

        self.assertEqual(input_data.east_rikishi, east_rikishi)
        self.assertEqual(input_data.west_rikishi, west_rikishi)
        self.assertEqual(input_data.fortune, fortune)

    def test_fortune_can_be_empty_list(self) -> None:
        """Fortune can be an empty list (though unusual)."""
        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="照ノ富士",
                transliteration="Terunofuji",
                interpretation="Shining Fuji",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=90,
            current=75,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="貴景勝",
                transliteration="Takakeisho",
                interpretation="Noble Victory",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-28"),
            potential=70,
            current=60,
        )

        input_data = BoutGeneratorInput(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=[],
        )

        self.assertEqual(input_data.fortune, [])

    def test_fortune_can_include_critical_values(self) -> None:
        """Fortune can include special values like -5 and 20."""
        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="朝青龍",
                transliteration="Asashoryu",
                interpretation="Morning Blue Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=95,
            current=85,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="白鵬",
                transliteration="Hakuho",
                interpretation="White Phoenix",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=98,
            current=88,
        )

        input_data = BoutGeneratorInput(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=[-5, 20, 10, 0, 13],
        )

        self.assertIn(-5, input_data.fortune)
        self.assertIn(20, input_data.fortune)


class TestBoutGeneratorOutput(unittest.TestCase):
    """Tests for the BoutGeneratorOutput Pydantic model."""

    def test_can_create_output_with_valid_data(self) -> None:
        """Should create BoutGeneratorOutput with all required fields."""
        output = BoutGeneratorOutput(
            thinking="Step-by-step analysis of the bout",
            winner="east",
            commentary=[
                "East side Hoshoryu faces west side Wakamotoharu.",
                "The tachi-ai is fierce.",
                "Victory by yorikiri.",
            ],
            kimarite="yorikiri",
            excitement_level=7.5,
            east_xp_gain=25,
            west_xp_gain=18,
        )

        self.assertEqual(output.winner, "east")
        self.assertEqual(output.kimarite, "yorikiri")
        self.assertEqual(output.excitement_level, 7.5)
        self.assertEqual(output.east_xp_gain, 25)
        self.assertEqual(output.west_xp_gain, 18)
        self.assertEqual(len(output.commentary), 3)

    def test_winner_must_be_east_or_west(self) -> None:
        """Winner field should only accept 'east' or 'west'."""
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            BoutGeneratorOutput(
                thinking="Analysis",
                winner="north",  # type: ignore[arg-type]
                commentary=["Line 1"],
                kimarite="yorikiri",
                excitement_level=5.0,
                east_xp_gain=10,
                west_xp_gain=5,
            )

    def test_kimarite_must_be_valid_technique(self) -> None:
        """Kimarite must be one of the 18 valid techniques."""
        from pydantic import ValidationError

        # Valid kimarite should work
        valid_output = BoutGeneratorOutput(
            thinking="Analysis",
            winner="west",
            commentary=["Victory"],
            kimarite="uwatenage",
            excitement_level=8.0,
            east_xp_gain=10,
            west_xp_gain=15,
        )
        self.assertEqual(valid_output.kimarite, "uwatenage")

        # Invalid kimarite should fail
        with self.assertRaises(ValidationError):
            BoutGeneratorOutput(
                thinking="Analysis",
                winner="east",
                commentary=["Victory"],
                kimarite="invalid_technique",  # type: ignore[arg-type]
                excitement_level=5.0,
                east_xp_gain=10,
                west_xp_gain=5,
            )

    def test_excitement_level_must_be_between_1_and_10(self) -> None:
        """Excitement level should be bounded between 1.0 and 10.0."""
        from pydantic import ValidationError

        # Valid excitement levels
        for level in [1.0, 5.5, 10.0]:
            output = BoutGeneratorOutput(
                thinking="Analysis",
                winner="east",
                commentary=["Victory"],
                kimarite="yorikiri",
                excitement_level=level,
                east_xp_gain=10,
                west_xp_gain=5,
            )
            self.assertEqual(output.excitement_level, level)

        # Below minimum
        with self.assertRaises(ValidationError):
            BoutGeneratorOutput(
                thinking="Analysis",
                winner="east",
                commentary=["Victory"],
                kimarite="yorikiri",
                excitement_level=0.5,
                east_xp_gain=10,
                west_xp_gain=5,
            )

        # Above maximum
        with self.assertRaises(ValidationError):
            BoutGeneratorOutput(
                thinking="Analysis",
                winner="east",
                commentary=["Victory"],
                kimarite="yorikiri",
                excitement_level=10.5,
                east_xp_gain=10,
                west_xp_gain=5,
            )

    def test_xp_gains_must_be_non_negative(self) -> None:
        """XP gain values must be >= 0."""
        from pydantic import ValidationError

        # Zero XP is valid
        output = BoutGeneratorOutput(
            thinking="Analysis",
            winner="east",
            commentary=["Victory"],
            kimarite="yorikiri",
            excitement_level=5.0,
            east_xp_gain=0,
            west_xp_gain=0,
        )
        self.assertEqual(output.east_xp_gain, 0)
        self.assertEqual(output.west_xp_gain, 0)

        # Negative XP for east should fail
        with self.assertRaises(ValidationError):
            BoutGeneratorOutput(
                thinking="Analysis",
                winner="east",
                commentary=["Victory"],
                kimarite="yorikiri",
                excitement_level=5.0,
                east_xp_gain=-5,
                west_xp_gain=5,
            )

        # Negative XP for west should fail
        with self.assertRaises(ValidationError):
            BoutGeneratorOutput(
                thinking="Analysis",
                winner="east",
                commentary=["Victory"],
                kimarite="yorikiri",
                excitement_level=5.0,
                east_xp_gain=10,
                west_xp_gain=-3,
            )

    def test_commentary_can_be_multiple_lines(self) -> None:
        """Commentary should support multiple lines."""
        commentary_lines = [
            "East side fighter charges forward.",
            "West side fighter attempts a throw.",
            "Grip battle ensues at center.",
            "East fighter gains advantage.",
            "Victory by yorikiri.",
        ]

        output = BoutGeneratorOutput(
            thinking="Analysis",
            winner="east",
            commentary=commentary_lines,
            kimarite="yorikiri",
            excitement_level=7.0,
            east_xp_gain=20,
            west_xp_gain=15,
        )

        self.assertEqual(len(output.commentary), 5)
        self.assertEqual(output.commentary, commentary_lines)

    def test_all_valid_kimarite_values_accepted(self) -> None:
        """All 18 valid kimarite techniques should be accepted."""
        valid_kimarite = [
            "yorikiri",
            "oshidashi",
            "hatakikomi",
            "uwatenage",
            "shitatenage",
            "tsuppari",
            "kotenage",
            "yori-taoshi",
            "oshitaoshi",
            "hikiotoshi",
            "uwatedashinage",
            "shitatedashinage",
            "tsukiotoshi",
            "sukuinage",
            "tottari",
            "ketaguri",
            "utchari",
            "katasukashi",
        ]

        for technique in valid_kimarite:
            with self.subTest(kimarite=technique):
                output = BoutGeneratorOutput(
                    thinking="Analysis",
                    winner="east",
                    commentary=["Victory"],
                    kimarite=technique,  # type: ignore[arg-type]
                    excitement_level=5.0,
                    east_xp_gain=10,
                    west_xp_gain=5,
                )
                self.assertEqual(output.kimarite, technique)


class TestBoutGenerator(unittest.TestCase):
    """Tests for the BoutGenerator class."""

    def _create_mock_response(
        self,
        winner: str = "east",
        kimarite: str = "yorikiri",
        excitement: float = 7.0,
    ) -> MagicMock:
        """Create a mock OpenAI response for testing."""
        mock_response = MagicMock()
        mock_response.output_parsed = BoutGeneratorOutput(
            thinking="Mock analysis of the bout",
            winner=winner,  # type: ignore[arg-type]
            commentary=[
                "East side fighter faces west side fighter.",
                "The tachi-ai is fierce.",
                f"Victory by {kimarite}.",
            ],
            kimarite=kimarite,  # type: ignore[arg-type]
            excitement_level=excitement,
            east_xp_gain=25,
            west_xp_gain=18,
        )
        mock_response.usage = {"total_tokens": 500}
        return mock_response

    def test_generator_initialization_with_seed(self) -> None:
        """Should initialize generator with seed for deterministic fortune."""
        gen1 = BoutGenerator(seed=42)
        gen2 = BoutGenerator(seed=42)

        # Both generators should produce same fortune sequence
        fortune1 = [gen1.random.randint(0, 13) for _ in range(5)]
        fortune2 = [gen2.random.randint(0, 13) for _ in range(5)]

        self.assertEqual(fortune1, fortune2)

    def test_generator_initialization_with_model(self) -> None:
        """Should initialize generator with specified model."""
        gen = BoutGenerator(model="gpt-5-mini", seed=42)
        self.assertEqual(gen.model, "gpt-5-mini")

    def test_generate_produces_valid_output(self) -> None:
        """Should generate a valid bout output."""
        gen = BoutGenerator(seed=42)

        # Configure the mock client
        mock_response = self._create_mock_response()
        gen.client.responses.parse.return_value = mock_response  # type: ignore[attr-defined]

        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Abundant Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=60,
            current=40,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="若元春",
                transliteration="Wakamotoharu",
                interpretation="Young Origin Spring",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-47"),
            potential=55,
            current=35,
        )

        result = gen.generate(east_rikishi, west_rikishi)

        self.assertIsInstance(result, BoutGeneratorOutput)
        self.assertIn(result.winner, ["east", "west"])
        self.assertIsNotNone(result.kimarite)
        self.assertGreaterEqual(result.excitement_level, 1.0)
        self.assertLessEqual(result.excitement_level, 10.0)
        self.assertGreaterEqual(result.east_xp_gain, 0)
        self.assertGreaterEqual(result.west_xp_gain, 0)

    def test_generate_calls_openai_with_correct_parameters(self) -> None:
        """Should call OpenAI API with correct model and input format."""
        gen = BoutGenerator(model="gpt-5-mini", seed=42)

        mock_response = self._create_mock_response()
        gen.client.responses.parse.return_value = mock_response  # type: ignore[attr-defined]

        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="照ノ富士",
                transliteration="Terunofuji",
                interpretation="Shining Fuji",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=90,
            current=75,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="貴景勝",
                transliteration="Takakeisho",
                interpretation="Noble Victory",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-28"),
            potential=70,
            current=60,
        )

        gen.generate(east_rikishi, west_rikishi)

        # Verify the API was called
        gen.client.responses.parse.assert_called_once()  # type: ignore[attr-defined]
        call_kwargs = gen.client.responses.parse.call_args[1]  # type: ignore[attr-defined]

        # Check parameters
        self.assertEqual(call_kwargs["model"], "gpt-5-mini")
        self.assertEqual(call_kwargs["reasoning"]["effort"], "low")
        self.assertEqual(call_kwargs["text_format"], BoutGeneratorOutput)

        # Check input structure
        input_messages = call_kwargs["input"]
        self.assertEqual(len(input_messages), 2)
        self.assertEqual(input_messages[0]["role"], "system")
        self.assertEqual(input_messages[1]["role"], "user")

    def test_generate_includes_fortune_in_input(self) -> None:
        """Should include fortune values in the API input."""
        gen = BoutGenerator(seed=42)

        mock_response = self._create_mock_response()
        gen.client.responses.parse.return_value = mock_response  # type: ignore[attr-defined]

        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="若隆景",
                transliteration="Wakatakakage",
                interpretation="Young Prosperous View",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-28"),
            potential=65,
            current=50,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="阿炎",
                transliteration="Abi",
                interpretation="Noble Fire",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-13"),
            potential=60,
            current=45,
        )

        gen.generate(east_rikishi, west_rikishi)

        # Get the user input from the API call
        call_kwargs = gen.client.responses.parse.call_args[1]  # type: ignore[attr-defined]
        user_input = call_kwargs["input"][1]["content"]

        # Parse the JSON input
        import json

        input_data = json.loads(user_input)

        # Verify fortune is included and has expected structure
        self.assertIn("fortune", input_data)
        self.assertIsInstance(input_data["fortune"], list)
        self.assertEqual(len(input_data["fortune"]), 5)
        # Fortune values should be in range 0-13
        for value in input_data["fortune"]:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 13)

    def test_generate_raises_error_when_parsing_fails(self) -> None:
        """Should raise ValueError when API response cannot be parsed."""
        gen = BoutGenerator(seed=42)

        # Configure mock to return None for output_parsed
        mock_response = MagicMock()
        mock_response.output_parsed = None
        gen.client.responses.parse.return_value = mock_response  # type: ignore[attr-defined]

        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="明生",
                transliteration="Meisei",
                interpretation="Bright Life",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-45"),
            potential=50,
            current=30,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="隆の勝",
                transliteration="Takanotsuru",
                interpretation="Prosperous Victory",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-11"),
            potential=48,
            current=28,
        )

        with self.assertRaises(ValueError) as context:
            gen.generate(east_rikishi, west_rikishi)

        self.assertIn("Failed to parse", str(context.exception))

    def test_different_seeds_produce_different_fortune(self) -> None:
        """Different seeds should produce different fortune sequences."""
        gen1 = BoutGenerator(seed=42)
        gen2 = BoutGenerator(seed=100)

        fortune1 = [gen1.random.randint(0, 13) for _ in range(5)]
        fortune2 = [gen2.random.randint(0, 13) for _ in range(5)]

        # At least some values should be different
        self.assertNotEqual(fortune1, fortune2)

    def test_system_prompt_loads_correctly(self) -> None:
        """System prompt should be loaded at class level."""
        # The prompt should be loaded once and accessible
        self.assertIsInstance(BoutGenerator._system_prompt, str)
        self.assertGreater(len(BoutGenerator._system_prompt), 0)

        # Should contain key sections from the prompt
        self.assertIn(
            "sumo bout simulator", BoutGenerator._system_prompt.lower()
        )
        self.assertIn("kimarite", BoutGenerator._system_prompt.lower())

    def test_generate_with_evenly_matched_fighters(self) -> None:
        """Should handle evenly matched fighters correctly."""
        gen = BoutGenerator(seed=42)

        mock_response = self._create_mock_response(
            winner="west", kimarite="uwatenage", excitement=9.5
        )
        gen.client.responses.parse.return_value = mock_response  # type: ignore[attr-defined]

        # Create two evenly matched rikishi
        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="一山本",
                transliteration="Ichiyamamoto",
                interpretation="One Mountain Origin",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-08"),
            potential=55,
            current=40,
            strength=10,
            technique=8,
            balance=8,
            endurance=7,
            mental=7,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="錦富士",
                transliteration="Nishikifuji",
                interpretation="Brocade Fuji",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-28"),
            potential=56,
            current=41,
            strength=9,
            technique=9,
            balance=8,
            endurance=7,
            mental=8,
        )

        result = gen.generate(east_rikishi, west_rikishi)

        # Should produce valid result
        self.assertIsInstance(result, BoutGeneratorOutput)
        self.assertIn(result.winner, ["east", "west"])

    def test_generate_with_severe_mismatch(self) -> None:
        """Should handle severe ability mismatch correctly."""
        gen = BoutGenerator(seed=42)

        mock_response = self._create_mock_response(
            winner="east", kimarite="oshidashi", excitement=2.5
        )
        gen.client.responses.parse.return_value = mock_response  # type: ignore[attr-defined]

        # Create mismatched fighters (elite vs beginner)
        east_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="大栄翔",
                transliteration="Daieisho",
                interpretation="Great Prosperous Soar",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-34"),
            potential=85,
            current=70,
            strength=18,
            technique=15,
            balance=14,
            endurance=13,
            mental=10,
        )
        west_rikishi = GeneratedRikishi(
            shikona=ShikonaInterpretation(
                shikona="新人",
                transliteration="Shinjin",
                interpretation="Newcomer",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-01"),
            potential=20,
            current=8,
            strength=2,
            technique=2,
            balance=1,
            endurance=2,
            mental=1,
        )

        result = gen.generate(east_rikishi, west_rikishi)

        # Should produce valid result
        self.assertIsInstance(result, BoutGeneratorOutput)

    def test_fortune_generation_produces_expected_range(self) -> None:
        """Generated fortune values should be in range 0-13."""
        gen = BoutGenerator(seed=42)

        # Generate many fortune sequences
        for _ in range(100):
            fortune = [gen.random.randint(0, 13) for _ in range(5)]
            for value in fortune:
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 13)

    def test_generator_uses_same_seed_for_fortune(self) -> None:
        """Generator should use consistent seed for fortune generation."""
        gen = BoutGenerator(seed=42)

        # Generate two fortune sequences
        fortune1 = [gen.random.randint(0, 13) for _ in range(5)]

        # Reset generator with same seed
        gen2 = BoutGenerator(seed=42)
        fortune2 = [gen2.random.randint(0, 13) for _ in range(5)]

        # Should match
        self.assertEqual(fortune1, fortune2)
