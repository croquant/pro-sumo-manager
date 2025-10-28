"""Division enumeration for sumo wrestling divisions."""

from django.db.models import TextChoices


class Division(TextChoices):
    """
    Sumo wrestling divisions.

    Divisions are ordered from highest (Makuuchi) to lowest
    (Banzuke-gai). The value represents the short code used for
    display and storage.
    """

    MAKUUCHI = "M", "Makuuchi"
    JURYO = "J", "Juryo"
    MAKUSHITA = "Ms", "Makushita"
    SANDANME = "Sd", "Sandanme"
    JONIDAN = "Jd", "Jonidan"
    JONOKUCHI = "Jk", "Jonokuchi"
    MAE_ZUMO = "Mz", "Mae-zumo"
    BANZUKE_GAI = "Bg", "Banzuke-gai"
