"""Tests for the Rikishi name generator."""

from django.test import SimpleTestCase

from libs.generators.name import RikishiNameGenerator


class RikishiNameGeneratorTests(SimpleTestCase):
    """Tests for deterministic name generation and phoneme fixes."""

    def test_seed_produces_deterministic_results(self) -> None:
        """Two generators seeded the same produce identical names."""
        gen1 = RikishiNameGenerator(seed=42)
        gen2 = RikishiNameGenerator(seed=42)
        self.assertEqual(gen1.get(), gen2.get())

    def test_fix_phonemes_replacements(self) -> None:
        """Specific phoneme patterns are replaced correctly."""
        gen = RikishiNameGenerator()
        fix = gen._RikishiNameGenerator__fix_phonemes  # type: ignore[attr-defined]
        self.assertEqual(fix("samurai"), "ji")
        self.assertEqual(fix("ryuu"), "ryu")
        self.assertEqual(fix("aoo"), "ao")
        self.assertEqual(fix("sou"), "so")
        self.assertEqual(fix("muu"), "mu")
