# Draft Pool Models Design — Issue #109

## Overview

Create two pool models (`DraftPoolShikona`, `DraftPoolWrestler`) that store pre-generated data for the draft flow. These are flat staging tables with no FK dependencies on game entities (except `Shikona` for name reuse). They support a multiplayer-safe reservation mechanism so concurrent users never see the same pool entries.

## Decisions

- **Flat staging tables** over relational approach — pool entries are staging data, not game entities. Origin data (`country_code`, `jp_prefecture`) is resolved to `Shusshin` via `get_or_create` at draft time.
- **OneToOneField to Shikona** on `DraftPoolShikona` — avoids duplicating name data. `Shikona` records are created at seed time; the pool model is a thin availability wrapper. `OneToOneField` (not FK) because a shikona should only appear in the pool once, unlike the `Rikishi` model which uses FK to allow shikona reuse over time.
- **Inline stats** on `DraftPoolWrestler` — no FK or inheritance from `Rikishi`. The models have different constraints, lifecycles, and purposes. Six fields aren't worth an abstraction.
- **Three-state status enum** (`available`, `reserved`, `consumed`) with `reserved_by` (FK to User) and `reserved_at` timestamp — supports multiplayer concurrency with reservation expiry.
- **15-minute reservation expiry** — configurable constant in `libs/constants.py`. Stale reservations are treated as available at query time.
- **Uniform lifecycle** — both `DraftPoolShikona` and `DraftPoolWrestler` use the same status/reservation mechanism.

## Models

### DraftPoolStatus enum

File: `game/enums/draft_pool_status_enum.py`

```
DraftPoolStatus(TextChoices)
  AVAILABLE = "available"
  RESERVED = "reserved"
  CONSUMED = "consumed"
```

### DraftPoolShikona

File: `game/models/draft_pool_shikona.py`

```
DraftPoolShikona
  - shikona: OneToOneField(Shikona, PROTECT)
  - status: CharField(choices=DraftPoolStatus, default=AVAILABLE)
  - reserved_by: ForeignKey(User, nullable, SET_NULL)
  - reserved_at: DateTimeField(nullable)
  - created_at: DateTimeField(auto_now_add)
```

### DraftPoolWrestler

File: `game/models/draft_pool_wrestler.py`

```
DraftPoolWrestler
  # Identity
  - draft_pool_shikona: OneToOneField(DraftPoolShikona, PROTECT)

  # Origin (resolved to Shusshin via get_or_create at draft time)
  - country_code: CharField(max=2, choices=Country)
  - jp_prefecture: CharField(max=5, choices=JPPrefecture, blank, default="")

  # Stats (hidden from player)
  - potential: PositiveIntegerField          # 5-100
  - strength: PositiveIntegerField           # 1-20
  - technique: PositiveIntegerField          # 1-20
  - balance: PositiveIntegerField            # 1-20
  - endurance: PositiveIntegerField          # 1-20
  - mental: PositiveIntegerField             # 1-20

  # Player-facing
  - scout_report: TextField

  # Lifecycle
  - status: CharField(choices=DraftPoolStatus, default=AVAILABLE)
  - reserved_by: ForeignKey(User, nullable, SET_NULL)
  - reserved_at: DateTimeField(nullable)
  - created_at: DateTimeField(auto_now_add)
```

**Constraints** (using `MIN_STAT_VALUE`, `MAX_STAT_VALUE`, `MIN_POTENTIAL`, `MAX_POTENTIAL` from `libs/constants.py`, matching Rikishi's pattern):
- Each stat between `MIN_STAT_VALUE` (1) and `MAX_STAT_VALUE` (20)
- Potential between `MIN_POTENTIAL` (5) and `MAX_POTENTIAL` (100)
- No total-stats-within-potential constraint (unlike Rikishi — pool wrestlers are staging data with pre-rolled stats, not subject to XP-based growth)
- Prefecture required only for JP country code (mirroring Shusshin)

### Constants

File: `libs/constants.py` (addition)

```python
DRAFT_POOL_RESERVATION_EXPIRY_MINUTES = 15
```

## File changes

- `game/enums/draft_pool_status_enum.py` — new enum
- `game/enums/__init__.py` — register enum
- `game/models/draft_pool_shikona.py` — new model
- `game/models/draft_pool_wrestler.py` — new model
- `game/models/__init__.py` — register models
- `libs/constants.py` — add reservation expiry constant
- Migration file — both models + constraints
- `tests/test_draft_pool_models.py` — new test file

## Testing

Tests in `tests/test_draft_pool_models.py`:

- Model creation with valid data
- Stat constraints (1-20 bounds, potential 5-100)
- Shusshin prefecture constraint (required only for JP)
- Status lifecycle (available → reserved → consumed)
- Reservation fields (`reserved_by` and `reserved_at`) populated together
- OneToOne integrity (shikona uniqueness in pool, pool shikona uniqueness in wrestler)

## Out of scope

- Service logic for drawing/reserving entries (issue #111)
- Management command for seeding (issue #110)
- View and template changes (issues #107, #112)
- Admin registration (nice-to-have, not required)
