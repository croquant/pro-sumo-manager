"""Middleware for accounts app."""

from collections.abc import Callable
from urllib.parse import urlparse

from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy

# Cache the login URL at module level for performance
_LOGIN_URL = str(reverse_lazy("account_login"))


class HtmxAuthRedirectMiddleware:
    """
    Handle authentication redirects for HTMX requests.

    When an HTMX request receives a redirect to the login page,
    this middleware converts it to an HX-Redirect header so the
    browser performs a full page navigation instead of trying
    to swap the login page into the current content area.
    """

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and response."""
        response = self.get_response(request)

        # Early return for non-redirect responses (most common case)
        if response.status_code != 302:
            return response

        # Check if this is an HTMX request
        is_htmx = getattr(request, "htmx", None)
        if not is_htmx:
            return response

        # Check if redirecting to login page
        location = response.get("Location", "")
        redirect_path = urlparse(location).path
        if not redirect_path.startswith(_LOGIN_URL):
            return response

        # Return a 200 response with HX-Redirect header
        # This tells HTMX to do a full page redirect
        redirect_response = HttpResponse(status=200)
        redirect_response["HX-Redirect"] = location
        return redirect_response
