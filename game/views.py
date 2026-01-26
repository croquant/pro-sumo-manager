"""Views for the game app."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Landing page."""
    return render(request, "game/index.html")
