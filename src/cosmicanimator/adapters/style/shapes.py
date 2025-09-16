# src/cosmicanimator/adapters/style/shapes.py

"""
Shape styling helpers for CosmicAnimator.

Provides composable utilities to style any Manim shape (Circle, Square, etc.)
with neon-like aesthetics:
- Fill + stroke colors pulled from the active theme.
- Optional glow layers (inner + outer).
- Automatic scaling from the theme’s base scale.

Depends on:
- `current_theme` (palette, stroke widths, base scale).
- `style_helpers` (`resolve_role_or_hex`, `add_glow_layers`).
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from manim import VMobject, VGroup
from cosmicanimator.core.theme import current_theme as t
from .style_helpers import resolve_role_or_hex, add_glow_layers


# ---------------------------------------------------------------------------
# Color transforms (used for glow variation)
# ---------------------------------------------------------------------------

def _brighten_color(hex_color: str, factor: float = 0.25) -> str:
    """
    Lighten a hex color by mixing it toward white.

    Parameters
    ----------
    hex_color:
        Input hex string (e.g. "#085C83").
    factor:
        Amount of lightening. 0 = no change, 1 = pure white.

    Returns
    -------
    str
        Lightened hex string.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)

    return f"#{r:02X}{g:02X}{b:02X}"


def _darken_color(hex_color: str, factor: float = 0.25) -> str:
    """
    Darken a hex color by mixing it toward black.

    Parameters
    ----------
    hex_color:
        Input hex string (e.g. "#22D3EE").
    factor:
        Amount of darkening. 0 = no change, 1 = pure black.

    Returns
    -------
    str
        Darkened hex string.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))

    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# Styling entry point
# ---------------------------------------------------------------------------

def style_shape(
    shape: VMobject,
    *,
    color: str = "primary",          # theme role or hex
    stroke: Optional[str] = None,    # theme role or hex (overrides fill stroke)
    glow: bool = True,
    scale: Optional[float] = None,
    fill_opacity: float = 0.0,
) -> VGroup:
    """
    Apply CosmicAnimator's neon style (fill, stroke, glow) to a shape.

    Parameters
    ----------
    shape:
        Any Manim VMobject (e.g. Circle, Square).
    color:
        Theme role or hex for fill/stroke/glow triplet.
    stroke:
        Optional override role/hex for stroke color only.
    glow:
        Whether to add inner + outer glow layers.
    scale:
        Optional scale multiplier. If None, uses theme base_scale.
    fill_opacity:
        Opacity of the fill color (0.0 = transparent).

    Returns
    -------
    VGroup
        Composite group containing:
        - optional inner glow
        - optional outer glow
        - styled shape
    """
    cfg: Dict[str, Any] = {
        "color": color,
        "stroke": stroke,
        "glow": glow,
        "scale": scale,
        "fill_opacity": fill_opacity,
    }

    # Resolve fill & stroke
    fill_triplet = resolve_role_or_hex(str(cfg["color"]))
    if cfg["stroke"] is not None:
        stroke_triplet = resolve_role_or_hex(str(cfg["stroke"]))
        stroke_hex = stroke_triplet["stroke"]
    else:
        stroke_hex = fill_triplet["stroke"]

    fill_hex = fill_triplet["color"]
    glow_hex = fill_triplet["glow"]

    # Apply fill + stroke to the base shape
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
    if bool(cfg["glow"]):
        # Inner glow: darker + closer
        inner = add_glow_layers(
            shape.copy(),
            glow_color=_darken_color(glow_hex, 0.50),
            bands=[(0.5, 0.60), (0.9, 0.35), (1.3, 0.18)],
        )
        parts.append(inner)

        # Outer glow: brighter + softer
        outer = add_glow_layers(
            shape.copy(),
            glow_color=_brighten_color(glow_hex, 0.70),
            bands=[(1.0, 0.13), (2.0, 0.10), (3.0, 0.07), (4.0, 0.04), (8.0, 0.02)],
        )
        parts.append(outer)

    parts.append(shape)
    return VGroup(*parts)
