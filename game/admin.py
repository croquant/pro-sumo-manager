"""Admin configuration for the game app."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from game.models import Division, GameDate, Rank, Shikona, Shusshin


@admin.register(Shusshin)
class ShusshinAdmin(admin.ModelAdmin[Shusshin]):
    """Admin panel configuration for :class:`game.models.Shusshin`."""

    list_display = ("country", "prefecture")
    list_filter = ("country_code",)
    search_fields = ("country_code", "jp_prefecture")
    ordering = ("country_code", "jp_prefecture")

    @admin.display(description="Country")
    def country(self, obj: Shusshin) -> str:
        """Return the human-readable country name."""
        return obj.get_country_code_display()

    @admin.display(description="Prefecture")
    def prefecture(self, obj: Shusshin) -> str:
        """Return the human-readable prefecture name."""
        return obj.get_jp_prefecture_display()


@admin.register(Shikona)
class ShikonaAdmin(admin.ModelAdmin[Shikona]):
    """Admin panel configuration for :class:`game.models.Shikona`."""

    list_display = ("transliteration", "name", "parent", "interpretation")
    list_select_related = ("parent",)
    search_fields = ("name", "transliteration")
    ordering = ("transliteration",)


@admin.register(GameDate)
class GameDateAdmin(admin.ModelAdmin[GameDate]):
    """Admin panel configuration for :class:`game.models.GameDate`."""

    list_display = ("year", "month", "day")
    list_filter = ("year", "month")
    search_fields = ("year", "month", "day")
    ordering = ("-year", "-month", "-day")
    readonly_fields = ("year", "month", "day")

    def has_add_permission(
        self,
        request: HttpRequest,
        _obj: GameDate | None = None,
    ) -> bool:
        """Disable manual creation - use GameClockService instead."""
        return False

    def has_change_permission(
        self,
        request: HttpRequest,
        _obj: GameDate | None = None,
    ) -> bool:
        """Disable editing - dates are immutable."""
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        _obj: GameDate | None = None,
    ) -> bool:
        """Disable deletion - preserve historical record."""
        return False


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin[Division]):
    """Admin panel configuration for :class:`game.models.Division`."""

    list_display = ("level", "division_name")
    ordering = ("level",)
    readonly_fields = ("level", "name")

    @admin.display(description="Division")
    def division_name(self, obj: Division) -> str:
        """Return the full division name."""
        return obj.get_name_display()

    def has_add_permission(
        self,
        request: HttpRequest,
        _obj: Division | None = None,
    ) -> bool:
        """Disable manual creation - populated via migration."""
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        _obj: Division | None = None,
    ) -> bool:
        """Disable deletion - divisions are permanent data."""
        return False


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin[Rank]):
    """Admin panel configuration for :class:`game.models.Rank`."""

    list_display = ("rank_name", "division", "level", "order", "direction_name")
    list_filter = ("division", "title", "direction")
    search_fields = ("title",)
    ordering = ("level", "order", "direction")
    readonly_fields = ("level",)

    @admin.display(description="Rank")
    def rank_name(self, obj: Rank) -> str:
        """Return the formatted rank name."""
        return str(obj)

    @admin.display(description="Direction")
    def direction_name(self, obj: Rank) -> str:
        """Return the full direction name."""
        return obj.get_direction_display() if obj.direction else "-"
