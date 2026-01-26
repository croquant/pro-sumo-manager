"""Populate Division table with all sumo divisions."""

from django.db import migrations


def populate_divisions(apps, schema_editor):
    """Create Division entries for all divisions."""
    Division = apps.get_model("game", "Division")

    divisions = [
        (1, "M"),   # Makuuchi
        (2, "J"),   # Juryo
        (3, "Ms"),  # Makushita
        (4, "Sd"),  # Sandanme
        (5, "Jd"),  # Jonidan
        (6, "Jk"),  # Jonokuchi
        (7, "Mz"),  # Mae-zumo
        (8, "Bg"),  # Banzuke-gai
    ]

    for level, name in divisions:
        Division.objects.create(level=level, name=name)


def reverse_divisions(apps, schema_editor):
    """Remove all Division entries."""
    Division = apps.get_model("game", "Division")
    Division.objects.all().delete()


class Migration(migrations.Migration):
    """Populate Division with all divisions."""

    dependencies = [
        ("game", "0002_populate_shusshin"),
    ]

    operations = [
        migrations.RunPython(populate_divisions, reverse_divisions),
    ]
