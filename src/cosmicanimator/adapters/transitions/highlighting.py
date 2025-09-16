# src/cosmicanimator/adapters/transitions/highlight.py

"""
Highlight and focus transition helpers for CosmicAnimator.

Features
--------
- `highlight_shapes`: temporarily highlight shapes with fill and/or glow overlays.
- `focus_on_shape`: dim everything except given targets, lifting them visually.

Notes
-----
- Both functions return `Succession` animations you can play directly.
- Built to be composable with your scene system — no direct scene mutation.
- Uses theme-aware styling (`style_shape`, `resolve_role_or_hex`, `build_glow_overlay`).
"""

from __future__ import annotations
from typing import Optional, Iterable, Literal
from manim import (
    VMobject,
    VGroup,
    Rectangle,
    AnimationGroup,
    Succession,
    FadeIn,
    FadeOut,
    Wait,
    smooth,
    linear,
    ORIGIN,
    config,
)
from cosmicanimator.core.theme import current_theme as t
from cosmicanimator.adapters.style import (
    is_hex_color,
    add_glow_layers,
    resolve_role_or_hex,
    style_shape,
)
from .transition_utils import (
    extract_targets,
    collect_target_colors,
    build_glow_overlay,
)

HighlightMode = Literal["fill", "glow", "both"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _full_screen_rect() -> Rectangle:
    """Return a rectangle covering the full camera frame."""
    rect = Rectangle(width=config.frame_width, height=config.frame_height)
    rect.move_to(ORIGIN)
    return rect


def _build_fill_overlay(shape: VMobject, color: str, fill_opacity: float, scale: float) -> VMobject:
    """
    Create a styled copy of a shape for highlight purposes.

    - Fills with given color & opacity.
    - Adds glow (via `style_shape`).
    - Optionally scales slightly to "pop" above originals.
    """
    styled = style_shape(
        shape.copy(),
        color=color,
        glow=True,
        fill_opacity=fill_opacity,
        scale=1.0,  # base style keeps geometry unchanged
    )
    if abs(scale - 1.0) > 1e-6:
        styled.scale(scale, about_point=shape.get_center())
    return styled


# ---------------------------------------------------------------------------
# Highlight
# ---------------------------------------------------------------------------

def highlight_shapes(
    targets: Iterable[VMobject | VGroup],
    *,
    color: str = "auto",            # theme role or hex, or "auto" for per-part colors
    mode: HighlightMode = "both",   # "fill" | "glow" | "both"
    fill_opacity: float = 0.60,
    scale: float = 1.04,
    include_text: bool = False,
    # timing
    in_time: float = 0.28,
    hold_time: float = 0.55,
    out_time: float = 0.30,
    lag_ratio: float = 0.08,
    # pulse options
    pulse: bool = False,
    pulse_times: int = 2,
    pulse_scale: float = 1.06,
    pulse_period: float = 0.35,
) -> Succession:
    """
    Temporarily highlight one or more shapes with overlays.

    Parameters
    ----------
    targets:
        Shapes (VMobject or VGroup) to highlight.
    color:
        Highlight color: theme role, hex, or "auto".
        - "auto" → derive per-part colors from each target.
    mode:
        "fill" = solid overlay, "glow" = glow-only, "both" = combined.
    fill_opacity:
        Opacity of fill overlay.
    scale:
        Scale-up factor for highlight "pop".
    include_text:
        Include text/labels if True.
    in_time, hold_time, out_time:
        Durations for appear → hold → disappear phases.
    lag_ratio:
        Stagger between multiple highlights.
    pulse:
        If True, animate small pulsing during hold phase.
    pulse_times:
        Number of pulse cycles.
    pulse_scale:
        Scale factor for pulse peak.
    pulse_period:
        Duration of each pulse cycle.

    Returns
    -------
    Succession
        Combined animation (FadeIn → Wait/Pulse → FadeOut).
    """
    overlays: list[VGroup] = []

    # Auto color resolution (per-part hex list)
    auto_colors: list[list[str]] | None = None
    if str(color).lower() == "auto":
        auto_colors = collect_target_colors(
            targets, include_text=include_text, fallback="primary", per_part=True
        )

    # Build overlays per target
    ti = 0
    for t in targets:
        geom_parts = extract_targets(t, include_text=include_text)
        parts: list[VMobject] = []
        per_part_colors = auto_colors[ti] if auto_colors is not None else None

        for idx, g in enumerate(geom_parts):
            part_color = per_part_colors[idx] if per_part_colors is not None else color
            if mode in ("fill", "both"):
                parts.append(_build_fill_overlay(g, part_color, fill_opacity, scale))
            if mode in ("glow", "both"):
                parts.append(build_glow_overlay(g, part_color))
        overlays.append(VGroup(*parts))
        ti += 1

    # Appear phase
    appear = AnimationGroup(
        *[FadeIn(ov, run_time=in_time) for ov in overlays],
        lag_ratio=lag_ratio,
        rate_func=smooth,
    )

    # Hold phase: pulse cycles or wait
    if pulse and pulse_times > 0:
        cycles = []
        for _ in range(pulse_times):
            up = AnimationGroup(
                *[ov.animate.scale(pulse_scale) for ov in overlays],
                lag_ratio=lag_ratio,
                run_time=pulse_period * 0.45,
                rate_func=linear,
            )
            down = AnimationGroup(
                *[ov.animate.scale(1 / pulse_scale) for ov in overlays],
                lag_ratio=lag_ratio,
                run_time=pulse_period * 0.55,
                rate_func=smooth,
            )
            cycles += [up, down]
        mid: AnimationGroup | Wait = Succession(*cycles)
    else:
        mid = Wait(hold_time)

    # Disappear phase
    disappear = AnimationGroup(
        *[FadeOut(ov, run_time=out_time) for ov in overlays],
        lag_ratio=lag_ratio,
        rate_func=smooth,
    )

    return Succession(appear, mid, disappear)


# ---------------------------------------------------------------------------
# Focus
# ---------------------------------------------------------------------------

def focus_on_shape(
    targets: Iterable[VMobject | VGroup],
    *,
    include_text: bool = True,
    backdrop_role: str = "#000000",
    backdrop_opacity: float = 0.62,
    in_time: float = 0.35,
    hold_time: float = 0.60,
    out_time: float = 0.30,
    lag_ratio: float = 0.0,
) -> Succession:
    """
    Dim everything except given targets with a translucent backdrop.

    Parameters
    ----------
    targets:
        Shapes to keep visible (all else dimmed).
    include_text:
        Include text in focused targets if True.
    backdrop_role:
        Backdrop fill color (theme role or hex).
    backdrop_opacity:
        Opacity of backdrop rectangle.
    in_time, hold_time, out_time:
        Durations for appear → hold → disappear phases.
    lag_ratio:
        Stagger for multiple targets.

    Returns
    -------
    Succession
        Combined animation (FadeIn backdrop → Wait → FadeOut backdrop).
    """
    # Backdrop rectangle
    color = resolve_role_or_hex(backdrop_role)
    backdrop = _full_screen_rect()
    backdrop.set_fill(color, opacity=backdrop_opacity)
    backdrop.set_stroke(opacity=0.0)
    backdrop.set_z_index(10)

    # Copies of targets placed above backdrop
    lifted: list[VMobject] = []
    for t in targets:
        parts = extract_targets(t, include_text=include_text)
        if not parts:
            continue
        group = VGroup(*[p.copy() for p in parts])
        group.set_z_index(20)
        lifted.append(group)

    # Appear phase
    appear = AnimationGroup(
        FadeIn(backdrop, run_time=in_time, rate_func=smooth),
        *[FadeIn(g, run_time=in_time, rate_func=smooth) for g in lifted],
        lag_ratio=lag_ratio,
    )

    mid = Wait(hold_time)

    # Disappear phase
    disappear = AnimationGroup(
        *[FadeOut(g, run_time=out_time, rate_func=smooth) for g in lifted],
        FadeOut(backdrop, run_time=out_time, rate_func=smooth),
        lag_ratio=lag_ratio,
    )

    return Succession(appear, mid, disappear)
