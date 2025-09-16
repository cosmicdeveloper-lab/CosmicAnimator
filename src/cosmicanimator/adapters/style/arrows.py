# src/cosmicanimator/adapters/style/arrows.py

"""
Arrow and line drawing helpers with CosmicAnimator’s neon visual style.

These helpers:
- Use theme defaults from `current_theme` (arrow style, palette, stroke widths).
- Apply consistent glow treatment to arrows (solid core + widened translucent strokes).
- Provide predictable variants: `glow_arrow`, `dotted_line`, `curved_arrow`.

Design notes
------------
- These functions never modify caller timing/animation logic.
- They only create styled Manim mobjects.
- Callers can override color, widths, and tip sizes via keyword args.
"""

from __future__ import annotations
from typing import Optional, Sequence
import numpy as np
from manim import VGroup, Arrow, DashedLine, CurvedArrow
from cosmicanimator.core.theme import current_theme as t

# Default (width multiplier, opacity) pairs for glow bands
_DEFAULT_GLOW_BANDS: list[tuple[float, float]] = [
    (1.5, 0.12),
    (2.5, 0.07),
    (3.5, 0.04),
]


# ---------------------------------------------------------------------------
# Glow arrow
# ---------------------------------------------------------------------------

def glow_arrow(
    start: Sequence[float] | np.ndarray,
    end: Sequence[float] | np.ndarray,
    *,
    color: Optional[str] = None,
    stroke_width: Optional[float] = None,
    tip_length: Optional[float] = None,
    buff: Optional[float] = None,
) -> VGroup:
    """
    Create an arrow with multi-band glow layers behind a solid core arrow.

    Parameters
    ----------
    start, end:
        3D points (array-like) defining the arrow.
    color:
        Override arrow color. If None, use theme arrow color.
    stroke_width:
        Override main stroke width. Defaults to theme.
    tip_length:
        Override arrow tip length. Defaults to theme.
    buff:
        Gap from endpoints (shortens the arrow line). Defaults to theme.

    Returns
    -------
    VGroup
        Group containing (glow_layers, arrow). The arrow is the last element.
    """
    style = t.arrow_style(None)
    base_color = t.get_color(color or style["color"])
    stroke_w = stroke_width if stroke_width is not None else style["stroke_width"]
    tip_len = tip_length if tip_length is not None else style["tip_length"]
    buff_val = buff if buff is not None else style["buff"]

    # Solid core arrow
    arrow = Arrow(
        start,
        end,
        buff=buff_val,
        stroke_width=stroke_w,
        color=base_color,
        tip_length=tip_len,
    ).set_fill(opacity=0.85)

    # Glow layers = widened strokes behind the core arrow
    glow_layers = VGroup(
        *[
            arrow.copy()
            .set_fill(opacity=0.0)
            .set_stroke(color=base_color, width=stroke_w * mul, opacity=op)
            for mul, op in _DEFAULT_GLOW_BANDS
        ]
    )
    return VGroup(glow_layers, arrow)


# ---------------------------------------------------------------------------
# Dotted line
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
    Create a dashed (dotted-style) line between two points.

    Parameters
    ----------
    start, end:
        3D points defining the line.
    color:
        Override line color. Defaults to theme arrow color.
    stroke_width:
        Override line stroke width. Defaults to theme arrow width.
    dash_length, gap_length:
        Control dash pattern. Effective dashed_ratio = dash_length / (dash+gap).
    buff:
        If provided, shortens the line at both ends by this amount.

    Returns
    -------
    VGroup
        Group containing a DashedLine.
    """
    style = t.arrow_style(None)
    base_color = t.get_color(color or style["color"])
    stroke_w = stroke_width if stroke_width is not None else style["stroke_width"]
    buff_val = buff if buff is not None else style["buff"]

    line = DashedLine(
        start,
        end,
        dash_length=dash_length,
        dashed_ratio=dash_length / (dash_length + gap_length),
        stroke_width=stroke_w,
        color=base_color,
    )

    # Apply buffer: shift start/end points inward along line direction
    if buff_val and buff_val != 0:
        u = line.get_unit_vector()
        line.put_start_and_end_on(
            np.array(start, dtype=float) + u * buff_val,
            np.array(end, dtype=float) - u * buff_val,
        )

    return VGroup(line)


# ---------------------------------------------------------------------------
# Curved arrow
# ---------------------------------------------------------------------------

def curved_arrow(
    start: np.ndarray,
    end: np.ndarray,
    *,
    angle: float = -0.8,
    color: Optional[str] = None,
    stroke_width: float | None = None,
) -> VGroup:
    """
    Create a curved arrow with glow layers.

    Parameters
    ----------
    start, end:
        3D NumPy arrays for endpoints.
    angle:
        Bend amount. Negative → clockwise relative to chord.
    color:
        Override arrow color. Defaults to theme.
    stroke_width:
        Override stroke width. Defaults to theme arrow width for glow layers.

    Returns
    -------
    VGroup
        Group containing (glow_layers, CurvedArrow).
    """
    style = t.arrow_style(None)
    base_color = t.get_color(color or style["color"])
    stroke_w = stroke_width if stroke_width is not None else style["stroke_width"]

    # Core curved arrow (stroke width = arrow_width theme key, not stroke_w)
    arrow = CurvedArrow(
        start_point=start,
        end_point=end,
        angle=angle,
        color=base_color,
        stroke_width=(stroke_width or t.get_stroke("arrow_width")),
    )

    # Glow layers behind curved arrow
    glow_layers = VGroup(
        *[
            arrow.copy()
            .set_fill(opacity=0.0)
            .set_stroke(color=base_color, width=stroke_w * mul, opacity=op)
            for mul, op in _DEFAULT_GLOW_BANDS
        ]
    )

    return VGroup(glow_layers, arrow)
