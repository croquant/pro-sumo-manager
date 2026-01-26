"""Custom decorators for the game app."""

from collections.abc import Callable
from functools import wraps

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

ViewFunc = Callable[..., HttpResponse]


def heya_required(view_func: ViewFunc) -> ViewFunc:
    """
    Redirect users without a heya to the setup flow.

    Use this on views that require the user to have a heya (stable).
    Users without a heya will be redirected to the heya name selection page.
    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated and (
            not hasattr(request.user, "heya") or request.user.heya is None
        ):
            return redirect("setup_heya_name")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def setup_in_progress(view_func: ViewFunc) -> ViewFunc:
    """
    Redirect users who already have a heya away from setup views.

    Use this on setup flow views to prevent users who have already
    completed setup from accessing them again.
    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated and (
            hasattr(request.user, "heya") and request.user.heya is not None
        ):
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
