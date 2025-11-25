# src/cosmicanimator/adapters/style/style_helpers.py

"""
Style helper utilities for CosmicAnimator (theme-agnostic).

This module provides:
- Hex detection (`is_hex_color`)
- Role/hex resolver (`resolve_role_or_hex`) with optional external resolver
- Color transforms (`brighten_color`, `darken_color`)
- Glow layer builder (`add_glow_layers`) — defaults via function params
- Plate depth stack builder (`build_plate_stack`) — defaults via function params

Design goals:
- No dependency on `theme.py`.
"""

from __future__ import annotations
from typing import Dict, Iterable, Optional, Sequence, Tuple
from manim import ManimColor, OUT, VGroup, VMobject
from manim.utils.color import color_to_rgb, rgb_to_color
from cosmicanimator.core.theme import current_theme as t


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def is_hex_color(value: str) -> bool:
    """
    Check if a string looks like a valid hex color.

    Parameters
    ----------
    value:
        Candidate string.

    Returns
    -------
    bool
        True if `value` starts with '#' and is in "#RGB" or "#RRGGBB" format.
    """
    if not isinstance(value, str):
        return False
    v = value.strip()
    return v.startswith("#") and len(v) in (4, 7)


def resolve_role_or_hex(name_or_hex: str) -> Dict[str, str]:
    """
    Resolve a role name or raw hex string into a unified color dict.

    Parameters
    ----------
    name_or_hex:
        - Hex string ("#RRGGBB" or "#RGB") → use same value for color/stroke/glow.
        - Role name (e.g. "primary") → resolve via theme.

    Returns
    -------
    dict
        Keys: {"color", "stroke", "glow"}.
    """
    if is_hex_color(name_or_hex):
        hex_color = t.get_color(name_or_hex)
        return {"color": hex_color, "stroke": hex_color, "glow": hex_color}

    role = t.get_role(str(name_or_hex))
    return {
        "color": role.get("color", t.get_color("white")),
        "stroke": role.get("stroke", role.get("color", t.get_color("white"))),
        "glow": role.get("glow", role.get("color", t.get_color("white"))),
    }


# ---------------------------------------------------------------------------
# Color transforms (used for glow variation)
# ---------------------------------------------------------------------------


def brighten_color(hex_color: str, factor: float = 0.25) -> str:
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
    r, g, b = [int(hex_color[i: i + 2], 16) for i in (0, 2, 4)]

    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)

    return f"#{r:02X}{g:02X}{b:02X}"


def darken_color(hex_color: str, factor: float = 0.25) -> str:
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
    r, g, b = [int(hex_color[i: i + 2], 16) for i in (0, 2, 4)]

    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))

    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# Glow helpers
# ---------------------------------------------------------------------------


def _normalize_bands(bands: Iterable) -> list[Tuple[float, float]]:
    """
    Normalize glow band specs into (width_multiplier, opacity) pairs.

    Accepts:
    - list[tuple(width_mul, opacity)]
    - list[dict{"width_mul"|"width", "opacity"}]
    - Any structure returned by a caller

    Returns
    -------
    list[tuple[float, float]]
        Cleaned bands with guaranteed float pairs.
    """
    normalized: list[Tuple[float, float]] = []
    for b in bands:
        if isinstance(b, dict):
            width_mul = float(b.get("width_mul", b.get("width", 1.0)))
            opacity = float(b.get("opacity", 0.1))
            normalized.append((width_mul, opacity))
        elif isinstance(b, (tuple, list)) and len(b) >= 2:
            normalized.append((float(b[0]), float(b[1])))
    return normalized


def build_plate_stack(
    base: VMobject,
    *,
    depth_layers: int = 5,
    layer_gap: float = 0.03,
    shade_bias: float = 0.02,
    stroke_color: str | None = None,
    stroke_opacity: float = 0.55,
    fill_opacity: float = 0.0,
    stroke_width: float = 10.0,
    plate_stroke_scale: float = 0.8,
    shift_vec=None,
) -> VGroup:
    """
    Build a darker, stepped 'plate' stack behind any VMobject.

    Darkens the provided stroke color progressively by `shade_bias`, shifts each
    layer by `layer_gap` along `shift_vec` (default: -OUT), and uses a slightly
    thinner stroke so edges never overtake the top object.

    Returns
    -------
    VGroup
        The stack of plate layers (does NOT include the original `base`).
    """
    if shift_vec is None:
        shift_vec = -OUT

    # Choose the color we darken from
    if stroke_color is None:
        try:
            base_stroke = base.get_stroke_color()
            stroke_hex = base_stroke.to_hex() if hasattr(base_stroke, "to_hex") else str(base_stroke)
        except Exception:
            stroke_hex = "#FFFFFF"
    else:
        stroke_hex = stroke_color

    # Effective stroke width for plate layers (no theme fallback)
    plate_width = float(stroke_width) * float(plate_stroke_scale)

    r, g, b = color_to_rgb(ManimColor(stroke_hex))
    layers = VGroup()

    for i in range(1, depth_layers + 1):
        fade = (i / depth_layers) * float(shade_bias)
        darker = rgb_to_color((r * (1 - fade), g * (1 - fade), b * (1 - fade)))

        layer = base.copy()
        # Keep fill transparent by default to avoid hazing
        layer.set_fill(opacity=float(fill_opacity))
        layer.set_stroke(color=darker, opacity=float(stroke_opacity), width=plate_width)
        layer.shift(i * float(layer_gap) * shift_vec)
        layers.add(layer)

    return layers


def add_glow_layers(
    base: VMobject,
    *,
    glow_color: Optional[str] = None,
    bands: Optional[Sequence[tuple[float, float]]] = None,
    count: int = 4,
    spread: float = 2.0,
    max_opacity: float = 0.20,
    relative_to_stroke: bool = False,
    base_width_override: Optional[float] = None,
    # theme-free width defaults live here
    normal_width: float = 7.0,
    thick_width: float = 10.0,
) -> VGroup:
    """
    Build stroke-only glow layers around a base VMobject.

    Creates progressively larger, more transparent outlines to simulate a
    glowing aura. Layers are simple copies of `base` with increasing stroke
    widths and decreasing opacities.

    Parameters
    ----------
    base:
        The original Manim VMobject to surround with glow layers.
    glow_color:
        Hex or role string. If None, uses the base object's stroke color.
    bands:
        Optional explicit list of glow band definitions, where each band is a
        tuple ``(width_multiplier, opacity)``. If provided, overrides all
        automatic glow band generation.
    count:
        Number of glow bands to generate when `bands` is not given.
        Defaults to 4.
    spread:
        Total width spread multiplier controlling how far the outermost band
        extends beyond the base stroke. Defaults to 2.0.
    max_opacity:
        Opacity of the innermost glow layer. Subsequent layers are scaled down
        from this value. Defaults to 0.20.
    relative_to_stroke:
        If True, each glow band’s width is relative to the base object's current
        stroke width (or `base_width_override` if provided). Otherwise it uses
        fixed theme-free widths (`normal_width` and `thick_width`).
    base_width_override:
        Manually override the stroke width used as the baseline when
        `relative_to_stroke=True`. Has no effect if `relative_to_stroke=False`.
    normal_width:
        Fallback stroke width for non-relative mode (theme-independent).
        Defaults to 7.0.
    thick_width:
        Fallback “thick” stroke width for non-relative mode (theme-independent).
        Defaults to 10.0.

    Returns
    -------
    VGroup
        Group of glow layers (each a VMobject copy with adjusted stroke width
        and opacity). Does *not* include the original `base` object.
    """
    layers = VGroup()

    if relative_to_stroke:
        base_w = float(base_width_override) if base_width_override is not None else float(base.get_stroke_width())
        thick = base_w
    else:
        base_w = float(normal_width)
        thick = float(thick_width)

    extra = max(thick - base_w, base_w * 0.75)

    # Resolve glow color
    if glow_color is not None:
        glow_hex = resolve_role_or_hex(glow_color)["glow"]
    else:
        try:
            glow_hex = base.get_stroke_color().to_hex()
        except Exception:
            glow_hex = "#FFFFFF"

    # Resolve or compute glow bands
    if bands is None:
        steps = max(1, int(count))
        if steps == 3 and abs(max_opacity - 0.20) < 1e-6 and abs(spread - 2.0) < 1e-6:
            bands = [(0.8, 0.10), (1.6, 0.07), (2.4, 0.04)]
        else:
            bands = [
                (
                    i / steps * float(spread),
                    float(max_opacity) * (1.0 - 0.75 * (i / max(1, steps - 1))),
                )
                for i in range(1, steps + 1)
            ]
    else:
        bands = list(bands)

    # Build stroke-only glow layers
    for width_mul, opacity in _normalize_bands(bands):
        layer = base.copy()
        layer.set_fill(opacity=0.0)
        layer.set_stroke(
            color=glow_hex,
            width=base_w + extra * float(width_mul),
            opacity=float(opacity),
        )
        layers.add(layer)

    return layers
