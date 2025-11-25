# src/cosmicanimator/core/theme.py

"""
Theme management for CosmicAnimator.

Provides a runtime-accessible `Theme` object that consolidates visual constants:
- Palette and roles (fill/stroke/glow triplets)
- Strokes and per-element defaults
- Glow/plate/text presets
- Arrow and layout style defaults
- Profiles, canvas settings, and voice/TTS configuration

This is the central bridge between `constants.py` and runtime styling logic
used by adapters (text, shapes, arrows, etc.).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Mapping
from cosmicanimator.core import constants as c


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _merge(base: Mapping[str, Any], over: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Return a shallow merge of two mappings, prioritizing `over`."""
    out = dict(base)
    if over:
        out.update(over)
    return out


def _tone(hex_base: str, *, stroke_bias: float, glow_bias: float) -> Tuple[str, str]:
    """
    Generate stroke and glow variants from a base color hex.

    Parameters
    ----------
    hex_base:
        Base color (e.g., "#8A3CFF").
    stroke_bias, glow_bias:
        Bias factors in [-1, 1] for darkening/lightening.

    Returns
    -------
    tuple[str, str]
        (stroke_hex, glow_hex)
    """

    def clamp(x: int) -> int:
        return max(0, min(255, x))

    def to_rgb(h: str) -> Tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    def to_hex(rgb: Tuple[int, int, int]) -> str:
        return "#%02X%02X%02X" % rgb

    r, g, b = to_rgb(hex_base)

    def mix(v: int, bias: float) -> int:
        if bias < 0:
            return clamp(int(v * (1.0 + bias)))
        return clamp(int(v + (255 - v) * bias))

    stroke = (mix(r, stroke_bias), mix(g, stroke_bias), mix(b, stroke_bias))
    glow = (mix(r, glow_bias), mix(g, glow_bias), mix(b, glow_bias))
    return to_hex(stroke), to_hex(glow)


# ---------------------------------------------------------------------------
# Theme class
# ---------------------------------------------------------------------------


class Theme:
    """
    Runtime style accessor built over `constants.py`.

    Provides unified access to:
    - Palette and computed role triplets (fill/stroke/glow)
    - Strokes, defaults, glow presets, plate presets
    - Text variants and arrow styles
    - Profiles, canvas dimensions, voice/TTS configuration
    """

    def __init__(
        self,
        *,
        theme_name: Optional[str] = None,
        palette: Optional[Mapping[str, str]] = None,
        role_triplets: Optional[Mapping[str, Dict[str, str]]] = None,
        strokes: Optional[Mapping[str, float]] = None,
        glow_presets: Optional[Mapping[str, List[Tuple[float, float]]]] = None,
        text_variants: Optional[Mapping[str, Dict[str, Any]]] = None,
        arrow_styles: Optional[Mapping[str, Dict[str, Any]]] = None,
        defaults: Optional[Mapping[str, Any]] = None,
        profiles: Optional[Mapping[str, Dict[str, Any]]] = None,
        canvas: Optional[Mapping[str, Dict[str, Any]]] = None,
        video_profile: Optional[str] = None,
        speaker: Optional[str] = None,
        speaker_style: Optional[str] = None,
    ) -> None:
        """Initialize a runtime theme configuration."""
        # ---- Profiles / canvas / voice ----
        self._profiles = _merge(getattr(c, "PROFILES", {}), profiles)
        self._video_profile = video_profile or getattr(c, "VIDEO_PROFILE", "short")
        self._canvas = _merge(getattr(c, "CANVAS", {}), canvas)
        self._speaker = speaker or getattr(c, "SPEAKER")
        self._speaker_style = speaker_style or getattr(c, "SPEAKER_STYLE")

        # ---- Palette ----
        base_theme_name = theme_name or getattr(c, "ACTIVE_THEME", "light")
        base_palette = getattr(c, "PALETTES", {}).get(
            base_theme_name, getattr(c, "PALETTES", {}).get("light", {})
        )
        self._palette: Dict[str, str] = _merge(base_palette, palette)

        # ---- Roles (compute triplets if not provided) ----
        if role_triplets is not None:
            self._roles = dict(role_triplets)
        else:
            bias = getattr(c, "TONE_BIASES", {"stroke_bias": -0.10, "glow_bias": -0.20})
            keys = getattr(
                c,
                "ROLE_KEYS",
                ("primary", "secondary", "success", "warning", "danger", "info", "muted"),
            )

            roles: Dict[str, Dict[str, str]] = {}
            for key in keys:
                base_hex = self._palette.get(key, self._palette.get("primary", "#FFFFFF"))
                stroke_hex, glow_hex = _tone(base_hex, **bias)
                roles[key] = {"fill": base_hex, "stroke": stroke_hex, "glow": glow_hex}
            self._roles = roles

        # ---- Strokes / Defaults ----
        self._strokes = _merge(getattr(c, "STROKES", {}), strokes)
        self._defaults = _merge(getattr(c, "DEFAULTS", {}), defaults)

        # ---- Glow / Plate / Text / Arrows ----
        self._glow = _merge(getattr(c, "GLOW_DEFAULTS", {}), glow_presets)
        self._plate = _merge(getattr(c, "PLATE_DEFAULTS", {}), {})
        self._text_variants = _merge(getattr(c, "TEXT_VARIANTS", {}), text_variants)

        constant_arrow_style = getattr(c, "ARROW_STYLE", {})
        self._arrow_styles = _merge(constant_arrow_style, arrow_styles)

        # ---- Background ----
        self._active_background = getattr(c, "ACTIVE_BACKGROUND", "starfield")

        # ---- Misc Keys ----
        self._bg_key = getattr(c, "BACKGROUND_KEY", "bg")
        self._text_key = getattr(c, "TEXT_KEY", "text")

    # -----------------------------------------------------------------------
    # Palette / Color Access
    # -----------------------------------------------------------------------

    def get_color(self, name: str) -> str:
        """Return a color hex by key or pass through a valid hex string."""
        if isinstance(name, str) and name.startswith("#") and len(name) in (4, 7):
            return name
        return self._palette.get(name, "#FFFFFF")

    @property
    def background_color(self) -> str:
        """Default background color (mapped to BACKGROUND_KEY)."""
        return self._palette.get(self._bg_key, "#000000")

    @property
    def default_text_color(self) -> str:
        """Default text color (mapped to TEXT_KEY)."""
        return self._palette.get(self._text_key, "#FFFFFF")

    # -----------------------------------------------------------------------
    # Background
    # -----------------------------------------------------------------------

    def get_background_name(self) -> str:
        """Return the active background key, e.g., 'starfield'."""
        return self._active_background

    # -----------------------------------------------------------------------
    # Roles / Strokes / Glow / Plate / Text / Arrow
    # -----------------------------------------------------------------------

    def get_role(self, role: Optional[str]) -> Dict[str, str]:
        """Return the color triplet dict for a given role name."""
        key = (role or "primary").strip().lower()
        return self._roles.get(key, self._roles["primary"])

    def get_stroke(self, kind: Optional[str]) -> float:
        """Return a numeric stroke width by name."""
        key = (kind or "normal").strip().lower()
        return float(self._strokes.get(key, self._strokes["normal"]))

    def get_glow(self, preset: Optional[str]) -> List[Tuple[float, float]]:
        """Return glow band pairs (width_mul, opacity) for the given preset."""
        key = (preset or "").strip().lower()
        return list(self._glow.get(key, self._glow.get("outer_shape", [])))

    def get_plate(self, name: str = "shape") -> Dict[str, Any]:
        """Return plate parameters for a given component type."""
        return dict(self._plate.get(name, self._plate.get("shape", {})))

    def get_text_variant(self, name: Optional[str]) -> Dict[str, Any]:
        """Return theme variant configuration for text (e.g., 'label', 'title')."""
        key = name or "label"
        return dict(self._text_variants.get(key, self._text_variants["label"]))

    def arrow_style(self, name: Optional[str]) -> Dict[str, Any]:
        """Return arrow style parameters (safe fallback to 'default')."""
        key = name or "default"
        return dict(self._arrow_styles.get(key, self._arrow_styles["default"]))

    # -----------------------------------------------------------------------
    # Profiles / Canvas / Voice
    # -----------------------------------------------------------------------

    def _p(self, section: str, key: str) -> Any:
        """Internal helper: lookup within active video profile."""
        prof = self._profiles.get(self._video_profile, self._profiles.get("short", {}))
        return prof.get(section, {}).get(key)

    def timing(self, name: str) -> float:
        """Retrieve timing value (seconds) for animation cues."""
        return float(self._p("timing", name) or 0.5)

    def spacing(self) -> float:
        """Layout spacing factor from profile."""
        return float(self._p("layout", "spacing") or 1.5)

    def base_scale(self) -> float:
        """Return base scaling multiplier for elements."""
        return float(self._p("layout", "scale") or 1.0)

    def font_px(self, size_key: str) -> int:
        """Resolve a font size key (e.g., 'label') to pixel value."""
        sizes = self._profiles.get(self._video_profile, {}).get("type", {})
        return int(sizes.get(size_key, sizes.get("label", 24)))

    @property
    def video_profile(self) -> str:
        """Active video profile key (e.g., 'short', 'long')."""
        return self._video_profile

    @property
    def canvas_aspect(self) -> str:
        """Aspect ratio string for the active video profile."""
        return self._canvas.get(self._video_profile, {}).get("aspect", "vertical")

    @property
    def canvas_resolution(self) -> Tuple[int, int]:
        """Canvas resolution tuple (width, height)."""
        return tuple(self._canvas.get(self._video_profile, {}).get("resolution", (1080, 1920)))  # type: ignore

    @property
    def canvas_safe(self) -> Dict[str, float]:
        """Safe margins for the active canvas layout."""
        return dict(self._canvas.get(self._video_profile, {}).get("safe", {}))

    def get_speaker(self) -> str:
        """Return the active TTS speaker identifier."""
        return self._speaker

    def get_speaker_style(self):
        """Return the active speaker's style."""
        return self._speaker_style

    def get_tts_model(self) -> str:
        """Return the active TTS model path."""
        return self._tts_model

    # -----------------------------------------------------------------------
    # Introspection
    # -----------------------------------------------------------------------

    def describe(self) -> Dict[str, Any]:
        """Return a diagnostic snapshot of the current theme configuration."""
        return {
            "video_profile": self._video_profile,
            "palette_keys": sorted(self._palette.keys()),
            "roles": sorted(self._roles.keys()),
            "strokes": sorted(self._strokes.keys()),
            "glow_presets": sorted(self._glow.keys()),
            "text_variants": sorted(self._text_variants.keys()),
            "arrow_styles": sorted(self._arrow_styles.keys()),
            "defaults": dict(self._defaults),
        }


# ---------------------------------------------------------------------------
# Default export
# ---------------------------------------------------------------------------

current_theme = Theme()
