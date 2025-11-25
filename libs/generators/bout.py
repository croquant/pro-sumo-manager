"""Generator for sumo bouts."""

import logging
import os
import random
from typing import Final, Literal

from pydantic import BaseModel, Field

from libs.generators.rikishi import GeneratedRikishi
from libs.singletons.openai import get_openai_singleton

logger = logging.getLogger(__name__)

DIRNAME: Final[str] = os.path.dirname(__file__)
FORTUNE_COUNT: Final[int] = 5  # Number of fortune rolls for bout simulation


class BoutGeneratorInput(BaseModel):
    """Input data for generating a bout."""

    east_rikishi: GeneratedRikishi = Field(
        ..., description="The rikishi on the east side of the bout"
    )
    west_rikishi: GeneratedRikishi = Field(
        ..., description="The rikishi on the west side of the bout"
    )
    fortune: list[int] = Field(
        ...,
        description=(
            "A list of random integers to be used for randomness in the bout"
        ),
    )


class BoutGeneratorOutput(BaseModel):
    """Output data from a generated bout."""

    thinking: str = Field(
        ..., description="Step-by-step reasoning for the bout simulation"
    )
    winner: Literal["east", "west"] = Field(
        ..., description="The winner of the bout"
    )
    commentary: list[str] = Field(
        ...,
        description="A list of commentary lines describing the bout",
        min_length=3,
    )
    kimarite: Literal[
        "yorikiri",
        "oshidashi",
        "hatakikomi",
        "uwatenage",
        "shitatenage",
        "tsuppari",
        "kotenage",
        "yori-taoshi",
        "oshitaoshi",
        "hikiotoshi",
        "uwatedashinage",
        "shitatedashinage",
        "tsukiotoshi",
        "sukuinage",
        "tottari",
        "ketaguri",
        "utchari",
        "katasukashi",
    ] = Field(..., description="The kimarite (winning technique) used")
    excitement_level: float = Field(
        ...,
        description="An excitement level from 1 (boring) to 10 (thrilling)",
        ge=1,
        le=10,
    )
    east_xp_gain: int = Field(
        ..., ge=0, description="XP gained by east rikishi"
    )
    west_xp_gain: int = Field(
        ..., ge=0, description="XP gained by west rikishi"
    )


def _load_system_prompt() -> str:
    """Load the system prompt from the bout_prompt.md file."""
    prompt_path = os.path.join(DIRNAME, "data", "bout_prompt.md")
    with open(prompt_path, encoding="utf-8") as f:
        return f.read()


class BoutGenerator:
    """Generator for simulating sumo bouts using an LLM."""

    # Load system prompt once at class level
    _system_prompt: Final[str] = _load_system_prompt()

    def __init__(
        self,
        model: str = "gpt-5-mini",
        seed: int | None = None,
    ) -> None:
        """
        Initialize the bout generator.

        Args:
            model: The LLM model to use.
            seed: Optional seed for random number generation (for fortune).

        """
        self.model = model
        self.client = get_openai_singleton()
        self.random = random.Random(seed)

    def generate(
        self, east_rikishi: GeneratedRikishi, west_rikishi: GeneratedRikishi
    ) -> BoutGeneratorOutput:
        """
        Generate a bout between two rikishi.

        Args:
            east_rikishi: The east rikishi.
            west_rikishi: The west rikishi.

        Returns:
            The generated bout result.

        Raises:
            ValueError: If the API response cannot be parsed.

        """
        input_data = BoutGeneratorInput(
            east_rikishi=east_rikishi,
            west_rikishi=west_rikishi,
            fortune=self._generate_fortune(),
        )

        input_list = [
            {
                "role": "system",
                "content": self._system_prompt,
            },
            {"role": "user", "content": input_data.model_dump_json()},
        ]

        logger.debug("Sending bout generation request to OpenAI")
        response = self.client.responses.parse(
            model=self.model,
            reasoning={"effort": "low"},
            input=input_list,
            text_format=BoutGeneratorOutput,
        )
        logger.info("OpenAI API Usage: %s", response.usage)

        result = response.output_parsed
        if result is None:
            raise ValueError("Failed to parse bout generation response")

        return result

    def _generate_fortune(self) -> list[int]:
        """
        Generate a list of fortune values including criticals.

        Returns:
            A list of integers representing fortune values.

        """
        fortune_values = []
        for _ in range(FORTUNE_COUNT):
            roll = self.random.random()
            if roll < 0.02:
                # Critical Success (2%)
                fortune_values.append(20)
            elif roll < 0.04:
                # Critical Fail (2%)
                fortune_values.append(-5)
            else:
                # Normal range (96%)
                fortune_values.append(self.random.randint(0, 13))
        return fortune_values
