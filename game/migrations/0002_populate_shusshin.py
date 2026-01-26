"""Populate Shusshin table with all countries and Japanese prefectures."""

from django.db import migrations


def populate_shusshin(apps, schema_editor):
    """Create Shusshin entries for all origins."""
    Shusshin = apps.get_model("game", "Shusshin")

    # Japanese prefectures (country_code=JP, jp_prefecture=prefecture code)
    jp_prefectures = [
        "JP-01", "JP-02", "JP-03", "JP-04", "JP-05", "JP-06", "JP-07",
        "JP-08", "JP-09", "JP-10", "JP-11", "JP-12", "JP-13", "JP-14",
        "JP-15", "JP-16", "JP-17", "JP-18", "JP-19", "JP-20", "JP-21",
        "JP-22", "JP-23", "JP-24", "JP-25", "JP-26", "JP-27", "JP-28",
        "JP-29", "JP-30", "JP-31", "JP-32", "JP-33", "JP-34", "JP-35",
        "JP-36", "JP-37", "JP-38", "JP-39", "JP-40", "JP-41", "JP-42",
        "JP-43", "JP-44", "JP-45", "JP-46", "JP-47",
    ]

    # All countries except Japan
    countries = [
        "AW", "AF", "AO", "AI", "AX", "AL", "AD", "AE", "AR", "AM",
        "AS", "AQ", "TF", "AG", "AU", "AT", "AZ", "BI", "BE", "BJ",
        "BQ", "BF", "BD", "BG", "BH", "BS", "BA", "BL", "BY", "BZ",
        "BM", "BO", "BR", "BB", "BN", "BT", "BV", "BW", "CF", "CA",
        "CC", "CH", "CL", "CN", "CI", "CM", "CD", "CG", "CK", "CO",
        "KM", "CV", "CR", "CU", "CW", "CX", "KY", "CY", "CZ", "DE",
        "DJ", "DM", "DK", "DO", "DZ", "EC", "EG", "ER", "EH", "ES",
        "EE", "ET", "FI", "FJ", "FK", "FR", "FO", "FM", "GA", "GB",
        "GE", "GG", "GH", "GI", "GN", "GP", "GM", "GW", "GQ", "GR",
        "GD", "GL", "GT", "GF", "GU", "GY", "HK", "HM", "HN", "HR",
        "HT", "HU", "ID", "IM", "IN", "IO", "IE", "IR", "IQ", "IS",
        "IL", "IT", "JM", "JE", "JO", "KZ", "KE", "KG", "KH", "KI",
        "KN", "KR", "KW", "LA", "LB", "LR", "LY", "LC", "LI", "LK",
        "LS", "LT", "LU", "LV", "MO", "MF", "MA", "MC", "MD", "MG",
        "MV", "MX", "MH", "MK", "ML", "MT", "MM", "ME", "MN", "MP",
        "MZ", "MR", "MS", "MQ", "MU", "MW", "MY", "YT", "NA", "NC",
        "NE", "NF", "NG", "NI", "NU", "NL", "NO", "NP", "NR", "NZ",
        "OM", "PK", "PA", "PN", "PE", "PH", "PW", "PG", "PL", "PR",
        "KP", "PT", "PY", "PS", "PF", "QA", "RE", "RO", "RU", "RW",
        "SA", "SD", "SN", "SG", "GS", "SH", "SJ", "SB", "SL", "SV",
        "SM", "SO", "PM", "RS", "SS", "ST", "SR", "SK", "SI", "SE",
        "SZ", "SX", "SC", "SY", "TC", "TD", "TG", "TH", "TJ", "TK",
        "TM", "TL", "TO", "TT", "TN", "TR", "TV", "TW", "TZ", "UG",
        "UA", "UM", "UY", "US", "UZ", "VA", "VC", "VE", "VG", "VI",
        "VN", "VU", "WF", "WS", "YE", "ZA", "ZM", "ZW",
    ]

    # Create Japanese prefecture entries
    for prefecture in jp_prefectures:
        Shusshin.objects.create(country_code="JP", jp_prefecture=prefecture)

    # Create entries for other countries
    for country in countries:
        Shusshin.objects.create(country_code=country, jp_prefecture="")


def reverse_shusshin(apps, schema_editor):
    """Remove all Shusshin entries."""
    Shusshin = apps.get_model("game", "Shusshin")
    Shusshin.objects.all().delete()


class Migration(migrations.Migration):
    """Populate Shusshin with all origins."""

    dependencies = [
        ("game", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_shusshin, reverse_shusshin),
    ]
