"""Tests for ShusshinGenerator."""

from __future__ import annotations

import unittest
from collections import Counter

from django.test import TestCase

from game.models import Shusshin as DjangoShusshin
from libs.generators.shusshin import (
    COUNTRY_PROBABILITIES,
    JAPANESE_PROB,
    PREFECTURE_PROBABILITIES,
    Shusshin,
    ShusshinGenerator,
)


class TestShusshinGenerator(unittest.TestCase):
    """Tests for the ShusshinGenerator class."""

    def test_generator_with_seed_is_deterministic(self) -> None:
        """Seeded generators should produce identical sequences."""
        gen1 = ShusshinGenerator(seed=42)
        gen2 = ShusshinGenerator(seed=42)

        results1 = [gen1.get() for _ in range(100)]
        results2 = [gen2.get() for _ in range(100)]

        self.assertEqual(results1, results2)

    def test_different_seeds_produce_different_sequences(self) -> None:
        """Different seeds should produce different sequences."""
        gen1 = ShusshinGenerator(seed=42)
        gen2 = ShusshinGenerator(seed=100)

        results1 = [gen1.get() for _ in range(50)]
        results2 = [gen2.get() for _ in range(50)]

        self.assertNotEqual(results1, results2)

    def test_japanese_probability_approximately_88_percent(self) -> None:
        """Over large sample, ~88% should be Japanese."""
        gen = ShusshinGenerator(seed=42)
        results = [gen.get() for _ in range(10000)]

        japanese_count = sum(1 for s in results if s.country_code == "JP")
        ratio = japanese_count / len(results)

        # Allow for statistical variance (~2% tolerance)
        self.assertGreaterEqual(ratio, 0.86)
        self.assertLessEqual(ratio, 0.90)

    def test_japanese_shusshin_has_prefecture(self) -> None:
        """Japanese wrestlers must have prefecture set."""
        gen = ShusshinGenerator(seed=42)
        for _ in range(1000):
            shusshin = gen.get()
            if shusshin.country_code == "JP":
                self.assertNotEqual(shusshin.jp_prefecture, "")
                self.assertTrue(shusshin.jp_prefecture.startswith("JP-"))
                self.assertEqual(len(shusshin.jp_prefecture), 5)

    def test_foreign_shusshin_has_no_prefecture(self) -> None:
        """Foreign wrestlers must not have prefecture set."""
        gen = ShusshinGenerator(seed=42)
        for _ in range(5000):  # More iterations to get enough foreigners
            shusshin = gen.get()
            if shusshin.country_code != "JP":
                self.assertEqual(shusshin.jp_prefecture, "")

    def test_foreign_shusshin_never_japan(self) -> None:
        """Foreign wrestlers (no prefecture) can't have country='JP'."""
        gen = ShusshinGenerator(seed=42)
        # Generate many to test "Other" path
        for _ in range(5000):
            shusshin = gen.get()
            if shusshin.jp_prefecture == "":
                self.assertNotEqual(shusshin.country_code, "JP")

    def test_all_prefectures_can_be_selected(self) -> None:
        """All 47 prefectures should be possible (given enough samples)."""
        gen = ShusshinGenerator(seed=42)
        prefectures = set()

        # Generate many Japanese wrestlers
        attempts = 0
        max_attempts = 100000
        while len(prefectures) < 47 and attempts < max_attempts:
            shusshin = gen.get()
            if shusshin.country_code == "JP" and shusshin.jp_prefecture:
                prefectures.add(shusshin.jp_prefecture)
            attempts += 1

        self.assertEqual(
            len(prefectures),
            47,
            f"Only found {len(prefectures)}/47 prefectures "
            f"after {attempts} attempts",
        )

    def test_prefecture_distribution_roughly_matches_probabilities(
        self,
    ) -> None:
        """Prefecture distribution should match defined probabilities."""
        gen = ShusshinGenerator(seed=42)
        prefecture_counts: Counter[str] = Counter()

        # Generate many Japanese wrestlers
        num_samples = 50000
        for _ in range(num_samples):
            shusshin = gen.get()
            if shusshin.country_code == "JP" and shusshin.jp_prefecture:
                prefecture_counts[shusshin.jp_prefecture] += 1

        total_japanese = sum(prefecture_counts.values())

        # Check that high-probability prefectures appear more often
        # Tokyo (JP-13) should be the most common (~8%)
        tokyo_ratio = prefecture_counts["JP-13"] / total_japanese
        self.assertGreaterEqual(tokyo_ratio, 0.07)
        self.assertLessEqual(tokyo_ratio, 0.09)

        # Tottori (JP-31) should be very rare (~0.3%)
        tottori_ratio = prefecture_counts["JP-31"] / total_japanese
        self.assertLess(tottori_ratio, 0.01)

    def test_foreign_countries_match_expected_distribution(self) -> None:
        """Foreign country distribution should roughly match probabilities."""
        gen = ShusshinGenerator(seed=42)
        country_counts: Counter[str] = Counter()

        # Generate many samples
        num_samples = 50000
        for _ in range(num_samples):
            shusshin = gen.get()
            if shusshin.country_code != "JP":
                country_counts[shusshin.country_code] += 1

        total_foreign = sum(country_counts.values())

        # Mongolia should be most common foreign country (~55%)
        if total_foreign > 0:
            mongolia_ratio = country_counts["MN"] / total_foreign
            # Should be around 0.55, allow variance
            self.assertGreaterEqual(mongolia_ratio, 0.50)
            self.assertLessEqual(mongolia_ratio, 0.60)

    def test_other_country_excludes_japan(self) -> None:
        """When 'Other' is selected, Japan must never be chosen."""
        # Use a seed that triggers "Other" selection
        gen = ShusshinGenerator(seed=42)

        other_countries = set()
        for _ in range(10000):
            shusshin = gen.get()
            # Foreign wrestlers not in the explicit country list
            if shusshin.country_code != "JP" and shusshin.country_code not in [
                "MN",
                "CN",
                "RU",
                "KP",
                "GE",
                "BG",
                "BR",
                "US",
                "UA",
                "KZ",
                "EE",
            ]:
                other_countries.add(shusshin.country_code)

        # Should have some "Other" countries
        self.assertGreater(len(other_countries), 0)

        # None should be JP or explicitly listed countries
        self.assertNotIn("JP", other_countries)
        for country in [
            "MN",
            "CN",
            "RU",
            "KP",
            "GE",
            "BG",
            "BR",
            "US",
            "UA",
            "KZ",
            "EE",
        ]:
            self.assertNotIn(country, other_countries)

    def test_probability_distributions_sum_to_one(self) -> None:
        """Prefecture and country probabilities must sum to 1.0."""
        pref_sum = sum(PREFECTURE_PROBABILITIES.values())
        country_sum = sum(COUNTRY_PROBABILITIES.values())

        self.assertGreaterEqual(pref_sum, 0.999)
        self.assertLessEqual(pref_sum, 1.001)
        self.assertGreaterEqual(country_sum, 0.999)
        self.assertLessEqual(country_sum, 1.001)

    def test_probability_constants_have_correct_length(self) -> None:
        """Probability dictionaries should have expected number of entries."""
        self.assertEqual(len(PREFECTURE_PROBABILITIES), 47)
        self.assertEqual(len(COUNTRY_PROBABILITIES), 12)

    def test_all_prefecture_codes_are_valid_format(self) -> None:
        """All prefecture codes should follow ISO 3166-2 format."""
        for code in PREFECTURE_PROBABILITIES:
            self.assertTrue(code.startswith("JP-"))
            self.assertEqual(len(code), 5)
            self.assertTrue(code[3:].isdigit())
            # Should be in range 01-47
            num = int(code[3:])
            self.assertGreaterEqual(num, 1)
            self.assertLessEqual(num, 47)

    def test_all_country_codes_are_valid_format(self) -> None:
        """All country codes should be 2-letter ISO codes or 'Other'."""
        for code in COUNTRY_PROBABILITIES:
            if code != "Other":
                self.assertEqual(len(code), 2)
                self.assertTrue(code.isupper())

    def test_all_probabilities_are_positive(self) -> None:
        """All probability values should be positive."""
        for prob in PREFECTURE_PROBABILITIES.values():
            self.assertGreater(prob, 0)

        for prob in COUNTRY_PROBABILITIES.values():
            self.assertGreater(prob, 0)

    def test_japanese_prob_constant_is_valid(self) -> None:
        """JAPANESE_PROB should be between 0 and 1."""
        self.assertGreater(JAPANESE_PROB, 0)
        self.assertLess(JAPANESE_PROB, 1)
        self.assertEqual(JAPANESE_PROB, 0.88)


class TestShusshinPydanticModel(unittest.TestCase):
    """Tests for the Shusshin Pydantic model."""

    def test_shusshin_model_can_be_created_japanese(self) -> None:
        """Should be able to create a Japanese Shusshin."""
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-13")
        self.assertEqual(shusshin.country_code, "JP")
        self.assertEqual(shusshin.jp_prefecture, "JP-13")

    def test_shusshin_model_can_be_created_foreign(self) -> None:
        """Should be able to create a foreign Shusshin."""
        shusshin = Shusshin(country_code="MN")
        self.assertEqual(shusshin.country_code, "MN")
        self.assertEqual(shusshin.jp_prefecture, "")

    def test_shusshin_model_defaults_prefecture_to_empty_string(self) -> None:
        """jp_prefecture should default to empty string if not provided."""
        shusshin = Shusshin(country_code="US")
        self.assertEqual(shusshin.jp_prefecture, "")

    def test_str_returns_prefecture_name_for_japanese(self) -> None:
        """__str__ should return 'Prefecture, Japan' for Japanese wrestlers."""
        shusshin = Shusshin(country_code="JP", jp_prefecture="JP-13")
        result = str(shusshin)
        self.assertIn("Japan", result)
        self.assertIn("Tokyo", result)  # JP-13 is Tokyo

    def test_str_returns_country_name_for_foreign(self) -> None:
        """__str__ should return country name for foreign wrestlers."""
        shusshin = Shusshin(country_code="MN")
        result = str(shusshin)
        self.assertEqual(result, "Mongolia")

    def test_str_returns_different_prefecture_names(self) -> None:
        """__str__ returns different prefecture names for different codes."""
        tokyo = Shusshin(country_code="JP", jp_prefecture="JP-13")
        osaka = Shusshin(country_code="JP", jp_prefecture="JP-27")

        self.assertIn("Tokyo", str(tokyo))
        self.assertIn("Osaka", str(osaka))
        self.assertNotEqual(str(tokyo), str(osaka))

    def test_str_handles_various_countries(self) -> None:
        """__str__ should handle various foreign countries."""
        test_cases = [
            ("MN", "Mongolia"),
            ("US", "United States"),
            ("RU", "Russian Federation"),
            ("GE", "Georgia"),
            ("BG", "Bulgaria"),
        ]

        for country_code, expected_name in test_cases:
            with self.subTest(country_code=country_code):
                shusshin = Shusshin(country_code=country_code)
                result = str(shusshin)
                self.assertEqual(result, expected_name)

    def test_str_fallback_to_code_if_pycountry_fails(self) -> None:
        """__str__ should fallback to code if pycountry lookup fails."""
        # Use an invalid but properly formatted code
        shusshin = Shusshin(country_code="XX")
        result = str(shusshin)
        # Should return the code itself as fallback
        self.assertEqual(result, "XX")

    def test_str_format_for_all_prefectures(self) -> None:
        """__str__ should work for all valid prefecture codes."""
        # Test a sample of prefectures
        sample_prefectures = ["JP-01", "JP-13", "JP-27", "JP-40", "JP-47"]

        for pref_code in sample_prefectures:
            with self.subTest(prefecture=pref_code):
                shusshin = Shusshin(country_code="JP", jp_prefecture=pref_code)
                result = str(shusshin)
                # Should contain "Japan" and some prefecture name
                self.assertIn("Japan", result)
                self.assertIn(",", result)
                # Format should be "Prefecture, Japan"
                parts = result.split(", ")
                self.assertEqual(len(parts), 2)
                self.assertEqual(parts[1], "Japan")


class TestShusshinDjangoIntegration(TestCase):
    """Integration tests for ShusshinGenerator with Django models."""

    def test_generated_japanese_shusshin_is_compatible_with_django_model(
        self,
    ) -> None:
        """Generator output for Japanese wrestlers matches Django model."""
        gen = ShusshinGenerator(seed=12345)  # Different seed to avoid conflicts

        # Find a Japanese wrestler from generator
        for _ in range(100):
            pydantic_shusshin = gen.get()
            if pydantic_shusshin.country_code == "JP":
                # Verify fields match Django model expectations
                self.assertEqual(pydantic_shusshin.country_code, "JP")
                self.assertNotEqual(pydantic_shusshin.jp_prefecture, "")
                self.assertTrue(
                    pydantic_shusshin.jp_prefecture.startswith("JP-")
                )
                self.assertEqual(len(pydantic_shusshin.jp_prefecture), 5)

                # Verify we can create a Django model with this data
                # Using get_or_create to avoid conflicts with other tests
                django_shusshin, _ = DjangoShusshin.objects.get_or_create(
                    country_code=pydantic_shusshin.country_code,
                    jp_prefecture=pydantic_shusshin.jp_prefecture,
                )
                self.assertIsNotNone(django_shusshin.pk)
                self.assertEqual(
                    django_shusshin.country_code, pydantic_shusshin.country_code
                )
                self.assertEqual(
                    django_shusshin.jp_prefecture,
                    pydantic_shusshin.jp_prefecture,
                )
                break

    def test_generated_foreign_shusshin_is_compatible_with_django_model(
        self,
    ) -> None:
        """Generator output for foreign wrestlers matches Django model."""
        gen = ShusshinGenerator(seed=67890)  # Different seed to avoid conflicts

        # Find a foreign wrestler from generator
        for _ in range(500):
            pydantic_shusshin = gen.get()
            if pydantic_shusshin.country_code != "JP":
                # Verify fields match Django model expectations
                self.assertNotEqual(pydantic_shusshin.country_code, "JP")
                self.assertEqual(pydantic_shusshin.jp_prefecture, "")

                # Verify we can create a Django model with this data
                # Using get_or_create to avoid conflicts with other tests
                django_shusshin, _ = DjangoShusshin.objects.get_or_create(
                    country_code=pydantic_shusshin.country_code,
                    jp_prefecture=pydantic_shusshin.jp_prefecture,
                )
                self.assertIsNotNone(django_shusshin.pk)
                self.assertEqual(
                    django_shusshin.country_code, pydantic_shusshin.country_code
                )
                self.assertEqual(django_shusshin.jp_prefecture, "")
                break

    def test_generator_output_passes_all_django_constraints(self) -> None:
        """All generated Shusshin should pass Django model constraints."""
        gen = ShusshinGenerator(seed=42)

        # Test Japanese wrestlers
        japanese_count = 0
        for _ in range(1000):
            pydantic_shusshin = gen.get()
            if pydantic_shusshin.country_code == "JP":
                # Must have prefecture
                self.assertNotEqual(pydantic_shusshin.jp_prefecture, "")
                self.assertTrue(
                    pydantic_shusshin.jp_prefecture.startswith("JP-")
                )
                japanese_count += 1
                if japanese_count >= 50:
                    break

        # Test foreign wrestlers
        foreign_count = 0
        for _ in range(5000):
            pydantic_shusshin = gen.get()
            if pydantic_shusshin.country_code != "JP":
                # Must NOT have prefecture
                self.assertEqual(pydantic_shusshin.jp_prefecture, "")
                foreign_count += 1
                if foreign_count >= 50:
                    break

    def test_generator_prefecture_codes_are_valid_enum_values(self) -> None:
        """All generated prefecture codes should be valid enum values."""
        gen = ShusshinGenerator(seed=42)

        # Import the enum
        from game.enums import JPPrefecture

        valid_prefectures = {choice[0] for choice in JPPrefecture.choices}

        # Generate many Japanese wrestlers
        for _ in range(1000):
            pydantic_shusshin = gen.get()
            if pydantic_shusshin.country_code == "JP":
                # Prefecture must be in valid enum values
                self.assertIn(
                    pydantic_shusshin.jp_prefecture, valid_prefectures
                )
