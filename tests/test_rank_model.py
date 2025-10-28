"""Tests for the Rank model."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from game.enums import Direction, RankTitle
from game.models import Division, Rank


class RankModelTests(TestCase):
    """Tests for the Rank model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.makuuchi = Division.objects.get(level=1)
        self.juryo = Division.objects.get(level=2)

    def test_str_returns_simple_title(self) -> None:
        """Should return just the title for non-positional ranks."""
        yokozuna = Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.YOKOZUNA,
            level=1,
            order=0,
            direction="",
        )
        self.assertEqual(str(yokozuna), "Yokozuna")

    def test_str_returns_formatted_name_with_position(self) -> None:
        """Should return formatted name with order and direction."""
        maegashira = Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.MAEGASHIRA,
            level=5,
            order=1,
            direction=Direction.EAST,
        )
        self.assertEqual(str(maegashira), "Maegashira 1E")

    def test_name_property_with_position(self) -> None:
        """Should return name with short direction."""
        rank = Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.MAEGASHIRA,
            level=5,
            order=3,
            direction=Direction.WEST,
        )
        self.assertEqual(rank.name, "Maegashira 3W")

    def test_long_name_property(self) -> None:
        """Should return name with full direction."""
        rank = Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.SEKIWAKE,
            level=3,
            order=1,
            direction=Direction.EAST,
        )
        self.assertEqual(rank.long_name, "Sekiwake 1 East")

    def test_short_name_property(self) -> None:
        """Should return abbreviated name."""
        rank = Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.OZEKI,
            level=2,
            order=1,
            direction=Direction.WEST,
        )
        self.assertEqual(rank.short_name, "O1W")

    def test_short_name_without_position(self) -> None:
        """Should return just title abbreviation for non-positional ranks."""
        yokozuna = Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.YOKOZUNA,
            level=1,
            order=0,
            direction="",
        )
        self.assertEqual(yokozuna.short_name, "Y")

    def test_ordering_by_level_order_direction(self) -> None:
        """Should order ranks by level, then order, then direction."""
        # Create ranks in random order
        Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.MAEGASHIRA,
            level=5,
            order=2,
            direction=Direction.WEST,
        )
        Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.YOKOZUNA,
            level=1,
            order=0,
            direction="",
        )
        Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.MAEGASHIRA,
            level=5,
            order=1,
            direction=Direction.EAST,
        )
        Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.OZEKI,
            level=2,
            order=1,
            direction=Direction.EAST,
        )

        ranks = list(Rank.objects.all())
        self.assertEqual(ranks[0].title, RankTitle.YOKOZUNA.value)
        self.assertEqual(ranks[1].title, RankTitle.OZEKI.value)
        self.assertEqual(ranks[2].order, 1)
        self.assertEqual(ranks[2].direction, Direction.EAST.value)
        self.assertEqual(ranks[3].order, 2)
        self.assertEqual(ranks[3].direction, Direction.WEST.value)

    def test_fail_duplicate_rank_position(self) -> None:
        """Should fail if same division, title, order, and direction."""
        Rank.objects.create(
            division=self.makuuchi,
            title=RankTitle.MAEGASHIRA,
            level=5,
            order=1,
            direction=Direction.EAST,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rank.objects.create(
                division=self.makuuchi,
                title=RankTitle.MAEGASHIRA,
                level=5,
                order=1,
                direction=Direction.EAST,
            )

    def test_fail_order_zero_when_positive_expected(self) -> None:
        """Should fail if order is 0 when it should be positive."""
        # Now enforced by CHECK constraint at database level
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rank.objects.create(
                division=self.makuuchi,
                title=RankTitle.MAEGASHIRA,
                level=5,
                order=0,
                direction=Direction.EAST,
            )

    def test_fail_direction_without_order(self) -> None:
        """Should fail if direction is set but order is 0."""
        # Now enforced by CHECK constraint at database level
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rank.objects.create(
                division=self.makuuchi,
                title=RankTitle.YOKOZUNA,
                level=1,
                order=0,
                direction=Direction.EAST,
            )

    def test_fail_order_without_direction(self) -> None:
        """Should fail if order > 0 but direction is empty."""
        # Now enforced by CHECK constraint at database level
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rank.objects.create(
                division=self.makuuchi,
                title=RankTitle.MAEGASHIRA,
                level=5,
                order=1,
                direction="",
            )

    def test_level_range_valid(self) -> None:
        """Should accept valid level values (1-12)."""
        test_cases = [
            (1, RankTitle.YOKOZUNA),
            (2, RankTitle.OZEKI),
            (6, RankTitle.JURYO),
            (12, RankTitle.BANZUKE_GAI),
        ]
        for level, title in test_cases:
            rank = Rank.objects.create(
                division=self.makuuchi,
                title=title,
                level=level,
                order=0,
                direction="",
            )
            rank.full_clean()  # Should not raise

    def test_fail_level_below_minimum(self) -> None:
        """Should fail if level is less than 1."""
        # PositiveSmallIntegerField already prevents 0 and negative values
        # Test with CHECK constraint using database insert
        with self.assertRaises((ValidationError, IntegrityError)):
            Rank.objects.create(
                division=self.makuuchi,
                title=RankTitle.YOKOZUNA,
                level=0,
                order=0,
                direction="",
            )

    def test_fail_level_above_maximum(self) -> None:
        """Should fail if level is greater than 12."""
        rank = Rank(
            division=self.makuuchi,
            title=RankTitle.YOKOZUNA,
            level=13,
            order=0,
            direction="",
        )
        with self.assertRaises(ValidationError):
            rank.full_clean()

    def test_division_relationship(self) -> None:
        """Should maintain proper ForeignKey relationship with Division."""
        rank = Rank.objects.create(
            division=self.juryo,
            title=RankTitle.JURYO,
            level=6,
            order=1,
            direction=Direction.EAST,
        )
        self.assertEqual(rank.division, self.juryo)
        self.assertIn(rank, self.juryo.ranks.all())

    def test_division_protected_delete(self) -> None:
        """Should prevent deletion of division that has ranks."""
        from django.db.models.deletion import ProtectedError

        Rank.objects.create(
            division=self.juryo,
            title=RankTitle.JURYO,
            level=6,
            order=1,
            direction=Direction.EAST,
        )
        with self.assertRaises(ProtectedError):
            self.juryo.delete()
