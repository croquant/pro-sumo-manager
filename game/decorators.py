"""Custom decorators for the game app."""

from collections.abc import Callable
from functools import wraps

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

ViewFunc = Callable[..., HttpResponse]


def _user_has_heya(user: object) -> bool:
    """
    Check if a user has an associated heya.

    Args:
    ----
        user: The user object to check.

    Returns:
    -------
        True if the user has a heya, False otherwise.

    """
    try:
        return user.heya is not None  # type: ignore[union-attr]
    except AttributeError:
        # RelatedObjectDoesNotExist inherits from AttributeError
        return False


def heya_required(view_func: ViewFunc) -> ViewFunc:
    """
    Redirect users without a heya to the setup flow.

    Use this on views that require the user to have a heya (stable).
    Users without a heya will be redirected to the heya name selection page.

    Example::

        @login_required
        @heya_required
        def dashboard(request):
            ...

    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated and not _user_has_heya(request.user):
            return redirect("setup_heya_name")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def setup_in_progress(view_func: ViewFunc) -> ViewFunc:
    """
    Redirect users who already have a heya away from setup views.

    Use this on setup flow views to prevent users who have already
    completed setup from accessing them again.

    Example::

        @login_required
        @setup_in_progress
        def setup_heya_name(request):
            ...

    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated and _user_has_heya(request.user):
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
