"""Utilities for generating sumo wrestler names."""

from __future__ import annotations

import json
import os
import random
import re
from collections.abc import Sequence

import pykakasi

DIRNAME = os.path.dirname(__file__)

PosEntry = tuple[str, float]
PosTable = list[list[PosEntry]]


def get_pos_table() -> PosTable:
    """Load the character position table used for name generation."""
    with open(os.path.join(DIRNAME, "data", "name_char_pos_table.json")) as f:
        raw_data: list[list[list[float | str]]] = json.load(f)
    return [[(str(c), float(p)) for c, p in pos] for pos in raw_data]


MIN_NAME_LEN = 2
LOW_MAX_NAME_LEN = 14
MED_MAX_NAME_LEN = 19
MAX_MAX_NAME_LEN = 24

LEN_PROBABILITIES = [
    0.025780189959294438,
    0.39620081411126185,
    0.4708276797829037,
    0.1044776119402985,
    0.0027137042062415195,
]

PHONEME_REPLACE = [
    ("samurai", "ji"),
    ("ryuu", "ryu"),
    ("ooo", "oo"),
    ("uoo", "uo"),
    ("aoo", "ao"),
    ("eoo", "eo"),
    ("aoo", "ao"),
    ("ioo", "io"),
    (r"(?<![nhr])ou", "o"),
    (r"ou$", "o"),
    (r"uu$", "u"),
]


class RikishiNameGenerator:
    """Generator for realistic-sounding sumo wrestler names."""

    def __init__(self) -> None:
        """Initialize the generator with probability tables and converters."""
        self.len_prob: Sequence[float] = LEN_PROBABILITIES
        self.pos_table: PosTable = get_pos_table()
        self.kks = pykakasi.kakasi()

    def __transliterate(self, name_jp: str) -> str:
        res = self.kks.convert(name_jp)
        return "".join([r["hepburn"] for r in res])

    def __get_len(self) -> int:
        return random.choices(  # noqa: S311
            population=range(1, len(self.len_prob) + 1), weights=self.len_prob
        )[0]

    def __fix_phonemes(self, name: str) -> str:
        for phoneme in PHONEME_REPLACE:
            name = re.sub(phoneme[0], phoneme[1], name)
        return name

    def __check_no(self, name_jp: str) -> bool:
        no_chars = {"\u30ce", "\u306e"}
        return not (name_jp[0] in no_chars or name_jp[-1] in no_chars)

    def __check_valid(self, name: str, name_jp: str) -> bool:
        length = len(name)
        max_len = random.choices(  # noqa: S311
            population=[LOW_MAX_NAME_LEN, MED_MAX_NAME_LEN, MAX_MAX_NAME_LEN],
            weights=[0.5, 0.4, 0.1],
        )[0]
        return MIN_NAME_LEN <= length <= max_len and self.__check_no(name_jp)

    def get(self) -> tuple[str, str]:
        """Return a tuple of (romanized name, Japanese name)."""
        while True:
            name_jp = ""
            for i in range(self.__get_len()):
                population, weights = zip(*self.pos_table[i], strict=False)
                c = random.choices(population, weights)[0]  # noqa: S311
                name_jp += c
            name = self.__transliterate(name_jp)
            name = self.__fix_phonemes(name)
            if self.__check_valid(name, name_jp):
                return (name, name_jp)
