"""Tests for the OpenAI singleton."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from libs.singletons.openai import _OpenAISingleton, get_openai_client


class OpenAIClientTests(unittest.TestCase):
    """Tests for the get_openai_client function."""

    @patch("libs.singletons.openai.OpenAI")
    @patch("libs.singletons.openai.os.getenv")
    def test_get_openai_client_with_api_key(
        self, mock_getenv: MagicMock, mock_openai: MagicMock
    ) -> None:
        """Should create OpenAI client when API key is set."""
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Reset the global instance to test initialization
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        client = get_openai_client()

        self.assertEqual(client, mock_client)
        mock_openai.assert_called_once_with(api_key="test-api-key")

    @patch("libs.singletons.openai.os.getenv")
    def test_get_openai_client_without_api_key(
        self, mock_getenv: MagicMock
    ) -> None:
        """Should raise ValueError when API key is not set."""
        mock_getenv.return_value = None

        # Reset the global instance to test initialization
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        with self.assertRaises(ValueError) as ctx:
            get_openai_client()

        self.assertIn("OPENAI_API_KEY", str(ctx.exception))

    @patch("libs.singletons.openai.OpenAI")
    @patch("libs.singletons.openai.os.getenv")
    def test_get_openai_client_singleton(
        self, mock_getenv: MagicMock, mock_openai: MagicMock
    ) -> None:
        """Should return the same instance on multiple calls."""
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Reset the global instance to test initialization
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        client1 = get_openai_client()
        client2 = get_openai_client()

        self.assertIs(client1, client2)
        # Should only create the client once
        mock_openai.assert_called_once()


class OpenAISingletonWrapperTests(unittest.TestCase):
    """Tests for the _OpenAISingleton wrapper class."""

    @patch("libs.singletons.openai.get_openai_client")
    def test_openai_singleton_proxy_attribute(
        self, mock_get_client: MagicMock
    ) -> None:
        """Should proxy attributes to the underlying OpenAI client."""
        mock_client = MagicMock()
        mock_client.responses = MagicMock()
        mock_get_client.return_value = mock_client

        wrapper = _OpenAISingleton()
        responses = wrapper.responses

        self.assertEqual(responses, mock_client.responses)
        mock_get_client.assert_called_once()

    @patch("libs.singletons.openai.get_openai_client")
    def test_openai_singleton_proxy_method(
        self, mock_get_client: MagicMock
    ) -> None:
        """Should proxy method calls to the underlying OpenAI client."""
        mock_client = MagicMock()
        mock_client.some_method.return_value = "result"
        mock_get_client.return_value = mock_client

        wrapper = _OpenAISingleton()
        result = wrapper.some_method()

        self.assertEqual(result, "result")
        mock_client.some_method.assert_called_once()
