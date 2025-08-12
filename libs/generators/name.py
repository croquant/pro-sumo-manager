import json
import os
import random
import re

import pykakasi

DIRNAME = os.path.dirname(__file__)


def get_pos_table():
    with open(os.path.join(DIRNAME, "data", "name_char_pos_table.json")) as f:
        return json.load(f)


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
    def __init__(self) -> None:
        self.len_prob = LEN_PROBABILITIES
        self.pos_table = get_pos_table()
        self.kks = pykakasi.kakasi()

    def __transliterate(self, name_jp):
        res = self.kks.convert(name_jp)
        return "".join([r["hepburn"] for r in res])

    def __get_len(self):
        return random.choices(
            population=range(1, len(self.len_prob) + 1), weights=self.len_prob
        )[0]

    def __fix_phonemes(self, name):
        for phoneme in PHONEME_REPLACE:
            name = re.sub(phoneme[0], phoneme[1], name)
        return name

    def __check_no(self, name_jp):
        no_chars = {"\u30ce", "\u306e"}
        return not (name_jp[0] in no_chars or name_jp[-1] in no_chars)

    def __check_valid(self, name, name_jp):
        length = len(name)
        max_len = random.choices(
            population=[LOW_MAX_NAME_LEN, MED_MAX_NAME_LEN, MAX_MAX_NAME_LEN],
            weights=[0.5, 0.4, 0.1],
        )[0]
        return MIN_NAME_LEN <= length <= max_len and self.__check_no(name_jp)

    def get(self):
        while True:
            name_jp = ""
            for i in range(self.__get_len()):
                population, weights = zip(*self.pos_table[i], strict=False)
                c = random.choices(population, weights)[0]
                name_jp += c
            name = self.__transliterate(name_jp)
            name = self.__fix_phonemes(name)
            if self.__check_valid(name, name_jp):
                return (name, name_jp)
