# Pre-generate Shikona Pool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pre-generate a pool of shikona so heya name selection and rikishi generation are instant instead of waiting for OpenAI API calls.

**Architecture:** Add `is_available`, `reserved_at`, `reserved_by` fields to the existing `Shikona` model. All pool logic lives in `ShikonaService` as `@staticmethod` methods. A management command populates the pool. `DraftPoolService` and the heya name view are updated to consume from the pool first, falling back to real-time generation.

**Tech Stack:** Django 5.x, SQLite (dev), OpenAI API (via existing `ShikonaGenerator`), Django `select_for_update()` for concurrency.

**Spec:** `docs/superpowers/specs/2026-03-24-pre-generate-shikona-pool-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `game/models/shikona.py` | Modify | Add `is_available`, `reserved_at`, `reserved_by` fields |
| `game/migrations/NNNN_add_shikona_pool_fields.py` | Create (auto) | Migration for new fields |
| `libs/constants.py` | Modify | Add `SHIKONA_RESERVATION_TTL_MINUTES` constant |
| `game/services/shikona_service.py` | Modify | Add pool methods, update existing methods |
| `game/views.py` | Modify | Pass `request.user` to service, handle reservation flow |
| `libs/generators/rikishi.py` | Modify | Add optional `shikona` param to `get()` |
| `game/services/draft_pool_service.py` | Modify | Use pool before generator |
| `game/management/commands/generate_shikona_pool.py` | Create | Management command to populate pool |
| `tests/test_shikona_service.py` | Create | Tests for pool methods |
| `tests/test_draft_pool_service.py` | Create | Tests for updated draft pool |
| `tests/test_generate_shikona_pool_command.py` | Create | Tests for management command |

---

## Task 1: Add Pool Fields to Shikona Model

**Files:**
- Modify: `game/models/shikona.py`
- Modify: `libs/constants.py`
- Create (auto): `game/migrations/NNNN_add_shikona_pool_fields.py`
- Test: `tests/test_shikona_model.py`

- [ ] **Step 1: Write failing tests for new fields**

Add to `tests/test_shikona_model.py`:

```python
from accounts.models import User


class ShikonaPoolFieldTests(TestCase):
    """Tests for shikona pool fields."""

    def test_is_available_defaults_true(self) -> None:
        """New shikona should default to is_available=True."""
        shikona = Shikona.objects.create(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )
        self.assertTrue(shikona.is_available)

    def test_reserved_at_defaults_null(self) -> None:
        """New shikona should have reserved_at=None."""
        shikona = Shikona.objects.create(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )
        self.assertIsNone(shikona.reserved_at)

    def test_reserved_by_defaults_null(self) -> None:
        """New shikona should have reserved_by=None."""
        shikona = Shikona.objects.create(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )
        self.assertIsNone(shikona.reserved_by)

    def test_reserved_by_user_deletion_sets_null(self) -> None:
        """Deleting the reserving user should set reserved_by to None."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        shikona = Shikona.objects.create(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
            reserved_by=user,
        )
        user.delete()
        shikona.refresh_from_db()
        self.assertIsNone(shikona.reserved_by)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_model.ShikonaPoolFieldTests -v 2`
Expected: Errors about missing `is_available`, `reserved_at`, `reserved_by` fields.

- [ ] **Step 3: Add constant for reservation TTL**

In `libs/constants.py`, add at the end:

```python
# Shikona pool constants
SHIKONA_RESERVATION_TTL_MINUTES: Final[int] = 5
```

- [ ] **Step 4: Add fields to Shikona model**

In `game/models/shikona.py`, add these imports at the top:

```python
from django.conf import settings
```

Add these fields to the `Shikona` class, after the `parent` field:

```python
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this shikona is available in the pool.",
    )
    reserved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this shikona was reserved for selection.",
    )
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reserved_shikona",
        help_text="User who reserved this shikona.",
    )
```

- [ ] **Step 5: Create migration**

Run: `uv run python manage.py makemigrations game -n add_shikona_pool_fields`

**Important:** The migration must default `is_available=False` for existing rows. After auto-generation, edit the migration to use a `RunPython` operation that sets existing rows to `is_available=False`. The field default is `True` (for new pool entries), but existing shikona are already assigned. Add after the field additions:

```python
def set_existing_shikona_unavailable(apps, schema_editor):
    """Mark all pre-existing shikona as unavailable (already assigned)."""
    Shikona = apps.get_model("game", "Shikona")
    Shikona.objects.all().update(is_available=False)

# In the operations list, after the AddField operations:
migrations.RunPython(
    set_existing_shikona_unavailable,
    migrations.RunPython.noop,
),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_model.ShikonaPoolFieldTests -v 2`
Expected: All 4 tests PASS.

- [ ] **Step 7: Run full test suite**

Run: `./test.sh`
Expected: All existing tests still pass. Coverage does not decrease.

- [ ] **Step 8: Commit**

```bash
git add game/models/shikona.py game/migrations/ libs/constants.py tests/test_shikona_model.py
git commit -m "feat(shikona): add pool fields (is_available, reserved_at, reserved_by)

Add fields to support pre-generated shikona pool with reservation
system. Existing shikona are marked as unavailable via data migration."
```

---

## Task 2: Add Pool Methods to ShikonaService

**Files:**
- Modify: `game/services/shikona_service.py`
- Create: `tests/test_shikona_service.py`

- [ ] **Step 1: Write failing tests for `release_expired_reservations`**

Create `tests/test_shikona_service.py`:

```python
"""Tests for ShikonaService pool methods."""

from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from game.models import Shikona
from game.services.shikona_service import ShikonaService
from libs.constants import SHIKONA_RESERVATION_TTL_MINUTES


def _create_user(
    username: str = "testuser", email: str = "test@example.com"
) -> User:
    """Create a test user."""
    return User.objects.create_user(
        username=username, email=email, password="testpass123"
    )


def _create_pool_shikona(
    name: str,
    transliteration: str,
    interpretation: str = "Test meaning",
    is_available: bool = True,
    reserved_at: timezone.datetime | None = None,
    reserved_by: User | None = None,
) -> Shikona:
    """Create a shikona in the pool."""
    return Shikona.objects.create(
        name=name,
        transliteration=transliteration,
        interpretation=interpretation,
        is_available=is_available,
        reserved_at=reserved_at,
        reserved_by=reserved_by,
    )


class ReleaseExpiredReservationsTests(TestCase):
    """Tests for ShikonaService.release_expired_reservations."""

    def test_releases_expired_reservations(self) -> None:
        """Should clear reservations older than TTL."""
        user = _create_user()
        expired_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        shikona = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=expired_time,
            reserved_by=user,
        )

        count = ShikonaService.release_expired_reservations()

        self.assertEqual(count, 1)
        shikona.refresh_from_db()
        self.assertIsNone(shikona.reserved_at)
        self.assertIsNone(shikona.reserved_by)

    def test_does_not_release_fresh_reservations(self) -> None:
        """Should keep reservations within TTL."""
        user = _create_user()
        fresh_time = timezone.now() - timedelta(minutes=1)
        shikona = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=fresh_time,
            reserved_by=user,
        )

        count = ShikonaService.release_expired_reservations()

        self.assertEqual(count, 0)
        shikona.refresh_from_db()
        self.assertIsNotNone(shikona.reserved_at)

    def test_does_not_touch_consumed_shikona(self) -> None:
        """Should not release consumed shikona even with old reserved_at."""
        user = _create_user()
        expired_time = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        shikona = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            is_available=False,
            reserved_at=expired_time,
            reserved_by=user,
        )

        count = ShikonaService.release_expired_reservations()

        self.assertEqual(count, 0)
        shikona.refresh_from_db()
        self.assertFalse(shikona.is_available)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_service.ReleaseExpiredReservationsTests -v 2`
Expected: AttributeError — `ShikonaService` has no `release_expired_reservations`.

- [ ] **Step 3: Implement `release_expired_reservations`**

In `game/services/shikona_service.py`, add imports at top:

```python
from datetime import timedelta

from django.utils import timezone

from libs.constants import SHIKONA_RESERVATION_TTL_MINUTES
```

Add to `ShikonaService` class:

```python
    @staticmethod
    def release_expired_reservations() -> int:
        """
        Clear reservations older than the TTL.

        Called lazily before fetching pool options. Only affects
        available shikona (not consumed ones).

        Returns:
        -------
            Number of reservations released.

        """
        cutoff = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES
        )
        count = Shikona.objects.filter(
            is_available=True,
            reserved_at__isnull=False,
            reserved_at__lt=cutoff,
        ).update(reserved_at=None, reserved_by=None)
        return count
```

Note: `Shikona` import is already present as `ShikonaModel` — use that alias consistently. The import line is `from game.models import Shikona as ShikonaModel`. Update references accordingly (use `ShikonaModel` instead of `Shikona` in the new methods).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_service.ReleaseExpiredReservationsTests -v 2`
Expected: All 3 tests PASS.

- [ ] **Step 5: Write failing tests for `get_available_shikona`**

Add to `tests/test_shikona_service.py`:

```python
class GetAvailableShikonaTests(TestCase):
    """Tests for ShikonaService.get_available_shikona."""

    def test_returns_available_unreserved_shikona(self) -> None:
        """Should return shikona that are available and not reserved."""
        s1 = _create_pool_shikona(
            name="豊山", transliteration="Toyoyama"
        )
        s2 = _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka"
        )

        result = ShikonaService.get_available_shikona(count=2)

        self.assertEqual(len(result), 2)
        ids = {s.id for s in result}
        self.assertIn(s1.id, ids)
        self.assertIn(s2.id, ids)

    def test_excludes_consumed_shikona(self) -> None:
        """Should not return consumed shikona."""
        _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            is_available=False,
        )
        s2 = _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka"
        )

        result = ShikonaService.get_available_shikona(count=2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, s2.id)

    def test_excludes_freshly_reserved_shikona(self) -> None:
        """Should not return shikona with active reservations."""
        user = _create_user()
        _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=timezone.now(),
            reserved_by=user,
        )
        s2 = _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka"
        )

        result = ShikonaService.get_available_shikona(count=2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, s2.id)

    def test_includes_expired_reservations(self) -> None:
        """Should return shikona with expired reservations."""
        user = _create_user()
        expired = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        s1 = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=expired,
            reserved_by=user,
        )

        result = ShikonaService.get_available_shikona(count=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, s1.id)

    def test_returns_fewer_if_pool_insufficient(self) -> None:
        """Should return available count when less than requested."""
        _create_pool_shikona(
            name="豊山", transliteration="Toyoyama"
        )

        result = ShikonaService.get_available_shikona(count=5)

        self.assertEqual(len(result), 1)

    def test_returns_empty_when_pool_empty(self) -> None:
        """Should return empty list when no shikona available."""
        result = ShikonaService.get_available_shikona(count=3)

        self.assertEqual(result, [])
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_service.GetAvailableShikonaTests -v 2`
Expected: AttributeError — `ShikonaService` has no `get_available_shikona`.

- [ ] **Step 7: Implement `get_available_shikona`**

Add to `ShikonaService` in `game/services/shikona_service.py`:

```python
    @staticmethod
    def get_available_shikona(count: int = 1) -> list[ShikonaModel]:
        """
        Return random available, non-reserved shikona from the pool.

        Filters for shikona that are available and either not reserved
        or have an expired reservation (older than TTL).

        Args:
        ----
            count: Number of shikona to return.

        Returns:
        -------
            List of available Shikona instances (may be fewer than
            requested if pool is insufficient).

        """
        cutoff = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES
        )
        return list(
            ShikonaModel.objects.filter(
                is_available=True,
            )
            .filter(
                models.Q(reserved_at__isnull=True)
                | models.Q(reserved_at__lt=cutoff)
            )
            .order_by("?")[:count]
        )
```

Add `from django.db import models` to imports if not already present.

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_service.GetAvailableShikonaTests -v 2`
Expected: All 6 tests PASS.

- [ ] **Step 9: Write failing tests for `reserve_shikona`**

Add to `tests/test_shikona_service.py`:

```python
class ReserveShikonaTests(TestCase):
    """Tests for ShikonaService.reserve_shikona."""

    def test_reserves_available_shikona(self) -> None:
        """Should set reserved_at and reserved_by on available shikona."""
        user = _create_user()
        s1 = _create_pool_shikona(
            name="豊山", transliteration="Toyoyama"
        )
        s2 = _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka"
        )

        result = ShikonaService.reserve_shikona(
            [s1.id, s2.id], user
        )

        self.assertEqual(len(result), 2)
        s1.refresh_from_db()
        s2.refresh_from_db()
        self.assertIsNotNone(s1.reserved_at)
        self.assertEqual(s1.reserved_by, user)
        self.assertIsNotNone(s2.reserved_at)
        self.assertEqual(s2.reserved_by, user)

    def test_skips_already_consumed_shikona(self) -> None:
        """Should skip shikona that are no longer available."""
        user = _create_user()
        consumed = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            is_available=False,
        )
        available = _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka"
        )

        result = ShikonaService.reserve_shikona(
            [consumed.id, available.id], user
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, available.id)

    def test_skips_already_reserved_shikona(self) -> None:
        """Should skip shikona reserved by another user."""
        user1 = _create_user(username="user1", email="u1@example.com")
        user2 = _create_user(username="user2", email="u2@example.com")
        reserved = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=timezone.now(),
            reserved_by=user1,
        )
        available = _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka"
        )

        result = ShikonaService.reserve_shikona(
            [reserved.id, available.id], user2
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, available.id)
```

- [ ] **Step 10: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_service.ReserveShikonaTests -v 2`
Expected: AttributeError — `ShikonaService` has no `reserve_shikona`.

- [ ] **Step 11: Implement `reserve_shikona`**

Add to `ShikonaService`:

```python
    @staticmethod
    def reserve_shikona(
        shikona_ids: list[int], user: User
    ) -> list[ShikonaModel]:
        """
        Reserve shikona for a user's heya name selection.

        Uses select_for_update() to prevent race conditions. Only
        reserves shikona that are still available and not freshly
        reserved by another user.

        Args:
        ----
            shikona_ids: IDs of shikona to reserve.
            user: The user reserving the shikona.

        Returns:
        -------
            List of successfully reserved Shikona instances.

        """
        from django.db import transaction

        cutoff = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES
        )
        reserved: list[ShikonaModel] = []

        with transaction.atomic():
            candidates = list(
                ShikonaModel.objects.select_for_update()
                .filter(
                    id__in=shikona_ids,
                    is_available=True,
                )
                .filter(
                    models.Q(reserved_at__isnull=True)
                    | models.Q(reserved_at__lt=cutoff)
                )
            )
            now = timezone.now()
            for shikona in candidates:
                shikona.reserved_at = now
                shikona.reserved_by = user
                shikona.save(
                    update_fields=["reserved_at", "reserved_by"]
                )
                reserved.append(shikona)

        return reserved
```

Add `from accounts.models import User` to the imports at the top of the file.

- [ ] **Step 12: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_service.ReserveShikonaTests -v 2`
Expected: All 3 tests PASS.

- [ ] **Step 13: Write failing tests for `release_reservation` and `consume_shikona`**

Add to `tests/test_shikona_service.py`:

```python
class ReleaseReservationTests(TestCase):
    """Tests for ShikonaService.release_reservation."""

    def test_releases_user_reservations(self) -> None:
        """Should clear reservations for the specified user."""
        user = _create_user()
        s1 = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=timezone.now(),
            reserved_by=user,
        )
        s2 = _create_pool_shikona(
            name="白鷹",
            transliteration="Hakutaka",
            reserved_at=timezone.now(),
            reserved_by=user,
        )

        ShikonaService.release_reservation(user)

        s1.refresh_from_db()
        s2.refresh_from_db()
        self.assertIsNone(s1.reserved_at)
        self.assertIsNone(s1.reserved_by)
        self.assertIsNone(s2.reserved_at)
        self.assertIsNone(s2.reserved_by)

    def test_does_not_release_other_user_reservations(self) -> None:
        """Should only release the specified user's reservations."""
        user1 = _create_user(username="user1", email="u1@example.com")
        user2 = _create_user(username="user2", email="u2@example.com")
        s1 = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=timezone.now(),
            reserved_by=user1,
        )
        s2 = _create_pool_shikona(
            name="白鷹",
            transliteration="Hakutaka",
            reserved_at=timezone.now(),
            reserved_by=user2,
        )

        ShikonaService.release_reservation(user1)

        s1.refresh_from_db()
        s2.refresh_from_db()
        self.assertIsNone(s1.reserved_at)
        self.assertIsNotNone(s2.reserved_at)
        self.assertEqual(s2.reserved_by, user2)


class ConsumeShikonaTests(TestCase):
    """Tests for ShikonaService.consume_shikona."""

    def test_marks_shikona_unavailable(self) -> None:
        """Should set is_available=False and clear reservation."""
        user = _create_user()
        shikona = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=timezone.now(),
            reserved_by=user,
        )

        ShikonaService.consume_shikona(shikona)

        shikona.refresh_from_db()
        self.assertFalse(shikona.is_available)
        self.assertIsNone(shikona.reserved_at)
        self.assertIsNone(shikona.reserved_by)

    def test_works_on_unreserved_shikona(self) -> None:
        """Should consume even if not reserved (e.g. rikishi generation)."""
        shikona = _create_pool_shikona(
            name="豊山", transliteration="Toyoyama"
        )

        ShikonaService.consume_shikona(shikona)

        shikona.refresh_from_db()
        self.assertFalse(shikona.is_available)
```

- [ ] **Step 14: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_service.ReleaseReservationTests tests.test_shikona_service.ConsumeShikonaTests -v 2`
Expected: AttributeError for missing methods.

- [ ] **Step 15: Implement `release_reservation` and `consume_shikona`**

Add to `ShikonaService`:

```python
    @staticmethod
    def release_reservation(user: User) -> None:
        """
        Clear reservation fields for all shikona reserved by a user.

        Called when user navigates away or requests new options.

        Args:
        ----
            user: The user whose reservations to release.

        """
        ShikonaModel.objects.filter(
            reserved_by=user,
            is_available=True,
        ).update(reserved_at=None, reserved_by=None)

    @staticmethod
    def consume_shikona(shikona: ShikonaModel) -> None:
        """
        Mark a shikona as permanently used.

        Sets is_available=False and clears reservation fields.

        Args:
        ----
            shikona: The shikona to consume.

        """
        shikona.is_available = False
        shikona.reserved_at = None
        shikona.reserved_by = None
        shikona.save(
            update_fields=[
                "is_available",
                "reserved_at",
                "reserved_by",
            ]
        )
```

- [ ] **Step 16: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_service.ReleaseReservationTests tests.test_shikona_service.ConsumeShikonaTests -v 2`
Expected: All 4 tests PASS.

- [ ] **Step 17: Run full test suite**

Run: `./test.sh`
Expected: All tests pass. Coverage does not decrease.

- [ ] **Step 18: Commit**

```bash
git add game/services/shikona_service.py tests/test_shikona_service.py
git commit -m "feat(shikona): add pool methods to ShikonaService

Add get_available_shikona, reserve_shikona, release_reservation,
consume_shikona, and release_expired_reservations static methods."
```

---

## Task 3: Update `generate_shikona_options` to Use Pool

**Files:**
- Modify: `game/services/shikona_service.py`
- Modify: `game/views.py`
- Modify: `tests/test_shikona_service.py`

- [ ] **Step 1: Write failing tests for updated `generate_shikona_options`**

Add to `tests/test_shikona_service.py`:

```python
from unittest.mock import MagicMock, patch


class GenerateShikonaOptionsPoolTests(TestCase):
    """Tests for generate_shikona_options using pool."""

    def test_uses_pool_when_available(self) -> None:
        """Should return options from pool without calling OpenAI."""
        user = _create_user()
        _create_pool_shikona(
            name="豊山", transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )
        _create_pool_shikona(
            name="白鷹", transliteration="Hakutaka",
            interpretation="White Hawk",
        )
        _create_pool_shikona(
            name="青龍", transliteration="Seiryu",
            interpretation="Blue Dragon",
        )

        options = ShikonaService.generate_shikona_options(
            count=3, user=user
        )

        self.assertEqual(len(options), 3)
        # Verify shikona are now reserved
        reserved = Shikona.objects.filter(
            reserved_by=user,
            reserved_at__isnull=False,
        )
        self.assertEqual(reserved.count(), 3)

    @patch(
        "game.services.shikona_service.ShikonaGenerator"
    )
    def test_falls_back_to_openai_when_pool_empty(
        self, mock_gen_class: MagicMock
    ) -> None:
        """Should generate via OpenAI when pool is empty."""
        user = _create_user()
        from libs.types.shikona import Shikona as ShikonaType

        mock_gen = mock_gen_class.return_value
        mock_gen.generate_single.return_value = ShikonaType(
            shikona="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )

        options = ShikonaService.generate_shikona_options(
            count=1, user=user
        )

        self.assertEqual(len(options), 1)
        mock_gen.generate_single.assert_called()

    def test_releases_expired_before_fetching(self) -> None:
        """Should release expired reservations before querying pool."""
        user1 = _create_user(
            username="user1", email="u1@example.com"
        )
        user2 = _create_user(
            username="user2", email="u2@example.com"
        )
        expired = timezone.now() - timedelta(
            minutes=SHIKONA_RESERVATION_TTL_MINUTES + 1
        )
        _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            reserved_at=expired,
            reserved_by=user1,
        )

        options = ShikonaService.generate_shikona_options(
            count=1, user=user2
        )

        # The expired reservation should have been released
        # and the shikona should be available
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].name, "豊山")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_service.GenerateShikonaOptionsPoolTests -v 2`
Expected: TypeError — `generate_shikona_options()` got unexpected keyword argument `user`.

- [ ] **Step 3: Update `generate_shikona_options` signature and implementation**

Replace the current `generate_shikona_options` method in `game/services/shikona_service.py` with:

```python
    @staticmethod
    def generate_shikona_options(
        count: int = 3,
        user: User | None = None,
    ) -> list[ShikonaOption]:
        """
        Generate unique shikona options for heya name selection.

        First tries to select from the pre-generated pool. If pool
        has enough available shikona, reserves them for the user.
        Falls back to real-time OpenAI generation if pool is empty.

        Args:
        ----
            count: Number of unique options to generate (default: 3).
            user: The user requesting options (for reservation).

        Returns:
        -------
            List of ShikonaOption instances with unique names.
            May return fewer than requested if generation fails.

        """
        # Release expired reservations first
        ShikonaService.release_expired_reservations()

        # If user provided, release their previous reservations
        if user is not None:
            ShikonaService.release_reservation(user)

        # Try pool first
        pool_shikona = ShikonaService.get_available_shikona(count)
        if pool_shikona and user is not None:
            reserved = ShikonaService.reserve_shikona(
                [s.id for s in pool_shikona], user
            )
            if reserved:
                return [
                    ShikonaOption(
                        name=s.name,
                        transliteration=s.transliteration,
                        interpretation=s.interpretation,
                    )
                    for s in reserved
                ]

        # Fall back to real-time generation
        options: list[ShikonaOption] = []
        existing_names = set(
            ShikonaModel.objects.values_list("name", flat=True)
        )
        existing_translit = set(
            ShikonaModel.objects.values_list(
                "transliteration", flat=True
            )
        )

        generator = ShikonaGenerator()
        max_attempts = count * 3

        for _ in range(max_attempts):
            if len(options) >= count:
                break

            try:
                shikona = generator.generate_single()
                if (
                    shikona.shikona not in existing_names
                    and shikona.transliteration not in existing_translit
                    and shikona.shikona
                    not in {opt.name for opt in options}
                ):
                    options.append(
                        ShikonaOption(
                            name=shikona.shikona,
                            transliteration=shikona.transliteration,
                            interpretation=shikona.interpretation,
                        )
                    )
                    logger.info(
                        "Generated shikona option: %s (%s)",
                        shikona.shikona,
                        shikona.transliteration,
                    )
            except ShikonaGenerationError as e:
                logger.warning("Failed to generate shikona: %s", e)
                continue

        if len(options) < count:
            logger.warning(
                "Could only generate %d/%d shikona options",
                len(options),
                count,
            )

        return options
```

Add `from __future__ import annotations` at the top of the file if not already present (needed for `User | None` syntax).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_service.GenerateShikonaOptionsPoolTests -v 2`
Expected: All 3 tests PASS.

- [ ] **Step 5: Write failing tests for updated `create_shikona_from_option`**

Add to `tests/test_shikona_service.py`:

```python
class CreateShikonaFromOptionPoolTests(TestCase):
    """Tests for create_shikona_from_option with pool shikona."""

    def test_consumes_pregenerated_shikona(self) -> None:
        """Should consume pre-generated shikona and release others."""
        user = _create_user()
        s1 = _create_pool_shikona(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
            reserved_at=timezone.now(),
            reserved_by=user,
        )
        s2 = _create_pool_shikona(
            name="白鷹",
            transliteration="Hakutaka",
            interpretation="White Hawk",
            reserved_at=timezone.now(),
            reserved_by=user,
        )
        option = ShikonaOption(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )

        result = ShikonaService.create_shikona_from_option(
            option, user=user
        )

        self.assertEqual(result.id, s1.id)
        s1.refresh_from_db()
        self.assertFalse(s1.is_available)
        # Other reservation should be released
        s2.refresh_from_db()
        self.assertIsNone(s2.reserved_at)
        self.assertIsNone(s2.reserved_by)

    def test_creates_new_shikona_when_not_in_pool(self) -> None:
        """Should create new shikona if not from pool."""
        option = ShikonaOption(
            name="新星",
            transliteration="Shinsei",
            interpretation="New Star",
        )

        result = ShikonaService.create_shikona_from_option(option)

        self.assertEqual(result.name, "新星")
        self.assertFalse(result.is_available)
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_shikona_service.CreateShikonaFromOptionPoolTests -v 2`
Expected: TypeError — `create_shikona_from_option()` got unexpected keyword argument `user`.

- [ ] **Step 7: Update `create_shikona_from_option`**

Replace the existing method:

```python
    @staticmethod
    def create_shikona_from_option(
        option: ShikonaOption,
        user: User | None = None,
    ) -> ShikonaModel:
        """
        Create or retrieve a Shikona model from a ShikonaOption.

        If the option matches a pre-generated shikona, consumes it
        and releases the user's other reservations. Otherwise creates
        a new shikona marked as consumed.

        Args:
        ----
            option: The ShikonaOption to persist.
            user: The user selecting the option (for releasing
                other reservations).

        Returns:
        -------
            The Shikona instance.

        """
        # Check if this is a pre-generated shikona
        existing = ShikonaModel.objects.filter(
            name=option.name,
            is_available=True,
        ).first()

        if existing is not None:
            ShikonaService.consume_shikona(existing)
            if user is not None:
                ShikonaService.release_reservation(user)
            return existing

        # Create new shikona (from OpenAI fallback)
        shikona = ShikonaModel.objects.create(
            name=option.name,
            transliteration=option.transliteration,
            interpretation=option.interpretation,
            is_available=False,
        )
        if user is not None:
            ShikonaService.release_reservation(user)
        return shikona
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_shikona_service.CreateShikonaFromOptionPoolTests -v 2`
Expected: All 2 tests PASS.

- [ ] **Step 9: Update view to pass `request.user`**

In `game/views.py`, update line 42 (inside `setup_heya_name`):

Change:
```python
        options = ShikonaService.generate_shikona_options(count=3)
```
To:
```python
        options = ShikonaService.generate_shikona_options(
            count=3, user=request.user
        )
```

In `_handle_heya_name_selection` (around line 84), the view currently calls `Shikona.objects.get_or_create()` directly. Update it to use `ShikonaService.create_shikona_from_option()` instead:

Change lines 83-90:
```python
        # Create or get the Shikona (handles race condition)
        shikona, _ = Shikona.objects.get_or_create(
            name=selected["name"],
            defaults={
                "transliteration": selected["transliteration"],
                "interpretation": selected["interpretation"],
            },
        )
```
To:
```python
        # Create or consume from pool
        shikona = ShikonaService.create_shikona_from_option(
            ShikonaOption(
                name=selected["name"],
                transliteration=selected["transliteration"],
                interpretation=selected["interpretation"],
            ),
            user=request.user,
        )
```

Add `ShikonaOption` to the import from `shikona_service`:
```python
from game.services.shikona_service import ShikonaOption, ShikonaService
```

- [ ] **Step 10: Run full test suite**

Run: `./test.sh`
Expected: All tests pass. Coverage does not decrease.

- [ ] **Step 11: Commit**

```bash
git add game/services/shikona_service.py game/views.py tests/test_shikona_service.py
git commit -m "feat(shikona): update heya name flow to use pool with reservation

generate_shikona_options now draws from pool first with user reservation.
create_shikona_from_option consumes pool shikona and releases others.
View updated to pass request.user through to service."
```

---

## Task 4: Update RikishiGenerator and DraftPoolService

**Files:**
- Modify: `libs/generators/rikishi.py`
- Modify: `game/services/draft_pool_service.py`
- Create: `tests/test_draft_pool_service.py`

- [ ] **Step 1: Write failing test for `RikishiGenerator.get()` with optional shikona**

Add to existing `tests/test_rikishi_generator.py` (or create if needed — check first):

```python
class RikishiGeneratorShikonaParamTests(unittest.TestCase):
    """Tests for RikishiGenerator.get() with pre-fetched shikona."""

    @patch("libs.generators.rikishi.ShikonaGenerator")
    @patch("libs.generators.rikishi.ShusshinGenerator")
    def test_uses_provided_shikona(
        self, mock_shusshin_cls: MagicMock, mock_shikona_cls: MagicMock
    ) -> None:
        """Should use provided shikona instead of generating one."""
        from libs.types.shikona import Shikona as ShikonaType
        from libs.types.shusshin import Shusshin as ShusshinType

        mock_shusshin_cls.return_value.get.return_value = ShusshinType(
            country_code="JP", jp_prefecture="Tokyo"
        )

        pre_made = ShikonaType(
            shikona="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )

        generator = RikishiGenerator(seed=42)
        result = generator.get(shikona=pre_made)

        self.assertEqual(result.shikona.shikona, "豊山")
        # Should NOT have called shikona generator
        mock_shikona_cls.return_value.generate_single.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python manage.py test tests.test_rikishi_generator.RikishiGeneratorShikonaParamTests -v 2`
Expected: TypeError — `get()` got unexpected keyword argument `shikona`.

- [ ] **Step 3: Add optional shikona parameter to `RikishiGenerator.get()`**

In `libs/generators/rikishi.py`, update the `get` method signature and body:

```python
    def get(self, shikona: Shikona | None = None) -> Rikishi:
        """
        Generate a complete rikishi with all attributes.

        Args:
            shikona: Optional pre-generated shikona to use.

        Returns:
            Rikishi with shikona, shusshin, abilities, and stats.

        """
        shusshin = self.shusshin_generator.get()
        if shikona is None:
            shikona = self.shikona_generator.generate_single(
                shusshin=str(shusshin)
            )
        potential = self._get_potential_ability()
        current = self._get_current_ability(potential)
        rikishi = Rikishi(
            shikona=shikona,
            shusshin=shusshin,
            potential=potential,
            current=current,
        )
        points_to_distribute = current - (MIN_STAT_VALUE * NUM_STATS)
        return self._distribute_stats(rikishi, points_to_distribute)
```

Add `Shikona` to the imports from `libs.types`:
```python
from libs.types.shikona import Shikona
```

Note: `Shikona` here is the Pydantic type, not the Django model. The existing `from libs.types.rikishi import Rikishi` is separate.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python manage.py test tests.test_rikishi_generator.RikishiGeneratorShikonaParamTests -v 2`
Expected: PASS.

- [ ] **Step 5: Write failing tests for `DraftPoolService` using pool**

Create `tests/test_draft_pool_service.py`:

```python
"""Tests for DraftPoolService with shikona pool integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import TestCase

from game.models import Shikona
from game.services.draft_pool_service import DraftPoolService


def _create_pool_shikona(
    name: str,
    transliteration: str,
    interpretation: str = "Test meaning",
) -> Shikona:
    """Create an available shikona in the pool."""
    return Shikona.objects.create(
        name=name,
        transliteration=transliteration,
        interpretation=interpretation,
        is_available=True,
    )


class DraftPoolServicePoolTests(TestCase):
    """Tests for generate_draft_pool using shikona pool."""

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_uses_pool_shikona(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should consume pool shikona for rikishi generation."""
        from libs.types.rikishi import Rikishi
        from libs.types.shikona import Shikona as ShikonaType
        from libs.types.shusshin import Shusshin as ShusshinType

        s1 = _create_pool_shikona(
            name="豊山", transliteration="Toyoyama"
        )

        mock_gen = mock_gen_cls.return_value
        mock_gen.get.return_value = Rikishi(
            shikona=ShikonaType(
                shikona="豊山",
                transliteration="Toyoyama",
                interpretation="Test meaning",
            ),
            shusshin=ShusshinType(
                country_code="JP", jp_prefecture="Tokyo"
            ),
            potential=50,
            current=10,
            strength=3,
            technique=2,
            balance=2,
            endurance=2,
            mental=1,
        )

        pool = DraftPoolService.generate_draft_pool(count=1)

        self.assertEqual(len(pool), 1)
        # Verify shikona was consumed
        s1.refresh_from_db()
        self.assertFalse(s1.is_available)
        # Verify shikona was passed to generator
        call_kwargs = mock_gen.get.call_args
        self.assertIsNotNone(call_kwargs[1].get("shikona"))

    @patch("game.services.draft_pool_service.RikishiGenerator")
    def test_falls_back_when_pool_empty(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should use generator without pool shikona when empty."""
        from libs.types.rikishi import Rikishi
        from libs.types.shikona import Shikona as ShikonaType
        from libs.types.shusshin import Shusshin as ShusshinType

        mock_gen = mock_gen_cls.return_value
        mock_gen.get.return_value = Rikishi(
            shikona=ShikonaType(
                shikona="新星",
                transliteration="Shinsei",
                interpretation="New Star",
            ),
            shusshin=ShusshinType(
                country_code="JP", jp_prefecture="Tokyo"
            ),
            potential=50,
            current=10,
            strength=3,
            technique=2,
            balance=2,
            endurance=2,
            mental=1,
        )

        pool = DraftPoolService.generate_draft_pool(count=1)

        self.assertEqual(len(pool), 1)
        # Verify generator was called without shikona param
        call_kwargs = mock_gen.get.call_args
        self.assertIsNone(call_kwargs[1].get("shikona"))
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_draft_pool_service -v 2`
Expected: Tests fail because `DraftPoolService` doesn't use pool yet.

- [ ] **Step 7: Update `DraftPoolService.generate_draft_pool()` to use pool**

In `game/services/draft_pool_service.py`, add imports:

```python
from game.services.shikona_service import ShikonaService
from libs.types.shikona import Shikona as ShikonaType
```

Replace the `generate_draft_pool` method:

```python
    @staticmethod
    def generate_draft_pool(count: int = 6) -> list[DraftPoolRikishi]:
        """
        Generate a pool of wrestler candidates for drafting.

        Uses pre-generated shikona from the pool when available,
        falling back to real-time generation via RikishiGenerator.

        Args:
        ----
            count: Number of wrestlers to generate (default: 6).

        Returns:
        -------
            List of DraftPoolRikishi instances ready for display.

        """
        pool: list[DraftPoolRikishi] = []
        generator = RikishiGenerator()

        # Get existing shikona names to avoid duplicates
        existing_names = set(
            Shikona.objects.values_list("name", flat=True)
        )

        # Try to get shikona from the pool
        pool_shikona = ShikonaService.get_available_shikona(count)
        pool_shikona_iter = iter(pool_shikona)

        max_attempts = count * DraftPoolService.MAX_ATTEMPTS_MULTIPLIER

        for _ in range(max_attempts):
            if len(pool) >= count:
                break

            try:
                # Use pool shikona if available
                pre_made = next(pool_shikona_iter, None)
                shikona_arg: ShikonaType | None = None
                if pre_made is not None:
                    ShikonaService.consume_shikona(pre_made)
                    shikona_arg = ShikonaType(
                        shikona=pre_made.name,
                        transliteration=pre_made.transliteration,
                        interpretation=pre_made.interpretation,
                    )

                rikishi = generator.get(shikona=shikona_arg)

                # Check uniqueness against DB and current pool
                if (
                    rikishi.shikona.shikona not in existing_names
                    and rikishi.shikona.shikona
                    not in {r.shikona_name for r in pool}
                ):
                    pool.append(
                        DraftPoolRikishi(
                            shikona_name=rikishi.shikona.shikona,
                            shikona_transliteration=(
                                rikishi.shikona.transliteration
                            ),
                            shikona_interpretation=(
                                rikishi.shikona.interpretation
                            ),
                            shusshin_country_code=(
                                rikishi.shusshin.country_code
                            ),
                            shusshin_jp_prefecture=(
                                rikishi.shusshin.jp_prefecture
                            ),
                            shusshin_display=str(rikishi.shusshin),
                            potential=rikishi.potential,
                            potential_tier=(
                                DraftPoolService.get_potential_tier(
                                    rikishi.potential
                                )
                            ),
                            strength=rikishi.strength,
                            technique=rikishi.technique,
                            balance=rikishi.balance,
                            endurance=rikishi.endurance,
                            mental=rikishi.mental,
                        )
                    )
                    logger.info(
                        "Generated draft candidate: %s (%s)",
                        rikishi.shikona.shikona,
                        rikishi.shikona.transliteration,
                    )
            except Exception as e:
                logger.warning(
                    "Failed to generate draft candidate: %s", e
                )
                continue

        if len(pool) < count:
            logger.warning(
                "Could only generate %d/%d draft candidates",
                len(pool),
                count,
            )

        return pool
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_draft_pool_service -v 2`
Expected: All tests PASS.

- [ ] **Step 9: Run full test suite**

Run: `./test.sh`
Expected: All tests pass. Coverage does not decrease.

- [ ] **Step 10: Commit**

```bash
git add libs/generators/rikishi.py game/services/draft_pool_service.py tests/test_draft_pool_service.py tests/test_rikishi_generator.py
git commit -m "feat(draft-pool): use shikona pool for rikishi generation

DraftPoolService now draws from pre-generated pool first.
RikishiGenerator.get() accepts optional shikona parameter."
```

---

## Task 5: Create Management Command

**Files:**
- Create: `game/management/commands/generate_shikona_pool.py`
- Create: `tests/test_generate_shikona_pool_command.py`

- [ ] **Step 1: Write failing tests for the management command**

Create `tests/test_generate_shikona_pool_command.py`:

```python
"""Tests for the generate_shikona_pool management command."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from game.models import Shikona
from libs.types.shikona import Shikona as ShikonaType


class GenerateShikonaPoolCommandTests(TestCase):
    """Tests for generate_shikona_pool command."""

    @patch("game.management.commands.generate_shikona_pool.ShikonaGenerator")
    def test_creates_shikona_with_is_available_true(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should create shikona marked as available."""
        mock_gen = mock_gen_cls.return_value
        mock_gen.generate_single.return_value = ShikonaType(
            shikona="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )

        out = StringIO()
        call_command(
            "generate_shikona_pool", "--count", "1", stdout=out
        )

        self.assertEqual(Shikona.objects.count(), 1)
        shikona = Shikona.objects.first()
        self.assertIsNotNone(shikona)
        self.assertTrue(shikona.is_available)
        self.assertEqual(shikona.name, "豊山")

    @patch("game.management.commands.generate_shikona_pool.ShikonaGenerator")
    def test_respects_count_parameter(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should generate the requested number of shikona."""
        mock_gen = mock_gen_cls.return_value
        shikona_data = [
            ("豊山", "Toyoyama", "Abundant Mountain"),
            ("白鷹", "Hakutaka", "White Hawk"),
            ("青龍", "Seiryu", "Blue Dragon"),
        ]
        mock_gen.generate_single.side_effect = [
            ShikonaType(
                shikona=s[0],
                transliteration=s[1],
                interpretation=s[2],
            )
            for s in shikona_data
        ]

        out = StringIO()
        call_command(
            "generate_shikona_pool", "--count", "3", stdout=out
        )

        self.assertEqual(Shikona.objects.count(), 3)

    @patch("game.management.commands.generate_shikona_pool.ShikonaGenerator")
    def test_skips_duplicate_names(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should skip shikona that already exist in the database."""
        # Pre-existing shikona
        Shikona.objects.create(
            name="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
            is_available=False,
        )

        mock_gen = mock_gen_cls.return_value
        mock_gen.generate_single.side_effect = [
            # First: duplicate
            ShikonaType(
                shikona="豊山",
                transliteration="Toyoyama",
                interpretation="Abundant Mountain",
            ),
            # Second: unique
            ShikonaType(
                shikona="白鷹",
                transliteration="Hakutaka",
                interpretation="White Hawk",
            ),
        ]

        out = StringIO()
        call_command(
            "generate_shikona_pool", "--count", "1", stdout=out
        )

        # Should have created only the new one
        self.assertEqual(Shikona.objects.count(), 2)
        self.assertTrue(
            Shikona.objects.filter(
                name="白鷹", is_available=True
            ).exists()
        )

    @patch("game.management.commands.generate_shikona_pool.ShikonaGenerator")
    def test_handles_generation_failure(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should continue on individual generation failures."""
        from libs.generators.shikona import ShikonaGenerationError

        mock_gen = mock_gen_cls.return_value
        mock_gen.generate_single.side_effect = [
            ShikonaGenerationError("API Error"),
            ShikonaType(
                shikona="白鷹",
                transliteration="Hakutaka",
                interpretation="White Hawk",
            ),
        ]

        out = StringIO()
        call_command(
            "generate_shikona_pool", "--count", "1", stdout=out
        )

        self.assertEqual(Shikona.objects.count(), 1)
        output = out.getvalue()
        self.assertIn("1", output)  # success count

    @patch("game.management.commands.generate_shikona_pool.ShikonaGenerator")
    def test_reports_progress(
        self, mock_gen_cls: MagicMock
    ) -> None:
        """Should show progress output."""
        mock_gen = mock_gen_cls.return_value
        mock_gen.generate_single.return_value = ShikonaType(
            shikona="豊山",
            transliteration="Toyoyama",
            interpretation="Abundant Mountain",
        )

        out = StringIO()
        call_command(
            "generate_shikona_pool", "--count", "1", stdout=out
        )

        output = out.getvalue()
        self.assertIn("1/1", output)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python manage.py test tests.test_generate_shikona_pool_command -v 2`
Expected: `ModuleNotFoundError` or `CommandError` — command doesn't exist yet.

- [ ] **Step 3: Create the management command**

Create `game/management/commands/generate_shikona_pool.py`:

```python
"""Management command to generate a pool of pre-generated shikona."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandParser
from django.db import IntegrityError

from game.models import Shikona
from libs.generators.shikona import ShikonaGenerationError, ShikonaGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Generate a pool of shikona for instant selection."""

    help = "Pre-generate a pool of shikona ring names via OpenAI."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--count",
            type=int,
            default=600,
            help="Number of shikona to generate (default: 600).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Progress report interval (default: 50).",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Execute the command."""
        count: int = options["count"]  # type: ignore[assignment]
        batch_size: int = options["batch_size"]  # type: ignore[assignment]

        generator = ShikonaGenerator()
        existing_names = set(
            Shikona.objects.values_list("name", flat=True)
        )
        existing_translit = set(
            Shikona.objects.values_list("transliteration", flat=True)
        )

        success = 0
        failures = 0
        duplicates = 0
        max_attempts = count * 3  # Allow retries for dupes/failures

        for attempt in range(max_attempts):
            if success >= count:
                break

            try:
                shikona = generator.generate_single()

                # Check for duplicates
                if (
                    shikona.shikona in existing_names
                    or shikona.transliteration in existing_translit
                ):
                    duplicates += 1
                    logger.debug(
                        "Skipping duplicate: %s", shikona.shikona
                    )
                    continue

                # Save to database
                Shikona.objects.create(
                    name=shikona.shikona,
                    transliteration=shikona.transliteration,
                    interpretation=shikona.interpretation,
                    is_available=True,
                )
                existing_names.add(shikona.shikona)
                existing_translit.add(shikona.transliteration)
                success += 1

                if success % batch_size == 0 or success == count:
                    self.stdout.write(
                        f"Generated {success}/{count}..."
                    )

            except ShikonaGenerationError as e:
                failures += 1
                logger.warning(
                    "Failed to generate shikona (attempt %d): %s",
                    attempt + 1,
                    e,
                )
                continue
            except IntegrityError:
                duplicates += 1
                logger.debug(
                    "IntegrityError (race condition duplicate)"
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Success: {success}, "
                f"Failures: {failures}, "
                f"Duplicates skipped: {duplicates}"
            )
        )
```

Also create `game/management/commands/__init__.py` if it doesn't exist:

```bash
touch game/management/commands/__init__.py
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_generate_shikona_pool_command -v 2`
Expected: All 5 tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `./test.sh`
Expected: All tests pass. Coverage does not decrease.

- [ ] **Step 6: Commit**

```bash
git add game/management/commands/ tests/test_generate_shikona_pool_command.py
git commit -m "feat(shikona): add generate_shikona_pool management command

Generates pre-generated shikona pool via OpenAI. Supports --count
and --batch-size flags. Skips duplicates, reports progress, handles
partial failures gracefully."
```

---

## Task 6: Final Verification

- [ ] **Step 1: Run lint and type checks**

Run: `uv run ruff check --fix && uv run ruff format`
Run: `uv run pyright`

Fix any issues.

- [ ] **Step 2: Run full test suite**

Run: `./test.sh`
Expected: All tests pass. Coverage does not decrease.

- [ ] **Step 3: Commit any fixes**

If lint/type check required changes:
```bash
git add -u
git commit -m "fix: address lint and type check issues"
```

- [ ] **Step 4: Verify migration**

Run: `uv run python manage.py migrate`
Run: `uv run python manage.py showmigrations game`
Expected: All migrations applied, including the new pool fields migration.
