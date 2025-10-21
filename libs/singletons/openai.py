"""Singleton OpenAI client instance for the application."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_openai_instance: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """
    Get or create the OpenAI client instance (lazy initialization).

    Returns:
        OpenAI client instance.

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set.

    """
    global _openai_instance
    if _openai_instance is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable must be set "
                "to use OpenAI features"
            )
        _openai_instance = OpenAI(api_key=api_key)
    return _openai_instance


# For backwards compatibility, create a property-like access
class _OpenAISingleton:
    """Wrapper class to provide property-like access to the OpenAI client."""

    def __getattr__(self, name: str) -> object:
        """Proxy all attributes to the underlying OpenAI client."""
        return getattr(get_openai_client(), name)


openai_singleton = _OpenAISingleton()
