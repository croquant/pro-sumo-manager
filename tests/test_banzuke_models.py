"""Tests for Banzuke and BanzukeEntry models."""

from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from game.models import (
    Banzuke,
    BanzukeEntry,
    Division,
    GameDate,
    Heya,
    Rank,
    Rikishi,
    Shikona,
    Shusshin,
)


class TestBanzukeModel(TestCase):
    """Tests for the Banzuke model."""

    def test_create_banzuke(self) -> None:
        """Should create a Banzuke with correct attributes."""
        start = GameDate.objects.create(year=2024, month=1, day=1)
        end = GameDate.objects.create(year=2024, month=1, day=15)
        banzuke = Banzuke.objects.create(
            name="Hatsu Basho",
            location="Tokyo",
            year=2024,
            month=1,
            start_date=start,
            end_date=end,
        )
        self.assertEqual(banzuke.name, "Hatsu Basho")
        self.assertEqual(banzuke.status, Banzuke.Status.SCHEDULED)
        self.assertEqual(str(banzuke), "2024 Hatsu Basho")

    def test_unique_banzuke_season(self) -> None:
        """Should prevent creating two Banzuke in the same season."""
        start = GameDate.objects.create(year=2024, month=1, day=1)
        end = GameDate.objects.create(year=2024, month=1, day=15)
        Banzuke.objects.create(
            name="Hatsu Basho",
            location="Tokyo",
            year=2024,
            month=1,
            start_date=start,
            end_date=end,
        )

        with self.assertRaises(IntegrityError):
            Banzuke.objects.create(
                name="Another Basho",
                location="Osaka",
                year=2024,
                month=1,
                start_date=start,
                end_date=end,
            )


class TestBanzukeEntryModel(TestCase):
    """Tests for the BanzukeEntry model."""

    def setUp(self) -> None:
        """Set up test data."""
        start = GameDate.objects.create(year=2024, month=1, day=1)
        end = GameDate.objects.create(year=2024, month=1, day=15)
        self.banzuke = Banzuke.objects.create(
            name="Hatsu Basho",
            location="Tokyo",
            year=2024,
            month=1,
            start_date=start,
            end_date=end,
        )

        division = Division.objects.get(name="M")
        self.rank = Rank.objects.create(division=division, title="Y", level=1)

        self.shikona = Shikona.objects.create(
            transliteration="Hakuho",
            name="白鵬",
            interpretation="White Phoenix",
        )
        shusshin = Shusshin.objects.get(country_code="MN")
        heya_name = Shikona.objects.create(
            transliteration="Miyagino", name="宮城野", interpretation="Miyagino"
        )
        self.heya = Heya.objects.create(name=heya_name, created_at=start)

        self.rikishi = Rikishi.objects.create(
            shikona=self.shikona,
            heya=self.heya,
            shusshin=shusshin,
            potential=100,
            strength=10,
            technique=10,
            balance=10,
            endurance=10,
            mental=10,
        )

    def test_create_banzuke_entry(self) -> None:
        """Should create a BanzukeEntry with correct attributes."""
        entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
        )

        self.assertEqual(entry.wins, 0)
        self.assertEqual(entry.losses, 0)
        self.assertEqual(
            str(entry), f"{self.banzuke} - {self.rikishi} ({self.rank})"
        )

    def test_unique_rikishi_per_banzuke(self) -> None:
        """Should prevent adding the same Rikishi twice to a Banzuke."""
        BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
        )

        # Try to add same rikishi again (even with different rank)
        rank2 = Rank.objects.create(
            division=self.rank.division, title="O", level=2
        )

        with self.assertRaises(IntegrityError):
            BanzukeEntry.objects.create(
                banzuke=self.banzuke,
                rikishi=self.rikishi,
                rank=rank2,
            )

    def test_unique_rank_per_banzuke(self) -> None:
        """Prevent assigning the same Rank to two Rikishi in a Banzuke."""
        BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
        )

        # Create another rikishi
        shikona2 = Shikona.objects.create(
            transliteration="Terunofuji",
            name="照ノ富士",
            interpretation="Shining Fuji",
        )
        rikishi2 = Rikishi.objects.create(
            shikona=shikona2,
            heya=self.heya,
            shusshin=self.rikishi.shusshin,
            potential=100,
            strength=10,
            technique=10,
            balance=10,
            endurance=10,
            mental=10,
        )

        # Try to assign same rank to different rikishi in same banzuke
        with self.assertRaises(IntegrityError):
            BanzukeEntry.objects.create(
                banzuke=self.banzuke,
                rikishi=rikishi2,
                rank=self.rank,
            )

    def test_wins_cannot_exceed_15(self) -> None:
        """Should prevent wins from exceeding 15."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            BanzukeEntry.objects.create(
                banzuke=self.banzuke,
                rikishi=self.rikishi,
                rank=self.rank,
                wins=16,
            )

    def test_losses_cannot_exceed_15(self) -> None:
        """Should prevent losses from exceeding 15."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            BanzukeEntry.objects.create(
                banzuke=self.banzuke,
                rikishi=self.rikishi,
                rank=self.rank,
                losses=16,
            )

    def test_absences_cannot_exceed_15(self) -> None:
        """Should prevent absences from exceeding 15."""
        with transaction.atomic(), self.assertRaises(IntegrityError):
            BanzukeEntry.objects.create(
                banzuke=self.banzuke,
                rikishi=self.rikishi,
                rank=self.rank,
                absences=16,
            )

    def test_total_matches_property(self) -> None:
        """Should calculate total matches correctly."""
        entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
            wins=8,
            losses=5,
            absences=2,
        )
        self.assertEqual(entry.total_matches, 15)

    def test_record_property_without_absences(self) -> None:
        """Should format record as 'W-L' when no absences."""
        entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
            wins=8,
            losses=7,
        )
        self.assertEqual(entry.record, "8-7")

    def test_record_property_with_absences(self) -> None:
        """Should format record as 'W-L-A' when there are absences."""
        entry = BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=self.rikishi,
            rank=self.rank,
            wins=8,
            losses=5,
            absences=2,
        )
        self.assertEqual(entry.record, "8-5-2")


class TestBanzukeConstraints(TestCase):
    """Tests for Banzuke validation constraints."""

    def test_invalid_month_zero(self) -> None:
        """Should prevent month of 0."""
        start = GameDate.objects.create(year=2024, month=1, day=1)
        end = GameDate.objects.create(year=2024, month=1, day=15)
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Banzuke.objects.create(
                name="Invalid Basho",
                location="Tokyo",
                year=2024,
                month=0,
                start_date=start,
                end_date=end,
            )

    def test_invalid_month_thirteen(self) -> None:
        """Should prevent month greater than 12."""
        start = GameDate.objects.create(year=2024, month=1, day=1)
        end = GameDate.objects.create(year=2024, month=1, day=15)
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Banzuke.objects.create(
                name="Invalid Basho",
                location="Tokyo",
                year=2024,
                month=13,
                start_date=start,
                end_date=end,
            )
