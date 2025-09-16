# src/cosmicanimator/adapters/constants.py

"""
Global style and timing constants for CosmicAnimator.

This file is the **single source of truth** for:
- Video profiles (timing, spacing, typography).
- Canvas settings (aspect, resolution, safe zones).
- Color palettes (light/dark).
- Role triplets (fill/stroke/glow).
- Stroke widths.
- Glow band presets.
- Text variants.
- Arrow styles.
- Defaults/fallbacks for actions/adapters.
- Convenience getters with robust fallbacks.

Extending themes
----------------
- Add a palette to `PALETTES` with a new key.
- Define role triplets and arrow styles as needed.
- Switch `ACTIVE_THEME` to point to your new palette.
"""

from __future__ import annotations
from typing import Dict, Tuple, List, Optional, Any

# ============================================================================
# 0) Global switches
# ============================================================================

VIDEO_PROFILE: str = "short"   # "short" | "long" | "square"
ACTIVE_THEME: str = "light"    # "light" | "dark" (can extend with more keys)

# ============================================================================
# 1) Profiles (timing, spacing, typography)
# ============================================================================

PROFILES: Dict[str, Dict[str, Any]] = {
    "short": {
        "timing": {"wait": 0.30, "fade": 0.40, "highlight": 0.20, "slide": 0.40, "zoom": 0.45, "pulse": 0.60},
        "layout": {"spacing": 1.50, "scale": 0.85},
        "type":   {"title": 36, "label": 26, "subtitle": 30},
    },
    "long": {
        "timing": {"wait": 1.00, "fade": 0.80, "highlight": 0.40, "slide": 0.70, "zoom": 0.75, "pulse": 0.90},
        "layout": {"spacing": 2.20, "scale": 1.00},
        "type":   {"title": 48, "label": 30, "subtitle": 26},
    },
    "square": {
        "timing": {"wait": 0.50, "fade": 0.60, "highlight": 0.30, "slide": 0.50, "zoom": 0.55, "pulse": 0.70},
        "layout": {"spacing": 1.80, "scale": 1.10},
        "type":   {"title": 40, "label": 28, "subtitle": 24},
    },
}

# ============================================================================
# 2) Canvas / aspect / safe zones
# ============================================================================

CANVAS: Dict[str, Dict[str, Any]] = {
    "short":   {"aspect": "vertical",  "resolution": (1080, 1920), "safe": {"top": 3.5, "bottom": -3.5, "left": -2.5, "right": 2.5}},
    "long":    {"aspect": "landscape", "resolution": (1920, 1080), "safe": {"top": 4.0, "bottom": -4.0, "left": -6.0, "right": 6.0}},
    "square":  {"aspect": "square",    "resolution": (1080, 1080), "safe": {"top": 3.0, "bottom": -3.0, "left": -3.0, "right": 3.0}},
}

ASPECT: str = CANVAS[VIDEO_PROFILE]["aspect"]
RESOLUTION: Tuple[int, int] = CANVAS[VIDEO_PROFILE]["resolution"]
SAFE: Dict[str, float] = CANVAS[VIDEO_PROFILE]["safe"]

# ============================================================================
# 3) Palettes (light/dark)
# ============================================================================

LIGHT_PALETTE: Dict[str, str] = {
    # Roles
    "primary":   "#95E6FF",
    "secondary": "#C493FF",
    "success":   "#34D399",
    "warning":   "#FAEB2C",
    "danger":    "#F43F5E",
    "info":      "#FF7878",
    "muted":     "#CBD5E1",
    # Text / background
    "text":      "#FFFFFF",
    "bg":        "#000000",
    # Extra hues
    "cyan":      "#06B6D4",
    "violet":    "#8B5CF6",
    "emerald":   "#10B981",
    "amber":     "#F59E0B",
    "rose":      "#E11D48",
    "slate":     "#64748B",
}

DARK_PALETTE: Dict[str, str] = {
    # Darker neon aesthetics
    "primary":   "#06B6D4",
    "secondary": "#8B5CF6",
    "success":   "#10B981",
    "warning":   "#D97706",
    "danger":    "#E11D48",
    "info":      "#3B82F6",
    "muted":     "#94A3B8",
    "text":      "#E5E7EB",
    "bg":        "#0B0F14",
    "cyan":      "#0891B2",
    "violet":    "#7C3AED",
    "emerald":   "#059669",
    "amber":     "#B45309",
    "rose":      "#BE123C",
    "slate":     "#475569",
}

PALETTES: Dict[str, Dict[str, str]] = {
    "light": LIGHT_PALETTE,
    "dark": DARK_PALETTE,
}


def active_palette() -> Dict[str, str]:
    """Return the currently active color palette dictionary."""
    return PALETTES.get(ACTIVE_THEME, LIGHT_PALETTE)


BACKGROUND_COLOR: str = active_palette()["bg"]
DEFAULT_TEXT_COLOR: str = active_palette()["text"]

# ============================================================================
# 4) Role triplets (fill/stroke/glow)
# ============================================================================


def _tone(hex_base: str, *, stroke_bias: float = -0.10, glow_bias: float = -0.20) -> Tuple[str, str]:
    """
    Derive (stroke_hex, glow_hex) from a base hex.

    stroke_bias/glow_bias:
        - Negative → darken toward black.
        - Positive → lighten toward white.
    """
    def clamp(x: int) -> int: return max(0, min(255, x))

    def to_rgb(h: str) -> Tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def to_hex(rgb: Tuple[int, int, int]) -> str:
        return "#%02X%02X%02X" % rgb

    r, g, b = to_rgb(hex_base)

    def mix(v: int, bias: float) -> int:
        return clamp(int(v * (1.0 + bias))) if bias < 0 else clamp(int(v + (255 - v) * bias))

    stroke = (mix(r, stroke_bias), mix(g, stroke_bias), mix(b, stroke_bias))
    glow = (mix(r, glow_bias), mix(g, glow_bias), mix(b, glow_bias))
    return to_hex(stroke), to_hex(glow)


def _triplet(role_key: str) -> Dict[str, str]:
    base = active_palette().get(role_key, active_palette()["primary"])
    stroke_hex, glow_hex = _tone(base)
    return {"fill": base, "stroke": stroke_hex, "glow": glow_hex}


ROLE_TRIPLETS: Dict[str, Dict[str, str]] = {
    key: _triplet(key) for key in ("primary", "secondary", "success", "warning", "danger", "info", "muted")
}

# ============================================================================
# 5) Stroke widths
# ============================================================================

STROKE_WIDTHS: Dict[str, float] = {
    "thin":        4.0,
    "normal":      7.0,
    "thick":      10.0,
    "extra_thick": 14.0,
}

# Legacy aggregate
STROKE: Dict[str, float] = {
    "shape_width": STROKE_WIDTHS["thick"],
    "arrow_width": STROKE_WIDTHS["normal"],
    "glow_extra":  16.0,
}

# ============================================================================
# 6) Glow band presets
# ============================================================================

GLOW_BANDS: Dict[str, List[Tuple[float, float]]] = {
    "soft":   [(0.6, 0.24), (1.2, 0.14), (1.8, 0.08)],
    "medium": [(0.8, 0.28), (1.6, 0.16), (2.4, 0.10)],
    "strong": [(0.9, 0.40), (1.8, 0.24), (2.7, 0.14), (3.6, 0.08)],
    "neon":   [(0.8, 0.40), (1.4, 0.28), (2.0, 0.16), (2.8, 0.09)],
}

GLOW_DEFAULT: Dict[str, Any] = {
    "bands_key": "neon",
    "bias": (0.0, 0.03, 0.0),  # optional directional bias (x, y, z)
}

# ============================================================================
# 7) Text variants
# ============================================================================

TEXT_VARIANTS: Dict[str, Dict[str, Any]] = {
    "title":    {"font_size": "title",   "color": "primary", "weight": "HEAVY",   "uppercase": False, "line_spacing": 0.95},
    "label":    {"font_size": "label",   "color": "primary", "weight": "BOLD",    "uppercase": False, "line_spacing": 1.00},
    "subtitle": {"font_size": "subtitle","color": "text",    "weight": "SEMIBOLD","uppercase": False, "line_spacing": 1.15},
}

# ============================================================================
# 8) Arrow styles
# ============================================================================

ARROW_STYLES: Dict[str, Dict[str, Any]] = {
    "default": {
        "color": ROLE_TRIPLETS["primary"]["stroke"],
        "stroke_width": STROKE_WIDTHS["normal"],
        "tip_length": 0.30,
        "buff": 0.25,
        "glow_layers": 2,
        "glow_opacity": 0.25,
        "glow_decay": 0.65,
        "dashed": False,
    },
    "dashed": {
        "color": ROLE_TRIPLETS["secondary"]["stroke"],
        "stroke_width": STROKE_WIDTHS["normal"],
        "tip_length": 0.28,
        "buff": 0.25,
        "glow_layers": 0,
        "glow_opacity": 0.00,
        "glow_decay": 0.00,
        "dashed": True,
    },
    "glowing": {
        "color": ROLE_TRIPLETS["primary"]["stroke"],
        "stroke_width": STROKE_WIDTHS["normal"],
        "tip_length": 0.30,
        "buff": 0.25,
        "glow_layers": 3,
        "glow_opacity": 0.30,
        "glow_decay": 0.60,
        "dashed": False,
    },
}

DEFAULT_ARROW_STYLE: Dict[str, Any] = ARROW_STYLES["default"]

# ============================================================================
# 9) Defaults / fallbacks
# ============================================================================

DEFAULTS: Dict[str, Any] = {
    "direction": "horizontal",          # "horizontal" | "vertical"
    "arrow_style": "default",
    "highlight_mode": "simultaneous",   # "simultaneous" | "sequential"
    "easing": "ease_in_out",
    "label_prefix": "Item",
    "shape": "square",
    "color": "primary",
    "stroke": "normal",
}

HIGHLIGHT_MODES: Tuple[str, ...] = ("simultaneous", "sequential")

# ============================================================================
# 10) Convenience getters
# ============================================================================


def p(section: str, key: str) -> Any:
    """Get a profile value like p('timing','fade') or p('type','title')."""
    return PROFILES.get(VIDEO_PROFILE, PROFILES["short"]).get(section, {}).get(key)


def timing(name: str) -> float:
    """Shortcut for timing values in the active profile (fallback 0.5)."""
    return float(p("timing", name) or 0.5)


def spacing() -> float:
    """Base spacing from the active profile (fallback 1.5)."""
    return float(p("layout", "spacing") or 1.5)


def base_scale() -> float:
    """Base scale multiplier from the active profile (fallback 1.0)."""
    return float(p("layout", "scale") or 1.0)


def font_size(kind: str) -> int:
    """Resolve a text size name to px (fallback: label or 24)."""
    sizes = PROFILES.get(VIDEO_PROFILE, PROFILES["short"]).get("type", {})
    return int(sizes.get(kind, sizes.get("label", 24)))


def get_color(name: str) -> str:
    """
    Return a hex color for a palette key or a raw hex string.

    Fallback: DEFAULT_TEXT_COLOR.
    """
    if isinstance(name, str) and name.startswith("#") and len(name) in (4, 7):
        return name
    return active_palette().get(name, DEFAULT_TEXT_COLOR)


def get_role(role: str) -> Dict[str, str]:
    """Return role triplet dict {fill, stroke, glow}. Fallback: 'primary'."""
    return ROLE_TRIPLETS.get(role, ROLE_TRIPLETS["primary"])


def get_stroke(kind: Optional[str]) -> float:
    """Return stroke width by name. Fallback: 'normal'."""
    key = (kind or "").strip().lower()
    return STROKE_WIDTHS.get(key, STROKE_WIDTHS["normal"])


def get_glow(preset: Optional[str]) -> List[Tuple[float, float]]:
    """Return glow bands preset. Fallback: GLOW_DEFAULT['bands_key']."""
    key = (preset or "").strip().lower()
    return GLOW_BANDS.get(key, GLOW_BANDS[GLOW_DEFAULT["bands_key"]])


def get_text_variant(name: Optional[str]) -> Dict[str, Any]:
    """Return a text variant config. Fallback: 'label'."""
    return TEXT_VARIANTS.get((name or "label"), TEXT_VARIANTS["label"])


def arrow_style(name: Optional[str]) -> Dict[str, Any]:
    """Return an arrow style dict. Fallback: 'default'."""
    return ARROW_STYLES.get((name or "default"), ARROW_STYLES["default"])

# ============================================================================
# 11) Setting resolver
# ============================================================================


def resolve_setting(
    key: str,
    step: Optional[Dict[str, Any]],
    scene_defaults: Optional[Dict[str, Any]],
    video_defaults: Optional[Dict[str, Any]],
    code_default: Any,
) -> Any:
    """
    Resolve a setting by priority:
    step → scene_defaults → video_defaults → code_default.

    This allows JSON scenarios to override per-step values cleanly.
    """
    if step and key in step and step[key] is not None:
        return step[key]
    if scene_defaults and key in scene_defaults and scene_defaults[key] is not None:
        return scene_defaults[key]
    if video_defaults and key in video_defaults and video_defaults[key] is not None:
        return video_defaults[key]
    return code_default
