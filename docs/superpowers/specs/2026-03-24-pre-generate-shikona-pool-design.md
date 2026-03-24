# Pre-generate Shikona Pool

**Issue**: [#84](https://github.com/croquant/pro-sumo-manager/issues/84)
**Date**: 2026-03-24

## Problem

Heya name selection and rikishi generation both depend on real-time OpenAI API calls for shikona generation. Each call takes several seconds, making onboarding slow (15s+ for heya names, ~5s per rikishi). Pre-generating a pool of shikona eliminates this bottleneck.

## Constraints

- Shared world: all human players and AI share one shikona pool.
- Concurrency: multiple users may view/select shikona simultaneously.
- No shusshin theming for the initial pool (future consideration).
- Pool management lives in the service layer; generators stay stateless.
- Management command for initial population; game loop integration later.

## Design

### Model Changes

Add three fields to `Shikona`:

```python
is_available = models.BooleanField(default=True, db_index=True)
reserved_at = models.DateTimeField(null=True, blank=True)
reserved_by = models.ForeignKey(
    "accounts.User",
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="reserved_shikona",
)
```

**States:**

| `is_available` | `reserved_at` | Meaning | Returned by `get_available_shikona`? |
|---|---|---|---|
| `True` | `NULL` | In pool, ready to use | Yes |
| `True` | set (< 5 min old) | Reserved for a user's heya selection | No |
| `True` | set (>= 5 min old) | Expired reservation, treated as available | Yes |
| `False` | any | Consumed (assigned to heya or rikishi) | No |

`is_available` tracks permanent consumption. Reservation is a separate, transient concern filtered by `reserved_at`.

Migration defaults `is_available=False` for existing rows since they are already assigned.

### ShikonaService — New Pool Methods

Added to the existing `ShikonaService` (all as `@staticmethod`, matching the existing pattern):

```python
def get_available_shikona(self, count: int = 1) -> list[Shikona]:
    """Return random available, non-reserved shikona from the pool.

    Filters: is_available=True AND (reserved_at IS NULL OR
    reserved_at < now - 5 min).
    """

def reserve_shikona(
    self, shikona_ids: list[int], user: User
) -> list[Shikona]:
    """Reserve shikona for a user's heya name selection.

    Uses select_for_update() to prevent races. Sets reserved_at
    and reserved_by. Returns successfully reserved shikona.
    """

def release_reservation(self, user: User) -> None:
    """Clear reservation fields for all shikona reserved by user.

    Called when user navigates away or requests new options.
    """

def consume_shikona(self, shikona: Shikona) -> None:
    """Mark shikona as permanently used.

    Sets is_available=False, clears reservation fields.
    """

def release_expired_reservations(self) -> int:
    """Clear reservations older than 5 minutes.

    Called lazily before fetching pool options. Returns count
    of released shikona.
    """
```

**Updated existing methods:**

- `generate_shikona_options(count, user)` — calls `release_expired_reservations()`, then tries `get_available_shikona(count)`. If pool has enough, calls `reserve_shikona()` for the user. Falls back to real-time OpenAI if pool is empty or insufficient.
- `create_shikona_from_option(option, user)` — if selected option is a pre-generated shikona, calls `consume_shikona()` and releases the user's other reservations via `release_reservation()`.

Reservation expiry is checked lazily (when fetching options), not via a background job.

### Management Command

`game/management/commands/generate_shikona_pool.py`

```
python manage.py generate_shikona_pool --count 600
```

- Calls `ShikonaGenerator.generate_single()` in a loop (not `generate_batch()`, which raises on any single failure). Catches individual failures to allow partial success.
- Saves each with `is_available=True`.
- Skips duplicates by checking existing `name` values.
- Shows progress counter (e.g., `Generated 42/600...`).
- Reports success/failure count at the end.
- `--batch-size` flag to control chunking.
- Safe to run multiple times.

### DraftPoolService Changes

`DraftPoolService.generate_draft_pool()` updated to:

1. Fetch N shikona from pool via `ShikonaService.get_available_shikona(count)`.
2. Consume each immediately (no reservation — backend operation).
3. Pass pre-fetched shikona into `RikishiGenerator.get()` via a new optional `shikona` parameter. Generator skips its own shikona generation when one is provided.
4. If pool has fewer than needed, use what's available and fall back to real-time generation for the rest.

`RikishiGenerator.get()` gains an optional `shikona` parameter. It remains stateless and unaware of the pool.

### Error Handling

- **Pool depletion**: All paths fall back to real-time OpenAI. No hard failure.
- **Reservation race**: `select_for_update()` in `reserve_shikona`. If a shikona was grabbed between query and lock, skip it and try the next. User always gets requested count (or as many as available).
- **Duplicate shikona from OpenAI**: Management command checks `exists()` before saving, skips and reports.
- **Partial OpenAI failure**: Command continues on individual failures, reports counts.
- **User abandons heya selection**: Reservation expires after 5 minutes via lazy cleanup.

## Testing

### Unit Tests

**`test_shikona_service.py`** — new pool tests:

- `get_available_shikona` returns only available, non-reserved shikona
- `get_available_shikona` treats expired reservations as available
- `reserve_shikona` sets reservation fields correctly
- `reserve_shikona` handles concurrent access via `select_for_update`
- `release_reservation` clears only the user's reservations
- `consume_shikona` sets `is_available=False`
- `release_expired_reservations` only releases stale ones
- `generate_shikona_options` uses pool when available
- `generate_shikona_options` falls back to OpenAI when pool empty
- `create_shikona_from_option` consumes and releases other reservations

**`test_draft_pool_service.py`** — updated tests:

- Draft pool uses pool shikona when available
- Partial pool: some from pool, rest generated
- Empty pool falls back entirely to generator

**`test_generate_shikona_pool_command.py`** — command tests:

- Creates shikona with `is_available=True`
- Respects `--count`
- Skips duplicates
- Handles OpenAI failures gracefully

## Files to Modify

- `game/models/shikona.py` — add fields
- `game/migrations/` — new migration
- `game/services/shikona_service.py` — add pool methods, update existing methods
- `game/services/draft_pool_service.py` — use pool before generator
- `libs/generators/rikishi.py` — add optional `shikona` parameter
- `game/management/commands/generate_shikona_pool.py` — new file
- `tests/test_shikona_service.py` — new pool tests
- `tests/test_draft_pool_service.py` — update existing tests
- `tests/test_generate_shikona_pool_command.py` — new file
