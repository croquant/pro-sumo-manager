"""Custom Django test runner that mocks OpenAI globally."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from django.test.runner import DiscoverRunner

if TYPE_CHECKING:
    from unittest.mock import _patch


class OpenAIMockedTestRunner(DiscoverRunner):
    """
    Custom test runner that automatically mocks OpenAI for all tests.

    This prevents any real API calls from being made during testing without
    requiring manual mocking in each test file.
    """

    openai_patcher: _patch[MagicMock]

    def setup_test_environment(self, **kwargs: object) -> None:
        """Set up the test environment with OpenAI mocked globally."""
        super().setup_test_environment(**kwargs)

        # Start patching OpenAI globally
        self.openai_patcher = patch("libs.singletons.openai.OpenAI")
        mock_openai_class = self.openai_patcher.start()

        # Configure the mock to return a properly structured client
        mock_client = MagicMock()
        mock_client.responses.parse = MagicMock()
        mock_openai_class.return_value = mock_client

        # Also ensure the singleton is reset between test runs
        import libs.singletons.openai

        libs.singletons.openai._openai_instance = None

    def teardown_test_environment(self, **kwargs: object) -> None:
        """Tear down the test environment and stop OpenAI patching."""
        # Stop the global OpenAI patch
        self.openai_patcher.stop()

        super().teardown_test_environment(**kwargs)
