# src/cosmicanimator/adapters/transitions/timing.py

"""
Timing utilities for scheduling animations in CosmicAnimator.

Defines
-------
- `Timing`: declarative dataclass for timing configs.
- `_schedule_indices`: compute per-item start offsets.
- `schedule_items`: pair items with their computed times.

Supports simultaneous, sequential, and staggered patterns,
with options for offsets, overlap, order, and normalization
into a fixed total duration.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Iterable, Literal

# Supported timing and ordering modes
TimingMode = Literal["simultaneous", "sequential", "stagger"]
OrderMode = Literal["forward", "reverse"]


# ---------------------------------------------------------------------------
# Timing spec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Timing:
    """
    Declarative timing specification for animation scheduling.

    Attributes
    ----------
    mode : {"simultaneous", "sequential", "stagger"}, default="simultaneous"
        - "simultaneous": all items start at the same time.
        - "sequential": items start one after another at fixed intervals.
        - "stagger": alias of sequential (naming convenience).
    offset : float, default=0.0
        Global delay before the first item starts.
    interval : float, default=0.3
        Time gap between successive starts (only used if `total` is not set).
    overlap : float, default=0.0
        Fractional overlap (0–1) between items, applied when normalizing with `total`.
    order : {"forward", "reverse"}, default="forward"
        Start order for items.
    total : float, optional
        If provided, fit all start times into `[offset, offset + total]`.
        Overrides `interval` to ensure uniform spacing.
    per_item : float, optional
        Hint for item duration (used with `total` to calculate overlap).
    """
    mode: TimingMode = "simultaneous"
    offset: float = 0.0
    interval: float = 0.3
    overlap: float = 0.0
    order: OrderMode = "forward"
    total: Optional[float] = None
    per_item: Optional[float] = None


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _schedule_indices(n: int, t: Timing) -> List[float]:
    """
    Compute start times for `n` items according to a `Timing` spec.

    Parameters
    ----------
    n : int
        Number of items.
    t : Timing
        Timing configuration.

    Returns
    -------
    list[float]
        Start times for each item (ordered according to `t.order`).

    Behavior
    --------
    - "simultaneous": all start at `offset`.
    - "sequential"/"stagger":
        * Default → each starts after `interval`.
        * With `total` → evenly distribute across span `[offset, offset+total]`.
        * With `total` + `per_item` → account for overlap to fit within span.
    """
    if n <= 0:
        return []

    # Forward or reverse order
    idxs = list(range(n)) if t.order == "forward" else list(reversed(range(n)))
    step = t.interval

    # Normalize to fit into total duration if requested
    if t.total is not None and n > 1:
        if t.per_item is not None:
            # Reduce effective span by last item duration * (1 - overlap)
            effective_tail = t.per_item * (1.0 - t.overlap)
            span = max(t.total - effective_tail, 0.0)
        else:
            span = t.total
        step = span / (n - 1)

    # Simultaneous → all same start
    if t.mode == "simultaneous" or n == 1:
        return [t.offset for _ in idxs]

    # Sequential/stagger
    starts = [t.offset + i * step for i in range(n)]
    return [starts[i] for i in idxs]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def schedule_items(items: Iterable, timing: Timing) -> List[Tuple[object, float]]:
    """
    Pair items with their computed start times.

    Parameters
    ----------
    items : iterable
        Items to schedule (any objects).
    timing : Timing
        Timing configuration.

    Returns
    -------
    list[tuple[item, float]]
        Pairs of (item, start_time).

    Examples
    --------
    >>> schedule_items(["A", "B", "C"], Timing(mode="sequential", interval=0.3))
    [('A', 0.0), ('B', 0.3), ('C', 0.6)]

    >>> schedule_items(["X", "Y"], Timing(mode="simultaneous", offset=1.0))
    [('X', 1.0), ('Y', 1.0)]
    """
    items = list(items)
    starts = _schedule_indices(len(items), timing)
    return list(zip(items, starts))
