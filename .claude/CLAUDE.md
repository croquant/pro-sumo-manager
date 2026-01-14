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
