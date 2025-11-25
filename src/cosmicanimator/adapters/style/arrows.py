# src/cosmicanimator/adapters/style/arrows.py

"""
Arrow styling utilities for CosmicAnimator.

Provides consistent, theme-aware arrow builders with neon/glow/plate effects.

Includes:
- `glow_arrow` — Standard straight arrow with optional glow and plate depth.
- `dotted_line` — Dashed connection line with optional buffering.
- `curved_arrow` — Curved arrow variant using the same styling logic.

Depends on:
- `current_theme` (stroke widths, glow bands, plate configs)
- `style_helpers` (`add_glow_layers`, `build_plate_stack`, etc.)
"""

from __future__ import annotations
from typing import Optional, Sequence
import numpy as np
from manim import VGroup, Arrow, DashedLine, CurvedArrow
from cosmicanimator.core.theme import current_theme as t
from .style_helpers import build_plate_stack, add_glow_layers


# ---------------------------------------------------------------------------
# Glow arrow (with optional plate depth)
# ---------------------------------------------------------------------------


def glow_arrow(
    start: Sequence[float] | np.ndarray,
    end: Sequence[float] | np.ndarray,
    *,
    color: Optional[str] = None,
    stroke_width: Optional[float] = None,
    tip_length: Optional[float] = None,
    buff: Optional[float] = None,
    plate: bool = True,
    glow: bool = True,
    glow_inner: bool = False,
    glow_outer: bool = True,
) -> VGroup:
    """
    Create a themed arrow with optional glow and plate stacking.

    Parameters
    ----------
    start, end:
        Coordinates for the arrow start and end points.
    color:
        Role or hex color for the arrow stroke (defaults to theme's arrow color).
    stroke_width:
        Optional manual stroke width override.
    tip_length:
        Optional arrow tip length. Defaults to theme value.
    buff:
        Optional distance to shorten arrow ends. Defaults to theme value.
    plate:
        Whether to add a dark plate stack behind the arrow.
    glow:
        Whether to add glow layers.
    glow_inner, glow_outer:
        Enable or disable inner/outer glow bands.

    Returns
    -------
    VGroup
        Group containing the arrow and all additional layers.
    """
    style = t.arrow_style(None)
    base_color = t.get_color(color or style["color"])
    stroke_w = stroke_width or style["stroke_width"]
    tip_len = tip_length or style["tip_length"]
    buff_val = buff or style["buff"]

    core = Arrow(
        start,
        end,
        buff=buff_val,
        stroke_width=stroke_w,
        color=base_color,
        tip_length=tip_len,
    ).set_fill(opacity=0.45)

    parts = []

    # Optional glow layers
    if glow and (glow_inner or glow_outer):
        if glow_outer:
            parts.append(add_glow_layers(core.copy(), bands=t.get_glow("outer_text")))
        if glow_inner:
            parts.append(add_glow_layers(core.copy(), bands=t.get_glow("inner_text")))

    # Optional plate layers
    if plate:
        plate_cfg = t.get_plate("arrow")
        parts.append(build_plate_stack(core, stroke_color=base_color, **plate_cfg))

    # Core arrow on top (slightly scaled to hide edges)
    core_scaled = core.copy().scale(1.001)
    parts.append(core_scaled)

    return VGroup(*parts)


# ---------------------------------------------------------------------------
# Dotted line (for guides or subtle connectors)
# ---------------------------------------------------------------------------


def dotted_line(
    start: Sequence[float] | np.ndarray,
    end: Sequence[float] | np.ndarray,
    *,
    color: Optional[str] = None,
    stroke_width: Optional[float] = None,
    dash_length: float = 0.3,
    gap_length: float = 0.2,
    buff: Optional[float] = None,
) -> VGroup:
    """
    Create a dotted/dashed line styled according to the theme.

    Parameters
    ----------
    start, end:
        Line start and end coordinates.
    color:
        Role or hex string for stroke color.
    stroke_width:
        Optional manual stroke width override.
    dash_length, gap_length:
        Control dash pattern spacing.
    buff:
        Optional spacing applied to both ends to prevent overlap with shapes.

    Returns
    -------
    VGroup
        Group containing a single DashedLine.
    """
    style = t.arrow_style(None)
    base_color = t.get_color(color or style["color"])
    stroke_w = stroke_width or style["stroke_width"]
    buff_val = buff or style["buff"]

    line = DashedLine(
        start,
        end,
        dash_length=dash_length,
        dashed_ratio=dash_length / (dash_length + gap_length),
        stroke_width=stroke_w,
        color=base_color,
    )

    if buff_val and buff_val != 0:
        u = line.get_unit_vector()
        line.put_start_and_end_on(
            np.array(start, dtype=float) + u * buff_val,
            np.array(end, dtype=float) - u * buff_val,
        )

    return VGroup(line)


# ---------------------------------------------------------------------------
# Curved arrow (with same plate/glow treatment)
# ---------------------------------------------------------------------------


def curved_arrow(
    start: np.ndarray,
    end: np.ndarray,
    *,
    angle: float = -0.8,
    color: Optional[str] = None,
    stroke_width: Optional[float] = None,
    plate: bool = True,
    glow: bool = True,
    glow_inner: bool = False,
    glow_outer: bool = True,
) -> VGroup:
    """
    Create a curved arrow with optional glow and plate layers.

    Parameters
    ----------
    start, end:
        Start and end coordinates for the curved arrow.
    angle:
        Curvature angle; negative values curve clockwise.
    color:
        Role or hex color for the stroke (defaults to theme arrow color).
    stroke_width:
        Optional stroke width override.
    plate:
        Whether to add plate layers for depth.
    glow:
        Whether to include glow layers.
    glow_inner, glow_outer:
        Enable or disable inner/outer glow bands.

    Returns
    -------
    VGroup
        Group containing the curved arrow and any attached layers.
    """
    style = t.arrow_style(None)
    base_color = t.get_color(color or style["color"])
    core_width = stroke_width or t.get_stroke("arrow_width")

    core = CurvedArrow(
        start_point=start,
        end_point=end,
        angle=angle,
        color=base_color,
        stroke_width=core_width,
    ).set_fill(opacity=0.0)

    parts = []

    # Optional glow layers
    if glow and (glow_inner or glow_outer):
        if glow_outer:
            parts.append(add_glow_layers(core.copy(), bands=t.get_glow("outer_text")))
        if glow_inner:
            parts.append(add_glow_layers(core.copy(), bands=t.get_glow("inner_text")))

    # Optional plate layers
    if plate:
        plate_cfg = t.get_plate("arrow")
        parts.append(build_plate_stack(core, stroke_color=base_color, **plate_cfg))

    core_scaled = core.copy().scale(1.001)
    parts.append(core_scaled)

    return VGroup(*parts)
