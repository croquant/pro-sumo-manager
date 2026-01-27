"""Views for the game app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from game.decorators import draft_pending, heya_required, setup_in_progress
from game.models import Heya, Shikona
from game.services.draft_pool_service import DraftPoolService
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


@login_required
@draft_pending
def setup_draft_pool(request: HttpRequest) -> HttpResponse:
    """
    Handle initial wrestler draft during onboarding.

    GET: Display 5-8 generated wrestler candidates for the user to draft.
    POST: Create the selected wrestler and redirect to dashboard.
    """
    if request.method == "POST":
        return _handle_draft_selection(request)

    # Generate pool and store in session for consistency
    if "draft_pool" not in request.session:
        pool = DraftPoolService.generate_draft_pool(count=6)
        if len(pool) < 3:
            messages.warning(
                request,
                "Draft pool is limited. Please try again later.",
            )
        request.session["draft_pool"] = DraftPoolService.serialize_for_session(
            pool
        )

    return render(
        request,
        "game/setup/draft_pool.html",
        {"pool": request.session["draft_pool"]},
    )


@transaction.atomic
def _handle_draft_selection(request: HttpRequest) -> HttpResponse:
    """Process the draft pool selection form submission."""
    selected_index = request.POST.get("selected_wrestler")

    if selected_index is None:
        messages.error(request, "Please select a wrestler to draft.")
        return redirect("setup_draft_pool")

    try:
        idx = int(selected_index)
        pool = request.session.get("draft_pool", [])

        if not 0 <= idx < len(pool):
            messages.error(request, "Invalid selection. Please try again.")
            return redirect("setup_draft_pool")

        selected = pool[idx]

        # Create the rikishi (heya is guaranteed by @draft_pending decorator)
        rikishi = DraftPoolService.create_rikishi_from_selection(
            selected,
            request.user.heya,  # type: ignore[union-attr]
        )

        # Clear session data
        request.session.pop("draft_pool", None)

        messages.success(
            request,
            f"You drafted {rikishi.shikona.transliteration}!",
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
