"""Generator for wrestler origins based on historical probabilities."""

from __future__ import annotations

import random
from typing import Final

import pycountry

from libs.types.shusshin import Shusshin

# Probability that a generated wrestler is Japanese (vs foreign)
JAPANESE_PROB: Final[float] = 0.88

# Probability distribution for Japanese prefectures (ISO 3166-2 codes)
PREFECTURE_PROBABILITIES: Final[dict[str, float]] = {
    "JP-01": 0.0746288441145281,  # Hokkaido
    "JP-02": 0.043478260869565216,  # Aomori
    "JP-03": 0.011532343584305408,  # Iwate
    "JP-04": 0.015906680805938492,  # Miyagi
    "JP-05": 0.019353128313891833,  # Akita
    "JP-06": 0.012725344644750796,  # Yamagata
    "JP-07": 0.0165694591728526,  # Fukushima
    "JP-08": 0.027704135737009545,  # Ibaraki
    "JP-09": 0.013785790031813362,  # Tochigi
    "JP-10": 0.013123011664899258,  # Gunma
    "JP-11": 0.03207847295864263,  # Saitama
    "JP-12": 0.035790031813361614,  # Chiba
    "JP-13": 0.08059384941675504,  # Tokyo
    "JP-14": 0.035790031813361614,  # Kanagawa
    "JP-15": 0.018027571580063628,  # Niigata
    "JP-16": 0.0076882290562036056,  # Toyama
    "JP-17": 0.011267232237539766,  # Ishikawa
    "JP-18": 0.007555673382820784,  # Fukui
    "JP-19": 0.008218451749734889,  # Yamanashi
    "JP-20": 0.010339342523860021,  # Nagano
    "JP-21": 0.01497879109225875,  # Gifu
    "JP-22": 0.021474019088016966,  # Shizuoka
    "JP-23": 0.05726405090137858,  # Aichi
    "JP-24": 0.014581124072110286,  # Mie
    "JP-25": 0.005567338282078473,  # Shiga
    "JP-26": 0.011532343584305408,  # Kyoto
    "JP-27": 0.0662778366914104,  # Osaka
    "JP-28": 0.03989925768822906,  # Hyogo
    "JP-29": 0.0076882290562036056,  # Nara
    "JP-30": 0.0076882290562036056,  # Wakayama
    "JP-31": 0.003181336161187699,  # Tottori
    "JP-32": 0.005567338282078473,  # Shimane
    "JP-33": 0.007820784729586427,  # Okayama
    "JP-34": 0.010737009544008483,  # Hiroshima
    "JP-35": 0.014050901378579003,  # Yamaguchi
    "JP-36": 0.006230116648992577,  # Tokushima
    "JP-37": 0.006627783669141039,  # Kagawa
    "JP-38": 0.014183457051961824,  # Ehime
    "JP-39": 0.010471898197242842,  # Kochi
    "JP-40": 0.048117709437963944,  # Fukuoka
    "JP-41": 0.013123011664899258,  # Saga
    "JP-42": 0.017497348886532343,  # Nagasaki
    "JP-43": 0.023064687168610817,  # Kumamoto
    "JP-44": 0.012195121951219513,  # Oita
    "JP-45": 0.015111346765641569,  # Miyazaki
    "JP-46": 0.039766702014846236,  # Kagoshima
    "JP-47": 0.009146341463414634,  # Okinawa
}

# Probability distribution for foreign countries (ISO 3166-1 alpha-2 codes)
# "Other" represents all countries not explicitly listed
COUNTRY_PROBABILITIES: Final[dict[str, float]] = {
    "BG": 0.03,  # Bulgaria
    "BR": 0.03,  # Brazil
    "CN": 0.07,  # China
    "EE": 0.02,  # Estonia
    "GE": 0.04,  # Georgia
    "KP": 0.04,  # North Korea
    "KZ": 0.02,  # Kazakhstan
    "MN": 0.55,  # Mongolia
    "Other": 0.09,  # All other countries
    "RU": 0.07,  # Russia
    "UA": 0.02,  # Ukraine
    "US": 0.02,  # United States
}


class ShusshinGenerator:
    """Generates wrestler origins using probability-weighted selection."""

    def __init__(self, seed: int | None = None) -> None:
        """Initialize generator with optional seed for deterministic results."""
        self.random = random.Random(seed)

    def get(self) -> Shusshin:
        """Generate a random Shusshin based on historical probabilities."""
        if self.random.random() < JAPANESE_PROB:
            return self._get_japanese()
        return self._get_foreigner()

    def _get_japanese(self) -> Shusshin:
        """Select Japanese wrestler origin weighted by prefecture."""
        population, weights = zip(
            *PREFECTURE_PROBABILITIES.items(), strict=True
        )
        prefecture_code = self.random.choices(
            population=population, weights=weights
        )[0]
        return Shusshin(country_code="JP", jp_prefecture=prefecture_code)

    def _get_foreigner(self) -> Shusshin:
        """Select foreign wrestler origin weighted by historical data."""
        population, weights = zip(*COUNTRY_PROBABILITIES.items(), strict=True)
        country = self.random.choices(population=population, weights=weights)[0]

        if country == "Other":
            # Select random country except explicitly listed ones
            excluded_countries = {
                key for key in COUNTRY_PROBABILITIES if key != "Other"
            } | {"JP"}
            available_countries = [
                c.alpha_2
                for c in pycountry.countries
                if c.alpha_2 not in excluded_countries
            ]
            country = self.random.choice(available_countries)

        return Shusshin(country_code=country)
