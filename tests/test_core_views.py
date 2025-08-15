"""Tests for the core views module."""

from __future__ import annotations

import importlib
import unittest


class CoreViewsImportTests(unittest.TestCase):
    """Ensure the core views module is importable."""

    def test_import(self) -> None:
        """Should import without side effects."""
        module = importlib.import_module("core.views")
        self.assertIsNotNone(module)
