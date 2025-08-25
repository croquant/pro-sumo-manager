"""Tests for the Shusshin model."""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.test import TestCase

from game.enums.country_enum import Country
from game.enums.jp_prefecture_enum import JPPrefecture
from game.models import Shusshin


class ShusshinModelTests(TestCase):
    """Tests for the Shusshin model."""

    def test_str_returns_prefecture_label_for_japan(self) -> None:
        """Should return the prefecture label when country is Japan."""
        shusshin = Shusshin.objects.get(
            country_code=Country.JP,
            jp_prefecture=JPPrefecture.TOKYO,
        )
        self.assertEqual(str(shusshin), "Tokyo")

    def test_str_returns_country_label_for_non_japan(self) -> None:
        """Should return the country label when not Japan."""
        shusshin = Shusshin.objects.get(country_code=Country.US)
        self.assertEqual(str(shusshin), "United States")

    def test_fail_with_jp_prefecture_if_not_japan(self) -> None:
        """Should fail if a non-Japanese Shusshin has a prefecture."""
        shusshin = Shusshin.objects.get(country_code=Country.US)
        with self.assertRaises(IntegrityError), transaction.atomic():
            shusshin.jp_prefecture = JPPrefecture.TOKYO
            shusshin.save()

    def test_fail_without_jp_prefecture_for_japan(self) -> None:
        """Should fail if a Japanese Shusshin is missing a prefecture."""
        shusshin = Shusshin.objects.get(
            country_code=Country.JP, jp_prefecture=JPPrefecture.TOKYO
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            shusshin.jp_prefecture = ""
            shusshin.save()

    def test_fail_duplicate_country_for_non_japan(self) -> None:
        """Should fail if two non-Japanese Shusshin share a country."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shusshin.objects.create(country_code=Country.US)

    def test_fail_duplicate_prefecture_for_japan(self) -> None:
        """Should fail if two Japanese Shusshin share a prefecture."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shusshin.objects.create(
                country_code=Country.JP,
                jp_prefecture=JPPrefecture.TOKYO,
            )


class ShusshinPopulationTests(TestCase):
    """Tests for the populated Shusshin records."""

    def test_all_shusshin_populated(self) -> None:
        """Should have entries for every country and Japanese prefecture."""
        non_jp_count = Shusshin.objects.filter(
            ~Q(country_code=Country.JP)
        ).count()
        jp_count = Shusshin.objects.filter(country_code=Country.JP).count()
        self.assertEqual(non_jp_count, len(list(Country)) - 1)
        self.assertEqual(jp_count, len(list(JPPrefecture)))
