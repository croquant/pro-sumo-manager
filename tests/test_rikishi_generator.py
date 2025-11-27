"""Tests for RikishiGenerator and Rikishi."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from libs.constants import (
    MAX_POTENTIAL,
    MAX_STAT_VALUE,
    MEAN_POTENTIAL,
    MIN_POTENTIAL,
    MIN_STAT_VALUE,
    NUM_STATS,
    SIGMA_POTENTIAL,
)
from libs.generators.rikishi import RikishiGenerator
from libs.types.rikishi import Rikishi
from libs.types.shikona import Shikona
from libs.types.shusshin import Shusshin


class TestRikishiModel(unittest.TestCase):
    """Tests for the Rikishi Pydantic model."""

    def test_can_create_rikishi_with_all_fields(self) -> None:
        """Should be able to create a rikishi with all required fields."""
        shikona = Shikona(
            shikona="鶴竜",
            transliteration="Kakuryu",
            interpretation="Crane Dragon",
        )
        shusshin = Shusshin(country_code="MN")

        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=50,
            current=25,
            strength=5,
            technique=6,
            balance=4,
            endurance=7,
            mental=3,
        )

        self.assertEqual(rikishi.shikona, shikona)
        self.assertEqual(rikishi.shusshin, shusshin)
        self.assertEqual(rikishi.potential, 50)
        self.assertEqual(rikishi.current, 25)
        self.assertEqual(rikishi.strength, 5)
        self.assertEqual(rikishi.technique, 6)
        self.assertEqual(rikishi.balance, 4)
        self.assertEqual(rikishi.endurance, 7)
        self.assertEqual(rikishi.mental, 3)

    def test_stats_default_to_1(self) -> None:
        """Individual stats should default to 1 if not specified."""
        shikona = Shikona(
            shikona="白鵬",
            transliteration="Hakuho",
            interpretation="White Phoenix",
        )
        shusshin = Shusshin(country_code="MN")

        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=30,
            current=15,
        )

        self.assertEqual(rikishi.strength, 1)
        self.assertEqual(rikishi.technique, 1)
        self.assertEqual(rikishi.balance, 1)
        self.assertEqual(rikishi.endurance, 1)
        self.assertEqual(rikishi.mental, 1)

    def test_potential_must_be_within_bounds(self) -> None:
        """Potential must be between MIN_POTENTIAL and MAX_POTENTIAL."""
        shikona = Shikona(
            shikona="朝青龍",
            transliteration="Asashoryu",
            interpretation="Morning Blue Dragon",
        )
        shusshin = Shusshin(country_code="MN")

        # Test minimum
        rikishi_min = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=MIN_POTENTIAL,
            current=MIN_POTENTIAL,
        )
        self.assertEqual(rikishi_min.potential, MIN_POTENTIAL)

        # Test maximum
        rikishi_max = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=MAX_POTENTIAL,
            current=MAX_POTENTIAL,
        )
        self.assertEqual(rikishi_max.potential, MAX_POTENTIAL)

        # Test below minimum (should fail validation)
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            Rikishi(
                shikona=shikona,
                shusshin=shusshin,
                potential=MIN_POTENTIAL - 1,
                current=MIN_POTENTIAL,
            )

        # Test above maximum (should fail validation)
        with self.assertRaises(ValidationError):
            Rikishi(
                shikona=shikona,
                shusshin=shusshin,
                potential=MAX_POTENTIAL + 1,
                current=MAX_POTENTIAL,
            )

    def test_stats_must_be_within_bounds(self) -> None:
        """Individual stats must be within MIN_STAT_VALUE to MAX_STAT_VALUE."""
        from pydantic import ValidationError

        shikona = Shikona(
            shikona="稀勢の里",
            transliteration="Kisenosato",
            interpretation="Rare Village of the Hometown",
        )
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-08")

        # Test valid range
        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=50,
            current=30,
            strength=MIN_STAT_VALUE,
            technique=MAX_STAT_VALUE,
        )
        self.assertEqual(rikishi.strength, MIN_STAT_VALUE)
        self.assertEqual(rikishi.technique, MAX_STAT_VALUE)

        # Test below minimum (should fail validation)
        with self.assertRaises(ValidationError):
            Rikishi(
                shikona=shikona,
                shusshin=shusshin,
                potential=50,
                current=30,
                strength=MIN_STAT_VALUE - 1,
            )

        # Test above maximum (should fail validation)
        with self.assertRaises(ValidationError):
            Rikishi(
                shikona=shikona,
                shusshin=shusshin,
                potential=50,
                current=30,
                strength=MAX_STAT_VALUE + 1,
            )

    def test_model_copy_creates_new_instance(self) -> None:
        """model_copy should create a new instance with updated values."""
        shikona = Shikona(
            shikona="照ノ富士",
            transliteration="Terunofuji",
            interpretation="Shining Fuji",
        )
        shusshin = Shusshin(country_code="MN")

        original = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=60,
            current=30,
        )

        # Create a copy with updated strength
        updated = original.model_copy(update={"strength": 10})

        # Original should be unchanged
        self.assertEqual(original.strength, 1)
        # Copy should have new value
        self.assertEqual(updated.strength, 10)
        # Other fields should be the same
        self.assertEqual(updated.potential, 60)
        self.assertEqual(updated.current, 30)


@patch("libs.generators.shikona.get_openai_singleton")
@patch("libs.generators.shikona.ShikonaGenerator._call_openai")
class TestRikishiGenerator(unittest.TestCase):
    """Tests for the RikishiGenerator class."""

    def _setup_mock_openai(self, mock_openai: MagicMock) -> None:
        """Configure OpenAI mock to return Shikona objects."""

        def mock_interpretation(
            kanji_name: str,
            parent_shikona: str | None = None,
            shusshin: str | None = None,
        ) -> Shikona:
            # Generate consistent output based on input kanji
            # This ensures determinism for seeded tests
            return Shikona(
                shikona=kanji_name,
                transliteration=f"Rikishi_{hash(kanji_name) % 10000}",
                interpretation=f"Test Wrestler {hash(kanji_name) % 100}",
            )

        mock_openai.side_effect = mock_interpretation

    def test_generator_with_seed_is_deterministic(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Seeded generators should produce identical rikishi."""
        self._setup_mock_openai(mock_openai)
        gen1 = RikishiGenerator(seed=42)
        gen2 = RikishiGenerator(seed=42)

        rikishi1 = gen1.get()
        rikishi2 = gen2.get()

        self.assertEqual(rikishi1.shikona, rikishi2.shikona)
        self.assertEqual(rikishi1.shusshin, rikishi2.shusshin)
        self.assertEqual(rikishi1.potential, rikishi2.potential)
        self.assertEqual(rikishi1.current, rikishi2.current)
        self.assertEqual(rikishi1.strength, rikishi2.strength)
        self.assertEqual(rikishi1.technique, rikishi2.technique)
        self.assertEqual(rikishi1.balance, rikishi2.balance)
        self.assertEqual(rikishi1.endurance, rikishi2.endurance)
        self.assertEqual(rikishi1.mental, rikishi2.mental)

    def test_different_seeds_produce_different_rikishi(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Different seeds should produce different rikishi."""
        self._setup_mock_openai(mock_openai)
        gen1 = RikishiGenerator(seed=42)
        gen2 = RikishiGenerator(seed=100)

        rikishi1 = gen1.get()
        rikishi2 = gen2.get()

        # At least some fields should be different
        differences = 0
        if rikishi1.potential != rikishi2.potential:
            differences += 1
        if rikishi1.current != rikishi2.current:
            differences += 1
        if rikishi1.strength != rikishi2.strength:
            differences += 1

        self.assertGreater(differences, 0)

    def test_generated_rikishi_has_all_required_fields(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generated rikishi should have all required fields populated."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)
        rikishi = gen.get()

        self.assertIsNotNone(rikishi.shikona)
        self.assertIsNotNone(rikishi.shusshin)
        self.assertIsNotNone(rikishi.potential)
        self.assertIsNotNone(rikishi.current)
        self.assertIsNotNone(rikishi.strength)
        self.assertIsNotNone(rikishi.technique)
        self.assertIsNotNone(rikishi.balance)
        self.assertIsNotNone(rikishi.endurance)
        self.assertIsNotNone(rikishi.mental)

    def test_potential_is_within_valid_range(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generated potential should be within MIN to MAX POTENTIAL."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(100):
            rikishi = gen.get()
            self.assertGreaterEqual(rikishi.potential, MIN_POTENTIAL)
            self.assertLessEqual(rikishi.potential, MAX_POTENTIAL)

    def test_current_is_less_than_or_equal_to_potential(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Current ability should never exceed potential."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(100):
            rikishi = gen.get()
            self.assertLessEqual(rikishi.current, rikishi.potential)

    def test_current_is_within_valid_range(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generated current should be within MIN_POTENTIAL and potential."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(100):
            rikishi = gen.get()
            self.assertGreaterEqual(rikishi.current, MIN_POTENTIAL)
            self.assertLessEqual(rikishi.current, rikishi.potential)

    def test_all_stats_are_within_valid_range(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """All stats should be within MIN_STAT_VALUE to MAX_STAT_VALUE."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(100):
            rikishi = gen.get()
            self.assertGreaterEqual(rikishi.strength, MIN_STAT_VALUE)
            self.assertLessEqual(rikishi.strength, MAX_STAT_VALUE)
            self.assertGreaterEqual(rikishi.technique, MIN_STAT_VALUE)
            self.assertLessEqual(rikishi.technique, MAX_STAT_VALUE)
            self.assertGreaterEqual(rikishi.balance, MIN_STAT_VALUE)
            self.assertLessEqual(rikishi.balance, MAX_STAT_VALUE)
            self.assertGreaterEqual(rikishi.endurance, MIN_STAT_VALUE)
            self.assertLessEqual(rikishi.endurance, MAX_STAT_VALUE)
            self.assertGreaterEqual(rikishi.mental, MIN_STAT_VALUE)
            self.assertLessEqual(rikishi.mental, MAX_STAT_VALUE)

    def test_potential_distribution_is_roughly_gaussian(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Potential follows Gaussian distribution centered on MEAN."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)
        potentials = [gen.get().potential for _ in range(1000)]

        # Calculate mean
        mean = sum(potentials) / len(potentials)

        # Mean should be close to MEAN_POTENTIAL (30)
        # Allow some variance since we're sampling
        self.assertGreaterEqual(mean, MEAN_POTENTIAL - 3)
        self.assertLessEqual(mean, MEAN_POTENTIAL + 3)

        # Most values should be within 1 standard deviation (10-50 range)
        within_one_sigma = sum(
            1
            for p in potentials
            if MEAN_POTENTIAL - SIGMA_POTENTIAL
            <= p
            <= MEAN_POTENTIAL + SIGMA_POTENTIAL
        )
        # Expect around 68% within one sigma
        self.assertGreater(within_one_sigma / len(potentials), 0.60)
        self.assertLess(within_one_sigma / len(potentials), 0.76)

        # Very few should reach elite levels (70+)
        elite_count = sum(1 for p in potentials if p >= 70)
        self.assertLess(elite_count / len(potentials), 0.10)

    def test_stat_distribution_reflects_current_ability(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Higher current ability should result in higher total stats."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        high_ability_rikishi = []
        low_ability_rikishi = []

        # Generate many rikishi and separate by current ability
        # Current ability typically ranges 5-15, so use thresholds within that
        for _ in range(500):
            rikishi = gen.get()
            total_stats = (
                rikishi.strength
                + rikishi.technique
                + rikishi.balance
                + rikishi.endurance
                + rikishi.mental
            )

            if rikishi.current >= 12:
                high_ability_rikishi.append(total_stats)
            elif rikishi.current <= 8:
                low_ability_rikishi.append(total_stats)

        # High ability rikishi should have higher average total stats
        if high_ability_rikishi and low_ability_rikishi:
            avg_high = sum(high_ability_rikishi) / len(high_ability_rikishi)
            avg_low = sum(low_ability_rikishi) / len(low_ability_rikishi)
            self.assertGreater(avg_high, avg_low)

    def test_stats_roughly_sum_to_current_ability(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Total stats should roughly correspond to current ability."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(50):
            rikishi = gen.get()
            total_stats = (
                rikishi.strength
                + rikishi.technique
                + rikishi.balance
                + rikishi.endurance
                + rikishi.mental
            )

            # Total stats should be: base (5) + distributed points
            # distributed points = current - (MIN_STAT_VALUE * NUM_STATS)
            expected_total = rikishi.current
            self.assertEqual(total_stats, expected_total)

    def test_multiple_generations_produce_unique_rikishi(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generating multiple rikishi should produce different individuals."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        rikishi_list = [gen.get() for _ in range(10)]

        # Check that at least some shikona are different
        shikona_set = {r.shikona.shikona for r in rikishi_list}
        self.assertGreater(len(shikona_set), 1)

    def test_stat_distribution_is_random(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Stats should be randomly distributed, not all equal."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        # Generate rikishi with enough points to distribute
        # Current typically ranges 5-15, so look for current > 8
        found_unequal = False
        for _ in range(100):
            rikishi = gen.get()
            if rikishi.current > 8:  # Need enough points for variation
                stats = [
                    rikishi.strength,
                    rikishi.technique,
                    rikishi.balance,
                    rikishi.endurance,
                    rikishi.mental,
                ]
                # Check if stats are not all equal
                if len(set(stats)) > 1:
                    found_unequal = True
                    break

        self.assertTrue(found_unequal, "Stats should not all be equal")

    def test_edge_case_minimum_current_ability(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generator should handle minimum current ability (5) correctly."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        # Generate many to find one with minimum current
        for _ in range(1000):
            rikishi = gen.get()
            if rikishi.current == MIN_POTENTIAL:
                # All stats should be at minimum
                self.assertEqual(rikishi.strength, MIN_STAT_VALUE)
                self.assertEqual(rikishi.technique, MIN_STAT_VALUE)
                self.assertEqual(rikishi.balance, MIN_STAT_VALUE)
                self.assertEqual(rikishi.endurance, MIN_STAT_VALUE)
                self.assertEqual(rikishi.mental, MIN_STAT_VALUE)
                break

    def test_edge_case_high_current_ability(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generator should handle high current ability correctly."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        # Generate many to find one with high current
        # Current typically ranges 5-15, so look for >= 12
        for _ in range(1000):
            rikishi = gen.get()
            if rikishi.current >= 12:
                # Stats should not exceed maximum
                self.assertLessEqual(rikishi.strength, MAX_STAT_VALUE)
                self.assertLessEqual(rikishi.technique, MAX_STAT_VALUE)
                self.assertLessEqual(rikishi.balance, MAX_STAT_VALUE)
                self.assertLessEqual(rikishi.endurance, MAX_STAT_VALUE)
                self.assertLessEqual(rikishi.mental, MAX_STAT_VALUE)
                break

    def test_generated_shikona_has_required_fields(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generated shikona should have all required fields."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)
        rikishi = gen.get()

        self.assertIsInstance(rikishi.shikona.shikona, str)
        self.assertGreater(len(rikishi.shikona.shikona), 0)
        self.assertIsInstance(rikishi.shikona.transliteration, str)
        self.assertGreater(len(rikishi.shikona.transliteration), 0)
        self.assertIsInstance(rikishi.shikona.interpretation, str)
        self.assertGreater(len(rikishi.shikona.interpretation), 0)

    def test_generated_shusshin_has_valid_country_code(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Generated shusshin should have a valid country code."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(100):
            rikishi = gen.get()
            # Country code should be 2 characters
            self.assertEqual(len(rikishi.shusshin.country_code), 2)
            self.assertTrue(rikishi.shusshin.country_code.isupper())

    def test_japanese_rikishi_have_prefecture(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Japanese rikishi should have prefecture set."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(200):
            rikishi = gen.get()
            if rikishi.shusshin.country_code == "JP":
                self.assertNotEqual(rikishi.shusshin.jp_prefecture, "")
                self.assertTrue(
                    rikishi.shusshin.jp_prefecture.startswith("JP-")
                )
                break

    def test_foreign_rikishi_have_no_prefecture(
        self, mock_openai: MagicMock, mock_singleton: MagicMock
    ) -> None:
        """Foreign rikishi should not have prefecture set."""
        self._setup_mock_openai(mock_openai)
        gen = RikishiGenerator(seed=42)

        for _ in range(500):
            rikishi = gen.get()
            if rikishi.shusshin.country_code != "JP":
                self.assertEqual(rikishi.shusshin.jp_prefecture, "")
                break


class TestDistributeStatsEdgeCases(unittest.TestCase):
    """Tests for the _distribute_stats method edge cases."""

    def test_distribute_stats_with_zero_points(self) -> None:
        """Distributing zero points should return rikishi unchanged."""
        gen = RikishiGenerator(seed=42)
        shikona = Shikona(
            shikona="貴景勝",
            transliteration="Takakeisho",
            interpretation="Noble Victory",
        )
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-28")

        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=10,
            current=5,
        )

        # Distribute 0 points
        result = gen._distribute_stats(rikishi, 0)

        # All stats should still be at default
        self.assertEqual(result.strength, 1)
        self.assertEqual(result.technique, 1)
        self.assertEqual(result.balance, 1)
        self.assertEqual(result.endurance, 1)
        self.assertEqual(result.mental, 1)

    def test_distribute_stats_with_negative_points_raises_error(self) -> None:
        """Distributing negative points should raise ValueError."""
        gen = RikishiGenerator(seed=42)
        shikona = Shikona(
            shikona="御嶽海",
            transliteration="Mitakeumi",
            interpretation="Mount Ontake Sea",
        )
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-20")

        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=30,
            current=15,
        )

        with self.assertRaises(ValueError) as context:
            gen._distribute_stats(rikishi, -5)

        self.assertIn("non-negative", str(context.exception))

    def test_distribute_stats_caps_at_maximum(self) -> None:
        """Distributing more points than possible should cap at max."""
        gen = RikishiGenerator(seed=42)
        shikona = Shikona(
            shikona="正代",
            transliteration="Shodai",
            interpretation="Correct Generation",
        )
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-43")

        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=100,
            current=100,
        )

        # Try to distribute way more points than possible
        # Max = NUM_STATS * (MAX_STAT_VALUE - MIN_STAT_VALUE) = 5 * 19 = 95
        result = gen._distribute_stats(rikishi, 1000)

        # No stat should exceed maximum
        self.assertLessEqual(result.strength, MAX_STAT_VALUE)
        self.assertLessEqual(result.technique, MAX_STAT_VALUE)
        self.assertLessEqual(result.balance, MAX_STAT_VALUE)
        self.assertLessEqual(result.endurance, MAX_STAT_VALUE)
        self.assertLessEqual(result.mental, MAX_STAT_VALUE)

        # Total should be at maximum possible
        total = (
            result.strength
            + result.technique
            + result.balance
            + result.endurance
            + result.mental
        )
        max_possible = NUM_STATS * MAX_STAT_VALUE
        self.assertEqual(total, max_possible)

    def test_distribute_stats_does_not_create_infinite_loop(self) -> None:
        """When all stats are maxed, distribution should not loop infinitely."""
        gen = RikishiGenerator(seed=42)
        shikona = Shikona(
            shikona="豪栄道",
            transliteration="Goeido",
            interpretation="Great Glory Path",
        )
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-27")

        # Create rikishi with all stats at max
        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=100,
            current=100,
            strength=MAX_STAT_VALUE,
            technique=MAX_STAT_VALUE,
            balance=MAX_STAT_VALUE,
            endurance=MAX_STAT_VALUE,
            mental=MAX_STAT_VALUE,
        )

        # Try to distribute more points (should not hang)
        result = gen._distribute_stats(rikishi, 10)

        # Stats should remain at max
        self.assertEqual(result.strength, MAX_STAT_VALUE)
        self.assertEqual(result.technique, MAX_STAT_VALUE)
        self.assertEqual(result.balance, MAX_STAT_VALUE)
        self.assertEqual(result.endurance, MAX_STAT_VALUE)
        self.assertEqual(result.mental, MAX_STAT_VALUE)
