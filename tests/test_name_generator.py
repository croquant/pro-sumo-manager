"""Tests for the Rikishi name generator."""

from django.test import SimpleTestCase

from libs.generators.name import RikishiNameGenerator


class RikishiNameGeneratorTests(SimpleTestCase):
    """Tests for deterministic name generation."""

    def test_seed_produces_deterministic_results(self) -> None:
        """Two generators seeded the same produce identical names."""
        gen1 = RikishiNameGenerator(seed=42)
        gen2 = RikishiNameGenerator(seed=42)
        self.assertEqual(gen1.get(), gen2.get())
