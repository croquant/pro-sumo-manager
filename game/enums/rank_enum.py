"""Rank enumeration for sumo wrestling rank titles and directions."""

from django.db.models import TextChoices


class RankTitle(TextChoices):
    """
    Sumo wrestling rank titles.

    Rank titles represent the specific position a wrestler holds within
    a division. The value represents the short code used for display
    and storage.
    """

    YOKOZUNA = "Y", "Yokozuna"
    OZEKI = "O", "Ozeki"
    SEKIWAKE = "S", "Sekiwake"
    KOMUSUBI = "K", "Komusubi"
    MAEGASHIRA = "M", "Maegashira"
    JURYO = "J", "Juryo"
    MAKUSHITA = "Ms", "Makushita"
    SANDANME = "Sd", "Sandanme"
    JONIDAN = "Jd", "Jonidan"
    JONOKUCHI = "Jk", "Jonokuchi"
    MAE_ZUMO = "Mz", "Mae-zumo"
    BANZUKE_GAI = "Bg", "Banzuke-gai"


class Direction(TextChoices):
    """
    Rank side/direction.

    In sumo's banzuke (ranking system), wrestlers are ranked on either
    the East (higher prestige) or West side at each numbered position.
    """

    EAST = "E", "East"
    WEST = "W", "West"
