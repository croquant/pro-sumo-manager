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


def _user_has_rikishi(user: object) -> bool:
    """
    Check if a user's heya has any rikishi.

    Args:
    ----
        user: The user object to check.

    Returns:
    -------
        True if the user's heya has at least one rikishi, False otherwise.

    """
    try:
        return user.heya.rikishi.exists()  # type: ignore[union-attr]
    except AttributeError:
        return False


def heya_required(view_func: ViewFunc) -> ViewFunc:
    """
    Redirect users without a heya or rikishi to the appropriate setup step.

    Use this on views that require the user to have a heya (stable) with
    at least one rikishi. Users without a heya will be redirected to the
    heya name selection page. Users with a heya but no rikishi will be
    redirected to the draft pool.

    Example::

        @login_required
        @heya_required
        def dashboard(request): ...

    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated:
            if not _user_has_heya(request.user):
                return redirect("setup_heya_name")
            if not _user_has_rikishi(request.user):
                return redirect("setup_draft_pool")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def setup_in_progress(view_func: ViewFunc) -> ViewFunc:
    """
    Redirect users who already have a heya away from heya name setup.

    Use this on the heya name selection view to prevent users who have
    already selected a heya name from accessing it again. Users with
    a heya but no rikishi are redirected to the draft pool.

    Example::

        @login_required
        @setup_in_progress
        def setup_heya_name(request): ...

    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated and _user_has_heya(request.user):
            if _user_has_rikishi(request.user):
                return redirect("dashboard")
            return redirect("setup_draft_pool")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def draft_pending(view_func: ViewFunc) -> ViewFunc:
    """
    Allow only users with heya but no rikishi yet.

    Use this on the draft pool view to ensure users have completed
    heya selection but haven't yet drafted their first wrestler.

    Example::

        @login_required
        @draft_pending
        def setup_draft_pool(request): ...

    """

    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated:
            if not _user_has_heya(request.user):
                return redirect("setup_heya_name")
            if _user_has_rikishi(request.user):
                return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
