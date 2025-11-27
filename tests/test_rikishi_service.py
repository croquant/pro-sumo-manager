"""Tests for RikishiService business logic."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase

from game.constants import MAX_STAT_VALUE
from game.models import Rikishi, Shikona, Shusshin
from game.services import RikishiService


class RikishiServiceTests(TestCase):
    """Test suite for RikishiService."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a shikona for the test rikishi
        self.shikona = Shikona.objects.create(
            name="朝青龍",
            transliteration="Asashoryu",
            interpretation="Morning Blue Dragon",
        )

        # Get or create a shusshin
        self.shusshin, _ = Shusshin.objects.get_or_create(
            country_code="MN",
        )

        # Create a rikishi with stats
        self.rikishi = Rikishi.objects.create(
            shikona=self.shikona,
            shusshin=self.shusshin,
            potential=50,
            xp=0,
            strength=5,
            technique=5,
            balance=5,
            endurance=5,
            mental=5,
        )

    def test_increase_random_stats_basic(self) -> None:
        """Should increase stats by the specified amount."""
        initial_total = self.rikishi.current
        RikishiService.increase_random_stats(self.rikishi, amount=5)

        self.rikishi.refresh_from_db()
        self.assertEqual(self.rikishi.current, initial_total + 5)

    def test_increase_random_stats_respects_potential(self) -> None:
        """Should not exceed potential when increasing stats."""
        # Set stats close to potential
        self.rikishi.strength = 10
        self.rikishi.technique = 10
        self.rikishi.balance = 10
        self.rikishi.endurance = 10
        self.rikishi.mental = 9  # Total = 49, potential = 50
        self.rikishi.save()

        # Try to add 5 points, but only 1 should be added
        RikishiService.increase_random_stats(self.rikishi, amount=5)

        self.rikishi.refresh_from_db()
        self.assertEqual(self.rikishi.current, 50)  # Should be at potential

    def test_increase_random_stats_respects_max_stat_value(self) -> None:
        """Should not exceed MAX_STAT_VALUE for any individual stat."""
        # Set one stat to max
        self.rikishi.strength = MAX_STAT_VALUE
        self.rikishi.technique = 5
        self.rikishi.balance = 5
        self.rikishi.endurance = 5
        self.rikishi.mental = 5
        self.rikishi.potential = 100  # Max allowed by constraint
        self.rikishi.save()

        # Increase stats many times
        for _ in range(100):
            RikishiService.increase_random_stats(self.rikishi, amount=1)

        self.rikishi.refresh_from_db()
        # Strength should still be at max
        self.assertEqual(self.rikishi.strength, MAX_STAT_VALUE)
        # Other stats should have increased
        self.assertGreater(self.rikishi.technique, 5)

    def test_increase_random_stats_all_stats_maxed(self) -> None:
        """Should handle case where all stats are maxed out."""
        # Set all stats to max
        self.rikishi.strength = MAX_STAT_VALUE
        self.rikishi.technique = MAX_STAT_VALUE
        self.rikishi.balance = MAX_STAT_VALUE
        self.rikishi.endurance = MAX_STAT_VALUE
        self.rikishi.mental = MAX_STAT_VALUE
        self.rikishi.potential = 100  # Max allowed by constraint
        self.rikishi.save()

        initial_total = self.rikishi.current

        # Try to increase stats
        RikishiService.increase_random_stats(self.rikishi, amount=10)

        self.rikishi.refresh_from_db()
        # Stats should not have changed
        self.assertEqual(self.rikishi.current, initial_total)

    def test_increase_random_stats_zero_amount(self) -> None:
        """Should handle zero amount gracefully."""
        initial_total = self.rikishi.current
        RikishiService.increase_random_stats(self.rikishi, amount=0)

        self.rikishi.refresh_from_db()
        self.assertEqual(self.rikishi.current, initial_total)

    def test_increase_random_stats_saves_to_database(self) -> None:
        """Should persist changes to the database."""
        initial_total = self.rikishi.current
        RikishiService.increase_random_stats(self.rikishi, amount=3)

        # Fetch fresh from database
        fresh_rikishi = Rikishi.objects.get(pk=self.rikishi.pk)
        self.assertEqual(fresh_rikishi.current, initial_total + 3)

    def test_increase_random_stats_validates_before_saving(self) -> None:
        """Should validate stats don't exceed potential before saving."""
        # Manually set stats to exceed potential (bypassing normal validation)
        self.rikishi.strength = 20
        self.rikishi.technique = 20
        self.rikishi.balance = 20
        self.rikishi.endurance = 20
        self.rikishi.mental = 20
        # current = 100, but potential = 50

        # This should raise ValidationError when trying to save
        with self.assertRaises(ValidationError):
            RikishiService.increase_random_stats(self.rikishi, amount=0)

    def test_increase_random_stats_distributes_randomly(self) -> None:
        """Should distribute points across different stats (probabilistic)."""
        # Reset to base stats
        self.rikishi.strength = 1
        self.rikishi.technique = 1
        self.rikishi.balance = 1
        self.rikishi.endurance = 1
        self.rikishi.mental = 1
        self.rikishi.potential = 100
        self.rikishi.save()

        # Add many points
        RikishiService.increase_random_stats(self.rikishi, amount=20)

        self.rikishi.refresh_from_db()

        # At least 3 different stats should have increased
        # (with 20 points distributed randomly, very unlikely to hit 1-2)
        stats_increased = sum(
            [
                self.rikishi.strength > 1,
                self.rikishi.technique > 1,
                self.rikishi.balance > 1,
                self.rikishi.endurance > 1,
                self.rikishi.mental > 1,
            ]
        )
        self.assertGreaterEqual(stats_increased, 3)


class RikishiValidationTests(TestCase):
    """Test suite for Rikishi validation in service layer."""

    def test_validate_debut_before_intai_raises_error(self) -> None:
        """Should raise ValidationError if debut is after retirement."""
        from game.models import GameDate

        debut_date = GameDate.objects.create(year=10, month=5, day=15)
        intai_date = GameDate.objects.create(year=5, month=3, day=10)

        with self.assertRaises(ValidationError) as cm:
            RikishiService.validate_debut_intai_dates(debut_date, intai_date)

        self.assertIn("Debut date must be before", str(cm.exception))

    def test_validate_debut_equal_to_intai_allows(self) -> None:
        """Should allow debut and retirement on the same day."""
        from game.models import GameDate

        same_date = GameDate.objects.create(year=5, month=5, day=5)

        # Should not raise
        RikishiService.validate_debut_intai_dates(same_date, same_date)

    def test_validate_null_dates_allows(self) -> None:
        """Should allow null debut and intai dates."""
        # Should not raise
        RikishiService.validate_debut_intai_dates(None, None)

    def test_create_rikishi_with_valid_dates(self) -> None:
        """Should create rikishi when dates are valid."""
        from game.models import GameDate

        shikona = Shikona.objects.create(
            name="白鵬",
            transliteration="Hakuho",
            interpretation="White Phoenix",
        )

        debut_date = GameDate.objects.create(year=5, month=3, day=10)
        intai_date = GameDate.objects.create(year=10, month=5, day=15)

        rikishi = RikishiService.create_rikishi(
            shikona=shikona,
            debut=debut_date,
            intai=intai_date,
        )

        self.assertEqual(rikishi.shikona, shikona)
        self.assertEqual(rikishi.debut, debut_date)
        self.assertEqual(rikishi.intai, intai_date)

    def test_create_rikishi_with_invalid_dates_raises(self) -> None:
        """Should raise ValidationError when creating with invalid dates."""
        from game.models import GameDate

        shikona = Shikona.objects.create(
            name="日馬富士",
            transliteration="Harumafuji",
            interpretation="Spring Wealthy Warrior",
        )

        debut_date = GameDate.objects.create(year=10, month=5, day=15)
        intai_date = GameDate.objects.create(year=5, month=3, day=10)

        with self.assertRaises(ValidationError):
            RikishiService.create_rikishi(
                shikona=shikona,
                debut=debut_date,
                intai=intai_date,
            )

    def test_update_rikishi_validates_dates(self) -> None:
        """Should validate dates when updating rikishi."""
        from game.models import GameDate

        shikona = Shikona.objects.create(
            name="稀勢の里",
            transliteration="Kisenosato",
            interpretation="Rare Sato Hamlet",
        )

        rikishi = RikishiService.create_rikishi(shikona=shikona)

        debut_date = GameDate.objects.create(year=10, month=5, day=15)
        intai_date = GameDate.objects.create(year=5, month=3, day=10)

        with self.assertRaises(ValidationError):
            RikishiService.update_rikishi(
                rikishi,
                debut=debut_date,
                intai=intai_date,
            )

    def test_update_rikishi_with_valid_changes(self) -> None:
        """Should update rikishi when changes are valid."""
        from game.models import GameDate, Rank

        shikona1 = Shikona.objects.create(
            name="琴奨菊",
            transliteration="Kotoshogiku",
            interpretation="Koto Prize Chrysanthemum",
        )

        shikona2 = Shikona.objects.create(
            name="豊山",
            transliteration="Yutakayama",
            interpretation="Abundant Mountain",
        )

        shusshin, _ = Shusshin.objects.get_or_create(country_code="US")

        # Get a rank from existing data
        rank = Rank.objects.first()

        rikishi = RikishiService.create_rikishi(shikona=shikona1)

        debut_date = GameDate.objects.create(year=5, month=3, day=10)
        intai_date = GameDate.objects.create(year=10, month=6, day=20)

        # Update with all fields
        updated = RikishiService.update_rikishi(
            rikishi,
            shikona=shikona2,
            shusshin=shusshin,
            rank=rank,
            debut=debut_date,
            intai=intai_date,
        )

        self.assertEqual(updated.shikona, shikona2)
        self.assertEqual(updated.shusshin, shusshin)
        self.assertEqual(updated.rank, rank)
        self.assertEqual(updated.debut, debut_date)
        self.assertEqual(updated.intai, intai_date)

    def test_str_representation(self) -> None:
        """Should return the wrestler's ring name transliteration."""
        shikona = Shikona.objects.create(
            name="御嶽海",
            transliteration="Mitakeumi",
            interpretation="Mountain Peak Sea",
        )

        rikishi = RikishiService.create_rikishi(shikona=shikona)

        self.assertEqual(str(rikishi), "Mitakeumi")

    def test_validate_stats_within_potential_passes(self) -> None:
        """Should pass validation when stats are within potential."""
        shikona = Shikona.objects.create(
            name="鶴竜",
            transliteration="Kakuryu",
            interpretation="Crane Dragon",
        )

        rikishi = RikishiService.create_rikishi(
            shikona=shikona,
            potential=50,
            strength=8,
            technique=9,
            balance=7,
            endurance=6,
            mental=10,
        )

        # Should not raise
        RikishiService.validate_stats_within_potential(rikishi)

    def test_validate_stats_exceed_potential_raises(self) -> None:
        """Should raise ValidationError when stats exceed potential."""
        shikona = Shikona.objects.create(
            name="豪栄道",
            transliteration="Goeido",
            interpretation="Strong Glory Path",
        )

        # Create with valid stats first
        rikishi = RikishiService.create_rikishi(
            shikona=shikona,
            potential=10,
            strength=2,
            technique=2,
            balance=2,
            endurance=2,
            mental=2,
        )

        # Manually exceed potential (bypassing validation)
        rikishi.strength = 10
        rikishi.technique = 10
        rikishi.balance = 10
        rikishi.endurance = 10
        rikishi.mental = 10
        # current = 50, potential = 10

        with self.assertRaises(ValidationError) as cm:
            RikishiService.validate_stats_within_potential(rikishi)

        self.assertIn("cannot exceed potential", str(cm.exception))

    def test_create_rikishi_with_invalid_total_raises(self) -> None:
        """Should raise ValidationError when creating with invalid total."""
        shikona = Shikona.objects.create(
            name="照ノ富士",
            transliteration="Terunofuji",
            interpretation="Shining Fuji",
        )

        with self.assertRaises(ValidationError):
            RikishiService.create_rikishi(
                shikona=shikona,
                potential=10,
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                # Total = 25, potential = 10 -> should raise
            )
