"""Tests for the Bout admin interface."""

from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from game.admin import BoutAdmin
from game.models import (
    Banzuke,
    BanzukeEntry,
    Bout,
    Division,
    GameDate,
    Heya,
    Rank,
    Rikishi,
    Shikona,
    Shusshin,
)


class BoutAdminTestCase(TestCase):
    """Base test case with common setup for Bout admin tests."""

    def setUp(self) -> None:
        """Set up test data."""
        self.site = AdminSite()
        self.admin = BoutAdmin(Bout, self.site)
        self.factory = RequestFactory()

        # Create dates
        self.start_date = GameDate.objects.create(year=2024, month=1, day=1)
        self.end_date = GameDate.objects.create(year=2024, month=1, day=15)

        # Create banzuke
        self.banzuke = Banzuke.objects.create(
            name="Hatsu Basho",
            location="Tokyo",
            year=2024,
            month=1,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        # Create division and ranks
        self.division = Division.objects.get(name="M")
        self.rank_east = Rank.objects.create(
            division=self.division, title="Y", level=1, order=1, direction="E"
        )
        self.rank_west = Rank.objects.create(
            division=self.division, title="Y", level=1, order=1, direction="W"
        )

        # Create heya
        heya_name = Shikona.objects.create(
            transliteration="Miyagino",
            name="宮城野",
            interpretation="Miyagino",
        )
        self.heya = Heya.objects.create(
            name=heya_name, created_at=self.start_date
        )

        # Create shusshin
        self.shusshin = Shusshin.objects.get(country_code="MN")

        # Create rikishi
        self.shikona_east = Shikona.objects.create(
            transliteration="Hakuho",
            name="白鵬",
            interpretation="White Phoenix",
        )
        self.east_rikishi = Rikishi.objects.create(
            shikona=self.shikona_east,
            heya=self.heya,
            shusshin=self.shusshin,
            potential=100,
            strength=15,
            technique=15,
            balance=15,
            endurance=15,
            mental=15,
        )

        self.shikona_west = Shikona.objects.create(
            transliteration="Terunofuji",
            name="照ノ富士",
            interpretation="Shining Fuji",
        )
        self.west_rikishi = Rikishi.objects.create(
            shikona=self.shikona_west,
            heya=self.heya,
            shusshin=self.shusshin,
            potential=100,
            strength=14,
            technique=14,
            balance=14,
            endurance=14,
            mental=14,
        )

        # Create banzuke entries
        self.east_entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.east_rikishi,
            rank=self.rank_east,
        )
        self.west_entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.west_rikishi,
            rank=self.rank_west,
        )

        # Create a bout
        self.bout = Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="A thrilling match between two yokozuna!",
        )


class TestBoutAdminDisplay(BoutAdminTestCase):
    """Tests for BoutAdmin display methods."""

    def test_east_rikishi_name(self) -> None:
        """Should return east rikishi's transliterated name."""
        result = self.admin.east_rikishi_name(self.bout)
        self.assertEqual(result, "Hakuho")

    def test_west_rikishi_name(self) -> None:
        """Should return west rikishi's transliterated name."""
        result = self.admin.west_rikishi_name(self.bout)
        self.assertEqual(result, "Terunofuji")

    def test_winner_display_east(self) -> None:
        """Should return winner name with position when east wins."""
        result = self.admin.winner_display(self.bout)
        self.assertEqual(result, "Hakuho (east)")

    def test_winner_display_west(self) -> None:
        """Should return winner name with position when west wins."""
        self.bout.winner = Bout.Winner.WEST
        self.bout.save()

        result = self.admin.winner_display(self.bout)
        self.assertEqual(result, "Terunofuji (west)")


class TestBoutAdminConfiguration(BoutAdminTestCase):
    """Tests for BoutAdmin configuration."""

    def test_list_display_fields(self) -> None:
        """Should have correct list_display configuration."""
        expected = (
            "banzuke",
            "day",
            "east_rikishi_name",
            "west_rikishi_name",
            "winner_display",
            "kimarite",
            "excitement_level",
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter_fields(self) -> None:
        """Should have correct list_filter configuration."""
        expected = ("banzuke", "day", "kimarite", "winner")
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self) -> None:
        """Should have correct search_fields configuration."""
        expected = (
            "east_rikishi__shikona__transliteration",
            "west_rikishi__shikona__transliteration",
        )
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self) -> None:
        """Should have commentary as readonly."""
        self.assertIn("commentary", self.admin.readonly_fields)

    def test_ordering(self) -> None:
        """Should order by banzuke and day."""
        self.assertEqual(self.admin.ordering, ("banzuke", "day"))

    def test_list_select_related(self) -> None:
        """Should have correct select_related for efficient queries."""
        expected = (
            "banzuke",
            "east_rikishi__shikona",
            "west_rikishi__shikona",
        )
        self.assertEqual(self.admin.list_select_related, expected)
