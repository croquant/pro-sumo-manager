"""Custom User model for Pro Sumo Manager."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with email as the primary login identifier.

    Extends AbstractUser to use email for authentication while keeping
    username for display purposes in the game.
    """

    email = models.EmailField(
        unique=True,
        help_text="Email address used for login",
    )

    # Username is required and used as the display name in the game
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Display name in the game",
    )

    # Use email for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        """Model metadata."""

        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        """Return the username for display."""
        return self.username
