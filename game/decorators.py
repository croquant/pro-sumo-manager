"""Custom decorators for the game app."""

from functools import wraps
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def heya_required(view_func: Callable) -> Callable:
    """
    Decorator that redirects users without a heya to the setup flow.

    Use this on views that require the user to have a heya (stable).
    Users without a heya will be redirected to the heya name selection page.
    """

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            if not hasattr(request.user, "heya") or request.user.heya is None:
                return redirect("setup_heya_name")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def setup_in_progress(view_func: Callable) -> Callable:
    """
    Decorator for setup views that redirects users who already have a heya.

    Use this on setup flow views to prevent users who have already
    completed setup from accessing them again.
    """

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            if hasattr(request.user, "heya") and request.user.heya is not None:
                return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
