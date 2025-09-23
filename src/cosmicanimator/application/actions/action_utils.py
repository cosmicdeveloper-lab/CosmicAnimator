# src/cosmicanimator/application/actions/action_utils.py

"""
Utility helpers for building action shapes and labels.

Provides
--------
- Shape registry (`SHAPE_REGISTRY`) with basic polygons and stars.
- `make_unit_shape`: build a normalized shape by kind or callable.
- `apply_label`: attach styled labels to shapes/arrows.

Notes
-----
- Shapes are created at unit-ish size (consistent across kinds).
- Labels are styled via `style_text` with variant `"label"`.
- For arrows/lines, labels are placed near the midpoint.
"""

from __future__ import annotations
from typing import Optional, Union, Callable

from manim import (
    VGroup, Mobject, UP, RIGHT, DOWN,
    Square, Circle, Triangle, RegularPolygon, Star, Ellipse,
    Line, Arrow, CurvedArrow,
)
from cosmicanimator.adapters.style import style_text


ShapeKind = Union[str, Callable[[], Mobject]]


# ---------------------------------------------------------------------------
# Shape registry
# ---------------------------------------------------------------------------

SHAPE_REGISTRY = {
    "square":   lambda: Square(),
    "circle":   lambda: Circle(),
    "triangle": lambda: Triangle(),
    "pentagon": lambda: RegularPolygon(n=5),
    "hexagon":  lambda: RegularPolygon(n=6),
    "star":     lambda: Star(n=5),
    "ellipse":  lambda: Ellipse(width=2.0, height=1.2),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def make_unit_shape(kind: ShapeKind, size: float = 1.0) -> Mobject:
    """
    Build a unit-sized shape.

    Parameters
    ----------
    kind : str | Callable[[], Mobject]
        - String key (e.g., "circle", "hexagon").
        - Callable producing a Manim mobject.
    size : float, optional
    Scaling factor. Defaults to 1.0.

    Returns
    -------
    Mobject
        The constructed shape.

    Notes
    -----
    Defaults to a square if kind is unknown.
    """
    if callable(kind):
        shape = kind()
    else:
        key = str(kind).lower()
        shape = SHAPE_REGISTRY.get(key, SHAPE_REGISTRY["square"])()

    # Apply uniform scaling
    if size != 1.0:
        shape.scale(size)

    return shape


def apply_label(
    basic_group: VGroup | Mobject,
    text: str,
    *,
    outside: bool = True,
    label_color: Optional[str] = None,
    padding: float = 0.20,
    inside_scale: float = 0.75,
) -> VGroup:
    """
    Attach a styled label to a shape or arrow.

    Parameters
    ----------
    basic_group : VGroup | Mobject
        Shape or arrow to attach label to.
    text : str
        Label string. If empty, the group is returned unchanged.
    outside : bool, default=True
        - For shapes: if True, place below the shape. If False, place inside.
        - For arrows/lines: ignored (always midpoint placement).
    label_color : str, optional
        Color override for the text.
    padding : float, default=0.20
        Spacing offset.
    inside_scale : float, default=0.75
        Max proportion of base width/height the label may occupy.

    Returns
    -------
    VGroup
        Group containing the base object and its label.
    """
    if not text:
        return basic_group

    # Determine base element (shape or arrow)
    if isinstance(basic_group, (Line, Arrow, CurvedArrow)):
        base = basic_group
    elif isinstance(basic_group, VGroup):
        base = basic_group[-1]
    else:
        base = basic_group

    lbl = style_text(text, variant="label", color=label_color)

    if isinstance(base, (Line, Arrow, CurvedArrow)):
        # Place label at midpoint, offset by orientation
        start, end = base.get_start(), base.get_end()
        v = end - start
        if abs(v[0]) >= abs(v[1]):  # mostly horizontal
            lbl.move_to(base.get_top() + padding * 1.5 * UP)
        else:  # mostly vertical
            lbl.move_to(base.get_right() + padding * 3 * RIGHT)
        lbl.set_z_index(getattr(base, "z_index", 0) + 1)

    else:
        if outside:
            lbl.next_to(base, DOWN, buff=padding)
        else:
            lbl.move_to(base.get_center())
            # Shrink to fit inside
            max_w = getattr(base, "width", None)
            max_h = getattr(base, "height", None)
            if max_w and lbl.width > max_w * inside_scale:
                lbl.set_width(max_w * inside_scale)
            if max_h and lbl.height > max_h * inside_scale:
                lbl.set_height(max_h * inside_scale)
        lbl.set_z_index(getattr(base, "z_index", 0) + 1)

    return VGroup(basic_group, lbl)
