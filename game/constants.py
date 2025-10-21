"""Constants and configuration values for the game application."""

from __future__ import annotations

from typing import Final

# Game calendar constants
N_MONTHS: Final[int] = 12
N_DAYS: Final[int] = 24

# Maximum value for individual wrestler stats
MAX_STAT_VALUE: Final[int] = 20

# Division names and levels for Django model choices
DIVISION_NAMES: Final[list[tuple[str, str]]] = [
    ("Makuuchi", "Makuuchi"),
    ("Juryo", "Juryo"),
    ("Makushita", "Makushita"),
    ("Sandanme", "Sandanme"),
    ("Jonidan", "Jonidan"),
    ("Jonokuchi", "Jonokuchi"),
    ("Mae-zumo", "Mae-zumo"),
    ("Banzuke-gai", "Banzuke-gai"),
]

# Short names for divisions (used in UI/display)
DIVISION_NAMES_SHORT: Final[dict[str, str]] = {
    "Makuuchi": "M",
    "Juryo": "J",
    "Makushita": "Ms",
    "Sandanme": "Sd",
    "Jonidan": "Jd",
    "Jonokuchi": "Jk",
    "Mae-zumo": "Mz",
    "Banzuke-gai": "Bg",
}

# Rank names for Django model choices
RANK_NAMES: Final[list[tuple[str, str]]] = [
    ("Yokozuna", "Yokozuna"),
    ("Ozeki", "Ozeki"),
    ("Sekiwake", "Sekiwake"),
    ("Komusubi", "Komusubi"),
    ("Maegashira", "Maegashira"),
    ("Juryo", "Juryo"),
    ("Makushita", "Makushita"),
    ("Sandanme", "Sandanme"),
    ("Jonidan", "Jonidan"),
    ("Jonokuchi", "Jonokuchi"),
    ("Mae-zumo", "Mae-zumo"),
    ("Banzuke-gai", "Banzuke-gai"),
]

# Short names for ranks (used in UI/display)
RANK_NAMES_SHORT: Final[dict[str, str]] = {
    "Yokozuna": "Y",
    "Ozeki": "O",
    "Sekiwake": "S",
    "Komusubi": "K",
    "Maegashira": "M",
    "Juryo": "J",
    "Makushita": "Ms",
    "Sandanme": "Sd",
    "Jonidan": "Jd",
    "Jonokuchi": "Jk",
    "Mae-zumo": "Mz",
    "Banzuke-gai": "Bg",
}

# Ranking levels for ordering (lower number = higher rank)
RANKING_LEVELS: Final[dict[str, int]] = {
    "Yokozuna": 1,
    "Ozeki": 2,
    "Sekiwake": 3,
    "Komusubi": 4,
    "Maegashira": 5,
    "Juryo": 6,
    "Makushita": 7,
    "Sandanme": 8,
    "Jonidan": 9,
    "Jonokuchi": 10,
    "Mae-zumo": 11,
    "Banzuke-gai": 12,
}

# Direction names for rank positions
DIRECTION_NAMES: Final[list[tuple[str, str]]] = [
    ("East", "East"),
    ("West", "West"),
]

# Short names for directions (used in UI/display)
DIRECTION_NAMES_SHORT: Final[dict[str, str]] = {
    "East": "E",
    "West": "W",
}
