"""Tests for the bout generator."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from libs.generators.bout import BoutGenerator
from libs.types.bout import Bout, BoutContext
from libs.types.rikishi import Rikishi
from libs.types.shikona import Shikona
from libs.types.shusshin import Shusshin


class TestBoutContext(unittest.TestCase):
    """Tests for the BoutContext Pydantic model."""

    def test_can_create_context_with_valid_data(self) -> None:
        """Should create BoutContext with all required fields."""
        east_rikishi = Rikishi(
            shikona=Shikona(
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
        west_rikishi = Rikishi(
            shikona=Shikona(
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

        context = BoutContext(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=fortune,
        )

        self.assertEqual(context.east_rikishi, east_rikishi)
        self.assertEqual(context.west_rikishi, west_rikishi)
        self.assertEqual(context.fortune, fortune)

    def test_fortune_can_be_empty_list(self) -> None:
        """Fortune can be an empty list (though unusual)."""
        east_rikishi = Rikishi(
            shikona=Shikona(
                shikona="照ノ富士",
                transliteration="Terunofuji",
                interpretation="Shining Fuji",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=90,
            current=75,
        )
        west_rikishi = Rikishi(
            shikona=Shikona(
                shikona="貴景勝",
                transliteration="Takakeisho",
                interpretation="Noble Victory",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-28"),
            potential=70,
            current=60,
        )

        context = BoutContext(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=[],
        )

        self.assertEqual(context.fortune, [])

    def test_fortune_can_include_critical_values(self) -> None:
        """Fortune can include special values like -5 and 20."""
        east_rikishi = Rikishi(
            shikona=Shikona(
                shikona="朝青龍",
                transliteration="Asashoryu",
                interpretation="Morning Blue Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=95,
            current=85,
        )
        west_rikishi = Rikishi(
            shikona=Shikona(
                shikona="白鵬",
                transliteration="Hakuho",
                interpretation="White Phoenix",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=98,
            current=88,
        )

        context = BoutContext(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=[-5, 20, 10, 0, 13],
        )

        self.assertIn(-5, context.fortune)
        self.assertIn(20, context.fortune)


class TestBout(unittest.TestCase):
    """Tests for the Bout Pydantic model."""

    def test_can_create_bout_with_valid_data(self) -> None:
        """Should create Bout with all required fields."""
        bout = Bout(
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

        self.assertEqual(bout.winner, "east")
        self.assertEqual(bout.kimarite, "yorikiri")
        self.assertEqual(bout.excitement_level, 7.5)
        self.assertEqual(bout.east_xp_gain, 25)
        self.assertEqual(bout.west_xp_gain, 18)
        self.assertEqual(len(bout.commentary), 3)

    def test_winner_must_be_east_or_west(self) -> None:
        """Winner field should only accept 'east' or 'west'."""
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            Bout(
                thinking="Analysis",
                winner="north",  # type: ignore[arg-type]
                commentary=["Line 1", "Line 2", "Line 3"],
                kimarite="yorikiri",
                excitement_level=5.0,
                east_xp_gain=10,
                west_xp_gain=5,
            )

    def test_kimarite_must_be_valid_technique(self) -> None:
        """Kimarite must be one of the 18 valid techniques."""
        from pydantic import ValidationError

        # Valid kimarite should work
        valid_bout = Bout(
            thinking="Analysis",
            winner="west",
            commentary=["Start", "Middle", "Victory"],
            kimarite="uwatenage",
            excitement_level=8.0,
            east_xp_gain=10,
            west_xp_gain=15,
        )
        self.assertEqual(valid_bout.kimarite, "uwatenage")

        # Invalid kimarite should fail
        with self.assertRaises(ValidationError):
            Bout(
                thinking="Analysis",
                winner="east",
                commentary=["Start", "Middle", "Victory"],
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
            bout = Bout(
                thinking="Analysis",
                winner="east",
                commentary=["Start", "Middle", "Victory"],
                kimarite="yorikiri",
                excitement_level=level,
                east_xp_gain=10,
                west_xp_gain=5,
            )
            self.assertEqual(bout.excitement_level, level)

        # Below minimum
        with self.assertRaises(ValidationError):
            Bout(
                thinking="Analysis",
                winner="east",
                commentary=["Start", "Middle", "Victory"],
                kimarite="yorikiri",
                excitement_level=0.5,
                east_xp_gain=10,
                west_xp_gain=5,
            )

        # Above maximum
        with self.assertRaises(ValidationError):
            Bout(
                thinking="Analysis",
                winner="east",
                commentary=["Start", "Middle", "Victory"],
                kimarite="yorikiri",
                excitement_level=10.5,
                east_xp_gain=10,
                west_xp_gain=5,
            )

    def test_xp_gains_must_be_non_negative(self) -> None:
        """XP gain values must be >= 0."""
        from pydantic import ValidationError

        # Zero XP is valid
        bout = Bout(
            thinking="Analysis",
            winner="east",
            commentary=["Start", "Middle", "Victory"],
            kimarite="yorikiri",
            excitement_level=5.0,
            east_xp_gain=0,
            west_xp_gain=0,
        )
        self.assertEqual(bout.east_xp_gain, 0)
        self.assertEqual(bout.west_xp_gain, 0)

        # Negative XP for east should fail
        with self.assertRaises(ValidationError):
            Bout(
                thinking="Analysis",
                winner="east",
                commentary=["Start", "Middle", "Victory"],
                kimarite="yorikiri",
                excitement_level=5.0,
                east_xp_gain=-5,
                west_xp_gain=5,
            )

        # Negative XP for west should fail
        with self.assertRaises(ValidationError):
            Bout(
                thinking="Analysis",
                winner="east",
                commentary=["Start", "Middle", "Victory"],
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

        bout = Bout(
            thinking="Analysis",
            winner="east",
            commentary=commentary_lines,
            kimarite="yorikiri",
            excitement_level=7.0,
            east_xp_gain=20,
            west_xp_gain=15,
        )

        self.assertEqual(len(bout.commentary), 5)
        self.assertEqual(bout.commentary, commentary_lines)

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
                bout = Bout(
                    thinking="Analysis",
                    winner="east",
                    commentary=["Start", "Middle", "Victory"],
                    kimarite=technique,  # type: ignore[arg-type]
                    excitement_level=5.0,
                    east_xp_gain=10,
                    west_xp_gain=5,
                )
                self.assertEqual(bout.kimarite, technique)


@patch("libs.generators.bout.get_openai_singleton")
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
        mock_response.output_parsed = Bout(
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

    def test_generator_initialization_with_seed(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should initialize generator with seed for deterministic fortune."""
        gen1 = BoutGenerator(seed=42)
        gen2 = BoutGenerator(seed=42)

        # Both generators should produce same fortune sequence
        fortune1 = gen1._generate_fortune()
        fortune2 = gen2._generate_fortune()

        self.assertEqual(fortune1, fortune2)

    def test_generator_initialization_with_model(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should initialize generator with specified model."""
        gen = BoutGenerator(model="gpt-5-mini", seed=42)
        self.assertEqual(gen.model, "gpt-5-mini")

    def test_generate_produces_valid_output(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should generate a valid bout output."""
        gen = BoutGenerator(seed=42)

        # Configure the mock client
        mock_response = self._create_mock_response()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        east_rikishi = Rikishi(
            shikona=Shikona(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Abundant Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=60,
            current=40,
        )
        west_rikishi = Rikishi(
            shikona=Shikona(
                shikona="若元春",
                transliteration="Wakamotoharu",
                interpretation="Young Origin Spring",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-47"),
            potential=55,
            current=35,
        )

        result = gen.generate(east_rikishi, west_rikishi)

        self.assertIsInstance(result, Bout)
        self.assertIn(result.winner, ["east", "west"])
        self.assertIsNotNone(result.kimarite)
        self.assertGreaterEqual(result.excitement_level, 1.0)
        self.assertLessEqual(result.excitement_level, 10.0)
        self.assertGreaterEqual(result.east_xp_gain, 0)
        self.assertGreaterEqual(result.west_xp_gain, 0)

    def test_generate_calls_openai_with_correct_parameters(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should call OpenAI API with correct model and input format."""
        gen = BoutGenerator(model="gpt-5-mini", seed=42)

        mock_response = self._create_mock_response()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        east_rikishi = Rikishi(
            shikona=Shikona(
                shikona="照ノ富士",
                transliteration="Terunofuji",
                interpretation="Shining Fuji",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=90,
            current=75,
        )
        west_rikishi = Rikishi(
            shikona=Shikona(
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
        mock_singleton.return_value.responses.parse.assert_called_once()
        call_kwargs = mock_singleton.return_value.responses.parse.call_args[1]

        # Check parameters
        self.assertEqual(call_kwargs["model"], "gpt-5-mini")
        self.assertEqual(call_kwargs["reasoning"]["effort"], "low")
        self.assertEqual(call_kwargs["text_format"], Bout)

        # Check input structure
        input_messages = call_kwargs["input"]
        self.assertEqual(len(input_messages), 2)
        self.assertEqual(input_messages[0]["role"], "system")
        self.assertEqual(input_messages[1]["role"], "user")

    def test_generate_includes_fortune_in_input(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should include fortune values in the API input."""
        gen = BoutGenerator(seed=42)

        mock_response = self._create_mock_response()
        mock_singleton.return_value.responses.parse.return_value = mock_response

        east_rikishi = Rikishi(
            shikona=Shikona(
                shikona="若隆景",
                transliteration="Wakatakakage",
                interpretation="Young Prosperous View",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-28"),
            potential=65,
            current=50,
        )
        west_rikishi = Rikishi(
            shikona=Shikona(
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
        call_kwargs = mock_singleton.return_value.responses.parse.call_args[1]
        user_input = call_kwargs["input"][1]["content"]

        # Parse the JSON input
        import json

        input_data = json.loads(user_input)

        # Verify fortune is included and has expected structure
        self.assertIn("fortune", input_data)
        self.assertIsInstance(input_data["fortune"], list)
        self.assertEqual(len(input_data["fortune"]), 5)
        # Fortune values should be in valid range
        # (0-13 normal, -5 critical fail, 20 critical success)
        for value in input_data["fortune"]:
            self.assertIn(
                value,
                list(range(0, 14)) + [-5, 20],
                f"Fortune value {value} not in valid range",
            )

    def test_generate_raises_error_when_parsing_fails(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should raise ValueError when API response cannot be parsed."""
        gen = BoutGenerator(seed=42)

        # Configure mock to return None for output_parsed
        mock_response = MagicMock()
        mock_response.output_parsed = None
        mock_singleton.return_value.responses.parse.return_value = mock_response

        east_rikishi = Rikishi(
            shikona=Shikona(
                shikona="明生",
                transliteration="Meisei",
                interpretation="Bright Life",
            ),
            shusshin=Shusshin(country_code="JP", jp_prefecture="JP-45"),
            potential=50,
            current=30,
        )
        west_rikishi = Rikishi(
            shikona=Shikona(
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

    def test_different_seeds_produce_different_fortune(
        self, mock_singleton: MagicMock
    ) -> None:
        """Different seeds should produce different fortune sequences."""
        gen1 = BoutGenerator(seed=42)
        gen2 = BoutGenerator(seed=100)

        fortune1 = gen1._generate_fortune()
        fortune2 = gen2._generate_fortune()

        # At least some values should be different
        self.assertNotEqual(fortune1, fortune2)

    def test_system_prompt_loads_correctly(
        self, mock_singleton: MagicMock
    ) -> None:
        """System prompt should be loaded at class level."""
        # The prompt should be loaded once and accessible
        self.assertIsInstance(BoutGenerator._system_prompt, str)
        self.assertGreater(len(BoutGenerator._system_prompt), 0)

        # Should contain key sections from the prompt
        self.assertIn(
            "sumo bout simulator", BoutGenerator._system_prompt.lower()
        )
        self.assertIn("kimarite", BoutGenerator._system_prompt.lower())

    def test_generate_with_evenly_matched_fighters(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should handle evenly matched fighters correctly."""
        gen = BoutGenerator(seed=42)

        mock_response = self._create_mock_response(
            winner="west", kimarite="uwatenage", excitement=9.5
        )
        mock_singleton.return_value.responses.parse.return_value = mock_response

        # Create two evenly matched rikishi
        east_rikishi = Rikishi(
            shikona=Shikona(
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
        west_rikishi = Rikishi(
            shikona=Shikona(
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
        self.assertIsInstance(result, Bout)
        self.assertIn(result.winner, ["east", "west"])

    def test_generate_with_severe_mismatch(
        self, mock_singleton: MagicMock
    ) -> None:
        """Should handle severe ability mismatch correctly."""
        gen = BoutGenerator(seed=42)

        mock_response = self._create_mock_response(
            winner="east", kimarite="oshidashi", excitement=2.5
        )
        mock_singleton.return_value.responses.parse.return_value = mock_response

        # Create mismatched fighters (elite vs beginner)
        east_rikishi = Rikishi(
            shikona=Shikona(
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
        west_rikishi = Rikishi(
            shikona=Shikona(
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
        self.assertIsInstance(result, Bout)

    def test_fortune_generation_produces_expected_range(
        self, mock_singleton: MagicMock
    ) -> None:
        """Fortune values should include normal range and criticals."""
        gen = BoutGenerator(seed=42)

        # Generate many fortune sequences
        for _ in range(100):
            fortune = gen._generate_fortune()
            self.assertEqual(len(fortune), 5)
            for value in fortune:
                # Values should be in normal range (0-13) or critical
                # values (-5, 20)
                self.assertIn(
                    value,
                    list(range(0, 14)) + [-5, 20],
                    f"Fortune value {value} not in valid range",
                )

    def test_generator_uses_same_seed_for_fortune(
        self, mock_singleton: MagicMock
    ) -> None:
        """Generator should use consistent seed for fortune generation."""
        gen = BoutGenerator(seed=42)

        # Generate two fortune sequences
        fortune1 = gen._generate_fortune()

        # Reset generator with same seed
        gen2 = BoutGenerator(seed=42)
        fortune2 = gen2._generate_fortune()

        # Should match
        self.assertEqual(fortune1, fortune2)

    def test_fortune_generation_can_produce_criticals(
        self, mock_singleton: MagicMock
    ) -> None:
        """Fortune generation should occasionally produce critical values."""
        gen = BoutGenerator(seed=12345)

        # Generate many fortune values to check if criticals appear
        all_values = []
        for _ in range(500):
            fortune = gen._generate_fortune()
            all_values.extend(fortune)

        # With 2500 values total (500 * 5), we should see some criticals
        # At 2% for each critical type, we expect ~50 of each
        has_critical_success = 20 in all_values
        has_critical_fail = -5 in all_values

        self.assertTrue(
            has_critical_success,
            "Critical success (20) should appear with enough samples",
        )
        self.assertTrue(
            has_critical_fail,
            "Critical fail (-5) should appear with enough samples",
        )

    def test_fortune_generation_returns_correct_count(
        self, mock_singleton: MagicMock
    ) -> None:
        """Fortune generation returns exactly FORTUNE_COUNT values."""
        from libs.generators.bout import FORTUNE_COUNT

        gen = BoutGenerator(seed=999)

        for _ in range(50):
            fortune = gen._generate_fortune()
            self.assertEqual(
                len(fortune),
                FORTUNE_COUNT,
                f"Expected {FORTUNE_COUNT} fortune values, got {len(fortune)}",
            )
