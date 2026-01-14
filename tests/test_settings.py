"""Tests for Django settings security features."""

from __future__ import annotations

import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


def _reload_settings_with_env(env: dict[str, str]) -> types.ModuleType:
    """
    Force reload of settings module with specific environment.

    This patches load_dotenv to prevent loading from .env file,
    ensuring only the provided environment variables are used.

    Returns:
        The freshly loaded settings module.

    """
    # Remove cached modules
    for mod in list(sys.modules.keys()):
        if mod.startswith("config"):
            del sys.modules[mod]

    # Patch load_dotenv to do nothing (prevent loading .env file)
    with (
        patch("dotenv.load_dotenv"),
        patch.dict(os.environ, env, clear=True),
    ):
        return importlib.import_module("config.settings")


class TestDebugSetting(unittest.TestCase):
    """Tests for DEBUG setting parsing."""

    def test_debug_defaults_to_true(self) -> None:
        """DEBUG should default to True when not set."""
        settings = _reload_settings_with_env({"DJANGO_SECRET_KEY": "test-key"})
        self.assertTrue(settings.DEBUG)

    def test_debug_true_values(self) -> None:
        """DEBUG should be True for various truthy string values."""
        truthy_values = ["True", "true", "TRUE", "1", "yes", "YES"]
        for value in truthy_values:
            with self.subTest(value=value):
                settings = _reload_settings_with_env(
                    {"DEBUG": value, "DJANGO_SECRET_KEY": "test-key"}
                )
                self.assertTrue(
                    settings.DEBUG, f"DEBUG should be True for '{value}'"
                )

    def test_debug_false_values(self) -> None:
        """DEBUG should be False for non-truthy string values."""
        falsy_values = ["False", "false", "0", "no", ""]
        for value in falsy_values:
            with self.subTest(value=value):
                settings = _reload_settings_with_env(
                    {
                        "DEBUG": value,
                        "DJANGO_SECRET_KEY": "test-key",
                        "ALLOWED_HOSTS": "example.com",
                    }
                )
                self.assertFalse(
                    settings.DEBUG, f"DEBUG should be False for '{value}'"
                )


class TestSecretKeySetting(unittest.TestCase):
    """Tests for SECRET_KEY setting security."""

    def test_secret_key_from_environment(self) -> None:
        """SECRET_KEY should be read from environment variable."""
        settings = _reload_settings_with_env(
            {"DJANGO_SECRET_KEY": "my-custom-secret-key"}
        )
        self.assertEqual(settings.SECRET_KEY, "my-custom-secret-key")

    def test_secret_key_auto_generated_in_debug_mode(self) -> None:
        """SECRET_KEY should be auto-generated when missing in DEBUG mode."""
        settings = _reload_settings_with_env({"DEBUG": "True"})
        self.assertIsNotNone(settings.SECRET_KEY)
        # Django's get_random_secret_key() generates 50-char keys
        self.assertGreaterEqual(len(settings.SECRET_KEY), 50)

    def test_secret_key_is_random_each_load(self) -> None:
        """Auto-generated SECRET_KEY should be random (not predictable)."""
        settings1 = _reload_settings_with_env({"DEBUG": "True"})
        key1 = settings1.SECRET_KEY

        settings2 = _reload_settings_with_env({"DEBUG": "True"})
        key2 = settings2.SECRET_KEY

        # Keys should be different on each load (random generation)
        self.assertNotEqual(key1, key2)

    def test_secret_key_required_in_production(self) -> None:
        """ImproperlyConfigured should be raised in production without key."""
        from django.core.exceptions import ImproperlyConfigured

        with self.assertRaises(ImproperlyConfigured) as ctx:
            _reload_settings_with_env(
                {"DEBUG": "False", "ALLOWED_HOSTS": "example.com"}
            )

        self.assertIn("DJANGO_SECRET_KEY", str(ctx.exception))


class TestAllowedHostsSetting(unittest.TestCase):
    """Tests for ALLOWED_HOSTS setting."""

    def test_allowed_hosts_defaults_in_debug_mode(self) -> None:
        """ALLOWED_HOSTS should have localhost defaults in DEBUG mode."""
        settings = _reload_settings_with_env(
            {"DEBUG": "True", "DJANGO_SECRET_KEY": "test-key"}
        )
        self.assertIn("localhost", settings.ALLOWED_HOSTS)
        self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)

    def test_allowed_hosts_empty_in_production_by_default(self) -> None:
        """ALLOWED_HOSTS should be empty in production when not set."""
        settings = _reload_settings_with_env(
            {"DEBUG": "False", "DJANGO_SECRET_KEY": "test-key"}
        )
        self.assertEqual(settings.ALLOWED_HOSTS, [])

    def test_allowed_hosts_from_environment(self) -> None:
        """ALLOWED_HOSTS should be parsed from environment variable."""
        settings = _reload_settings_with_env(
            {
                "DEBUG": "False",
                "DJANGO_SECRET_KEY": "test-key",
                "ALLOWED_HOSTS": "example.com,api.example.com",
            }
        )
        self.assertEqual(
            settings.ALLOWED_HOSTS, ["example.com", "api.example.com"]
        )

    def test_allowed_hosts_strips_whitespace(self) -> None:
        """ALLOWED_HOSTS should strip whitespace from entries."""
        settings = _reload_settings_with_env(
            {
                "DEBUG": "False",
                "DJANGO_SECRET_KEY": "test-key",
                "ALLOWED_HOSTS": " example.com , api.example.com ",
            }
        )
        self.assertEqual(
            settings.ALLOWED_HOSTS, ["example.com", "api.example.com"]
        )

    def test_allowed_hosts_ignores_empty_entries(self) -> None:
        """ALLOWED_HOSTS should ignore empty entries from splitting."""
        settings = _reload_settings_with_env(
            {
                "DEBUG": "False",
                "DJANGO_SECRET_KEY": "test-key",
                "ALLOWED_HOSTS": "example.com,,api.example.com,",
            }
        )
        self.assertEqual(
            settings.ALLOWED_HOSTS, ["example.com", "api.example.com"]
        )

    def test_allowed_hosts_overrides_debug_defaults(self) -> None:
        """Explicit ALLOWED_HOSTS should override DEBUG mode defaults."""
        settings = _reload_settings_with_env(
            {
                "DEBUG": "True",
                "DJANGO_SECRET_KEY": "test-key",
                "ALLOWED_HOSTS": "custom.dev",
            }
        )
        self.assertEqual(settings.ALLOWED_HOSTS, ["custom.dev"])
