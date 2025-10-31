"""Tests to ensure no real OpenAI API calls are made during testing."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from libs.generators.rikishi import RikishiGenerator
from libs.generators.shikona import ShikonaGenerator
from libs.singletons.openai import get_openai_singleton


class TestNoRealOpenAICalls(unittest.TestCase):
    """
    Verify that OpenAI is properly mocked globally by the test runner.

    These tests ensure that the custom test runner (OpenAIMockedTestRunner)
    is working correctly and preventing any real API calls.
    """

    def test_openai_singleton_returns_mock(self) -> None:
        """OpenAI singleton should return a mock client, not real client."""
        # Reset singleton to force re-initialization
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        client = get_openai_singleton()

        # Client should be a MagicMock, not a real OpenAI client
        self.assertIsInstance(client, MagicMock)

    def test_shikona_generator_uses_mock_client(self) -> None:
        """ShikonaGenerator should use a mocked OpenAI client."""
        # Reset singleton to ensure clean test
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        generator = ShikonaGenerator(seed=42)

        # The client should be a MagicMock
        self.assertIsInstance(generator.client, MagicMock)

    def test_rikishi_generator_uses_mock_client(self) -> None:
        """RikishiGenerator's ShikonaGenerator should use mock client."""
        # Reset singleton to ensure clean test
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        generator = RikishiGenerator(seed=42)

        # The shikona generator's client should be a MagicMock
        self.assertIsInstance(generator.shikona_generator.client, MagicMock)

    def test_singleton_maintains_singleton_behavior(self) -> None:
        """Multiple calls to get_openai_singleton should return same mock."""
        # Reset singleton to start fresh
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

        client1 = get_openai_singleton()
        client2 = get_openai_singleton()

        # Both should be mocks
        self.assertIsInstance(client1, MagicMock)
        self.assertIsInstance(client2, MagicMock)

        # Should return the same instance (singleton behavior)
        self.assertIs(client1, client2)
