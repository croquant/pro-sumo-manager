# Issue #71: Bout Result Persistence Implementation Plan

## Overview
Implement persistence for bout results to track individual match history in tournaments.

---

## Phase 1: Create the Bout Model

### File: `game/models/bout.py` (NEW)

Create a new model with:

```python
class Bout(models.Model):
    """Represents a single bout between two rikishi in a tournament."""

    class Winner(models.TextChoices):
        EAST = "east", "East"
        WEST = "west", "West"

    # Foreign keys
    banzuke = models.ForeignKey(Banzuke, on_delete=models.PROTECT, related_name="bouts")
    east_rikishi = models.ForeignKey(Rikishi, on_delete=models.PROTECT, related_name="bouts_as_east")
    west_rikishi = models.ForeignKey(Rikishi, on_delete=models.PROTECT, related_name="bouts_as_west")

    # Bout metadata
    day = models.PositiveSmallIntegerField()  # 1-15
    winner = models.CharField(max_length=4, choices=Winner.choices)
    kimarite = models.CharField(max_length=32)  # Winning technique

    # XP gains
    east_xp_gain = models.PositiveIntegerField()
    west_xp_gain = models.PositiveIntegerField()

    # Match quality
    excitement_level = models.DecimalField(max_digits=3, decimal_places=1)  # 1.0-10.0
    commentary = models.TextField()  # JSON list or joined text
```

### Constraints to implement:
1. `UniqueConstraint`: Each wrestler pair can only fight once per tournament
2. `CheckConstraint`: Day must be 1-15
3. `CheckConstraint`: Excitement level 1.0-10.0
4. `CheckConstraint`: east_rikishi != west_rikishi (via clean() method)
5. Kimarite must be from valid list (via clean() method or CharField choices)

### Update `game/models/__init__.py`:
Add `Bout` to imports and `__all__`

---

## Phase 2: Create Migration

### File: `game/migrations/0006_bout.py` (auto-generated)

Run: `python manage.py makemigrations game`

---

## Phase 3: Create BoutService

### File: `game/services/bout_service.py` (NEW)

```python
class BoutService:
    """Service for recording bout results and updating related data."""

    @staticmethod
    @transaction.atomic
    def record_bout(
        banzuke: Banzuke,
        day: int,
        east_rikishi: Rikishi,
        west_rikishi: Rikishi,
        bout_result: BoutOutput,  # From libs/types/bout.py
    ) -> Bout:
        """
        Record a bout result from BoutGenerator output.

        1. Create Bout record
        2. Update BanzukeEntry win/loss counts (with select_for_update)
        3. Award XP to both wrestlers
        """
        pass

    @staticmethod
    def get_head_to_head(rikishi1: Rikishi, rikishi2: Rikishi) -> dict:
        """Get head-to-head record between two rikishi (future use)."""
        pass
```

### Key implementation details:
- Use `select_for_update()` when modifying BanzukeEntry to prevent race conditions
- Validate that both rikishi have BanzukeEntry records for the tournament
- Determine winner/loser and update wins/losses accordingly
- Award XP using `RikishiService.increase_random_stats()` or direct XP addition

### Update `game/services/__init__.py`:
Add `BoutService` to imports

---

## Phase 4: Add Admin Interface

### Update `game/admin.py`:

```python
@admin.register(Bout)
class BoutAdmin(admin.ModelAdmin[Bout]):
    """Admin panel configuration for Bout model."""

    list_display = (
        "banzuke",
        "day",
        "east_rikishi_name",
        "west_rikishi_name",
        "winner_display",
        "kimarite",
        "excitement_level",
    )
    list_filter = ("banzuke", "day", "kimarite", "winner")
    search_fields = (
        "east_rikishi__shikona__transliteration",
        "west_rikishi__shikona__transliteration",
    )
    ordering = ("banzuke", "day")
    readonly_fields = ("commentary",)  # Read-only as per requirements
    list_select_related = (
        "banzuke",
        "east_rikishi__shikona",
        "west_rikishi__shikona",
    )
```

---

## Phase 5: Define Valid Kimarite

### Option A: Use Literal type from `libs/types/bout.py`
Extract the kimarite list and create a constant:

```python
# libs/constants.py or game/enums/kimarite_enum.py
VALID_KIMARITE = [
    "yorikiri", "oshidashi", "hatakikomi", "uwatenage",
    "shitatenage", "tsuppari", "kotenage", "yori-taoshi",
    "oshitaoshi", "hikiotoshi", "uwatedashinage", "shitatedashinage",
    "tsukiotoshi", "sukuinage", "tottari", "ketaguri",
    "utchari", "katasukashi",
]
```

### Option B: Create TextChoices enum
For better Django admin integration and type safety.

---

## Phase 6: Write Tests

### File: `tests/test_bout_model.py` (NEW)

Test cases:
1. **Create bout** - Basic creation with valid data
2. **Unique constraint** - Same wrestlers can't fight twice in same tournament
3. **Self-fight validation** - Wrestler can't fight themselves
4. **Day validation** - Day must be 1-15
5. **Excitement level validation** - Must be 1.0-10.0
6. **Kimarite validation** - Must be from valid list
7. **String representation** - `__str__` method

### File: `tests/test_bout_service.py` (NEW)

Test cases:
1. **Record bout** - Creates Bout and updates BanzukeEntry counts
2. **Winner gets win** - Correct BanzukeEntry.wins incremented
3. **Loser gets loss** - Correct BanzukeEntry.losses incremented
4. **XP awarded** - Both rikishi receive XP
5. **Atomic transaction** - Rollback on error
6. **Missing BanzukeEntry** - Raises appropriate error
7. **Concurrent updates** - select_for_update works correctly

### File: `tests/test_bout_admin.py` (NEW)

Test cases:
1. **List view loads** - Admin changelist renders
2. **Filters work** - Can filter by tournament, wrestler, kimarite
3. **Search works** - Can search by wrestler name
4. **Commentary readonly** - Verify readonly in detail view

---

## Phase 7: Type Safety

Ensure all new code passes Pyright strict mode:
- Add proper type hints to all functions
- Use `from __future__ import annotations`
- Handle Optional types correctly

---

## Implementation Order

1. **Model** (`game/models/bout.py`) - Foundation
2. **Update __init__** (`game/models/__init__.py`) - Export model
3. **Migration** - Create database table
4. **Constants** - Define valid kimarite list
5. **Service** (`game/services/bout_service.py`) - Business logic
6. **Update services __init__** - Export service
7. **Admin** (`game/admin.py`) - Add BoutAdmin
8. **Tests** - All test files
9. **Verify** - Run `./test.sh` and Pyright

---

## Files to Create/Modify

### New Files:
- `game/models/bout.py`
- `game/services/bout_service.py`
- `game/migrations/0006_bout.py` (auto-generated)
- `tests/test_bout_model.py`
- `tests/test_bout_service.py`
- `tests/test_bout_admin.py`

### Modified Files:
- `game/models/__init__.py` - Add Bout export
- `game/services/__init__.py` - Add BoutService export
- `game/admin.py` - Add BoutAdmin
- `libs/constants.py` - Add VALID_KIMARITE (optional)

---

## Code Patterns to Follow

1. **Models**: Follow `banzuke.py` pattern with proper Meta class, constraints, __str__
2. **Services**: Follow `rikishi_service.py` pattern with @staticmethod, @transaction.atomic
3. **Admin**: Follow existing pattern with list_display, list_filter, search_fields, custom display methods
4. **Tests**: Follow `test_banzuke_models.py` pattern with setUp, clear test names, proper assertions

---

## Validation Checklist

- [ ] All tests pass (`./test.sh`)
- [ ] Type checking passes (`pyright`)
- [ ] Code coverage maintained
- [ ] Admin interface functional
- [ ] Bout results correctly update BanzukeEntry win/loss counts
- [ ] XP correctly awarded to both wrestlers
