"""Utilities for generating sumo wrestler names."""

from __future__ import annotations

import json
import os
import random
import re
from collections.abc import Sequence
from typing import Any

import pykakasi

DIRNAME = os.path.dirname(__file__)

PosEntry = tuple[str, float]
StartTable = list[PosEntry]
BigramTable = dict[str, StartTable]


def get_bigram_tables() -> tuple[StartTable, BigramTable]:
    """Load the bigram tables used for name generation."""
    with open(
        os.path.join(DIRNAME, "data", "name_char_bigram_table.json"),
        encoding="utf-8",
    ) as f:
        raw_data: dict[str, Any] = json.load(f)
    start = [(str(c), float(p)) for c, p in raw_data["start"]]
    bigrams: BigramTable = {
        str(prev): [(str(c), float(p)) for c, p in nxt]
        for prev, nxt in raw_data["bigrams"].items()
    }
    return start, bigrams


MIN_NAME_LEN = 2
LOW_MAX_NAME_LEN = 14
MED_MAX_NAME_LEN = 19
MAX_MAX_NAME_LEN = 24
MAX_ATTEMPTS = 100

LEN_PROBABILITIES = [
    0.4066852367688022,
    0.48328690807799446,
    0.10724233983286907,
    0.0027855153203342614,
]

PHONEME_REPLACE = [
    (re.compile("samurai"), "ji"),
    (re.compile("ryuu"), "ryu"),
    (re.compile("ooo"), "oo"),
    (re.compile("uoo"), "uo"),
    (re.compile("aoo"), "ao"),
    (re.compile("eoo"), "eo"),
    (re.compile("ioo"), "io"),
    (re.compile(r"(?<![nhr])ou"), "o"),
    (re.compile(r"ou$"), "o"),
    (re.compile(r"uu$"), "u"),
]


class RikishiNameGenerator:
    """Generator for realistic-sounding sumo wrestler names."""

    def __init__(self, seed: int | None = None) -> None:
        """
        Initialize the generator.

        Args:
            seed: Optional seed for deterministic name generation.

        """
        self.random = random.Random(seed)
        self.len_prob: Sequence[float] = LEN_PROBABILITIES
        self.start_table, self.bigram_table = get_bigram_tables()
        self.kks = pykakasi.kakasi()

    def __transliterate(self, name_jp: str) -> str:
        res = self.kks.convert(name_jp)
        return "".join([r["hepburn"] for r in res])

    def __get_len(self) -> int:
        return self.random.choices(
            population=range(MIN_NAME_LEN, MIN_NAME_LEN + len(self.len_prob)),
            weights=self.len_prob,
        )[0]

    def __fix_phonemes(self, name: str) -> str:
        for pattern, replacement in PHONEME_REPLACE:
            name = pattern.sub(replacement, name)
        return name

    def __check_no(self, name_jp: str) -> bool:
        no_chars = {"\u30ce", "\u306e"}
        return not (name_jp[0] in no_chars or name_jp[-1] in no_chars)

    def __check_valid(self, name: str, name_jp: str) -> bool:
        length = len(name)
        max_len = self.random.choices(
            population=[LOW_MAX_NAME_LEN, MED_MAX_NAME_LEN, MAX_MAX_NAME_LEN],
            weights=[0.5, 0.4, 0.1],
        )[0]
        lower = name.lower()
        return (
            MIN_NAME_LEN <= length <= max_len
            and self.__check_no(name_jp)
            and not lower.startswith("no")
            and not lower.endswith("no")
        )

    def get(self) -> tuple[str, str]:
        """
        Return a tuple of (romanized name, Japanese name).

        Raises:
            RuntimeError: If a valid name cannot be generated within
                ``MAX_ATTEMPTS``.

        """
        for _ in range(MAX_ATTEMPTS):
            name_jp = ""
            length = self.__get_len()
            for i in range(length):
                if i == 0:
                    population, weights = zip(*self.start_table, strict=False)
                else:
                    prev = name_jp[-1]
                    population, weights = zip(
                        *self.bigram_table.get(prev, self.start_table),
                        strict=False,
                    )
                c = self.random.choices(population, weights)[0]
                name_jp += c
            name = self.__transliterate(name_jp)
            name = self.__fix_phonemes(name)
            if self.__check_valid(name, name_jp):
                return (name, name_jp)
        raise RuntimeError(
            f"Failed to generate a valid name after {MAX_ATTEMPTS} attempts"
        )
