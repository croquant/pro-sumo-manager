"""Tests for the Shusshin model."""

from django.db import IntegrityError, transaction
from django.test import TestCase

from core.enums.country_enum import Country
from core.enums.jp_prefecture_enum import JPPrefecture
from core.models import Shusshin


class ShusshinModelTests(TestCase):
    """Tests for the Shusshin model."""

    def test_str_returns_prefecture_label_for_japan(self) -> None:
        """Should return the prefecture label when country is Japan."""
        shusshin = Shusshin.objects.create(
            country_code=Country.JP,
            jp_prefecture=JPPrefecture.TOKYO,
        )
        self.assertEqual(str(shusshin), "Tokyo")

    def test_str_returns_country_label_for_non_japan(self) -> None:
        """Should return the country label when not Japan."""
        shusshin = Shusshin.objects.create(
            country_code=Country.US,
        )
        self.assertEqual(str(shusshin), "United States")

    def test_fail_with_jp_prefecture_if_not_japan(self) -> None:
        """Should fail if a non-Japanese Shusshin has a prefecture."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shusshin.objects.create(
                country_code=Country.US,
                jp_prefecture=JPPrefecture.TOKYO,
            )

    def test_fail_without_jp_prefecture_for_japan(self) -> None:
        """Should fail if a Japanese Shusshin is missing a prefecture."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shusshin.objects.create(
                country_code=Country.JP,
            )
