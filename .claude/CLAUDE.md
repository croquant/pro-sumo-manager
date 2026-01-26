# Pro Sumo Manager

Django-based sumo stable management simulation game.

## Quick Reference

- **Test**: `./test.sh` (required before commits)
- **Package manager**: `uv` (use `uv sync`, `uv run`)
- **Type checker**: Pyright (strict)
- **Linter**: Ruff (`ruff.toml`)

## Project Structure

```
config/     # Django settings
game/       # Main app (models/, enums/, services/, admin.py)
libs/       # Generators and utilities
tests/      # pytest suite
```

## Key Conventions

- Python 3.13, Django 5.2.5
- Strict type hints required
- Line length: 80 chars
- Pre-commit runs: ruff, pyright, Django checks, tests
- Coverage must not decrease

## Frontend Stack

- **CSS Build**: `./build-css.sh` (runs Tailwind watcher)
- **Templates**: `game/templates/game/`
- **Components**: `cotton/` (django-cotton)
- **Partials**: `game/templates/game/partials/` (HTMX responses)

### Technologies

- HTMX for server interactions (no JavaScript needed)
- Tailwind CSS v4 + DaisyUI for styling
- django-cotton for reusable components

### Development

Run in two terminals:
1. `./build-css.sh` - CSS watcher
2. `uv run python manage.py runserver` - Django server
