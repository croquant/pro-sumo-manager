# Pro Sumo Manager

Django-based sumo stable management simulation game.

## Commands

- **Run tests**: `./test.sh` — IMPORTANT: must pass before every commit
- **Run single test**: `uv run python manage.py test tests.test_bout_service`
- **Type check**: `uv run pyright`
- **Lint/format**: `uv run ruff check --fix && uv run ruff format`
- **Create migration**: `uv run python manage.py makemigrations`
- **Install deps**: `uv sync`
- **Dev server**: `uv run python manage.py runserver`
- **CSS watcher**: `./build-css.sh` (Tailwind, run in separate terminal)

## Environment

- Copy `.env.example` to `.env` for local development
- Required vars: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`

## Code Style

- Line length: 80 chars
- Double quotes for strings
- Strict type hints on all functions (parameters and return types)
- Docstrings required on all public modules, classes, and functions (ruff D rules enabled)
- Imports sorted by ruff (isort-compatible)

## Testing

- Uses Django's `TestCase`, not pytest
- OpenAI is mocked globally via custom test runner — never make real API calls in tests
- `./test.sh` enforces coverage cannot decrease (baseline in `coverage/.coverage_total`)
- Test files live in `tests/` at project root, named `test_*.py`

## Architecture

- `config/` — Django settings, URLs, ASGI/WSGI
- `game/models/` — one model per file
- `game/views.py` — single file (not a directory)
- `game/services/` — business logic, keeps views thin
- `game/enums/` — enums in separate files
- `libs/constants.py` — shared game constants (stats, calendar, potentials)
- `libs/generators/` — data generators (names, rikishi, bouts, shusshin)
- `libs/types/` — Pydantic types used by generators
- `libs/singletons/openai.py` — OpenAI client singleton
- `accounts/` — custom user model with allauth

## Frontend

- HTMX for interactions, django-cotton for components
- Templates in `game/templates/game/`, partials in `partials/` subdirectory
- Tailwind CSS v4 + DaisyUI for styling

## Pre-commit

Runs automatically on commit: trailing whitespace, ruff (check + format), pyright, Django system check, migrations check, and `./test.sh`. All must pass.
