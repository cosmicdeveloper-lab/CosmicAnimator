# src/cosmicanimator/adapters/style/text.py

"""
Text styling helpers for CosmicAnimator.

Provides `style_text` to create Manim Text objects with theme-driven styling:

- Variant presets (size, weight, color, spacing).
- Uppercase transform (for subtitles/headlines).
- Stroke width scaling relative to font size.
- Optional stroke color override.
- Lightweight shadow layers (duplicated + offset, no GPU blur).

Depends on `core.theme.current_theme` for size tokens, roles, and colors.
"""

from __future__ import annotations
from typing import Optional, Union, Dict, Any
from manim import Text, VGroup, UP, RIGHT
from cosmicanimator.core.theme import current_theme as t


# ---------------------------------------------------------------------------
# Stroke scaling
# ---------------------------------------------------------------------------

def _scaled_stroke(font_px: float, stroke_width: float) -> float:
    """
    Scale stroke width depending on value range.

    Rules
    -----
    - If `stroke_width < 2.0`: interpret as *relative fraction* of font size
      (e.g., 0.05 = 5% of font size).
    - If `stroke_width >= 2.0`: interpret as *absolute pixels*.

    Parameters
    ----------
    font_px:
        Resolved font size in pixels.
    stroke_width:
        Requested stroke width (fraction or px).

    Returns
    -------
    float
        Final stroke width in pixels.
    """
    sw = float(stroke_width or 0.0)
    return font_px * sw if sw < 2.0 else sw


# ---------------------------------------------------------------------------
# Variant merging
# ---------------------------------------------------------------------------

def _merge_variant(variant: Optional[str], **overrides) -> Dict[str, Any]:
    """
    Merge a text variant from the theme with caller overrides.

    Parameters
    ----------
    variant:
        Variant name (e.g., "title", "label", "subtitle").
    overrides:
        Explicit overrides like font_size, color, uppercase, etc.

    Returns
    -------
    dict
        Complete text config (merged).
    """
    base: Dict[str, Any] = {}
    if variant:
        v = t.get_text_variant(variant)
        if isinstance(v, dict):
            base = dict(v)  # shallow copy

    if not base:
        # Fallback defaults if no variant is found
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
# Shadows
# ---------------------------------------------------------------------------

def _wrap_with_shadow(text_obj: Text, shadow_cfg: Dict[str, Any] | None) -> VGroup:
    """
    Add a lightweight shadow by duplicating and offsetting text.

    Implementation
    --------------
    - Creates a copy of the text.
    - Fills it with black at reduced opacity.
    - Offsets by a small dx/dy.
    - Groups with the original text.

    Notes
    -----
    - This is *not* blurred — just a crisp offset.
    - Optimized for short-form video rendering speed.

    Returns
    -------
    VGroup
        Group containing optional shadow + the original text.
    """
    group = VGroup()  # always return a group for stability
    if shadow_cfg:
        sh = text_obj.copy()
        sh.set_fill("#000000", opacity=float(shadow_cfg.get("alpha", 0.5)))
        # Offset in scene units (small for subtlety)
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
    Resolve a font size spec into absolute pixels using theme.

    Behavior
    --------
    - None → theme "label" preset.
    - int/float → absolute px value.
    - str → token name (e.g., "title", "subtitle") resolved via theme.

    Returns
    -------
    float
        Resolved size in pixels.
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
    color: Optional[str] = None,        # theme role or hex
    weight: Optional[str] = None,
    disable_ligatures: bool = True,
    stroke_width: Optional[float] = None,
    stroke_color: Optional[str] = None,  # theme role or hex
    uppercase: Optional[bool] = None,
    line_spacing: Optional[float] = None,
) -> VGroup:
    """
    Create styled text according to theme variants and overrides.

    Parameters
    ----------
    text:
        Content string.
    variant:
        Theme variant name ("title", "label", "subtitle", etc.).
    font_size:
        Explicit font size (int px) or variant token.
    color:
        Text color (theme role or hex). Defaults to variant/theme.
    weight:
        Font weight (e.g., "BOLD", "LIGHT"). Defaults to variant/theme.
    disable_ligatures:
        Disable font ligatures (improves clarity in code-style fonts).
    stroke_width:
        Outline thickness. <2.0 = fraction of font size, else pixels.
    stroke_color:
        Outline color (theme role or hex). Falls back to fill color.
    uppercase:
        Convert text to uppercase if True.
    line_spacing:
        Vertical spacing between lines.

    Returns
    -------
    VGroup
        Styled Manim Text object, optionally with shadow layers.
    """
    # Merge arguments with variant defaults
    cfg = _merge_variant(
        variant,
        font_size=font_size,
        color=color,
        weight=weight,
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        uppercase=uppercase,
        line_spacing=line_spacing,
    )

    # Uppercase transform
    content = text.upper() if cfg.get("uppercase") else text

    # Resolve font size in px
    size_px = _resolve_font_px(cfg["font_size"])

    # Base Manim Text object
    txt = Text(
        content,
        font_size=size_px,
        weight=cfg.get("weight", "BOLD"),
        disable_ligatures=disable_ligatures,
        line_spacing=float(cfg.get("line_spacing", 1.0)),
    ).set_fill(t.get_color(cfg["color"]))

    # Apply stroke if configured
    sw = float(cfg.get("stroke_width") or 0.0)
    sw = _scaled_stroke(size_px, sw)
    if sw > 0:
        stroke_key = cfg.get("stroke_color") or cfg["color"]
        txt.set_stroke(t.get_color(stroke_key), width=sw, opacity=1.0)

    # Wrap in optional shadow
    shadow_cfg = cfg.get("shadow")
    return _wrap_with_shadow(txt, shadow_cfg)
