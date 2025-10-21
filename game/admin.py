"""Admin configuration for the game app."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from game.models import GameDate, Shikona, Shusshin


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
