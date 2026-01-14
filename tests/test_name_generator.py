"""Tests for the name generator utilities."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from libs.generators import name


class NameUtilityTests(unittest.TestCase):
    """Tests for top-level name utility functions."""

    def test_get_initial_existing_names(self) -> None:
        """Should load names from the shikona corpus."""
        names = name.get_initial_existing_names()
        self.assertIn("豊昇龍", names)

    def test_generate_name_char_bigram_table(self) -> None:
        """Should build the bigram table and persist it to disk."""
        data = name.generate_name_char_bigram_table()
        self.assertIn("start", data)
        self.assertIn("bigrams", data)
        path = name.DATA_DIR / "name_char_bigram_table.json"
        self.assertTrue(path.exists())

    def test_get_bigram_tables(self) -> None:
        """Should load the bigram tables from disk."""
        start, bigrams = name.get_bigram_tables()
        self.assertIsInstance(start, list)
        self.assertIsInstance(bigrams, dict)
        self.assertTrue(start)
        self.assertTrue(bigrams)


class RikishiNameGeneratorTests(unittest.TestCase):
    """Tests for the RikishiNameGenerator class."""

    def test_get_produces_kanji_and_romaji(self) -> None:
        """Should generate a unique kanji and romaji name pair."""
        generator = name.RikishiNameGenerator(seed=0)
        kanji, romaji = generator.get()
        self.assertTrue(kanji)
        self.assertTrue(romaji)
        self.assertNotEqual(kanji, romaji)

    def test_transliterate_returns_romaji(self) -> None:
        """Should transliterate kanji into romaji."""
        generator = name.RikishiNameGenerator(seed=0)
        result = generator._RikishiNameGenerator__transliterate("魁")
        self.assertEqual(result, "kai")

    def test_fix_phonemes_adjusts_output(self) -> None:
        """Should apply phoneme replacements to romaji."""
        generator = name.RikishiNameGenerator(seed=0)
        result = generator._RikishiNameGenerator__fix_phonemes("ryuu")
        self.assertEqual(result, "ryu")

    def test_fix_phonemes_hepburn_adjustments(self) -> None:
        """Should normalize common Hepburn romanization patterns."""
        generator = name.RikishiNameGenerator(seed=0)
        cases = {
            "si": "shi",
            "ti": "chi",
            "tu": "tsu",
            "zi": "ji",
            "hu": "fu",
            "paa": "pa",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                result = generator._RikishiNameGenerator__fix_phonemes(raw)
                self.assertEqual(result, expected)

    def test_get_kanji_shikona_missing_start_bigram(self) -> None:
        """Should raise if the starting character has no bigrams."""
        generator = name.RikishiNameGenerator(seed=0)
        generator.start_table = [("X", 1.0)]
        generator.bigram_table = {}
        with self.assertRaises(RuntimeError):
            generator._get_kanji_shikona()

    def test_get_kanji_shikona_missing_prev_bigram(self) -> None:
        """Should raise if a previous character lacks bigram entries."""
        generator = name.RikishiNameGenerator(seed=0)
        generator.start_table = [("X", 1.0)]
        generator.bigram_table = {"X": {"chars": [("A", 1.0)], "end": 0.0}}
        with self.assertRaises(RuntimeError):
            generator._get_kanji_shikona()

    def test_get_raises_after_max_attempts(self) -> None:
        """Should raise when a valid name cannot be produced."""
        with patch("libs.generators.name.MAX_ATTEMPTS", 1):
            generator = name.RikishiNameGenerator(seed=0)
            existing = next(iter(generator.existing_names))
            generator._get_kanji_shikona = lambda: existing
            with self.assertRaises(RuntimeError):
                generator.get()
