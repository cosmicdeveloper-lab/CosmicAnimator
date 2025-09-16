# src/cosmicanimator/adapters/transitions/fade.py

"""
Fade and ghosting transition helpers for CosmicAnimator.

Provides
--------
- `fade_out_group`: fade out multiple objects with optional staggering.
- `fade_in_group`: fade in multiple objects with optional staggering.
- `ghost_shapes`: temporarily dim ("ghost") stroke layers, then restore.

Notes
-----
- All functions accept both VMobject and VGroup.
- Scheduling is handled by `Timing` and `schedule_items`.
- Ghosting is stroke-aware: filled cores can be skipped if desired.
"""

from __future__ import annotations
from typing import Iterable
from manim import rate_functions as rf
from manim import (
    VGroup,
    VMobject,
    AnimationGroup,
    FadeOut,
    FadeIn,
    smooth,
    Succession,
    Wait,
)
from .timing import Timing, schedule_items
from .transition_utils import extract_targets


# ---------------------------------------------------------------------------
# Fade out
# ---------------------------------------------------------------------------

def fade_out_group(
    targets: Iterable[VMobject | VGroup],
    *,
    timing: Timing = Timing(mode="simultaneous", interval=0.06, order="forward"),
    run_time: float = 0.40,
    rate_func=smooth,
) -> AnimationGroup:
    """
    Fade out a collection of objects (including text).

    Parameters
    ----------
    targets:
        VMobject or VGroup items to fade out.
    timing:
        Timing object controlling offset, interval, mode, and order.
    run_time:
        Duration of each fade-out.
    rate_func:
        Easing function.

    Returns
    -------
    AnimationGroup
        Parallel group of Wait → FadeOut sequences.
    """
    leaves: list[VMobject] = []
    for t in targets:
        parts = extract_targets(t, include_text=True, strategy="parents_with_points") or [t]
        leaves.extend(parts)

    scheduled = schedule_items(leaves, timing)

    seqs = [
        Succession(
            Wait(start),
            FadeOut(m, run_time=run_time, rate_func=rate_func),
        )
        for m, start in scheduled
    ]
    return AnimationGroup(*seqs, lag_ratio=0.0)


# ---------------------------------------------------------------------------
# Fade in
# ---------------------------------------------------------------------------

def fade_in_group(
    targets: Iterable[VMobject | VGroup],
    *,
    timing: Timing = Timing(mode="simultaneous", interval=0.06, order="forward"),
    run_time: float = 0.40,
    rate_func=smooth,
) -> AnimationGroup:
    """
    Fade in a collection of objects.

    Parameters
    ----------
    targets:
        VMobject or VGroup items to fade in.
    timing:
        Timing object controlling offset, interval, mode, and order.
    run_time:
        Duration of each fade-in.
    rate_func:
        Easing function.

    Returns
    -------
    AnimationGroup
        Parallel group of Wait → FadeIn sequences.
    """
    leaves: list[VMobject] = []
    for t in targets:
        parts = extract_targets(t, include_text=True, strategy="parents_with_points") or [t]
        leaves.extend(parts)

    scheduled = schedule_items(leaves, timing)

    seqs = [
        Succession(
            Wait(start),
            FadeIn(m, run_time=run_time, rate_func=rate_func),
        )
        for m, start in scheduled
    ]
    return AnimationGroup(*seqs, lag_ratio=0.0)


# ---------------------------------------------------------------------------
# Ghost shapes
# ---------------------------------------------------------------------------

def ghost_shapes(
    targets: Iterable[VMobject | VGroup],
    *,
    dim_opacity: float = 0.1,
    run_time: float = 0.6,
    pause_ratio: float = 0.12,
    rate_func=None,
    min_stroke: float = 0.2,
    exclude_filled: bool = False,
) -> AnimationGroup:
    """
    Temporarily dim ("ghost") stroke layers, then restore opacity.

    Parameters
    ----------
    targets:
        VMobject or VGroup items to ghost.
    dim_opacity:
        Minimum opacity during ghost effect.
    run_time:
        Duration of full ghost cycle.
    pause_ratio:
        Fraction of cycle to pause at min opacity.
    rate_func:
        Custom rate function. If None, uses `there_and_back_with_pause`.
    min_stroke:
        Minimum stroke opacity required to ghost a layer.
    exclude_filled:
        If True, skip shapes with fill_opacity > 0.05
        (so solid cores remain visible).

    Returns
    -------
    AnimationGroup
        Grouped ghosting animations (no staggering).
    """
    rf_used = rate_func or (lambda t: rf.there_and_back_with_pause(t, pause_ratio=pause_ratio))

    # Gather leaves (no text for ghosting)
    leaf_parts: list[VMobject] = []
    for t in targets:
        parts = extract_targets(t, include_text=False, strategy="leaves") or [t]
        leaf_parts.extend(parts)

    # Stroke-aware filtering
    def _get(op, attr, m):
        try:
            return float(getattr(m, op)())
        except Exception:
            try:
                return float(getattr(m, attr))
            except Exception:
                return None

    def select_layers_by_stroke(parts: Iterable[VMobject]) -> list[VMobject]:
        selected = []
        for m in parts:
            f = _get("get_fill_opacity", "fill_opacity", m) or 0.0
            s = _get("get_stroke_opacity", "stroke_opacity", m)
            if s is None:
                continue
            if s >= min_stroke and (not exclude_filled or f <= 0.05):
                selected.append(m)
        return selected

    layers = select_layers_by_stroke(leaf_parts)

    # Animate opacity dip-and-return
    anims = [
        m.animate(run_time=run_time, rate_func=rf_used).set_opacity(dim_opacity)
        for m in layers
    ]
    return AnimationGroup(*anims, lag_ratio=0.0)
