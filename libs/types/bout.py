"""Type definitions for bout generation."""

from typing import Literal

from pydantic import BaseModel, Field

from libs.types.rikishi import Rikishi


class BoutContext(BaseModel):
    """Input data for generating a bout."""

    east_rikishi: Rikishi = Field(
        ..., description="The rikishi on the east side of the bout"
    )
    west_rikishi: Rikishi = Field(
        ..., description="The rikishi on the west side of the bout"
    )
    fortune: list[int] = Field(
        ...,
        description=(
            "A list of random integers to be used for randomness in the bout"
        ),
    )


class Bout(BaseModel):
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
