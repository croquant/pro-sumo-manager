"""Tests for the OpenAI singleton."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from libs.singletons.openai import get_openai_singleton


class OpenAIClientTests(unittest.TestCase):
    """Tests for the get_openai_singleton function."""

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

        client = get_openai_singleton()

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
            get_openai_singleton()

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

        client1 = get_openai_singleton()
        client2 = get_openai_singleton()

        self.assertIs(client1, client2)
        # Should only create the client once
        mock_openai.assert_called_once()
