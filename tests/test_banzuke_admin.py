"""Tests for the Banzuke admin configuration."""

from typing import cast

from django.contrib.admin.sites import site
from django.test import TestCase

from game.admin import BanzukeAdmin, BanzukeEntryAdmin
from game.models import (
    Banzuke,
    BanzukeEntry,
    Division,
    GameDate,
    Heya,
    Rank,
    Rikishi,
    Shikona,
    Shusshin,
)


class BanzukeAdminTests(TestCase):
    """Tests for :class:`game.admin.BanzukeAdmin`."""

    def setUp(self) -> None:
        """Store the registered admin instance for reuse."""
        self.admin = cast(BanzukeAdmin, site._registry[Banzuke])

    def test_admin_registered(self) -> None:
        """Banzuke should be registered with the admin site."""
        self.assertIsInstance(self.admin, BanzukeAdmin)

    def test_admin_configuration(self) -> None:
        """Admin options should expose useful information and filters."""
        self.assertEqual(
            self.admin.list_display,
            ("name", "location", "year", "month", "status"),
        )
        self.assertEqual(self.admin.list_filter, ("status", "year"))
        self.assertEqual(self.admin.search_fields, ("name", "location"))
        self.assertEqual(self.admin.ordering, ("-year", "-month"))


class BanzukeEntryAdminTests(TestCase):
    """Tests for :class:`game.admin.BanzukeEntryAdmin`."""

    def setUp(self) -> None:
        """Set up test data and admin instance."""
        self.admin = cast(BanzukeEntryAdmin, site._registry[BanzukeEntry])

        start = GameDate.objects.create(year=2024, month=1, day=1)
        end = GameDate.objects.create(year=2024, month=1, day=15)
        self.banzuke = Banzuke.objects.create(
            name="Hatsu Basho",
            location="Tokyo",
            year=2024,
            month=1,
            start_date=start,
            end_date=end,
        )

        division = Division.objects.get(name="M")
        self.rank = Rank.objects.create(division=division, title="Y", level=1)

        shikona = Shikona.objects.create(
            transliteration="Hakuho",
            name="白鵬",
            interpretation="White Phoenix",
        )
        shusshin = Shusshin.objects.get(country_code="MN")
        heya_name = Shikona.objects.create(
            transliteration="Miyagino",
            name="宮城野",
            interpretation="Miyagino",
        )
        heya = Heya.objects.create(name=heya_name, created_at=start)

        self.rikishi = Rikishi.objects.create(
            shikona=shikona,
            heya=heya,
            shusshin=shusshin,
            potential=100,
            strength=10,
            technique=10,
            balance=10,
            endurance=10,
            mental=10,
        )

        self.entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
            wins=8,
            losses=5,
            absences=2,
        )

    def test_admin_registered(self) -> None:
        """BanzukeEntry should be registered with the admin site."""
        self.assertIsInstance(self.admin, BanzukeEntryAdmin)

    def test_admin_configuration(self) -> None:
        """Admin options should expose useful information and filters."""
        self.assertEqual(
            self.admin.list_display,
            ("banzuke", "rikishi_name", "rank", "record_display"),
        )
        self.assertEqual(self.admin.list_filter, ("banzuke", "rank__division"))
        self.assertEqual(
            self.admin.search_fields,
            ("rikishi__shikona__transliteration",),
        )

    def test_display_methods(self) -> None:
        """Display helpers should return correct values."""
        self.assertEqual(self.admin.rikishi_name(self.entry), "Hakuho")
        self.assertEqual(self.admin.record_display(self.entry), "8-5-2")
