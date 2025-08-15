from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from core.enums import Country, JPPrefecture


def populate_shusshin(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Shusshin = apps.get_model("core", "Shusshin")
    for country in Country:
        if country == Country.JP:
            for prefecture in JPPrefecture:
                Shusshin.objects.create(
                    country_code=Country.JP,
                    jp_prefecture=prefecture.value,
                )
        else:
            Shusshin.objects.create(country_code=country.value)


def unpopulate_shusshin(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Shusshin = apps.get_model("core", "Shusshin")
    Shusshin.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_shusshin_unique_shusshin_country_except_japan_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_shusshin, unpopulate_shusshin),
    ]
