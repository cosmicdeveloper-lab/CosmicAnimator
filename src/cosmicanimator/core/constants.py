# src/cosmicanimator/core/constants.py

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
"""

from __future__ import annotations
from typing import Dict, Tuple, List, Optional, Any

# ============================================================================
# Global switches
# ============================================================================

VIDEO_PROFILE: str = "short"   # "short" | "long" | "square"
ACTIVE_THEME: str = "light"    # "light" | "dark" (can extend with more keys)

# ============================================================================
# Profiles (timing, spacing, typography)
# ============================================================================

PROFILES: Dict[str, Dict[str, Any]] = {
    "short": {
        "timing": {"wait": 0.30, "fade": 0.40, "highlight": 0.20, "slide": 0.40, "zoom": 0.45, "pulse": 0.60},
        "layout": {"spacing": 1.50, "scale": 0.85},
        "type":   {"title": 70, "label": 26, "subtitle": 28},
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
# Canvas / aspect / safe zones
# ============================================================================

CANVAS: Dict[str, Dict[str, Any]] = {
    "short":   {"aspect": "vertical",  "resolution": (1080, 1920),
                "safe": {"top": 3.5, "bottom": -3.5, "left": -2.5, "right": 2.5}},

    "long":    {"aspect": "landscape", "resolution": (1920, 1080),
                "safe": {"top": 4.0, "bottom": -4.0, "left": -6.0, "right": 6.0}},

    "square":  {"aspect": "square",    "resolution": (1080, 1080),
                "safe": {"top": 3.0, "bottom": -3.0, "left": -3.0, "right": 3.0}},
}

ASPECT: str = CANVAS[VIDEO_PROFILE]["aspect"]
RESOLUTION: Tuple[int, int] = CANVAS[VIDEO_PROFILE]["resolution"]
SAFE: Dict[str, float] = CANVAS[VIDEO_PROFILE]["safe"]

# ============================================================================
# Palettes (light/dark)
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

PALETTES = {
    "light": LIGHT_PALETTE,
    "dark": DARK_PALETTE,
}

ROLE_KEYS = ("primary", "secondary", "success", "warning", "danger", "info", "muted")
TEXT_KEY = "text"
TONE_BIASES = {"stroke_bias": -0.10, "glow_bias": -0.20}

# ============================================================================
# Background
# ============================================================================

ACTIVE_BACKGROUND = "starfield"

# ============================================================================
# Stroke widths
# ============================================================================

STROKES = {
    "thin": 4.0,
    "normal": 7.0,
    "thick": 10.0,
    "extra_thick": 14.0,
}

# ============================================================================
# Glow band presets
# ============================================================================

GLOW_DEFAULTS: Dict[str, List[Tuple[float, float]]] = {
    # Shared inner glow
    "inner_tight": [(0.95, 0.22), (1.05, 0.15)],

    # Per-element outer glows
    "outer_text":   [(1.10, 0.10), (2.20, 0.07), (3.50, 0.05)],
    "outer_shape": [(1.15, 0.12), (2.20, 0.08), (3.50, 0.05), (6.00, 0.03)],
    "outer_arrow": [(1.15, 0.12), (2.20, 0.08), (3.50, 0.05), (6.00, 0.03)],
}

# ============================================================================
# Plate Default
# ============================================================================

PLATE_DEFAULTS: Dict[str, Any] = {
    "shape": {
        "depth_layers": 10,
        "layer_gap": 0.05,
        "shade_bias": 0.04,
        "plate_stroke_scale": 0.8,
        "stroke_opacity": 0.55,
        "fill_opacity": 0.0,
        "stroke_width": 10,

    },
    "arrow": {
        "depth_layers": 5,
        "layer_gap": 0.03,
        "shade_bias": 0.02,
        "plate_stroke_scale": 0.85,
        "stroke_opacity": 0.55,
        "fill_opacity": 0.0,
        "stroke_width": 7,

    },
    "text": {
        "depth_layers": 6,
        "layer_gap": 0.035,
        "shade_bias": 0.03,
        "plate_stroke_scale": 0.8,
        "stroke_opacity": 0.55,
        "fill_opacity": 0.0,
        "stroke_width": 10,

    },
}

# ============================================================================
# Text variants
# ============================================================================

TEXT_VARIANTS: Dict[str, Dict[str, Any]] = {
    "title":    {"font_size": "title", "color": "#8F54FF", "stroke_color": "#2A0E63",
                 "weight": "HEAVY",  "uppercase": False, "line_spacing": 0.95},

    "label":    {"font_size": "label", "color": "#FFFFFF", "weight": "BOLD",
                 "uppercase": False, "line_spacing": 1.00},

    "subtitle": {"font_size": "subtitle", "color": "#EAF3FF", "stroke_color": "#2B3A56",
                 "weight": "SEMIBOLD", "uppercase": False, "line_spacing": 1.15},
}

# ============================================================================
# Arrow styles
# ============================================================================

ARROW_STYLE: Dict[str, Dict[str, Any]] = {
    "default": {
        "color": "muted",
        "color_source": "stroke",
        "stroke_width": 7,
        "tip_length": 0.30,
        "buff": 0.25,
        "glow_layers": 2,
        "glow_opacity": 0.25,
        "glow_decay": 0.65,
    }
}

DEFAULT_ARROW_STYLE: Dict[str, Any] = ARROW_STYLE["default"]

# ============================================================================
# Speaker and TTS model
# ============================================================================

SPEAKER: str = "en-GB-RyanNeural"
SPEAKER_STYLE = ""
