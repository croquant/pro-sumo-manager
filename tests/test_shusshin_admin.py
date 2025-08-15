"""Tests for the Shusshin admin configuration."""

from typing import cast

from django.contrib.admin.sites import site
from django.test import TestCase

from core.admin import ShusshinAdmin
from core.enums.country_enum import Country
from core.enums.jp_prefecture_enum import JPPrefecture
from core.models import Shusshin


class ShusshinAdminTests(TestCase):
    """Tests for :class:`core.admin.ShusshinAdmin`."""

    def setUp(self) -> None:
        """Store the registered admin instance for reuse."""
        self.admin = cast(ShusshinAdmin, site._registry[Shusshin])

    def test_admin_registered(self) -> None:
        """Shusshin should be registered with the admin site."""
        self.assertIsInstance(self.admin, ShusshinAdmin)

    def test_admin_configuration(self) -> None:
        """Admin options should expose useful information and filters."""
        self.assertEqual(self.admin.list_display, ("country", "prefecture"))
        self.assertEqual(self.admin.list_filter, ("country_code",))
        self.assertEqual(
            self.admin.search_fields,
            ("country_code", "jp_prefecture"),
        )
        self.assertEqual(self.admin.ordering, ("country_code", "jp_prefecture"))

    def test_display_methods(self) -> None:
        """Display helpers should return human-readable labels."""
        shusshin = Shusshin.objects.get(
            country_code=Country.JP,
            jp_prefecture=JPPrefecture.TOKYO,
        )
        self.assertEqual(self.admin.country(shusshin), "Japan")
        self.assertEqual(self.admin.prefecture(shusshin), "Tokyo")
