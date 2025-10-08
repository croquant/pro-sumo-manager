# Project Context for Claude Code

## Project Overview

**Pro Sumo Manager** is a Django-based sumo stable management simulation game (version 0.0.1a1). Players run their own sumo stable (heya), sign wrestlers, plan training, set match strategies, and compete to reach the top tier of professional sumo wrestling.

## Sumo Wrestling Domain Concepts

### Key Terminology
- **Shikona (四股名)**: Ring name taken by a sumo wrestler. Written in kanji with romaji transliteration
- **Shusshin (出身)**: Place of origin for a wrestler (country + Japanese prefecture if from Japan)
- **Heya (部屋)**: Sumo stable or training facility where wrestlers live and train
- **Rikishi (力士)**: Sumo wrestler

## Architecture & Tech Stack

### Framework
- **Django 5.2.5**: Web framework
- **Python 3.13**: Language version (strict type checking with mypy)
- **SQLite**: Database
- **OpenAI API**: AI-powered features

### Project Structure
```
config/          # Django project settings, URLs, ASGI/WSGI
game/            # Main Django app (core game logic)
  ├── models.py  # Database models (Shusshin, Shikona)
  ├── admin.py   # Django admin interface
  ├── enums/     # Enum definitions (Country, JPPrefecture)
  └── migrations/
libs/            # Shared utilities and generators
  └── generators/
      ├── name.py          # Bigram-based shikona generator
      └── data/            # Corpus data for name generation
tests/           # Test suite (pytest)
```

## Key Models

### Shusshin (Origin)
Represents a wrestler's place of origin with special handling for Japan:
- **country_code**: ISO 3166-1 alpha-2 code (2 chars)
- **jp_prefecture**: Japanese prefecture code (5 chars, only for JP)

**Important Constraints:**
- If country is JP, jp_prefecture MUST be set (not empty)
- If country is NOT JP, jp_prefecture MUST be empty
- Non-JP countries: one Shusshin per country (unique constraint)
- JP: one Shusshin per prefecture (unique constraint)
- Ordering: country_code, then jp_prefecture

### Shikona (Ring Name)
Represents a wrestler's professional ring name:
- **name**: Kanji name (max 8 chars, unique)
- **transliteration**: Romaji/Hepburn romanization (max 32 chars, unique)
- **interpretation**: Meaning/translation of the name (max 64 chars)
- **Ordering**: By transliteration (alphabetical)

## Name Generation System

### RikishiNameGenerator (`libs/generators/name.py`)
Generates authentic-sounding Japanese ring names using:
- **Bigram probability model**: Trained on corpus of real shikona
- **Character-based generation**: Builds names character by character
- **Phoneme normalization**: Converts to proper Hepburn romanization
- **Uniqueness tracking**: Prevents duplicate names
- **Max length**: 5 kanji characters
- **Data source**: `libs/generators/data/shikona_corpus.txt`

**Phoneme Processing:**
- Converts Kunrei-shiki to Hepburn (si→shi, ti→chi, tu→tsu, etc.)
- Normalizes long vowels (aa→a, ii→i, ou→o)
- Handles special sequences (ryuu→ryu, samurai→ji)

## Development Workflow

### Environment Setup
- Package manager: **uv** (uv.lock for dependencies)
- Python version: Specified in `.python-version`
- Environment variables: See `.env.example`

### Code Quality Tools
- **Ruff**: Linting and formatting (configured in `ruff.toml`)
- **mypy**: Strict type checking with django-stubs
- **pre-commit**: Enforces formatting, linting, Django checks, migrations, and tests

### Testing
- **Always use `./test.sh`** to run the test suite
- Coverage tracking is enforced via pre-commit hooks
- Coverage report: `coverage/coverage.json`
- When coverage changes, `.coverage_total` is updated automatically
- **Never skip pre-commit hooks** (`--no-verify`) except in emergencies

### Pre-commit Hook Workflow
1. Hooks run automatically on `git commit`
2. If files are modified (e.g., by `ruff format`), stage them and rerun
3. If `.coverage_total` is updated, stage and commit it
4. Keep running until hooks pass cleanly

## Important Conventions

### Code Style
- Strict type hints (mypy strict mode enabled)
- Django-stubs for Django type checking
- Migrations excluded from mypy checks
- Docstrings use triple quotes and proper formatting
- Models have explicit `__str__` methods

### Database Constraints
- Use Django's `CheckConstraint` for business logic validation
- Use `UniqueConstraint` with conditions for complex uniqueness rules
- Always define `Meta.ordering` for consistent query results
- Use `verbose_name` and `verbose_name_plural` for proper admin display

### Enum Patterns
- Use Django's `TextChoices` for database-backed enums
- Store as short codes (e.g., "JP"), display as labels (e.g., "Japan")
- Country enum: ISO 3166-1 alpha-2 codes (all countries included)
- JP Prefecture enum: Custom 5-char codes

## Current Git State

- **Current branch**: `fix-country-names`
- **Main branch**: `master` (use for PRs)
- **Recent work**: Refactoring country names and Shikona model
- **Untracked files in root**: Various PDF/JSON test files (not part of project)

## Testing Patterns

### Existing Test Coverage
- `test_name_generator.py`: Name generation logic
- `test_shusshin_model.py`: Shusshin model and constraints
- `test_shusshin_admin.py`: Django admin interface

### Testing Approach
- Use Django TestCase for model tests
- Test database constraints explicitly
- Test uniqueness rules and validation logic
- Coverage must be maintained or improved

## Common Tasks

### Adding a New Model
1. Define model in `game/models.py` with full type hints
2. Add constraints in `Meta` class
3. Register in `game/admin.py`
4. Create migration: `python manage.py makemigrations`
5. Write tests in `tests/`
6. Run `./test.sh` to verify

### Adding a New Enum
1. Create enum file in `game/enums/` using `TextChoices`
2. Export from `game/enums/__init__.py`
3. Use in model as `choices` parameter
4. Create migration if modifying existing fields

### Working with Names
- Use `RikishiNameGenerator` for generating shikona
- Generator is seeded for deterministic testing
- Names are stored as both kanji and romanized forms
- Uniqueness is enforced at the database level

## AI Integration Notes

- OpenAI dependency present (not yet fully utilized in visible code)
- Likely used for generating name interpretations or game content
- Check `.env` for required API keys

## References

- **AGENTS.md**: AI agent workflow instructions
- **pyproject.toml**: Dependencies and tool configuration
- **ruff.toml**: Linting rules
- **.pre-commit-config.yaml**: Hook configuration
