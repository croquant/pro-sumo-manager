"""Tests for TrainingSession admin configuration."""

from __future__ import annotations

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from game.admin import TrainingSessionAdmin
from game.models import Rikishi, Shikona, TrainingSession
from game.services import TrainingService


class TrainingSessionAdminTests(TestCase):
    """Test suite for TrainingSessionAdmin."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = TrainingSessionAdmin(TrainingSession, self.site)
        self.factory = RequestFactory()

        self.shikona = Shikona.objects.create(
            name="テスト",
            transliteration="Tesuto",
            interpretation="Test wrestler",
        )
        self.rikishi = Rikishi.objects.create(
            shikona=self.shikona,
            potential=50,
            xp=500,
            strength=5,
            technique=3,
            balance=2,
            endurance=1,
            mental=1,
        )
        self.session = TrainingService.train_stat(self.rikishi, "strength")

    def test_rikishi_name_display(self) -> None:
        """Should return the wrestler's ring name."""
        self.assertEqual(
            self.admin.rikishi_name(self.session),
            "Tesuto",
        )

    def test_stat_display(self) -> None:
        """Should return the stat name."""
        self.assertEqual(self.admin.stat_display(self.session), "Strength")

    def test_stat_change_display(self) -> None:
        """Should return the stat change."""
        self.assertEqual(self.admin.stat_change(self.session), "5 → 6")

    def test_has_add_permission(self) -> None:
        """Should not allow manual creation."""
        request = self.factory.get("/admin/")
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_change_permission(self) -> None:
        """Should not allow editing."""
        request = self.factory.get("/admin/")
        self.assertFalse(self.admin.has_change_permission(request))
        self.assertFalse(self.admin.has_change_permission(request, self.session))

    def test_has_delete_permission(self) -> None:
        """Should not allow deletion."""
        request = self.factory.get("/admin/")
        self.assertFalse(self.admin.has_delete_permission(request))
        self.assertFalse(self.admin.has_delete_permission(request, self.session))

    def test_list_display_fields(self) -> None:
        """Should have correct list display fields."""
        expected = (
            "rikishi_name",
            "stat_display",
            "stat_change",
            "xp_cost",
            "created_at",
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_readonly_fields(self) -> None:
        """Should have correct readonly fields."""
        expected = (
            "rikishi",
            "stat",
            "xp_cost",
            "stat_before",
            "stat_after",
            "created_at",
        )
        self.assertEqual(self.admin.readonly_fields, expected)
