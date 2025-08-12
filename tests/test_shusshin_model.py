"""Tests for the Shusshin model."""

from django.db import IntegrityError, transaction
from django.test import TestCase

from core.enums.country_enum import Country
from core.enums.jp_prefecture_enum import JPPrefecture
from core.models import Shusshin


class ShusshinModelTests(TestCase):
    """Tests for the Shusshin model."""

    def test_str_returns_prefecture_label_for_japan(self) -> None:
        """`__str__` returns the prefecture label when country is Japan."""
        shusshin = Shusshin.objects.create(
            country_code=Country.JP,
            jp_prefecture=JPPrefecture.JP_13,
        )
        self.assertEqual(str(shusshin), JPPrefecture.JP_13.label)

    def test_str_returns_country_label_for_non_japan(self) -> None:
        """`__str__` returns the country label when not Japan."""
        shusshin = Shusshin.objects.create(
            country_code=Country.US,
            jp_prefecture="",
        )
        self.assertEqual(str(shusshin), Country.US.label)

    def test_jp_prefecture_required_only_for_japan(self) -> None:
        """Constraint enforces prefecture only for Japanese origins."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shusshin.objects.create(
                country_code=Country.US,
                jp_prefecture=JPPrefecture.JP_13,
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shusshin.objects.create(
                country_code=Country.JP,
                jp_prefecture="",
            )
