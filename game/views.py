"""Views for the game app."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Landing page."""
    return render(request, "game/index.html")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the main game dashboard."""
    return render(request, "game/dashboard.html")
