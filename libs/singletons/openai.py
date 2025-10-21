"""Singleton OpenAI client instance for the application."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openai_singleton = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
