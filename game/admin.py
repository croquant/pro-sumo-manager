"""Admin configuration for the game app."""

from django.contrib import admin

from game.models import Shusshin


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
