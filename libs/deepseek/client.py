"""HTTP client for interacting with the DeepSeek API."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import APIStatusError, APITimeoutError, OpenAI, OpenAIError

__all__ = ["DeepSeekClient", "DeepSeekError"]


class DeepSeekError(Exception):
    """Raised when the DeepSeek API returns an error or invalid response."""


class DeepSeekClient:
    """Lightweight client for the DeepSeek API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout: float = 30.0,
    ) -> None:
        """
        Create a new DeepSeekClient instance.

        Args:
            api_key: API key for authentication. Falls back to the
                ``DEEPSEEK_API_KEY`` environment variable.
            base_url: Base URL for the DeepSeek API.
            model: Default model to use for requests.
            timeout: Request timeout in seconds.

        Raises:
            DeepSeekError: If no API key is provided.

        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise DeepSeekError("DEEPSEEK_API_KEY is not configured")

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._logger = logging.getLogger(__name__)
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def request(self, system_prompt: str, payload: str) -> dict[str, Any]:
        """
        Send a completion request to the DeepSeek API.

        Args:
            system_prompt: System prompt to guide the model.
            payload: User payload to send to the model.

        Returns:
            Parsed JSON response from the API.

        Raises:
            DeepSeekError: On network issues, HTTP errors, or invalid responses.

        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload},
        ]

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            request_id = getattr(response, "_request_id", None)
            if request_id:
                self._logger.info("DeepSeek request ID: %s", request_id)
            try:
                content = response.choices[0].message.content
                parsed = json.loads(content)
            except (json.JSONDecodeError, IndexError, AttributeError) as exc:
                raise DeepSeekError(
                    "Unable to parse JSON from DeepSeek"
                ) from exc
            if not isinstance(parsed, dict) or not parsed:
                raise DeepSeekError("DeepSeek returned an empty response")
            return parsed
        except APITimeoutError as exc:
            raise DeepSeekError("Request to DeepSeek timed out") from exc
        except APIStatusError as exc:
            message = (
                f"DeepSeek API error: {exc.status_code} {exc.response.text}"
            )
            raise DeepSeekError(message) from exc
        except OpenAIError as exc:
            raise DeepSeekError("Error communicating with DeepSeek") from exc
