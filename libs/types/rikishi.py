"""Type definitions for rikishi."""

from typing import Literal

from pydantic import BaseModel, Field

from libs.constants import (
    MAX_POTENTIAL,
    MAX_STAT_VALUE,
    MIN_POTENTIAL,
    MIN_STAT_VALUE,
)
from libs.types.shikona import Shikona
from libs.types.shusshin import Shusshin

# Type alias for stat names
StatName = Literal["strength", "technique", "balance", "endurance", "mental"]


class Rikishi(BaseModel):
    """
    A complete rikishi with name, origin, abilities, and individual stats.

    The relationship between current ability and individual stats:
    - current: Overall ability score (5-100) representing total capability
    - Individual stats: Specific attributes (1-20 each) that sum up to represent
      how the current ability is distributed across different areas
    - When current ability increases through training, individual stats improve
    - The starting distribution: all stats begin at 1, then (current - 5) points
      are randomly distributed among the five stats
    """

    shikona: Shikona = Field(..., description="Ring name with interpretation")
    shusshin: Shusshin = Field(..., description="Place of origin")
    potential: int = Field(
        ...,
        ge=MIN_POTENTIAL,
        le=MAX_POTENTIAL,
        description="Maximum ability the rikishi can reach (5-100)",
    )
    current: int = Field(
        ...,
        ge=MIN_POTENTIAL,
        le=MAX_POTENTIAL,
        description="Current overall ability level (5-100)",
    )
    strength: int = Field(
        default=1,
        ge=MIN_STAT_VALUE,
        le=MAX_STAT_VALUE,
        description="Physical strength stat (1-20)",
    )
    technique: int = Field(
        default=1,
        ge=MIN_STAT_VALUE,
        le=MAX_STAT_VALUE,
        description="Technical skill stat (1-20)",
    )
    balance: int = Field(
        default=1,
        ge=MIN_STAT_VALUE,
        le=MAX_STAT_VALUE,
        description="Balance and stability stat (1-20)",
    )
    endurance: int = Field(
        default=1,
        ge=MIN_STAT_VALUE,
        le=MAX_STAT_VALUE,
        description="Stamina and endurance stat (1-20)",
    )
    mental: int = Field(
        default=1,
        ge=MIN_STAT_VALUE,
        le=MAX_STAT_VALUE,
        description="Mental fortitude stat (1-20)",
    )
