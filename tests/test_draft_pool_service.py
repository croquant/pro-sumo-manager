"""Tests for DraftPoolService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import TestCase

from game.models import Shikona as ShikonaModel
from game.services.draft_pool_service import DraftPoolService
from libs.types.shikona import Shikona as ShikonaType


class DraftPoolServicePoolTests(TestCase):
    """Tests for DraftPoolService pool shikona integration."""

    def _make_pool_shikona(
        self,
        name: str = "山嵐",
        transliteration: str = "Yamaarashi",
        interpretation: str = "Mountain Storm",
    ) -> ShikonaModel:
        """Create an available pool shikona model instance."""
        return ShikonaModel.objects.create(
            name=name,
            transliteration=transliteration,
            interpretation=interpretation,
            is_available=True,
        )

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_uses_pool_shikona(self, mock_generator_class: MagicMock) -> None:
        """Pool shikona are consumed and passed to the generator."""
        pool_shikona = self._make_pool_shikona()

        # Set up mock generator instance
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        # Build a fake rikishi return value
        fake_shikona = ShikonaType(
            shikona=pool_shikona.name,
            transliteration=pool_shikona.transliteration,
            interpretation=pool_shikona.interpretation,
        )
        fake_rikishi = MagicMock()
        fake_rikishi.shikona = fake_shikona
        fake_rikishi.shusshin.country_code = "JP"
        fake_rikishi.shusshin.jp_prefecture = "JP-13"
        fake_rikishi.shusshin.__str__ = lambda self: "Tokyo, Japan"
        fake_rikishi.potential = 30
        fake_rikishi.strength = 5
        fake_rikishi.technique = 5
        fake_rikishi.balance = 5
        fake_rikishi.endurance = 5
        fake_rikishi.mental = 5
        mock_generator.get.return_value = fake_rikishi

        DraftPoolService.generate_draft_pool(count=1)

        # Verify generator was called with a ShikonaType
        mock_generator.get.assert_called_once()
        call_kwargs = mock_generator.get.call_args
        passed_shikona = (
            call_kwargs.kwargs.get("shikona") or call_kwargs.args[0]
        )
        self.assertIsInstance(passed_shikona, ShikonaType)
        self.assertEqual(passed_shikona.shikona, pool_shikona.name)
        self.assertEqual(
            passed_shikona.transliteration, pool_shikona.transliteration
        )

        # Verify pool shikona was consumed (is_available=False)
        pool_shikona.refresh_from_db()
        self.assertFalse(pool_shikona.is_available)

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_falls_back_when_pool_empty(
        self, mock_generator_class: MagicMock
    ) -> None:
        """When pool is empty, generator is called without shikona arg."""
        # No pool shikona created — pool is empty

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        fake_shikona = ShikonaType(
            shikona="無名",
            transliteration="Mumei",
            interpretation="Nameless",
        )
        fake_rikishi = MagicMock()
        fake_rikishi.shikona = fake_shikona
        fake_rikishi.shusshin.country_code = "MN"
        fake_rikishi.shusshin.jp_prefecture = ""
        fake_rikishi.shusshin.__str__ = lambda self: "Mongolia"
        fake_rikishi.potential = 25
        fake_rikishi.strength = 5
        fake_rikishi.technique = 5
        fake_rikishi.balance = 5
        fake_rikishi.endurance = 5
        fake_rikishi.mental = 5
        mock_generator.get.return_value = fake_rikishi

        DraftPoolService.generate_draft_pool(count=1)

        mock_generator.get.assert_called_once()
        call_kwargs = mock_generator.get.call_args
        # shikona should be None when pool is empty
        passed_shikona = call_kwargs.kwargs.get("shikona", "SENTINEL")
        if passed_shikona == "SENTINEL":
            # Called positionally — should be None or not present
            if call_kwargs.args:
                self.assertIsNone(call_kwargs.args[0])
        else:
            self.assertIsNone(passed_shikona)
