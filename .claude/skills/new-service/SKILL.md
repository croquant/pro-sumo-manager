---
name: new-service
description: Scaffold a new service in game/services/ with a matching test file. Use this skill when the user wants to create a new service, add business logic for a new domain, or says things like "new service for X", "create a service", or "add service layer for Y".
---

# Scaffold a New Service

Create a service class in `game/services/` and its matching test file in `tests/`, following the project's established patterns.

## Before writing

1. Read `game/services/__init__.py` to see existing exports
2. Skim one existing service (e.g., `game/services/training_service.py`) to match the current style
3. Check what models exist in `game/models/` that the new service might need

## Service file: `game/services/<name>_service.py`

The project keeps views thin and puts business logic in services. Services are classes with `@staticmethod` methods — they don't hold state. This pattern exists because it keeps logic testable without needing to instantiate service objects.

```python
"""Service for managing <domain> operations."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

# Import only the models you need
from game.models import <Model>


class <Name>Service:
    """
    Service for managing <domain>-related operations.

    <Brief description of what this service handles and why
    it exists as a separate service.>
    """

    @staticmethod
    def <method_name>(<params with type hints>) -> <return type>:
        """
        <What this method does.>

        Args:
        ----
            <param>: <description>.

        Returns:
        -------
            <description>.

        Raises:
        ------
            ValidationError: <when>.

        """
        ...
```

### Style rules

- `from __future__ import annotations` as first import
- 80 char line length, double quotes
- Full type hints on all parameters and return types
- Docstrings with Args/Returns/Raises sections (numpy style with 4-space indent on section underlines)
- Use `@transaction.atomic` when multiple DB writes need to succeed or fail together
- Raise `django.core.exceptions.ValidationError` for business rule violations

## Register the service

Add the new service to `game/services/__init__.py`:

```python
from .<name>_service import <Name>Service
```

And add it to the `__all__` list.

## Test file

After creating the service, use the `/gen-test` conventions to create `tests/test_<name>_service.py`. At minimum, test every public method with both a success case and an error/edge case.

## After writing

Run the tests to verify everything works:

```bash
uv run python manage.py test tests.test_<name>_service
```

Fix any failures before presenting to the user.
