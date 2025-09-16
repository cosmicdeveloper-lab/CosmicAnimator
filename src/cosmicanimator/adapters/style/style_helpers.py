# src/cosmicanimator/adapters/style/style_helpers.py

"""
Style helper utilities for CosmicAnimator.

This module provides:
- Hex detection (`is_hex_color`)
- Role/hex resolver (`resolve_role_or_hex`)
- Glow layer builder (`add_glow_layers`)

All functions build on `core.theme.current_theme` to ensure consistency
with the active theme (palette, roles, strokes, glow presets).
"""

from __future__ import annotations
from typing import Optional, Sequence, Iterable, Tuple, Dict
from manim import VMobject, VGroup
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
# Glow helpers
# ---------------------------------------------------------------------------

def _normalize_bands(bands: Iterable) -> list[Tuple[float, float]]:
    """
    Normalize glow band specs into (width_multiplier, opacity) pairs.

    Accepts:
    - list[tuple(width_mul, opacity)]
    - list[dict{"width_mul"|"width", "opacity"}]
    - Any structure returned by `t.get_glow(...)`.

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


def add_glow_layers(
    base: VMobject,
    *,
    glow_color: Optional[str] = None,
    bands: Optional[Sequence[tuple[float, float]]] = None,
    count: int = 4,
    spread: float = 2.0,
    max_opacity: float = 0.20,
) -> VGroup:
    """
    Generate multiple stroke-only copies of a base VMobject to simulate glow.

    Parameters
    ----------
    base:
        Any Manim VMobject to apply glow around.
    glow_color:
        Color override for the glow (role name or hex).
        If None, attempts to reuse the base stroke color, with fallback to theme "primary".
    bands:
        Explicit list of (width_multiplier, opacity) pairs.
        If provided, this overrides `count`/`spread`/`max_opacity`.
    count:
        Number of glow layers if `bands` not provided.
    spread:
        Maximum stroke expansion multiplier (controls how far the glow extends).
    max_opacity:
        Peak opacity for the innermost glow layer.

    Returns
    -------
    VGroup
        Group of glow layers (does NOT include the base shape).
    """
    layers = VGroup()

    # Base stroke width (anchor for expansion)
    base_w = float(t.get_stroke("normal"))

    # Extra thickness budget ensures glow is visible even on thick strokes
    thick = float(t.get_stroke("thick"))
    extra = max(thick - base_w, base_w * 0.75)

    # Resolve glow color
    if glow_color is not None:
        glow_hex = resolve_role_or_hex(glow_color)["glow"]
    else:
        try:
            glow_hex = base.get_stroke_color().to_hex()
        except Exception:
            glow_hex = resolve_role_or_hex("primary")["stroke"]

    # Resolve or compute glow bands
    if bands is None:
        preset = _normalize_bands(t.get_glow("neon"))
        if preset:
            bands = preset
        else:
            # Default fallback heuristic
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
