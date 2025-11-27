"""Generator for sumo bouts."""

import logging
import os
import random
from typing import Final

from libs.generators.rikishi import Rikishi
from libs.singletons.openai import get_openai_singleton
from libs.types.bout import Bout, BoutContext

logger = logging.getLogger(__name__)

DIRNAME: Final[str] = os.path.dirname(__file__)
FORTUNE_COUNT: Final[int] = 5  # Number of fortune rolls for bout simulation


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

    def generate(self, east_rikishi: Rikishi, west_rikishi: Rikishi) -> Bout:
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
        input_data = BoutContext(
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
            text_format=Bout,
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
