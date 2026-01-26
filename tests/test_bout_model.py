"""Tests for the Bout model."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from game.models import (
    Banzuke,
    BanzukeEntry,
    Bout,
    Division,
    GameDate,
    Heya,
    Rank,
    Rikishi,
    Shikona,
    Shusshin,
)
from game.models.bout import VALID_KIMARITE


class BoutModelTestCase(TestCase):
    """Base test case with common setup for Bout tests."""

    def setUp(self) -> None:
        """Set up test data."""
        # Create dates
        self.start_date = GameDate.objects.create(year=2024, month=1, day=1)
        self.end_date = GameDate.objects.create(year=2024, month=1, day=15)

        # Create banzuke
        self.banzuke = Banzuke.objects.create(
            name="Hatsu Basho",
            location="Tokyo",
            year=2024,
            month=1,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        # Create division and ranks
        self.division = Division.objects.get(name="M")
        self.rank_east = Rank.objects.create(
            division=self.division, title="Y", level=1, order=1, direction="E"
        )
        self.rank_west = Rank.objects.create(
            division=self.division, title="Y", level=1, order=1, direction="W"
        )

        # Create heya
        heya_name = Shikona.objects.create(
            transliteration="Miyagino",
            name="宮城野",
            interpretation="Miyagino",
        )
        self.heya = Heya.objects.create(
            name=heya_name, created_at=self.start_date
        )

        # Create shusshin
        self.shusshin = Shusshin.objects.get(country_code="MN")

        # Create rikishi
        self.shikona_east = Shikona.objects.create(
            transliteration="Hakuho",
            name="白鵬",
            interpretation="White Phoenix",
        )
        self.east_rikishi = Rikishi.objects.create(
            shikona=self.shikona_east,
            heya=self.heya,
            shusshin=self.shusshin,
            potential=100,
            strength=15,
            technique=15,
            balance=15,
            endurance=15,
            mental=15,
        )

        self.shikona_west = Shikona.objects.create(
            transliteration="Terunofuji",
            name="照ノ富士",
            interpretation="Shining Fuji",
        )
        self.west_rikishi = Rikishi.objects.create(
            shikona=self.shikona_west,
            heya=self.heya,
            shusshin=self.shusshin,
            potential=100,
            strength=14,
            technique=14,
            balance=14,
            endurance=14,
            mental=14,
        )

        # Create banzuke entries
        self.east_entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.east_rikishi,
            rank=self.rank_east,
        )
        self.west_entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.west_rikishi,
            rank=self.rank_west,
        )


class TestBoutModel(BoutModelTestCase):
    """Tests for the Bout model."""

    def test_create_bout(self) -> None:
        """Should create a Bout with correct attributes."""
        bout = Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="A thrilling match!",
        )

        self.assertEqual(bout.day, 1)
        self.assertEqual(bout.winner, Bout.Winner.EAST)
        self.assertEqual(bout.kimarite, "yorikiri")
        self.assertEqual(bout.east_xp_gain, 10)
        self.assertEqual(bout.west_xp_gain, 5)
        self.assertEqual(bout.excitement_level, Decimal("7.5"))

    def test_str_representation(self) -> None:
        """Should return correct string representation."""
        bout = Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="A thrilling match!",
        )

        expected = (
            f"{self.banzuke} Day 1: {self.east_rikishi} vs {self.west_rikishi}"
        )
        self.assertEqual(str(bout), expected)

    def test_winner_rikishi_property_east(self) -> None:
        """Should return east rikishi when east wins."""
        bout = Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="A thrilling match!",
        )

        self.assertEqual(bout.winner_rikishi, self.east_rikishi)
        self.assertEqual(bout.loser_rikishi, self.west_rikishi)

    def test_winner_rikishi_property_west(self) -> None:
        """Should return west rikishi when west wins."""
        bout = Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.WEST,
            kimarite="oshidashi",
            east_xp_gain=5,
            west_xp_gain=10,
            excitement_level=Decimal("8.0"),
            commentary="A great match!",
        )

        self.assertEqual(bout.winner_rikishi, self.west_rikishi)
        self.assertEqual(bout.loser_rikishi, self.east_rikishi)


class TestBoutConstraints(BoutModelTestCase):
    """Tests for Bout model constraints."""

    def test_unique_bout_per_tournament(self) -> None:
        """Should prevent same wrestlers fighting twice in same tournament."""
        Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="First match",
        )

        # Try to create another bout with same wrestlers
        with self.assertRaises(IntegrityError):
            Bout.objects.create(
                banzuke=self.banzuke,
                day=5,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.west_rikishi,
                winner=Bout.Winner.WEST,
                kimarite="oshidashi",
                east_xp_gain=5,
                west_xp_gain=10,
                excitement_level=Decimal("6.0"),
                commentary="Second match",
            )

    def test_day_must_be_at_least_1(self) -> None:
        """Should prevent day less than 1."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Bout.objects.create(
                banzuke=self.banzuke,
                day=0,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.west_rikishi,
                winner=Bout.Winner.EAST,
                kimarite="yorikiri",
                east_xp_gain=10,
                west_xp_gain=5,
                excitement_level=Decimal("7.5"),
                commentary="Invalid day",
            )

    def test_day_must_be_at_most_15(self) -> None:
        """Should prevent day greater than 15."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Bout.objects.create(
                banzuke=self.banzuke,
                day=16,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.west_rikishi,
                winner=Bout.Winner.EAST,
                kimarite="yorikiri",
                east_xp_gain=10,
                west_xp_gain=5,
                excitement_level=Decimal("7.5"),
                commentary="Invalid day",
            )

    def test_excitement_level_minimum(self) -> None:
        """Should prevent excitement level less than 1.0."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Bout.objects.create(
                banzuke=self.banzuke,
                day=1,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.west_rikishi,
                winner=Bout.Winner.EAST,
                kimarite="yorikiri",
                east_xp_gain=10,
                west_xp_gain=5,
                excitement_level=Decimal("0.5"),
                commentary="Too boring",
            )

    def test_excitement_level_maximum(self) -> None:
        """Should prevent excitement level greater than 10.0."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Bout.objects.create(
                banzuke=self.banzuke,
                day=1,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.west_rikishi,
                winner=Bout.Winner.EAST,
                kimarite="yorikiri",
                east_xp_gain=10,
                west_xp_gain=5,
                excitement_level=Decimal("10.5"),
                commentary="Too exciting",
            )


class TestBoutValidation(BoutModelTestCase):
    """Tests for Bout model clean() validation."""

    def test_wrestler_cannot_fight_themselves(self) -> None:
        """Should raise ValidationError if wrestler fights themselves."""
        bout = Bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.east_rikishi,  # Same wrestler!
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="Self match",
        )

        with self.assertRaises(ValidationError) as ctx:
            bout.full_clean()
        self.assertIn("west_rikishi", ctx.exception.message_dict)

    def test_invalid_kimarite_rejected(self) -> None:
        """Should raise ValidationError for invalid kimarite."""
        bout = Bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="invalid_technique",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="Invalid technique",
        )

        with self.assertRaises(ValidationError) as ctx:
            bout.full_clean()
        self.assertIn("kimarite", ctx.exception.message_dict)

    def test_all_valid_kimarite_accepted(self) -> None:
        """Should accept all valid kimarite values."""
        for i, kimarite in enumerate(VALID_KIMARITE):
            # Create new rikishi for each test to avoid unique constraint
            shikona = Shikona.objects.create(
                transliteration=f"TestRikishi{i}",
                name=f"テスト{i}",
                interpretation=f"Test {i}",
            )
            rikishi = Rikishi.objects.create(
                shikona=shikona,
                heya=self.heya,
                potential=50,
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
            )

            bout = Bout(
                banzuke=self.banzuke,
                day=i + 1 if i < 15 else 1,
                east_rikishi=self.east_rikishi if i % 2 == 0 else rikishi,
                west_rikishi=rikishi if i % 2 == 0 else self.east_rikishi,
                winner=Bout.Winner.EAST,
                kimarite=kimarite,
                east_xp_gain=10,
                west_xp_gain=5,
                excitement_level=Decimal("7.5"),
                commentary=f"Match with {kimarite}",
            )
            # Should not raise
            bout.full_clean()


class TestBoutDifferentTournaments(BoutModelTestCase):
    """Tests for bouts in different tournaments."""

    def test_same_wrestlers_can_fight_in_different_tournaments(self) -> None:
        """Should allow same wrestlers to fight in different tournaments."""
        # Create bout in first tournament
        Bout.objects.create(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.EAST,
            kimarite="yorikiri",
            east_xp_gain=10,
            west_xp_gain=5,
            excitement_level=Decimal("7.5"),
            commentary="First tournament",
        )

        # Create second tournament
        start2 = GameDate.objects.create(year=2024, month=3, day=1)
        end2 = GameDate.objects.create(year=2024, month=3, day=15)
        banzuke2 = Banzuke.objects.create(
            name="Haru Basho",
            location="Osaka",
            year=2024,
            month=3,
            start_date=start2,
            end_date=end2,
        )

        # Should succeed - different tournament
        bout2 = Bout.objects.create(
            banzuke=banzuke2,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            winner=Bout.Winner.WEST,
            kimarite="oshidashi",
            east_xp_gain=5,
            west_xp_gain=10,
            excitement_level=Decimal("8.0"),
            commentary="Second tournament",
        )

        self.assertEqual(bout2.banzuke, banzuke2)
