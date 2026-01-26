"""Tests for game views."""

from django.test import TestCase
from django.urls import reverse


class IndexViewTests(TestCase):
    """Tests for the index view."""

    def test_index_view_returns_200(self) -> None:
        """Test landing page renders successfully."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_index_view_contains_title(self) -> None:
        """Test landing page contains expected content."""
        response = self.client.get(reverse("index"))
        self.assertContains(response, "Pro Sumo Manager")
