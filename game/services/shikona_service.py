"""Service for generating Shikona (ring names) for heya selection."""

from __future__ import annotations

import random
from dataclasses import dataclass

from game.models import Shikona


@dataclass
class ShikonaOption:
    """A generated shikona option for display."""

    name: str  # Japanese kanji
    transliteration: str  # Romaji
    interpretation: str  # Meaning


# Shikona components for generation
# Format: (kanji, romaji, meaning)
SHIKONA_PREFIXES = [
    ("大", "Ō", "Great"),
    ("若", "Waka", "Young"),
    ("琴", "Koto", "Harp"),
    ("朝", "Asa", "Morning"),
    ("隆", "Taka", "Noble"),
    ("照", "Teru", "Shining"),
    ("霧", "Kiri", "Mist"),
    ("千", "Chi", "Thousand"),
    ("栃", "Tochi", "Horse chestnut"),
    ("高", "Taka", "High"),
    ("白", "Haku", "White"),
    ("北", "Kita", "North"),
    ("玉", "Tama", "Jewel"),
    ("清", "Kiyo", "Pure"),
    ("双", "Futago", "Twin"),
]

SHIKONA_SUFFIXES = [
    ("海", "umi", "Sea"),
    ("山", "yama", "Mountain"),
    ("川", "gawa", "River"),
    ("龍", "ryū", "Dragon"),
    ("島", "shima", "Island"),
    ("風", "kaze", "Wind"),
    ("雲", "kumo", "Cloud"),
    ("富士", "fuji", "Mount Fuji"),
    ("桜", "zakura", "Cherry blossom"),
    ("鵬", "hō", "Phoenix"),
    ("乃花", "nohana", "Flower"),
    ("錦", "nishiki", "Brocade"),
    ("光", "hikari", "Light"),
    ("岩", "iwa", "Rock"),
    ("嶽", "dake", "Peak"),
]


class ShikonaService:
    """
    Service for generating and managing Shikona (ring names).

    This service provides business logic for creating unique shikona
    options for stable name selection during onboarding.
    """

    @staticmethod
    def generate_shikona_options(count: int = 3) -> list[ShikonaOption]:
        """
        Generate unique shikona options for heya name selection.

        Args:
        ----
            count: Number of unique options to generate (default: 3).

        Returns:
        -------
            List of ShikonaOption instances with unique names.

        """
        options: list[ShikonaOption] = []
        used_names: set[str] = set()

        # Get existing shikona names to avoid duplicates
        existing_names = set(Shikona.objects.values_list("name", flat=True))
        existing_translit = set(
            Shikona.objects.values_list("transliteration", flat=True)
        )

        max_attempts = count * 10  # Prevent infinite loops
        attempts = 0

        while len(options) < count and attempts < max_attempts:
            attempts += 1

            # Pick random prefix and suffix
            prefix = random.choice(SHIKONA_PREFIXES)
            suffix = random.choice(SHIKONA_SUFFIXES)

            # Combine into name
            kanji = prefix[0] + suffix[0]
            romaji = prefix[1] + suffix[1]
            meaning = f"{prefix[2]} {suffix[2]}"

            # Check uniqueness
            if (
                kanji not in used_names
                and kanji not in existing_names
                and romaji not in existing_translit
            ):
                used_names.add(kanji)
                options.append(
                    ShikonaOption(
                        name=kanji,
                        transliteration=romaji,
                        interpretation=meaning,
                    )
                )

        return options

    @staticmethod
    def create_shikona_from_option(option: ShikonaOption) -> Shikona:
        """
        Create a Shikona model instance from a ShikonaOption.

        Args:
        ----
            option: The ShikonaOption to persist.

        Returns:
        -------
            The newly created Shikona instance.

        """
        return Shikona.objects.create(
            name=option.name,
            transliteration=option.transliteration,
            interpretation=option.interpretation,
        )
