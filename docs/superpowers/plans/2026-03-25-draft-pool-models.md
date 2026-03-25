# Draft Pool Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `DraftPoolShikona` and `DraftPoolWrestler` models with a three-state reservation lifecycle for multiplayer-safe draft pool management.

**Architecture:** Two flat staging models with a shared `DraftPoolStatus` enum. `DraftPoolShikona` wraps an existing `Shikona` via OneToOneField. `DraftPoolWrestler` links to `DraftPoolShikona` and stores inline stats, origin data, and scout report. Both models share an identical reservation mechanism (status + reserved_by + reserved_at).

**Tech Stack:** Django 5.x, Python 3.12, SQLite (dev), `django.test.TestCase`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `game/enums/draft_pool_status_enum.py` | `DraftPoolStatus` TextChoices enum |
| Modify | `game/enums/__init__.py` | Register new enum |
| Create | `game/models/draft_pool_shikona.py` | `DraftPoolShikona` model |
| Create | `game/models/draft_pool_wrestler.py` | `DraftPoolWrestler` model |
| Modify | `game/models/__init__.py` | Register new models |
| Modify | `libs/constants.py` | Add `DRAFT_POOL_RESERVATION_EXPIRY_MINUTES` |
| Create | `tests/test_draft_pool_models.py` | All model tests |

---

### Task 1: DraftPoolStatus Enum

**Files:**
- Create: `game/enums/draft_pool_status_enum.py`
- Modify: `game/enums/__init__.py`

- [ ] **Step 1: Create the enum file**

```python
"""Draft pool status choices."""

from django.db import models


class DraftPoolStatus(models.TextChoices):
    """Status choices for draft pool entries."""

    AVAILABLE = "available", "Available"
    RESERVED = "reserved", "Reserved"
    CONSUMED = "consumed", "Consumed"
```

- [ ] **Step 2: Register in `game/enums/__init__.py`**

Add import and `__all__` entry following the existing pattern (alphabetical order):

```python
from game.enums.draft_pool_status_enum import DraftPoolStatus
```

Add `"DraftPoolStatus"` to `__all__`.

- [ ] **Step 3: Verify import works**

Run: `uv run python -c "from game.enums import DraftPoolStatus; print(DraftPoolStatus.choices)"`
Expected: `[('available', 'Available'), ('reserved', 'Reserved'), ('consumed', 'Consumed')]`

- [ ] **Step 4: Commit**

```bash
git add game/enums/draft_pool_status_enum.py game/enums/__init__.py
git commit -m "feat(models): add DraftPoolStatus enum"
```

---

### Task 2: Add Reservation Expiry Constant

**Files:**
- Modify: `libs/constants.py`

- [ ] **Step 1: Add the constant**

Add at the end of `libs/constants.py`:

```python
# Draft pool constants
DRAFT_POOL_RESERVATION_EXPIRY_MINUTES: Final[int] = 15
```

- [ ] **Step 2: Verify import works**

Run: `uv run python -c "from libs.constants import DRAFT_POOL_RESERVATION_EXPIRY_MINUTES; print(DRAFT_POOL_RESERVATION_EXPIRY_MINUTES)"`
Expected: `15`

- [ ] **Step 3: Commit**

```bash
git add libs/constants.py
git commit -m "feat(constants): add draft pool reservation expiry"
```

---

### Task 3: DraftPoolShikona Model

**Files:**
- Create: `game/models/draft_pool_shikona.py`
- Modify: `game/models/__init__.py`

- [ ] **Step 1: Create the model file**

```python
"""Draft pool shikona model for pre-generated ring names."""

from django.conf import settings
from django.db import models

from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.models.shikona import Shikona


class DraftPoolShikona(models.Model):
    """Pre-generated ring name available in the draft pool.

    A thin wrapper around a Shikona record that tracks availability
    in the draft pool. Supports reservation to prevent concurrent
    users from seeing the same entry.
    """

    shikona = models.OneToOneField(
        Shikona,
        on_delete=models.PROTECT,
        related_name="draft_pool_entry",
        help_text="The pre-generated ring name",
    )
    status = models.CharField(
        max_length=10,
        choices=DraftPoolStatus.choices,
        default=DraftPoolStatus.AVAILABLE,
        help_text="Current availability status",
    )
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_draft_shikona",
        help_text="User who has reserved this entry",
    )
    reserved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this entry was reserved",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata."""

        verbose_name = "Draft Pool Shikona"
        verbose_name_plural = "Draft Pool Shikona"

    def __str__(self) -> str:
        """Return the shikona and status."""
        return f"{self.shikona} ({self.status})"
```

- [ ] **Step 2: Register in `game/models/__init__.py`**

Add import following existing alphabetical pattern:

```python
from .draft_pool_shikona import DraftPoolShikona
```

Add `"DraftPoolShikona"` to `__all__`.

- [ ] **Step 3: Create migration**

Run: `uv run python manage.py makemigrations game`
Expected: migration created for `DraftPoolShikona`

- [ ] **Step 4: Run migration**

Run: `uv run python manage.py migrate`
Expected: migration applies cleanly

- [ ] **Step 5: Commit**

```bash
git add game/models/draft_pool_shikona.py game/models/__init__.py game/migrations/
git commit -m "feat(models): add DraftPoolShikona model"
```

---

### Task 4: DraftPoolWrestler Model

**Files:**
- Create: `game/models/draft_pool_wrestler.py`
- Modify: `game/models/__init__.py`

- [ ] **Step 1: Create the model file**

```python
"""Draft pool wrestler model for pre-generated wrestlers."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from game.enums.country_enum import Country
from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.enums.jp_prefecture_enum import JPPrefecture
from game.models.draft_pool_shikona import DraftPoolShikona
from libs.constants import MAX_POTENTIAL, MAX_STAT_VALUE, MIN_POTENTIAL, MIN_STAT_VALUE


class DraftPoolWrestler(models.Model):
    """Pre-generated wrestler available in the draft pool.

    A flat staging record containing all data needed to create a
    Rikishi when a player drafts this wrestler. Stats and potential
    are hidden from the player; only the scout report is shown.
    """

    # Identity
    draft_pool_shikona = models.OneToOneField(
        DraftPoolShikona,
        on_delete=models.PROTECT,
        related_name="wrestler",
        help_text="Ring name for this wrestler",
    )

    # Origin (resolved to Shusshin via get_or_create at draft time)
    country_code = models.CharField(
        max_length=2,
        choices=Country.choices,
        help_text="Country of origin (ISO 3166-1 alpha-2)",
    )
    jp_prefecture = models.CharField(
        max_length=5,
        choices=JPPrefecture.choices,
        blank=True,
        default="",
        help_text="Japanese prefecture (required if country is JP)",
    )

    # Stats (hidden from player)
    potential = models.PositiveIntegerField(
        help_text="Maximum total stat points",
    )
    strength = models.PositiveIntegerField(
        help_text="Physical power and pushing ability",
    )
    technique = models.PositiveIntegerField(
        help_text="Technical skill",
    )
    balance = models.PositiveIntegerField(
        help_text="Stability and footing",
    )
    endurance = models.PositiveIntegerField(
        help_text="Stamina",
    )
    mental = models.PositiveIntegerField(
        help_text="Mental fortitude",
    )

    # Player-facing
    scout_report = models.TextField(
        help_text="LLM-generated narrative about this wrestler",
    )

    # Lifecycle
    status = models.CharField(
        max_length=10,
        choices=DraftPoolStatus.choices,
        default=DraftPoolStatus.AVAILABLE,
        help_text="Current availability status",
    )
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_draft_wrestlers",
        help_text="User who has reserved this entry",
    )
    reserved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this entry was reserved",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata."""

        verbose_name = "Draft Pool Wrestler"
        verbose_name_plural = "Draft Pool Wrestlers"
        constraints = [
            # Stat range constraints
            models.CheckConstraint(
                condition=Q(strength__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_strength_min",
                violation_error_message=(
                    f"Strength must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(strength__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_strength_max",
                violation_error_message=(
                    f"Strength cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(technique__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_technique_min",
                violation_error_message=(
                    f"Technique must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(technique__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_technique_max",
                violation_error_message=(
                    f"Technique cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(balance__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_balance_min",
                violation_error_message=(
                    f"Balance must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(balance__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_balance_max",
                violation_error_message=(
                    f"Balance cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(endurance__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_endurance_min",
                violation_error_message=(
                    f"Endurance must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(endurance__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_endurance_max",
                violation_error_message=(
                    f"Endurance cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(mental__gte=MIN_STAT_VALUE),
                name="draft_pool_wrestler_mental_min",
                violation_error_message=(
                    f"Mental must be at least {MIN_STAT_VALUE}."
                ),
            ),
            models.CheckConstraint(
                condition=Q(mental__lte=MAX_STAT_VALUE),
                name="draft_pool_wrestler_mental_max",
                violation_error_message=(
                    f"Mental cannot exceed {MAX_STAT_VALUE}."
                ),
            ),
            # Potential range constraint
            models.CheckConstraint(
                condition=(
                    Q(potential__gte=MIN_POTENTIAL)
                    & Q(potential__lte=MAX_POTENTIAL)
                ),
                name="draft_pool_wrestler_potential_range",
                violation_error_message=(
                    f"Potential must be between {MIN_POTENTIAL}"
                    f" and {MAX_POTENTIAL}."
                ),
            ),
            # Shusshin constraint (mirroring Shusshin model)
            models.CheckConstraint(
                name="draft_pool_wrestler_jp_prefecture",
                condition=(
                    (
                        Q(country_code=Country.JP)
                        & ~Q(jp_prefecture="")
                    )
                    | (
                        ~Q(country_code=Country.JP)
                        & Q(jp_prefecture="")
                    )
                ),
            ),
        ]

    def __str__(self) -> str:
        """Return the wrestler's ring name and status."""
        return (
            f"{self.draft_pool_shikona.shikona} ({self.status})"
        )
```

- [ ] **Step 2: Register in `game/models/__init__.py`**

Add import following existing alphabetical pattern:

```python
from .draft_pool_wrestler import DraftPoolWrestler
```

Add `"DraftPoolWrestler"` to `__all__`.

- [ ] **Step 3: Create migration**

Run: `uv run python manage.py makemigrations game`
Expected: migration created for `DraftPoolWrestler`

- [ ] **Step 4: Run migration**

Run: `uv run python manage.py migrate`
Expected: migration applies cleanly

- [ ] **Step 5: Commit**

```bash
git add game/models/draft_pool_wrestler.py game/models/__init__.py game/migrations/
git commit -m "feat(models): add DraftPoolWrestler model"
```

---

### Task 5: DraftPoolShikona Tests

**Files:**
- Create: `tests/test_draft_pool_models.py`

- [ ] **Step 1: Write DraftPoolShikona tests**

```python
"""Tests for draft pool models."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, models, transaction
from django.test import TestCase
from django.utils import timezone

from game.enums.draft_pool_status_enum import DraftPoolStatus
from game.models import DraftPoolShikona, Shikona

User = get_user_model()


class DraftPoolShikonaModelTests(TestCase):
    """Tests for the DraftPoolShikona model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.shikona = Shikona.objects.create(
            name="鶴龍",
            transliteration="Tsururyu",
            interpretation="Crane Dragon",
        )

    def test_create_with_defaults(self) -> None:
        """Should create with available status and no reservation."""
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        self.assertEqual(entry.status, DraftPoolStatus.AVAILABLE)
        self.assertIsNone(entry.reserved_by)
        self.assertIsNone(entry.reserved_at)
        self.assertIsNotNone(entry.created_at)

    def test_str_includes_shikona_and_status(self) -> None:
        """Should include shikona and status in string."""
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        result = str(entry)
        self.assertIn("Tsururyu", result)
        self.assertIn("available", result)

    def test_reserve_entry(self) -> None:
        """Should allow reserving with user and timestamp."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        entry.status = DraftPoolStatus.RESERVED
        entry.reserved_by = user
        entry.reserved_at = timezone.now()
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.status, DraftPoolStatus.RESERVED)
        self.assertEqual(entry.reserved_by, user)
        self.assertIsNotNone(entry.reserved_at)

    def test_consume_entry(self) -> None:
        """Should allow consuming an entry."""
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
        )
        entry.status = DraftPoolStatus.CONSUMED
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.status, DraftPoolStatus.CONSUMED)

    def test_fail_duplicate_shikona(self) -> None:
        """Should prevent two pool entries for the same shikona."""
        DraftPoolShikona.objects.create(shikona=self.shikona)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolShikona.objects.create(shikona=self.shikona)

    def test_shikona_protected_on_delete(self) -> None:
        """Should prevent deleting a shikona that has a pool entry."""
        DraftPoolShikona.objects.create(shikona=self.shikona)
        with self.assertRaises(
            models.ProtectedError
        ), transaction.atomic():
            self.shikona.delete()

    def test_user_deletion_nullifies_reservation(self) -> None:
        """Should set reserved_by to null when user is deleted."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        entry = DraftPoolShikona.objects.create(
            shikona=self.shikona,
            status=DraftPoolStatus.RESERVED,
            reserved_by=user,
            reserved_at=timezone.now(),
        )
        user.delete()

        entry.refresh_from_db()
        self.assertIsNone(entry.reserved_by)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run python manage.py test tests.test_draft_pool_models.DraftPoolShikonaModelTests -v 2`
Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_draft_pool_models.py
git commit -m "test(models): add DraftPoolShikona tests"
```

---

### Task 6: DraftPoolWrestler Tests

**Files:**
- Modify: `tests/test_draft_pool_models.py`

- [ ] **Step 1: Add DraftPoolWrestler tests**

Add the following test class to `tests/test_draft_pool_models.py`. Add `DraftPoolWrestler` to the imports from `game.models`, and add imports for `Country`, `JPPrefecture` from `game.enums`.

```python
class DraftPoolWrestlerModelTests(TestCase):
    """Tests for the DraftPoolWrestler model."""

    def _create_pool_shikona(
        self, name: str, transliteration: str, interpretation: str
    ) -> DraftPoolShikona:
        """Create a Shikona and DraftPoolShikona pair."""
        shikona = Shikona.objects.create(
            name=name,
            transliteration=transliteration,
            interpretation=interpretation,
        )
        return DraftPoolShikona.objects.create(shikona=shikona)

    def setUp(self) -> None:
        """Set up test data."""
        self.pool_shikona = self._create_pool_shikona(
            "鶴龍", "Tsururyu", "Crane Dragon"
        )
        self.valid_kwargs: dict[str, object] = {
            "draft_pool_shikona": self.pool_shikona,
            "country_code": Country.JP,
            "jp_prefecture": JPPrefecture.TOKYO,
            "potential": 50,
            "strength": 10,
            "technique": 8,
            "balance": 7,
            "endurance": 6,
            "mental": 5,
            "scout_report": "A promising wrestler from Tokyo.",
        }

    def test_create_with_valid_data(self) -> None:
        """Should create a wrestler with all required fields."""
        wrestler = DraftPoolWrestler.objects.create(
            **self.valid_kwargs
        )
        self.assertEqual(
            wrestler.status, DraftPoolStatus.AVAILABLE
        )
        self.assertIsNone(wrestler.reserved_by)
        self.assertIsNone(wrestler.reserved_at)
        self.assertIsNotNone(wrestler.created_at)
        self.assertEqual(wrestler.potential, 50)
        self.assertEqual(wrestler.strength, 10)
        self.assertEqual(wrestler.scout_report, "A promising wrestler from Tokyo.")

    def test_str_includes_shikona_and_status(self) -> None:
        """Should include shikona and status in string."""
        wrestler = DraftPoolWrestler.objects.create(
            **self.valid_kwargs
        )
        result = str(wrestler)
        self.assertIn("Tsururyu", result)
        self.assertIn("available", result)

    def test_non_jp_country_with_empty_prefecture(self) -> None:
        """Should allow non-JP country with empty prefecture."""
        pool_shikona = self._create_pool_shikona(
            "白鳳", "Hakuhou", "White Phoenix"
        )
        wrestler = DraftPoolWrestler.objects.create(
            draft_pool_shikona=pool_shikona,
            country_code=Country.US,
            jp_prefecture="",
            potential=40,
            strength=5,
            technique=5,
            balance=5,
            endurance=5,
            mental=5,
            scout_report="An American wrestler.",
        )
        self.assertEqual(wrestler.country_code, Country.US)

    def test_fail_jp_without_prefecture(self) -> None:
        """Should fail for JP country without prefecture."""
        pool_shikona = self._create_pool_shikona(
            "白鳳", "Hakuhou", "White Phoenix"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(
                draft_pool_shikona=pool_shikona,
                country_code=Country.JP,
                jp_prefecture="",
                potential=40,
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                scout_report="Missing prefecture.",
            )

    def test_fail_non_jp_with_prefecture(self) -> None:
        """Should fail for non-JP country with prefecture."""
        pool_shikona = self._create_pool_shikona(
            "白鳳", "Hakuhou", "White Phoenix"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(
                draft_pool_shikona=pool_shikona,
                country_code=Country.US,
                jp_prefecture=JPPrefecture.TOKYO,
                potential=40,
                strength=5,
                technique=5,
                balance=5,
                endurance=5,
                mental=5,
                scout_report="Invalid prefecture.",
            )

    def test_fail_strength_below_min(self) -> None:
        """Should fail if strength is below minimum."""
        self.valid_kwargs["strength"] = 0
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_strength_above_max(self) -> None:
        """Should fail if strength exceeds maximum."""
        self.valid_kwargs["strength"] = 21
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_potential_below_min(self) -> None:
        """Should fail if potential is below 5."""
        self.valid_kwargs["potential"] = 4
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_potential_above_max(self) -> None:
        """Should fail if potential exceeds 100."""
        self.valid_kwargs["potential"] = 101
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_fail_duplicate_pool_shikona(self) -> None:
        """Should prevent two wrestlers for the same pool shikona."""
        DraftPoolWrestler.objects.create(**self.valid_kwargs)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DraftPoolWrestler.objects.create(**self.valid_kwargs)

    def test_reserve_wrestler(self) -> None:
        """Should allow reserving with user and timestamp."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        wrestler = DraftPoolWrestler.objects.create(
            **self.valid_kwargs
        )
        wrestler.status = DraftPoolStatus.RESERVED
        wrestler.reserved_by = user
        wrestler.reserved_at = timezone.now()
        wrestler.save()

        wrestler.refresh_from_db()
        self.assertEqual(
            wrestler.status, DraftPoolStatus.RESERVED
        )
        self.assertEqual(wrestler.reserved_by, user)
        self.assertIsNotNone(wrestler.reserved_at)

    def test_pool_shikona_protected_on_delete(self) -> None:
        """Should prevent deleting a pool shikona that has a wrestler."""
        DraftPoolWrestler.objects.create(**self.valid_kwargs)
        with self.assertRaises(
            models.ProtectedError
        ), transaction.atomic():
            self.pool_shikona.delete()
```

- [ ] **Step 2: Run all draft pool model tests**

Run: `uv run python manage.py test tests.test_draft_pool_models -v 2`
Expected: all tests pass (both `DraftPoolShikonaModelTests` and `DraftPoolWrestlerModelTests`)

- [ ] **Step 3: Commit**

```bash
git add tests/test_draft_pool_models.py
git commit -m "test(models): add DraftPoolWrestler tests"
```

---

### Task 7: Final Validation

- [ ] **Step 1: Run full test suite**

Run: `./test.sh`
Expected: all tests pass, coverage does not decrease

- [ ] **Step 2: Run type checker**

Run: `uv run pyright`
Expected: no errors

- [ ] **Step 3: Run linter**

Run: `uv run ruff check --fix && uv run ruff format`
Expected: no issues

- [ ] **Step 4: Commit any formatting fixes**

If ruff made changes, stage the specific files that were modified:

```bash
git add game/ tests/ libs/
git commit -m "style: fix formatting from ruff"
```
