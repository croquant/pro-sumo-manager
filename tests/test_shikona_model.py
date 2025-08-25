"""Tests for the Shikona model."""

from django.db import IntegrityError, transaction
from django.test import TestCase

from game.models import Shikona


class ShikonaModelTests(TestCase):
    """Tests for the Shikona model."""

    def test_str_returns_transliteration_and_name(self) -> None:
        """Should return transliteration followed by the kanji name."""
        shikona = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        self.assertEqual(str(shikona), "Tsururyu (鶴龍)")

    def test_fail_duplicate_name(self) -> None:
        """Should fail if two Shikona share the same name."""
        Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shikona.objects.create(
                name="鶴龍",
                transliteration="Other",
                interpretation="Phoenix",
            )

    def test_fail_duplicate_transliteration(self) -> None:
        """Should fail if two Shikona share the same transliteration."""
        Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shikona.objects.create(
                name="鳳凰",
                transliteration="Tsururyu",
                interpretation="Phoenix",
            )
