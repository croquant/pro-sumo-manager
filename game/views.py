"""Views for the game app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from game.decorators import heya_required, setup_in_progress
from game.models import Heya, Rikishi, Shikona, Shusshin
from game.services.draft_pool_service import DraftCandidate, DraftPoolService
from game.services.game_clock import GameClockService
from game.services.shikona_service import ShikonaService


def index(request: HttpRequest) -> HttpResponse:
    """Landing page."""
    return render(request, "game/index.html")


@login_required
@heya_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the main game dashboard."""
    return render(request, "game/dashboard.html")


@login_required
@setup_in_progress
def setup_heya_name(request: HttpRequest) -> HttpResponse:
    """
    Handle heya name selection during onboarding.

    GET: Display 3 generated shikona options for the user to choose from.
    POST: Create the heya with the selected name and redirect to next step.
    """
    if request.method == "POST":
        return _handle_heya_name_selection(request)

    # Generate options and store in session for consistency
    if "heya_options" not in request.session:
        options = ShikonaService.generate_shikona_options(count=3)
        if len(options) < 3:
            messages.warning(
                request,
                "Some name options may be limited due to high demand.",
            )
        request.session["heya_options"] = [
            {
                "name": opt.name,
                "transliteration": opt.transliteration,
                "interpretation": opt.interpretation,
            }
            for opt in options
        ]

    return render(
        request,
        "game/setup/heya_name.html",
        {"options": request.session["heya_options"]},
    )


@transaction.atomic
def _handle_heya_name_selection(request: HttpRequest) -> HttpResponse:
    """Process the heya name selection form submission."""
    selected_index = request.POST.get("selected_option")

    if selected_index is None:
        messages.error(request, "Please select a name for your stable.")
        return redirect("setup_heya_name")

    try:
        index = int(selected_index)
        options = request.session.get("heya_options", [])

        if not 0 <= index < len(options):
            messages.error(request, "Invalid selection. Please try again.")
            return redirect("setup_heya_name")

        selected = options[index]

        # Create or get the Shikona (handles race condition)
        shikona, _ = Shikona.objects.get_or_create(
            name=selected["name"],
            defaults={
                "transliteration": selected["transliteration"],
                "interpretation": selected["interpretation"],
            },
        )

        # Initialize game clock (handles "already exists" gracefully)
        current_date = GameClockService.initialize()

        # Create the Heya
        Heya.objects.create(
            name=shikona,
            created_at=current_date,
            owner=request.user,
        )

        # Clear session data (use pop for safer cleanup)
        request.session.pop("heya_options", None)

        messages.success(
            request,
            f"Welcome to {shikona.transliteration} stable!",
        )

        return redirect("setup_draft_pool")

    except IntegrityError:
        # Race condition: name was taken between generation and creation
        request.session.pop("heya_options", None)
        messages.error(
            request,
            "This name was just taken. Please select a different name.",
        )
        return redirect("setup_heya_name")
    except (ValueError, KeyError, IndexError):
        messages.error(request, "Invalid selection. Please try again.")
        return redirect("setup_heya_name")


def _user_needs_draft(user: object) -> bool:
    """
    Check if a user needs to complete the draft phase.

    A user needs to draft if they have a heya but no rikishi yet.

    Args:
        user: The user object to check.

    Returns:
        True if the user needs to draft, False otherwise.

    """
    try:
        heya = user.heya  # type: ignore[union-attr]
        return heya is not None and not heya.rikishi.exists()
    except AttributeError:
        return False


@login_required
def setup_draft_pool(request: HttpRequest) -> HttpResponse:
    """
    Handle draft pool selection during onboarding.

    GET: Display a pool of generated wrestlers for the user to choose from.
    POST: Create the selected wrestler and assign to the user's heya.
    """
    # Check user has a heya
    user = request.user
    if not hasattr(user, "heya") or user.heya is None:  # type: ignore[union-attr]
        return redirect("setup_heya_name")

    # Check user hasn't already drafted
    heya = user.heya  # type: ignore[union-attr]
    if heya.rikishi.exists():
        return redirect("dashboard")

    if request.method == "POST":
        return _handle_draft_selection(request)

    # Generate draft pool and store in session for consistency
    if "draft_pool" not in request.session:
        candidates = DraftPoolService.generate_draft_pool()
        request.session["draft_pool"] = [c.to_dict() for c in candidates]

    # Convert back to DraftCandidate objects for template
    candidates = [
        DraftCandidate.from_dict(c) for c in request.session["draft_pool"]
    ]

    return render(
        request,
        "game/setup/draft_pool.html",
        {"candidates": candidates, "heya_name": heya.name},
    )


@transaction.atomic
def _handle_draft_selection(request: HttpRequest) -> HttpResponse:
    """Process the draft selection form submission."""
    selected_index = request.POST.get("selected_wrestler")

    if selected_index is None:
        messages.error(request, "Please select a wrestler to draft.")
        return redirect("setup_draft_pool")

    try:
        index = int(selected_index)
        pool_data = request.session.get("draft_pool", [])

        if not 0 <= index < len(pool_data):
            messages.error(request, "Invalid selection. Please try again.")
            return redirect("setup_draft_pool")

        selected = DraftCandidate.from_dict(pool_data[index])
        heya = request.user.heya  # type: ignore[union-attr]

        # Create or get the Shikona
        shikona, _ = Shikona.objects.get_or_create(
            name=selected.shikona_name,
            defaults={
                "transliteration": selected.shikona_transliteration,
                "interpretation": "",  # Interpretation not stored in candidate
            },
        )

        # Get or create the Shusshin
        shusshin = _get_shusshin_from_display(selected.shusshin_display)

        # Create the Rikishi
        Rikishi.objects.create(
            shikona=shikona,
            heya=heya,
            shusshin=shusshin,
            potential=selected._potential,
            strength=selected.strength,
            technique=selected.technique,
            balance=selected.balance,
            endurance=selected.endurance,
            mental=selected.mental,
        )

        # Clear session data
        request.session.pop("draft_pool", None)

        messages.success(
            request,
            f"You have drafted {selected.shikona_transliteration}!",
        )

        return redirect("dashboard")

    except IntegrityError:
        request.session.pop("draft_pool", None)
        messages.error(
            request,
            "This wrestler was just drafted. Please select another.",
        )
        return redirect("setup_draft_pool")
    except (ValueError, KeyError, IndexError):
        messages.error(request, "Invalid selection. Please try again.")
        return redirect("setup_draft_pool")


def _get_shusshin_from_display(display: str) -> Shusshin | None:
    """
    Look up a Shusshin from a display name.

    Args:
        display: The display name (prefecture or country name).

    Returns:
        The matching Shusshin object, or None if not found.

    """
    from game.enums.country_enum import Country
    from game.enums.jp_prefecture_enum import JPPrefecture

    # Try to find by prefecture name (Japanese wrestlers)
    for pref in JPPrefecture:
        if pref.label == display:
            return Shusshin.objects.filter(
                country_code="JP",
                jp_prefecture=pref.value,
            ).first()

    # Try to find by country name (foreign wrestlers)
    for country in Country:
        if country.label == display:
            return Shusshin.objects.filter(country_code=country.value).first()

    return None
