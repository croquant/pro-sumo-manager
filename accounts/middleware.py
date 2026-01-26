"""Middleware for accounts app."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.urls import reverse


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

        # Check if this is an HTMX request that got redirected to login
        is_htmx = getattr(request, "htmx", None)
        login_url = reverse("account_login")
        if (
            is_htmx
            and response.status_code == 302
            and login_url in response.get("Location", "")
        ):
            # Return a 200 response with HX-Redirect header
            # This tells HTMX to do a full page redirect
            redirect_response = HttpResponse(status=200)
            redirect_response["HX-Redirect"] = response.get("Location", "")
            return redirect_response

        return response
