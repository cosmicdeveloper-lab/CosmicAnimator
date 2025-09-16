# src/cosmicanimator/adapters/transitions/visuals.py

"""
Visual overlay effects for CosmicAnimator.

Currently provides:
- `ripple_effect`: concentric rings expanding or contracting from targets.

Notes
-----
- Rings are styled with theme-aware glow overlays.
- Colors can be explicit (hex/role) or `"auto"` to match target colors.
- Designed for short-form emphasis animations (ripples, pings, echoes).
"""

from __future__ import annotations
from typing import Optional, Iterable, List, Union
import numpy as np
from manim import (
    VMobject,
    VGroup,
    Circle,
    AnimationGroup,
    Succession,
    FadeIn,
    FadeOut,
    Wait,
    smooth,
)
from cosmicanimator.core.theme import current_theme as t
from .transition_utils import collect_target_colors, build_glow_overlay
from cosmicanimator.adapters.style import resolve_role_or_hex

VMOrGroup = Union[VMobject, VGroup]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _max_half_extent(m: VMOrGroup) -> float:
    """
    Estimate a good base radius for ripple rings.

    Parameters
    ----------
    m : VMobject | VGroup
        Target object.

    Returns
    -------
    float
        Half of the larger of width/height (fallback: bounding box).
    """
    try:
        w = float(m.width)
        h = float(m.height)
    except Exception:
        bbox = m.get_bounding_box()  # [[x0,y0,0],[x1,y1,0],[x2,y2,0]]
        x0, y0, _ = bbox[0]
        x1, y1, _ = bbox[1]
        x2, y2, _ = bbox[2]
        w = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        h = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return 0.5 * max(w, h)


def _make_ring(center, radius: float, color: str, width: float, opacity: float) -> Circle:
    """
    Create a stroked circle (ring) with glow overlay.

    Parameters
    ----------
    center : array-like
        Position to center the ring.
    radius : float
        Circle radius.
    color : str
        Stroke color (theme role or hex).

    Returns
    -------
    Circle
        Styled circle with glow overlay applied.
    """
    ring = Circle(radius=radius)
    ring.move_to(center)
    ring.set_fill(opacity=0.0)
    ring = build_glow_overlay(shape=ring, color=color)
    return ring


# ---------------------------------------------------------------------------
# Ripple effect
# ---------------------------------------------------------------------------

def ripple_effect(
    targets: Iterable[VMobject | VGroup],
    *,
    color: str = "auto",
    rings: int = 3,
    ring_gap: float = 0.25,
    stroke_width: float = 4.0,
    base_opacity: float = 0.9,
    from_edge: bool = True,
    center_override: Optional[np.ndarray] = None,
    inward: bool = False,
    fade_in: bool = False,
    fade_out: bool = True,
    in_time: float = 0.10,
    expand_time: float = 0.8,
    hold_time: float = 0.00,
    out_time: float = 0.25,
    ring_lag: float = 0.12,
    target_lag: float = 0.05,
    rate_func=smooth,
) -> AnimationGroup:
    """
    Create ripple rings expanding or contracting from targets.

    Parameters
    ----------
    targets:
        Objects to ripple from.
    color:
        Ring stroke color (theme role, hex, or "auto" = match targets).
    rings:
        Number of rings per target.
    ring_gap:
        Spacing between rings.
    stroke_width:
        Stroke width of rings (not heavily used since glow overlays dominate).
    base_opacity:
        Initial ring opacity.
    from_edge:
        If True, rings start at object’s edge; else, near its center.
    center_override:
        Explicit center point (overrides target center).
    inward:
        If True, rings shrink inward instead of expanding.
    fade_in, fade_out:
        Whether rings fade in/out.
    in_time, expand_time, hold_time, out_time:
        Timings for phases (seconds).
    ring_lag:
        Stagger between rings for wave-train effect.
    target_lag:
        Stagger between multiple targets.
    rate_func:
        Easing function for expansion/shrink.

    Returns
    -------
    AnimationGroup
        Combined ripple animations.
    """
    per_target_colors = None
    if str(color).lower() == "auto":
        per_target_colors = collect_target_colors(
            targets, include_text=False, fallback="primary", per_part=False
        )
        targets = list(targets)  # reuse safely

    all_targets: List = []
    for idx, t in enumerate(targets):
        center = center_override if center_override is not None else t.get_center()
        base_r = _max_half_extent(t) if from_edge else 0.01

        ring_animations: List = []
        for i in range(rings):
            start_r = base_r + (i * ring_gap)
            ring_color = per_target_colors[idx] if per_target_colors else color

            if inward:
                ring = _make_ring(center, radius=start_r * 1.8, color=ring_color, width=stroke_width, opacity=base_opacity)
                start_scale = 1.0
                end_scale = max(1e-3, (start_r / (start_r * 1.8)))
            else:
                ring = _make_ring(center, radius=start_r, color=ring_color, width=stroke_width, opacity=base_opacity)
                start_scale = 0.05 if from_edge else 0.2
                end_scale = 1.0

            ring.scale(start_scale, about_point=center)

            steps: List = []
            steps.append(FadeIn(ring, run_time=in_time if fade_in else 0, rate_func=rate_func))
            steps.append(
                ring.animate(run_time=expand_time, rate_func=rate_func).scale(
                    end_scale / start_scale, about_point=center
                )
            )
            if hold_time > 0:
                steps.append(Wait(hold_time))
            steps.append(FadeOut(ring, run_time=out_time if fade_out else 0, rate_func=rate_func))

            ring_animations.append(Succession(*steps))

        all_targets.append(AnimationGroup(*ring_animations, lag_ratio=ring_lag))

    return AnimationGroup(*all_targets, lag_ratio=target_lag)
