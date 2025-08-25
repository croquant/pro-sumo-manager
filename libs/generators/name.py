"""Utilities for generating sumo wrestler names."""

from __future__ import annotations

import json
import os
import random
import re
from collections import Counter
from collections.abc import Callable
from typing import Any, TypedDict, cast

import pykakasi

DIRNAME = os.path.dirname(__file__)


PosEntry = tuple[str, float]
StartTable = list[PosEntry]


class BigramEntry(TypedDict):
    """Bigram probabilities for a single character."""

    end: float
    chars: StartTable


BigramTable = dict[str, BigramEntry]
TransitionTable = dict[str, StartTable]


def get_initial_existing_names() -> list[str]:
    """Retrieve a set of all existing names from skikona_corpus.txt."""
    with open(
        os.path.join(DIRNAME, "data", "shikona_corpus.txt"), encoding="utf-8"
    ) as f:
        names = [line.strip() for line in f if line.strip()]
    return names


def generate_name_char_bigram_table() -> dict[str, Any]:
    """Generate character bigram tables from a corpus of shikona."""
    names = get_initial_existing_names()

    start_counts: Counter[str] = Counter()
    bigram_counts: dict[str, Counter[str]] = {}
    end_counts: Counter[str] = Counter()
    for name in names:
        start_counts[name[0]] += 1
        for prev, nxt in zip(name, name[1:], strict=False):
            bigram_counts.setdefault(prev, Counter())[nxt] += 1
        end_counts[name[-1]] += 1

    start_total = sum(start_counts.values())
    start_table: StartTable = sorted(
        ((c, count / start_total) for c, count in start_counts.items()),
        key=lambda x: x[0],
    )

    bigram_table: BigramTable = {}
    for prev in sorted(set(bigram_counts) | set(end_counts)):
        counter = bigram_counts.get(prev, Counter())
        end = end_counts.get(prev, 0)
        total = end + sum(counter.values())
        bigram_table[prev] = {
            "chars": sorted(
                ((c, cnt / total) for c, cnt in counter.items()),
                key=lambda x: x[0],
            ),
            "end": end / total,
        }

    data = {"start": start_table, "bigrams": bigram_table}
    with open(
        os.path.join(DIRNAME, "data", "name_char_bigram_table.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def get_bigram_tables() -> tuple[StartTable, BigramTable]:
    """Load the bigram tables used for name generation."""
    with open(
        os.path.join(DIRNAME, "data", "name_char_bigram_table.json"),
        encoding="utf-8",
    ) as f:
        raw_data: dict[str, Any] = json.load(f)
    start = [(str(c), float(p)) for c, p in raw_data["start"]]
    bigrams_raw: dict[str, Any] = raw_data["bigrams"]
    bigrams: BigramTable = {
        str(prev): {
            "chars": [(str(c), float(p)) for c, p in entry["chars"]],
            "end": float(entry["end"]),
        }
        for prev, entry in bigrams_raw.items()
    }
    return start, bigrams


MAX_MAX_NAME_LEN = 5
MAX_ATTEMPTS = 100

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
    # Hepburn adjustments for consistency across romanization
    (re.compile(r"si"), "shi"),  # Convert Kunrei-shiki "si" to Hepburn "shi"
    (re.compile(r"ti"), "chi"),  # Convert "ti" to "chi"
    (re.compile(r"tu"), "tsu"),  # Convert "tu" to "tsu"
    (re.compile(r"zi"), "ji"),  # Convert "zi" to "ji"
    (re.compile(r"hu"), "fu"),  # Convert "hu" to "fu"
    # Normalize long vowels by collapsing duplicates
    (re.compile(r"aa"), "a"),
    (re.compile(r"ii"), "i"),
    (re.compile(r"ee"), "e"),
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
        generate_name_char_bigram_table()
        self.start_table, self.bigram_table = get_bigram_tables()
        self.kks = cast(Callable[[], Any], pykakasi.kakasi)()
        self.existing_names: set[str] = set(get_initial_existing_names())

    def __transliterate(self, name_jp: str) -> str:
        res = self.kks.convert(name_jp)
        return "".join([r["hepburn"] for r in res])

    def __fix_phonemes(self, name: str) -> str:
        for pattern, replacement in PHONEME_REPLACE:
            name = pattern.sub(replacement, name)
        return name

    def _get_kanji_shikona(self) -> str:
        shikona = ""

        population = [c for c, _ in self.start_table]
        weights = [p for _, p in self.start_table]
        start_c = self.random.choices(population, weights)[0]
        shikona += start_c

        bigrams_table = self.bigram_table.get(start_c)
        if bigrams_table is None:
            raise RuntimeError(
                f"No bigrams found for start character '{start_c}'"
            )

        while True:
            prev_c = shikona[-1]
            bigrams_table = self.bigram_table.get(prev_c)
            if bigrams_table is None:
                raise RuntimeError(
                    f"No bigrams found for previous character '{prev_c}'"
                )
            if self.random.random() < bigrams_table["end"]:
                return shikona
            population = [c for c, _ in bigrams_table["chars"]]
            weights = [p for _, p in bigrams_table["chars"]]
            next_c = self.random.choices(population, weights)[0]
            shikona += next_c

    def get(self) -> tuple[str, str]:
        """
        Generate a unique kanji sumo name and its romaji transliteration.

        Returns
        -------
        tuple[str, str]
            A tuple containing the generated kanji name and its romaji
            equivalent.

        Raises
        ------
        RuntimeError
            If a valid name cannot be generated after multiple attempts.

        """
        for _ in range(MAX_ATTEMPTS):
            kanji_name = self._get_kanji_shikona()
            if (
                len(kanji_name) > MAX_MAX_NAME_LEN
                or kanji_name in self.existing_names
            ):
                continue
            romaji_name = self.__fix_phonemes(self.__transliterate(kanji_name))
            self.existing_names.add(kanji_name)
            return kanji_name, romaji_name
        raise RuntimeError(
            "Failed to generate a valid name after multiple attempts."
        )
