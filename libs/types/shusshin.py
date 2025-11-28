"""Type definitions for shusshin (origin)."""

import pycountry
from pydantic import BaseModel, Field


class Shusshin(BaseModel):
    """Wrestler origin data (Django-agnostic)."""

    country_code: str = Field(
        ..., description="ISO 3166-1 alpha-2 country code"
    )
    jp_prefecture: str = Field(
        default="",
        description="ISO 3166-2 code for Japanese prefectures (if applicable)",
    )

    def __str__(self) -> str:
        """Return human-readable origin string."""
        if self.country_code == "JP" and self.jp_prefecture:
            prefecture = pycountry.subdivisions.get(code=self.jp_prefecture)
            prefecture_name = (
                prefecture.name if prefecture else self.jp_prefecture
            )
            return f"{prefecture_name}, Japan"
        country = pycountry.countries.get(alpha_2=self.country_code)
        country_name = country.name if country else self.country_code
        return country_name
