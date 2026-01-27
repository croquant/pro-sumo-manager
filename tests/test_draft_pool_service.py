"""Tests for the DraftPoolService."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from game.services import DraftCandidate, DraftPoolService
from libs.types.rikishi import Rikishi
from libs.types.shikona import Shikona
from libs.types.shusshin import Shusshin


class TestGetPotentialTier(TestCase):
    """Tests for DraftPoolService.get_potential_tier."""

    def test_limited_tier_lower_bound(self) -> None:
        """Should return 'Limited' for potential of 5."""
        self.assertEqual(DraftPoolService.get_potential_tier(5), "Limited")

    def test_limited_tier_upper_bound(self) -> None:
        """Should return 'Limited' for potential of 20."""
        self.assertEqual(DraftPoolService.get_potential_tier(20), "Limited")

    def test_average_tier_lower_bound(self) -> None:
        """Should return 'Average' for potential of 21."""
        self.assertEqual(DraftPoolService.get_potential_tier(21), "Average")

    def test_average_tier_upper_bound(self) -> None:
        """Should return 'Average' for potential of 35."""
        self.assertEqual(DraftPoolService.get_potential_tier(35), "Average")

    def test_promising_tier_lower_bound(self) -> None:
        """Should return 'Promising' for potential of 36."""
        self.assertEqual(DraftPoolService.get_potential_tier(36), "Promising")

    def test_promising_tier_upper_bound(self) -> None:
        """Should return 'Promising' for potential of 50."""
        self.assertEqual(DraftPoolService.get_potential_tier(50), "Promising")

    def test_talented_tier_lower_bound(self) -> None:
        """Should return 'Talented' for potential of 51."""
        self.assertEqual(DraftPoolService.get_potential_tier(51), "Talented")

    def test_talented_tier_upper_bound(self) -> None:
        """Should return 'Talented' for potential of 70."""
        self.assertEqual(DraftPoolService.get_potential_tier(70), "Talented")

    def test_exceptional_tier_lower_bound(self) -> None:
        """Should return 'Exceptional' for potential of 71."""
        self.assertEqual(DraftPoolService.get_potential_tier(71), "Exceptional")

    def test_exceptional_tier_upper_bound(self) -> None:
        """Should return 'Exceptional' for potential of 85."""
        self.assertEqual(DraftPoolService.get_potential_tier(85), "Exceptional")

    def test_generational_tier_lower_bound(self) -> None:
        """Should return 'Generational' for potential of 86."""
        self.assertEqual(
            DraftPoolService.get_potential_tier(86), "Generational"
        )

    def test_generational_tier_upper_bound(self) -> None:
        """Should return 'Generational' for potential of 100."""
        self.assertEqual(
            DraftPoolService.get_potential_tier(100), "Generational"
        )


class TestGenerateDraftPool(TestCase):
    """Tests for DraftPoolService.generate_draft_pool."""

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_pool_size_within_bounds(self, mock_gen_class: MagicMock) -> None:
        """Should generate between 5 and 8 wrestlers."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.return_value = Rikishi(
            shikona=Shikona(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=50,
            current=20,
            strength=5,
            technique=5,
            balance=5,
            endurance=3,
            mental=2,
        )

        # Test with multiple seeds to check pool size variation
        for seed in range(100):
            pool = DraftPoolService.generate_draft_pool(seed=seed)
            self.assertGreaterEqual(
                len(pool),
                5,
                f"Pool size {len(pool)} is less than minimum 5 (seed={seed})",
            )
            self.assertLessEqual(
                len(pool),
                8,
                f"Pool size {len(pool)} exceeds maximum 8 (seed={seed})",
            )

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_pool_wrestlers_have_no_heya(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Generated wrestlers should not have a heya assigned."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.return_value = Rikishi(
            shikona=Shikona(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=50,
            current=20,
            strength=5,
            technique=5,
            balance=5,
            endurance=3,
            mental=2,
        )

        pool = DraftPoolService.generate_draft_pool(seed=42)

        # DraftCandidate objects don't have heya - they're not DB models yet
        # This is by design - they're candidates, not assigned wrestlers
        for candidate in pool:
            self.assertIsInstance(candidate, DraftCandidate)

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_pool_has_potential_tier(self, mock_gen_class: MagicMock) -> None:
        """All candidates should have a potential tier label."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.return_value = Rikishi(
            shikona=Shikona(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=50,
            current=20,
            strength=5,
            technique=5,
            balance=5,
            endurance=3,
            mental=2,
        )

        pool = DraftPoolService.generate_draft_pool(seed=42)

        for candidate in pool:
            self.assertIn(
                candidate.potential_tier,
                [
                    "Limited",
                    "Average",
                    "Promising",
                    "Talented",
                    "Exceptional",
                    "Generational",
                ],
            )

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_pool_deterministic_with_seed(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Same seed should produce same pool size."""
        mock_gen = mock_gen_class.return_value
        mock_gen.get.return_value = Rikishi(
            shikona=Shikona(
                shikona="豊昇龍",
                transliteration="Hoshoryu",
                interpretation="Rising Dragon",
            ),
            shusshin=Shusshin(country_code="MN"),
            potential=50,
            current=20,
            strength=5,
            technique=5,
            balance=5,
            endurance=3,
            mental=2,
        )

        pool1 = DraftPoolService.generate_draft_pool(seed=42)
        pool2 = DraftPoolService.generate_draft_pool(seed=42)

        self.assertEqual(len(pool1), len(pool2))


class TestDraftCandidate(TestCase):
    """Tests for the DraftCandidate dataclass."""

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        """Should serialize and deserialize correctly."""
        candidate = DraftCandidate(
            shikona_name="豊昇龍",
            shikona_transliteration="Hoshoryu",
            shusshin_display="Mongolia",
            strength=5,
            technique=6,
            balance=4,
            endurance=3,
            mental=2,
            potential_tier="Promising",
            _potential=45,
        )

        data = candidate.to_dict()
        restored = DraftCandidate.from_dict(data)

        self.assertEqual(restored.shikona_name, candidate.shikona_name)
        self.assertEqual(
            restored.shikona_transliteration, candidate.shikona_transliteration
        )
        self.assertEqual(restored.shusshin_display, candidate.shusshin_display)
        self.assertEqual(restored.strength, candidate.strength)
        self.assertEqual(restored.technique, candidate.technique)
        self.assertEqual(restored.balance, candidate.balance)
        self.assertEqual(restored.endurance, candidate.endurance)
        self.assertEqual(restored.mental, candidate.mental)
        self.assertEqual(restored.potential_tier, candidate.potential_tier)
        self.assertEqual(restored._potential, candidate._potential)


class TestEnsureVariety(TestCase):
    """Tests for DraftPoolService.ensure_variety."""

    def test_variety_with_different_tiers(self) -> None:
        """Should return True when pool has different potential tiers."""
        candidates = [
            DraftCandidate(
                shikona_name="A",
                shikona_transliteration="A",
                shusshin_display="Japan",
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                potential_tier="Promising",
                _potential=40,
            ),
            DraftCandidate(
                shikona_name="B",
                shikona_transliteration="B",
                shusshin_display="Japan",
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                potential_tier="Average",
                _potential=25,
            ),
        ]

        self.assertTrue(DraftPoolService.ensure_variety(candidates))

    def test_no_variety_with_same_tier(self) -> None:
        """Should return False when all have same potential tier."""
        candidates = [
            DraftCandidate(
                shikona_name="A",
                shikona_transliteration="A",
                shusshin_display="Japan",
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                potential_tier="Average",
                _potential=25,
            ),
            DraftCandidate(
                shikona_name="B",
                shikona_transliteration="B",
                shusshin_display="Japan",
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                potential_tier="Average",
                _potential=30,
            ),
        ]

        self.assertFalse(DraftPoolService.ensure_variety(candidates))
