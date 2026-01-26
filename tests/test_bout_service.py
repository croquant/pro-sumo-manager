"""Tests for the BoutService."""

from decimal import Decimal
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
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
from game.services import BoutService


class BoutServiceTestCase(TestCase):
    """Base test case with common setup for BoutService tests."""

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
            xp=0,
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
            xp=0,
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

    def _create_mock_bout_result(
        self,
        winner: str = "east",
        kimarite: str = "yorikiri",
        east_xp: int = 10,
        west_xp: int = 5,
        excitement: float = 7.5,
    ) -> MagicMock:
        """Create a mock BoutOutput object."""
        mock = MagicMock()
        mock.winner = winner
        mock.kimarite = kimarite
        mock.east_xp_gain = east_xp
        mock.west_xp_gain = west_xp
        mock.excitement_level = excitement
        mock.commentary = ["Line 1", "Line 2", "Line 3"]
        return mock


class TestRecordBout(BoutServiceTestCase):
    """Tests for BoutService.record_bout()."""

    def test_record_bout_creates_bout_record(self) -> None:
        """Should create a Bout record with correct data."""
        bout_result = self._create_mock_bout_result()

        bout = BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        self.assertIsInstance(bout, Bout)
        self.assertEqual(bout.banzuke, self.banzuke)
        self.assertEqual(bout.day, 1)
        self.assertEqual(bout.east_rikishi, self.east_rikishi)
        self.assertEqual(bout.west_rikishi, self.west_rikishi)
        self.assertEqual(bout.winner, "east")
        self.assertEqual(bout.kimarite, "yorikiri")
        self.assertEqual(bout.east_xp_gain, 10)
        self.assertEqual(bout.west_xp_gain, 5)
        self.assertEqual(bout.excitement_level, Decimal("7.5"))
        self.assertEqual(bout.commentary, "Line 1\nLine 2\nLine 3")

    def test_record_bout_updates_winner_wins(self) -> None:
        """Should increment winner's wins in BanzukeEntry."""
        bout_result = self._create_mock_bout_result(winner="east")

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        self.east_entry.refresh_from_db()
        self.assertEqual(self.east_entry.wins, 1)
        self.assertEqual(self.east_entry.losses, 0)

    def test_record_bout_updates_loser_losses(self) -> None:
        """Should increment loser's losses in BanzukeEntry."""
        bout_result = self._create_mock_bout_result(winner="east")

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        self.west_entry.refresh_from_db()
        self.assertEqual(self.west_entry.wins, 0)
        self.assertEqual(self.west_entry.losses, 1)

    def test_record_bout_west_winner(self) -> None:
        """Should correctly update records when west wins."""
        bout_result = self._create_mock_bout_result(winner="west")

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        self.east_entry.refresh_from_db()
        self.west_entry.refresh_from_db()

        self.assertEqual(self.east_entry.wins, 0)
        self.assertEqual(self.east_entry.losses, 1)
        self.assertEqual(self.west_entry.wins, 1)
        self.assertEqual(self.west_entry.losses, 0)

    def test_record_bout_awards_xp_to_east(self) -> None:
        """Should award XP to east rikishi."""
        bout_result = self._create_mock_bout_result(east_xp=15)

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        self.east_rikishi.refresh_from_db()
        self.assertEqual(self.east_rikishi.xp, 15)

    def test_record_bout_awards_xp_to_west(self) -> None:
        """Should award XP to west rikishi."""
        bout_result = self._create_mock_bout_result(west_xp=8)

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        self.west_rikishi.refresh_from_db()
        self.assertEqual(self.west_rikishi.xp, 8)

    def test_record_bout_xp_accumulates(self) -> None:
        """Should accumulate XP across multiple bouts."""
        # Set initial XP
        self.east_rikishi.xp = 100
        self.east_rikishi.save()

        bout_result = self._create_mock_bout_result(east_xp=25)

        # Need a different opponent for second bout
        shikona3 = Shikona.objects.create(
            transliteration="Asanoyama",
            name="朝乃山",
            interpretation="Morning Mountain",
        )
        rank3 = Rank.objects.create(
            division=self.division, title="O", level=2, order=1, direction="E"
        )
        rikishi3 = Rikishi.objects.create(
            shikona=shikona3,
            heya=self.heya,
            potential=80,
            strength=10,
            technique=10,
            balance=10,
            endurance=10,
            mental=10,
        )
        BanzukeEntry.objects.create(
            banzuke=self.banzuke,
            rikishi=rikishi3,
            rank=rank3,
        )

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=rikishi3,
            bout_result=bout_result,
        )

        self.east_rikishi.refresh_from_db()
        self.assertEqual(self.east_rikishi.xp, 125)


class TestRecordBoutValidation(BoutServiceTestCase):
    """Tests for BoutService.record_bout() validation."""

    def test_record_bout_rejects_self_fight(self) -> None:
        """Should raise ValidationError if wrestler fights themselves."""
        bout_result = self._create_mock_bout_result()

        with self.assertRaises(ValidationError) as ctx:
            BoutService.record_bout(
                banzuke=self.banzuke,
                day=1,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.east_rikishi,
                bout_result=bout_result,
            )

        self.assertIn("cannot fight themselves", str(ctx.exception))

    def test_record_bout_rejects_missing_east_entry(self) -> None:
        """Should raise ValidationError if east rikishi not in tournament."""
        # Create rikishi without banzuke entry
        shikona = Shikona.objects.create(
            transliteration="NoEntry",
            name="無登録",
            interpretation="No Entry",
        )
        unregistered = Rikishi.objects.create(
            shikona=shikona,
            heya=self.heya,
            potential=50,
            strength=5,
            technique=5,
            balance=5,
            endurance=5,
            mental=5,
        )

        bout_result = self._create_mock_bout_result()

        with self.assertRaises(ValidationError) as ctx:
            BoutService.record_bout(
                banzuke=self.banzuke,
                day=1,
                east_rikishi=unregistered,
                west_rikishi=self.west_rikishi,
                bout_result=bout_result,
            )

        self.assertIn("not entered", str(ctx.exception))

    def test_record_bout_rejects_missing_west_entry(self) -> None:
        """Should raise ValidationError if west rikishi not in tournament."""
        shikona = Shikona.objects.create(
            transliteration="NoEntry2",
            name="無登録2",
            interpretation="No Entry 2",
        )
        unregistered = Rikishi.objects.create(
            shikona=shikona,
            heya=self.heya,
            potential=50,
            strength=5,
            technique=5,
            balance=5,
            endurance=5,
            mental=5,
        )

        bout_result = self._create_mock_bout_result()

        with self.assertRaises(ValidationError) as ctx:
            BoutService.record_bout(
                banzuke=self.banzuke,
                day=1,
                east_rikishi=self.east_rikishi,
                west_rikishi=unregistered,
                bout_result=bout_result,
            )

        self.assertIn("not entered", str(ctx.exception))

    def test_record_bout_rejects_duplicate_bout(self) -> None:
        """Should raise error for duplicate bout in same tournament."""
        bout_result = self._create_mock_bout_result()

        # First bout succeeds
        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        # Second bout with same wrestlers fails (ValidationError from clean)
        with self.assertRaises(ValidationError) as ctx:
            BoutService.record_bout(
                banzuke=self.banzuke,
                day=5,
                east_rikishi=self.east_rikishi,
                west_rikishi=self.west_rikishi,
                bout_result=bout_result,
            )

        self.assertIn("already fought", str(ctx.exception))


class TestGetTournamentBouts(BoutServiceTestCase):
    """Tests for BoutService.get_tournament_bouts()."""

    def test_get_tournament_bouts_returns_all(self) -> None:
        """Should return all bouts for a tournament."""
        # Create multiple bouts with different opponents
        bout_result = self._create_mock_bout_result()

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        bouts = BoutService.get_tournament_bouts(self.banzuke)
        self.assertEqual(len(bouts), 1)

    def test_get_tournament_bouts_filters_by_day(self) -> None:
        """Should filter bouts by day when specified."""
        bout_result = self._create_mock_bout_result()

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        # Day 1 should have 1 bout
        day1_bouts = BoutService.get_tournament_bouts(self.banzuke, day=1)
        self.assertEqual(len(day1_bouts), 1)

        # Day 2 should have 0 bouts
        day2_bouts = BoutService.get_tournament_bouts(self.banzuke, day=2)
        self.assertEqual(len(day2_bouts), 0)

    def test_get_tournament_bouts_empty_tournament(self) -> None:
        """Should return empty list for tournament with no bouts."""
        bouts = BoutService.get_tournament_bouts(self.banzuke)
        self.assertEqual(bouts, [])


class TestGetRikishiBouts(BoutServiceTestCase):
    """Tests for BoutService.get_rikishi_bouts()."""

    def test_get_rikishi_bouts_as_east(self) -> None:
        """Should return bouts where rikishi was east."""
        bout_result = self._create_mock_bout_result()

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        bouts = BoutService.get_rikishi_bouts(self.east_rikishi)
        self.assertEqual(len(bouts), 1)
        self.assertEqual(bouts[0].east_rikishi, self.east_rikishi)

    def test_get_rikishi_bouts_as_west(self) -> None:
        """Should return bouts where rikishi was west."""
        bout_result = self._create_mock_bout_result()

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
        )

        bouts = BoutService.get_rikishi_bouts(self.west_rikishi)
        self.assertEqual(len(bouts), 1)
        self.assertEqual(bouts[0].west_rikishi, self.west_rikishi)

    def test_get_rikishi_bouts_filters_by_tournament(self) -> None:
        """Should filter bouts by tournament when specified."""
        bout_result = self._create_mock_bout_result()

        BoutService.record_bout(
            banzuke=self.banzuke,
            day=1,
            east_rikishi=self.east_rikishi,
            west_rikishi=self.west_rikishi,
            bout_result=bout_result,
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

        # Should find bout only in first tournament
        bouts = BoutService.get_rikishi_bouts(
            self.east_rikishi, banzuke=self.banzuke
        )
        self.assertEqual(len(bouts), 1)

        # Should find no bouts in second tournament
        bouts2 = BoutService.get_rikishi_bouts(
            self.east_rikishi, banzuke=banzuke2
        )
        self.assertEqual(len(bouts2), 0)
