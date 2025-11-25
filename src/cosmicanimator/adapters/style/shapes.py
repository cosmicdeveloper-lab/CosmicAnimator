# src/cosmicanimator/adapters/style/shapes.py

"""
Shape styling helpers for CosmicAnimator.

Provides composable utilities to style any Manim shape (Circle, Square, etc.)
with neon-like aesthetics:

- Fill and stroke colors pulled from the active theme.
- Optional glow layers (inner and outer).
- Optional plate stack and soft shadow.
- Automatic scaling based on the theme’s base scale.

Depends on:
- `current_theme` (palette, stroke widths, base scale).
- `style_helpers` (`resolve_role_or_hex`, `add_glow_layers`, etc.).
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from manim import (
    VMobject, Square, Circle, Triangle,
    VGroup,
    OUT,
    DOWN,
    RIGHT,
)
from cosmicanimator.core.theme import current_theme as t
from .style_helpers import (
    resolve_role_or_hex,
    add_glow_layers,
    darken_color,
    brighten_color,
    build_plate_stack,
)


# ---------------------------------------------------------------------------
# Styling entry point
# ---------------------------------------------------------------------------


def style_shape(
    shape: VMobject,
    *,
    color: str = "primary",
    stroke: Optional[str] = None,
    glow: bool = True,
    scale: Optional[float] = None,
    fill_opacity: float = 0.0,
    glow_inner: bool = False,
    glow_outer: bool = True,
    plate: bool = True,
    shadow: bool = False,
) -> VGroup:
    """
    Apply full theme-based styling to a shape (fill, stroke, glow, plate, shadow).

    Parameters
    ----------
    shape:
        Base Manim VMobject (e.g., Circle, Square) to style.
    color:
        Fill role or hex string (default: "primary").
    stroke:
        Optional stroke role or hex color. Defaults to same as `color`.
    glow:
        Whether to add glow layers at all. Defaults to True.
    scale:
        Optional scaling factor. If None, uses `t.base_scale()`.
    fill_opacity:
        Opacity for the main fill color (0.0 = fully transparent).
    glow_inner:
        Whether to include a tight inner glow (usually darker tone).
    glow_outer:
        Whether to include a broader outer glow (usually brighter tone).
    plate:
        Whether to add plate-style stacked layers behind the shape.
    shadow:
        Whether to add a soft black offset shadow behind the plate.

    Returns
    -------
    VGroup
        Group containing the styled shape (and optional glow, plate, shadow).
    """
    cfg: Dict[str, Any] = {
        "color": color,
        "stroke": stroke,
        "glow": glow,
        "scale": scale,
        "fill_opacity": fill_opacity,
    }

    # Resolve fill and stroke colors
    fill_triplet = resolve_role_or_hex(str(cfg["color"]))
    if cfg["stroke"] is not None:
        stroke_triplet = resolve_role_or_hex(str(cfg["stroke"]))
        stroke_hex = stroke_triplet["stroke"]
    else:
        stroke_hex = fill_triplet["stroke"]

    fill_hex = fill_triplet["color"]
    glow_hex = fill_triplet["glow"]

    # Apply fill and stroke to the base shape
    shape.set_fill(color=fill_hex, opacity=float(cfg["fill_opacity"]))
    shape.set_stroke(
        color=stroke_hex,
        width=max(float(t.get_stroke("normal")), 6.0),  # enforce minimum width
    )

    # Apply scaling
    s = cfg["scale"] if cfg["scale"] is not None else float(t.base_scale())
    if s != 1.0:
        shape.scale(float(s))

    parts = []

    # Add glow layers (outer and/or inner)
    if glow and (glow_inner or glow_outer):
        if glow_outer:
            parts.append(
                add_glow_layers(
                    shape.copy(),
                    glow_color=brighten_color(glow_hex, 0.5),
                    bands=t.get_glow("outer_shape"),
                )
            )
        if glow_inner:
            parts.append(
                add_glow_layers(
                    shape.copy(),
                    glow_color=darken_color(glow_hex, 0.40),
                    bands=t.get_glow("inner_tight"),
                )
            )

    # Add plate and shadow
    if plate:
        plate_cfg = t.get_plate("shape")
        layers = build_plate_stack(shape, stroke_color=stroke_hex, **plate_cfg)
        parts.append(layers)

        styled_top = VGroup(*parts, shape)
        styled_top.scale(1.002)
        plate_group = VGroup(layers, styled_top)

        if shadow:
            sh = shape.copy()
            sh.set_fill(opacity=0.0)
            sh.set_stroke(
                color="#000000",
                opacity=0.35,
                width=t.get_stroke("extra_thick"),
            )
            sh.scale(1.05)
            sh.shift(0.25 * DOWN + 0.25 * RIGHT + 0.8 * OUT)
            return VGroup(sh, plate_group)

        return plate_group

    # Fallback (only glow layers)
    return VGroup(*parts)
