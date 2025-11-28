"""Type definitions for shikona."""

from pydantic import BaseModel, Field


class Shikona(BaseModel):
    """Structured response for a single shikona interpretation from OpenAI."""

    shikona: str = Field(
        ..., description="The kanji representation of the ring name"
    )
    transliteration: str = Field(
        ..., description="The reading of the name in Latin characters"
    )
    interpretation: str = Field(
        ..., description="The meaning and significance of the name"
    )
