"""Tests for TrainingService business logic."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase

from game.models import Rikishi, Shikona, TrainingSession
from game.services import TrainingService
from libs.constants import MAX_STAT_VALUE


class TrainingServiceTests(TestCase):
    """Test suite for TrainingService."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.shikona = Shikona.objects.create(
            name="テスト",
            transliteration="Tesuto",
            interpretation="Test wrestler",
        )
        self.rikishi = Rikishi.objects.create(
            shikona=self.shikona,
            potential=50,
            xp=500,
            strength=5,
            technique=3,
            balance=2,
            endurance=1,
            mental=1,
        )


class CalculateXpCostTests(TrainingServiceTests):
    """Tests for TrainingService.calculate_xp_cost."""

    def test_cost_at_level_1(self) -> None:
        """XP cost at level 1 should be 10."""
        self.assertEqual(TrainingService.calculate_xp_cost(1), 10)

    def test_cost_at_level_5(self) -> None:
        """XP cost at level 5 should be 50."""
        self.assertEqual(TrainingService.calculate_xp_cost(5), 50)

    def test_cost_at_level_10(self) -> None:
        """XP cost at level 10 should be 100."""
        self.assertEqual(TrainingService.calculate_xp_cost(10), 100)

    def test_cost_at_level_20(self) -> None:
        """XP cost at level 20 should be 200."""
        self.assertEqual(TrainingService.calculate_xp_cost(20), 200)


class ValidateCanTrainTests(TrainingServiceTests):
    """Tests for TrainingService.validate_can_train."""

    def test_valid_training(self) -> None:
        """Should not raise when training is valid."""
        TrainingService.validate_can_train(self.rikishi, "strength")

    def test_invalid_stat_name(self) -> None:
        """Should raise ValidationError for invalid stat name."""
        with self.assertRaises(ValidationError) as ctx:
            TrainingService.validate_can_train(self.rikishi, "invalid_stat")
        self.assertIn("Invalid stat", str(ctx.exception))

    def test_stat_at_max(self) -> None:
        """Should raise ValidationError when stat is at MAX_STAT_VALUE."""
        self.rikishi.strength = MAX_STAT_VALUE
        self.rikishi.potential = 100
        self.rikishi.save()

        with self.assertRaises(ValidationError) as ctx:
            TrainingService.validate_can_train(self.rikishi, "strength")
        self.assertIn("already at maximum", str(ctx.exception))

    def test_at_potential_limit(self) -> None:
        """Should raise ValidationError when at potential limit."""
        self.rikishi.potential = 12  # 5+3+2+1+1 = 12
        self.rikishi.save()

        with self.assertRaises(ValidationError) as ctx:
            TrainingService.validate_can_train(self.rikishi, "strength")
        self.assertIn("reached their potential", str(ctx.exception))

    def test_insufficient_xp(self) -> None:
        """Should raise ValidationError when not enough XP."""
        self.rikishi.xp = 10  # Cost for strength (level 5) is 50
        self.rikishi.save()

        with self.assertRaises(ValidationError) as ctx:
            TrainingService.validate_can_train(self.rikishi, "strength")
        self.assertIn("Insufficient XP", str(ctx.exception))


class TrainStatTests(TrainingServiceTests):
    """Tests for TrainingService.train_stat."""

    def test_train_stat_success(self) -> None:
        """Should successfully train a stat."""
        initial_xp = self.rikishi.xp
        initial_strength = self.rikishi.strength
        expected_cost = TrainingService.calculate_xp_cost(initial_strength)

        session = TrainingService.train_stat(self.rikishi, "strength")

        self.rikishi.refresh_from_db()

        self.assertEqual(self.rikishi.strength, initial_strength + 1)
        self.assertEqual(self.rikishi.xp, initial_xp - expected_cost)

        self.assertEqual(session.rikishi, self.rikishi)
        self.assertEqual(session.stat, "strength")
        self.assertEqual(session.xp_cost, expected_cost)
        self.assertEqual(session.stat_before, initial_strength)
        self.assertEqual(session.stat_after, initial_strength + 1)

    def test_train_different_stats(self) -> None:
        """Should be able to train different stats."""
        stats = ["strength", "technique", "balance", "endurance", "mental"]

        for stat in stats:
            initial_value = getattr(self.rikishi, stat)
            TrainingService.train_stat(self.rikishi, stat)
            self.rikishi.refresh_from_db()
            self.assertEqual(getattr(self.rikishi, stat), initial_value + 1)

    def test_train_creates_session_record(self) -> None:
        """Training should create a TrainingSession record."""
        initial_count = TrainingSession.objects.count()

        TrainingService.train_stat(self.rikishi, "technique")

        self.assertEqual(TrainingSession.objects.count(), initial_count + 1)

    def test_train_invalid_stat_raises(self) -> None:
        """Should raise ValidationError for invalid stat."""
        with self.assertRaises(ValidationError) as ctx:
            TrainingService.train_stat(self.rikishi, "charisma")
        self.assertIn("Invalid stat", str(ctx.exception))

    def test_train_insufficient_xp_raises(self) -> None:
        """Should raise ValidationError when XP is insufficient."""
        self.rikishi.xp = 0
        self.rikishi.save()

        with self.assertRaises(ValidationError) as ctx:
            TrainingService.train_stat(self.rikishi, "mental")
        self.assertIn("Insufficient XP", str(ctx.exception))

    def test_train_at_potential_raises(self) -> None:
        """Should raise ValidationError when at potential."""
        self.rikishi.potential = self.rikishi.current
        self.rikishi.save()

        with self.assertRaises(ValidationError) as ctx:
            TrainingService.train_stat(self.rikishi, "mental")
        self.assertIn("reached their potential", str(ctx.exception))

    def test_train_at_max_stat_raises(self) -> None:
        """Should raise ValidationError when stat is at max."""
        self.rikishi.mental = MAX_STAT_VALUE
        self.rikishi.potential = 100
        self.rikishi.save()

        with self.assertRaises(ValidationError) as ctx:
            TrainingService.train_stat(self.rikishi, "mental")
        self.assertIn("already at maximum", str(ctx.exception))

    def test_multiple_training_sessions(self) -> None:
        """Should be able to train multiple times."""
        initial_strength = self.rikishi.strength

        TrainingService.train_stat(self.rikishi, "strength")
        TrainingService.train_stat(self.rikishi, "strength")
        TrainingService.train_stat(self.rikishi, "strength")

        self.rikishi.refresh_from_db()
        self.assertEqual(self.rikishi.strength, initial_strength + 3)

        sessions = TrainingSession.objects.filter(
            rikishi=self.rikishi, stat="strength"
        )
        self.assertEqual(sessions.count(), 3)


class TrainingSessionModelTests(TrainingServiceTests):
    """Tests for TrainingSession model."""

    def test_str_representation(self) -> None:
        """Test string representation of TrainingSession."""
        session = TrainingService.train_stat(self.rikishi, "strength")
        expected = f"{self.rikishi} trained Strength (5 -> 6)"
        self.assertEqual(str(session), expected)

    def test_ordering(self) -> None:
        """Sessions should be ordered by created_at descending."""
        TrainingService.train_stat(self.rikishi, "strength")
        TrainingService.train_stat(self.rikishi, "technique")
        TrainingService.train_stat(self.rikishi, "balance")

        sessions = list(TrainingSession.objects.all())
        self.assertEqual(sessions[0].stat, "balance")
        self.assertEqual(sessions[1].stat, "technique")
        self.assertEqual(sessions[2].stat, "strength")
