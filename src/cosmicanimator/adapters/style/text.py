# src/cosmicanimator/adapters/style/text.py

"""
Text styling helpers for CosmicAnimator.

Implements the same “plate + glow” aesthetic used by shapes and arrows:
- Optional inner/outer glow bands (via `add_glow_layers`).
- Plate-style depth stack (via `build_plate_stack`).
- Optional crisp offset shadow (for contrast).
- Variant-based theme lookups for font size, color, stroke, etc.

Depends on:
- `cosmicanimator.core.theme.current_theme` as `t`
- `adapters/style/style_helpers`: `resolve_role_or_hex`, `add_glow_layers`
"""

from __future__ import annotations
from typing import Optional, Union, Dict, Any
from manim import Text, VGroup, UP, RIGHT
from cosmicanimator.core.theme import current_theme as t
from .style_helpers import (
    resolve_role_or_hex,
    add_glow_layers,
    brighten_color,
    darken_color,
    build_plate_stack,
)

# ---------------------------------------------------------------------------
# Stroke scaling
# ---------------------------------------------------------------------------


def _scaled_stroke(font_px: float, stroke_width: float) -> float:
    """
    Compute effective stroke width.

    Notes
    -----
    - Values < 2.0 are treated as a fraction of the font size.
    - Values ≥ 2.0 are interpreted as absolute pixel width.
    """
    sw = float(stroke_width or 0.0)
    return font_px * sw if sw < 2.0 else sw


# ---------------------------------------------------------------------------
# Variant merging
# ---------------------------------------------------------------------------


def _merge_variant(variant: Optional[str], **overrides) -> Dict[str, Any]:
    """
    Merge a text variant with explicit parameter overrides.

    Parameters
    ----------
    variant:
        Variant name from theme, or None.
    overrides:
        Keyword overrides to merge into the base variant dict.

    Returns
    -------
    dict
        Consolidated configuration dictionary for text styling.
    """
    base: Dict[str, Any] = {}

    if variant:
        v = t.get_text_variant(variant)
        if isinstance(v, dict):
            base = dict(v)

    if not base:
        base = {
            "font_size": "label",
            "color": "primary",
            "weight": "BOLD",
            "stroke_width": 0.0,
            "uppercase": False,
            "line_spacing": 1.0,
            # optional: "shadow": {"dx": 1, "dy": -1, "alpha": 0.5}
        }

    for k, v in overrides.items():
        if v is not None:
            base[k] = v

    return base


# ---------------------------------------------------------------------------
# Crisp offset shadow
# ---------------------------------------------------------------------------


def _wrap_with_shadow(text_obj: Text, shadow_cfg: Dict[str, Any] | None) -> VGroup:
    """
    Create a crisp offset shadow behind a Text object.

    Parameters
    ----------
    text_obj:
        The Manim Text object to wrap.
    shadow_cfg:
        Dictionary with keys {"dx", "dy", "alpha"} controlling shadow offset
        (in percent of text size) and opacity.

    Returns
    -------
    VGroup
        Group containing [shadow (if enabled), text].
    """
    group = VGroup()
    if shadow_cfg:
        sh = text_obj.copy()
        sh.set_fill("#000000", opacity=float(shadow_cfg.get("alpha", 0.5)))
        dx = float(shadow_cfg.get("dx", 1)) * 0.01
        dy = float(shadow_cfg.get("dy", -1)) * 0.01
        sh.shift(RIGHT * dx + UP * dy)
        group.add(sh)

    group.add(text_obj)
    return group


# ---------------------------------------------------------------------------
# Font size resolution
# ---------------------------------------------------------------------------


def _resolve_font_px(size: Union[int, float, str, None]) -> float:
    """
    Resolve a font size identifier or numeric value to absolute pixels.

    Parameters
    ----------
    size:
        May be:
        - a number (interpreted directly as pixels),
        - a variant key (e.g. "label", "title"),
        - None (uses the "label" variant default).

    Returns
    -------
    float
        Font size in pixels.
    """
    if size is None:
        return float(t.font_px(t.get_text_variant("label")["font_size"]))
    if isinstance(size, (int, float)):
        return float(size)
    return float(t.font_px(size))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def style_text(
    text: str,
    *,
    variant: Optional[str] = None,
    font_size: Union[int, float, str, None] = None,
    color: Optional[str] = None,
    weight: Optional[str] = None,
    disable_ligatures: bool = True,
    stroke_width: Optional[float] = None,
    stroke_color: Optional[str] = None,
    uppercase: Optional[bool] = None,
    line_spacing: Optional[float] = None,
    glow: bool = True,
    glow_inner: bool = False,
    glow_outer: bool = True,
    plate: bool = True,
    shadow: bool = True,
) -> VGroup:
    """
    Create styled text with theme-driven settings and cosmic glow effects.

    Composition:
        [ optional outer glow, optional inner glow, optional plate layers, core text (+shadow wrapper) ]

    Parameters
    ----------
    text:
        The text content.
    variant:
        Theme text variant (e.g. "title", "label").
    font_size:
        Explicit font size override (numeric or variant key).
    color:
        Role or hex string for fill color.
    weight:
        Font weight (e.g. "BOLD", "SEMIBOLD").
    disable_ligatures:
        If True, disables font ligatures for clarity.
    stroke_width:
        Stroke width (absolute or relative, see `_scaled_stroke`).
    stroke_color:
        Role or hex string for stroke color.
    uppercase:
        Whether to convert text to uppercase.
    line_spacing:
        Line spacing factor.
    glow:
        Whether to include glow layers.
    glow_inner, glow_outer:
        Enable or disable specific glow types.
    plate:
        Whether to add plate-style layered depth.
    shadow:
        Whether to include a crisp offset shadow.

    Returns
    -------
    VGroup
        A Manim group containing the complete styled text stack.
    """
    cfg = _merge_variant(
        variant,
        font_size=font_size,
        color=color,
        weight=weight,
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        uppercase=uppercase,
        line_spacing=line_spacing,
        shadow=(cfg_shadow := (shadow and {"dx": 1, "dy": -1, "alpha": 0.5}) or None),
    )

    content = text.upper() if cfg.get("uppercase") else text
    size_px = _resolve_font_px(cfg["font_size"])

    # Resolve color roles → hex triplet
    fill_triplet = resolve_role_or_hex(str(cfg["color"]))

    fill_hex = fill_triplet["color"]
    glow_hex = fill_triplet["glow"]

    if cfg.get("stroke_color"):
        stroke_triplet = resolve_role_or_hex(str(cfg["stroke_color"]))
        stroke_hex = stroke_triplet["stroke"]
    else:
        # Fallback: use stroke associated with fill role
        stroke_hex = fill_triplet["stroke"]

    # Build base text
    txt = Text(
        content,
        font_size=size_px,
        weight=cfg.get("weight", "BOLD"),
        disable_ligatures=disable_ligatures,
        line_spacing=float(cfg.get("line_spacing", 1.0)),
    ).set_fill(t.get_color(fill_hex))

    sw = float(cfg.get("stroke_width") or 0.0)
    sw = _scaled_stroke(size_px, sw)
    if sw > 0:
        txt.set_stroke(t.get_color(stroke_hex), width=sw, opacity=1.0)

    core_group = _wrap_with_shadow(txt, cfg.get("shadow") if shadow else None)

    parts = []

    # Optional glow layers
    if glow and (glow_inner or glow_outer):
        if glow_outer:
            parts.append(
                add_glow_layers(
                    txt.copy(),
                    glow_color=brighten_color(glow_hex, 0.5),
                    bands=t.get_glow("outer_text"),
                )
            )
        if glow_inner:
            parts.append(
                add_glow_layers(
                    txt.copy(),
                    glow_color=darken_color(glow_hex, 0.40),
                    bands=t.get_glow("inner_tight"),
                )
            )

    # Optional plate stack
    if plate:
        plate_cfg = t.get_plate("text")
        parts.append(build_plate_stack(txt, stroke_color=stroke_hex, **plate_cfg))

    # Core text (with shadow) slightly scaled up to ensure clean overlap
    core_cover = core_group.copy().scale(1.002)
    parts.append(core_cover)

    return VGroup(*parts)
