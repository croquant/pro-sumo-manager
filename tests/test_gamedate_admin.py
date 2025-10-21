"""Tests for the GameDate admin configuration."""

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from game.admin import GameDateAdmin
from game.models import GameDate


class GameDateAdminTests(TestCase):
    """Tests for the GameDate admin configuration."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = GameDateAdmin(GameDate, self.site)
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",  # noqa: S106
        )

    def test_has_add_permission_always_false(self) -> None:
        """Should always return False to prevent manual creation."""
        request = self.factory.get("/admin/game/gamedate/add/")
        request.user = self.user

        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_change_permission_always_false(self) -> None:
        """Should always return False to prevent editing."""
        request = self.factory.get("/admin/game/gamedate/")
        request.user = self.user

        self.assertFalse(self.admin.has_change_permission(request))

    def test_has_change_permission_with_obj_always_false(self) -> None:
        """Should always return False even with specific object."""
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        request = self.factory.get("/admin/game/gamedate/")
        request.user = self.user

        self.assertFalse(self.admin.has_change_permission(request, game_date))

    def test_has_delete_permission_always_false(self) -> None:
        """Should always return False to preserve historical record."""
        request = self.factory.get("/admin/game/gamedate/")
        request.user = self.user

        self.assertFalse(self.admin.has_delete_permission(request))

    def test_has_delete_permission_with_obj_always_false(self) -> None:
        """Should always return False even with specific object."""
        game_date = GameDate.objects.create(year=1, month=1, day=1)
        request = self.factory.get("/admin/game/gamedate/")
        request.user = self.user

        self.assertFalse(self.admin.has_delete_permission(request, game_date))
