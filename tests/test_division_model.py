"""Tests for the Division model."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from game.enums import Division as DivisionEnum
from game.models import Division


class DivisionModelTests(TestCase):
    """Tests for the Division model."""

    def test_str_returns_division_label(self) -> None:
        """Should return the division label."""
        division = Division.objects.get(level=1)
        self.assertEqual(str(division), "Makuuchi")

    def test_ordering_by_level(self) -> None:
        """Should order divisions by level (1=highest, 8=lowest)."""
        divisions = list(Division.objects.all())
        self.assertEqual(len(divisions), 8)
        self.assertEqual(divisions[0].name, DivisionEnum.MAKUUCHI)
        self.assertEqual(divisions[1].name, DivisionEnum.JURYO)
        self.assertEqual(divisions[2].name, DivisionEnum.MAKUSHITA)
        self.assertEqual(divisions[3].name, DivisionEnum.SANDANME)
        self.assertEqual(divisions[4].name, DivisionEnum.JONIDAN)
        self.assertEqual(divisions[5].name, DivisionEnum.JONOKUCHI)
        self.assertEqual(divisions[6].name, DivisionEnum.MAE_ZUMO)
        self.assertEqual(divisions[7].name, DivisionEnum.BANZUKE_GAI)

    def test_short_name_returns_enum_value(self) -> None:
        """Should return the short code from the enum value."""
        makuuchi = Division.objects.get(level=1)
        self.assertEqual(makuuchi.name, DivisionEnum.MAKUUCHI.value)
        self.assertEqual(makuuchi.name, "M")

        juryo = Division.objects.get(level=2)
        self.assertEqual(juryo.name, DivisionEnum.JURYO.value)
        self.assertEqual(juryo.name, "J")

    def test_get_name_display_returns_full_name(self) -> None:
        """Should return the full division name using get_name_display()."""
        makuuchi = Division.objects.get(level=1)
        self.assertEqual(makuuchi.get_name_display(), "Makuuchi")

        banzuke_gai = Division.objects.get(level=8)
        self.assertEqual(banzuke_gai.get_name_display(), "Banzuke-gai")

    def test_fail_duplicate_name(self) -> None:
        """Should fail if two divisions have the same name."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Division.objects.create(level=99, name=DivisionEnum.MAKUUCHI)

    def test_fail_level_below_minimum(self) -> None:
        """Should fail if level is less than 1."""
        division = Division(level=0, name=DivisionEnum.MAKUUCHI)
        with self.assertRaises(ValidationError) as context:
            division.full_clean()
        self.assertIn("level", str(context.exception))

    def test_fail_level_above_maximum(self) -> None:
        """Should fail if level is greater than 8."""
        division = Division(level=9, name=DivisionEnum.MAKUUCHI)
        with self.assertRaises(ValidationError) as context:
            division.full_clean()
        self.assertIn("level", str(context.exception))

    def test_level_within_valid_range(self) -> None:
        """Should accept levels between 1 and 8."""
        for level in range(1, 9):
            division = Division.objects.get(level=level)
            division.full_clean()  # Should not raise


class DivisionPopulationTests(TestCase):
    """Tests for the populated Division records."""

    def test_all_divisions_populated(self) -> None:
        """Should have exactly 8 divisions populated."""
        self.assertEqual(Division.objects.count(), 8)

    def test_division_levels_correct(self) -> None:
        """Should have divisions at levels 1-8 with correct names."""
        expected_divisions = [
            (1, DivisionEnum.MAKUUCHI, "Makuuchi"),
            (2, DivisionEnum.JURYO, "Juryo"),
            (3, DivisionEnum.MAKUSHITA, "Makushita"),
            (4, DivisionEnum.SANDANME, "Sandanme"),
            (5, DivisionEnum.JONIDAN, "Jonidan"),
            (6, DivisionEnum.JONOKUCHI, "Jonokuchi"),
            (7, DivisionEnum.MAE_ZUMO, "Mae-zumo"),
            (8, DivisionEnum.BANZUKE_GAI, "Banzuke-gai"),
        ]

        for level, enum_value, display_name in expected_divisions:
            division = Division.objects.get(level=level)
            self.assertEqual(division.name, enum_value.value)
            self.assertEqual(division.get_name_display(), display_name)

    def test_no_duplicate_levels(self) -> None:
        """Should have no duplicate level values."""
        levels = Division.objects.values_list("level", flat=True)
        self.assertEqual(len(levels), len(set(levels)))

    def test_no_duplicate_names(self) -> None:
        """Should have no duplicate name values."""
        names = Division.objects.values_list("name", flat=True)
        self.assertEqual(len(names), len(set(names)))
