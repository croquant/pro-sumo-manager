"""Tests for the Rikishi name generator."""

from unittest.mock import patch

from django.test import SimpleTestCase

from libs.generators.name import (
    MAX_MAX_NAME_LEN,
    MIN_NAME_LEN,
    RikishiNameGenerator,
)


class RikishiNameGeneratorTests(SimpleTestCase):
    """Tests for deterministic name generation and phoneme fixes."""

    def test_seed_produces_deterministic_results(self) -> None:
        """Two generators seeded the same produce identical name sequences."""
        gen1 = RikishiNameGenerator(seed=42)
        gen2 = RikishiNameGenerator(seed=42)
        seq1 = [gen1.get() for _ in range(5)]
        seq2 = [gen2.get() for _ in range(5)]
        self.assertEqual(seq1, seq2)

    def test_fix_phonemes_replacements(self) -> None:
        """Specific phoneme patterns are replaced correctly."""
        gen = RikishiNameGenerator()
        fix = gen._RikishiNameGenerator__fix_phonemes  # type: ignore[attr-defined]
        self.assertEqual(fix("samurai"), "ji")
        self.assertEqual(fix("ryuu"), "ryu")
        self.assertEqual(fix("aoo"), "ao")
        self.assertEqual(fix("sou"), "so")
        self.assertEqual(fix("muu"), "mu")

    def test_fix_phonemes_edge_cases(self) -> None:
        """Edge cases for phoneme replacements are handled."""
        gen = RikishiNameGenerator()
        fix = gen._RikishiNameGenerator__fix_phonemes  # type: ignore[attr-defined]
        self.assertEqual(fix("uoo"), "uo")
        self.assertEqual(fix("eoo"), "eo")
        self.assertEqual(fix("ioo"), "io")
        self.assertEqual(fix("ooo"), "oo")
        self.assertEqual(fix("nou"), "no")
        self.assertEqual(fix("noui"), "noui")
        self.assertEqual(fix("houi"), "houi")
        self.assertEqual(fix("roui"), "roui")

    def test_generated_name_length_constraints(self) -> None:
        """Generated names meet length constraints."""
        gen = RikishiNameGenerator(seed=123)
        for _ in range(100):
            name, name_jp = gen.get()
            self.assertGreaterEqual(len(name), MIN_NAME_LEN)
            self.assertGreaterEqual(len(name_jp), MIN_NAME_LEN)
            self.assertLessEqual(len(name), MAX_MAX_NAME_LEN)
            self.assertLessEqual(len(name_jp), MAX_MAX_NAME_LEN)

    def test_romanized_name_is_ascii_and_no_bounds(self) -> None:
        """Romanized names are ASCII and don't start or end with 'no'."""
        gen = RikishiNameGenerator(seed=8)
        for _ in range(100):
            name, _ = gen.get()
            self.assertTrue(name.isascii())
            lower = name.lower()
            self.assertFalse(lower.startswith("no"))
            self.assertFalse(lower.endswith("no"))

    def test_generated_name_contains_kanji(self) -> None:
        """Japanese names include at least one kanji character."""
        gen = RikishiNameGenerator(seed=7)
        for _ in range(50):
            _, name_jp = gen.get()
            self.assertTrue(any("\u4e00" <= c <= "\u9fff" for c in name_jp))

    def test_get_raises_after_max_attempts(self) -> None:
        """An error is raised when a valid name can't be generated."""
        gen = RikishiNameGenerator(seed=1)
        with (
            patch.object(
                gen, "_RikishiNameGenerator__check_valid", return_value=False
            ),
            self.assertRaisesRegex(
                RuntimeError, "Failed to generate a valid name"
            ),
        ):
            gen.get()
