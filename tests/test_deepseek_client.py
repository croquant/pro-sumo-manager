"""Tests for the DeepSeek client."""

from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

import httpx
from openai import APIStatusError, APITimeoutError, OpenAIError

from libs.deepseek import DeepSeekClient, DeepSeekError


class DeepSeekClientTests(unittest.TestCase):
    """Unit tests for DeepSeekClient."""

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self) -> None:
        """Should raise if the API key is missing."""
        with self.assertRaises(DeepSeekError):
            DeepSeekClient()

    @patch("libs.deepseek.client.OpenAI")
    def test_request_success(self, mock_openai: Mock) -> None:
        """Should return parsed JSON on success."""
        response = Mock()
        response._request_id = "123"
        response.choices = [Mock(message=Mock(content='{"ok": true}'))]
        mock_openai.return_value.chat.completions.create.return_value = response
        client = DeepSeekClient(api_key="key", base_url="https://example.com")
        result = client.request("sys", "payload")
        self.assertEqual(result, {"ok": True})

    @patch("libs.deepseek.client.OpenAI")
    def test_request_http_error(self, mock_openai: Mock) -> None:
        """Should raise DeepSeekError on HTTP error status."""
        request = httpx.Request("POST", "https://example.com")
        response = httpx.Response(500, text="boom", request=request)
        mock_openai.return_value.chat.completions.create.side_effect = (
            APIStatusError("error", response=response, body="boom")
        )
        client = DeepSeekClient(api_key="key", base_url="https://example.com")
        with self.assertRaises(DeepSeekError):
            client.request("sys", "payload")

    @patch("libs.deepseek.client.OpenAI")
    def test_request_transport_error(self, mock_openai: Mock) -> None:
        """Should raise DeepSeekError on generic errors."""
        mock_openai.return_value.chat.completions.create.side_effect = (
            OpenAIError("boom")
        )
        client = DeepSeekClient(api_key="key", base_url="https://example.com")
        with self.assertRaises(DeepSeekError):
            client.request("sys", "payload")

    @patch("libs.deepseek.client.OpenAI")
    def test_request_invalid_json(self, mock_openai: Mock) -> None:
        """Should raise DeepSeekError on invalid JSON payload."""
        response = Mock()
        response._request_id = None
        response.choices = [Mock(message=Mock(content="not json"))]
        mock_openai.return_value.chat.completions.create.return_value = response
        client = DeepSeekClient(api_key="key", base_url="https://example.com")
        with self.assertRaises(DeepSeekError):
            client.request("sys", "payload")

    @patch("libs.deepseek.client.OpenAI")
    def test_request_timeout(self, mock_openai: Mock) -> None:
        """Should raise DeepSeekError on timeout."""
        request = httpx.Request("POST", "https://example.com")
        mock_openai.return_value.chat.completions.create.side_effect = (
            APITimeoutError(request)
        )
        client = DeepSeekClient(api_key="key", base_url="https://example.com")
        with self.assertRaises(DeepSeekError):
            client.request("sys", "payload")

    @patch("libs.deepseek.client.OpenAI")
    def test_request_empty_json(self, mock_openai: Mock) -> None:
        """Should raise DeepSeekError on empty JSON payload."""
        response = Mock()
        response.choices = [Mock(message=Mock(content="{}"))]
        mock_openai.return_value.chat.completions.create.return_value = response
        client = DeepSeekClient(api_key="key", base_url="https://example.com")
        with self.assertRaises(DeepSeekError):
            client.request("sys", "payload")
