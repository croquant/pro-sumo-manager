"""Tests for the Shikona model."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from game.models import Shikona


class ShikonaModelTests(TestCase):
    """Tests for the Shikona model."""

    def test_str_returns_transliteration_and_name(self) -> None:
        """Should return transliteration followed by the kanji name."""
        shikona = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        self.assertEqual(str(shikona), "Tsururyu (鶴龍)")

    def test_fail_duplicate_name(self) -> None:
        """Should fail if two Shikona share the same name."""
        Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shikona.objects.create(
                name="鶴龍",
                transliteration="Other",
                interpretation="Phoenix",
            )

    def test_fail_duplicate_transliteration(self) -> None:
        """Should fail if two Shikona share the same transliteration."""
        Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Shikona.objects.create(
                name="鳳凰",
                transliteration="Tsururyu",
                interpretation="Phoenix",
            )

    def test_parent_field_optional(self) -> None:
        """Should allow creating Shikona without a parent."""
        shikona = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        self.assertIsNone(shikona.parent)

    def test_parent_child_relationship(self) -> None:
        """Should establish parent-child relationship between Shikona."""
        parent = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        child = Shikona.objects.create(
            name="鳳凰",
            transliteration="Hououmaru",
            interpretation="Phoenix Circle",
            parent=parent,
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_parent_deletion_sets_null(self) -> None:
        """Should set parent to null when parent is deleted."""
        parent = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        child = Shikona.objects.create(
            name="鳳凰",
            transliteration="Hououmaru",
            interpretation="Phoenix Circle",
            parent=parent,
        )
        parent.delete()

        child.refresh_from_db()
        self.assertIsNone(child.parent)

    def test_multiple_children(self) -> None:
        """Should allow a parent to have multiple children."""
        parent = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        child1 = Shikona.objects.create(
            name="鳳凰",
            transliteration="Hououmaru",
            interpretation="Phoenix Circle",
            parent=parent,
        )
        child2 = Shikona.objects.create(
            name="白鳳",
            transliteration="Hakuhou",
            interpretation="White Phoenix",
            parent=parent,
        )
        self.assertEqual(parent.children.count(), 2)
        self.assertIn(child1, parent.children.all())
        self.assertIn(child2, parent.children.all())

    def test_prevent_self_reference(self) -> None:
        """Should prevent a shikona from being its own parent."""
        shikona = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        shikona.parent = shikona
        with self.assertRaises(ValidationError) as cm:
            shikona.full_clean()
        self.assertIn("parent", cm.exception.message_dict)
        self.assertIn(
            "A shikona cannot be its own parent",
            cm.exception.message_dict["parent"][0],
        )

    def test_prevent_two_node_circular_reference(self) -> None:
        """Should prevent circular reference in a two-node chain."""
        parent = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        child = Shikona.objects.create(
            name="鳳凰",
            transliteration="Hououmaru",
            interpretation="Phoenix Circle",
            parent=parent,
        )
        # Try to set parent's parent to child (creating A -> B -> A)
        parent.parent = child
        with self.assertRaises(ValidationError) as cm:
            parent.full_clean()
        self.assertIn("parent", cm.exception.message_dict)
        self.assertIn(
            "circular reference",
            cm.exception.message_dict["parent"][0],
        )

    def test_prevent_three_node_circular_reference(self) -> None:
        """Should prevent circular reference in a three-node chain."""
        grandparent = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        parent = Shikona.objects.create(
            name="鳳凰",
            transliteration="Hououmaru",
            interpretation="Phoenix Circle",
            parent=grandparent,
        )
        child = Shikona.objects.create(
            name="白鳳",
            transliteration="Hakuhou",
            interpretation="White Phoenix",
            parent=parent,
        )
        # Try to set grandparent's parent to child (creating A -> B -> C -> A)
        grandparent.parent = child
        with self.assertRaises(ValidationError) as cm:
            grandparent.full_clean()
        self.assertIn("parent", cm.exception.message_dict)
        self.assertIn(
            "circular reference",
            cm.exception.message_dict["parent"][0],
        )

    def test_allow_valid_lineage_chain(self) -> None:
        """Should allow valid lineage chains without circular references."""
        grandparent = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )
        parent = Shikona.objects.create(
            name="鳳凰",
            transliteration="Hououmaru",
            interpretation="Phoenix Circle",
            parent=grandparent,
        )
        child = Shikona.objects.create(
            name="白鳳",
            transliteration="Hakuhou",
            interpretation="White Phoenix",
            parent=parent,
        )
        # This should not raise any errors
        child.full_clean()
        grandparent.full_clean()  # Test validation with no parent
        self.assertEqual(child.parent, parent)
        self.assertEqual(parent.parent, grandparent)
        self.assertIsNone(grandparent.parent)
