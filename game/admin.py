"""Admin configuration for the game app."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from game.models import (
    Banzuke,
    BanzukeEntry,
    Bout,
    Division,
    GameDate,
    Rank,
    Rikishi,
    Shikona,
    Shusshin,
    TrainingSession,
)


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
        obj: GameDate | None = None,  # noqa: ARG002
    ) -> bool:
        """Disable editing - dates are immutable."""
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: GameDate | None = None,  # noqa: ARG002
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
        obj: Division | None = None,  # noqa: ARG002
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


@admin.register(Rikishi)
class RikishiAdmin(admin.ModelAdmin[Rikishi]):
    """Admin panel configuration for :class:`game.models.Rikishi`."""

    list_display = (
        "shikona_name",
        "shusshin_display",
        "rank_display",
        "debut_display",
        "intai_display",
        "current_stats",
        "potential",
        "xp",
    )
    list_filter = ("rank__division", "shusshin__country_code")
    search_fields = (
        "shikona__name",
        "shikona__transliteration",
    )
    ordering = ("shikona__transliteration",)
    list_select_related = ("shikona", "shusshin", "rank", "debut", "intai")

    @admin.display(description="Shikona")
    def shikona_name(self, obj: Rikishi) -> str:
        """Return the wrestler's ring name."""
        return obj.shikona.transliteration

    @admin.display(description="Shusshin")
    def shusshin_display(self, obj: Rikishi) -> str:
        """Return the wrestler's place of origin."""
        return str(obj.shusshin) if obj.shusshin else "-"

    @admin.display(description="Rank")
    def rank_display(self, obj: Rikishi) -> str:
        """Return the wrestler's current rank."""
        return str(obj.rank) if obj.rank else "-"

    @admin.display(description="Debut")
    def debut_display(self, obj: Rikishi) -> str:
        """Return the debut date."""
        return str(obj.debut) if obj.debut else "-"

    @admin.display(description="Retirement")
    def intai_display(self, obj: Rikishi) -> str:
        """Return the retirement date."""
        return str(obj.intai) if obj.intai else "-"

    @admin.display(description="Current/Potential")
    def current_stats(self, obj: Rikishi) -> str:
        """Return current vs potential stats."""
        return f"{obj.current}/{obj.potential}"


@admin.register(Banzuke)
class BanzukeAdmin(admin.ModelAdmin[Banzuke]):
    """Admin panel configuration for :class:`game.models.Banzuke`."""

    list_display = ("name", "location", "year", "month", "status")
    list_filter = ("status", "year")
    search_fields = ("name", "location")
    ordering = ("-year", "-month")


@admin.register(BanzukeEntry)
class BanzukeEntryAdmin(admin.ModelAdmin[BanzukeEntry]):
    """Admin panel configuration for :class:`game.models.BanzukeEntry`."""

    list_display = (
        "banzuke",
        "rikishi_name",
        "rank",
        "record_display",
    )
    list_filter = ("banzuke", "rank__division")
    search_fields = ("rikishi__shikona__transliteration",)
    ordering = ("banzuke", "rank")
    list_select_related = ("banzuke", "rikishi__shikona", "rank__division")

    @admin.display(description="Rikishi")
    def rikishi_name(self, obj: BanzukeEntry) -> str:
        """Return the wrestler's ring name."""
        return obj.rikishi.shikona.transliteration

    @admin.display(description="Record")
    def record_display(self, obj: BanzukeEntry) -> str:
        """Return the win-loss record."""
        return obj.record


@admin.register(Bout)
class BoutAdmin(admin.ModelAdmin[Bout]):
    """Admin panel configuration for :class:`game.models.Bout`."""

    list_display = (
        "banzuke",
        "day",
        "east_rikishi_name",
        "west_rikishi_name",
        "winner_display",
        "kimarite",
        "excitement_level",
    )
    list_filter = ("banzuke", "day", "kimarite", "winner")
    search_fields = (
        "east_rikishi__shikona__transliteration",
        "west_rikishi__shikona__transliteration",
    )
    ordering = ("banzuke", "day")
    readonly_fields = ("commentary",)
    list_select_related = (
        "banzuke",
        "east_rikishi__shikona",
        "west_rikishi__shikona",
    )

    @admin.display(description="East")
    def east_rikishi_name(self, obj: Bout) -> str:
        """Return the east wrestler's ring name."""
        return obj.east_rikishi.shikona.transliteration

    @admin.display(description="West")
    def west_rikishi_name(self, obj: Bout) -> str:
        """Return the west wrestler's ring name."""
        return obj.west_rikishi.shikona.transliteration

    @admin.display(description="Winner")
    def winner_display(self, obj: Bout) -> str:
        """Return the winner's name with position."""
        winner_name = obj.winner_rikishi.shikona.transliteration
        return f"{winner_name} ({obj.winner})"


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin[TrainingSession]):
    """Admin panel configuration for :class:`game.models.TrainingSession`."""

    list_display = (
        "rikishi_name",
        "stat_display",
        "stat_change",
        "xp_cost",
        "created_at",
    )
    list_filter = ("stat", "created_at")
    search_fields = ("rikishi__shikona__transliteration",)
    ordering = ("-created_at",)
    list_select_related = ("rikishi__shikona",)
    readonly_fields = (
        "rikishi",
        "stat",
        "xp_cost",
        "stat_before",
        "stat_after",
        "created_at",
    )

    @admin.display(description="Rikishi")
    def rikishi_name(self, obj: TrainingSession) -> str:
        """Return the wrestler's ring name."""
        return obj.rikishi.shikona.transliteration

    @admin.display(description="Stat")
    def stat_display(self, obj: TrainingSession) -> str:
        """Return the stat name."""
        return obj.get_stat_display()

    @admin.display(description="Change")
    def stat_change(self, obj: TrainingSession) -> str:
        """Return the stat change."""
        return f"{obj.stat_before} → {obj.stat_after}"

    def has_add_permission(
        self,
        request: HttpRequest,
        _obj: TrainingSession | None = None,
    ) -> bool:
        """Disable manual creation - use TrainingService instead."""
        return False

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: TrainingSession | None = None,  # noqa: ARG002
    ) -> bool:
        """Disable editing - training records are immutable."""
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: TrainingSession | None = None,  # noqa: ARG002
    ) -> bool:
        """Disable deletion - preserve training history."""
        return False
