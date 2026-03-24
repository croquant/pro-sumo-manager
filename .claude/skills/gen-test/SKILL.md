---
name: gen-test
description: Generate a Django test file for a module. Use this skill whenever the user asks to create tests, add test coverage, write tests for a service/model/view, or mentions "gen-test". Also use when the user says things like "test this", "add tests for X", or "we need tests for the new service".
---

# Generate Test File

Create a test file in `tests/` that follows this project's conventions exactly.

## Before writing

1. Read the module being tested to understand its public API
2. Read `tests/runner.py` to recall how OpenAI is mocked globally
3. Skim 1-2 existing test files in `tests/` for current patterns (e.g., `tests/test_rikishi_service.py`, `tests/test_training_service.py`)

## Conventions

These conventions exist because the project enforces them via pre-commit hooks (ruff, pyright, coverage checks). Breaking them means the commit will fail.

- **Location**: `tests/test_<module_name>.py`
- **Framework**: `django.test.TestCase` — not pytest, not unittest directly
- **Imports**: Use `from __future__ import annotations` as the first import
- **Type hints**: All methods need return type annotations (`:-> None` for test methods)
- **Docstrings**: Every test class and test method needs a docstring (ruff D rules)
- **Line length**: 80 characters max
- **Strings**: Double quotes
- **OpenAI**: Already mocked globally by the custom test runner — never mock it yourself, never make real API calls
- **No fixtures files**: Create test data in `setUp()` using Django ORM

## Test structure

```python
"""Tests for <module description>."""

from __future__ import annotations

from django.test import TestCase
# ... other imports

class <Module>Tests(TestCase):
    """Test suite for <Module>."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create minimal required model instances via ORM

    def test_<behavior_being_tested>(self) -> None:
        """Should <expected behavior in plain English>."""
        # Arrange / Act / Assert
```

## What to test

- All public methods on the module
- Edge cases: empty inputs, boundary values, invalid data
- For services: both success paths and expected `ValidationError` raises
- For models: custom methods, properties, constraints, `__str__`
- For views: status codes, template used, context data, redirects

## After writing

Run the new test file to make sure it passes:

```bash
uv run python manage.py test tests.test_<module_name>
```

If it fails, fix it before presenting to the user. Tests that don't pass on first run waste everyone's time.
